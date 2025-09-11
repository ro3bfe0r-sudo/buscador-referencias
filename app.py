import pandas as pd
import streamlit as st
from io import BytesIO

# -----------------------------
# Configuración de la página (antes de cualquier input)
# -----------------------------
st.set_page_config(
    page_title="Buscador de Referencias OMRON",
    layout="wide",
    page_icon="Logo-Omron-500x283 - Copy.jpg"
)

# -----------------------------
# Autenticación
# -----------------------------
ST_USERNAME = "Frodo.Baggins"
ST_PASSWORD = "M0rd0r!R1ng$2025"

def check_password():
    def password_entered():
        if (st.session_state["username"] == ST_USERNAME and
            st.session_state["password"] == ST_PASSWORD):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        if st.session_state.get("password_correct") == False and "password" in st.session_state:
            st.error("Usuario o contraseña incorrectos")
        return False
    else:
        return True

if not check_password():
    st.stop()

# -----------------------------
# Archivos y columnas
# -----------------------------
REF_FILE = "BBDD REFERENCIAS 2025 AGOSTO.xlsx"
STOCK_FILE = "BBDD Stocks.xlsx"

ref_columns = [
    "Item Code",
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
    df_ref = pd.read_excel(REF_FILE, usecols=ref_columns)
    df_stock = pd.read_excel(STOCK_FILE, usecols=stock_columns)

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
    return df_merged

df = load_data()

# -----------------------------
# Panel lateral
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
    query = st.text_input("🔎 Búsqueda general (OEE / Catalog / Long Desc)")

# -----------------------------
# Filtrado de datos
# -----------------------------
results = df.copy()

if oee_filter:
    results = results[results["OEE Second Item Number"].astype(str).str.contains(oee_filter, case=False, na=False)]
if catalog_filter:
    results = results[results["Catalog Description"].astype(str).str.contains(catalog_filter, case=False, na=False)]
if long_desc_filter:
    results = results[results["Item Long Description"].astype(str).str.contains(long_desc_filter, case=False, na=False)]
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
# Mostrar resultados y selección
# -----------------------------
st.markdown(f"### 📊 Resultados encontrados: {len(results_display)}")

selected_item_code = st.selectbox(
    "Selecciona un item para ver detalles",
    options=results_display["Item Code"].tolist()
)

if selected_item_code:
    item = results_display[results_display["Item Code"] == selected_item_code].iloc[0]
    st.write(f"**OEE Second Item Number:** {item['OEE Second Item Number']}")
    st.write(f"**Catalog Description:** {item['Catalog Description']}")
    st.write(f"**Item Long Description:** {item['Item Long Description']}")
    st.write(f"**Stocking Type:** {item['Stocking Type']}")
    st.write(f"**Qty Immediately:** {item['Qty Immediately']}")
    st.write(f"**Qty Future:** {item['Qty Future']}")
    st.write(f"**List Price ES:** {item['List Price ES']}")
    
    # Imagen más pequeña
    if pd.notna(item["<Primary Image.|Node|.Deep Link - 160px>"]):
        st.image(item["<Primary Image.|Node|.Deep Link - 160px>"], width=200)

# -----------------------------
# Descargar Excel
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
# Footer
# -----------------------------
st.markdown("---")
st.markdown(
    "Hecho con ❤️ por **Sales Support de Omron** | Rápido, fácil y corporativo"
)
