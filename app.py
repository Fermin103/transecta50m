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

# --- LÓGICA DE RELLENO DE SUELO DESNUDO ---
def rellenar_suelo_desnudo(datos):
    if not datos:
        return [{"Especie": "Suelo Desnudo", "Inicio": 0.0, "Fin": 50.0, "Longitud (m)": 50.0}]
    
    # Ordenar todos los intervalos por inicio
    df = pd.DataFrame(datos).sort_values(by="Inicio")
    
    # Encontrar la unión de todos los intervalos ocupados (independientemente de la especie)
    intervalos_ocupados = []
    for _, row in df.iterrows():
        inicio, fin = row['Inicio'], row['Fin']
        if not intervalos_ocupados or inicio > intervalos_ocupados[-1][1]:
            intervalos_ocupados.append([inicio, fin])
        else:
            intervalos_ocupados[-1][1] = max(intervalos_ocupados[-1][1], fin)
    
    # Crear intervalos de "Suelo Desnudo" en los huecos
    datos_completos = list(datos)
    cursor = 0.0
    for inicio_occ, fin_occ in intervalos_ocupados:
        if inicio_occ > cursor:
            datos_completos.append({
                "Especie": "Suelo Desnudo",
                "Inicio": cursor,
                "Fin": inicio_occ,
                "Longitud (m)": round(inicio_occ - cursor, 2),
                "Automatico": True
            })
        cursor = max(cursor, fin_occ)
    
    if cursor < 50.0:
        datos_completos.append({
            "Especie": "Suelo Desnudo",
            "Inicio": cursor,
            "Fin": 50.0,
            "Longitud (m)": round(50.0 - cursor, 2),
            "Automatico": True
        })
        
    return datos_completos

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf(df_resumen, df_detalle):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Informe de Transecta Botanica (50m)", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Resumen de Cobertura", ln=True)
    pdf.set_font("helvetica", "", 10)
    
    for _, row in df_resumen.iterrows():
        linea = f"{row['Especie']}: {row['Longitud (m)']}m ({row['% Cobertura']}%) - Apariciones: {row['Nº de Apariciones']}"
        pdf.cell(0, 8, linea.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Detalle de Tramos", ln=True)
    pdf.set_font("helvetica", "", 9)
    
    for _, row in df_detalle.iterrows():
        linea_det = f"Desde {row['Inicio']}m hasta {row['Fin']}m: {row['Especie']}"
        pdf.cell(0, 7, linea_det.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        
    # El método output() en fpdf2 devuelve bytes por defecto o se puede forzar
    return bytes(pdf.output())

# --- INTERFAZ ---
st.title("🌿 Registro de Transectas (0-50m)")

ultimo_punto_reg = max([d['Fin'] for d in st.session_state.datos_intervalos]) if st.session_state.datos_intervalos else 0.0

tab_reg, tab_an = st.tabs(["📏 Registro de Campo", "📊 Informe y Análisis"])

with tab_reg:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2.5, 1, 1, 1])
        with c1:
            esp = st.selectbox("Especie", options=st.session_state.lista_especies, index=None, placeholder="Busca o escribe...")
            if esp and esp not in st.session_state.lista_especies:
                st.session_state.lista_especies.append(esp)
                st.session_state.lista_especies.sort()
                st.rerun()
        with c2:
            ini = st.number_input("Inicio (m)", min_value=0.0, max_value=50.0, value=float(ultimo_punto_reg), step=0.01)
        with c3:
            val_fin = float(ini + 0.1)
            if val_fin > 50.0: val_fin = 50.0
            fin = st.number_input("Fin (m)", min_value=0.0, max_value=50.0, value=val_fin, step=0.01)
        with c4:
            st.write(" ")
            if st.button("📥 Registrar", use_container_width=True):
                if esp and fin > ini:
                    st.session_state.datos_intervalos.append({"Especie": esp, "Inicio": ini, "Fin": fin, "Longitud (m)": round(fin-ini, 2)})
                    st.rerun()

    if st.session_state.datos_intervalos:
        st.subheader("Tramos ingresados manualmente")
        st.dataframe(pd.DataFrame(st.session_state.datos_intervalos).sort_values(by="Inicio", ascending=False), use_container_width=True)
        if st.button("🗑️ Borrar último"):
            st.session_state.datos_intervalos.pop()
            st.rerun()

with tab_an:
    # Aplicar relleno automático para el análisis
    datos_completos = rellenar_suelo_desnudo(st.session_state.datos_intervalos)
    
    if datos_completos:
        df_completo = pd.DataFrame(datos_completos)
        
        # 1. Tabla de Resumen
        resumen = df_completo.groupby("Especie").agg(
            Longitud_Total=("Longitud (m)", "sum"),
            Apariciones=("Especie", "count")
        ).reset_index()
        
        resumen.columns = ["Especie", "Longitud (m)", "Nº de Apariciones"]
        resumen["% Cobertura"] = (resumen["Longitud (m)"] / 50 * 100).round(2)
        
        # Ordenar por número de apariciones (mayor a menor)
        resumen = resumen.sort_values(by="Nº de Apariciones", ascending=False)
        
        st.subheader("📋 Resumen de la Transecta (0-50m)")
        st.dataframe(resumen, hide_index=True, use_container_width=True)
        
        # 2. Gráficos
        col_bar, col_pie = st.columns(2)
        
        with col_bar:
            st.write("**Cobertura por Especie (%)**")
            fig_bar = px.bar(resumen, x="Especie", y="% Cobertura", color="Especie", text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_pie:
            st.write("**Cobertura Vegetal vs Suelo Desnudo**")
            # Cálculo de cobertura vegetal total (unión de todo lo que no es suelo desnudo)
            long_suelo = resumen[resumen["Especie"] == "Suelo Desnudo"]["Longitud (m)"].sum()
            long_veg = 50.0 - long_suelo
            
            pie_data = pd.DataFrame({
                "Categoría": ["Cobertura Vegetal", "Suelo Desnudo"],
                "Porcentaje": [round((long_veg/50)*100, 2), round((long_suelo/50)*100, 2)]
            })
            
            fig_pie = px.pie(pie_data, values="Porcentaje", names="Categoría", 
                             color="Categoría", color_discrete_map={"Cobertura Vegetal":"green", "Suelo Desnudo":"brown"})
            st.plotly_chart(fig_pie, use_container_width=True)

        # 3. Descarga de PDF
        st.divider()
        if st.button("🔨 Generar y Descargar Informe PDF", use_container_width=True):
            try:
                pdf_bytes = generar_pdf(resumen, df_completo.sort_values(by="Inicio"))
                st.download_button(
                    label="⬇️ Haz clic aquí para descargar",
                    data=pdf_bytes,
                    file_name="informe_transecta.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error al crear el PDF: {e}")
                
        # 4. Mapa visual de la transecta
        st.subheader("🗺️ Mapa de Distribución")
        fig_map = px.timeline(df_completo, x_start="Inicio", x_end="Fin", y="Especie", color="Especie")
        fig_map.update_layout(xaxis_type='linear', xaxis=dict(range=[0, 50], title="Metros"))
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No hay datos para analizar.")