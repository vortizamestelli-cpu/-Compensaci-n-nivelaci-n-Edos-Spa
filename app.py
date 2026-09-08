import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Compensación de Nivelación - EDOS SpA",
    page_icon="📏",
    layout="wide"
)

st.title("📏 Compensación y Cálculo de Nivelación Geométrica")
st.markdown("**EDOS SpA** | Módulo de Cálculo Altimétrico y Libreta Topográfica")

# Barra lateral para parámetros generales
st.sidebar.header("Parámetros del Proyecto")
proyecto = st.sidebar.text_input("Nombre del Proyecto", "Obra / Sector General")
operador = st.sidebar.text_input("Topógrafo / Operador", "Vicente Ortiz A.")
cota_partida = st.sidebar.number_input("Cota Inicial de Partida (BM) [m]", value=100.000, format="%.3f")

st.markdown("---")

st.subheader("1. Ingreso de Libreta de Campo")
st.markdown("Registre las lecturas de mira en las columnas correspondientes:")

# Datos de ejemplo iniciales con columnas abreviadas
data_default = pd.DataFrame([
    {"Punto": "BM-1", "Lect. Atrás": 1.455, "Lect. Int.": 0.0, "Lect. Ad.": 0.0, "Cota Inst.": 0.0, "Cota Terr.": 100.000},
    {"Punto": "P-1", "Lect. Atrás": 0.0, "Lect. Int.": 1.320, "Lect. Ad.": 0.0, "Cota Inst.": 0.0, "Cota Terr.": 0.0},
    {"Punto": "P-2", "Lect. Atrás": 0.0, "Lect. Int.": 0.0, "Lect. Ad.": 0.942, "Cota Inst.": 0.0, "Cota Terr.": 0.0},
    {"Punto": "BM-2", "Lect. Atrás": 0.0, "Lect. Int.": 0.0, "Lect. Ad.": 1.890, "Cota Inst.": 0.0, "Cota Terr.": 0.0}
])

# Editor interactivo
df_libreta = st.data_editor(data_default, num_rows="dynamic", use_container_width=True)

if not df_libreta.empty:
    st.markdown("---")
    st.subheader("2. Resultados y Cálculo Altimétrico")

    try:
        df = df_libreta.copy()
        
        cota_actual = cota_partida
        hi_actual = 0.0
        
        # Cálculo secuencial línea por línea
        for index, row in df.iterrows():
            bs = row["Lect. Atrás"]
            is_val = row["Lect. Int."]
            fs = row["Lect. Ad."]
            
            if index == 0:
                cota_actual = cota_partida
                if bs > 0:
                    hi_actual = cota_actual + bs
            else:
                if bs > 0:
                    hi_actual = cota_actual + bs
                
                if is_val > 0 and hi_actual > 0:
                    cota_actual = hi_actual - is_val
                elif fs > 0 and hi_actual > 0:
                    cota_actual = hi_actual - fs

            df.loc[index, "Cota Inst."] = round(hi_actual, 3)
            df.loc[index, "Cota Terr."] = round(cota_actual, 3)

        st.dataframe(df, use_container_width=True)

        sum_bs = df["Lect. Atrás"].sum()
        sum_fs = df["Lect. Ad."].sum()
        desnivel_total = sum_bs - sum_fs

        col1, col2, col3 = st.columns(3)
        col1.metric("Suma Vistas Atrás (ΣBS)", f"{sum_bs:.3f} m")
        col2.metric("Suma Vistas Adelante (ΣFS)", f"{sum_fs:.3f} m")
        col3.metric("Desnivel Acumulado", f"{desnivel_total:.3f} m")

        st.markdown("---")
        st.subheader("3. Exportación de Datos")
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Libreta Calculada (CSV)",
            data=csv,
            file_name="libreta_nivelacion_edos.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error en el procesamiento de la libreta: {e}")
