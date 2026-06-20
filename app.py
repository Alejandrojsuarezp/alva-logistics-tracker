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
    font-size: 11px;
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
div[data-testid="stSidebar"] div[role="radiogroup"] label {
    font-size: 14px !important;
    padding: 6px 8px !important;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label p {
    font-size: 14px !important;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
}
.badge-pending  { background: #EFF6FF; color: #1d4ed8; }
.badge-progress { background: #FFFBEB; color: #b45309; }
.badge-ready    { background: #F0FDF4; color: #15803d; }
.badge-shipped  { background: #F8FAFC; color: #64748b; }

/* Page title */
.xlt-page-title {
    font-size: 24px;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 2px;
}
.xlt-page-sub {
    font-size: 14px;
    color: #94a3b8;
    margin-bottom: 1.25rem;
}

/* Metric card */
.xlt-metric {
    background: #ffffff;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    padding: 16px;
}
.xlt-metric-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
    font-size: 16px;
}
.xlt-metric-val {
    font-size: 28px;
    font-weight: 600;
    color: #0f172a;
    line-height: 1;
}
.xlt-metric-lbl {
    font-size: 13px;
    color: #94a3b8;
    margin-top: 4px;
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
    font-size: 14px;
}
.xlt-table th {
    background: #fafafa;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    color: #94a3b8;
    border-bottom: 1px solid #f0f0f0;
}
.xlt-table td {
    padding: 10px 16px;
    border-bottom: 1px solid #f8f8f8;
    color: #0f172a;
    font-size: 14px;
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
    font-size: 15px;
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
    font-size: 15px;
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
    font-size: 11px;
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
    font-size: 13px;
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
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #64748b !important;
}
div[data-testid="stButton"] button {
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 14px !important;
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
        "Dashboard",
        "Shipments",
        "Loads",
        "Pricing",
        "Updates Log",
        "Consolidations",
        "Truck Builder",
    ], label_visibility="collapsed")

    st.markdown(f"""
    <div class="xlt-nav-div"></div>
    <div style="padding:12px 16px;font-size:11px;color:#94a3b8;">
        Texas · {datetime.now().strftime('%b %d, %Y')}
    </div>
    """, unsafe_allow_html=True)

# ── DASHBOARD ───────────────────────────────────────────────────────────────
if pagina == "Dashboard":
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
                        "Trailer Type Needed": f_trailer,
                        "Weight": f_weight,
                        "Bundles": int(f_bundles),
                        "Warehouse Status": "Pending Print",
                        "Order Date": date.today().isoformat(),
                        "Requested Delivery Date": f_delivery.isoformat(),
                        "Notes": f_notes,
                    }
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
        loads    = get_loads()
        quotes   = get_pricing()
        shipments = get_all_shipments()

    col_f, col_btn = st.columns([4, 1])
    with col_f:
        filtro_ld = st.selectbox("Filter", ["All","Scheduled","In Transit","Shipped"], label_visibility="collapsed")
    with col_btn:
        show_load_form = st.button("＋  New Load", type="primary", use_container_width=True)

    filtered_ld = [l for l in loads if filtro_ld == "All" or l["load_status"] == filtro_ld]
    st.markdown(f'<div class="xlt-page-sub">{len(filtered_ld)} loads</div>', unsafe_allow_html=True)

    if filtered_ld:
        rows = ""
        for l in filtered_ld:
            rows += f"""<tr>
                <td><strong>{l.get('load_number','—')}</strong></td>
                <td>{l.get('carrier','—')}</td>
                <td>{fmt_weight(l.get('total_weight',''))}</td>
                <td>{l.get('total_bundles','—')}</td>
                <td>{l.get('load_status','—')}</td>
                <td>{l.get('eta_pickup','—')}</td>
                <td>${fmt_weight(l.get('freight_cost',''))}</td>
                <td>${fmt_weight(l.get('sales_value',''))}</td>
            </tr>"""
        st.markdown(f"""
        <div class="xlt-table-wrap">
        <table class="xlt-table">
        <thead><tr>
            <th>Load #</th><th>Carrier</th><th>Weight</th><th>Bundles</th>
            <th>Status</th><th>ETA Pickup</th><th>Freight Cost</th><th>Sales Value</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No loads found.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Update Load Status
    with st.expander("✏️  Update Load Status", expanded=False):
        if loads:
            col_l, col_s = st.columns(2)
            with col_l:
                load_sel = st.selectbox("Load", [l["load_number"] for l in loads])
            with col_s:
                nuevo_load_status = st.selectbox("New Status", ["Scheduled","In Transit","Shipped"])
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

    # New Load Form
    if show_load_form:
        st.session_state["show_load_form"] = True

    if st.session_state.get("show_load_form"):
        st.markdown('<div class="xlt-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="xlt-form-title">➕ New Load</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            f_load_num = st.text_input("Load Number * (from broker)", placeholder="e.g. LD-00123")
        with c2:
            f_load_status = st.selectbox("Load Status *", ["Scheduled","In Transit","Shipped"])

        # Linked Shipments — multiselect
        ship_options = [f"{s['shipment_number']} — {s['customer']} · {s['city']}, {s['state']}"
                        for s in shipments if s["warehouse_status"] != "Shipped"]
        f_shipments = st.multiselect("Linked Shipments *", ship_options)

        # Selected Quote — only Pending quotes
        pending_quotes = [q for q in quotes if q.get("status") == "Pending"]
        quote_options  = [f"Q-{q['quote_number']} — {q['carrier']} · ${fmt_weight(q.get('freight_cost',''))}"
                          for q in pending_quotes]
        f_quote = st.selectbox("Selected Quote from Pricing *", ["— Select —"] + quote_options)

        c1, c2 = st.columns(2)
        with c1:
            f_trailer_ld = st.selectbox("Trailer Type *", [
                "Flatbed 48'","Flatbed 53'","Stepdeck 48'","Stepdeck 53'","Hotshot 40'"
            ])
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
                    # Get record IDs
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

    col_f, col_btn = st.columns([4, 1])
    with col_f:
        filtro_pr = st.selectbox("Filter", ["All","Pending","Selected","Lost"], label_visibility="collapsed")
    with col_btn:
        show_quote_form = st.button("＋  New Quote", type="primary", use_container_width=True)

    filtered_pr = [q for q in quotes if filtro_pr == "All" or q["status"] == filtro_pr]
    st.markdown(f'<div class="xlt-page-sub">{len(filtered_pr)} quotes</div>', unsafe_allow_html=True)

    if filtered_pr:
        rows = ""
        for q in filtered_pr:
            rows += f"""<tr>
                <td><strong>Q-{q.get('quote_number','—')}</strong></td>
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
            <th>Quote #</th><th>Carrier</th><th>Freight Cost</th><th>Sales Value</th>
            <th>Freight %</th><th>Profit</th><th>Status</th>
        </tr></thead>
        <tbody>{rows}</tbody>
        </table></div>""", unsafe_allow_html=True)
    else:
        st.info("No quotes found.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Update Quote Status
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

    # New Quote Form
    if show_quote_form:
        st.session_state["show_quote_form"] = True

    if st.session_state.get("show_quote_form"):
        st.markdown('<div class="xlt-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="xlt-form-title">➕ New Quote <span class="auto-badge">Q- # auto-generated · Freight % and Profit auto-calculated by Airtable</span></div>', unsafe_allow_html=True)

        # Linked Shipments
        ship_options_pr = [f"{s['shipment_number']} — {s['customer']} · {s['city']}, {s['state']}"
                           for s in shipments if s["warehouse_status"] != "Shipped"]
        f_ship_pr = st.multiselect("Linked Shipments *", ship_options_pr)

        c1, c2 = st.columns(2)
        with c1:
            # Carrier list from Airtable single select — common carriers
            f_carrier = st.selectbox("Carrier *", [
                "Cowntown Logistics","TQL","Ecologistics",
                "Worldwide Logistics","ICM Logistics","West Jersey Express"
            ])
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
        updates   = get_updates_log()
        shipments = get_all_shipments()
        loads     = get_loads()

    col_f, col_btn = st.columns([4, 1])
    with col_f:
        filtro_ul = st.selectbox("Filter", ["All","Status Change","Note","Issue","Flagged"], label_visibility="collapsed")
    with col_btn:
        show_update_form = st.button("＋  New Entry", type="primary", use_container_width=True)

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

    # New Entry Form
    if show_update_form:
        st.session_state["show_update_form"] = True

    if st.session_state.get("show_update_form"):
        st.markdown('<div class="xlt-form-card">', unsafe_allow_html=True)
        st.markdown('<div class="xlt-form-title">➕ New Entry <span class="auto-badge">Date/Time auto-generated</span></div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            ship_opts_ul = [s["shipment_number"] for s in shipments]
            f_ship_ul = st.selectbox("Linked Shipment *", ["— Select —"] + ship_opts_ul)
        with c2:
            load_opts_ul = ["— None —"] + [l["load_number"] for l in loads]
            f_load_ul = st.selectbox("Linked Load (optional)", load_opts_ul)

        c1, c2 = st.columns(2)
        with c1:
            f_type_ul = st.selectbox("Type *", ["Status Change","Note","Issue","Other"])
        with c2:
            f_resp_ul = st.selectbox("Responsible *", ["Alejandro","Yeral","Daniel","Humberto","Other"])

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
                        "Date/Time": datetime.now().isoformat(),
                    }
                    if ship_obj:
                        fields["Shipment"] = [ship_obj["id"]]
                    if f_load_ul != "— None —":
                        load_obj = next((l for l in loads if l["load_number"] == f_load_ul), None)
                        if load_obj:
                            fields["Linked Load"] = [load_obj["id"]]

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
    st.markdown('<div class="xlt-page-sub">Analyzes active shipments and detects consolidation opportunities</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        Analyzes shipments with status <strong>Pending Print</strong>, <strong>In Progress</strong> and <strong>Ready</strong>.
        Detects three types of opportunities:<br>
        <strong>Type A</strong> — Two shipments without a load, close destinations, fit in one trailer<br>
        <strong>Type B</strong> — A shipment without load that fits in an existing load with available space<br>
        <strong>Type C</strong> — Two shipments with small trailers assigned that together justify upgrading to a larger trailer
    </div>
    """, unsafe_allow_html=True)

    if st.button("Detect Opportunities", type="primary"):
        with st.spinner("Analyzing active shipments..."):
            st.session_state["consolidaciones"] = detectar_consolidaciones()

    if "consolidaciones" in st.session_state:
        oportunidades = st.session_state["consolidaciones"]
        if oportunidades:
            st.success(f"{len(oportunidades)} opportunity(ies) detected")
            for i, op in enumerate(oportunidades, 1):
                with st.expander(f"Opportunity #{i} — {op['destino_1']} + {op['destino_2']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Distance", f"{op['distancia_millas']} miles")
                    c2.metric("Combined weight", f"{op['peso_combinado']:,} lbs")
                    c3.metric("Available space", f"{op['espacio_disponible']:,} lbs")
                    st.markdown(f"**Shipment 1:** {op['shipment_1']} → {op['destino_1']} ({op['peso_1']:,} lbs)")
                    st.markdown(f"**Shipment 2:** {op['shipment_2']} → {op['destino_2']} ({op['peso_2']:,} lbs)")
                    st.markdown(f"**Suggested trailer:** {op['trailer_sugerido']}")
        else:
            st.warning("No consolidation opportunities detected with current active shipments.")

# ── TRUCK BUILDER ─────────────────────────────────────────────────────────────
elif pagina == "Truck Builder":
    st.markdown('<div class="xlt-page-title">Truck Builder</div>', unsafe_allow_html=True)
    st.markdown('<div class="xlt-page-sub">Opens in a new tab for full interactivity</div>', unsafe_allow_html=True)
    st.link_button("Open Truck Builder 🚛", "https://alejandrojsuarezp.github.io/alva-logistics-tracker/truck_builder.html", type="primary")
