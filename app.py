import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Compensación de Nivelación - EDOS SpA",
    page_icon="📏",
    layout="wide",
)

st.title("📏 Compensación de Nivelación Geométrica")
st.markdown(
    "**EDOS SpA** | Módulo de Cálculo, Cierre y Control Altimétrico"
)

# ==========================================
# 1. PARÁMETROS DEL PROYECTO (SESSION STATE)
# ==========================================
st.sidebar.header("Parámetros del Proyecto")

if "proyecto" not in st.session_state:
  st.session_state.proyecto = "Obra / Sector General"
if "topografo" not in st.session_state:
  st.session_state.topografo = "Vicente Ortiz A."
if "cota_inicial" not in st.session_state:
  st.session_state.cota_inicial = 500.000

st.session_state.proyecto = st.sidebar.text_input(
    "Nombre del Proyecto", st.session_state.proyecto
)
st.session_state.topografo = st.sidebar.text_input(
    "Topógrafo / Operador", st.session_state.topografo
)
st.session_state.cota_inicial = st.sidebar.number_input(
    "Cota Inicial de Partida (BM) [m]",
    value=st.session_state.cota_inicial,
    format="%.3f",
)

# ==========================================
# 2. INGRESO DE LIBRETA DE CAMPO
# ==========================================
st.markdown("### 1. Ingreso de Libreta de Campo")
st.markdown(
    "Registre las lecturas de mira o modifique las filas directamente en la"
    " tabla:"
)

# Inicializar el DataFrame en el session_state si no existe
if "df_libreta" not in st.session_state:
  st.session_state.df_libreta = pd.DataFrame({
      "Punto": ["BM-1", "P-1", "P-2", "BM-2"],
      "Lect. Atrás": [1.455, 0.0, 0.0, 0.0],
      "Lect. Int.": [0.0, 1.320, 0.0, 0.0],
      "Lect. Adel.": [0.0, 0.0, 0.942, 1.890],
  })

# st.data_editor sincronizado directamente con session_state para evitar doble clic o desfase
edited_df = st.data_editor(
    st.session_state.df_libreta,
    num_rows="dynamic",
    key="libreta_editor",
    use_container_width=True,
)

# Actualizamos el session_state con los cambios del editor
st.session_state.df_libreta = edited_df

# ==========================================
# 3. CÁLCULOS ALTIMÉTRICOS AUTOMÁTICOS
# ==========================================
cota_actual = st.session_state.cota_inicial
c_inst = 0.0
cotas = []
c_insts = []

sum_bs = 0.0
sum_fs = 0.0

for idx, row in st.session_state.df_libreta.iterrows():
  bs = float(row.get("Lect. Atrás", 0.0) or 0.0)
  bi = float(row.get("Lect. Int.", 0.0) or 0.0)
  fs = float(row.get("Lect. Adel.", 0.0) or 0.0)

  sum_bs += bs
  sum_fs += fs

  if bs > 0:
    c_inst = cota_actual + bs

  c_insts.append(c_inst if c_inst > 0 else 0.0)

  if bs > 0:
    cotas.append(cota_actual)
  elif bi > 0:
    cota = c_inst - bi
    cotas.append(cota)
    cota_actual = cota
  elif fs > 0:
    cota = c_inst - fs
    cotas.append(cota)
    cota_actual = cota
  else:
    cotas.append(cota_actual)

# Construir DataFrame final con resultados
df_resultado = st.session_state.df_libreta.copy()
df_resultado["C. Inst."] = c_insts
df_resultado["Cota"] = cotas

# ==========================================
# 4. RESULTADOS Y ANÁLISIS ALTIMÉTRICO
# ==========================================
st.markdown("### 2. Resultados y Análisis Altimétrico")

col1, col2, col3 = st.columns(3)
col1.metric("Suma Vistas Atrás (BS)", f"{sum_bs:.3f} m")
col2.metric("Suma Vistas Adelante (FS)", f"{sum_fs:.3f} m")
desnivel = sum_bs - sum_fs
col3.metric("Desnivel Acumulado", f"{desnivel:.3f} m")

st.markdown("#### Detalle Calculado")
st.dataframe(df_resultado, use_container_width=True)

# ==========================================
# 5. EXPORTACIÓN Y FINALIZACIÓN
# ==========================================
st.markdown("### 3. Exportación y Finalización de Libreta")

csv = df_resultado.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Descargar Libreta Calculada (CSV)",
    data=csv,
    file_name=(
        f"libreta_nivelacion_{st.session_state.proyecto.replace(' ', '_')}.csv"
    ),
    mime="text/csv",
)
