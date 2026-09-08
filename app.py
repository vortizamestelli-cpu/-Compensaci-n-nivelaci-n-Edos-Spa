import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Compensación de Nivelación - EDOS SpA", page_icon="📏", layout="wide"
)

st.title("📏 Compensación de Nivelación Geométrica")
st.markdown("**EDOS SpA** | Módulo de Cálculo, Cierre y Control Altimétrico")

# --- BARRA LATERAL: PARÁMETROS DEL PROYECTO ---
st.sidebar.header("Parámetros del Proyecto")
nombre_proyecto = st.sidebar.text_input(
    "Nombre del Proyecto", "Obra / Sector General"
)
operador = st.sidebar.text_input("Topógrafo / Operador", "Vicente Ortiz A.")
cota_inicial = st.sidebar.number_input(
    "Cota Inicial de Partida (BM) [m]", value=500.000, format="%.3f"
)

# --- 1. INGRESO DE LIBRETA DE CAMPO ---
st.header("1. Ingreso de Libreta de Campo")
st.markdown(
    "Registre las lecturas de mira en las columnas correspondientes (ingreso"
    " manual en rojo):"
)

# Datos iniciales de ejemplo para la tabla editable
datos_iniciales = pd.DataFrame(
    {
        "Punto": ["BM-1", "P-1", "P-2", "BM-2"],
        "Lect. Atrás": [1.455, 0.0, 0.0, 0.0],
        "Lect. Int.": [0.0, 1.320, 0.0, 0.0],
        "Lect. Adel.": [0.0, 0.0, 0.942, 1.890],
    }
)

df_libreta = st.data_editor(
    datos_iniciales, num_rows="dynamic", use_container_width=True
)

# --- LÓGICA DE CÁLCULO ALTIMÉTRICO ---
cotas_inst = []
cotas_terreno = []
cota_actual = cota_inicial
cota_inst_actual = 0.0

for index, row in df_libreta.iterrows():
  ba = row["Lect. Atrás"]
  bi = row["Lect. Int."]
  bf = row["Lect. Adel."]

  if ba > 0:
    cota_inst_actual = cota_actual + ba
  cotas_inst.append(cota_inst_actual)

  if ba > 0:
    cota_actual = cota_inst_actual
  elif bi > 0:
    cota_terreno = cota_inst_actual - bi
    cotas_terreno.append(cota_terreno)
    continue
  elif bf > 0:
    cota_terreno = cota_inst_actual - bf
    cotas_terreno.append(cota_terreno)
    cota_actual = cota_terreno
    continue

  if index == 0:
    cotas_terreno.append(cota_inicial)
  else:
    cotas_terreno.append(cota_actual)

df_libreta["C. Inst."] = cotas_inst
df_libreta["Cota"] = cotas_terreno

# --- 2. RESULTADOS Y ANÁLISIS ALTIMÉTRICO ---
st.header("2. Resultados y Análisis Altimétrico")

sum_bs = df_libreta["Lect. Atrás"].sum()
sum_fs = df_libreta["Lect. Adel."].sum()
desnivel = sum_bs - sum_fs

col1, col2, col3 = st.columns(3)
col1.metric("Suma Vistas Atrás (BS)", f"{sum_bs:.3f} m")
col2.metric("Suma Vistas Adelante (FS)", f"{sum_fs:.3f} m")
col3.metric("Desnivel Acumulado", f"{desnivel:.3f} m")

# Renombrar columnas para reducir el ancho visual en la tabla
df_mostrar = df_libreta.rename(
    columns={
        "Lect. Atrás": "L. Atrás",
        "Lect. Int.": "L. Int.",
        "Lect. Adel.": "L. Adel.",
    }
)


# Función para aplicar estilo: destacar lecturas de ingreso en rojo
def resaltar_lecturas(df):
  columnas_ingreso = ["L. Atrás", "L. Int.", "L. Adel."]
  return df.style.map(
      lambda x: "color: #d9534f; font-weight: bold;",
      subset=[col for col in columnas_ingreso if col in df.columns],
  )


# Mostrar la tabla estilizada en Streamlit
st.dataframe(resaltar_lecturas(df_mostrar), use_container_width=True)

# --- 3. EXPORTACIÓN DE DATOS ---
st.header("3. Exportación de Datos")
csv_data = df_libreta.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Descargar Libreta Calculada (CSV)",
    data=csv_data,
    file_name="libreta_nivelacion_edos.csv",
    mime="text/csv",
)
