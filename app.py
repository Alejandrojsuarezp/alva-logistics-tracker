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
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from config import AIRTABLE_TOKEN, SHIPMENTS_TABLE, LOADS_TABLE, PRICING_TABLE, UPDATES_LOG_TABLE
from airtable_connection import get_all_shipments, get_loads, get_pricing, get_updates_log, get_shipment_number_map, get_records
from consolidation_detector import detectar_consolidaciones, get_shipment_coordinates

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

/* ── CONSOLIDATIONS ────────────────────────────────────────────────────────── */
.xlt-cons-card {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 14px;
}
.xlt-cons-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid #e7e5e4;
    flex-wrap: wrap;
}
.xlt-cons-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
.xlt-cons-header-number {
    font-size: 15px;
    font-weight: 700;
    color: #1c1917;
}
.xlt-cons-header-dest {
    font-size: 13px;
    color: #78716c;
}
.xlt-cons-header-trailer {
    font-size: 12px;
    color: #a8a29e;
    background: #f5f5f4;
    border-radius: 4px;
    padding: 2px 7px;
}
.xlt-cons-header-weight {
    font-size: 15px;
    font-weight: 700;
    color: #1c1917;
    white-space: nowrap;
}
.xlt-cons-matches {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}
.xlt-cons-match {
    flex: 1 1 0;
    min-width: 200px;
    background: #fafaf9;
    border: 1px solid #e7e5e4;
    border-radius: 8px;
    padding: 12px 14px;
}
.xlt-cons-match-best {
    background: #F0FDF4;
    border-color: #bbf7d0;
}
.xlt-cons-match-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #a8a29e;
    font-size: 12px;
    font-style: italic;
}
.xlt-cons-rank {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #a8a29e;
    margin-bottom: 6px;
}
.xlt-cons-rank-best {
    color: #15803d;
}
.xlt-cons-match-number {
    font-size: 14px;
    font-weight: 700;
    color: #1c1917;
}
.xlt-cons-match-dest {
    font-size: 12px;
    color: #78716c;
    margin-bottom: 10px;
}
.xlt-cons-weights {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 10px;
}
.xlt-cons-weight-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #78716c;
    padding: 2px 0;
}
.xlt-cons-weight-divider {
    height: 1px;
    background: #e7e5e4;
    margin: 4px 0;
}
.xlt-cons-weight-combined {
    font-weight: 700;
    color: #15803d;
    font-size: 13px;
}
.xlt-cons-distance {
    display: inline-block;
    background: #f5f5f4;
    color: #57534e;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
    margin-bottom: 8px;
}
.xlt-cons-match-footer {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}

/* ── PRICING (grouped by shipment, top-3 quotes per shipment) ────────────────
   Group wrapper and quote-card wrapper are real st.container(key=...) elements
   (not raw HTML), since each quote card also carries real Select/Lost buttons —
   so they're styled via [class*="st-key-..."] wildcards, matching the technique
   already used for xlt_shp_table/xlt_shp_table_bottom. ─────────────────────── */
[class*="st-key-xlt_price_group_"] {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 14px;
}
.xlt-price-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid #e7e5e4;
    flex-wrap: wrap;
}
.xlt-price-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
.xlt-price-header-number {
    font-size: 15px;
    font-weight: 700;
    color: #1c1917;
}
.xlt-price-header-dest {
    font-size: 13px;
    color: #78716c;
}
.xlt-price-header-count {
    font-size: 11px;
    font-weight: 600;
    color: #a8a29e;
    background: #f5f5f4;
    border-radius: 20px;
    padding: 3px 10px;
    white-space: nowrap;
}
[class*="st-key-xlt_price_card_"] {
    background: #fafaf9;
    border: 1px solid #e7e5e4;
    border-radius: 8px;
    padding: 12px 14px;
}
[class*="st-key-xlt_price_card_"][class*="_best_"] {
    background: #F0FDF4;
    border-color: #bbf7d0;
}
[class*="st-key-xlt_price_card_"][class*="_selected_"] {
    background: #F0FDF4;
    border-color: #bbf7d0;
}
[class*="st-key-xlt_price_card_"][class*="_lost_"] {
    opacity: 0.55;
}
.xlt-price-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 130px;
    color: #a8a29e;
    font-size: 12px;
    font-style: italic;
    background: #fafaf9;
    border: 1px dashed #e7e5e4;
    border-radius: 8px;
    padding: 12px 14px;
}
.xlt-price-best-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .04em;
    color: #15803d;
    background: #DCFCE7;
    border-radius: 20px;
    padding: 3px 9px;
    margin-bottom: 8px;
}
.xlt-price-quote-number {
    font-size: 12px;
    color: #a8a29e;
    margin-bottom: 2px;
}
.xlt-price-carrier {
    font-size: 16px;
    font-weight: 700;
    color: #1c1917;
    margin-bottom: 10px;
}
.xlt-price-financials {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 10px;
}
.xlt-price-fin-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #78716c;
    padding: 2px 0;
}
.xlt-price-fin-divider {
    height: 1px;
    background: #e7e5e4;
    margin: 4px 0;
}
.xlt-price-profit-row {
    display: flex;
    justify-content: space-between;
    font-weight: 700;
    font-size: 14px;
    padding-top: 2px;
}
.xlt-price-profit-green { color: #15803d; }
.xlt-price-profit-amber { color: #b45309; }
.xlt-price-profit-red   { color: #b91c1c; }

[class*="st-key-price_select_btn_"] div[data-testid="stButton"] button {
    background: #16a34a !important;
    color: #ffffff !important;
    border: none !important;
}
[class*="st-key-price_select_btn_"] div[data-testid="stButton"] button:hover {
    background: #15803d !important;
}
[class*="st-key-price_lost_btn_"] div[data-testid="stButton"] button {
    background: #dc2626 !important;
    color: #ffffff !important;
    border: none !important;
}
[class*="st-key-price_lost_btn_"] div[data-testid="stButton"] button:hover {
    background: #b91c1c !important;
}

/* ── PILLS (filter row) ────────────────────────────────────────────────────── */
div[data-testid="stButtonGroup"] button {
    border-radius: 20px !important;
    border: 1px solid #e7e5e4 !important;
    background: #ffffff !important;
    color: #57534e !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 5px 14px !important;
    box-shadow: none !important;
}
div[data-testid="stButtonGroup"] button:hover {
    border-color: #1c1917 !important;
    color: #1c1917 !important;
}
div[data-testid="stButtonGroup"] button[aria-checked="true"] {
    background: #1c1917 !important;
    border-color: #1c1917 !important;
    color: #ffffff !important;
}

/* ── SHIPMENTS TABLE (built from st.columns rows, not a raw <table>, so each
   row can carry a real More/Less button) ─────────────────────────────────── */
[class*="st-key-xlt_shp_table"] {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    overflow: hidden;
}
.st-key-xlt_shp_table div[data-testid="stHorizontalBlock"] {
    padding: 8px 16px;
    border-bottom: 1px solid #e7e5e4;
    align-items: center;
}
.st-key-xlt_shp_table div[data-testid="stHorizontalBlock"]:hover {
    background: #f5f5f4;
}
.st-key-xlt_shp_table div[data-testid="stHorizontalBlock"]:last-child {
    border-bottom: none;
}
.st-key-xlt_shp_table div[data-testid="stButton"] button {
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 600;
    background: #f5f5f4;
    color: #57534e;
    border: 1px solid #e7e5e4;
    box-shadow: none;
}
.st-key-xlt_shp_table div[data-testid="stButton"] button:hover {
    background: #e7e5e4;
    color: #1c1917;
}
.xlt-shp-header {
    display: flex;
    padding: 10px 16px;
    background: #fafaf9;
    border-bottom: 1px solid #e7e5e4;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #a8a29e;
}
.xlt-shp-header > div { flex: 1; }
.xlt-shp-cell {
    font-size: 14px;
    color: #1c1917;
}
.xlt-shp-cell-strong {
    font-weight: 700;
}
.xlt-wh-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.xlt-wh-texas { background: #EFF6FF; color: #1d4ed8; }
.xlt-wh-florida { background: #FFFBEB; color: #b45309; }

/* ── SHIPMENT DETAIL PANEL ─────────────────────────────────────────────────── */
.xlt-detail-row {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    font-size: 13px;
    color: #1c1917;
    padding: 5px 0;
    border-bottom: 1px solid #f5f5f4;
}
.xlt-detail-row span:first-child {
    color: #a8a29e;
}
.xlt-detail-row span:last-child {
    font-weight: 600;
    text-align: right;
}
.xlt-dims-box {
    margin-top: 10px;
    background: #fafaf9;
    border: 1px solid #e7e5e4;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
    color: #1c1917;
}
.xlt-dims-empty {
    color: #a8a29e;
    font-style: italic;
}
.st-key-xlt_shp_detail {
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 10px;
    padding: 20px 22px;
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
            coords = get_shipment_coordinates(shipment)
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

@st.cache_data(ttl=20, show_spinner=False)
def _get_shipments_and_loads():
    """Cached so the 30s autorefresh timer (and every filter/expand button click, which
    each trigger a full script rerun) don't re-hit Airtable every time — get_all_shipments()
    + get_loads() together take 10s+ uncached, which can exceed the autorefresh interval
    and leave a page stuck re-loading before a run ever finishes. Shared by Dashboard and
    Shipments, which both fetch the same two tables with no extra arguments."""
    return get_all_shipments(), get_loads()

@st.cache_data(ttl=20, show_spinner=False)
def _get_pricing_and_shipments():
    """Same rationale as _get_shipments_and_loads, for the Pricing page. Cleared
    explicitly after Select/Lost mutations so the rerun doesn't show a stale status."""
    return get_pricing(), get_all_shipments()

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

    try:
        with st.spinner("Loading data..."):
            shipments, loads = _get_shipments_and_loads()
    except Exception as e:
        st.error(f"⚠️ Failed to load dashboard data from Airtable: {e}")
        st.stop()

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

    try:
        with st.spinner("Loading shipments..."):
            shipments, loads = _get_shipments_and_loads()
    except Exception as e:
        st.error(f"⚠️ Failed to load shipments from Airtable: {e}")
        st.stop()

    def _warehouse_badge(wh):
        if wh == "Texas":
            return '<span class="xlt-wh-badge xlt-wh-texas">Texas</span>'
        if wh == "Florida":
            return '<span class="xlt-wh-badge xlt-wh-florida">Florida</span>'
        return '<span class="xlt-wh-badge">—</span>'

    # ── Filters row ──
    col_status, col_wh, col_extra, col_search = st.columns([2.4, 1.6, 1.6, 1.6])
    with col_status:
        status_filter = st.pills(
            "Status", ["All", "Pending Print", "In Progress", "Ready", "Shipped"],
            default="All", required=True, key="shp_filter_status", label_visibility="collapsed",
        )
    with col_wh:
        wh_filter = st.pills(
            "Warehouse", ["All warehouses", "Texas", "Florida"],
            default="All warehouses", required=True, key="shp_filter_wh", label_visibility="collapsed",
        )
    with col_extra:
        extra_filter = st.pills(
            "Extra", ["Pick Up only", "No load"], selection_mode="multi",
            key="shp_filter_extra", label_visibility="collapsed",
        ) or []
    with col_search:
        search_query = st.text_input(
            "Search", placeholder="Search # or customer...",
            key="shp_filter_search", label_visibility="collapsed",
        )

    # ── Apply filters ──
    filtered = shipments
    if status_filter != "All":
        filtered = [s for s in filtered if s.get("warehouse_status") == status_filter]
    if wh_filter != "All warehouses":
        filtered = [s for s in filtered if s.get("warehouse") == wh_filter]
    if "Pick Up only" in extra_filter:
        filtered = [s for s in filtered if s.get("pick_up") == "Yes"]
    if "No load" in extra_filter:
        filtered = [s for s in filtered if not s.get("load_assigned")]
    if search_query:
        q = search_query.strip().lower()
        filtered = [
            s for s in filtered
            if q in str(s.get("shipment_number", "")).lower() or q in str(s.get("customer", "")).lower()
        ]

    st.markdown(f'<div class="xlt-page-sub">{len(filtered)} shipments</div>', unsafe_allow_html=True)

    # ── Row / detail-panel renderers (used below to interleave the detail panel
    #    immediately after the row that was clicked, instead of after the whole table) ──
    def _render_shipment_row(s):
        cols = st.columns([1.3, 1.6, 1.6, 1.0, 0.9, 1.1, 0.7])
        with cols[0]:
            st.markdown(f'<div class="xlt-shp-cell xlt-shp-cell-strong">{html.escape(str(s.get("shipment_number") or "—"))}</div>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f'<div class="xlt-shp-cell">{html.escape(str(s.get("customer") or "—"))}</div>', unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f'<div class="xlt-shp-cell">{html.escape(str(s.get("city") or ""))}, {html.escape(str(s.get("state") or ""))}</div>', unsafe_allow_html=True)
        with cols[3]:
            st.markdown(_warehouse_badge(s.get("warehouse")), unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f'<div class="xlt-shp-cell">{fmt_weight(s.get("weight",""))}</div>', unsafe_allow_html=True)
        with cols[5]:
            st.markdown(badge_html(s.get("warehouse_status", "")), unsafe_allow_html=True)
        with cols[6]:
            is_expanded = st.session_state.get("expanded_shipment") == s["id"]
            if st.button("Less" if is_expanded else "More", key=f"expand_{s['id']}", use_container_width=True):
                st.session_state["expanded_shipment"] = None if is_expanded else s["id"]
                st.rerun()

    def _render_shipment_detail(s, should_scroll):
        st.markdown('<div id="shp-detail-anchor"></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="xlt-section-title">📋 Details — {html.escape(str(s.get("shipment_number","")))}</div>', unsafe_allow_html=True)

        if should_scroll:
            st.iframe("""
                <script>
                setTimeout(function() {
                    var el = window.parent.document.getElementById('shp-detail-anchor');
                    if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
                }, 100);
                </script>
            """, height=1)

        with st.container(key="xlt_shp_detail"):
                d1, d2, d3, d4 = st.columns(4)

                with d1:
                    st.markdown('<div class="xlt-form-group-label">Product</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="xlt-detail-row"><span>Bundles</span><span>{s.get('bundles') or '—'}</span></div>
                    <div class="xlt-detail-row"><span>Elbows</span><span>{s.get('elbows') or '—'}</span></div>
                    <div class="xlt-detail-row"><span>Weight</span><span>{fmt_weight(s.get('weight',''))} lbs</span></div>
                    <div class="xlt-detail-row"><span>Trailer Type Needed</span><span>{html.escape(str(s.get('trailer_type') or '—'))}</span></div>
                    """, unsafe_allow_html=True)
                    dims = s.get("dimensions")
                    if dims:
                        st.markdown(f'<div class="xlt-dims-box">{html.escape(str(dims))}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="xlt-dims-box xlt-dims-empty">No dimensions recorded yet</div>', unsafe_allow_html=True)

                with d2:
                    st.markdown('<div class="xlt-form-group-label">Destination</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="xlt-detail-row"><span>Address</span><span>{html.escape(str(s.get('address') or '—'))}</span></div>
                    <div class="xlt-detail-row"><span>City, State, ZIP</span><span>{html.escape(str(s.get('city') or ''))}, {html.escape(str(s.get('state') or ''))} {html.escape(str(s.get('zip_code') or ''))}</span></div>
                    <div class="xlt-detail-row"><span>Order Date</span><span>{fmt_date(s.get('order_date',''))}</span></div>
                    <div class="xlt-detail-row"><span>Requested Delivery</span><span>{fmt_date(s.get('delivery_date',''))}</span></div>
                    """, unsafe_allow_html=True)

                with d3:
                    st.markdown('<div class="xlt-form-group-label">Load & Carrier</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="xlt-detail-row"><span>Load #</span><span>{html.escape(str(s.get('load_assigned') or 'Not assigned'))}</span></div>
                    <div class="xlt-detail-row"><span>Carrier</span><span>{html.escape(str(s.get('carrier') or '—'))}</span></div>
                    <div class="xlt-detail-row"><span>Load Status</span><span>{html.escape(str(s.get('load_status') or '—'))}</span></div>
                    <div class="xlt-detail-row"><span>ETA Pickup</span><span>{html.escape(str(s.get('eta_pickup') or '—'))}</span></div>
                    <div class="xlt-detail-row"><span>Pick Up</span><span>{'Yes' if s.get('pick_up') == 'Yes' else 'No'}</span></div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(_warehouse_badge(s.get("warehouse")), unsafe_allow_html=True)

                with d4:
                    st.markdown('<div class="xlt-form-group-label">Actions</div>', unsafe_allow_html=True)

                    # Update warehouse status
                    if st.button("Update Warehouse Status", key="shp_act_status_btn", type="primary", use_container_width=True):
                        st.session_state["shp_action_status"] = not st.session_state.get("shp_action_status", False)
                    if st.session_state.get("shp_action_status"):
                        new_status = st.selectbox("New Status", ["Pending Print", "In Progress", "Ready", "Shipped"], key="shp_new_status_sel")
                        if st.button("Confirm", key="shp_confirm_status", use_container_width=True):
                            r = update_record_api(SHIPMENTS_TABLE, s["id"], {"Warehouse Status": new_status})
                            if r.status_code == 200:
                                st.success(f"✅ Updated to {new_status}")
                                st.session_state["shp_action_status"] = False
                                st.rerun()
                            else:
                                st.error(f"Error {r.status_code}: {r.text}")

                    # Add update log entry
                    if st.button("Add Update Log Entry", key="shp_act_log_btn", use_container_width=True):
                        st.session_state["shp_action_log"] = not st.session_state.get("shp_action_log", False)
                    if st.session_state.get("shp_action_log"):
                        log_type = st.selectbox("Type", UPDATE_TYPES, key="shp_log_type")
                        log_resp = st.selectbox("Responsible", RESPONSIBLE_OPTIONS, key="shp_log_resp")
                        log_desc = st.text_area("Description", key="shp_log_desc", height=70)
                        log_flag = st.checkbox("⚑ Attention Flag", key="shp_log_flag")
                        if st.button("Save Entry", key="shp_confirm_log", use_container_width=True):
                            if not log_desc:
                                st.error("Description is required.")
                            else:
                                fields = {
                                    "Type": log_type, "Description": log_desc,
                                    "Responsible": log_resp, "Attention Flag": log_flag,
                                    "Shipment": [s["id"]],
                                }
                                r = create_record(UPDATES_LOG_TABLE, fields)
                                if r.status_code in (200, 201):
                                    st.success("✅ Entry saved")
                                    st.session_state["shp_action_log"] = False
                                    st.rerun()
                                else:
                                    st.error(f"Error {r.status_code}: {r.text}")

                    # Add quote to Pricing
                    if st.button("Add Quote to Pricing", key="shp_act_quote_btn", use_container_width=True):
                        st.session_state["shp_action_quote"] = not st.session_state.get("shp_action_quote", False)
                    if st.session_state.get("shp_action_quote"):
                        q_carrier = st.selectbox("Carrier", CARRIERS, key="shp_q_carrier")
                        q_status = st.selectbox("Status", ["Pending", "Selected", "Lost"], key="shp_q_status")
                        q_freight = st.number_input("Freight Cost ($)", min_value=0.0, step=50.0, key="shp_q_freight")
                        q_sales = st.number_input("Sales Value ($)", min_value=0.0, step=50.0, key="shp_q_sales")
                        if st.button("Create Quote", key="shp_confirm_quote", use_container_width=True):
                            if q_freight == 0:
                                st.error("Freight Cost is required.")
                            else:
                                fields = {
                                    "Carrier": q_carrier, "Freight Cost": q_freight,
                                    "Sales Value": q_sales, "Status": q_status,
                                    "Shipments": [s["id"]],
                                }
                                r = create_record(PRICING_TABLE, fields)
                                if r.status_code in (200, 201):
                                    st.success("✅ Quote created")
                                    st.session_state["shp_action_quote"] = False
                                    st.rerun()
                                else:
                                    st.error(f"Error {r.status_code}: {r.text}")

                    # Assign to load
                    if st.button("Assign to Load", key="shp_act_load_btn", use_container_width=True):
                        st.session_state["shp_action_load"] = not st.session_state.get("shp_action_load", False)
                    if st.session_state.get("shp_action_load"):
                        open_loads = [l for l in loads if l.get("load_status") != "Shipped"]
                        load_options = [f"{l['load_number']} — {l.get('carrier','')}" for l in open_loads]
                        if load_options:
                            sel_load = st.selectbox("Load", load_options, key="shp_load_sel")
                            if st.button("Confirm Assignment", key="shp_confirm_load", use_container_width=True):
                                load_num = sel_load.split(" — ")[0]
                                load_obj = next((l for l in open_loads if l["load_number"] == load_num), None)
                                if load_obj:
                                    existing_ids = load_obj.get("linked_shipment_ids", [])
                                    new_ids = list(dict.fromkeys(existing_ids + [s["id"]]))
                                    r = update_record_api(LOADS_TABLE, load_obj["id"], {"Linked Shipments": new_ids})
                                    if r.status_code == 200:
                                        st.success(f"✅ Assigned to {load_num}")
                                        st.session_state["shp_action_load"] = False
                                        st.rerun()
                                    else:
                                        st.error(f"Error {r.status_code}: {r.text}")
                        else:
                            st.info("No open loads available.")

    # ── Resolve the expanded shipment once, and whether it just opened/switched
    #    (only then do we auto-scroll — not on every autorefresh/form rerun) ──
    expanded_id = st.session_state.get("expanded_shipment")
    detail_shipment = None
    should_scroll = False
    if expanded_id:
        detail_shipment = next((x for x in shipments if x["id"] == expanded_id), None)
        if detail_shipment is None:
            st.session_state["expanded_shipment"] = None
            expanded_id = None
        elif st.session_state.get("_shp_detail_tracker") != expanded_id:
            for k in ("shp_action_status", "shp_action_log", "shp_action_quote", "shp_action_load"):
                st.session_state[k] = False
            st.session_state["_shp_detail_tracker"] = expanded_id
            should_scroll = True

    expanded_idx = None
    if expanded_id:
        expanded_idx = next((i for i, s in enumerate(filtered) if s["id"] == expanded_id), None)

    # ── Table, split around the expanded row so its detail panel renders
    #    immediately below it instead of after the whole table ──
    if filtered:
        top_slice = filtered if expanded_idx is None else filtered[:expanded_idx + 1]
        with st.container(key="xlt_shp_table"):
            st.markdown("""
            <div class="xlt-shp-header">
                <div style="flex:1.3;">Shipment #</div>
                <div style="flex:1.6;">Customer</div>
                <div style="flex:1.6;">Destination</div>
                <div style="flex:1.0;">Warehouse</div>
                <div style="flex:0.9;">Weight</div>
                <div style="flex:1.1;">Status</div>
                <div style="flex:0.7;"></div>
            </div>
            """, unsafe_allow_html=True)
            for s in top_slice:
                _render_shipment_row(s)

        if expanded_idx is not None:
            _render_shipment_detail(detail_shipment, should_scroll)

            bottom_slice = filtered[expanded_idx + 1:]
            if bottom_slice:
                with st.container(key="xlt_shp_table_bottom"):
                    for s in bottom_slice:
                        _render_shipment_row(s)
    else:
        st.info("No shipments found.")

    # Expanded shipment doesn't match the active filters (e.g. filter changed while its
    # panel was open) — still show it rather than silently collapsing it, just with no
    # row to anchor under.
    if expanded_id and expanded_idx is None and detail_shipment is not None:
        _render_shipment_detail(detail_shipment, should_scroll)

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

    try:
        with st.spinner("Loading..."):
            quotes, shipments = _get_pricing_and_shipments()
    except Exception as e:
        st.error(f"⚠️ Failed to load pricing data from Airtable: {e}")
        st.stop()

    # ── Summary bar (computed from the full, unfiltered quote list) ──
    pending_ct  = sum(1 for q in quotes if q.get("status") == "Pending")
    selected_ct = sum(1 for q in quotes if q.get("status") == "Selected")
    lost_ct     = sum(1 for q in quotes if q.get("status") == "Lost")

    def _is_this_month(q):
        try:
            d = datetime.strptime(q.get("date") or "", "%Y-%m-%d")
            now = datetime.now()
            return d.year == now.year and d.month == now.month
        except ValueError:
            return False

    month_profits = [q.get("profit", 0) or 0 for q in quotes if _is_this_month(q)]
    avg_profit = (sum(month_profits) / len(month_profits)) if month_profits else None
    avg_profit_display = f"${fmt_weight(round(avg_profit))}" if avg_profit is not None else "—"

    c1, c2, c3, c4 = st.columns(4)
    price_metrics = [
        (c1, "#1d4ed8", pending_ct,          "Pending Quotes"),
        (c2, "#15803d", selected_ct,         "Selected"),
        (c3, "#b91c1c", lost_ct,             "Lost"),
        (c4, "#4338ca", avg_profit_display,  "Avg Profit This Month"),
    ]
    for col, color, val, lbl in price_metrics:
        with col:
            st.markdown(f"""
            <div class="xlt-metric">
                <div class="xlt-metric-val">{val}</div>
                <div class="xlt-metric-lbl">{lbl}</div>
                <div class="xlt-metric-bar" style="background:{color};"></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filters row ──
    col_status, col_wh, col_sort, col_search = st.columns([1.8, 1.6, 2.0, 1.6])
    with col_status:
        status_filter = st.pills(
            "Status", ["All", "Pending", "Selected", "Lost"],
            default="All", required=True, key="price_filter_status", label_visibility="collapsed",
        )
    with col_wh:
        wh_filter = st.pills(
            "Warehouse", ["All warehouses", "Texas", "Florida"],
            default="All warehouses", required=True, key="price_filter_wh", label_visibility="collapsed",
        )
    with col_sort:
        sort_filter = st.pills(
            "Sort", ["Best profit first", "Newest first"],
            default="Best profit first", required=True, key="price_filter_sort", label_visibility="collapsed",
        )
    with col_search:
        search_query = st.text_input(
            "Search", placeholder="Search # or customer...",
            key="price_filter_search", label_visibility="collapsed",
        )

    # ── Group quotes (filtered by Status) under their linked shipment ──
    status_filtered = [q for q in quotes if status_filter == "All" or q.get("status") == status_filter]
    shipment_by_number = {s["shipment_number"]: s for s in shipments if s.get("shipment_number")}

    groups = {}
    for q in status_filtered:
        linked = q.get("linked_shipments") or ""
        for num in [x.strip() for x in linked.split(",") if x.strip() and x.strip() != "—"]:
            if num in shipment_by_number:
                groups.setdefault(num, []).append(q)

    search_q = search_query.strip().lower()
    group_entries = []
    for shp_num, qs in groups.items():
        shipment = shipment_by_number[shp_num]
        if wh_filter != "All warehouses" and shipment.get("warehouse") != wh_filter:
            continue
        if search_q:
            haystack = [shp_num, str(shipment.get("customer") or "")] + [str(qq.get("carrier") or "") for qq in qs]
            if not any(search_q in h.lower() for h in haystack):
                continue

        qs_sorted = sorted(qs, key=lambda x: x.get("profit", 0) or 0, reverse=True)
        top3 = qs_sorted[:3]
        group_entries.append({
            "shipment": shipment,
            "quotes": top3,
            "total_count": len(qs),
            "best_id": top3[0]["id"] if top3 else None,
            "max_profit": qs_sorted[0].get("profit", 0) or 0 if qs_sorted else 0,
            "max_date": max((qq.get("date") or "" for qq in qs), default=""),
        })

    if sort_filter == "Best profit first":
        group_entries.sort(key=lambda g: g["max_profit"], reverse=True)
    else:
        group_entries.sort(key=lambda g: g["max_date"], reverse=True)

    total_quotes_shown = sum(g["total_count"] for g in group_entries)
    st.markdown(
        f'<div class="xlt-page-sub">{len(group_entries)} shipment{"s" if len(group_entries) != 1 else ""} '
        f'· {total_quotes_shown} quote{"s" if total_quotes_shown != 1 else ""}</div>',
        unsafe_allow_html=True,
    )

    def _price_wh_badge(wh):
        if wh == "Texas":
            return '<span class="xlt-wh-badge xlt-wh-texas">Texas</span>'
        if wh == "Florida":
            return '<span class="xlt-wh-badge xlt-wh-florida">Florida</span>'
        return '<span class="xlt-wh-badge">—</span>'

    def _price_update_status(q, new_status):
        r = update_record_api(PRICING_TABLE, q["id"], {"Status": new_status})
        if r.status_code == 200:
            _get_pricing_and_shipments.clear()
            st.success(f"✅ Q-{q.get('quote_number','')} → {new_status}")
            st.rerun()
        else:
            st.error(f"Error {r.status_code}: {r.text}")

    def _render_quote_card(q, is_best, shipment_id):
        # A quote can be linked to more than one shipment, so the same quote can be
        # rendered once per shipment group — scope every widget/container key to the
        # (shipment, quote) pair, not just the quote id, or Streamlit raises a
        # duplicate-key error the second time that quote is drawn.
        uid = f"{shipment_id}_{q['id']}"
        status = q.get("status", "Pending")
        state_bits = []
        if is_best:
            state_bits.append("best")
        if status == "Selected":
            state_bits.append("selected")
        elif status == "Lost":
            state_bits.append("lost")
        card_key = f"xlt_price_card_{'_'.join(state_bits) or 'default'}_{uid}"

        profit = q.get("profit", 0) or 0
        if profit > 500:
            profit_class = "xlt-price-profit-green"
        elif profit >= 100:
            profit_class = "xlt-price-profit-amber"
        else:
            profit_class = "xlt-price-profit-red"

        with st.container(key=card_key):
            best_badge = '<div class="xlt-price-best-badge">💰 Best profit</div>' if is_best else ""
            st.markdown(f"""
            {best_badge}
            <div class="xlt-price-quote-number">Q-{html.escape(str(q.get('quote_number') or '—'))} · {fmt_date(q.get('date',''))}</div>
            <div class="xlt-price-carrier">{html.escape(str(q.get('carrier') or '—'))}</div>
            <div class="xlt-price-financials">
                <div class="xlt-price-fin-row"><span>Freight Cost</span><span>${fmt_weight(q.get('freight_cost',''))}</span></div>
                <div class="xlt-price-fin-row"><span>Sales Value</span><span>${fmt_weight(q.get('sales_value',''))}</span></div>
                <div class="xlt-price-fin-row"><span>Freight %</span><span>{q.get('freight_pct','—')}%</span></div>
                <div class="xlt-price-fin-divider"></div>
                <div class="xlt-price-profit-row {profit_class}"><span>Profit</span><span>${fmt_weight(profit)}</span></div>
            </div>
            """, unsafe_allow_html=True)

            if status == "Lost":
                with st.container(key=f"price_select_btn_{uid}"):
                    if st.button("Select", key=f"price_select_{uid}", use_container_width=True):
                        _price_update_status(q, "Selected")
            else:
                b1, b2 = st.columns(2)
                with b1:
                    if status == "Selected":
                        st.button("✓ Selected", key=f"price_selected_disabled_{uid}", use_container_width=True, disabled=True)
                    else:
                        with st.container(key=f"price_select_btn_{uid}"):
                            if st.button("Select", key=f"price_select_{uid}", use_container_width=True):
                                _price_update_status(q, "Selected")
                with b2:
                    lost_label = "Mark Lost" if status == "Selected" else "Lost"
                    with st.container(key=f"price_lost_btn_{uid}"):
                        if st.button(lost_label, key=f"price_lost_{uid}", use_container_width=True):
                            _price_update_status(q, "Lost")

    if not group_entries:
        st.info("No quotes found.")
    else:
        for g in group_entries:
            s = g["shipment"]
            with st.container(key=f"xlt_price_group_{s['id']}"):
                st.markdown(f"""
                <div class="xlt-price-header">
                    <div class="xlt-price-header-left">
                        <span class="xlt-price-header-number">{html.escape(str(s.get('shipment_number') or '—'))}</span>
                        <span class="xlt-price-header-dest">{html.escape(str(s.get('customer') or '—'))} · {html.escape(str(s.get('city') or ''))}, {html.escape(str(s.get('state') or ''))}</span>
                        {_price_wh_badge(s.get('warehouse'))}
                        {badge_html(s.get('warehouse_status',''))}
                    </div>
                    <div class="xlt-price-header-count">{g['total_count']} quote{'s' if g['total_count'] != 1 else ''}</div>
                </div>
                """, unsafe_allow_html=True)

                cols = st.columns(3)
                for i in range(3):
                    with cols[i]:
                        if i < len(g["quotes"]):
                            q = g["quotes"][i]
                            _render_quote_card(q, is_best=(q["id"] == g["best_id"]), shipment_id=s["id"])
                        else:
                            st.markdown('<div class="xlt-price-empty">No other quotes</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="xlt-page-sub">Top 3 closest shipment matches per shipment, grouped by warehouse</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        Analyzes shipments with status <strong>Pending Print</strong>, <strong>In Progress</strong> and <strong>Ready</strong> (excludes Pick Up = Yes).
        Texas and Florida shipments are never compared against each other. For each shipment, the 3 closest other shipments
        in the same warehouse are shown as candidate matches, ordered by distance (shortest first).
    </div>
    """, unsafe_allow_html=True)

    if st.button("Detect Opportunities", type="primary"):
        with st.spinner("Analyzing active shipments by warehouse..."):
            st.session_state["consolidaciones"] = detectar_consolidaciones()

    if "consolidaciones" in st.session_state:
        resultado = st.session_state["consolidaciones"]
        texas_entries = resultado.get("Texas", [])
        florida_entries = resultado.get("Florida", [])
        excluded = resultado.get("excluded", [])
        excluded_pickup = [e for e in excluded if e["reason"] == "Pick Up = Yes"]

        if excluded:
            lines = "\n".join(f"- {e['shipment_number']}: {e['reason']}" for e in excluded)
            st.warning(f"{len(excluded)} shipment(s) skipped from detection:\n{lines}")

        texas_matches = sum(len(e["matches"]) for e in texas_entries)
        florida_matches = sum(len(e["matches"]) for e in florida_entries)
        unique_shipments = len(texas_entries) + len(florida_entries)

        c1, c2, c3, c4 = st.columns(4)
        summary_metrics = [
            (c1, COLOR_TEXAS,   texas_matches,       "Texas Opportunities"),
            (c2, COLOR_FLORIDA, florida_matches,     "Florida Opportunities"),
            (c3, "#4338ca",     unique_shipments,     "Unique Shipments"),
            (c4, "#b45309",     len(excluded_pickup), "Excluded (Pick Up)"),
        ]
        for col, color, val, lbl in summary_metrics:
            with col:
                st.markdown(f"""
                <div class="xlt-metric">
                    <div class="xlt-metric-val">{val}</div>
                    <div class="xlt-metric-lbl">{lbl}</div>
                    <div class="xlt-metric-bar" style="background:{color};"></div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        filtro_cons = st.selectbox(
            "Filter", ["All", "Texas", "Florida", "Ready only", "No load only"],
            label_visibility="collapsed",
        )

        combined = [("Texas", e) for e in texas_entries] + [("Florida", e) for e in florida_entries]
        if filtro_cons == "Texas":
            combined = [(wh, e) for wh, e in combined if wh == "Texas"]
        elif filtro_cons == "Florida":
            combined = [(wh, e) for wh, e in combined if wh == "Florida"]
        elif filtro_cons == "Ready only":
            combined = [(wh, e) for wh, e in combined if e["shipment"]["status"] == "Ready"]
        elif filtro_cons == "No load only":
            combined = [(wh, e) for wh, e in combined if not e["shipment"]["load_assigned"]]

        if not combined:
            st.info("No consolidation opportunities match the current filter.")
        else:
            def _cons_load_badge(load):
                if load:
                    return f'<span class="badge badge-pickup">{html.escape(str(load))}</span>'
                return '<span class="badge badge-pending">No load</span>'

            RANK_LABELS = ["Best match", "2nd option", "3rd option"]

            for warehouse, entrada in combined:
                base = entrada["shipment"]
                matches = entrada["matches"]

                match_cols_html = ""
                for i in range(3):
                    if i < len(matches):
                        m = matches[i]
                        card_class = "xlt-cons-match xlt-cons-match-best" if i == 0 else "xlt-cons-match"
                        rank_class = "xlt-cons-rank xlt-cons-rank-best" if i == 0 else "xlt-cons-rank"
                        match_cols_html += f"""
                        <div class="{card_class}">
                            <div class="{rank_class}">{RANK_LABELS[i]}</div>
                            <div class="xlt-cons-match-number">{html.escape(str(m['shipment_number']))}</div>
                            <div class="xlt-cons-match-dest">{html.escape(str(m['destination']))}</div>
                            <div class="xlt-cons-weights">
                                <div class="xlt-cons-weight-row"><span>Base</span><span>{fmt_weight(base['weight'])} lbs</span></div>
                                <div class="xlt-cons-weight-row"><span>Match</span><span>{fmt_weight(m['weight'])} lbs</span></div>
                                <div class="xlt-cons-weight-divider"></div>
                                <div class="xlt-cons-weight-row xlt-cons-weight-combined"><span>Combined</span><span>{fmt_weight(m['combined_weight'])} lbs</span></div>
                            </div>
                            <div class="xlt-cons-distance">{m['distance_miles']} mi</div>
                            <div class="xlt-cons-match-footer">{badge_html(m['status'])}{_cons_load_badge(m['load_assigned'])}</div>
                        </div>"""
                    else:
                        match_cols_html += '<div class="xlt-cons-match xlt-cons-match-empty">No further match</div>'

                st.markdown(f"""
                <div class="xlt-cons-card">
                    <div class="xlt-cons-header">
                        <div class="xlt-cons-header-left">
                            <span class="xlt-cons-header-number">{html.escape(str(base['shipment_number']))}</span>
                            <span class="xlt-cons-header-dest">{html.escape(str(base['destination']))}</span>
                            <span class="xlt-cons-header-trailer">{html.escape(str(base['trailer_type']) or "—")}</span>
                            {badge_html(base['status'])}
                            {_cons_load_badge(base['load_assigned'])}
                        </div>
                        <div class="xlt-cons-header-weight">{fmt_weight(base['weight'])} lbs</div>
                    </div>
                    <div class="xlt-cons-matches">{match_cols_html}</div>
                </div>
                """, unsafe_allow_html=True)

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

    def _circle_icon(hex_color):
        return folium.DivIcon(
            icon_size=(14, 14), icon_anchor=(7, 7),
            html=f'<div style="width:14px;height:14px;border-radius:50%;background:{hex_color};'
                 f'border:1px solid rgba(0,0,0,0.35);box-shadow:0 0 2px rgba(0,0,0,0.4);"></div>',
        )

    m = folium.Map(location=[31.5, -88.0], zoom_start=6, tiles="cartodbpositron")
    folium.Marker(WAREHOUSE_COORDS["Texas"], tooltip="Texas Warehouse",
                  icon=_star_icon(COLOR_TEXAS)).add_to(m)
    folium.Marker(WAREHOUSE_COORDS["Florida"], tooltip="Florida Warehouse",
                  icon=_star_icon(COLOR_FLORIDA)).add_to(m)

    cluster = MarkerCluster(name="Loads").add_to(m)

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

        folium.Marker(
            location=mk["coords"],
            icon=_circle_icon(mk["color"]),
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(cluster)

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