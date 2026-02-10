import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Transecta Botánica - Intervalos", layout="wide")

# --- ESTADO DE LA SESIÓN ---
if 'lista_especies' not in st.session_state:
    st.session_state.lista_especies = ["Suelo Desnudo", "Broza", "Jarilla", "Coirón", "Flechilla"]

if 'datos_intervalos' not in st.session_state:
    st.session_state.datos_intervalos = []

# --- INTERFAZ ---
st.title("🌿 Registro de Transectas por Intervalos (0-50m)")

tab_registro, tab_especies, tab_analisis = st.tabs([
    "📏 Registro de Intervalos", 
    "🌱 Gestión de Especies", 
    "📊 Análisis de Cobertura"
])

# --- SOLAPA: GESTIÓN DE ESPECIES ---
with tab_especies:
    st.header("Configuración del Catálogo")
    nueva_sp = st.text_input("Nombre de la planta / Categoría")
    if st.button("Añadir a la lista"):
        if nueva_sp and nueva_sp not in st.session_state.lista_especies:
            st.session_state.lista_especies.append(nueva_sp)
            st.rerun()
    st.write("**Especies actuales:**", ", ".join(st.session_state.lista_especies))

# --- SOLAPA: REGISTRO DE INTERVALOS ---
with tab_registro:
    st.info("Ingresa el inicio y fin de cada especie. Pueden superponerse (parches).")
    
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            especie_sel = st.selectbox("Especie/Componente", options=st.session_state.lista_especies)
        
        with col2:
            # Sugiere el fin del último registro como inicio
            ultimo_fin = st.session_state.datos_intervalos[-1]["Fin"] if st.session_state.datos_intervalos else 0.0
            inicio = st.number_input("Inicio (m)", min_value=0.0, max_value=50.0, value=float(ultimo_fin), step=0.1)
        
        with col3:
            fin = st.number_input("Fin (m)", min_value=0.0, max_value=50.0, value=float(inicio + 0.5), step=0.1)
            
        with col4:
            st.write(" ")
            if st.button("Registrar Intervalo", use_container_width=True):
                if fin > inicio:
                    longitud = fin - inicio
                    st.session_state.datos_intervalos.append({
                        "Especie": especie_sel,
                        "Inicio": inicio,
                        "Fin": fin,
                        "Longitud (m)": round(longitud, 2)
                    })
                    st.success(f"Registrado: {especie_sel} ({inicio}m - {fin}m)")
                else:
                    st.error("El 'Fin' debe ser mayor que el 'Inicio'")

    # Mostrar tabla de registros actuales
    if st.session_state.datos_intervalos:
        df_inter = pd.DataFrame(st.session_state.datos_intervalos)
        st.subheader("Registros en la Transecta")
        st.dataframe(df_inter, use_container_width=True)
        
        if st.button("🗑️ Borrar último registro"):
            st.session_state.datos_intervalos.pop()
            st.rerun()

# --- SOLAPA: ANÁLISIS ---
with tab_analisis:
    if st.session_state.datos_intervalos:
        df_analisis = pd.DataFrame(st.session_state.datos_intervalos)
        
        # Agrupar por especie para sumar longitudes totales
        cobertura = df_analisis.groupby("Especie")["Longitud (m)"].sum().reset_index()
        # Cálculo sobre el total de 50 metros
        cobertura["% Cobertura"] = (cobertura["Longitud (m)"] / 50 * 100).round(2)
        
        col_t, col_g = st.columns([1, 2])
        
        with col_t:
            st.subheader("Resumen de Cobertura")
            st.write("*(Basado en 50 metros totales)*")
            st.dataframe(cobertura, hide_index=True)
            
        with col_g:
            # Gráfico de Gantt/Líneas para ver la distribución real en la transecta
            fig = px.timeline(df_analisis, 
                              x_start="Inicio", 
                              x_end="Fin", 
                              y="Especie", 
                              color="Especie",
                              title="Distribución Espacial en la Transecta (0-50m)")
            
            # Ajuste manual para que el eje X se comporte como metros y no como fechas
            fig.update_layout(xaxis_type='linear')
            fig.layout.xaxis.update(dict(tickmode='linear', tick0=0, dtick=5, range=[0, 50]))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        csv = df_analisis.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Datos Completos", csv, "transecta_intervalos.csv", "text/csv")
    else:
        st.warning("No hay datos registrados.")