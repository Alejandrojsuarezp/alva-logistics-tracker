# ============================================
# ALVA LOGISTICS TRACKER - Conexion a Airtable
# ============================================

import requests
import json
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
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = response.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if offset:
            params["offset"] = offset
        else:
            break
    return all_records

def _resolve_list_field(raw):
    """Helper: Airtable lookup fields often return lists. Flatten to a display string."""
    if isinstance(raw, list):
        return ", ".join([str(x) for x in raw if x])
    return str(raw) if raw else ""

def _resolve_scalar(raw):
    """Normalize an Airtable field value down to a clean string. Select/lookup fields can come
    back as a plain string, a list (lookup rollups, multi-select), or a dict (e.g. a linked
    record reference) — handle all three instead of assuming a plain string."""
    if isinstance(raw, list):
        return _resolve_scalar(raw[0]) if raw else ""
    if isinstance(raw, dict):
        return str(raw.get("name") or raw.get("value") or raw.get("text") or raw.get("id") or "")
    return str(raw) if raw else ""

def _resolve_warehouse(fields):
    """Warehouse comes from a lookup field on Loads, rolled up from linked shipments.
    Airtable auto-names un-renamed lookup fields (e.g. "Warehouse (from Linked Shipments)")."""
    for key, raw in fields.items():
        if key == "Warehouse" or key.startswith("Warehouse ("):
            return _resolve_scalar(raw)
    return ""

def get_active_shipments():
    formula = "OR({Warehouse Status}='Pending Print', {Warehouse Status}='In Progress', {Warehouse Status}='Ready')"
    records = get_records(SHIPMENTS_TABLE, formula)

    # Build load_id -> load_number map to resolve linked loads
    load_records = get_records(LOADS_TABLE)
    id_to_load_number = {
        r["id"]: r.get("fields", {}).get("Load Number", "")
        for r in load_records
    }

    shipments = []
    for record in records:
        fields = record.get("fields", {})

        # Check if this shipment has a load assigned
        # The field "Loads" is the reverse link from Loads table
        linked_load_ids = fields.get("Loads", [])
        if not isinstance(linked_load_ids, list):
            linked_load_ids = []
        # Resolve load IDs to load numbers
        load_numbers = [id_to_load_number.get(rid, "") for rid in linked_load_ids if rid]
        load_assigned = ", ".join([n for n in load_numbers if n]) if load_numbers else ""

        shipments.append({
            "id": record["id"],
            "shipment_number": fields.get("Shipment Number", ""),
            "customer": fields.get("Customer", ""),
            "warehouse": fields.get("Warehouse", ""),
            "address": fields.get("Address", ""),
            "city": fields.get("City", ""),
            "state": fields.get("State", ""),
            "zip_code": fields.get("ZIP Code", ""),
            "weight": fields.get("Weight", 0),
            "bundles": fields.get("Bundles", 0),
            "elbows": fields.get("Elbows", 0),
            "dimensions": fields.get("Dimensions", ""),
            "trailer_type": fields.get("Trailer Type Needed", ""),
            "warehouse_status": fields.get("Warehouse Status", ""),
            "pick_up": fields.get("Pick Up", "No"),
            "delivery_date": fields.get("Requested Delivery Date", ""),
            "order_date": fields.get("Order Date", ""),
            "load_assigned": load_assigned,
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
            "warehouse": fields.get("Warehouse", ""),
            "address": fields.get("Address", ""),
            "city": fields.get("City", ""),
            "state": fields.get("State", ""),
            "zip_code": fields.get("ZIP Code", ""),
            "weight": fields.get("Weight", 0),
            "bundles": fields.get("Bundles", 0),
            "elbows": fields.get("Elbows", 0),
            "dimensions": fields.get("Dimensions", ""),
            "trailer_type": fields.get("Trailer Type Needed", ""),
            "warehouse_status": fields.get("Warehouse Status", ""),
            "pick_up": fields.get("Pick Up", "No"),
            "delivery_date": fields.get("Requested Delivery Date", ""),
            "order_date": fields.get("Order Date", "")
        })
    return shipments

def get_shipment_number_map():
    """Fetch Shipments once and build id -> Shipment Number, for resolving linked records elsewhere."""
    shipment_records = get_records(SHIPMENTS_TABLE)
    return {
        r["id"]: r.get("fields", {}).get("Shipment Number", "")
        for r in shipment_records
    }

def get_shipment_lookup_maps():
    """Fetch Shipments once and build id -> Shipment Number and id -> State in a single pass,
    for callers (like get_loads) that need both without fetching Shipments twice."""
    shipment_records = get_records(SHIPMENTS_TABLE)
    id_to_number = {}
    id_to_state = {}
    for r in shipment_records:
        f = r.get("fields", {})
        id_to_number[r["id"]] = f.get("Shipment Number", "")
        id_to_state[r["id"]] = f.get("State", "")
    return id_to_number, id_to_state

def get_loads(id_to_shpt_number=None, id_to_shpt_state=None, debug=False):
    records = get_records(LOADS_TABLE)
    # Resolves "Linked Shipments" (multipleRecordLinks, returns record IDs) into readable numbers.
    # Accepts pre-built maps so callers needing several of these functions can fetch Shipments once.
    if id_to_shpt_number is None or id_to_shpt_state is None:
        number_map, state_map = get_shipment_lookup_maps()
        if id_to_shpt_number is None:
            id_to_shpt_number = number_map
        if id_to_shpt_state is None:
            id_to_shpt_state = state_map

    if debug and records:
        print("DEBUG get_loads() — raw fields of first Load record from Airtable:")
        print(json.dumps(records[0].get("fields", {}), indent=2, default=str))

    loads = []
    for record in records:
        fields = record.get("fields", {})

        # Carrier comes from a lookup field (array)
        carrier = _resolve_list_field(fields.get("Carrier", ""))

        # Warehouse comes from a lookup field (array), rolled up from linked shipments
        warehouse = _resolve_warehouse(fields)

        # Freight cost / Sales value come from lookup fields (arrays)
        freight_raw = fields.get("Freight Cost", 0)
        freight = freight_raw[0] if isinstance(freight_raw, list) and freight_raw else (freight_raw if not isinstance(freight_raw, list) else 0)

        sales_raw = fields.get("Sales Value", 0)
        sales = sales_raw[0] if isinstance(sales_raw, list) and sales_raw else (sales_raw if not isinstance(sales_raw, list) else 0)

        # Linked Shipments is multipleRecordLinks -> list of record IDs
        linked_ids = fields.get("Linked Shipments", [])
        if not isinstance(linked_ids, list):
            linked_ids = []
        linked_numbers = [id_to_shpt_number.get(rid, rid) for rid in linked_ids]
        linked_shipments = ", ".join([str(n) for n in linked_numbers if n]) or "—"

        # The "Destinations" lookup on Loads often only contains the city (e.g. "STERLING HEIGHTS"),
        # with no state. Fall back to the state of the first linked shipment that has one.
        destination_state = ""
        for rid in linked_ids:
            st_val = id_to_shpt_state.get(rid, "")
            if st_val:
                destination_state = st_val
                break

        loads.append({
            "id": record["id"],
            "load_number": fields.get("Load Number", ""),
            "carrier": carrier,
            "warehouse": warehouse,
            "trailer_type": _resolve_scalar(fields.get("Trailer Type", "")),
            "total_weight": f"{int(fields.get('Total Weight', 0) or 0):,}",
            "total_bundles": fields.get("Total Bundles", 0),
            "destinations": fields.get("Destinations", []),
            "destination_state": destination_state,
            "load_status": _resolve_scalar(fields.get("Load Status", "")),
            "eta_pickup": format_date(fields.get("ETA Pickup", "")),
            "freight_cost": freight,
            "sales_value": sales,
            "freight_pct": fields.get("Freight %", 0),
            "linked_shipments": linked_shipments,
            "linked_shipment_ids": linked_ids,
        })
    return loads

def get_pricing(id_to_shpt_number=None):
    records = get_records(PRICING_TABLE)
    if id_to_shpt_number is None:
        id_to_shpt_number = get_shipment_number_map()

    quotes = []
    for record in records:
        fields = record.get("fields", {})

        linked_ids = fields.get("Shipments", [])
        if not isinstance(linked_ids, list):
            linked_ids = []
        linked_numbers = [id_to_shpt_number.get(rid, rid) for rid in linked_ids]
        linked_shipments = ", ".join([str(n) for n in linked_numbers if n]) or "—"

        quotes.append({
            "id": record["id"],
            "quote_number": fields.get("Q-", ""),
            "carrier": fields.get("Carrier", ""),
            "freight_cost": fields.get("Freight Cost", 0),
            "sales_value": fields.get("Sales Value", 0),
            "freight_pct": fields.get("Freight %", 0),
            "profit": fields.get("Profit $", 0),
            "status": fields.get("Status", ""),
            "linked_shipments": linked_shipments,
        })
    return quotes

def get_updates_log(id_to_shpt_number=None):
    records = get_records(UPDATES_LOG_TABLE)
    if id_to_shpt_number is None:
        id_to_shpt_number = get_shipment_number_map()

    updates = []
    for record in records:
        fields = record.get("fields", {})

        # "Shipment" is multipleRecordLinks -> list of record IDs
        shipment_ids = fields.get("Shipment", [])
        if not isinstance(shipment_ids, list):
            shipment_ids = []
        shipment_numbers = [id_to_shpt_number.get(rid, rid) for rid in shipment_ids]
        shipment = ", ".join([str(n) for n in shipment_numbers if n]) or ""

        # "Linked Load" is a lookup field (array)
        load_raw = fields.get("Linked Load", "")
        load = _resolve_list_field(load_raw)

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
    response = requests.patch(url, headers=HEADERS, json={"fields": fields}, timeout=10)
    return response.json()