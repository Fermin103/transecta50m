import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# Configuración de página
st.set_page_config(page_title="Transecta Botánica Pro", layout="wide")

# --- ESTADO DE LA SESIÓN ---
if 'lista_especies' not in st.session_state:
    st.session_state.lista_especies = sorted([
        "Acantholippia seriphioides", "Atriplex lampa", "Atriplex undulata", 
        "Bacharis darwinii", "Bougainvillea spinosa", "Cyclolepis genistoides", 
        "Junellia seriphioides", "Larrea cuneifolia", "Larrea divaricata", 
        "Lycium Sp", "Menodora robusta", "Monttea aphylla", "Mulguraea aspera", 
        "Pappostipa speciosa", "Salicornia neii", "Schinus polygamus", 
        "Senecio filaginoides", "Senna aphylla", "Broza"
    ])

if 'datos_intervalos' not in st.session_state:
    st.session_state.datos_intervalos = []

# --- LÓGICA DE RELLENO DE SUELO DESNUDO ---
def rellenar_suelo_desnudo(datos):
    if not datos:
        return [{"Especie": "Suelo Desnudo", "Inicio": 0.0, "Fin": 50.0, "Longitud (m)": 50.0}]
    
    df = pd.DataFrame(datos).sort_values(by="Inicio")
    intervalos_ocupados = []
    for _, row in df.iterrows():
        inicio, fin = row['Inicio'], row['Fin']
        if not intervalos_ocupados or inicio > intervalos_ocupados[-1][1]:
            intervalos_ocupados.append([inicio, fin])
        else:
            intervalos_ocupados[-1][1] = max(intervalos_ocupados[-1][1], fin)
    
    datos_completos = list(datos)
    cursor = 0.0
    for inicio_occ, fin_occ in intervalos_ocupados:
        if inicio_occ > cursor:
            datos_completos.append({"Especie": "Suelo Desnudo", "Inicio": cursor, "Fin": inicio_occ, "Longitud (m)": round(inicio_occ - cursor, 2)})
        cursor = max(cursor, fin_occ)
    
    if cursor < 50.0:
        datos_completos.append({"Especie": "Suelo Desnudo", "Inicio": cursor, "Fin": 50.0, "Longitud (m)": round(50.0 - cursor, 2)})
        
    return datos_completos

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf(df_resumen, df_detalle, long_veg, long_suelo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Informe Final de Transecta Botanica", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Planilla de Especies Detectadas", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(80, 8, "Especie", 1); pdf.cell(40, 8, "Longitud (m)", 1); pdf.cell(30, 8, "Apariciones", 1); pdf.cell(40, 8, "% Cobertura", 1)
    pdf.ln()
    
    for _, row in df_resumen.iterrows():
        if row['Especie'] != "Suelo Desnudo":
            pdf.cell(80, 7, str(row['Especie']), 1)
            pdf.cell(40, 7, f"{row['Longitud (m)']} m", 1)
            pdf.cell(30, 7, str(row['Nº de Apariciones']), 1)
            pdf.cell(40, 7, f"{row['% Cobertura']}%", 1)
            pdf.ln()

    pdf.ln(10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Resumen Global", ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 8, f"Cobertura Vegetal Total: {round((long_veg/50)*100, 2)}%", ln=True)
    pdf.cell(0, 8, f"Suelo Desnudo Total: {round((long_suelo/50)*100, 2)}%", ln=True)
    
    return bytes(pdf.output())

# --- INTERFAZ ---
st.title("🌿 Registro de Transectas (0-50m)")

tab_reg, tab_an = st.tabs(["📏 Registro de Campo", "📊 Informe y Análisis"])

with tab_reg:
    with st.expander("➕ Agregar especie que no está en la lista"):
        c_esp1, c_esp2 = st.columns([3, 1])
        with c_esp1:
            nueva_esp_input = st.text_input("Nombre de la nueva especie", key="input_nueva_esp")
        with c_esp2:
            st.write(" ")
            if st.button("Guardar Especie", use_container_width=True):
                if nueva_esp_input and nueva_esp_input not in st.session_state.lista_especies:
                    st.session_state.lista_especies.append(nueva_esp_input)
                    st.session_state.lista_especies.sort()
                    st.success(f"{nueva_esp_input} agregada!")
                    st.rerun()

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2.5, 1, 1, 1])
        with col1:
            esp_seleccionada = st.selectbox("Seleccionar Especie", options=st.session_state.lista_especies, index=None, placeholder="Busca en la lista...")
        with col2:
            sug_ini = st.session_state.datos_intervalos[-1]["Fin"] if st.session_state.datos_intervalos else 0.0
            ini = st.number_input("Inicio (m)", min_value=0.0, max_value=50.0, value=float(sug_ini), step=0.01)
        with col3:
            v_fin = float(ini + 0.5) if ini + 0.5 <= 50.0 else 50.0
            fin = st.number_input("Fin (m)", min_value=0.0, max_value=50.0, value=v_fin, step=0.01)
        with col4:
            st.write(" ")
            if st.button("📥 Registrar Tramo", use_container_width=True):
                if esp_seleccionada and fin > ini:
                    st.session_state.datos_intervalos.append({"Especie": esp_seleccionada, "Inicio": ini, "Fin": fin, "Longitud (m)": round(fin-ini, 2)})
                    st.rerun()

    if st.session_state.datos_intervalos:
        st.dataframe(pd.DataFrame(st.session_state.datos_intervalos).sort_values(by="Inicio", ascending=False), use_container_width=True)
        if st.button("🗑️ Borrar último registro"):
            st.session_state.datos_intervalos.pop()
            st.rerun()

with tab_an:
    if st.session_state.datos_intervalos:
        datos_completos = rellenar_suelo_desnudo(st.session_state.datos_intervalos)
        df_full = pd.DataFrame(datos_completos)
        
        resumen = df_full.groupby("Especie").agg(Longitud_Total=("Longitud (m)", "sum"), Apariciones=("Especie", "count")).reset_index()
        resumen.columns = ["Especie", "Longitud (m)", "Nº de Apariciones"]
        resumen["% Cobertura"] = (resumen["Longitud (m)"] / 50 * 100).round(2)
        
        # --- LÓGICA DE ORDENAMIENTO SOLICITADA ---
        # 1. Por Apariciones (Descendente)
        # 2. Por % Cobertura (Descendente) como desempate
        resumen = resumen.sort_values(by=["Nº de Apariciones", "% Cobertura"], ascending=[False, False])
        
        planilla_especies = resumen[resumen["Especie"] != "Suelo Desnudo"]
        
        st.subheader("📋 Planilla de Especies (Ordenada por Apariciones y Cobertura)")
        st.dataframe(planilla_especies, hide_index=True, use_container_width=True)
        
        c_bar, c_pie = st.columns(2)
        with c_bar:
            st.plotly_chart(px.bar(planilla_especies, x="Especie", y="% Cobertura", title="% Cobertura por Especie", text_auto=True), use_container_width=True)
        with c_pie:
            long_suelo = resumen[resumen["Especie"] == "Suelo Desnudo"]["Longitud (m)"].sum()
            long_veg = 50.0 - long_suelo
            df_pie = pd.DataFrame({"Cat": ["Cobertura Veg.", "Suelo Desnudo"], "Val": [long_veg, long_suelo]})
            st.plotly_chart(px.pie(df_pie, values="Val", names="Cat", title="Total Transecta (50m)", color="Cat", color_discrete_map={"Cobertura Veg.":"#2E7D32","Suelo Desnudo":"#795548"}), use_container_width=True)

        st.subheader("🗺️ Mapa de Distribución Espacial")
        fig_map = px.timeline(df_full, x_start="Inicio", x_end="Fin", y="Especie", color="Especie", color_discrete_map={"Suelo Desnudo": "#E5E5E5"})
        fig_map.update_layout(xaxis_type='linear', xaxis=dict(range=[0, 50], title="Metros"))
        st.plotly_chart(fig_map, use_container_width=True)

        if st.button("🔨 Descargar Informe PDF", use_container_width=True):
            pdf_b = generar_pdf(resumen, df_full.sort_values(by="Inicio"), long_veg, long_suelo)
            st.download_button("⬇️ Guardar PDF", data=pdf_b, file_name="informe_transecta.pdf", mime="application/pdf")
    else:
        st.warning("No hay datos para analizar.")