import pandas as pd
import streamlit as st
from io import BytesIO

# -----------------------------
# Autenticación
# -----------------------------
ST_USERNAME = "Frodo.Baggins"
ST_PASSWORD = "M0rd0r!R1ng$2025"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if username == ST_USERNAME and password == ST_PASSWORD:
                st.session_state.authenticated = True
            else:
                st.error("Usuario o contraseña incorrectos")
        return False
    return True

if not check_password():
    st.stop()

# -----------------------------
# Configuración de la página
# -----------------------------
st.set_page_config(
    page_title="Buscador de Referencias OMRON",
    layout="wide",
    page_icon="Logo-Omron-500x283 - Copy.jpg"
)

# Icono dentro de la app
st.image("Logo-Omron-500x283 - Copy.jpg", width=150)

# -----------------------------
# Archivos y columnas
# -----------------------------
FILE_NAME = "BBDD REFERENCIAS 2025 AGOSTO.xlsx"
STOCK_FILE = "BBDD Stocks.xlsx"

columnas_seleccionadas = [
    "OEE Second Item Number",
    "Catalog Description",
    "Item Long Description",
    "List Price ES",
    "Stocking Type",
    "<Primary Image.|Node|.Deep Link - 160px>"
]

stock_columns = [
    "OC Product Code",
    "Quantity Immediately Available",
    "Quantity Future Available"
]

# -----------------------------
# Cargar datos
# -----------------------------
@st.cache_data
def load_data():
    df_ref = pd.read_excel(FILE_NAME, usecols=columnas_seleccionadas)
    df_stock = pd.read_excel(STOCK_FILE, usecols=stock_columns)

    df_stock.rename(columns={
        "Quantity Immediately Available": "Qty Immediately",
        "Quantity Future Available": "Qty Future"
    }, inplace=True)

    df_merged = df_ref.merge(
        df_stock,
        how="left",
        left_on="OEE Second Item Number",
        right_on="OC Product Code"
    )

    df_merged.drop(columns=["OC Product Code"], inplace=True)
    return df_merged

df = load_data()

# -----------------------------
# Panel lateral
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
    query = st.text_input("🔎 Búsqueda general (OEE / Descripción / Item Long Description)")

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
    mask_long = results["Item Long Description"].astype(str).str.contains(query, case=False, na=False)
    results = results[mask_oee | mask_catalog | mask_long]

# -----------------------------
# Formatear List Price
# -----------------------------
results["List Price ES"] = pd.to_numeric(results["List Price ES"], errors='coerce')
results_display = results.copy()
results_display["List Price ES"] = results_display["List Price ES"].apply(
    lambda x: f"€ {x:,.2f}" if pd.notnull(x) else ""
)

# -----------------------------
# Selección de fila
# -----------------------------
st.markdown(f"### 📊 Resultados encontrados: {len(results_display)}")
selected_item = st.selectbox("Selecciona un item para ver detalles", results_display["OEE Second Item Number"].astype(str))

if selected_item:
    item_data = results_display[results_display["OEE Second Item Number"].astype(str) == selected_item].iloc[0]
    st.write("**OEE Second Item Number:**", item_data["OEE Second Item Number"])
    st.write("**Catalog Description:**", item_data["Catalog Description"])
    st.write("**Item Long Description:**", item_data["Item Long Description"])
    st.write("**List Price ES:**", item_data["List Price ES"])
    st.write("**Stocking Type:**", item_data["Stocking Type"])
    st.write("**Qty Immediately:**", item_data.get("Qty Immediately", "N/A"))
    st.write("**Qty Future:**", item_data.get("Qty Future", "N/A"))

    # Imagen más pequeña
    if pd.notnull(item_data["<Primary Image.|Node|.Deep Link - 160px>"]):
        st.image(item_data["<Primary Image.|Node|.Deep Link - 160px>"], width=200)

# -----------------------------
# Mostrar tabla completa
# -----------------------------
st.dataframe(results_display, use_container_width=True)

# -----------------------------
# Botón de descarga
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
st.markdown("Hecho con ❤️ por **Sales Support de Omron** | Rápido, fácil y corporativo")
