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
            <th>Date/Time</th><th>Shipment</th><th>Linked Load</th><th>Type</th><th>Description</th><th>Responsible</th><th>Flag</th>
        </tr></thead><tbody>"""
        for u in updates:
            flag = u.get('attention_flag', '')
            flag_html = '<span class="flag-yes">Yes</span>' if flag else '<span class="flag-no">-</span>'
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
                    st.markdown(f"**Shipment 1:** {op['shipment_1']} -> {op['destino_1']} ({op['peso_1']:,} lbs)")
                    st.markdown(f"**Shipment 2:** {op['shipment_2']} -> {op['destino_2']} ({op['peso_2']:,} lbs)")
                    st.markdown(f"**Suggested trailer:** {op['trailer_sugerido']}")
        else:
            st.warning("No consolidation opportunities detected with current active shipments.")

# ── TRUCK BUILDER ─────────────────────────
elif pagina == "Truck Builder":
    st.title("Truck Builder")
    st.markdown("---")

    BUNDLES = {
        "1/2": {"10": {"w":30,"h":16,"l":127}, "20": None},
        "3/4": {"10": {"w":38,"h":15,"l":126}, "20": None},
        "1":   {"10": {"w":36,"h":19,"l":127}, "20": {"w":36,"h":19,"l":254}},
        "1-1/4": {"10": {"w":42,"h":24,"l":134}, "20": {"w":42,"h":24,"l":268}},
        "1-1/2": {"10": {"w":43,"h":22,"l":131}, "20": {"w":43,"h":22,"l":262}},
        "2":   {"10": {"w":37,"h":22,"l":135}, "20": {"w":37,"h":22,"l":271}},
        "2-1/2": {"10": {"w":43,"h":20,"l":135}, "20": {"w":43,"h":20,"l":270}},
        "3":   {"10": {"w":42,"h":27,"l":138}, "20": {"w":42,"h":27,"l":276}},
        "3-1/2": {"10": {"w":41,"h":28,"l":135}, "20": {"w":41,"h":28,"l":270}},
        "4":   {"10": {"w":45,"h":28,"l":138}, "20": {"w":45,"h":28,"l":277}},
        "5":   {"10": {"w":42,"h":32,"l":141}, "20": {"w":42,"h":32,"l":283}},
        "6":   {"10": {"w":42,"h":32,"l":141}, "20": {"w":42,"h":32,"l":282}},
        "8":   {"10": {"w":40,"h":31,"l":135}, "20": {"w":40,"h":31,"l":270}},
    }

    COLORS = {
        "1/2":"#7F77DD","3/4":"#534AB7","1":"#1D9E75","1-1/4":"#0F6E56",
        "1-1/2":"#D85A30","2":"#993C1D","2-1/2":"#D4537E","3":"#993556",
        "3-1/2":"#378ADD","4":"#185FA5","5":"#BA7517","6":"#854F0B","8":"#639922"
    }

    ROWS, COLS = 4, 6
    TRAILER_W, TRAILER_L, DECK_H, LEGAL_H = 102, 576, 60, 162

    if "tb_grid" not in st.session_state:
        st.session_state.tb_grid = [[None]*COLS for _ in range(ROWS)]
    if "tb_sel" not in st.session_state:
        st.session_state.tb_sel = None

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        size_sel = st.selectbox("Pipe size", [s + '"' for s in BUNDLES.keys()])
        size_key = size_sel.replace('"', '')
    with col2:
        available = [k for k, v in BUNDLES[size_key].items() if v is not None]
        len_sel = st.selectbox("Length", available, format_func=lambda x: x + " ft")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear all"):
            st.session_state.tb_grid = [[None]*COLS for _ in range(ROWS)]
            st.session_state.tb_sel = None
            st.rerun()

    b_data = BUNDLES[size_key][len_sel]
    grid = st.session_state.tb_grid
    sel = st.session_state.tb_sel

    if sel:
        st.info(f"Bundle selected: {grid[sel[0]][sel[1]]['size']}\" {grid[sel[0]][sel[1]]['len']}ft — click another cell to move it")
    else:
        st.caption("Click empty cell to place bundle. Click filled cell to select it, then click another cell to move it.")

    st.markdown("---")

    # FRONT labels
    hcols = st.columns([0.4] + [1]*6 + [0.4])
    hcols[1].markdown("<center><b style='font-size:12px;color:#666'>FRONT</b></center>", unsafe_allow_html=True)
    hcols[4].markdown("<center><b style='font-size:12px;color:#666'>FRONT</b></center>", unsafe_allow_html=True)

    changed = False
    for r in range(ROWS):
        rcols = st.columns([0.4] + [1]*6 + [0.4])
        if r == 1:
            rcols[0].markdown("<div style='font-size:11px;color:#666;font-weight:600;text-align:center;padding-top:20px'>LEFT<br>SIDE</div>", unsafe_allow_html=True)
            rcols[7].markdown("<div style='font-size:11px;color:#666;font-weight:600;text-align:center;padding-top:20px'>RIGHT<br>SIDE</div>", unsafe_allow_html=True)

        for c in range(COLS):
            cell = grid[r][c]
            is_sel = sel == (r, c)
            col = rcols[c + 1]

            if cell:
                clr = COLORS.get(cell['size'], '#378ADD')
                if is_sel:
                    style = "background-color:" + clr + ";color:white;border:3px solid gold;border-radius:8px;padding:8px;text-align:center;font-weight:700;font-size:15px;margin:2px;cursor:pointer"
                else:
                    style = "background-color:" + clr + "22;color:" + clr + ";border:2px solid " + clr + ";border-radius:8px;padding:8px;text-align:center;font-weight:700;font-size:15px;margin:2px;cursor:pointer"
                if c == 2:
                    style += ";border-right:4px solid #222"
                col.markdown("<div style='" + style + "'>" + cell['size'] + '"<br><span style=font-size:11px>' + str(cell['len']) + "ft</span></div>", unsafe_allow_html=True)
            else:
                if is_sel:
                    style = "background-color:#E1F5EE;border:2px dashed #1D9E75;border-radius:8px;padding:8px;text-align:center;color:#1D9E75;font-size:20px;margin:2px;cursor:pointer"
                else:
                    style = "background-color:#fafafa;border:2px dashed #ddd;border-radius:8px;padding:8px;text-align:center;color:#ddd;font-size:20px;margin:2px;cursor:pointer"
                if c == 2:
                    style += ";border-right:4px solid #222"
                col.markdown("<div style='" + style + "'>·</div>", unsafe_allow_html=True)

            if col.button(".", key="g_" + str(r) + "_" + str(c)):
                if sel is None:
                    if cell:
                        st.session_state.tb_sel = (r, c)
                    else:
                        grid[r][c] = {"size": size_key, "len": int(len_sel), "w": b_data["w"], "h": b_data["h"], "l": b_data["l"]}
                        st.session_state.tb_sel = None
                else:
                    sr, sc = sel
                    if (r, c) == sel:
                        st.session_state.tb_sel = None
                    elif cell is None:
                        grid[r][c] = grid[sr][sc]
                        grid[sr][sc] = None
                        st.session_state.tb_sel = None
                    else:
                        grid[r][c], grid[sr][sc] = grid[sr][sc], grid[r][c]
                        st.session_state.tb_sel = None
                changed = True

    if changed:
        st.rerun()

    st.markdown("---")

    total = sum(1 for r in range(ROWS) for c in range(COLS) if grid[r][c])
    col_heights = []
    for c in range(COLS):
        h = DECK_H
        for r in range(ROWS):
            if grid[r][c]:
                h += grid[r][c]["h"]
        col_heights.append(h)
    max_h = max(col_heights)
    ft = int(max_h // 12)
    inch = round(max_h % 12)
    left_w = sum(grid[r][c]["w"]*grid[r][c]["h"]*0.000284 for r in range(ROWS) for c in range(3) if grid[r][c])
    right_w = sum(grid[r][c]["w"]*grid[r][c]["h"]*0.000284 for r in range(ROWS) for c in range(3,6) if grid[r][c])

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total bundles", total)
    m2.metric("Slots used", str(total) + " / " + str(ROWS*COLS))
    m3.metric("Max height", str(ft) + "'" + str(inch) + '"')
    m4.metric("Left weight", str(int(left_w)) + " lbs")
    m5.metric("Right weight", str(int(right_w)) + " lbs")

    if max_h > LEGAL_H + DECK_H:
        st.error("Height exceeded — " + str(ft) + "'" + str(inch) + '" supera 13\'6"')
    elif total > 0:
        st.success("Load OK — " + str(ft) + "'" + str(inch) + '" altura, ' + str(ROWS*COLS - total) + " slots disponibles")

    st.markdown("---")
    import plotly.graph_objects as go

    def make_box(x0, x1, y0, y1, z0, z1, color):
        vx = [x0,x1,x1,x0,x0,x1,x1,x0]
        vy = [y0,y0,y1,y1,y0,y0,y1,y1]
        vz = [z0,z0,z0,z0,z1,z1,z1,z1]
        i = [0,0,0,1,1,2,4,4,4,5,5,6]
        j = [1,2,4,2,5,3,5,6,0,6,1,7]
        k = [2,3,5,5,6,7,6,7,7,7,2,3]
        return go.Mesh3d(x=vx, y=vy, z=vz, i=i, j=j, k=k, color=color, opacity=0.85, flatshading=True)

    fig = go.Figure()
    fig.add_trace(make_box(0, TRAILER_L, -TRAILER_W/2, TRAILER_W/2, 0, DECK_H, "#aaaaaa"))

    row_l = TRAILER_L / ROWS
    col_w = TRAILER_W / COLS

    for r in range(ROWS):
        for c in range(COLS):
            s = grid[r][c]
            if not s:
                continue
            x0 = r * row_l
            x1 = x0 + row_l - 2
            y0 = -TRAILER_W/2 + c * col_w
            y1 = y0 + col_w - 2
            clr = COLORS.get(s["size"], "#378ADD")
            fig.add_trace(make_box(x0, x1, y0, y1, DECK_H, DECK_H + s["h"], clr))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="Length", range=[0, TRAILER_L]),
            yaxis=dict(title="Width", range=[-TRAILER_W/2, TRAILER_W/2]),
            zaxis=dict(title="Height", range=[0, LEGAL_H+DECK_H]),
            aspectmode="data",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1))
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)