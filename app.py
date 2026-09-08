import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Compensación de Nivelación - EDOS SpA",
    page_icon="📏",
    layout="wide"
)

st.title("📏 Compensación de Nivelación Geométrica")
st.markdown("**EDOS SpA** | Módulo de Cálculo, Cierre y Control Altimétrico")

# Barra lateral para parámetros generales
st.sidebar.header("Parámetros del Proyecto")
proyecto = st.sidebar.text_input("Nombre del Proyecto", "Obra / Sector General")
operador = st.sidebar.text_input("Topógrafo / Operador", "Vicente Ortiz A.")
cota_partida = st.sidebar.number_input("Cota Inicial de Partida (BM) [m]", value=100.000, format="%.3f")

st.markdown("---")

st.subheader("1. Ingreso de Libreta de Campo")
st.markdown("Registre las lecturas de mira para las vistas atrás (BS) y vistas adelante (FS) de cada estación.")

# Datos de ejemplo iniciales
data_default = pd.DataFrame([
    {"Punto": "BM-1", "Distancia (m)": 0.0, "V. Atrás (BS)": 1.455, "V. Adelante (FS)": 0.0, "Tipo": "BM"},
    {"Punto": "P-1", "Distancia (m)": 25.5, "V. Atrás (BS)": 1.820, "V. Adelante (FS)": 0.942, "Tipo": "EI"},
    {"Punto": "P-2", "Distancia (m)": 30.0, "V. Atrás (BS)": 2.110, "V. Adelante (FS)": 1.155, "Tipo": "EI"},
    {"Punto": "BM-2", "Distancia (m)": 20.0, "V. Atrás (BS)": 0.0, "V. Adelante (FS)": 1.890, "Tipo": "BM"}
])

# Editor interactivo
df_libreta = st.data_editor(data_default, num_rows="dynamic", use_container_width=True)

if not df_libreta.empty:
    st.markdown("---")
    st.subheader("2. Resultados y Análisis Altimétrico")

    try:
        df = df_libreta.copy()
        
        sum_bs = df["V. Atrás (BS)"].sum()
        sum_fs = df["V. Adelante (FS)"].sum()
        desnivel_total = sum_bs - sum_fs
        distancia_total = df["Distancia (m)"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Suma Vistas Atrás (ΣBS)", f"{sum_bs:.3f} m")
        col2.metric("Suma Vistas Adelante (ΣFS)", f"{sum_fs:.3f} m")
        col3.metric("Desnivel Acumulado", f"{desnivel_total:.3f} m")

        st.markdown("---")
        st.subheader("3. Control de Cierre y Tolerancia")
        
        tipo_nivelacion = st.radio(
            "Seleccione el tipo de cierre:", 
            ["Circuito Cerrado (Llegada al mismo BM)", "Circuito Abierto con Cota de Llegada Conocida", "Libre / Sin Cota de Cierre Final"]
        )
        
        cota_llegada_teorica = cota_partida
        if tipo_nivelacion == "Circuito Abierto con Cota de Llegada Conocida":
            cota_llegada_teorica = st.number_input("Cota de Llegada Conocida [m]", value=100.120, format="%.3f")

        if tipo_nivelacion != "Libre / Sin Cota de Cierre Final":
            cota_calculada_final = cota_partida + desnivel_total
            error_cierre = cota_calculada_final - cota_llegada_teorica
            
            st.info(f"**Cota de Llegada Calculada:** {cota_calculada_final:.3f} m  \n**Error de Cierre Altímétrico (e):** {error_cierre*1000:.2f} mm")
            
            # Tolerancia normativa típica en construcción civil (12 mm * sqrt(km))
            tolerancia_mm = 12.0 * np.sqrt(max(distancia_total / 1000.0, 0.01))
            st.write(f"Tolerancia admisible estimada: **{tolerancia_mm:.1f} mm**")

            if abs(error_cierre * 1000) <= tolerancia_mm:
                st.success("¡El error de cierre se encuentra dentro de la tolerancia normativa!")
            else:
                st.warning("El error de cierre excede la tolerancia estimada. Verifique las lecturas en terreno.")

        st.markdown("---")
        st.subheader("4. Exportación de Datos")
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Libreta Compensada (CSV)",
            data=csv,
            file_name="libreta_compensada_edos.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error en el procesamiento de la libreta: {e}")
