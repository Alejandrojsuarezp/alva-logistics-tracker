# ============================================
# X LOGISTICS TRACKER - Web Interface
# ============================================

import streamlit as st
import pandas as pd
import requests
import html
from collections import Counter
from datetime import datetime, date
import folium
from streamlit_folium import st_folium
from config import AIRTABLE_TOKEN, SHIPMENTS_TABLE, LOADS_TABLE, PRICING_TABLE, UPDATES_LOG_TABLE
from airtable_connection import get_all_shipments, get_loads, get_pricing, get_updates_log, get_shipment_number_map, get_records
from consolidation_detector import detectar_consolidaciones, get_coordinates_address, _load_cache

st.set_page_config(
    page_title="X Logistics Tracker",
    page_icon="🚛",
    layout="wide"
)

# ── GLOBAL CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.25rem 2.5rem 2.5rem 2.5rem !important; }

body, .stApp {
    background: #f5f5f4;
}

section[data-testid="stSidebar"] { display: none; }
div[data-testid="stSidebarNav"] { display: none; }

/* ── TOPBAR ─────────────────────────────────────────────────────────────── */
.st-key-xlt_topbar {
    background: #ffffff;
    border-bottom: 1px solid #e7e5e4;
    margin: -1.25rem -2.5rem 1.5rem -2.5rem;
    padding: 10px 2.5rem;
}
.st-key-xlt_topbar div[data-testid="column"] {
    display: flex;
    align-items: center;
}
.xlt-logo {
    display: flex;
    align-items: center;
    gap: 8px;
}
.xlt-logo-text {
    display: flex;
    flex-direction: column;
    line-height: 1.15;
}
.xlt-logo-title {
    font-size: 13px;
    font-weight: 800;
    color: #1c1917;
}
.xlt-logo-sub {
    font-size: 11px;
    font-weight: 300;
    color: #1c1917;
}

.st-key-xlt_topbar div[data-testid="stButton"] { margin: 0; }
.st-key-xlt_topbar div[data-testid="stButton"] button {
    width: 100%;
    border: none;
    border-radius: 0;
    border-bottom: 2px solid transparent;
    padding: 8px 4px;
    font-size: 13px;
    font-weight: 500;
    background: transparent;
    color: #78716c;
    box-shadow: none;
    transition: color .15s, border-color .15s;
}
.st-key-xlt_topbar div[data-testid="stButton"] button p {
    font-size: 13px !important;
    margin: 0;
}
.st-key-xlt_topbar div[data-testid="stButton"] button:hover {
    color: #1c1917;
}
.st-key-xlt_topbar div[data-testid="stButton"] button[kind="primary"] {
    color: #1c1917;
    font-weight: 700;
    border-bottom: 2px solid #1c1917;
    background: transparent;
    box-shadow: none;
}
.st-key-xlt_topbar div[data-testid="stButton"] button[kind="primary"]:hover {
    color: #1c1917;
}

/* + New button (its own keyed container so it wins over the nav-item primary style) */
.st-key-xlt_topbar_cta div[data-testid="stButton"] button[kind="primary"] {
    background: #1c1917;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    box-shadow: none;
}
.st-key-xlt_topbar_cta div[data-testid="stButton"] button[kind="primary"]:hover {
    background: #3f3a37;
    color: #ffffff;
}
.st-key-xlt_topbar_cta div[data-testid="stButton"] button:disabled {
    background: #f5f5f4;
    color: #a8a29e;
    border: 1px solid #e7e5e4;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: .01em;
}
.badge::before {
    content: "";
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    opacity: .8;
}
.badge-pending  { background: #EFF6FF; color: #1d4ed8; }
.badge-progress { background: #FFFBEB; color: #b45309; }
.badge-ready    { background: #F0FDF4; color: #15803d; }
.badge-shipped  { background: #F8FAFC; color: #64748b; }
.badge-pickup   { background: #F5F3FF; color: #6d28d9; }

.xlt-page-title {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.01em;
    color: #1c1917;
    margin-bottom: 4px;
}
.xlt-page-sub {
    font-size: 14px;
    color: #a8a29e;
    margin-bottom: 1.75rem;
}

.xlt-metric {
    position: relative;
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    padding: 20px 20px 16px 20px;
    overflow: hidden;
}
.xlt-metric-val {
    font-size: 22px;
    font-weight: 800;
    color: #1c1917;
    line-height: 1;
}
.xlt-metric-lbl {
    font-size: 13px;
    font-weight: 500;
    color: #a8a29e;
    margin-top: 6px;
}
.xlt-metric-bar {
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 2px;
}

.xlt-table-wrap {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    overflow: hidden;
    overflow-x: auto;
}
.xlt-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}
.xlt-table th {
    background: #fafaf9;
    padding: 12px 16px;
    text-align: left;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #a8a29e;
    border-bottom: 1px solid #e7e5e4;
    white-space: nowrap;
}
.xlt-table td {
    padding: 13px 16px;
    border-bottom: 1px solid #e7e5e4;
    color: #1c1917;
    font-size: 14px;
    white-space: nowrap;
}
.xlt-table tr:nth-child(even) td { background: #fafaf9; }
.xlt-table tr:last-child td { border-bottom: none; }
.xlt-table tr:hover td { background: #f5f5f4; }

.xlt-section-card {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 1.25rem;
}
.xlt-section-title {
    font-size: 16px;
    font-weight: 700;
    color: #1c1917;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 7px;
}

.xlt-form-card {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    padding: 26px 28px;
    margin-top: 1.25rem;
}
.xlt-form-title {
    font-size: 18px;
    font-weight: 700;
    color: #1c1917;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px solid #e7e5e4;
    display: flex;
    align-items: center;
    gap: 8px;
}
.xlt-form-group-label {
    font-size: 11px;
    font-weight: 700;
    color: #a8a29e;
    text-transform: uppercase;
    letter-spacing: .06em;
    margin: 18px 0 6px 0;
}
.auto-badge {
    font-size: 11px;
    background: #f5f5f4;
    color: #78716c;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 500;
}
.info-box {
    background: #fafaf9;
    border: 1px solid #e7e5e4;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    color: #78716c;
    margin-bottom: 8px;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stDateInput"] label,
div[data-testid="stMultiSelect"] label {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #78716c !important;
}
div[data-testid="stButton"] button {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 14px !important;
    border-radius: 8px;
    padding: 10px 16px;
}
div[data-testid="stButton"] button[kind="primary"] {
    background: #1c1917;
    color: #ffffff;
    border: none;
    box-shadow: none;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background: #3f3a37;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

# Auto-refresh every 30 seconds
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=30000)

# ── HEADERS FOR AIRTABLE ────────────────────────────────────────────────────
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}
BASE_ID = st.secrets["BASE_ID"]

# ── REFERENCE LISTS — must match Airtable single-select options exactly ────
CARRIERS = ["Cowtown Logistics", "TQL", "Ecologistics", "Worldwide Logistics", "ICM Logistic", "West Jersey Express"]
TRAILER_TYPES = ["Hotshot 40'", "Flatbed 48'", "Flatbed 53'", "Stepdeck 48'", "Stepdeck 53'", "Conestoga 48'", "Conestoga 53'", "LTL"]
UPDATE_TYPES = ["Status Change", "Delay", "Documentation", "Communication", "Issue/Problem", "Billing"]
RESPONSIBLE_OPTIONS = ["Warehouse", "Logistics", "Customer Service", "Carrier", "Customer"]
WAREHOUSE_OPTIONS = ["Texas", "Florida"]
PICKUP_OPTIONS = ["No", "Yes"]
US_STATES = [
    "TX","FL","AL","AR","AZ","CA","CO","GA","ID","IL","IN","KS","KY",
    "LA","MI","MN","MO","MS","MT","NC","ND","NE","NM","NV","OH","OK",
    "OR","SC","SD","TN","UT","VA","WA","WI","WY"
]

# ── HELPER FUNCTIONS ────────────────────────────────────────────────────────
def badge_html(status):
    if isinstance(status, list):
        status = status[0] if status else ""
    status = str(status) if status else "—"
    cls = {
        "Pending Print": "badge-pending",
        "In Progress":   "badge-progress",
        "Ready":         "badge-ready",
        "Shipped":       "badge-shipped",
        "Pending":       "badge-pending",
        "Selected":      "badge-ready",
        "Lost":          "badge-shipped",
        "Scheduled":     "badge-pending",
        "In Transit":    "badge-progress",
        "Yes":           "badge-pickup",
    }.get(status, "badge-shipped")
    return f'<span class="badge {cls}">{status}</span>'

def fmt_weight(x):
    try: return f"{int(x):,}"
    except: return str(x) if x else "—"

def fmt_date(x):
    if not x: return "—"
    try: return datetime.strptime(x, "%Y-%m-%d").strftime("%m/%d/%Y")
    except: return x

def create_record(table_id, fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
    response = requests.post(url, headers=HEADERS, json={"fields": fields}, timeout=10)
    return response

def update_record_api(table_id, record_id, fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}/{record_id}"
    response = requests.patch(url, headers=HEADERS, json={"fields": fields}, timeout=10)
    return response

WAREHOUSE_COORDS = {
    "Texas":   (32.7767, -97.2894),
    "Florida": (26.7153, -80.0534),
}
COLOR_TEXAS = "#185FA5"
COLOR_FLORIDA = "#FFC107"
COLOR_CONSOLIDATED = "#FF8C00"
COLOR_UNKNOWN = "#9CA3AF"

@st.cache_data(ttl=60, show_spinner=False)
def _get_live_map_data():
    """Fetches Loads + Shipments and geocodes each Ready load's shipment destinations.
    Cached for 60s so panning/zooming the map (a Streamlit rerun) doesn't re-hit Airtable
    or Nominatim on every interaction."""
    loads = get_loads(debug=True)
    shipments = get_all_shipments()
    shipment_by_id = {s["id"]: s for s in shipments}

    ready_loads = [l for l in loads if l.get("load_status") == "Ready"]
    cache = _load_cache()

    markers = []
    for l in ready_loads:
        linked_ids = l.get("linked_shipment_ids", [])
        is_consolidated = len(linked_ids) >= 2
        wh = l.get("warehouse")
        if is_consolidated:
            color = COLOR_CONSOLIDATED
        elif wh == "Texas":
            color = COLOR_TEXAS
        elif wh == "Florida":
            color = COLOR_FLORIDA
        else:
            color = COLOR_UNKNOWN

        # Resolve all shipments in this load first, so consolidated loads can list
        # "also in this load" siblings on every marker's popup.
        load_shipments = []
        for sid in linked_ids:
            shipment = shipment_by_id.get(sid)
            if not shipment:
                continue
            coords = get_coordinates_address(
                shipment.get("address", ""), shipment.get("city", ""),
                shipment.get("state", ""), shipment.get("zip_code", ""), cache,
            )
            if not coords:
                continue
            load_shipments.append({
                "coords": coords,
                "shipment_number": shipment.get("shipment_number", ""),
                "destination": f"{shipment.get('city','')}, {shipment.get('state','')}",
            })

        for i, si in enumerate(load_shipments):
            others = [o for j, o in enumerate(load_shipments) if j != i]
            markers.append({
                "coords": si["coords"],
                "color": color,
                "warehouse": wh,
                "load_number": l.get("load_number", ""),
                "carrier": l.get("carrier", ""),
                "shipment_number": si["shipment_number"],
                "destination": si["destination"],
                "others": others,
            })

    raw_loads = get_records(LOADS_TABLE)

    return {
        "markers": markers,
        "tx_loads": sum(1 for l in ready_loads if l.get("warehouse") == "Texas"),
        "fl_loads": sum(1 for l in ready_loads if l.get("warehouse") == "Florida"),
        "consolidated_pairs": sum(1 for l in ready_loads if len(l.get("linked_shipment_ids", [])) >= 2),
        "total_loads": len(ready_loads),
        "status_counts": dict(Counter(l.get("load_status", "") for l in loads)),
        "warehouse_counts": dict(Counter(l.get("warehouse", "") for l in loads)),
        "raw_first_fields": raw_loads[0].get("fields", {}) if raw_loads else {},
    }

# ── TOPBAR ──────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    "Dashboard", "Shipments", "Loads", "Pricing",
    "Updates Log", "Consolidations", "Live Map", "Truck Builder",
]
# Pages that have a "New X" form — the topbar + New button is only active on these.
CREATE_ACTION = {
    "Shipments":   "show_shipment_form",
    "Loads":       "show_load_form",
    "Pricing":     "show_quote_form",
    "Updates Log": "show_update_form",
}
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Dashboard"

with st.container(key="xlt_topbar"):
    cols = st.columns([2.4] + [1] * len(NAV_ITEMS) + [1.2])

    with cols[0]:
        st.markdown("""
        <div class="xlt-logo">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="3" y1="3" x2="19" y2="19" stroke="#1c1917" stroke-width="4" stroke-linecap="round"/>
                <line x1="19" y1="3" x2="3" y2="19" stroke="#1c1917" stroke-width="4" stroke-linecap="round"/>
            </svg>
            <div class="xlt-logo-text">
                <div class="xlt-logo-title">Logistics</div>
                <div class="xlt-logo-sub">Tracker</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    for i, label in enumerate(NAV_ITEMS):
        with cols[i + 1]:
            is_active = st.session_state["pagina"] == label
            if st.button(label, key=f"nav_{label}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state["pagina"] = label
                st.rerun()

    with cols[-1]:
        with st.container(key="xlt_topbar_cta"):
            active_page = st.session_state["pagina"]
            create_flag = CREATE_ACTION.get(active_page)
            if create_flag:
                if st.button("＋ New", key="topbar_new", use_container_width=True, type="primary"):
                    st.session_state[create_flag] = True
                    st.rerun()
            else:
                st.button("＋ New", key="topbar_new_disabled", use_container_width=True, disabled=True)

pagina = st.session_state["pagina"]

# ── DASHBOARD ───────────────────────────────────────────────────────────────
if pagina == "Dashboard":
    st.markdown('<div class="xlt-page-title">Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="xlt-page-sub">{datetime.now().strftime("%A, %B %d %Y")} · Texas & Florida</div>', unsafe_allow_html=True)

    with st.spinner("Loading data..."):
        shipments = get_all_shipments()
        loads = get_loads()

    pending    = [s for s in shipments if s["warehouse_status"] == "Pending Print"]
    in_prog    = [s for s in shipments if s["warehouse_status"] == "In Progress"]
    ready      = [s for s in shipments if s["warehouse_status"] == "Ready"]
    shipped    = [s for s in shipments if s["warehouse_status"] == "Shipped"]
    active_lds = [l for l in loads if l["load_status"] not in ("Shipped", "Delivered")]

    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, "#1d4ed8", len(pending),    "Pending Print"),
        (c2, "#b45309", len(in_prog),    "In Progress"),
        (c3, "#15803d", len(ready),      "Ready"),
        (c4, "#64748b", len(shipped),    "Shipped"),
        (c5, "#4338ca", len(active_lds), "Active Loads"),
    ]
    for col, color, val, lbl in metrics:
        with col:
            st.markdown(f"""
            <div class="xlt-metric">
                <div class="xlt-metric-val">{val}</div>
                <div class="xlt-metric-lbl">{lbl}</div>
                <div class="xlt-metric-bar" style="background:{color};"></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        activos = pending + in_prog + ready
        st.markdown('<div class="xlt-section-title">🚢 Active Shipments</div>', unsafe_allow_html=True)
        if activos:
            rows = ""
            for s in activos[:8]:
                rows += f"""<tr>
                    <td>{s.get('shipment_number','—')}</td>
                    <td>{s.get('customer','—')}</td>
                    <td>{s.get('warehouse','—')}</td>
                    <td>{s.get('city','')}, {s.get('state','')}</td>
                    <td>{fmt_weight(s.get('weight',''))}</td>
                    <td>{badge_html(s.get('warehouse_status',''))}</td>
                </tr>"""
            st.markdown(f"""
            <div class="xlt-table-wrap">
            <table class="xlt-table">
            <thead><tr><th>Shipment</th><th>Customer</th><th>Warehouse</th><th>Destination</th><th>Weight</th><th>Status</th></tr></thead>
            <tbody>{rows}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else:
            st.info("No active shipments.")

    with col_r:
        st.markdown('<div class="xlt-section-title">📦 Active Loads</div>', unsafe_allow_html=True)
        if active_lds:
            rows = ""
            for l in active_lds[:8]:
                rows += f"""<tr>
                    <td>{l.get('load_number','—')}</td>
                    <td>{l.get('carrier','—')}</td>
                    <td>{l.get('linked_shipments','—')}</td>
                    <td>{fmt_weight(l.get('total_weight',''))}</td>
                    <td>{badge_html(l.get('load_status',''))}</td>
                    <td>{l.get('eta_pickup','—')}</td>
                </tr>"""
            st.markdown(f"""
            <div class="xlt-table-wrap">
            <table class="xlt-table">
            <thead><tr><th>Load #</th><th>Carrier</th><th>Shipments</th><th>Weight</th><th>Status</th><th>ETA Pickup</th></tr></thead>
            <tbody>{rows}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else:
            st.info("No active loads.")

# ── SHIPMENTS ───────────────────────────────────────────────────────────────
elif pagina == "Shipments":
    st.markdown('<div class="xlt-page-title">Shipments</div>', unsafe_allow_html=True)

    with st.spinner("Loading shipments..."):
        shipments = get_all_shipments()

    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        filtro = st.selectbox("Filter by status", ["All","Pending Print","In Progress","Ready","Shipped"], label_visibility="collapsed")
    with col_f2:
        filtro_wh = st.selectbox("Filter by warehouse", ["All Warehouses","Texas","Florida"], label_visibility="collapsed")

    filtered = [s for s in shipments if filtro == "All" or s["warehouse_status"] == filtro]
    if filtro_wh != "All Warehouses":
        filtered = [s for s in filtered if s.get("warehouse") == filtro_wh]
    st.markdown(f'<div class="xlt-page-sub">{len(filtered)} shipments</div>', unsafe_allow_html=True)

    if filtered:
        rows = ""
        for s in filtered:
            pickup_badge = badge_html("Yes") if s.get("pick_up") == "Yes" else "—"
            rows += f"""<tr>
                <td><strong>{s.get('shipment_number','—')}</strong></td>
                <td>{s.get('customer','—')}</td>
                <td>{s.get('warehouse','—')}</td>
                <td>{s.get('address','—')}</td>
                <td>{s.get('city','')}, {s.get('state','')}</td>
                <td>{fmt_weight(s.get('weight',''))}</td>
                <td>{s.get('bundles','—')}</td>
                <td>{s.get('elbows','—')}</td>
                <td>{s.get('trailer_type','—')}</td>
                <td>{fmt_date(s.get('delivery_date',''))}</td>
                <td>{pickup_badge}</td>
                <td>{badge_html(s.get('warehouse_status',''))}</td>
            </tr>"""
        st.markdown(f"""
        <div class="xlt-table-wrap">
        <table class="xlt-table">
        <thead><tr>
            <th>Shipment #</th><th>Customer</th><th>Warehouse</th><th>Address</th><th>City, State</th>
            <th>Weight</th><th>Bundles</th><th>Elbows</th><th>Trailer</th><th>Delivery</th><th>Pick Up</th><th>Status</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No shipments found.")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("✏️  Update Warehouse Status", expanded=False):
        col_s, col_ns = st.columns(2)
        with col_s:
            shipment_sel = st.selectbox("Shipment", [s["shipment_number"] for s in shipments])
        with col_ns:
            nuevo_status = st.selectbox("New Status", ["Pending Print","In Progress","Ready","Shipped"])
        if st.button("Update Status", type="primary"):
            obj = next((s for s in shipments if s["shipment_number"] == shipment_sel), None)
            if obj:
                r = update_record_api(SHIPMENTS_TABLE, obj["id"], {"Warehouse Status": nuevo_status})
                if r.status_code == 200:
                    st.success(f"✅ {shipment_sel} → {nuevo_status}")
                    st.rerun()
                else:
                    st.error(f"Error {r.status_code}: {r.text}")

    if st.session_state.get("show_shipment_form"):
        st.markdown('<div class="xlt-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="xlt-form-title">➕ New Shipment <span class="auto-badge">Order Date auto-generated · Status starts as Pending Print</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="xlt-form-group-label">Basic Info</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            f_shipment_num = st.text_input("Shipment Number *", placeholder="e.g. SHPT-0012345")
        with c2:
            f_customer = st.text_input("Customer *", placeholder="Company name")

        c1, c2 = st.columns(2)
        with c1:
            f_email = st.text_input("Customer Email", placeholder="email@company.com")
        with c2:
            f_delivery = st.date_input("Requested Delivery Date *", min_value=date.today())

        st.markdown('<div class="xlt-form-group-label">Destination</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            f_warehouse = st.selectbox("Warehouse *", WAREHOUSE_OPTIONS)
        with c2:
            f_address = st.text_input("Address", placeholder="Street address")

        c1, c2, c3 = st.columns(3)
        with c1:
            f_city = st.text_input("City *", placeholder="Houston")
        with c2:
            f_state = st.selectbox("State *", US_STATES)
        with c3:
            f_zip = st.text_input("ZIP Code", placeholder="77001")

        st.markdown('<div class="xlt-form-group-label">Cargo & Trailer</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            f_trailer = st.selectbox("Trailer Type Needed *", TRAILER_TYPES)
        with c2:
            f_weight = st.number_input("Weight (lbs) *", min_value=0, step=100)

        c1, c2, c3 = st.columns(3)
        with c1:
            f_bundles = st.number_input("Bundles", min_value=0, step=1)
        with c2:
            f_elbows = st.number_input("Elbows", min_value=0, step=1)
        with c3:
            f_pickup = st.selectbox("Pick Up", PICKUP_OPTIONS)

        f_dimensions = st.text_input("Dimensions", placeholder="Pallet/crate dimensions once ready (e.g. 48x40x36 in)")
        f_notes = st.text_area("Notes", placeholder="Special instructions, gate codes, contacts...", height=80)

        col_cancel, col_spacer, col_save = st.columns([1, 3, 1])
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state["show_shipment_form"] = False
                st.rerun()
        with col_save:
            if st.button("Create Shipment", type="primary", use_container_width=True):
                if not f_shipment_num or not f_customer or not f_city or (f_bundles == 0 and f_elbows == 0):
                    st.error("Please fill in all required fields (*). Bundles or Elbows must be greater than 0.")
                else:
                    fields = {
                        "Shipment Number": f_shipment_num,
                        "Customer": f_customer,
                        "Warehouse": f_warehouse,
                        "City": f_city,
                        "State": f_state,
                        "Trailer Type Needed": f_trailer,
                        "Weight": f_weight,
                        "Warehouse Status": "Pending Print",
                        "Order Date": date.today().isoformat(),
                        "Requested Delivery Date": f_delivery.isoformat(),
                        "Pick Up": f_pickup,
                        "Notes": f_notes,
                    }
                    if f_bundles: fields["Bundles"] = int(f_bundles)
                    if f_elbows: fields["Elbows"] = int(f_elbows)
                    if f_address: fields["Address"] = f_address
                    if f_dimensions: fields["Dimensions"] = f_dimensions
                    if f_zip:
                        try:
                            fields["ZIP Code"] = int(f_zip)
                        except:
                            fields["ZIP Code"] = f_zip
                    if f_email:
                        fields["Customer Email"] = f_email
                    r = create_record(SHIPMENTS_TABLE, fields)
                    if r.status_code in (200, 201):
                        st.success(f"✅ Shipment {f_shipment_num} created successfully!")
                        st.session_state["show_shipment_form"] = False
                        st.rerun()
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")

        st.markdown('</div>', unsafe_allow_html=True)

# ── LOADS ────────────────────────────────────────────────────────────────────
elif pagina == "Loads":
    st.markdown('<div class="xlt-page-title">Loads</div>', unsafe_allow_html=True)

    with st.spinner("Loading..."):
        shipment_map = get_shipment_number_map()
        loads     = get_loads(shipment_map)
        quotes    = get_pricing(shipment_map)
        shipments = get_all_shipments()

    filtro_ld = st.selectbox("Filter", ["All","Ready","Scheduled","In Transit","Shipped"], label_visibility="collapsed")

    filtered_ld = [l for l in loads if filtro_ld == "All" or l["load_status"] == filtro_ld]
    st.markdown(f'<div class="xlt-page-sub">{len(filtered_ld)} loads</div>', unsafe_allow_html=True)

    if filtered_ld:
        rows = ""
        for l in filtered_ld:
            rows += f"""<tr>
                <td><strong>{l.get('load_number','—')}</strong></td>
                <td>{l.get('carrier','—')}</td>
                <td>{l.get('linked_shipments','—')}</td>
                <td>{fmt_weight(l.get('total_weight',''))}</td>
                <td>{l.get('total_bundles','—')}</td>
                <td>{badge_html(l.get('load_status',''))}</td>
                <td>{l.get('eta_pickup','—')}</td>
                <td>${fmt_weight(l.get('freight_cost',''))}</td>
            </tr>"""
        st.markdown(f"""
        <div class="xlt-table-wrap">
        <table class="xlt-table">
        <thead><tr>
            <th>Load #</th><th>Carrier</th><th>Shipments</th><th>Weight</th><th>Bundles</th>
            <th>Status</th><th>ETA Pickup</th><th>Freight Cost</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No loads found.")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("✏️  Update Load Status", expanded=False):
        if loads:
            col_l, col_s = st.columns(2)
            with col_l:
                load_sel = st.selectbox("Load", [l["load_number"] for l in loads])
            with col_s:
                nuevo_load_status = st.selectbox("New Status", ["Ready","Scheduled","In Transit","Shipped"])
            if st.button("Update Load Status", type="primary"):
                obj = next((l for l in loads if l["load_number"] == load_sel), None)
                if obj:
                    r = update_record_api(LOADS_TABLE, obj["id"], {"Load Status": nuevo_load_status})
                    if r.status_code == 200:
                        st.success(f"✅ {load_sel} → {nuevo_load_status}")
                        st.rerun()
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")
        else:
            st.info("No loads available.")

    if st.session_state.get("show_load_form"):
        st.markdown('<div class="xlt-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="xlt-form-title">➕ New Load</div>', unsafe_allow_html=True)

        st.markdown('<div class="xlt-form-group-label">Load Info</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            f_load_num = st.text_input("Load Number * (from broker)", placeholder="e.g. LOAD 27617")
        with c2:
            f_load_status = st.selectbox("Load Status *", ["Ready","Scheduled","In Transit","Shipped"])

        st.markdown('<div class="xlt-form-group-label">Shipments & Quote</div>', unsafe_allow_html=True)
        ship_options = [f"{s['shipment_number']} — {s['customer']} · {s['city']}, {s['state']}"
                        for s in shipments if s["warehouse_status"] != "Shipped" and s.get("pick_up") != "Yes"]
        f_shipments = st.multiselect("Linked Shipments *", ship_options)

        pending_quotes = [q for q in quotes if q.get("status") == "Pending"]
        quote_options  = [f"Q-{q['quote_number']} — {q['carrier']} · ${fmt_weight(q.get('freight_cost',''))}"
                          for q in pending_quotes]
        f_quote = st.selectbox("Selected Quote from Pricing *", ["— Select —"] + quote_options)

        st.markdown('<div class="xlt-form-group-label">Trailer & Schedule</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            f_trailer_ld = st.selectbox("Trailer Type *", TRAILER_TYPES)
        with c2:
            f_eta = st.date_input("ETA Pickup *", min_value=date.today())

        col_cancel, col_spacer, col_save = st.columns([1, 3, 1])
        with col_cancel:
            if st.button("Cancel ", use_container_width=True):
                st.session_state["show_load_form"] = False
                st.rerun()
        with col_save:
            if st.button("Create Load", type="primary", use_container_width=True):
                if not f_load_num or not f_shipments or f_quote == "— Select —":
                    st.error("Please fill in all required fields (*).")
                else:
                    ship_numbers = [s.split(" — ")[0] for s in f_shipments]
                    ship_ids = [s["id"] for s in shipments if s["shipment_number"] in ship_numbers]
                    q_number = f_quote.split(" — ")[0].replace("Q-","")
                    quote_obj = next((q for q in pending_quotes if str(q["quote_number"]) == q_number), None)

                    fields = {
                        "Load Number": f_load_num,
                        "Load Status": f_load_status,
                        "Trailer Type": f_trailer_ld,
                        "ETA Pickup": f_eta.isoformat(),
                    }
                    if ship_ids:
                        fields["Linked Shipments"] = ship_ids
                    if quote_obj:
                        fields["Selected Quote"] = [quote_obj["id"]]

                    r = create_record(LOADS_TABLE, fields)
                    if r.status_code in (200, 201):
                        st.success(f"✅ Load {f_load_num} created successfully!")
                        st.session_state["show_load_form"] = False
                        st.rerun()
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")

        st.markdown('</div>', unsafe_allow_html=True)

# ── PRICING ──────────────────────────────────────────────────────────────────
elif pagina == "Pricing":
    st.markdown('<div class="xlt-page-title">Pricing</div>', unsafe_allow_html=True)

    with st.spinner("Loading..."):
        quotes    = get_pricing()
        shipments = get_all_shipments()

    filtro_pr = st.selectbox("Filter", ["All","Pending","Selected","Lost"], label_visibility="collapsed")

    filtered_pr = [q for q in quotes if filtro_pr == "All" or q["status"] == filtro_pr]
    st.markdown(f'<div class="xlt-page-sub">{len(filtered_pr)} quotes</div>', unsafe_allow_html=True)

    if filtered_pr:
        rows = ""
        for q in filtered_pr:
            rows += f"""<tr>
                <td><strong>Q-{q.get('quote_number','—')}</strong></td>
                <td>{q.get('linked_shipments','—')}</td>
                <td>{q.get('carrier','—')}</td>
                <td>${fmt_weight(q.get('freight_cost',''))}</td>
                <td>${fmt_weight(q.get('sales_value',''))}</td>
                <td>{q.get('freight_pct','—')}%</td>
                <td>${fmt_weight(q.get('profit',''))}</td>
                <td>{badge_html(q.get('status',''))}</td>
            </tr>"""
        st.markdown(f"""
        <div class="xlt-table-wrap">
        <table class="xlt-table">
        <thead><tr>
            <th>Quote #</th><th>Shipments</th><th>Carrier</th><th>Freight Cost</th><th>Sales Value</th>
            <th>Freight %</th><th>Profit</th><th>Status</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No quotes found.")

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("✏️  Update Quote Status", expanded=False):
        if quotes:
            col_q, col_s = st.columns(2)
            with col_q:
                quote_sel = st.selectbox("Quote", [f"Q-{q['quote_number']} — {q['carrier']}" for q in quotes])
            with col_s:
                nuevo_quote_status = st.selectbox("New Status", ["Pending","Selected","Lost"])
            if st.button("Update Quote Status", type="primary"):
                q_num = quote_sel.split(" — ")[0].replace("Q-","")
                obj = next((q for q in quotes if str(q["quote_number"]) == q_num), None)
                if obj:
                    r = update_record_api(PRICING_TABLE, obj["id"], {"Status": nuevo_quote_status})
                    if r.status_code == 200:
                        st.success(f"✅ {quote_sel} → {nuevo_quote_status}")
                        st.rerun()
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")
        else:
            st.info("No quotes available.")

    if st.session_state.get("show_quote_form"):
        st.markdown('<div class="xlt-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="xlt-form-title">➕ New Quote <span class="auto-badge">Q- # auto-generated · Freight % and Profit auto-calculated by Airtable</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="xlt-form-group-label">Shipments</div>', unsafe_allow_html=True)
        ship_options_pr = [f"{s['shipment_number']} — {s['customer']} · {s['city']}, {s['state']}"
                           for s in shipments if s["warehouse_status"] != "Shipped" and s.get("pick_up") != "Yes"]
        f_ship_pr = st.multiselect("Linked Shipments *", ship_options_pr)

        st.markdown('<div class="xlt-form-group-label">Carrier & Pricing</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            f_carrier = st.selectbox("Carrier *", CARRIERS)
        with c2:
            f_quote_status = st.selectbox("Status *", ["Pending","Selected","Lost"])

        c1, c2 = st.columns(2)
        with c1:
            f_freight = st.number_input("Freight Cost ($) *", min_value=0.0, step=50.0, format="%.2f")
        with c2:
            f_sales = st.number_input("Sales Value ($) *", min_value=0.0, step=50.0, format="%.2f")

        f_notes_pr = st.text_area("Notes", placeholder="Special requirements, restrictions...", height=70)

        col_cancel, col_spacer, col_save = st.columns([1, 3, 1])
        with col_cancel:
            if st.button("Cancel  ", use_container_width=True):
                st.session_state["show_quote_form"] = False
                st.rerun()
        with col_save:
            if st.button("Create Quote", type="primary", use_container_width=True):
                if not f_ship_pr or f_freight == 0:
                    st.error("Please fill in all required fields (*).")
                else:
                    ship_numbers_pr = [s.split(" — ")[0] for s in f_ship_pr]
                    ship_ids_pr = [s["id"] for s in shipments if s["shipment_number"] in ship_numbers_pr]

                    fields = {
                        "Carrier": f_carrier,
                        "Freight Cost": f_freight,
                        "Sales Value": f_sales,
                        "Status": f_quote_status,
                    }
                    if ship_ids_pr:
                        fields["Shipments"] = ship_ids_pr
                    if f_notes_pr:
                        fields["Notes"] = f_notes_pr

                    r = create_record(PRICING_TABLE, fields)
                    if r.status_code in (200, 201):
                        st.success("✅ Quote created successfully!")
                        st.session_state["show_quote_form"] = False
                        st.rerun()
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")

        st.markdown('</div>', unsafe_allow_html=True)

# ── UPDATES LOG ──────────────────────────────────────────────────────────────
elif pagina == "Updates Log":
    st.markdown('<div class="xlt-page-title">Updates Log</div>', unsafe_allow_html=True)

    with st.spinner("Loading..."):
        shipment_map = get_shipment_number_map()
        updates   = get_updates_log(shipment_map)
        shipments = get_all_shipments()
        loads     = get_loads(shipment_map)

    filtro_ul = st.selectbox("Filter", ["All"] + UPDATE_TYPES + ["Flagged"], label_visibility="collapsed")

    if filtro_ul == "Flagged":
        filtered_ul = [u for u in updates if u.get("attention_flag")]
    elif filtro_ul != "All":
        filtered_ul = [u for u in updates if u.get("type") == filtro_ul]
    else:
        filtered_ul = updates

    st.markdown(f'<div class="xlt-page-sub">{len(filtered_ul)} entries</div>', unsafe_allow_html=True)

    if filtered_ul:
        rows = ""
        for u in filtered_ul:
            flag = "⚑" if u.get("attention_flag") else "—"
            flag_style = "color:#b45309;font-weight:600;" if u.get("attention_flag") else "color:#94a3b8;"
            rows += f"""<tr>
                <td>{u.get('datetime','—')}</td>
                <td>{u.get('shipment','—')}</td>
                <td>{u.get('linked_load','—')}</td>
                <td>{u.get('type','—')}</td>
                <td>{u.get('description','—')}</td>
                <td>{u.get('responsible','—')}</td>
                <td style="{flag_style}">{flag}</td>
            </tr>"""
        st.markdown(f"""
        <div class="xlt-table-wrap">
        <table class="xlt-table">
        <thead><tr>
            <th>Date/Time</th><th>Shipment</th><th>Load</th><th>Type</th>
            <th>Description</th><th>Responsible</th><th>Flag</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No entries found.")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.get("show_update_form"):
        st.markdown('<div class="xlt-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="xlt-form-title">➕ New Entry <span class="auto-badge">Date/Time auto-generated</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="xlt-form-group-label">Linked Records</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            ship_opts_ul = [s["shipment_number"] for s in shipments]
            f_ship_ul = st.selectbox("Linked Shipment *", ["— Select —"] + ship_opts_ul)
        with c2:
            load_opts_ul = ["— None —"] + [l["load_number"] for l in loads]
            f_load_ul = st.selectbox("Linked Load (optional)", load_opts_ul)

        st.markdown('<div class="xlt-form-group-label">Details</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            f_type_ul = st.selectbox("Type *", UPDATE_TYPES)
        with c2:
            f_resp_ul = st.selectbox("Responsible *", RESPONSIBLE_OPTIONS)

        f_desc_ul = st.text_area("Description *", placeholder="What happened or was updated...", height=80)
        f_flag_ul = st.checkbox("⚑ Attention Flag — requires follow-up")

        col_cancel, col_spacer, col_save = st.columns([1, 3, 1])
        with col_cancel:
            if st.button("Cancel   ", use_container_width=True):
                st.session_state["show_update_form"] = False
                st.rerun()
        with col_save:
            if st.button("Save Entry", type="primary", use_container_width=True):
                if f_ship_ul == "— Select —" or not f_desc_ul:
                    st.error("Please fill in all required fields (*).")
                else:
                    ship_obj = next((s for s in shipments if s["shipment_number"] == f_ship_ul), None)
                    fields = {
                        "Type": f_type_ul,
                        "Description": f_desc_ul,
                        "Responsible": f_resp_ul,
                        "Attention Flag": f_flag_ul,
                    }
                    if ship_obj:
                        fields["Shipment"] = [ship_obj["id"]]

                    r = create_record(UPDATES_LOG_TABLE, fields)
                    if r.status_code in (200, 201):
                        st.success("✅ Entry saved successfully!")
                        st.session_state["show_update_form"] = False
                        st.rerun()
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")

        st.markdown('</div>', unsafe_allow_html=True)

# ── CONSOLIDATIONS ───────────────────────────────────────────────────────────
elif pagina == "Consolidations":
    st.markdown('<div class="xlt-page-title">Consolidation Detector</div>', unsafe_allow_html=True)
    st.markdown('<div class="xlt-page-sub">Analyzes active shipments per warehouse and detects consolidation opportunities</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        Analyzes shipments with status <strong>Pending Print</strong>, <strong>In Progress</strong> and <strong>Ready</strong> (excludes Pick Up = Yes).
        Texas and Florida shipments are never compared against each other — results are grouped by warehouse.<br>
        <strong>Type A</strong> — Two shipments without a load, close destinations, fit in one trailer<br>
        <strong>Type B</strong> — A shipment without load that fits in an existing load with available space<br>
        <strong>Type C</strong> — Two shipments with small trailers assigned that together justify upgrading to a larger trailer
    </div>
    """, unsafe_allow_html=True)

    if st.button("Detect Opportunities", type="primary"):
        with st.spinner("Analyzing active shipments by warehouse..."):
            st.session_state["consolidaciones"] = detectar_consolidaciones()

    if "consolidaciones" in st.session_state:
        resultado = st.session_state["consolidaciones"]
        total = sum(len(v) for v in resultado.values())

        if total:
            st.success(f"{total} opportunity(ies) detected across both warehouses")
        else:
            st.warning("No consolidation opportunities detected with current active shipments.")

        for warehouse in ["Texas", "Florida"]:
            oportunidades = resultado.get(warehouse, [])
            st.markdown(f'<div class="xlt-section-title">📍 {warehouse} Warehouse — {len(oportunidades)} opportunity(ies)</div>', unsafe_allow_html=True)

            if not oportunidades:
                st.info(f"No opportunities detected for {warehouse}.")
                continue

            for i, op in enumerate(oportunidades, 1):
                tipo = op.get("tipo", "A")
                if tipo in ("A", "C"):
                    title = f"#{i} — Type {tipo} — {op['destino_1']} + {op['destino_2']}"
                else:
                    title = f"#{i} — Type {tipo} — {op['destino_1']} → {op.get('load_existente','')}"

                with st.expander(title):
                    st.markdown(f"*{op['descripcion']}*")

                    if tipo in ("A", "C"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Distance", f"{op['distancia_millas']} miles")
                        c2.metric("Combined weight", f"{op['peso_combinado']:,} lbs")
                        c3.metric("Available space", f"{op.get('espacio_disponible', 0):,} lbs")

                        def _status_badge(status):
                            colors = {
                                "Ready": "background:#F0FDF4;color:#15803d",
                                "In Progress": "background:#FFFBEB;color:#b45309",
                                "Pending Print": "background:#EFF6FF;color:#1d4ed8",
                            }
                            style = colors.get(status, "background:#F1EFE8;color:#5F5E5A")
                            return f'<span style="{style};padding:2px 8px;border-radius:20px;font-size:12px;font-weight:500;">{status}</span>'

                        def _load_badge(load):
                            if load:
                                return f'<span style="background:#F1EFE8;color:#5F5E5A;padding:2px 8px;border-radius:20px;font-size:12px;font-weight:500;">🚛 {load}</span>'
                            return f'<span style="background:#FCEBEB;color:#A32D2D;padding:2px 8px;border-radius:20px;font-size:12px;font-weight:500;">No load</span>'

                        st.markdown(f"""
                        <div style="border:0.5px solid #f0f0f0;border-radius:8px;overflow:hidden;margin-top:8px;">
                          <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:0.5px solid #f0f0f0;">
                            <span style="font-size:13px;font-weight:500;min-width:130px;">{op['shipment_1']}</span>
                            <span style="font-size:12px;color:#64748b;flex:1;">{op['destino_1']} · {op['peso_1']:,} lbs</span>
                            {_status_badge(op.get('status_1',''))}
                            {_load_badge(op.get('load_1',''))}
                          </div>
                          <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;">
                            <span style="font-size:13px;font-weight:500;min-width:130px;">{op['shipment_2']}</span>
                            <span style="font-size:12px;color:#64748b;flex:1;">{op['destino_2']} · {op['peso_2']:,} lbs</span>
                            {_status_badge(op.get('status_2',''))}
                            {_load_badge(op.get('load_2',''))}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if tipo == "C":
                            st.caption(f"Currently: {op.get('trailer_actual_1','')} + {op.get('trailer_actual_2','')} — Exact savings vary by broker and route.")
                        st.markdown(f"**Suggested:** {op['trailer_sugerido']}")

                        # Warning if any shipment already has a load
                        if op.get('load_1') or op.get('load_2'):
                            st.warning("⚠️ One or more shipments already have a load assigned — verify before consolidating.")

                    elif tipo == "B":
                        c1, c2 = st.columns(2)
                        c1.metric("Distance", f"{op['distancia_millas']} miles")
                        c2.metric("Available space in load", f"{op['espacio_disponible_en_load']:,} lbs")

                        def _status_badge_b(status):
                            colors = {
                                "Ready": "background:#F0FDF4;color:#15803d",
                                "In Progress": "background:#FFFBEB;color:#b45309",
                                "Pending Print": "background:#EFF6FF;color:#1d4ed8",
                            }
                            style = colors.get(status, "background:#F1EFE8;color:#5F5E5A")
                            return f'<span style="{style};padding:2px 8px;border-radius:20px;font-size:12px;font-weight:500;">{status}</span>'

                        st.markdown(f"""
                        <div style="border:0.5px solid #f0f0f0;border-radius:8px;overflow:hidden;margin-top:8px;">
                          <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:0.5px solid #f0f0f0;">
                            <span style="font-size:13px;font-weight:500;min-width:130px;">{op['shipment_1']}</span>
                            <span style="font-size:12px;color:#64748b;flex:1;">{op['destino_1']} · {op['peso_1']:,} lbs</span>
                            {_status_badge_b(op.get('status_1',''))}
                          </div>
                          <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;">
                            <span style="font-size:13px;font-weight:500;min-width:130px;">{op.get('load_existente','')}</span>
                            <span style="font-size:12px;color:#64748b;flex:1;">{op.get('load_destino','')} · existing load</span>
                            <span style="background:#F1EFE8;color:#5F5E5A;padding:2px 8px;border-radius:20px;font-size:12px;font-weight:500;">🚛 Active load</span>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"**Suggested:** {op['trailer_sugerido']}")

# ── LIVE MAP ──────────────────────────────────────────────────────────────────
elif pagina == "Live Map":
    st.markdown('<div class="xlt-page-title">Live Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="xlt-page-sub">Loads ready for pickup, plotted by destination (data refreshes every 60s)</div>', unsafe_allow_html=True)

    with st.spinner("Loading loads..."):
        data = _get_live_map_data()

    with st.expander("🔧 Debug: raw Load data from Airtable"):
        st.write("Load Status counts across all loads:", data["status_counts"])
        st.write("Warehouse value counts across all loads:", data["warehouse_counts"])
        st.write("Raw fields for the first Load record returned by Airtable:")
        st.json(data["raw_first_fields"])

    c1, c2, c3, c4 = st.columns(4)
    live_map_metrics = [
        (c1, COLOR_TEXAS,       data["tx_loads"],           "Texas Loads"),
        (c2, "#b45309",         data["fl_loads"],           "Florida Loads"),
        (c3, COLOR_CONSOLIDATED, data["consolidated_pairs"], "Consolidated Pairs"),
        (c4, "#64748b",         data["total_loads"],        "Total"),
    ]
    for col, color, val, lbl in live_map_metrics:
        with col:
            st.markdown(f"""
            <div class="xlt-metric">
                <div class="xlt-metric-val">{val}</div>
                <div class="xlt-metric-lbl">{lbl}</div>
                <div class="xlt-metric-bar" style="background:{color};"></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    def _star_icon(hex_color):
        return folium.DivIcon(html=f'<div style="font-size:26px;line-height:1;color:{hex_color};text-shadow:0 0 3px rgba(0,0,0,0.35);">★</div>')

    m = folium.Map(location=[31.5, -88.0], zoom_start=6, tiles="cartodbpositron")
    folium.Marker(WAREHOUSE_COORDS["Texas"], tooltip="Texas Warehouse",
                  icon=_star_icon(COLOR_TEXAS)).add_to(m)
    folium.Marker(WAREHOUSE_COORDS["Florida"], tooltip="Florida Warehouse",
                  icon=_star_icon(COLOR_FLORIDA)).add_to(m)

    for mk in data["markers"]:
        wh_coords = WAREHOUSE_COORDS.get(mk["warehouse"])
        popup_lines = [
            f"<b>Load:</b> {html.escape(str(mk['load_number']))}",
            f"<b>Carrier:</b> {html.escape(str(mk['carrier']))}",
            f"<b>This shipment:</b> {html.escape(str(mk['shipment_number']))} → {html.escape(str(mk['destination']))}",
        ]
        for other in mk.get("others", []):
            popup_lines.append(
                f"<b>Also in this load:</b> {html.escape(str(other['shipment_number']))} → {html.escape(str(other['destination']))}"
            )
        popup_html = "<br>".join(popup_lines)

        folium.CircleMarker(
            location=mk["coords"], radius=7, color=mk["color"], fill=True,
            fill_color=mk["color"], fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(m)

        if wh_coords:
            folium.PolyLine([wh_coords, mk["coords"]], color=mk["color"], weight=1.5, opacity=0.5).add_to(m)

    st.markdown(f"""
    <div style="position:fixed; bottom:30px; left:40px; z-index:9999; background:#ffffffee;
                border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px;
                box-shadow:0 4px 14px rgba(0,0,0,0.08); font-size:12px; color:#0f172a; max-width:220px;">
      <div style="font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;font-size:11px;margin-bottom:8px;">Legend</div>
      <div style="margin-bottom:5px;"><span style="color:{COLOR_TEXAS};">★</span> Blue star — Texas warehouse</div>
      <div style="margin-bottom:5px;"><span style="color:{COLOR_FLORIDA};">★</span> Yellow star — Florida warehouse</div>
      <div style="margin-bottom:5px;"><span style="color:{COLOR_TEXAS};">●</span> Blue circle — Texas load</div>
      <div style="margin-bottom:5px;"><span style="color:{COLOR_FLORIDA};">●</span> Yellow circle — Florida load</div>
      <div><span style="color:{COLOR_CONSOLIDATED};">●</span> Orange circle — Consolidated load</div>
    </div>
    """, unsafe_allow_html=True)

    st_folium(m, width=None, height=560)

# ── TRUCK BUILDER ─────────────────────────────────────────────────────────────
elif pagina == "Truck Builder":
    st.markdown('<div class="xlt-page-title">Truck Builder</div>', unsafe_allow_html=True)
    st.markdown('<div class="xlt-page-sub">Opens in a new tab for full interactivity</div>', unsafe_allow_html=True)
    st.link_button("Open Truck Builder 🚛", "https://alejandrojsuarezp.github.io/alva-logistics-tracker/truck_builder.html", type="primary")