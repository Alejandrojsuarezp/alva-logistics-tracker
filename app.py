# ============================================
# X LOGISTICS TRACKER - Web Interface
# ============================================

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
from config import AIRTABLE_TOKEN, SHIPMENTS_TABLE, LOADS_TABLE, PRICING_TABLE, UPDATES_LOG_TABLE
from airtable_connection import get_all_shipments, get_loads, get_pricing, get_updates_log
from consolidation_detector import detectar_consolidaciones

st.set_page_config(
    page_title="X Logistics Tracker",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── GLOBAL CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import font */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');

/* Reset & base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Hide Streamlit default elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem 2rem !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #f0f0f0;
    width: 210px !important;
    min-width: 210px !important;
}
section[data-testid="stSidebar"] > div {
    padding: 0 !important;
}

/* Brand */
.xlt-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 20px 16px 16px 16px;
    border-bottom: 1px solid #f0f0f0;
    margin-bottom: 8px;
}
.xlt-brand-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #185FA5;
    flex-shrink: 0;
}
.xlt-brand-name {
    font-size: 13px;
    font-weight: 600;
    color: #0f172a;
    line-height: 1.2;
}

/* Nav section label */
.xlt-nav-section {
    font-size: 9px;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: .07em;
    padding: 10px 16px 4px 16px;
}

/* Nav divider */
.xlt-nav-div {
    height: 1px;
    background: #f0f0f0;
    margin: 6px 12px;
}

/* Override Streamlit radio */
div[data-testid="stSidebarNav"] { display: none; }

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
}
.badge-pending  { background: #EFF6FF; color: #1d4ed8; }
.badge-progress { background: #FFFBEB; color: #b45309; }
.badge-ready    { background: #F0FDF4; color: #15803d; }
.badge-shipped  { background: #F8FAFC; color: #64748b; }

/* Page title */
.xlt-page-title {
    font-size: 20px;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 2px;
}
.xlt-page-sub {
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 1.25rem;
}

/* Metric card */
.xlt-metric {
    background: #ffffff;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    padding: 14px 16px;
}
.xlt-metric-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
    font-size: 15px;
}
.xlt-metric-val {
    font-size: 26px;
    font-weight: 600;
    color: #0f172a;
    line-height: 1;
}
.xlt-metric-lbl {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 3px;
}

/* Table */
.xlt-table-wrap {
    background: #ffffff;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    overflow: hidden;
}
.xlt-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.xlt-table th {
    background: #fafafa;
    padding: 9px 14px;
    text-align: left;
    font-size: 11px;
    font-weight: 500;
    color: #94a3b8;
    border-bottom: 1px solid #f0f0f0;
}
.xlt-table td {
    padding: 9px 14px;
    border-bottom: 1px solid #f8f8f8;
    color: #0f172a;
    font-size: 12px;
}
.xlt-table tr:last-child td { border-bottom: none; }
.xlt-table tr:hover td { background: #fafbff; }

/* Section card */
.xlt-section-card {
    background: #ffffff;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 1rem;
}
.xlt-section-title {
    font-size: 13px;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Form styling */
.xlt-form-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin-top: 1rem;
}
.xlt-form-title {
    font-size: 14px;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    gap: 7px;
}
.auto-badge {
    font-size: 10px;
    background: #EFF6FF;
    color: #185FA5;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 500;
}
.info-box {
    background: #F8FAFC;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    color: #64748b;
    margin-bottom: 8px;
}

/* Streamlit widget overrides */
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stDateInput"] label,
div[data-testid="stMultiSelect"] label {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #64748b !important;
}
div[data-testid="stButton"] button {
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ── HEADERS FOR AIRTABLE ────────────────────────────────────────────────────
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}
BASE_ID = st.secrets["BASE_ID"]

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
    response = requests.post(url, headers=HEADERS, json={"fields": fields})
    return response

def update_record_api(table_id, record_id, fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}/{record_id}"
    response = requests.patch(url, headers=HEADERS, json={"fields": fields})
    return response

# ── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="xlt-brand">
        <div class="xlt-brand-dot"></div>
        <div class="xlt-brand-name">X Logistics<br>Tracker</div>
    </div>
    <div class="xlt-nav-section">Main</div>
    """, unsafe_allow_html=True)

    pagina = st.radio("nav", [
        "🏠  Dashboard",
        "📦  Shipments",
        "🚛  Loads",
        "💲  Pricing",
        "📋  Updates Log",
        "🔄  Consolidations",
        "🔧  Truck Builder",
    ], label_visibility="collapsed")

    st.markdown(f"""
    <div class="xlt-nav-div"></div>
    <div style="padding:12px 16px;font-size:11px;color:#94a3b8;">
        Texas · {datetime.now().strftime('%b %d, %Y')}
    </div>
    """, unsafe_allow_html=True)

# ── DASHBOARD ───────────────────────────────────────────────────────────────
if pagina == "🏠  Dashboard":
    st.markdown('<div class="xlt-page-title">Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="xlt-page-sub">{datetime.now().strftime("%A, %B %d %Y")} · Texas</div>', unsafe_allow_html=True)

    with st.spinner("Loading data..."):
        shipments = get_all_shipments()
        loads = get_loads()

    pending    = [s for s in shipments if s["warehouse_status"] == "Pending Print"]
    in_prog    = [s for s in shipments if s["warehouse_status"] == "In Progress"]
    ready      = [s for s in shipments if s["warehouse_status"] == "Ready"]
    shipped    = [s for s in shipments if s["warehouse_status"] == "Shipped"]
    active_lds = [l for l in loads if l["load_status"] not in ("Shipped", "Delivered")]

    # Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, "⏳", "#EFF6FF", "#185FA5", len(pending),   "Pending Print"),
        (c2, "⚙️", "#FFFBEB", "#b45309", len(in_prog),   "In Progress"),
        (c3, "✅", "#F0FDF4", "#15803d", len(ready),     "Ready"),
        (c4, "🚛", "#F8FAFC", "#64748b", len(shipped),   "Shipped"),
        (c5, "📦", "#EEF2FF", "#4338ca", len(active_lds),"Active Loads"),
    ]
    for col, icon, bg, color, val, lbl in metrics:
        with col:
            st.markdown(f"""
            <div class="xlt-metric">
                <div class="xlt-metric-icon" style="background:{bg};color:{color};">{icon}</div>
                <div class="xlt-metric-val">{val}</div>
                <div class="xlt-metric-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Active Shipments
    with col_l:
        activos = pending + in_prog + ready
        st.markdown('<div class="xlt-section-title">🚢 Active Shipments</div>', unsafe_allow_html=True)
        if activos:
            rows = ""
            for s in activos[:8]:
                rows += f"""<tr>
                    <td>{s.get('shipment_number','—')}</td>
                    <td>{s.get('customer','—')}</td>
                    <td>{s.get('city','')}, {s.get('state','')}</td>
                    <td>{fmt_weight(s.get('weight',''))}</td>
                    <td>{badge_html(s.get('warehouse_status',''))}</td>
                </tr>"""
            st.markdown(f"""
            <div class="xlt-table-wrap">
            <table class="xlt-table">
            <thead><tr><th>Shipment</th><th>Customer</th><th>Destination</th><th>Weight</th><th>Status</th></tr></thead>
            <tbody>{rows}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else:
            st.info("No active shipments.")

    # Active Loads
    with col_r:
        st.markdown('<div class="xlt-section-title">📦 Active Loads</div>', unsafe_allow_html=True)
        if active_lds:
            rows = ""
            for l in active_lds[:8]:
                rows += f"""<tr>
                    <td>{l.get('load_number','—')}</td>
                    <td>{l.get('carrier','—')}</td>
                    <td>{fmt_weight(l.get('total_weight',''))}</td>
                    <td>{badge_html(l.get('load_status',''))}</td>
                    <td>{l.get('eta_pickup','—')}</td>
                </tr>"""
            st.markdown(f"""
            <div class="xlt-table-wrap">
            <table class="xlt-table">
            <thead><tr><th>Load #</th><th>Carrier</th><th>Weight</th><th>Status</th><th>ETA Pickup</th></tr></thead>
            <tbody>{rows}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else:
            st.info("No active loads.")

# ── SHIPMENTS ───────────────────────────────────────────────────────────────
elif pagina == "📦  Shipments":
    st.markdown('<div class="xlt-page-title">Shipments</div>', unsafe_allow_html=True)

    with st.spinner("Loading shipments..."):
        shipments = get_all_shipments()

    # Filter + count
    col_f, col_btn = st.columns([4, 1])
    with col_f:
        filtro = st.selectbox("Filter by status", ["All","Pending Print","In Progress","Ready","Shipped"], label_visibility="collapsed")
    with col_btn:
        show_form = st.button("＋  New Shipment", type="primary", use_container_width=True)

    filtered = [s for s in shipments if filtro == "All" or s["warehouse_status"] == filtro]
    st.markdown(f'<div class="xlt-page-sub">{len(filtered)} shipments</div>', unsafe_allow_html=True)

    # Table
    if filtered:
        rows = ""
        for s in filtered:
            rows += f"""<tr>
                <td><strong>{s.get('shipment_number','—')}</strong></td>
                <td>{s.get('customer','—')}</td>
                <td>{s.get('city','')}, {s.get('state','')}</td>
                <td>{s.get('zip_code','—')}</td>
                <td>{fmt_weight(s.get('weight',''))}</td>
                <td>{s.get('bundles','—')}</td>
                <td>{s.get('trailer_type','—')}</td>
                <td>{fmt_date(s.get('delivery_date',''))}</td>
                <td>{badge_html(s.get('warehouse_status',''))}</td>
            </tr>"""
        st.markdown(f"""
        <div class="xlt-table-wrap">
        <table class="xlt-table">
        <thead><tr>
            <th>Shipment #</th><th>Customer</th><th>City, State</th><th>ZIP</th>
            <th>Weight</th><th>Bundles</th><th>Trailer</th><th>Delivery</th><th>Status</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No shipments found.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Update Status
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

    # New Shipment Form
    if show_form:
        st.session_state["show_shipment_form"] = True

    if st.session_state.get("show_shipment_form"):
        st.markdown('<div class="xlt-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="xlt-form-title">➕ New Shipment <span class="auto-badge">Order Date auto-generated · Status starts as Pending Print</span></div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            f_shipment_num = st.text_input("Shipment Number *", placeholder="e.g. SH-0042")
        with c2:
            f_customer = st.text_input("Customer *", placeholder="Company name")

        c1, c2 = st.columns(2)
        with c1:
            f_email = st.text_input("Customer Email", placeholder="email@company.com")
        with c2:
            f_delivery = st.date_input("Requested Delivery Date *", min_value=date.today())

        c1, c2, c3 = st.columns(3)
        with c1:
            f_city = st.text_input("City *", placeholder="Houston")
        with c2:
            f_state = st.selectbox("State *", [
                "TX","FL","AL","AR","AZ","CA","CO","GA","ID","IL","IN","KS","KY",
                "LA","MI","MN","MO","MS","MT","NC","ND","NE","NM","NV","OH","OK",
                "OR","SC","SD","TN","UT","VA","WA","WI","WY"
            ])
        with c3:
            f_zip = st.text_input("ZIP Code", placeholder="77001")

        c1, c2, c3 = st.columns(3)
        with c1:
            f_trailer = st.selectbox("Trailer Type Needed *", [
                "Flatbed 48'","Flatbed 53'","Stepdeck 48'","Stepdeck 53'","Hotshot 40'"
            ])
        with c2:
            f_weight = st.number_input("Weight (lbs) *", min_value=0, step=100)
        with c3:
            f_bundles = st.number_input("Bundles *", min_value=0, step=1)

        f_notes = st.text_area("Notes", placeholder="Special instructions, gate codes, contacts...", height=80)

        col_cancel, col_spacer, col_save = st.columns([1, 3, 1])
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state["show_shipment_form"] = False
                st.rerun()
        with col_save:
            if st.button("Create Shipment", type="primary", use_container_width=True):
                if not f_shipment_num or not f_customer or not f_city:
                    st.error("Please fill in all required fields (*).")
                else:
                    fields = {
                        "Shipment Number": f_shipment_num,
                        "Customer": f_customer,
                        "City": f_city,
                        "State": f_state,
                        "ZIP Code": f_zip,
                        "Trailer Type Needed": f_trailer,
                        "Weight": f_weight,
                        "Bundles": int(f_bundles),
                        "Warehouse Status": "Pending Print",
                        "Order Date": date.today().isoformat(),
                        "Requested Delivery Date": f_delivery.isoformat(),
                        "Notes": f_notes,
                    }
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
elif pagina == "🚛  Loads":
    st.markdown('<div class="xlt-page-title">Loads</div>', unsafe_allow_html=True)
    st.info("Coming soon — Loads page with full form is being built.")

# ── PRICING ──────────────────────────────────────────────────────────────────
elif pagina == "💲  Pricing":
    st.markdown('<div class="xlt-page-title">Pricing</div>', unsafe_allow_html=True)
    st.info("Coming soon — Pricing page with full form is being built.")

# ── UPDATES LOG ──────────────────────────────────────────────────────────────
elif pagina == "📋  Updates Log":
    st.markdown('<div class="xlt-page-title">Updates Log</div>', unsafe_allow_html=True)
    st.info("Coming soon — Updates Log page with full form is being built.")

# ── CONSOLIDATIONS ───────────────────────────────────────────────────────────
elif pagina == "🔄  Consolidations":
    st.markdown('<div class="xlt-page-title">Consolidation Detector</div>', unsafe_allow_html=True)
    st.info("Coming soon — Consolidations page is being rebuilt with Type A, B and C detection.")

# ── TRUCK BUILDER ─────────────────────────────────────────────────────────────
elif pagina == "🔧  Truck Builder":
    st.markdown('<div class="xlt-page-title">Truck Builder</div>', unsafe_allow_html=True)
    st.markdown('<div class="xlt-page-sub">Opens in a new tab for full interactivity</div>', unsafe_allow_html=True)
    st.link_button("Open Truck Builder 🚛", "https://alejandrojsuarezp.github.io/alva-logistics-tracker/truck_builder.html", type="primary")