# ============================================
# ALVA LOGISTICS TRACKER - Web Interface
# ============================================

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from config import AIRTABLE_TOKEN, SHIPMENTS_TABLE
from airtable_connection import get_all_shipments, get_loads, get_pricing
from consolidation_detector import detectar_consolidaciones

# Page configuration
st.set_page_config(
    page_title="Alva Logistics Tracker",
    page_icon="🚛",
    layout="wide"
)

# Auto-refresh every 30 seconds
st.markdown("""<meta http-equiv="refresh" content="30">""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🚛 Alva Logistics")
st.sidebar.markdown("**Transportation System**")
st.sidebar.markdown("---")

pagina = st.sidebar.radio("Navigation", [
    "Dashboard",
    "Shipments",
    "Loads",
    "Pricing",
    "Consolidations"
])

st.sidebar.markdown("---")
st.sidebar.markdown(f"*Texas — {datetime.now().strftime('%m/%d/%Y')}*")

# Headers for Airtable
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

def update_status(record_id, new_status):
    url = f"https://api.airtable.com/v0/{st.secrets['BASE_ID']}/{SHIPMENTS_TABLE}/{record_id}"
    payload = {"fields": {"Warehouse Status": new_status}}
    response = requests.patch(url, headers=HEADERS, json=payload)
    return response

# ── DASHBOARD ──────────────────────────────
if pagina == "Dashboard":
    st.title("Operations Dashboard")
    st.markdown(f"**Texas** — {datetime.now().strftime('%A, %B %d %Y')}")
    st.markdown("---")

    with st.spinner("Loading data..."):
        shipments = get_all_shipments()
        loads = get_loads()

    pending = [s for s in shipments if s["warehouse_status"] == "Pending Print"]
    in_progress = [s for s in shipments if s["warehouse_status"] == "In Progress"]
    ready = [s for s in shipments if s["warehouse_status"] == "Ready"]
    shipped = [s for s in shipments if s["warehouse_status"] == "Shipped"]
    active_loads = [l for l in loads if l["load_status"] != "Shipped"]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Pending Print", len(pending))
    col2.metric("In Progress", len(in_progress))
    col3.metric("Ready", len(ready))
    col4.metric("Shipped", len(shipped))
    col5.metric("Active Loads", len(active_loads))

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Active Shipments")
        activos = pending + in_progress + ready
        if activos:
            df = pd.DataFrame(activos)[["shipment_number", "city", "state", "weight", "warehouse_status"]]
            df.columns = ["Shipment", "City", "State", "Weight (lbs)", "Status"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No active shipments.")

    with col_right:
        st.subheader("Active Loads")
        if active_loads:
            df_loads = pd.DataFrame(active_loads)[["load_number", "carrier", "total_weight", "load_status", "eta_pickup"]]
            df_loads.columns = ["Load", "Carrier", "Total Weight", "Status", "ETA Pickup"]
            st.dataframe(df_loads, use_container_width=True, hide_index=True)
        else:
            st.info("No active loads.")

# ── SHIPMENTS ──────────────────────────────
elif pagina == "Shipments":
    st.title("Shipments")
    st.markdown("---")

    with st.spinner("Loading shipments..."):
        shipments = get_all_shipments()

    col_filter, col_count = st.columns([3, 1])
    with col_filter:
        filtro = st.selectbox("Filter by status", [
            "All", "Pending Print", "In Progress", "Ready", "Shipped"
        ])

    if filtro != "All":
        shipments_filtrados = [s for s in shipments if s["warehouse_status"] == filtro]
    else:
        shipments_filtrados = shipments

    with col_count:
        st.metric("Total", len(shipments_filtrados))

    if shipments_filtrados:
        df = pd.DataFrame(shipments_filtrados)[[
            "shipment_number", "customer", "city", "state",
            "weight", "bundles", "trailer_type", "warehouse_status", "delivery_date"
        ]]
        df.columns = ["Shipment", "Customer", "City", "State", "Weight", "Bundles", "Trailer", "Status", "Delivery Date"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No shipments found with that filter.")

    st.markdown("---")
    st.subheader("Update Warehouse Status")
    st.caption("Select a shipment and update its status directly from here.")

    shipment_sel = st.selectbox("Shipment", [s["shipment_number"] for s in shipments])
    nuevo_status = st.selectbox("New Status", [
        "Pending Print", "In Progress", "Ready", "Shipped"
    ])

    if st.button("Update Status", type="primary"):
        shipment_obj = next((s for s in shipments if s["shipment_number"] == shipment_sel), None)
        if shipment_obj:
            response = update_status(shipment_obj["id"], nuevo_status)
            if response.status_code == 200:
                st.success(f"✅ {shipment_sel} updated to {nuevo_status}")
                st.rerun()
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        else:
            st.error("Shipment not found")

# ── LOADS ──────────────────────────────────
elif pagina == "Loads":
    st.title("Loads")
    st.markdown("---")

    with st.spinner("Loading loads..."):
        loads = get_loads()

    if loads:
        df = pd.DataFrame(loads)[[
            "load_number", "carrier", "total_weight",
            "total_bundles", "load_status", "eta_pickup",
            "freight_cost", "sales_value"
        ]]
        df.columns = ["Load", "Carrier", "Total Weight", "Bundles", "Status", "ETA Pickup", "Freight Cost", "Sales Value"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(loads)} loads")
    else:
        st.info("No loads registered.")

# ── PRICING ────────────────────────────────
elif pagina == "Pricing":
    st.title("Pricing")
    st.markdown("---")

    with st.spinner("Loading quotes..."):
        quotes = get_pricing()

    col_filter, col_count = st.columns([3, 1])
    with col_filter:
        filtro_status = st.selectbox("Filter by status", [
            "All", "Pending", "Selected", "Lost"
        ])

    if filtro_status != "All":
        quotes_filtrados = [q for q in quotes if q["status"] == filtro_status]
    else:
        quotes_filtrados = quotes

    with col_count:
        st.metric("Total", len(quotes_filtrados))

    if quotes_filtrados:
        df = pd.DataFrame(quotes_filtrados)[[
            "quote_number", "carrier", "freight_cost",
            "sales_value", "profit", "status"
        ]]
        df.columns = ["Quote #", "Carrier", "Freight Cost", "Sales Value", "Profit", "Status"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No quotes found with that filter.")

# ── CONSOLIDATIONS ────────────────────────
elif pagina == "Consolidations":
    st.title("Consolidation Detector")
    st.markdown("---")
    st.info("The detector analyzes all active shipments and calculates real distances between destinations.")

    if st.button("Detect opportunities"):
        with st.spinner("Analyzing active shipments..."):
            oportunidades = detectar_consolidaciones()

        if oportunidades:
            st.success(f"{len(oportunidades)} opportunity(ies) detected")
            for i, op in enumerate(oportunidades, 1):
                with st.expander(f"Opportunity #{i} — {op['destino_1']} + {op['destino_2']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Distance", f"{op['distancia_millas']} miles")
                    col2.metric("Combined weight", f"{op['peso_combinado']:,} lbs")
                    col3.metric("Available space", f"{op['espacio_disponible']:,} lbs")
                    st.markdown(f"**Shipment 1:** {op['shipment_1']} → {op['destino_1']} ({op['peso_1']:,} lbs)")
                    st.markdown(f"**Shipment 2:** {op['shipment_2']} → {op['destino_2']} ({op['peso_2']:,} lbs)")
                    st.markdown(f"**Suggested trailer:** {op['trailer_sugerido']}")
        else:
            st.warning("No consolidation opportunities detected with current active shipments.")