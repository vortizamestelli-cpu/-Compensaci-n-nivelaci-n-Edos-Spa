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
  st.session_state.cota_inicial = 487.809

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
# 2. INGRESO DE LIBRETA DE CAMPO (CON FORMULARIO)
# ==========================================
st.markdown("### 1. Ingreso de Libreta de Campo")
st.markdown(
    "Modifique los valores en la tabla y presione el botón **'Aplicar y"
    " Calcular'** para registrar los cambios de inmediato:"
)

# Inicializar el DataFrame en el session_state si no existe con datos de ejemplo válidos
if "df_libreta" not in st.session_state:
  st.session_state.df_libreta = pd.DataFrame({
      "Punto": ["pr3", "1", "pr10", "1", "pr3"],
      "Lect. Atrás": [1.723, 0.884, 1.075, 2.054, 0.0],
      "Lect. Int.": [0.0, 0.0, 0.0, 0.0, 0.0],
      "Lect. Adel.": [0.0, 1.960, 0.720, 1.239, 1.815],
  })

# st.form agrupa los cambios de la tabla hasta hacer clic en el botón de envío
with st.form("form_libreta"):
  edited_df = st.data_editor(
      st.session_state.df_libreta,
      num_rows="dynamic",
      key="libreta_editor",
      use_container_width=True,
  )
  submit_button = st.form_submit_button(
      "💾 Aplicar y Calcular", type="primary"
  )

# Guardar los cambios en el estado global al presionar el botón del formulario
if submit_button:
  st.session_state.df_libreta = edited_df
  st.success("¡Datos aplicados correctamente en la libreta!")

# ==========================================
# 3. CÁLCULOS ALTIMÉTRICOS AUTOMÁTICOS (CORREGIDOS)
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

  # Caso especial para el primer punto (BM inicial)
  if idx == 0 and bs > 0 and fs == 0:
    c_inst = cota_actual + bs
    cotas.append(cota_actual)
    c_insts.append(c_inst)
    continue

  # 1. Calcular la cota del punto usando la visual adelante (FS) o intermedia (BI) vigente
  cota_punto = cota_actual
  if fs > 0:
    cota_punto = c_inst - fs
    cota_actual = cota_punto
  elif bi > 0:
    cota_punto = c_inst - bi
    cota_actual = cota_punto
  elif bs > 0:
    cota_punto = cota_actual

  cotas.append(cota_punto)

  # 2. Si el punto tiene vista atrás (BS), actualizamos la altura instrumental para el siguiente tramo
  if bs > 0:
    c_inst = cota_actual + bs

  c_insts.append(c_inst if c_inst > 0 else 0.0)

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
