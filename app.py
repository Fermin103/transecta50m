import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Herbario Digital - 50m", page_icon="🌵", layout="wide")

# --- CONFIGURACIÓN ---
LARGO_TRANSECTA = 50.0  # Metros totales

ESPECIES_COMUNES = [
    "Personalizar...", 
    "Larrea tridentata (Jarilla)", 
    "Prosopis juliflora (Mezquite)", 
    "Atriplex canescens (Costilla de vaca)", 
    "Pappostipa speciosa (Coirón)", 
    "Suelo desnudo",
    "Broza/Mantarasca"
]

st.title("🌿 Monitor de Cobertura Vegetal (Transecta 50m)")

# 1. GEOLOCALIZACIÓN
with st.expander("📍 Ubicación del Punto de Inicio", expanded=False):
    loc = get_geolocation()
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        st.success(f"Coordenadas: {lat}, {lon}")
    else:
        st.info("Buscando señal GPS...")
        lat, lon = None, None

# 2. ENTRADA DE DATOS (EN METROS)
if 'datos' not in st.session_state:
    st.session_state.datos = []

with st.container():
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        opcion = st.selectbox("Selecciona Especie/Sustrato", ESPECIES_COMUNES)
        if opcion == "Personalizar...":
            especie_final = st.text_input("Nombre de especie nueva:")
        else:
            especie_final = opcion

    with col2:
        metros_ocupados = st.number_input("Distancia ocupada (m)", 0.0, LARGO_TRANSECTA, step=0.1)

    with col3:
        st.write(" ") 
        btn_add = st.button("➕ Registrar Tramo", use_container_width=True)

if btn_add and especie_final:
    st.session_state.datos.append({
        "Especie": especie_final,
        "Metros": metros_ocupados,
        "Lat": lat,
        "Lon": lon
    })

# 3. CÁLCULOS Y VISUALIZACIÓN
if st.session_state.datos:
    df = pd.DataFrame(st.session_state.datos)
    
    # Métricas principales
    metros_totales = df["Metros"].sum()
    restante = max(0.0, LARGO_TRANSECTA - metros_totales)
    porcentaje_total = (metros_totales / LARGO_TRANSECTA) * 100
    
    st.divider()
    
    # Fila de métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Metros Registrados", f"{metros_totales:.2f} m")
    m2.metric("Cobertura Total", f"{porcentaje_total:.1f} %")
    m3.metric("Faltan para los 50m", f"{restante:.2f} m")

    st.progress(min(metros_totales / LARGO_TRANSECTA, 1.0))

    # --- GRÁFICO Y TABLA ---
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.write("### Composición de la Transecta")
        # Preparar datos para el gráfico
        resumen = df.groupby("Especie")["Metros"].sum().reset_index()
        
        # Añadir el espacio restante al gráfico para que sea un círculo de 50m real
        if restante > 0:
            df_pie = pd.concat([resumen, pd.DataFrame({"Especie": ["Sin registrar"], "Metros": [restante]})])
        else:
            df_pie = resumen

        fig = px.pie(df_pie, values='Metros', names='Especie', 
                     color_discrete_sequence=px.colors.qualitative.Pastel,
                     hole=0.4)
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    with col_der:
        st.write("### Detalle por Especie")
        resumen["% Cobertura"] = (resumen["Metros"] / LARGO_TRANSECTA) * 100
        st.dataframe(resumen.style.format({"Metros": "{:.2f} m", "% Cobertura": "{:.2f} %"}), 
                     use_container_width=True, hide_index=True)

    # 4. EXPORTACIÓN
    st.divider()
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Descargar Excel (CSV)", csv, "transecta_50m.csv", "text/csv")
    
    if st.button("🗑️ Reiniciar Transecta"):
        st.session_state.datos = []
        st.rerun()