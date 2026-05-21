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

# Auto-refresh every 30 seconds without page reload
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=30000)

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
            html_s = """
            <style>
            .dash-table { width:100%; border-collapse:collapse; font-size:14px; }
            .dash-table th { background:#1e3a5f; color:white; padding:8px 10px; font-weight:600; border-bottom:2px solid #ccc; text-align:center; }
            .dash-table td { padding:7px 10px; border-bottom:1px solid #e0e0e0; text-align:center; }
            .dash-table tr:hover td { background:#f5f8ff; }
            </style>
            <table class="dash-table">
            <thead><tr>
                <th>Shipment</th><th>City</th><th>State</th><th>Weight (lbs)</th><th>Status</th>
            </tr></thead><tbody>"""
            for s in activos:
                try: w = f"{int(s.get('weight',0)):,}"
                except: w = ""
                html_s += f"""<tr>
                    <td>{s.get('shipment_number','')}</td>
                    <td>{s.get('city','')}</td>
                    <td>{s.get('state','')}</td>
                    <td>{w}</td>
                    <td>{s.get('warehouse_status','')}</td>
                </tr>"""
            html_s += "</tbody></table>"
            st.markdown(html_s, unsafe_allow_html=True)
        else:
            st.info("No active shipments.")

    with col_right:
        st.subheader("Active Loads")
        if active_loads:
            html_l = """
            <table class="dash-table">
            <thead><tr>
                <th>Load</th><th>Carrier</th><th>Total Weight</th><th>Status</th><th>ETA Pickup</th>
            </tr></thead><tbody>"""
            for l in active_loads:
                try: tw = f"{int(l.get('total_weight',0)):,}"
                except: tw = l.get('total_weight','')
                html_l += f"""<tr>
                    <td>{l.get('load_number','')}</td>
                    <td>{l.get('carrier','')}</td>
                    <td>{tw}</td>
                    <td>{l.get('load_status','')}</td>
                    <td>{l.get('eta_pickup','')}</td>
                </tr>"""
            html_l += "</tbody></table>"
            st.markdown(html_l, unsafe_allow_html=True)
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
        def fmt_weight(x):
            try: return f"{int(x):,}"
            except: return ""
        def fmt_date(x):
            try: return datetime.strptime(x, "%Y-%m-%d").strftime("%m-%d-%Y")
            except: return x if x else ""

        html = """
        <style>
        .alva-table { width:100%; border-collapse:collapse; font-size:14px; }
        .alva-table th.left  { background:#1e3a5f; color:white; padding:8px 10px; font-weight:600; border-bottom:2px solid #ccc; text-align:left; }
        .alva-table th.center { background:#1e3a5f; color:white; padding:8px 10px; font-weight:600; border-bottom:2px solid #ccc; text-align:center; }
        .alva-table td { padding:7px 10px; border-bottom:1px solid #e0e0e0; }
        .alva-table tr:hover td { background:#f5f8ff; }
        .left  { text-align:left; }
        .center { text-align:center; }
        </style>
        <table class="alva-table">
        <thead><tr>
            <th class="center">Shipment</th>
            <th class="center">Customer</th>
            <th class="center">City</th>
            <th class="center">State</th>
            <th class="center">Weight</th>
            <th class="center">Bundles</th>
            <th class="center">Trailer</th>
            <th class="center">Status</th>
            <th class="center">Delivery Date</th>
        </tr></thead>
        <tbody>
        """
        for s in shipments_filtrados:
            html += f"""<tr>
                <td class="center">{s.get('shipment_number','')}</td>
                <td class="center">{s.get('customer','')}</td>
                <td class="center">{s.get('city','')}</td>
                <td class="center">{s.get('state','')}</td>
                <td class="center">{fmt_weight(s.get('weight',''))}</td>
                <td class="center">{s.get('bundles','')}</td>
                <td class="center">{s.get('trailer_type','')}</td>
                <td class="center">{s.get('warehouse_status','')}</td>
                <td class="center">{fmt_date(s.get('delivery_date',''))}</td>
            </tr>"""
        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)
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
        html_l = """
        <style>
        .loads-table { width:100%; border-collapse:collapse; font-size:14px; }
        .loads-table th { background:#1e3a5f; color:white; padding:8px 10px; font-weight:600; border-bottom:2px solid #ccc; text-align:center; }
        .loads-table td { padding:7px 10px; border-bottom:1px solid #e0e0e0; text-align:center; }
        .loads-table tr:hover td { background:#f5f8ff; }
        </style>
        <table class="loads-table">
        <thead><tr>
            <th>Load</th><th>Carrier</th><th>Total Weight</th><th>Bundles</th><th>Status</th><th>ETA Pickup</th><th>Freight Cost</th><th>Sales Value</th>
        </tr></thead><tbody>"""
        for l in loads:
            try: tw = f"{int(l.get('total_weight',0)):,}"
            except: tw = l.get('total_weight','')
            try: fc = f"${int(l.get('freight_cost',0)):,}"
            except: fc = l.get('freight_cost','')
            try: sv = f"${int(l.get('sales_value',0)):,}"
            except: sv = l.get('sales_value','')
            html_l += f"""<tr>
                <td>{l.get('load_number','')}</td>
                <td>{l.get('carrier','')}</td>
                <td>{tw}</td>
                <td>{l.get('total_bundles','')}</td>
                <td>{l.get('load_status','')}</td>
                <td>{l.get('eta_pickup','')}</td>
                <td>{fc}</td>
                <td>{sv}</td>
            </tr>"""
        html_l += "</tbody></table>"
        st.markdown(html_l, unsafe_allow_html=True)
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