# ============================================
# ALVA LOGISTICS TRACKER - Configuracion Global
# ============================================

import os
import streamlit as st

def get_secret(key, default=None):
    try:
        return st.secrets[key]
    except:
        return os.environ.get(key, default)

# Airtable
AIRTABLE_TOKEN = get_secret("AIRTABLE_TOKEN")
BASE_ID = get_secret("BASE_ID")

# IDs de las tablas
SHIPMENTS_TABLE = get_secret("SHIPMENTS_TABLE")
PRICING_TABLE = get_secret("PRICING_TABLE")
LOADS_TABLE = get_secret("LOADS_TABLE")
UPDATES_LOG_TABLE = get_secret("UPDATES_LOG_TABLE")

# Email
EMAIL_REMITENTE = get_secret("EMAIL_REMITENTE")
EMAIL_CONTRASENA = get_secret("EMAIL_CONTRASENA")
EMAIL_DESTINATARIO = get_secret("EMAIL_DESTINATARIO")

# Limites logisticos
DISTANCIA_MAX_MILLAS = 150
PESO_MAX_FLATBED = 48000
PESO_MAX_STEPDECK = 48000
PESO_MAX_HOTSHOT = 15000