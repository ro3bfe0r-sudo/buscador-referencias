import pandas as pd
import streamlit as st
from io import BytesIO

# -----------------------------
# Configuración de la página
# -----------------------------
st.set_page_config(
    page_title="Buscador de Referencias OMRON",
    layout="wide",
    page_icon="🔎"
)

# -----------------------------
# Estilo personalizado (fondo azul)
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0072C6;  /* Azul corporativo */
        color: white;
    }
    .stSidebar {
        background-color: #005EA3;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Logo Omron en header
# -----------------------------
st.markdown(
    """
    <div style="display:flex; justify-content: space-between; align-items:center;">
        <h1>Buscador de Referencias OMRON</h1>
        <img src="https://assets.omron.eu/images/omron-logo.png" width="120">
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Nombre del Excel y columnas
# -----------------------------
FILE_NAME = "BBDD REFERENCIAS 2025 AGOSTO.xlsx"
columnas_seleccionadas = [
    "OEE Second Item Number",
    "Catalog Description",
    "List Price ES",
    "Stocking Type",
    "Primary Image.|Node|.Deep Link - 160px"
]

# -----------------------------
# Cargar datos (rápido)
# -----------------------------
@st.cache_data
def load_data():
    return pd.read_excel(FILE_NAME, usecols=columnas_seleccionadas)

df = load_data()

# -----------------------------
# Panel lateral con filtros
# -----------------------------
with st.sidebar:
    st.header("Filtros de búsqueda")
    
    oee_filter = st.text_input("OEE Second Item Number")
    catalog_filter = st.text_input("Catalog Description")
    stocking_filter = st.multiselect(
        "Stocking Type",
        options=sorted(df["Stocking Type"].dropna().unique())
    )
    
    st.markdown("---")
    query = st.text_input("🔎 Búsqueda general (OEE / Descripción)")

# -----------------------------
# Filtrado de datos
# -----------------------------
results = df.copy()

if oee_filter:
    results = results[results["OEE Second Item Number"].astype(str).str.contains(oee_filter, case=False, na=False)]
if catalog_filter:
    results = results[results["Catalog Description"].astype(str).str.contains(catalog_filter, case=False, na=False)]
if stocking_filter:
    results = results[results["Stocking Type"].isin(stocking_filter)]
if query:
    mask_oee = results["OEE Second Item Number"].astype(str).str.contains(query, case=False, na=False)
    mask_catalog = results["Catalog Description"].astype(str).str.contains(query, case=False, na=False)
    results = results[mask_oee | mask_catalog]

# -----------------------------
# Formatear List Price como moneda
# -----------------------------
results["List Price ES"] = pd.to_numeric(results["List Price ES"], errors='coerce')
results_display = results.copy()
results_display["List Price ES"] = results_display["List Price ES"].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "")

# -----------------------------
# Mostrar imágenes como thumbnails
# -----------------------------
if "Primary Image.|Node|.Deep Link - 160px" in results_display.columns:
    results_display["Image"] = results_display["Primary Image.|Node|.Deep Link - 160px"].apply(
        lambda url: f'![img]({url})' if pd.notnull(url) else ""
    )

# -----------------------------
# Mostrar resultados
# -----------------------------
st.markdown(f"### 📊 Resultados encontrados: {len(results_display)}")
if results_display.empty:
    st.info("No se encontraron resultados para los filtros aplicados.")
else:
    st.dataframe(results_display, use_container_width=True)

# -----------------------------
# Botón de descarga de Excel
# -----------------------------
if not results.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        results.to_excel(writer, index=False, sheet_name='Resultados')
    output.seek(0)
    st.download_button(
        label="📥 Descargar resultados filtrados",
        data=output,
        file_name="Resultados_Busqueda.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -----------------------------
# Footer corporativo
# -----------------------------
st.markdown("---")
st.markdown(
    "Hecho con ❤️ por **Sales Support de Omron** | Rápido, fácil y corporativo"
)

