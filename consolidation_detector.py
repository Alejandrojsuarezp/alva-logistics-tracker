# ============================================
# ALVA LOGISTICS TRACKER - Detector de Consolidaciones
# ============================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

from config import (
    DISTANCIA_MAX_MILLAS,
    EMAIL_REMITENTE, EMAIL_CONTRASENA, EMAIL_DESTINATARIO,
    SHIPMENTS_TABLE
)
from airtable_connection import get_active_shipments, update_record

geolocator = Nominatim(user_agent="alva_logistics")

# ── SHIPMENT COORDINATES ──────────────────────────────────────────────────────
# Persistent cache lives on the Shipment record itself (Airtable "Coordinates" field,
# format "lat,lon") — no local cache file. Once a shipment is geocoded, future runs
# read it straight from Airtable and never call Nominatim for it again.

def _parse_coordinates(raw):
    """Parse a Coordinates field value ('lat,lon' string) into a (lat, lon) tuple, or None."""
    if not raw:
        return None
    try:
        lat_str, lon_str = str(raw).split(",")
        return (float(lat_str.strip()), float(lon_str.strip()))
    except (ValueError, AttributeError):
        return None

def get_shipment_coordinates(shipment):
    """Return (lat, lon) for a shipment. Uses the cached 'Coordinates' field on the Airtable
    record if present — skips Nominatim entirely. Otherwise geocodes via Nominatim (structured
    address, falling back to city/state) and writes the result back to that field so future
    runs use the cached value."""
    cached = _parse_coordinates(shipment.get("coordinates"))
    if cached:
        return cached

    structured = {"country": "USA"}
    if shipment.get("address"):
        structured["street"] = str(shipment["address"]).strip()
    if shipment.get("city"):
        structured["city"] = str(shipment["city"]).strip()
    if shipment.get("state"):
        structured["state"] = str(shipment["state"]).strip()
    if shipment.get("zip_code"):
        structured["postalcode"] = str(shipment["zip_code"]).strip()

    coords = None
    if len(structured) > 1:
        time.sleep(1)  # Nominatim rate-limit courtesy
        try:
            location = geolocator.geocode(structured)
            if location:
                coords = (location.latitude, location.longitude)
        except Exception as e:
            print(f"Geocoding error for structured address {structured}: {e}")

    if not coords and shipment.get("city") and shipment.get("state"):
        time.sleep(1)
        try:
            location = geolocator.geocode(f"{shipment['city']}, {shipment['state']}, USA")
            if location:
                coords = (location.latitude, location.longitude)
        except Exception as e:
            print(f"Geocoding error for {shipment['city']}, {shipment['state']}: {e}")

    if coords and shipment.get("id"):
        try:
            update_record(SHIPMENTS_TABLE, shipment["id"], {"Coordinates": f"{coords[0]},{coords[1]}"})
        except Exception as e:
            print(f"Warning: could not write coordinates back to Airtable for {shipment.get('shipment_number','?')}: {e}")

    return coords

def calcular_distancia_millas(coords1, coords2):
    return geodesic(coords1, coords2).kilometers * 0.621371

def _filtrar_elegibles(shipments):
    """Split shipments into (eligible, excluded). A shipment is excluded if it's marked
    Pick Up = Yes (doesn't need logistics consolidation) or has no recognized warehouse.
    Excluded entries carry a human-readable reason for surfacing in the UI."""
    eligible = []
    excluded = []
    for s in shipments:
        if s.get("pick_up") == "Yes":
            excluded.append({"shipment_number": s.get("shipment_number", "?"), "reason": "Pick Up = Yes"})
        elif s.get("warehouse") not in ("Texas", "Florida"):
            excluded.append({"shipment_number": s.get("shipment_number", "?"), "reason": "No warehouse assigned"})
        else:
            eligible.append(s)
    return eligible, excluded

def _agrupar_por_warehouse(shipments):
    grupos = {"Texas": [], "Florida": []}
    for s in shipments:
        grupos[s["warehouse"]].append(s)
    return grupos

def _shipment_summary(s):
    """Compact view of a shipment for the UI — used both for the base shipment and for matches."""
    return {
        "shipment_number": s.get("shipment_number", ""),
        "destination": f"{s.get('city','')}, {s.get('state','')}",
        "weight": s.get("weight", 0),
        "trailer_type": s.get("trailer_type", ""),
        "status": s.get("warehouse_status", ""),
        "load_assigned": s.get("load_assigned", ""),
    }

def _construir_matches(shpts_con_coords):
    """For each shipment, find its top 3 closest other shipments in the same warehouse group
    (within DISTANCIA_MAX_MILLAS), ordered by distance ascending. Shipments with no candidate
    within range are skipped entirely — nothing to show."""
    resultados = []
    for base in shpts_con_coords:
        candidatos = []
        for other in shpts_con_coords:
            if other is base:
                continue
            distancia = calcular_distancia_millas(base["coords"], other["coords"])
            if distancia > DISTANCIA_MAX_MILLAS:
                continue
            match = _shipment_summary(other)
            match["distance_miles"] = round(distancia, 1)
            match["combined_weight"] = base.get("weight", 0) + other.get("weight", 0)
            candidatos.append(match)

        if not candidatos:
            continue

        candidatos.sort(key=lambda m: m["distance_miles"])
        resultados.append({
            "shipment": _shipment_summary(base),
            "matches": candidatos[:3],
        })
    return resultados

def detectar_consolidaciones():
    """
    Returns a dict: {"Texas": [...], "Florida": [...], "excluded": [...]}
    Each Texas/Florida entry is {"shipment": {...}, "matches": [...]} — a shipment's top 3
    closest other shipments in the same warehouse, ordered by distance (shortest first).
    Shipments from different warehouses are never compared against each other. "excluded"
    lists active shipments that were skipped from detection entirely, with a reason each.
    """
    print("Obteniendo shipments activos de Airtable...")
    shipments = get_active_shipments()
    shipments, excluded = _filtrar_elegibles(shipments)
    print(f"Shipments elegibles: {len(shipments)} — excluidos: {len(excluded)}")

    print("Obteniendo coordenadas de shipments...")
    for s in shipments:
        s["coords"] = get_shipment_coordinates(s)

    grupos = _agrupar_por_warehouse(shipments)
    resultado = {"Texas": [], "Florida": [], "excluded": excluded}

    for warehouse, shpts_wh in grupos.items():
        shpts_con_coords = [s for s in shpts_wh if s.get("coords")]
        resultado[warehouse] = _construir_matches(shpts_con_coords)

    return resultado

def enviar_email_consolidacion(resultado_por_warehouse):
    resultado_por_warehouse = {k: v for k, v in resultado_por_warehouse.items() if k in ("Texas", "Florida")}
    total_shipments = sum(len(v) for v in resultado_por_warehouse.values())
    if total_shipments == 0:
        print("No hay oportunidades que reportar.")
        return

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    cuerpo = f"DETECTOR DE CONSOLIDACION - ALVA LOGISTICS\n"
    cuerpo += f"Fecha: {fecha}\n"
    cuerpo += "=" * 50 + "\n\n"
    cuerpo += f"{total_shipments} SHIPMENT(S) CON OPORTUNIDADES DE CONSOLIDACION\n\n"

    for warehouse, entradas in resultado_por_warehouse.items():
        cuerpo += "=" * 50 + "\n"
        cuerpo += f"{warehouse.upper()} WAREHOUSE — {len(entradas)} shipment(s)\n"
        cuerpo += "=" * 50 + "\n\n"

        for entrada in entradas:
            base = entrada["shipment"]
            cuerpo += f"{base['shipment_number']} -> {base['destination']} ({base['weight']:,} lbs)\n"
            for i, m in enumerate(entrada["matches"], 1):
                cuerpo += (
                    f"  #{i}: {m['shipment_number']} -> {m['destination']} "
                    f"({m['weight']:,} lbs) — {m['distance_miles']} mi, "
                    f"combined {m['combined_weight']:,} lbs\n"
                )
            cuerpo += "\n"

    cuerpo += "=" * 50 + "\n"
    cuerpo += "Alva Logistics Tracker — Script automatico"

    mensaje = MIMEMultipart()
    mensaje["From"] = EMAIL_REMITENTE
    mensaje["To"] = EMAIL_DESTINATARIO
    mensaje["Subject"] = f"Consolidacion Detectada - {total_shipments} Shipment(s) — {datetime.now().strftime('%m/%d/%Y')}"
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(EMAIL_REMITENTE, EMAIL_CONTRASENA)
        servidor.sendmail(EMAIL_REMITENTE, EMAIL_DESTINATARIO, mensaje.as_string())
        servidor.quit()
        print(f"Email enviado exitosamente a {EMAIL_DESTINATARIO}")
    except Exception as e:
        print(f"Error enviando email: {e}")

if __name__ == "__main__":
    resultado = detectar_consolidaciones()
    excluidos = resultado.get("excluded", [])
    if excluidos:
        print(f"\n{len(excluidos)} shipment(s) excluido(s):")
        for e in excluidos:
            print(f"  - {e['shipment_number']}: {e['reason']}")

    total = len(resultado.get("Texas", [])) + len(resultado.get("Florida", []))
    if total:
        print(f"\n{total} shipment(s) con oportunidades de consolidacion")
        for warehouse in ("Texas", "Florida"):
            entradas = resultado.get(warehouse, [])
            print(f"\n--- {warehouse.upper()} ({len(entradas)}) ---")
            for entrada in entradas:
                base = entrada["shipment"]
                print(f"\n{base['shipment_number']} -> {base['destination']} ({base['weight']:,} lbs)")
                for i, m in enumerate(entrada["matches"], 1):
                    print(f"  #{i}: {m['shipment_number']} -> {m['destination']} — {m['distance_miles']} mi")
        enviar_email_consolidacion(resultado)
    else:
        print("No se detectaron oportunidades de consolidacion.")