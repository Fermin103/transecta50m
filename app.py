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
        "Senecio filaginoides", "Senna aphylla", "Suelo Desnudo", "Broza"
    ])

if 'datos_intervalos' not in st.session_state:
    st.session_state.datos_intervalos = []

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf(df_resumen, df_detalle):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Informe de Transecta Botánica (50m)", ln=True, align='C')
    pdf.ln(10)
    
    # Resumen
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Resumen de Cobertura", ln=True)
    pdf.set_font("helvetica", "", 10)
    
    for _, row in df_resumen.iterrows():
        linea = f"{row['Especie']}: {row['Longitud (m)']}m ({row['% Cobertura']}%)"
        pdf.cell(0, 8, linea, ln=True)
        
    pdf.ln(10)
    
    # Detalle
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Detalle de Tramos", ln=True)
    pdf.set_font("helvetica", "", 9)
    
    for _, row in df_detalle.iterrows():
        linea_det = f"Desde {row['Inicio']}m hasta {row['Fin']}m: {row['Especie']}"
        pdf.cell(0, 7, linea_det, ln=True)
        
    return pdf.output()

# --- INTERFAZ ---
st.title("🌿 Registro de Transectas (0-50m)")

tab_reg, tab_an = st.tabs(["📏 Registro", "📊 Informe"])

with tab_reg:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
        with c1:
            esp = st.selectbox("Especie", options=st.session_state.lista_especies, index=None, placeholder="Escribe o busca...")
            if esp and esp not in st.session_state.lista_especies:
                st.session_state.lista_especies.append(esp)
                st.session_state.lista_especies.sort()
                st.rerun()
        with c2:
            sug = st.session_state.datos_intervalos[-1]["Fin"] if st.session_state.datos_intervalos else 0.0
            ini = st.number_input("Inicio (m)", min_value=0.0, max_value=50.0, value=float(sug))
        with c3:
            fin = st.number_input("Fin (m)", min_value=0.0, max_value=50.0, value=float(ini + 0.1))
        with c4:
            st.write(" ")
            if st.button("📥 Registrar"):
                if esp and fin > ini:
                    st.session_state.datos_intervalos.append({"Especie": esp, "Inicio": ini, "Fin": fin, "Longitud (m)": round(fin-ini, 2)})
                    st.rerun()

    if st.session_state.datos_intervalos:
        st.dataframe(pd.DataFrame(st.session_state.datos_intervalos).sort_values(by="Inicio", ascending=False))
        if st.button("🗑️ Borrar último"):
            st.session_state.datos_intervalos.pop()
            st.rerun()

with tab_an:
    if st.session_state.datos_intervalos:
        df = pd.DataFrame(st.session_state.datos_intervalos)
        res = df.groupby("Especie")["Longitud (m)"].sum().reset_index()
        res["% Cobertura"] = (res["Longitud (m)"] / 50 * 100).round(2)
        
        col_r, col_c = st.columns([1, 2])
        with col_r:
            st.dataframe(res.sort_values("% Cobertura", ascending=False), hide_index=True)
            if st.button("🔨 Preparar PDF"):
                pdf_out = generar_pdf(res, df)
                st.download_button("📄 Descargar PDF", data=pdf_out, file_name="transecta.pdf")
        with col_c:
            fig = px.timeline(df, x_start="Inicio", x_end="Fin", y="Especie", color="Especie")
            fig.update_layout(xaxis_type='linear')
            st.plotly_chart(fig)
    else:
        st.warning("Sin datos.")