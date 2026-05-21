# ============================================
# ALVA LOGISTICS TRACKER - Interfaz Web
# ============================================

import streamlit as st
import pandas as pd
from datetime import datetime
from airtable_connection import (
    get_all_shipments, get_loads, get_pricing
)
from consolidation_detector import detectar_consolidaciones

# Configuracion de la pagina
st.set_page_config(
    page_title="Alva Logistics Tracker",
    page_icon="🚛",
    layout="wide"
)

# Auto-refresh cada 30 segundos
st.markdown("""<meta http-equiv="refresh" content="30">""", unsafe_allow_html=True)

# Sidebar navegacion
st.sidebar.title("🚛 Alva Logistics")
st.sidebar.markdown("**Sistema de Transporte**")
st.sidebar.markdown("---")

pagina = st.sidebar.radio("Navegacion", [
    "Dashboard",
    "Shipments",
    "Loads",
    "Pricing",
    "Consolidaciones"
])

st.sidebar.markdown("---")
st.sidebar.markdown(f"*Texas — {datetime.now().strftime('%m/%d/%Y')}*")

# ── DASHBOARD ──────────────────────────────
if pagina == "Dashboard":
    st.title("Dashboard Operativo")
    st.markdown(f"**Texas** — {datetime.now().strftime('%A, %B %d %Y')}")
    st.markdown("---")

    with st.spinner("Cargando datos..."):
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
    col5.metric("Loads Activos", len(active_loads))

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Shipments Activos")
        activos = pending + in_progress + ready
        if activos:
            df = pd.DataFrame(activos)[["shipment_number", "city", "state", "weight", "warehouse_status"]]
            df.columns = ["Shipment", "Ciudad", "Estado", "Peso (lbs)", "Status"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay shipments activos.")

    with col_right:
        st.subheader("Loads Activos")
        if active_loads:
            df_loads = pd.DataFrame(active_loads)[["load_number", "carrier", "total_weight", "load_status", "eta_pickup"]]
            df_loads.columns = ["Load", "Carrier", "Peso Total", "Status", "ETA Pickup"]
            st.dataframe(df_loads, use_container_width=True, hide_index=True)
        else:
            st.info("No hay loads activos.")

# ── SHIPMENTS ──────────────────────────────
elif pagina == "Shipments":
    st.title("Shipments")
    st.markdown("---")

    with st.spinner("Cargando shipments..."):
        shipments = get_all_shipments()

    col_filter, col_count = st.columns([3, 1])
    with col_filter:
        filtro = st.selectbox("Filtrar por status", [
            "Todos", "Pending Print", "In Progress", "Ready", "Shipped"
        ])

    if filtro != "Todos":
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
        df.columns = ["Shipment", "Cliente", "Ciudad", "Estado", "Peso", "Bultos", "Trailer", "Status", "Fecha Entrega"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay shipments con ese filtro.")

    st.markdown("---")
    st.subheader("Actualizar Warehouse Status")
    st.caption("Selecciona un shipment y cambia su status directamente desde aqui.")

    col1, col2, col3 = st.columns(3)
    with col1:
        numeros = [s["shipment_number"] for s in shipments]
        shipment_sel = st.selectbox("Shipment", numeros)
    with col2:
        nuevo_status = st.selectbox("Nuevo Status", [
            "Pending Print", "In Progress", "Ready", "Shipped"
        ])
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Actualizar Status"):
            from airtable_connection import update_record
            from config import SHIPMENTS_TABLE
            shipment_obj = next((s for s in shipments if s["shipment_number"] == shipment_sel), None)
            if shipment_obj:
                result = update_record(SHIPMENTS_TABLE, shipment_obj["id"], {"Warehouse Status": nuevo_status})
                st.success(f"Status de {shipment_sel} actualizado a {nuevo_status}")
                st.rerun()

# ── LOADS ──────────────────────────────────
elif pagina == "Loads":
    st.title("Loads")
    st.markdown("---")

    with st.spinner("Cargando loads..."):
        loads = get_loads()

    if loads:
        df = pd.DataFrame(loads)[[
            "load_number", "carrier", "total_weight",
            "total_bundles", "load_status", "eta_pickup",
            "freight_cost", "sales_value"
        ]]
        df.columns = ["Load", "Carrier", "Peso Total", "Bultos", "Status", "ETA Pickup", "Flete", "Sales Value"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Total: {len(loads)} loads")
    else:
        st.info("No hay loads registrados.")

# ── PRICING ────────────────────────────────
elif pagina == "Pricing":
    st.title("Pricing")
    st.markdown("---")

    with st.spinner("Cargando cotizaciones..."):
        quotes = get_pricing()

    col_filter, col_count = st.columns([3, 1])
    with col_filter:
        filtro_status = st.selectbox("Filtrar por status", [
            "Todos", "Pending", "Selected", "Lost"
        ])

    if filtro_status != "Todos":
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
        df.columns = ["Quote #", "Carrier", "Flete", "Sales Value", "Profit", "Status"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay cotizaciones con ese filtro.")

# ── CONSOLIDACIONES ────────────────────────
elif pagina == "Consolidaciones":
    st.title("Detector de Consolidaciones")
    st.markdown("---")
    st.info("El detector analiza todos los shipments activos y calcula distancias reales entre destinos.")

    if st.button("Detectar oportunidades"):
        with st.spinner("Analizando shipments activos..."):
            oportunidades = detectar_consolidaciones()

        if oportunidades:
            st.success(f"{len(oportunidades)} oportunidad(es) detectada(s)")
            for i, op in enumerate(oportunidades, 1):
                with st.expander(f"Oportunidad #{i} — {op['destino_1']} + {op['destino_2']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Distancia", f"{op['distancia_millas']} millas")
                    col2.metric("Peso combinado", f"{op['peso_combinado']:,} lbs")
                    col3.metric("Espacio disponible", f"{op['espacio_disponible']:,} lbs")
                    st.markdown(f"**Shipment 1:** {op['shipment_1']} → {op['destino_1']} ({op['peso_1']:,} lbs)")
                    st.markdown(f"**Shipment 2:** {op['shipment_2']} → {op['destino_2']} ({op['peso_2']:,} lbs)")
                    st.markdown(f"**Trailer sugerido:** {op['trailer_sugerido']}")
        else:
            st.warning("No se detectaron oportunidades de consolidacion con los shipments activos.")