import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Transecta Botánica Pro - 50m", layout="wide")

# --- ESTADO DE LA SESIÓN (Base de datos interna) ---
# Precarga de especies detectadas en tus archivos Excel
if 'lista_especies' not in st.session_state:
    st.session_state.lista_especies = sorted([
        "Suelo Desnudo", "Broza", "Piedra", "Musgo", "Costra Biológica",
        "Chuquiraga erinacea (Jarilla)", "Nassauvia axillaris", 
        "Stipa tenuis (Flechiilla)", "Stipa speciosa (Coirón)", 
        "Poa ligularis", "Grindelia chiloensis", "Senecio filaginoides",
        "Mulinum spinosum", "Larrea divaricata", "Adesmia sp."
    ])

if 'datos_intervalos' not in st.session_state:
    st.session_state.datos_intervalos = []

# --- INTERFAZ PRINCIPAL ---
st.title("🌿 Registro de Transectas Botánicas (0-50m)")
st.markdown("Sistema profesional para el registro de parches y estratos superpuestos.")

tab_registro, tab_especies, tab_analisis = st.tabs([
    "📏 Registro de Intervalos", 
    "🌱 Gestión de Especies/Componentes", 
    "📊 Análisis de Cobertura"
])

# --- SOLAPA: GESTIÓN DE ESPECIES ---
with tab_especies:
    st.header("Configuración del Catálogo de Campo")
    st.info("Agrega aquí cualquier especie que no esté en la lista inicial.")
    
    col_add, col_list = st.columns([1, 1])
    with col_add:
        nueva_sp = st.text_input("Nombre de la nueva especie o componente")
        if st.button("➕ Registrar en el catálogo"):
            if nueva_sp and nueva_sp not in st.session_state.lista_especies:
                st.session_state.lista_especies.append(nueva_sp)
                st.session_state.lista_especies.sort()
                st.success(f"'{nueva_sp}' añadida al catálogo.")
                st.rerun()
    
    with col_list:
        st.subheader("Catálogo actual")
        st.write(", ".join(st.session_state.lista_especies))

# --- SOLAPA: REGISTRO DE INTERVALOS ---
with tab_registro:
    st.subheader("Entrada de Datos por Tramos")
    
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        
        with c1:
            especie_sel = st.selectbox("Seleccionar Especie o Componente", 
                                       options=st.session_state.lista_especies)
        
        with c2:
            # Sugiere el último fin como nuevo inicio para agilizar la carga lineal
            sugerencia_inicio = st.session_state.datos_intervalos[-1]["Fin"] if st.session_state.datos_intervalos else 0.0
            inicio = st.number_input("Inicio (m)", min_value=0.0, max_value=50.0, 
                                     value=float(sugerencia_inicio), step=0.01, format="%.2f")
        
        with c3:
            fin = st.number_input("Fin (m)", min_value=0.0, max_value=50.0, 
                                   value=float(inicio + 0.10), step=0.01, format="%.2f")
            
        with c4:
            st.write(" ")
            if st.button("📥 Registrar Tramo", use_container_width=True):
                if fin > inicio:
                    st.session_state.datos_intervalos.append({
                        "Especie": especie_sel,
                        "Inicio": inicio,
                        "Fin": fin,
                        "Longitud (m)": round(fin - inicio, 2)
                    })
                    st.toast(f"Registrado {especie_sel}")
                else:
                    st.error("El Fin debe ser mayor al Inicio")

    # Tabla dinámica de registros
    if st.session_state.datos_intervalos:
        df_display = pd.DataFrame(st.session_state.datos_intervalos)
        st.dataframe(df_display.sort_values(by="Inicio", ascending=False), use_container_width=True)
        
        if st.button("🗑️ Eliminar último registro"):
            st.session_state.datos_intervalos.pop()
            st.rerun()

# --- SOLAPA: ANÁLISIS ---
with tab_analisis:
    if st.session_state.datos_intervalos:
        df_an = pd.DataFrame(st.session_state.datos_intervalos)
        
        # Cálculo de cobertura real (Suma de longitudes / 50m)
        cobertura = df_an.groupby("Especie")["Longitud (m)"].sum().reset_index()
        cobertura["% Cobertura"] = (cobertura["Longitud (m)"] / 50 * 100).round(2)
        
        col_res, col_chart = st.columns([1, 2])
        
        with col_res:
            st.subheader("Resumen Estadístico")
            st.dataframe(cobertura.sort_values("% Cobertura", ascending=False), hide_index=True)
            
        with col_chart:
            # Gráfico de distribución espacial (estilo Gantt)
            fig = px.timeline(df_an, x_start="Inicio", x_end="Fin", y="Especie", color="Especie",
                              title="Distribución en la Transecta (0-50m)")
            fig.update_layout(xaxis_type='linear')
            fig.layout.xaxis.update(dict(range=[0, 50], dtick=5, title="Metros"))
            st.plotly_chart(fig, use_container_width=True)

        # Exportación
        st.divider()
        csv = df_an.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Descargar Datos (CSV)", csv, "transecta_final.csv", "text/csv")
    else:
        st.warning("No hay datos registrados para analizar.")