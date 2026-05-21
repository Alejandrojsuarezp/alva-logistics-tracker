# ============================================
# ALVA LOGISTICS TRACKER - Detector de Consolidaciones
# ============================================

import smtplib
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
from airtable_connection import get_active_shipments

geolocator = Nominatim(user_agent="alva_logistics")

def get_coordinates(city, state):
    try:
        location = geolocator.geocode(f"{city}, {state}, USA")
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception:
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

def detectar_consolidaciones():
    print("Obteniendo shipments activos de Airtable...")
    shipments = get_active_shipments()
    print(f"Shipments activos: {len(shipments)}")

    print("Obteniendo coordenadas...")
    for s in shipments:
        s["coords"] = get_coordinates(s["city"], s["state"])
        time.sleep(1)

    shipments_con_coords = [s for s in shipments if s["coords"]]
    oportunidades = []

    for s1, s2 in combinations(shipments_con_coords, 2):
        distancia = calcular_distancia_millas(s1["coords"], s2["coords"])
        peso_combinado = s1["weight"] + s2["weight"]
        trailer_sugerido, capacidad = evaluar_trailer(peso_combinado)
        espacio_disponible = capacidad - peso_combinado

        if distancia <= DISTANCIA_MAX_MILLAS and capacidad > 0:
            oportunidades.append({
                "shipment_1": s1["shipment_number"],
                "destino_1": f"{s1['city']}, {s1['state']}",
                "peso_1": s1["weight"],
                "shipment_2": s2["shipment_number"],
                "destino_2": f"{s2['city']}, {s2['state']}",
                "peso_2": s2["weight"],
                "distancia_millas": round(distancia, 1),
                "peso_combinado": peso_combinado,
                "trailer_sugerido": trailer_sugerido,
                "espacio_disponible": espacio_disponible
            })

    return oportunidades

def enviar_email_consolidacion(oportunidades):
    if not oportunidades:
        print("No hay oportunidades que reportar.")
        return

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    cuerpo = f"DETECTOR DE CONSOLIDACION - ALVA LOGISTICS\n"
    cuerpo += f"Fecha: {fecha}\n"
    cuerpo += "=" * 50 + "\n\n"
    cuerpo += f"{len(oportunidades)} OPORTUNIDAD(ES) DETECTADA(S):\n\n"

    for i, op in enumerate(oportunidades, 1):
        cuerpo += f"OPORTUNIDAD #{i}\n"
        cuerpo += f"  Shipment 1 : {op['shipment_1']} → {op['destino_1']} ({op['peso_1']:,} lbs)\n"
        cuerpo += f"  Shipment 2 : {op['shipment_2']} → {op['destino_2']} ({op['peso_2']:,} lbs)\n"
        cuerpo += f"  Distancia  : {op['distancia_millas']} millas\n"
        cuerpo += f"  Peso total : {op['peso_combinado']:,} lbs\n"
        cuerpo += f"  Trailer    : {op['trailer_sugerido']}\n"
        cuerpo += f"  Espacio    : {op['espacio_disponible']:,} lbs disponibles\n\n"

    cuerpo += "=" * 50 + "\n"
    cuerpo += "Alva Logistics Tracker — Script automatico"

    mensaje = MIMEMultipart()
    mensaje["From"] = EMAIL_REMITENTE
    mensaje["To"] = EMAIL_DESTINATARIO
    mensaje["Subject"] = f"Consolidacion Detectada - {len(oportunidades)} Oportunidad(es) — {datetime.now().strftime('%m/%d/%Y')}"
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
    oportunidades = detectar_consolidaciones()
    if oportunidades:
        print(f"\n{len(oportunidades)} oportunidad(es) detectada(s)")
        for i, op in enumerate(oportunidades, 1):
            print(f"\nOPORTUNIDAD #{i}")
            print(f"  {op['shipment_1']} → {op['destino_1']} ({op['peso_1']:,} lbs)")
            print(f"  {op['shipment_2']} → {op['destino_2']} ({op['peso_2']:,} lbs)")
            print(f"  Distancia  : {op['distancia_millas']} millas")
            print(f"  Peso total : {op['peso_combinado']:,} lbs")
            print(f"  Trailer    : {op['trailer_sugerido']}")
            print(f"  Espacio    : {op['espacio_disponible']:,} lbs disponibles")
        enviar_email_consolidacion(oportunidades)
    else:
        print("No se detectaron oportunidades de consolidacion.")