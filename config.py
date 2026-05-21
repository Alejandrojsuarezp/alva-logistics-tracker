# ============================================
# ALVA LOGISTICS TRACKER - Configuracion Global
# ============================================

import streamlit as st

# Airtable
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
BASE_ID = st.secrets["BASE_ID"]

# IDs de las tablas
SHIPMENTS_TABLE = st.secrets["SHIPMENTS_TABLE"]
PRICING_TABLE = st.secrets["PRICING_TABLE"]
LOADS_TABLE = st.secrets["LOADS_TABLE"]
UPDATES_LOG_TABLE = st.secrets["UPDATES_LOG_TABLE"]

# Email
EMAIL_REMITENTE = st.secrets["EMAIL_REMITENTE"]
EMAIL_CONTRASENA = st.secrets["EMAIL_CONTRASENA"]
EMAIL_DESTINATARIO = st.secrets["EMAIL_DESTINATARIO"]

# Limites logisticos
DISTANCIA_MAX_MILLAS = 150
PESO_MAX_FLATBED = 48000
PESO_MAX_STEPDECK = 48000
PESO_MAX_HOTSHOT = 15000