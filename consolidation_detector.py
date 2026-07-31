# ============================================
# ALVA LOGISTICS TRACKER - Detector de Consolidaciones
# ============================================

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from itertools import combinations
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

from config import (
    DISTANCIA_MAX_MILLAS, PESO_MAX_FLATBED,
    PESO_MAX_STEPDECK, PESO_MAX_HOTSHOT,
    EMAIL_REMITENTE, EMAIL_CONTRASENA, EMAIL_DESTINATARIO
)
from airtable_connection import get_active_shipments, get_loads

geolocator = Nominatim(user_agent="alva_logistics")

# Trailer types considered "small" for Type C upgrade detection
TRAILERS_PEQUENOS = ["Hotshot 40'"]
TRAILERS_GRANDES_SUGERIDOS = ["Flatbed 48'", "Stepdeck 48'"]

# Weight capacity by trailer type, for Type B "fits in existing load" checks.
# LTL has no fixed weight capacity and is handled separately (skipped).
CAPACIDAD_POR_TRAILER = {
    "Hotshot 40'": PESO_MAX_HOTSHOT,
    "Flatbed 48'": PESO_MAX_FLATBED,
    "Flatbed 53'": PESO_MAX_FLATBED,
    "Stepdeck 48'": PESO_MAX_STEPDECK,
    "Stepdeck 53'": PESO_MAX_STEPDECK,
    "Conestoga 48'": PESO_MAX_FLATBED,
    "Conestoga 53'": PESO_MAX_FLATBED,
}

# ── PERSISTENT COORDS CACHE ──────────────────────────────────────────────────
# Stores geocoded coordinates so Nominatim is never called twice for the same city.
# File lives in the same directory as this script.
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coords_cache.json")

def _load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save coords cache: {e}")

def get_coordinates(city, state, cache):
    """Return (lat, lon) for city/state. Reads/writes the shared in-memory cache dict
    (see _load_cache) so callers only need to load it from disk once per run."""
    key = f"{city.strip().lower()},{state.strip().lower()}"

    if key in cache:
        cached = cache[key]
        if cached is None:
            return None
        return tuple(cached)

    # Not in cache — call Nominatim
    try:
        location = geolocator.geocode(f"{city}, {state}, USA")
        if location:
            coords = (location.latitude, location.longitude)
            cache[key] = list(coords)
            _save_cache(cache)
            return coords
        else:
            cache[key] = None
            _save_cache(cache)
            return None
    except Exception as e:
        print(f"Geocoding error for {city}, {state}: {e}")
        return None

def calcular_distancia_millas(coords1, coords2):
    return geodesic(coords1, coords2).kilometers * 0.621371

def evaluar_trailer(peso_total):
    if peso_total <= PESO_MAX_HOTSHOT:
        return "Hotshot 40'", PESO_MAX_HOTSHOT
    elif peso_total <= PESO_MAX_FLATBED:
        return "Flatbed 48' o Stepdeck 48'", PESO_MAX_FLATBED
    else:
        return "Excede capacidad", 0

def _shipments_elegibles(shipments):
    """Filter out shipments marked as Pick Up = Yes — they don't need logistics consolidation."""
    return [s for s in shipments if s.get("pick_up") != "Yes"]

def _agrupar_por_warehouse(shipments):
    grupos = {"Texas": [], "Florida": []}
    for s in shipments:
        wh = s.get("warehouse")
        if wh in grupos:
            grupos[wh].append(s)
        else:
            print(f"Warning: shipment {s.get('shipment_number', '?')} has no recognized warehouse ('{wh}') — excluded from consolidation detection")
    return grupos

def _detectar_tipo_a(shipments_sin_coords_filtradas):
    """Type A: two shipments without a load, close destinations, combined weight fits one trailer."""
    oportunidades = []
    for s1, s2 in combinations(shipments_sin_coords_filtradas, 2):
        if not s1.get("coords") or not s2.get("coords"):
            continue
        distancia = calcular_distancia_millas(s1["coords"], s2["coords"])
        peso_combinado = s1["weight"] + s2["weight"]
        trailer_sugerido, capacidad = evaluar_trailer(peso_combinado)
        espacio_disponible = capacidad - peso_combinado

        if distancia <= DISTANCIA_MAX_MILLAS and capacidad > 0:
            oportunidades.append({
                "tipo": "A",
                "descripcion": "Dos shipments sin load — combinar en un trailer",
                "shipment_1": s1["shipment_number"],
                "destino_1": f"{s1['city']}, {s1['state']}",
                "peso_1": s1["weight"],
                "status_1": s1.get("warehouse_status", ""),
                "load_1": s1.get("load_assigned", ""),
                "shipment_2": s2["shipment_number"],
                "destino_2": f"{s2['city']}, {s2['state']}",
                "peso_2": s2["weight"],
                "status_2": s2.get("warehouse_status", ""),
                "load_2": s2.get("load_assigned", ""),
                "distancia_millas": round(distancia, 1),
                "peso_combinado": peso_combinado,
                "trailer_sugerido": trailer_sugerido,
                "espacio_disponible": espacio_disponible
            })
    return oportunidades

def _detectar_tipo_b(shipments_filtrados, loads_activos):
    """Type B: a shipment without load fits in an existing load with available space."""
    oportunidades = []
    for s in shipments_filtrados:
        if not s.get("coords"):
            continue
        for load in loads_activos:
            load_coords = load.get("coords")
            if not load_coords:
                continue
            distancia = calcular_distancia_millas(s["coords"], load_coords)
            if distancia > DISTANCIA_MAX_MILLAS:
                continue

            trailer_tipo = load.get("trailer_type", "")
            if trailer_tipo == "LTL":
                continue  # LTL has no fixed weight capacity to check against

            capacidad_trailer = CAPACIDAD_POR_TRAILER.get(trailer_tipo)
            if capacidad_trailer is None:
                print(f"Warning: load {load.get('load_number','?')} has unrecognized trailer type '{trailer_tipo}' — skipping Type B capacity check")
                continue

            try:
                peso_actual_load = int(str(load.get("total_weight", "0")).replace(",", ""))
            except (ValueError, TypeError):
                peso_actual_load = 0
            espacio_disponible = capacidad_trailer - peso_actual_load

            if espacio_disponible >= s["weight"]:
                oportunidades.append({
                    "tipo": "B",
                    "descripcion": "Shipment sin load cabe en un load existente",
                    "shipment_1": s["shipment_number"],
                    "destino_1": f"{s['city']}, {s['state']}",
                    "peso_1": s["weight"],
                    "status_1": s.get("warehouse_status", ""),
                    "load_1": s.get("load_assigned", ""),
                    "load_existente": load.get("load_number", ""),
                    "load_destino": load.get("destinations", ""),
                    "distancia_millas": round(distancia, 1),
                    "espacio_disponible_en_load": espacio_disponible,
                    "trailer_sugerido": f"Agregar a {load.get('load_number','')}"
                })
    return oportunidades

def _detectar_tipo_c(shipments_filtrados):
    """Type C: two shipments each assigned a small trailer (e.g. Hotshot) that together
    justify upgrading to one larger trailer."""
    oportunidades = []
    candidatos = [s for s in shipments_filtrados if s.get("trailer_type") in TRAILERS_PEQUENOS]

    for s1, s2 in combinations(candidatos, 2):
        if not s1.get("coords") or not s2.get("coords"):
            continue
        distancia = calcular_distancia_millas(s1["coords"], s2["coords"])
        peso_combinado = s1["weight"] + s2["weight"]

        if distancia <= DISTANCIA_MAX_MILLAS and peso_combinado <= PESO_MAX_FLATBED:
            oportunidades.append({
                "tipo": "C",
                "descripcion": "Dos shipments con trailer pequeño asignado — considerar upgrade",
                "shipment_1": s1["shipment_number"],
                "destino_1": f"{s1['city']}, {s1['state']}",
                "peso_1": s1["weight"],
                "status_1": s1.get("warehouse_status", ""),
                "load_1": s1.get("load_assigned", ""),
                "trailer_actual_1": s1.get("trailer_type", ""),
                "shipment_2": s2["shipment_number"],
                "destino_2": f"{s2['city']}, {s2['state']}",
                "peso_2": s2["weight"],
                "status_2": s2.get("warehouse_status", ""),
                "load_2": s2.get("load_assigned", ""),
                "trailer_actual_2": s2.get("trailer_type", ""),
                "distancia_millas": round(distancia, 1),
                "peso_combinado": peso_combinado,
                "trailer_sugerido": "Flatbed 48' (upgrade) — revisar pricing con brokers"
            })
    return oportunidades

def detectar_consolidaciones():
    """
    Returns a dict: {"Texas": [...], "Florida": [...]}
    Each list contains opportunities of Type A, B and C for that warehouse only.
    Shipments from different warehouses are never compared against each other.
    """
    print("Obteniendo shipments activos de Airtable...")
    shipments = get_active_shipments()
    shipments = _shipments_elegibles(shipments)
    print(f"Shipments elegibles (excluyendo Pick Up): {len(shipments)}")

    print("Obteniendo loads activos...")
    loads = get_loads()
    loads_activos = [l for l in loads if l.get("load_status") not in ("Shipped", "Delivered")]

    cache = _load_cache()  # loaded ONCE for the whole run, then passed around

    print("Obteniendo coordenadas de shipments...")
    for s in shipments:
        key = f"{s['city'].strip().lower()},{s['state'].strip().lower()}"
        if key not in cache:
            time.sleep(1)  # Only sleep when actually calling Nominatim
        s["coords"] = get_coordinates(s["city"], s["state"], cache)

    print("Obteniendo coordenadas de loads activos...")
    for l in loads_activos:
        destinos = l.get("destinations", "")
        if isinstance(destinos, list):
            destinos = destinos[0] if destinos else ""
        if destinos and "," in str(destinos):
            partes = str(destinos).split(",")
            ciudad = partes[0].strip()
            estado = partes[1].strip() if len(partes) > 1 else ""
            key = f"{ciudad.lower()},{estado.lower()}"
            if key not in cache:
                time.sleep(1)
            l["coords"] = get_coordinates(ciudad, estado, cache)
        else:
            l["coords"] = None

    grupos = _agrupar_por_warehouse(shipments)
    resultado = {"Texas": [], "Florida": []}

    for warehouse, shpts_wh in grupos.items():
        shpts_con_coords = [s for s in shpts_wh if s.get("coords")]

        tipo_a = _detectar_tipo_a(shpts_con_coords)
        tipo_b = _detectar_tipo_b(shpts_con_coords, loads_activos)
        tipo_c = _detectar_tipo_c(shpts_con_coords)

        resultado[warehouse] = tipo_a + tipo_b + tipo_c

    return resultado

def enviar_email_consolidacion(resultado_por_warehouse):
    total_oportunidades = sum(len(v) for v in resultado_por_warehouse.values())
    if total_oportunidades == 0:
        print("No hay oportunidades que reportar.")
        return

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    cuerpo = f"DETECTOR DE CONSOLIDACION - ALVA LOGISTICS\n"
    cuerpo += f"Fecha: {fecha}\n"
    cuerpo += "=" * 50 + "\n\n"
    cuerpo += f"{total_oportunidades} OPORTUNIDAD(ES) DETECTADA(S) EN TOTAL\n\n"

    for warehouse, oportunidades in resultado_por_warehouse.items():
        cuerpo += "=" * 50 + "\n"
        cuerpo += f"{warehouse.upper()} WAREHOUSE — {len(oportunidades)} oportunidad(es)\n"
        cuerpo += "=" * 50 + "\n\n"

        for i, op in enumerate(oportunidades, 1):
            cuerpo += f"OPORTUNIDAD #{i} — Tipo {op['tipo']}\n"
            cuerpo += f"  {op['descripcion']}\n"
            if op["tipo"] in ("A", "C"):
                cuerpo += f"  Shipment 1 : {op['shipment_1']} -> {op['destino_1']} ({op['peso_1']:,} lbs)\n"
                cuerpo += f"  Shipment 2 : {op['shipment_2']} -> {op['destino_2']} ({op['peso_2']:,} lbs)\n"
                cuerpo += f"  Distancia  : {op['distancia_millas']} millas\n"
                cuerpo += f"  Peso total : {op['peso_combinado']:,} lbs\n"
            elif op["tipo"] == "B":
                cuerpo += f"  Shipment   : {op['shipment_1']} -> {op['destino_1']} ({op['peso_1']:,} lbs)\n"
                cuerpo += f"  Load       : {op['load_existente']} -> {op['load_destino']}\n"
                cuerpo += f"  Distancia  : {op['distancia_millas']} millas\n"
                cuerpo += f"  Espacio disponible en load: {op['espacio_disponible_en_load']:,} lbs\n"
            cuerpo += f"  Sugerencia : {op['trailer_sugerido']}\n\n"

    cuerpo += "=" * 50 + "\n"
    cuerpo += "Alva Logistics Tracker — Script automatico"

    mensaje = MIMEMultipart()
    mensaje["From"] = EMAIL_REMITENTE
    mensaje["To"] = EMAIL_DESTINATARIO
    mensaje["Subject"] = f"Consolidacion Detectada - {total_oportunidades} Oportunidad(es) — {datetime.now().strftime('%m/%d/%Y')}"
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
    total = sum(len(v) for v in resultado.values())
    if total:
        print(f"\n{total} oportunidad(es) detectada(s) en total")
        for warehouse, oportunidades in resultado.items():
            print(f"\n--- {warehouse.upper()} ({len(oportunidades)}) ---")
            for i, op in enumerate(oportunidades, 1):
                print(f"\nOPORTUNIDAD #{i} — Tipo {op['tipo']}")
                print(f"  {op['descripcion']}")
                print(f"  Sugerencia: {op['trailer_sugerido']}")
        enviar_email_consolidacion(resultado)
    else:
        print("No se detectaron oportunidades de consolidacion.")