import streamlit as st
from io import BytesIO

# -----------------------------
# Configuración de la página
st.set_page_config(page_title="Buscador de Referencias OMRON", layout="wide")
# -----------------------------
st.set_page_config(
    page_title="Buscador de Referencias OMRON",
    layout="wide",
    page_icon="🔎"
)

# Nombre del Excel y columnas a usar
# -----------------------------
# Nombre del Excel y columnas
# -----------------------------
FILE_NAME = "BBDD REFERENCIAS 2025 AGOSTO.xlsx"
columnas_seleccionadas = [
    "OEE Second Item Number",
@@ -14,49 +22,69 @@
    "Stocking Type"
]

# Cargar solo columnas necesarias (rápido)
# -----------------------------
# Cargar datos
# -----------------------------
@st.cache_data
def load_data():
    return pd.read_excel(FILE_NAME, usecols=columnas_seleccionadas)

df = load_data()

# -----------------------------
# Panel lateral con filtros
# -----------------------------
with st.sidebar:
    st.header("Filtros")
    st.header("Filtros de búsqueda")
    
    oee_filter = st.text_input("OEE Second Item Number")
    catalog_filter = st.text_input("Catalog Description")
    stocking_filter = st.multiselect(
        "Stocking Type",
        options=sorted(df["Stocking Type"].dropna().unique())
    )
    
    st.markdown("---")
    query = st.text_input("🔎 Búsqueda general (OEE / Descripción)")

# Filtrado vectorizado (rápido)
# -----------------------------
# Filtrado de datos
# -----------------------------
results = df.copy()

if oee_filter:
    results = results[results["OEE Second Item Number"].astype(str).str.contains(oee_filter, case=False, na=False)]
    results = results[
        results["OEE Second Item Number"].astype(str).str.contains(oee_filter, case=False, na=False)
    ]
if catalog_filter:
    results = results[results["Catalog Description"].astype(str).str.contains(catalog_filter, case=False, na=False)]
    results = results[
        results["Catalog Description"].astype(str).str.contains(catalog_filter, case=False, na=False)
    ]
if stocking_filter:
    results = results[results["Stocking Type"].isin(stocking_filter)]
if query:
    mask_oee = results["OEE Second Item Number"].astype(str).str.contains(query, case=False, na=False)
    mask_catalog = results["Catalog Description"].astype(str).str.contains(query, case=False, na=False)
    results = results[mask_oee | mask_catalog]

# Convertir List Price ES a float y formatear como moneda
# -----------------------------
# Formatear List Price como moneda
# -----------------------------
results["List Price ES"] = pd.to_numeric(results["List Price ES"], errors='coerce')
results_display = results.copy()
results_display["List Price ES"] = results_display["List Price ES"].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "")
results_display["List Price ES"] = results_display["List Price ES"].apply(
    lambda x: f"€ {x:,.2f}" if pd.notnull(x) else ""
)

# -----------------------------
# Mostrar resultados
# -----------------------------
st.markdown(f"### 📊 Resultados encontrados: {len(results_display)}")
st.dataframe(results_display, use_container_width=True)

# Descargar resultados
# -----------------------------
# Botón de descarga de Excel
# -----------------------------
if not results.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
@@ -70,6 +98,11 @@ def load_data():
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Footer
# -----------------------------
# Footer corporativo
# -----------------------------
st.markdown("---")
st.markdown("Hecho con ❤️ por Sales Support de Omron | Rápido y fácil de usar")
