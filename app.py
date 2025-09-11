import pandas as pd
import streamlit as st
from io import BytesIO

# -----------------------------
# Configuración de la página
# -----------------------------
st.set_page_config(
    page_title="Buscador de Referencias OMRON",
    layout="wide",
    page_icon="Logo-Omron-500x283 - Copy.jpg"
)

st.image("Logo-Omron-500x283 - Copy.jpg", width=200)  # Miniatura más pequeña

# -----------------------------
# Nombres de archivos y columnas
# -----------------------------
REF_FILE = "BBDD REFERENCIAS 2025 AGOSTO.xlsx"
STOCK_FILE = "BBDD Stocks.xlsx"

ref_cols = [
    "Item Code",
    "OEE Second Item Number",
    "Catalog Description",
    "Item Long Description",
    "List Price ES",
    "Stocking Type",
    "<Primary Image.|Node|.Deep Link - 160px>"
]

stock_cols = [
    "OC Product Code",
    "Quantity Immediately Available",
    "Quantity Future Available"
]

# -----------------------------
# Cargar datos optimizado
# -----------------------------
@st.cache_data
def load_data():
    df_ref = pd.read_excel(REF_FILE, usecols=ref_cols, dtype=str)
    df_stock = pd.read_excel(STOCK_FILE, usecols=stock_cols, dtype=str)

    df_stock.rename(columns={
        "Quantity Immediately Available": "Qty Immediately",
        "Quantity Future Available": "Qty Future"
    }, inplace=True)

    df_merged = df_ref.merge(
        df_stock,
        how="left",
        left_on="Item Code",
        right_on="OC Product Code"
    )
    df_merged.drop(columns=["OC Product Code"], inplace=True)

    df_merged["List Price ES"] = pd.to_numeric(df_merged["List Price ES"], errors='coerce')
    return df_merged

df = load_data()

# -----------------------------
# Panel lateral con filtros
# -----------------------------
with st.sidebar:
    st.header("Filtros de búsqueda")
    
    oee_filter = st.text_input("OEE Second Item Number")
    catalog_filter = st.text_input("Catalog Description")
    long_desc_filter = st.text_input("Item Long Description")
    stocking_filter = st.multiselect(
        "Stocking Type",
        options=sorted(df["Stocking Type"].dropna().unique())
    )
    
    st.markdown("---")
    query = st.text_input("🔎 Búsqueda general (OEE / Catalog / Long Description)")

# -----------------------------
# Filtrado de datos
# -----------------------------
results = df.copy()

def str_contains(col, val):
    return col.fillna("").astype(str).str.contains(val, case=False, na=False)

if oee_filter:
    results = results[str_contains(results["OEE Second Item Number"], oee_filter)]
if catalog_filter:
    results = results[str_contains(results["Catalog Description"], catalog_filter)]
if long_desc_filter:
    results = results[str_contains(results["Item Long Description"], long_desc_filter)]
if stocking_filter:
    results = results[results["Stocking Type"].isin(stocking_filter)]

# Búsqueda general
if query:
    mask_oee = str_contains(results["OEE Second Item Number"], query)
    mask_catalog = str_contains(results["Catalog Description"], query)
    mask_long_desc = str_contains(results["Item Long Description"], query)
    results = results[mask_oee | mask_catalog | mask_long_desc]

# -----------------------------
# Mostrar resultados y dropdown
# -----------------------------
st.markdown(f"### 📊 Resultados encontrados: {len(results)}")

options = results["Item Code"].tolist()
selected_item_code = st.selectbox("Selecciona un Item Code para ver detalles", options)

if selected_item_code:
    selected_item = results[results["Item Code"] == selected_item_code].iloc[0]

    st.markdown("### Detalles del Item")
    st.write(f"**OEE Second Item Number:** {selected_item['OEE Second Item Number']}")
    st.write(f"**Catalog Description:** {selected_item['Catalog Description']}")
    st.write(f"**Item Long Description:** {selected_item['Item Long Description']}")
    st.write(f"**List Price ES:** € {selected_item['List Price ES']:,.2f}")
    st.write(f"**Stocking Type:** {selected_item['Stocking Type']}")
    st.write(f"**Qty Immediately:** {selected_item['Qty Immediately']}")
    st.write(f"**Qty Future:** {selected_item['Qty Future']}")

    image_url = selected_item.get("<Primary Image.|Node|.Deep Link - 160px>")
    if pd.notnull(image_url) and image_url != "":
        st.image(image_url, caption="Imagen del Item", width=200)  # Miniatura más pequeña

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
