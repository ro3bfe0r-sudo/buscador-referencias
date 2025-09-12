import pandas as pd
import streamlit as st
from io import BytesIO

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
# Configuración de la página
# -----------------------------
st.set_page_config(
    page_title="Buscador de Referencias OMRON",
    layout="wide",
    page_icon="Logo-Omron-500x283 - Copy.jpg"
)

st.image("Logo-Omron-500x283 - Copy.jpg", width=150)

# -----------------------------
# Archivos y columnas
# -----------------------------
REF_FILE = "BBDD REFERENCIAS 2025 AGOSTO.xlsx"
STOCK_FILE = "BBDD Stocks.xlsx"
NSC_FILE = "NSC Discount Limit Report for NSC Admin-2025-09-11-14-43-13.xlsx"

ref_columns = [
    "Item Code",
    "OEE Second Item Number",
    "Catalog Description",
    "Item Long Description",
    "List Price ES",
    "Stocking Type",
    "<Primary Image.|Node|.Deep Link - 160px>",
    "<Discount Link.|Node|.Discount - Level 3 - Family>"
]

stock_columns = [
    "OC Product Code",
    "Quantity Immediately Available",
    "Quantity Future Available"
]

nsc_columns = ["Discount Group", "Discount Group Description", "Sales person Limit"]

# -----------------------------
# Cargar datos
# -----------------------------
@st.cache_data
def load_data():
    df_ref = pd.read_excel(REF_FILE, usecols=ref_columns)
    df_stock = pd.read_excel(STOCK_FILE, usecols=stock_columns)
    df_nsc = pd.read_excel(NSC_FILE, usecols=nsc_columns)

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

    df_merged = df_merged.merge(
        df_nsc,
        how="left",
        left_on="<Discount Link.|Node|.Discount - Level 3 - Family>",
        right_on="Discount Group"
    )

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
    
    stocking_type_p = st.checkbox("Mostrar solo P - Omron Stocked Item")
    available_only = st.checkbox("Mostrar solo stock disponible")
    
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
    palabras = long_desc_filter.split()
    mask = results["Item Long Description"].astype(str).apply(
        lambda desc: all(palabra.lower() in desc.lower() for palabra in palabras)
    )
    results = results[mask]

if query:
    mask_oee = results["OEE Second Item Number"].astype(str).str.contains(query, case=False, na=False)
    mask_catalog = results["Catalog Description"].astype(str).str.contains(query, case=False, na=False)
    mask_long = results["Item Long Description"].astype(str).str.contains(query, case=False, na=False)
    results = results[mask_oee | mask_catalog | mask_long]

if stocking_type_p:
    results = results[results["Stocking Type"] == "P - Omron Stocked Item"]

if available_only:
    results = results[results["Qty Immediately"] > 0]

# -----------------------------
# Formatear List Price y aplicar límite de descuento
# -----------------------------
results["List Price ES"] = pd.to_numeric(results["List Price ES"], errors='coerce')
results["Discount Limit"] = results["Sales person Limit"].apply(lambda x: x if pd.notnull(x) else 0)
results["Price Limit"] = results.apply(
    lambda row: row["List Price ES"] * (1 - row["Discount Limit"]/100) if row["Discount Limit"] > 0 else row["List Price ES"],
    axis=1
)

results_display = results.copy()
results_display["List Price ES"] = results_display["List Price ES"].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "")
results_display["Discount Limit"] = results_display["Discount Limit"].apply(lambda x: f"{x:.0f}%" if x>0 else "")
results_display["Price Limit"] = results_display["Price Limit"].apply(lambda x: f"€ {x:,.2f}" if pd.notnull(x) else "")

# -----------------------------
# Mostrar resultados y selección de item
# -----------------------------
st.markdown(f"### 📊 Resultados encontrados: {len(results_display)}")

selected_item = st.selectbox(
    "Selecciona un item para ver detalles",
    options=results_display["OEE Second Item Number"].astype(str)
)

if selected_item:
    item = results_display[results_display["OEE Second Item Number"].astype(str) == selected_item].iloc[0]
    st.write(f"**OEE Second Item Number:** {item['OEE Second Item Number']}")
    st.write(f"**Catalog Description:** {item['Catalog Description']}")
    st.write(f"**Item Long Description:** {item['Item Long Description']}")
    st.write(f"**Stocking Type:** {item['Stocking Type']}")
    st.write(f"**Qty Immediately:** {item['Qty Immediately']}")
    st.write(f"**Qty Future:** {item['Qty Future']}")
    st.write(f"**List Price ES:** {item['List Price ES']}")
    st.write(f"**Discount Limit:** {item['Discount Limit']}")
    st.write(f"**Price Limit:** {item['Price Limit']}")
    if pd.notna(item["<Primary Image.|Node|.Deep Link - 160px>"]):
        st.image(item["<Primary Image.|Node|.Deep Link - 160px>"], width=200)

# -----------------------------
# Carrito de selección (varios items)
# -----------------------------
st.markdown("### 🛒 Añadir item al carrito")

if "seleccion_items" not in st.session_state:
    st.session_state.seleccion_items = pd.DataFrame(columns=["Item Code", "Quantity", "Discount"])

if selected_item:
    col1, col2, col3, col4 = st.columns([3,2,2,1])
    with col1:
        st.write(f"{item['Item Code']} - {item['Catalog Description']}")
    with col2:
        qty = st.number_input(f"Cantidad {item['Item Code']}", min_value=0, value=0, key=f"qty_{item['Item Code']}")
    with col3:
        disc = st.number_input(f"Descuento % {item['Item Code']}", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key=f"disc_{item['Item Code']}")
    with col4:
        if st.button("Añadir", key=f"add_{item['Item Code']}") and qty > 0:
            st.session_state.seleccion_items.loc[item['Item Code']] = [item['Item Code'], qty, disc]
            st.success(f"{item['Item Code']} añadido al carrito")

# Mostrar carrito actual
if not st.session_state.seleccion_items.empty:
    st.markdown("### 📝 Carrito actual")
    st.dataframe(st.session_state.seleccion_items)

    # Descargar selección de items
    output_sel = BytesIO()
    with pd.ExcelWriter(output_sel, engine='xlsxwriter') as writer:
        st.session_state.seleccion_items.to_excel(writer, index=False, sheet_name='Selección')
    output_sel.seek(0)

    st.download_button(
        label="📥 Descargar selección de items",
        data=output_sel,
        file_name="Seleccion_Items.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -----------------------------
# Descargar Excel de resultados filtrados
# -----------------------------
if not results.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        results_display.to_excel(writer, index=False, sheet_name='Resultados')
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
