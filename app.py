import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_js_eval import streamlit_js_eval

# Configuración de página
st.set_page_config(page_title="Transecta Botánica Pro", layout="wide")

# --- GESTIÓN DE ESPECIES EN SESIÓN ---
if 'lista_especies' not in st.session_state:
    # Especies iniciales basadas en tu Excel
    st.session_state.lista_especies = ["Suelo Desnudo", "Jarilla", "Coirón", "Flechilla", "Tomillo"]

if 'datos_transecta' not in st.session_state:
    st.session_state.datos_transecta = []

# --- BARRA LATERAL (Configuración y Nueva Especie) ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Agregar nueva especie
    st.subheader("➕ Añadir Especie")
    nueva_sp = st.text_input("Nombre de la especie")
    if st.button("Registrar Especie"):
        if nueva_sp and nueva_sp not in st.session_state.lista_especies:
            st.session_state.lista_especies.append(nueva_sp)
            st.success(f"{nueva_sp} añadida!")
        else:
            st.warning("La especie ya existe o el nombre está vacío.")

    st.divider()
    if st.button("🗑️ Borrar todo y empezar de nuevo"):
        st.session_state.datos_transecta = []
        st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("🌿 Registro de Transectas con Parches")
st.info("Puedes seleccionar varias especies si están superpuestas en el mismo punto.")

# Formulario de entrada
with st.container(border=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        punto = st.number_input("Punto/Distancia (m)", min_value=0.0, step=0.1, value=float(len(st.session_state.datos_transecta)))
    
    with col2:
        # Aquí está el cambio clave: multiselect para parches superpuestos
        especies_seleccionadas = st.multiselect(
            "Especies en este punto (Parche)", 
            options=st.session_state.lista_especies,
            default=["Suelo Desnudo"] if not st.session_state.lista_especies else None
        )
    
    with col3:
        st.write(" ")
        if st.button("📍 Registrar Punto", use_container_width=True):
            if especies_seleccionadas:
                # Guardamos como una cadena separada por comas para el DataFrame
                st.session_state.datos_transecta.append({
                    "Punto": punto,
                    "Especies": ", ".join(especies_seleccionadas),
                    "Cant_Especies": len(especies_seleccionadas)
                })
                st.rerun()

# --- VISUALIZACIÓN Y CÁLCULOS ---
if st.session_state.datos_transecta:
    df = pd.DataFrame(st.session_state.datos_transecta)
    
    tab1, tab2 = st.tabs(["📊 Análisis de Cobertura", "📋 Datos Crudos"])
    
    with tab1:
        # Calcular frecuencia de cada especie individualmente aunque estén en parches
        todas_las_apariciones = []
        for registro in st.session_state.datos_transecta:
            esps = registro["Especies"].split(", ")
            todas_las_apariciones.extend(esps)
        
        df_counts = pd.Series(todas_las_apariciones).value_counts().reset_index()
        df_counts.columns = ['Especie', 'Frecuencia']
        df_counts['% Cobertura'] = (df_counts['Frecuencia'] / len(df)) * 100

        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Tabla de Cobertura")
            st.dataframe(df_counts, hide_index=True, use_container_width=True)
            
        with col_b:
            st.subheader("Gráfico de Composición")
            fig = px.pie(df_counts, values='Frecuencia', names='Especie', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Registro detallado de la transecta")
        st.dataframe(df, use_container_width=True)
        
        # Opción para descargar
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar CSV", csv, "transecta_botanica.csv", "text/csv")
else:
    st.write("Aún no hay datos registrados. Comienza añadiendo puntos arriba.")