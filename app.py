# ============================================
# ALVA LOGISTICS TRACKER - Web Interface
# ============================================

import streamlit as st
import json
import pandas as pd
import requests
from datetime import datetime
from config import AIRTABLE_TOKEN, SHIPMENTS_TABLE
from airtable_connection import get_all_shipments, get_loads, get_pricing, get_updates_log, get_bundle_dimensions
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
    "Updates Log",
    "Consolidations",
    "Truck Builder"
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
        html_p = """
        <style>
        .pricing-table { width:100%; border-collapse:collapse; font-size:14px; }
        .pricing-table th { background:#1e3a5f; color:white; padding:8px 10px; font-weight:600; border-bottom:2px solid #ccc; text-align:center; }
        .pricing-table td { padding:7px 10px; border-bottom:1px solid #e0e0e0; text-align:center; }
        .pricing-table tr:hover td { background:#f5f8ff; }
        </style>
        <table class="pricing-table">
        <thead><tr>
            <th>Quote #</th><th>Carrier</th><th>Freight Cost</th><th>Sales Value</th><th>Profit</th><th>Status</th>
        </tr></thead><tbody>"""
        for q in quotes_filtrados:
            try: fc = f"${int(q.get('freight_cost',0)):,}"
            except: fc = q.get('freight_cost','')
            try: sv = f"${int(q.get('sales_value',0)):,}"
            except: sv = q.get('sales_value','')
            try: pr = f"${int(q.get('profit',0)):,}"
            except: pr = q.get('profit','')
            html_p += f"""<tr>
                <td>{q.get('quote_number','')}</td>
                <td>{q.get('carrier','')}</td>
                <td>{fc}</td>
                <td>{sv}</td>
                <td>{pr}</td>
                <td>{q.get('status','')}</td>
            </tr>"""
        html_p += "</tbody></table>"
        st.markdown(html_p, unsafe_allow_html=True)
    else:
        st.info("No quotes found with that filter.")
# ── UPDATES LOG ───────────────────────────
elif pagina == "Updates Log":
    st.title("Updates Log")
    st.markdown("---")

    with st.spinner("Loading updates..."):
        updates = get_updates_log()

    if updates:
        html_u = """
        <style>
        .updates-table { width:100%; border-collapse:collapse; font-size:14px; }
        .updates-table th { background:#1e3a5f; color:white; padding:8px 10px; font-weight:600; border-bottom:2px solid #ccc; text-align:center; }
        .updates-table td { padding:7px 10px; border-bottom:1px solid #e0e0e0; text-align:center; }
        .updates-table tr:hover td { background:#f5f8ff; }
        .flag-yes { background:#fff3cd; color:#856404; padding:2px 8px; border-radius:4px; font-weight:600; }
        .flag-no  { color:#aaa; }
        </style>
        <table class="updates-table">
        <thead><tr>
            <th>Date/Time</th><th>Shipment</th><th>Linked Load</th><th>Type</th><th>Description</th><th>Responsible</th><th>⚠ Flag</th>
        </tr></thead><tbody>"""
        for u in updates:
            flag = u.get('attention_flag', '')
            flag_html = '<span class="flag-yes">⚠ Yes</span>' if flag else '<span class="flag-no">—</span>'
            html_u += f"""<tr>
                <td>{u.get('datetime','')}</td>
                <td>{u.get('shipment','')}</td>
                <td>{u.get('linked_load','')}</td>
                <td>{u.get('type','')}</td>
                <td>{u.get('description','')}</td>
                <td>{u.get('responsible','')}</td>
                <td>{flag_html}</td>
            </tr>"""
        html_u += "</tbody></table>"
        st.markdown(html_u, unsafe_allow_html=True)
        st.caption(f"Total: {len(updates)} updates")
    else:
        st.info("No updates logged yet.")
# ── CONSOLIDATIONS ────────────────────────

# ── CONSOLIDATIONS ────────────────────────
elif pagina == "Consolidations":
    st.title("Consolidation Detector")
    st.markdown("---")
    st.info("The detector analyzes all active shipments and calculates real distances between destinations.")

    if st.button("Detect opportunities"):
        with st.spinner("Analyzing active shipments..."):
            st.session_state["consolidaciones"] = detectar_consolidaciones()

    if "consolidaciones" in st.session_state:
        oportunidades = st.session_state["consolidaciones"]
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
# ── TRUCK BUILDER ─────────────────────────
elif pagina == "Truck Builder":
    st.title("Truck Builder")
    st.markdown("---")

    size_options = ""
    for size in ["1/2","3/4","1","1-1/4","1-1/2","2","2-1/2","3","3-1/2","4","5","6","8"]:
        size_options += f'<option value="{size}">{size}"</option>'

    bundles_js = """const BUNDLES_DB = {
"1/2_10":{size:"1/2",length_ft:10,length_in:127,width_in:30,height_in:16},
"3/4_10":{size:"3/4",length_ft:10,length_in:126,width_in:38,height_in:15},
"1_10":{size:"1",length_ft:10,length_in:127,width_in:36,height_in:19},
"1-1/4_10":{size:"1-1/4",length_ft:10,length_in:134,width_in:42,height_in:24},
"1-1/2_10":{size:"1-1/2",length_ft:10,length_in:131,width_in:43,height_in:22},
"2_10":{size:"2",length_ft:10,length_in:135,width_in:37,height_in:22},
"2-1/2_10":{size:"2-1/2",length_ft:10,length_in:135,width_in:43,height_in:20},
"3_10":{size:"3",length_ft:10,length_in:138,width_in:42,height_in:27},
"3-1/2_10":{size:"3-1/2",length_ft:10,length_in:135,width_in:41,height_in:28},
"4_10":{size:"4",length_ft:10,length_in:138,width_in:45,height_in:28},
"5_10":{size:"5",length_ft:10,length_in:141,width_in:42,height_in:32},
"6_10":{size:"6",length_ft:10,length_in:141,width_in:42,height_in:32},
"8_10":{size:"8",length_ft:10,length_in:135,width_in:40,height_in:31},
"1_20":{size:"1",length_ft:20,length_in:254,width_in:36,height_in:19},
"1-1/4_20":{size:"1-1/4",length_ft:20,length_in:268,width_in:42,height_in:24},
"1-1/2_20":{size:"1-1/2",length_ft:20,length_in:262,width_in:43,height_in:22},
"2_20":{size:"2",length_ft:20,length_in:271,width_in:37,height_in:22},
"2-1/2_20":{size:"2-1/2",length_ft:20,length_in:270,width_in:43,height_in:20},
"3_20":{size:"3",length_ft:20,length_in:276,width_in:42,height_in:27},
"3-1/2_20":{size:"3-1/2",length_ft:20,length_in:270,width_in:41,height_in:28},
"4_20":{size:"4",length_ft:20,length_in:277,width_in:45,height_in:28},
"5_20":{size:"5",length_ft:20,length_in:283,width_in:42,height_in:32},
"6_20":{size:"6",length_ft:20,length_in:282,width_in:42,height_in:32},
"8_20":{size:"8",length_ft:20,length_in:270,width_in:40,height_in:31}
};"""

    html_final = """
    <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    .app{font-family:sans-serif;padding:0.5rem 0;color:#1a1a1a;}
    .top-bar{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;margin-bottom:14px;}
    .field{display:flex;flex-direction:column;gap:3px;}
    .field label{font-size:12px;color:#666;}
    .field select,.field input{height:34px;font-size:13px;padding:0 8px;border:1px solid #ccc;border-radius:6px;background:white;}
    .btn{height:34px;padding:0 14px;font-size:13px;cursor:pointer;border-radius:6px;border:1px solid #ccc;background:white;}
    .btn-primary{background:#1e3a5f;color:white;border-color:#1e3a5f;}
    .btn-danger{border-color:#E24B4A;color:#E24B4A;}
    .metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:14px;}
    .metric{background:#f5f5f5;border-radius:8px;padding:10px;}
    .metric .lbl{font-size:11px;color:#888;}
    .metric .val{font-size:18px;font-weight:500;}
    .ok{color:#1D9E75;}.warn{color:#BA7517;}.err{color:#E24B4A;}
    .main{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;}
    .panel{border:1px solid #e0e0e0;border-radius:8px;background:#fafafa;padding:10px;}
    .panel-title{font-size:12px;font-weight:500;color:#666;margin-bottom:8px;text-align:center;}
    table.loadgrid{border-collapse:collapse;margin:0 auto;}
    table.loadgrid td{width:38px;height:38px;border:1px dashed #ccc;cursor:pointer;text-align:center;font-size:10px;font-weight:500;vertical-align:middle;}
    table.loadgrid td:hover{border-color:#378ADD;}
    table.loadgrid td.filled{border-style:solid;}
    table.loadgrid td.center-line{border-right:2px solid #333;}
    canvas{width:100%;display:block;border-radius:4px;}
    .views3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px;}
    .view3-box{border:1px solid #e0e0e0;border-radius:8px;background:#fafafa;padding:8px;}
    .alert{padding:8px 12px;border-radius:6px;font-size:13px;margin-bottom:10px;}
    .alert-ok{background:#E1F5EE;color:#0F6E56;}
    .alert-warn{background:#FAEEDA;color:#854F0B;}
    .alert-err{background:#FCEBEB;color:#A32D2D;}
    </style>
    <div class="app">
    <div class="top-bar">
      <div class="field"><label>Pipe size</label><select id="sel-size">SIZE_OPTIONS_HERE</select></div>
      <div class="field"><label>Length</label><select id="sel-len"><option value="10">10 ft</option><option value="20">20 ft</option></select></div>
      <div class="field"><label>Qty</label><input type="number" id="sel-qty" value="1" min="1" max="24" style="width:60px;"></div>
      <button class="btn btn-primary" onclick="addBundles()">+ Add</button>
      <button class="btn btn-danger" onclick="clearAll()">Clear</button>
    </div>
    <div id="alerts"></div>
    <div class="metrics">
      <div class="metric"><div class="lbl">Total bundles</div><div class="val" id="m-total">0</div></div>
      <div class="metric"><div class="lbl">Slots used</div><div class="val" id="m-slots">0 / 24</div></div>
      <div class="metric"><div class="lbl">Max height</div><div class="val" id="m-height">—</div></div>
      <div class="metric"><div class="lbl">Left weight</div><div class="val" id="m-left">0 lbs</div></div>
      <div class="metric"><div class="lbl">Right weight</div><div class="val" id="m-right">0 lbs</div></div>
    </div>
    <div class="main">
      <div class="panel">
        <div class="panel-title">Loading diagram — top view (click to remove)</div>
        <div style="font-size:11px;color:#999;text-align:center;margin-bottom:4px;">FRONT → &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; BACK</div>
        <table class="loadgrid" id="loadgrid"></table>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:#999;margin-top:4px;">
          <span>LEFT SIDE</span><span>RIGHT SIDE</span></div>
      </div>
      <div class="panel">
        <div class="panel-title">Vista 360° — arrastra para rotar</div>
        <canvas id="cv-360" height="200"></canvas>
      </div>
    </div>
    <div class="views3">
      <div class="view3-box"><div class="panel-title">Vista frontal</div><canvas id="cv-front" height="140"></canvas></div>
      <div class="view3-box"><div class="panel-title">Vista lateral</div><canvas id="cv-side" height="140"></canvas></div>
      <div class="view3-box"><div class="panel-title">Vista aerea</div><canvas id="cv-top" height="140"></canvas></div>
    </div>
    </div>
    <script>
    BUNDLES_JS_HERE
    const COLORS={"1/2":"#7F77DD","3/4":"#534AB7","1":"#1D9E75","1-1/4":"#0F6E56","1-1/2":"#D85A30","2":"#993C1D","2-1/2":"#D4537E","3":"#993556","3-1/2":"#378ADD","4":"#185FA5","5":"#BA7517","6":"#854F0B","8":"#639922"};
    const ROWS=4,COLS=6,TRAILER_W=102,LEGAL_H=162,DECK_H=60,TRAILER_L=576;
    let slots=Array(ROWS*COLS).fill(null);
    function getBundleData(size,len){return BUNDLES_DB[size+"_"+parseInt(len)]||null;}
    function slotIndex(r,c){return r*COLS+c;}
    function buildGrid(){
      const tbl=document.getElementById('loadgrid');tbl.innerHTML='';
      for(let r=0;r<ROWS;r++){
        const tr=document.createElement('tr');
        for(let c=0;c<COLS;c++){
          const td=document.createElement('td');const idx=slotIndex(r,c);const s=slots[idx];
          if(c===2)td.classList.add('center-line');
          if(s){td.classList.add('filled');td.style.background=COLORS[s.size]+'33';td.style.borderColor=COLORS[s.size];td.style.color=COLORS[s.size];td.textContent=s.size;}
          td.onclick=()=>{if(slots[idx]){slots[idx]=null;update();}};
          tr.appendChild(td);
        }
        tbl.appendChild(tr);
      }
    }
    function addBundles(){
      const size=document.getElementById('sel-size').value;
      const len=parseInt(document.getElementById('sel-len').value);
      const qty=parseInt(document.getElementById('sel-qty').value)||1;
      const b=getBundleData(size,len);
     if(!b){console.log('Not found:',size+'_'+len,'Keys:',Object.keys(BUNDLES_DB));return;}
      let added=0;
      for(let i=0;i<ROWS*COLS&&added<qty;i++){
        if(!slots[i]){slots[i]={size,len,w:b.width_in,h:b.height_in,l:b.length_in};added++;}
      }
      update();
    }
    function clearAll(){slots=Array(ROWS*COLS).fill(null);update();}
    function getStats(){
      let total=0,leftW=0,rightW=0;
      const colH=Array(COLS).fill(DECK_H);
      for(let r=0;r<ROWS;r++){for(let c=0;c<COLS;c++){const s=slots[slotIndex(r,c)];if(s){total++;if(c<3)leftW+=s.w*s.h*0.000284;else rightW+=s.w*s.h*0.000284;colH[c]+=s.h;}}}
      return{total,leftW:Math.round(leftW),rightW:Math.round(rightW),maxH:Math.max(...colH)};
    }
    function update(){
      buildGrid();const st=getStats();const filled=slots.filter(Boolean).length;
      document.getElementById('m-total').textContent=st.total;
      document.getElementById('m-slots').textContent=filled+' / '+(ROWS*COLS);
      const ft=Math.floor(st.maxH/12),inch=Math.round(st.maxH%12);
      const hEl=document.getElementById('m-height');
      hEl.textContent=ft+"'"+inch+'"';
      hEl.className='val '+(st.maxH>LEGAL_H+DECK_H?'err':st.maxH>LEGAL_H+DECK_H-10?'warn':'ok');
      document.getElementById('m-left').textContent=st.leftW+' lbs';
      document.getElementById('m-right').textContent=st.rightW+' lbs';
      const al=document.getElementById('alerts');al.innerHTML='';
      if(st.maxH>LEGAL_H+DECK_H)al.innerHTML='<div class="alert alert-err">Height exceeded</div>';
      else if(filled>0)al.innerHTML='<div class="alert alert-ok">Load OK — '+ft+"'"+inch+'"</div>';
      drawFront();drawSide();drawTop();draw360();
    }
    function drawFront(){
      const cv=document.getElementById('cv-front');const ctx=cv.getContext('2d');
      const W=cv.offsetWidth||200;cv.width=W;cv.height=140;ctx.clearRect(0,0,W,140);
      const PAD=24,baseY=128,drawH=100,drawW=W-PAD*2;
      const sH=drawH/(LEGAL_H+DECK_H),sW=drawW/(TRAILER_W+20);
      const deckPx=DECK_H*sH,trailerWpx=TRAILER_W*sW,offsetX=PAD+10;
      ctx.fillStyle='#888780';ctx.fillRect(offsetX,baseY-deckPx,trailerWpx,deckPx);
      ctx.strokeStyle='#E24B4A';ctx.lineWidth=1;ctx.setLineDash([4,3]);
      const limY=baseY-deckPx-LEGAL_H*sH;
      ctx.beginPath();ctx.moveTo(offsetX-4,limY);ctx.lineTo(offsetX+trailerWpx+4,limY);ctx.stroke();ctx.setLineDash([]);
      ctx.fillStyle='#E24B4A';ctx.font='9px sans-serif';ctx.fillText("13'6\"",offsetX+trailerWpx+4,limY+4);
      const colW=TRAILER_W/COLS*sW;
      const colHeights=Array(COLS).fill(0);
      for(let r=0;r<ROWS;r++){for(let c=0;c<COLS;c++){if(slots[slotIndex(r,c)])colHeights[c]++;}}
      for(let c=0;c<COLS;c++){
        const s=slots.find((sl,i)=>sl&&i%COLS===c);if(!s)continue;
        for(let row=0;row<colHeights[c];row++){
          const bX=offsetX+c*colW,bY=baseY-deckPx-(row+1)*s.h*sH;
          ctx.fillStyle=COLORS[s.size]+'cc';ctx.fillRect(bX+1,bY+1,colW-2,s.h*sH-1);
          ctx.strokeStyle=COLORS[s.size];ctx.lineWidth=0.5;ctx.strokeRect(bX+1,bY+1,colW-2,s.h*sH-1);
        }
      }
    }
    function drawSide(){
      const cv=document.getElementById('cv-side');const ctx=cv.getContext('2d');
      const W=cv.offsetWidth||200;cv.width=W;cv.height=140;ctx.clearRect(0,0,W,140);
      const PAD=8,baseY=128,drawH=100,drawW=W-PAD*2;
      const sH=drawH/(LEGAL_H+DECK_H),sL=drawW/(TRAILER_L+20);
      const deckPx=DECK_H*sH,trailerLpx=TRAILER_L*sL;
      ctx.fillStyle='#888780';ctx.fillRect(PAD,baseY-deckPx,trailerLpx,deckPx);
      ctx.strokeStyle='#E24B4A';ctx.lineWidth=1;ctx.setLineDash([4,3]);
      const limY=baseY-deckPx-LEGAL_H*sH;
      ctx.beginPath();ctx.moveTo(PAD-4,limY);ctx.lineTo(PAD+trailerLpx+4,limY);ctx.stroke();ctx.setLineDash([]);
      ctx.fillStyle='#E24B4A';ctx.font='9px sans-serif';ctx.fillText("13'6\"",PAD+trailerLpx+4,limY+4);
      const rowL=TRAILER_L/ROWS;
      for(let r=0;r<ROWS;r++){
        const colH=Array(COLS).fill(0);
        for(let c=0;c<COLS;c++){if(slots[slotIndex(r,c)])colH[c]++;}
        const maxStack=Math.max(...colH);
        const s=slots.find((sl,i)=>sl&&Math.floor(i/COLS)===r);if(!s)continue;
        const gX=PAD+r*rowL*sL,gW=rowL*sL-2;
        for(let row=0;row<maxStack;row++){
          const bY=baseY-deckPx-(row+1)*s.h*sH;
          ctx.fillStyle=COLORS[s.size]+'cc';ctx.fillRect(gX+1,bY+1,gW,s.h*sH-1);
          ctx.strokeStyle=COLORS[s.size];ctx.lineWidth=0.5;ctx.strokeRect(gX+1,bY+1,gW,s.h*sH-1);
        }
      }
      ctx.fillStyle='#666';ctx.font='9px sans-serif';ctx.textAlign='center';
      ctx.fillText('48ft',PAD+trailerLpx/2,baseY+12);ctx.textAlign='left';
    }
    function drawTop(){
      const cv=document.getElementById('cv-top');const ctx=cv.getContext('2d');
      const W=cv.offsetWidth||200;cv.width=W;cv.height=140;ctx.clearRect(0,0,W,140);
      const PAD_X=8,PAD_Y=15,drawW=W-PAD_X*2,drawH=115;
      const sL=drawW/TRAILER_L,sW=drawH/TRAILER_W;
      const trailerLpx=TRAILER_L*sL,trailerWpx=TRAILER_W*sW;
      ctx.fillStyle='#e8e8e5';ctx.fillRect(PAD_X,PAD_Y,trailerLpx,trailerWpx);
      ctx.strokeStyle='#999';ctx.lineWidth=1;ctx.strokeRect(PAD_X,PAD_Y,trailerLpx,trailerWpx);
      ctx.strokeStyle='#333';ctx.lineWidth=1;ctx.setLineDash([4,3]);
      ctx.beginPath();ctx.moveTo(PAD_X+trailerLpx/2,PAD_Y);ctx.lineTo(PAD_X+trailerLpx/2,PAD_Y+trailerWpx);ctx.stroke();ctx.setLineDash([]);
      const rowL=TRAILER_L/ROWS,colH=TRAILER_W/COLS;
      for(let r=0;r<ROWS;r++){for(let c=0;c<COLS;c++){
        const s=slots[slotIndex(r,c)];if(!s)continue;
        const bX=PAD_X+r*rowL*sL,bY=PAD_Y+c*colH*sW;
        ctx.fillStyle=COLORS[s.size]+'cc';ctx.fillRect(bX+1,bY+1,rowL*sL-2,colH*sW-2);
        ctx.strokeStyle=COLORS[s.size];ctx.lineWidth=0.5;ctx.strokeRect(bX+1,bY+1,rowL*sL-2,colH*sW-2);
        ctx.fillStyle=COLORS[s.size];ctx.font='8px sans-serif';ctx.textAlign='center';
        ctx.fillText(s.size,bX+rowL*sL/2,bY+colH*sW/2+3);ctx.textAlign='left';
      }}
      ctx.fillStyle='#666';ctx.font='9px sans-serif';ctx.textAlign='center';
      ctx.fillText('FRONT',PAD_X+rowL*sL/2,PAD_Y-3);ctx.fillText('BACK',PAD_X+trailerLpx-rowL*sL/2,PAD_Y-3);ctx.textAlign='left';
    }
    let rotX=0.4,rotY=-0.5,dragging=false,lastX=0,lastY=0;
    document.getElementById('cv-360').addEventListener('mousedown',e=>{dragging=true;lastX=e.clientX;lastY=e.clientY;});
    window.addEventListener('mouseup',()=>dragging=false);
    window.addEventListener('mousemove',e=>{if(!dragging)return;rotY+=(e.clientX-lastX)*0.01;rotX+=(e.clientY-lastY)*0.01;lastX=e.clientX;lastY=e.clientY;draw360();});
    function project(x,y,z,cx,cy,scale){
      const cosY=Math.cos(rotY),sinY=Math.sin(rotY),cosX=Math.cos(rotX),sinX=Math.sin(rotX);
      const x2=x*cosY-z*sinY,z2=x*sinY+z*cosY,y2=y*cosX-z2*sinX,z3=y*sinX+z2*cosX;
      const d=400/(400+z3+200);return{px:cx+x2*d*scale,py:cy+y2*d*scale,d:z3};
    }
    function draw360(){
      const cv=document.getElementById('cv-360');const ctx=cv.getContext('2d');
      const W=cv.offsetWidth||300;cv.width=W;cv.height=200;ctx.clearRect(0,0,W,200);
      const cx=W/2,cy=110,scale=0.28,TL=TRAILER_L/2,TW=TRAILER_W/2;
      function box(x1,y1,z1,x2,y2,z2,col){
        const corners=[[x1,y1,z1],[x2,y1,z1],[x2,y2,z1],[x1,y2,z1],[x1,y1,z2],[x2,y1,z2],[x2,y2,z2],[x1,y2,z2]].map(([x,y,z])=>project(x,y,z,cx,cy,scale));
        [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[0,3,7,4],[1,2,6,5]].map(f=>({f,d:f.reduce((s,i)=>s+corners[i].d,0)/4})).sort((a,b)=>b.d-a.d).forEach(({f})=>{
          ctx.beginPath();f.forEach((i,j)=>{const p=corners[i];j?ctx.lineTo(p.px,p.py):ctx.moveTo(p.px,p.py);});
          ctx.closePath();ctx.fillStyle=col+'bb';ctx.fill();ctx.strokeStyle=col;ctx.lineWidth=0.5;ctx.stroke();
        });
      }
      box(-TL,-DECK_H-2,-TW,TL,-DECK_H,TW,'#888780');
      const rowL=TRAILER_L/ROWS,colW=TRAILER_W/COLS,faces=[];
      for(let r=0;r<ROWS;r++){for(let c=0;c<COLS;c++){
        const s=slots[slotIndex(r,c)];if(!s)continue;
        const x1=-TL+r*rowL,x2=x1+rowL-2,z1=-TW+c*colW,z2=z1+colW-2,y1=-DECK_H-s.h,y2=-DECK_H;
        const avg=project((x1+x2)/2,(y1+y2)/2,(z1+z2)/2,cx,cy,scale);
        faces.push({x1,y1,z1,x2,y2,z2,col:COLORS[s.size],d:avg.d});
      }}
      faces.sort((a,b)=>b.d-a.d).forEach(f=>box(f.x1,f.y1,f.z1,f.x2,f.y2,f.z2,f.col));
    }
    update();
    </script>
    """.replace("SIZE_OPTIONS_HERE", size_options).replace("BUNDLES_JS_HERE", bundles_js)

    st.components.v1.html(html_final, height=900, scrolling=True)