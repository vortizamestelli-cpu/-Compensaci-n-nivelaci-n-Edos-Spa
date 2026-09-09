from fpdf import FPDF
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
# 1. PARÁMETROS DEL PROYECTO Y MENÚ
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

tipo_nivelacion = st.sidebar.selectbox(
    "Tipo de Nivelación",
    [
        "Nivelación Abierta (Desnivel / Línea)",
        "Nivelación Cerrada (Circuito)",
    ],
)

st.session_state.cota_inicial = st.sidebar.number_input(
    "Cota Inicial de Partida (BM) [m]",
    value=st.session_state.cota_inicial,
    format="%.3f",
)

cota_final_conocida = st.session_state.cota_inicial
if "Cerrada" in tipo_nivelacion:
  cota_final_conocida = st.sidebar.number_input(
      "Cota Final Teórica / De Cierre (BM) [m]",
      value=st.session_state.cota_inicial,
      format="%.3f",
  )

# ==========================================
# 2. INGRESO DE LIBRETA DE CAMPO (CON FORMULARIO)
# ==========================================
st.markdown(f"### 1. Ingreso de Libreta de Campo ({tipo_nivelacion})")
st.markdown(
    "Modifique los valores en la tabla y presione el botón **'Aplicar y"
    " Calcular'** para registrar los cambios de inmediato:"
)

if "df_libreta" not in st.session_state:
  st.session_state.df_libreta = pd.DataFrame({
      "Punto": ["BM-1", "P-1", "P-2", "BM-1"],
      "Lect. Atrás": [1.723, 0.884, 1.075, 0.0],
      "Lect. Int.": [0.0, 0.0, 0.0, 0.0],
      "Lect. Adel.": [0.0, 1.960, 0.720, 1.815],
  })

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

if submit_button:
  st.session_state.df_libreta = edited_df
  st.success("¡Datos aplicados correctamente en la libreta!")

# ==========================================
# 3. CÁLCULOS ALTIMÉTRICOS
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

  if idx == 0 and bs > 0 and fs == 0:
    c_inst = cota_actual + bs
    cotas.append(cota_actual)
    c_insts.append(c_inst)
    continue

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

  if bs > 0:
    c_inst = cota_actual + bs

  c_insts.append(c_inst if c_inst > 0 else 0.0)

df_resultado = st.session_state.df_libreta.copy()
df_resultado["C. Inst."] = c_insts
df_resultado["Cota Bruta"] = cotas

err_cierre = 0.0
if "Cerrada" in tipo_nivelacion and len(df_resultado) > 0:
  cota_calculada_final = cotas[-1]
  err_cierre = cota_calculada_final - cota_final_conocida

  correcciones = []
  n_puntos = len(cotas)
  for i in range(n_puntos):
    corr = -err_cierre * (i / max(1, n_puntos - 1))
    correcciones.append(corr)

  df_resultado["Corrección"] = correcciones
  df_resultado["Cota Compensada"] = (
      df_resultado["Cota Bruta"] + df_resultado["Corrección"]
  )
else:
  df_resultado["Cota Compensada"] = df_resultado["Cota Bruta"]

# ==========================================
# 4. RESULTADOS Y ANÁLISIS ALTIMÉTRICO
# ==========================================
st.markdown("### 2. Resultados y Análisis Altimétrico")

col1, col2, col3 = st.columns(3)
col1.metric("Suma Vistas Atrás (BS)", f"{sum_bs:.3f} m")
col2.metric("Suma Vistas Adelante (FS)", f"{sum_fs:.3f} m")
desnivel = sum_bs - sum_fs
col3.metric("Desnivel Acumulado", f"{desnivel:.3f} m")

if "Cerrada" in tipo_nivelacion:
  cota_calc_final = cotas[-1] if len(cotas) > 0 else 0
  st.info(
      f"**Control de Cierre:** Cota Calculada = {cota_calc_final:.3f} m | Cota"
      f" Teórica = {cota_final_conocida:.3f} m | **Error de Cierre:**"
      f" {err_cierre*1000:.1f} mm"
  )

st.markdown("#### Detalle Calculado")
st.dataframe(df_resultado, use_container_width=True)


# ==========================================
# 5. GENERACIÓN DE PDF Y EXPORTACIÓN
# ==========================================
class PDFReporte(FPDF):

  def header(self):
    self.set_font("helvetica", "B", 14)
    self.cell(
        0, 8, "EDOS SpA - Informe de Nivelación Geométrica", 0, 1, "C"
    )
    self.set_font("helvetica", "", 9)
    self.cell(
        0,
        5,
        "Modulo de Control y Compensación Altimétrica de Terreno",
        0,
        1,
        "C",
    )
    self.ln(5)

  def footer(self):
    self.set_y(-15)
    self.set_font("helvetica", "I", 8)
    self.cell(
        0,
        10,
        f"Página {self.page_no()} - EDOS SpA",
        0,
        0,
        "C",
    )


def crear_pdf(df, proyecto, topografo, tipo_niv, cota_ini, error_c):
  pdf = PDFReporte(orientation="L", unit="mm", format="A4")
  pdf.add_page()

  # Datos del Proyecto
  pdf.set_font("helvetica", "B", 10)
  pdf.cell(0, 6, "DATOS GENERALES DEL PROYECTO", 0, 1)
  pdf.set_font("helvetica", "", 9)
  pdf.cell(0, 5, f"Proyecto: {proyecto}", 0, 1)
  pdf.cell(0, 5, f"Topógrafo / Operador: {topografo}", 0, 1)
  pdf.cell(0, 5, f"Tipo de Nivelación: {tipo_niv}", 0, 1)
  pdf.cell(0, 5, f"Cota Inicial (BM): {cota_ini:.3f} m", 0, 1)
  if "Cerrada" in tipo_niv:
    pdf.cell(
        0, 5, f"Error de Cierre Calculado: {error_c*1000:.1f} mm", 0, 1
    )
  pdf.ln(5)

  # Tabla de resultados
  pdf.set_font("helvetica", "B", 9)
  columnas = list(df.columns)
  anchos = [30, 32, 32, 32, 35, 35, 35, 35]  # Anchos proporcionales para A4

  # Cabeceras
  for i, col in enumerate(columnas):
    pdf.cell(anchos[i] if i < len(anchos) else 25, 7, str(col), 1, 0, "C")
  pdf.ln()

  # Filas de datos
  pdf.set_font("helvetica", "", 8)
  for _, row in df.iterrows():
    for i, val in enumerate(row):
      if isinstance(val, float):
        val_str = f"{val:.3f}"
      else:
        val_str = str(val) if val is not None else ""
      pdf.cell(
          anchos[i] if i < len(anchos) else 25, 6, val_str, 1, 0, "C"
      )
    pdf.ln()

  return bytes(pdf.output())


st.markdown("### 3. Exportación y Finalización de Libreta")

pdf_bytes = crear_pdf(
    df_resultado,
    st.session_state.proyecto,
    st.session_state.topografo,
    tipo_nivelacion,
    st.session_state.cota_inicial,
    err_cierre,
)

st.download_button(
    label="📥 Descargar Informe en PDF",
    data=pdf_bytes,
    file_name=(
        f"Informe_Nivelacion_{st.session_state.proyecto.replace(' ', '_')}.pdf"
    ),
    mime="application/pdf",
)
