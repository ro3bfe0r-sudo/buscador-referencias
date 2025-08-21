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
# CSS para estilo corporativo
# -----------------------------
st.markdown("""
    <style>
    body {
        background-color: #0072C6;  /* azul corporativo */
        color: white;
    }
    .stDataFrame tbody tr th {color: black;}
    .stDataFrame tbody tr td {color: black;}
    .stDataFrame thead tr th {color: black;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# Nombre del Excel y columnas
# -----------------------------
FILE_NAME = "BBDD REFERENCIAS 2025 AGOSTO.xlsx"
columnas_seleccionadas = [
    "OEE Second Item Number",
    "Catalog Description",
    "List Price ES",
    "Stocking Type",
    "Primary Image Deep Link"
]

# -----------------------------
# Cargar datos (rápido)
# -----------------------------
@st.cache_data
def load_data():
    return pd.read_excel(FILE_NAME, usecols=columnas_seleccionadas)

df = load_data()

# -----------------------------
# Cabecera con logo
# -----------------------------
col1, col2 = st.columns([1,6])
with col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Omron_logo.svg/2560px-Omron_logo.svg.png", width=120)
with col2:
    st.markdown("## Buscador de Referencias OMRON")

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
    results = results[
        results["OEE Second Item Number"].astype(str).str.contains(oee_filter, case=False, na=False)
    ]
if catalog_filter:
    results = results[
        results["Catalog Description"].astype(str).str.contains(catalog_filter, case=False, na=False)
    ]
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
results_display["List Price ES"] = results_display["List Price ES"].apply(
    lambda x: f"€ {x:,.2f}" if pd.notnull(x) else ""
)

# -----------------------------
# Mostrar resultados con imágenes
# -----------------------------
st.markdown(f"### 📊 Resultados encontrados: {len(results_display)}")
if results_display.empty:
    st.info("No se encontraron resultados para los filtros aplicados.")
else:
    for idx, row in results_display.iterrows():
        col1, col2, col3 = st.columns([1,3,2])
        with col1:
            if pd.notnull(row["Primary Image Deep Link"]):
                st.image(row["Primary Image Deep Link"], width=100)
        with col2:
            st.markdown(f"**{row['Catalog Description']}**")
            st.markdown(f"OEE: {row['OEE Second Item Number']}")
        with col3:
            st.markdown(f"Stocking Type: {row['Stocking Type']}")
            st.markdown(f"Price: {row['List Price ES']}")

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



