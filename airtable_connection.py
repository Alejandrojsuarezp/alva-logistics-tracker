# ============================================
# ALVA LOGISTICS TRACKER - Conexion a Airtable
# ============================================

import requests
from config import AIRTABLE_TOKEN, BASE_ID, SHIPMENTS_TABLE, PRICING_TABLE, LOADS_TABLE, UPDATES_LOG_TABLE, BUNDLE_DIMENSIONS_TABLE

def format_date(date_str):
    if not date_str:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%m/%d/%Y %I:%M %p")
    except:
        return date_str

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

        # Get carrier from lookup
        carrier_raw = fields.get("Carrier", "")
        if isinstance(carrier_raw, list):
            carrier = carrier_raw[0] if carrier_raw else ""
        else:
            carrier = carrier_raw

        # Get freight cost from lookup
        freight_raw = fields.get("Freight Cost", 0)
        if isinstance(freight_raw, list):
            freight = freight_raw[0] if freight_raw else 0
        else:
            freight = freight_raw

        # Get sales value from lookup
        sales_raw = fields.get("Sales Value", 0)
        if isinstance(sales_raw, list):
            sales = sales_raw[0] if sales_raw else 0
        else:
            sales = sales_raw

        # Get linked shipment numbers from lookup field
        shpt_numbers_raw = fields.get("Shipment Numbers", [])
        if isinstance(shpt_numbers_raw, list) and shpt_numbers_raw:
            linked_shipments = ", ".join([str(s) for s in shpt_numbers_raw])
        elif isinstance(shpt_numbers_raw, str) and shpt_numbers_raw:
            linked_shipments = shpt_numbers_raw
        else:
            # Fallback: count linked records
            linked_raw = fields.get("Linked Shipments", [])
            n = len(linked_raw) if isinstance(linked_raw, list) else 0
            linked_shipments = f"{n} shipment(s)" if n > 0 else "—"

        loads.append({
            "id": record["id"],
            "load_number": fields.get("Load Number", ""),
            "carrier": carrier,
            "total_weight": f"{int(fields.get('Total Weight', 0)):,}",
            "total_bundles": fields.get("Total Bundles", 0),
            "destinations": fields.get("Destinations", []),
            "load_status": fields.get("Load Status", ""),
            "eta_pickup": format_date(fields.get("ETA Pickup", "")),
            "freight_cost": freight,
            "sales_value": sales,
            "freight_pct": fields.get("Freight %", 0),
            "linked_shipments": linked_shipments
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

def get_updates_log():
    records = get_records(UPDATES_LOG_TABLE)
    updates = []
    for record in records:
        fields = record.get("fields", {})
        shipment_raw = fields.get("Shipment", "")
        if isinstance(shipment_raw, list):
            shipment = shipment_raw[0] if shipment_raw else ""
        else:
            shipment = shipment_raw
        load_raw = fields.get("Linked Load", "")
        if isinstance(load_raw, list):
            load = load_raw[0] if load_raw else ""
        else:
            load = load_raw
        updates.append({
            "id": record["id"],
            "update": fields.get("Update", ""),
            "shipment": shipment,
            "linked_load": load,
            "datetime": format_date(fields.get("Date/Time", "")),
            "type": fields.get("Type", ""),
            "description": fields.get("Description", ""),
            "responsible": fields.get("Responsible", ""),
            "attention_flag": fields.get("Attention Flag", False)
        })
    return updates

def get_bundle_dimensions():
    records = get_records(BUNDLE_DIMENSIONS_TABLE)
    dimensions = []
    for record in records:
        fields = record.get("fields", {})
        dimensions.append({
            "id": record["id"],
            "size": fields.get("Size", ""),
            "sch": fields.get("SCH", ""),
            "length_ft": fields.get("Length (ft)", 0),
            "length_in": fields.get("Length (in)", 0),
            "width_in": fields.get("Width (in)", 0),
            "height_in": fields.get("Height (in)", 0)
        })
    return dimensions

def update_record(table_id, record_id, fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}/{record_id}"
    response = requests.patch(url, headers=HEADERS, json={"fields": fields})
    return response.json()
