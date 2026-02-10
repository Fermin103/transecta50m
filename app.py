import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# Configuración de página
st.set_page_config(page_title="Transecta Botánica Pro", layout="wide")

# --- ESTADO DE LA SESIÓN ---
if 'lista_especies' not in st.session_state:
    # Lista oficial solicitada en orden alfabético
    st.session_state.lista_especies = sorted([
        "Acantholippia seriphioides", "Atriplex lampa", "Atriplex undulata", 
        "Bacharis darwinii", "Bougainvillea spinosa", "Cyclolepis genistoides", 
        "Junellia seriphioides", "Larrea cuneifolia", "Larrea divaricata", 
        "Lycium Sp", "Menodora robusta", "Monttea aphylla", "Mulguraea aspera", 
        "Pappostipa speciosa", "Salicornia neii", "Schinus polygamus", 
        "Senecio filaginoides", "Senna aphylla", "Suelo Desnudo", "Broza"
    ])

if 'datos_intervalos' not in st.session_state:
    st.session_state.datos_intervalos = []

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf(df_resumen, df_detalle):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Informe de Transecta Botánica (50m)", ln=True, align='C')
    pdf.ln(10)
    
    # Resumen de Cobertura
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "Resumen de Cobertura (%)", ln=True)
    pdf.set_font("Arial", '', 10)
    
    # Encabezados tabla resumen
    pdf.cell(95, 8, "Especie / Componente", 1)
    pdf.cell(45, 8, "Longitud Total (m)", 1)
    pdf.cell(45, 8, "% Cobertura", 1)
    pdf.ln()
    
    for index, row in df_resumen.iterrows():
        pdf.cell(95, 7, str(row['Especie']), 1)
        pdf.cell(45, 7, f"{row['Longitud (m)']} m", 1)
        pdf.cell(45, 7, f"{row['% Cobertura']} %", 1)
        pdf.ln()
        
    pdf.ln(10)
    
    # Detalle de Tramos
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "Detalle de Tramos Registrados", ln=True)
    pdf.set_font("Arial", '', 9)
    
    # Encabezados tabla detalle
    pdf.cell(80, 8, "Especie", 1)
    pdf.cell(35, 8, "Inicio (m)", 1)
    pdf.cell(35, 8, "Fin (m)", 1)
    pdf.cell(35, 8, "Largo (m)", 1)
    pdf.ln()
    
    for index, row in df_detalle.iterrows():
        pdf.cell(80, 7, str(row['Especie']), 1)
        pdf.cell(35, 7, str(row['Inicio']), 1)
        pdf.cell(35, 7, str(row['Fin']), 1)
        pdf.cell(35, 7, str(row['Longitud (m)']), 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title("🌿 Registro de Transectas (0-50m)")

tab_registro, tab_analisis = st.tabs(["📏 Registro de Tramos", "📊 Análisis e Informe"])

# --- TAB REGISTRO ---
with tab_registro:
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2.5, 1, 1, 1])
        
        with col1:
            especie_sel = st.selectbox(
                "Seleccionar o Escribir Especie",
                options=st.session_state.lista_especies,
                index=None,
                placeholder="Busca o escribe...",
            )
            
            if especie_sel and especie_sel not in st.session_state.lista_especies:
                st.session_state.lista_especies.append(especie_sel)
                st.session_state.lista_especies.sort()
                st.rerun()

        with col2:
            sugerencia_inicio = st.session_state.datos_intervalos[-1]["Fin"] if st.session_state.datos_intervalos else 0.0
            inicio = st.number_input("Inicio (m)", min_value=0.0, max_value=50.0, value=float(sugerencia_inicio), step=0.01)
        
        with col3:
            fin = st.number_input("Fin (m)", min_value=0.0, max_value=50.0, value=float(inicio + 0.5), step=0.01)
            
        with col4:
            st.write(" ")
            if st.button("📥 Registrar", use_container_width=True):
                if especie_sel and fin > inicio:
                    st.session_state.datos_intervalos.append({
                        "Especie": especie_sel, "Inicio": inicio, "Fin": fin, "Longitud (m)": round(fin - inicio, 2)
                    })
                    st.rerun()

    if st.session_state.datos_intervalos:
        df_display = pd.DataFrame(st.session_state.datos_intervalos)
        st.dataframe(df_display.sort_values(by="Inicio", ascending=False), use_container_width=True)
        if st.button("🗑️ Eliminar último"):
            st.session_state.datos_intervalos.pop()
            st.rerun()

# --- TAB ANÁLISIS ---
with tab_analisis:
    if st.session_state.datos_intervalos:
        df_an = pd.DataFrame(st.session_state.datos_intervalos)
        cobertura = df_an.groupby("Especie")["Longitud (m)"].sum().reset_index()
        cobertura["% Cobertura"] = (cobertura["Longitud (m)"] / 50 * 100).round(2)
        
        st.subheader("Resultados de Cobertura")
        col_res, col_chart = st.columns([1, 2])
        
        with col_res:
            st.dataframe(cobertura.sort_values("% Cobertura", ascending=False), hide_index=True)
            
            # BOTÓN FINALIZAR (PDF)
            st.divider()
            pdf_data = generar_pdf(cobertura, df_an)
            st.download_button(
                label="📄 Finalizar y Descargar Informe PDF",
                data=pdf_data,
                file_name="informe_transecta.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with col_chart:
            fig = px.timeline(df_an, x_start="Inicio", x_end="Fin", y="Especie", color="Especie")
            fig.update_layout(xaxis_type='linear')
            fig.layout.xaxis.update(dict(range=[0, 50]))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos registrados.")