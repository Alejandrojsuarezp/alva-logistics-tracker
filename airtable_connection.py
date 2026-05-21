# ============================================
# ALVA LOGISTICS TRACKER - Conexion a Airtable
# ============================================

import requests
from config import AIRTABLE_TOKEN, BASE_ID, SHIPMENTS_TABLE, PRICING_TABLE, LOADS_TABLE, UPDATES_LOG_TABLE

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

def get_records(table_id, filter_formula=None):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
    params = {}
    if filter_formula:
        params["filterByFormula"] = filter_formula
    
    all_records = []
    while True:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if offset:
            params["offset"] = offset
        else:
            break
    return all_records

def get_active_shipments():
    formula = "OR({Warehouse Status}='Pending Print', {Warehouse Status}='In Progress', {Warehouse Status}='Ready')"
    records = get_records(SHIPMENTS_TABLE, formula)
    shipments = []
    for record in records:
        fields = record.get("fields", {})
        shipments.append({
            "id": record["id"],
            "shipment_number": fields.get("Shipment Number", ""),
            "customer": fields.get("Customer", ""),
            "city": fields.get("City", ""),
            "state": fields.get("State", ""),
            "zip_code": fields.get("ZIP Code", ""),
            "weight": fields.get("Weight", 0),
            "bundles": fields.get("Bundles", 0),
            "trailer_type": fields.get("Trailer Type Needed", ""),
            "warehouse_status": fields.get("Warehouse Status", ""),
            "delivery_date": fields.get("Requested Delivery Date", ""),
            "order_date": fields.get("Order Date", "")
        })
    return shipments

def get_all_shipments():
    records = get_records(SHIPMENTS_TABLE)
    shipments = []
    for record in records:
        fields = record.get("fields", {})
        shipments.append({
            "id": record["id"],
            "shipment_number": fields.get("Shipment Number", ""),
            "customer": fields.get("Customer", ""),
            "city": fields.get("City", ""),
            "state": fields.get("State", ""),
            "zip_code": fields.get("ZIP Code", ""),
            "weight": fields.get("Weight", 0),
            "bundles": fields.get("Bundles", 0),
            "trailer_type": fields.get("Trailer Type Needed", ""),
            "warehouse_status": fields.get("Warehouse Status", ""),
            "delivery_date": fields.get("Requested Delivery Date", ""),
            "order_date": fields.get("Order Date", "")
        })
    return shipments

def get_loads():
    records = get_records(LOADS_TABLE)
    loads = []
    for record in records:
        fields = record.get("fields", {})
        loads.append({
            "id": record["id"],
            "load_number": fields.get("Load Number", ""),
            "carrier": fields.get("Carrier", ""),
            "total_weight": fields.get("Total Weight", 0),
            "total_bundles": fields.get("Total Bundles", 0),
            "destinations": fields.get("Destinations", []),
            "load_status": fields.get("Load Status", ""),
            "eta_pickup": fields.get("ETA Pickup", ""),
            "freight_cost": fields.get("Freight Cost", 0),
            "sales_value": fields.get("Sales Value", 0),
            "freight_pct": fields.get("Freight %", 0)
        })
    return loads

def get_pricing():
    records = get_records(PRICING_TABLE)
    quotes = []
    for record in records:
        fields = record.get("fields", {})
        quotes.append({
            "id": record["id"],
            "quote_number": fields.get("Q-", ""),
            "carrier": fields.get("Carrier", ""),
            "freight_cost": fields.get("Freight Cost", 0),
            "sales_value": fields.get("Sales Value", 0),
            "freight_pct": fields.get("Freight %", 0),
            "profit": fields.get("Profit $", 0),
            "status": fields.get("Status", "")
        })
    return quotes

def update_record(table_id, record_id, fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}/{record_id}"
    print(f"Actualizando: {url}")
    print(f"Fields: {fields}")
    print(f"Token: {AIRTABLE_TOKEN[:20]}...")
    response = requests.patch(url, headers=HEADERS, json={"fields": fields})
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.json()
