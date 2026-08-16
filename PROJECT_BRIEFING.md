# Alva Logistics Tracker — Project Briefing

*Prepared 2026-08-09 for context handoff to a new Claude chat.*

## 1. Project Purpose & Business Context

Alva Logistics Tracker is an internal operations tool for a logistics/freight
brokerage business (referred to in the UI as "X Logistics Tracker") that ships
pipe/tubing products (bundles, elbows — plumbing/industrial pipe fittings) from
two warehouses (**Texas** and **Florida**) to customers around the US, mostly by
flatbed/stepdeck/hotshot/conestoga trailer.

Core business workflow the app supports:
1. **Shipments** are created (product, destination, weight, dimensions) at a warehouse.
2. **Pricing** — brokers get freight quotes from **carriers**, track them as
   Pending / Selected / Lost, and compute profit (Sales Value − Freight Cost).
3. Selected quotes become **Loads** (an actual truck booking with a carrier),
   which one or more Shipments get linked to (a Load can carry multiple
   consolidated Shipments).
4. **Consolidation detection** finds shipments at the same warehouse whose
   destinations are geographically close (within 250 miles), so they can be
   combined onto a single truck to save freight cost — flags the top-3 closest
   matches per shipment and can email a report.
5. **Updates Log** tracks a timestamped audit trail of status changes, delays,
   documentation, communication, issues, and billing notes per shipment/load.
6. **Live Map** visualizes all "Ready" loads geographically (color-coded by
   warehouse / consolidated).
7. **Truck Builder** is a standalone visual trailer-loading planner (separate
   HTML tool) for figuring out how bundles fit physically on a given trailer.

The business logic encodes real trucking constraints: max weight limits per
trailer type (Flatbed/Stepdeck 48,000 lbs, Hotshot 15,000 lbs), a 250-mile
consolidation radius, and warehouse-specific eligibility (Texas/Florida only).

## 2. Repository Files & Their Functions

| File | Role |
|---|---|
| `app.py` (2,082 lines) | Main Streamlit web app — all UI pages, styling, and Airtable read/write calls live here (monolithic single-file app). |
| `airtable_connection.py` | Airtable REST API wrapper — all `GET`/`PATCH` calls, field normalization, and record-shaping into plain dicts consumed by `app.py` and `consolidation_detector.py`. |
| `consolidation_detector.py` | Standalone script/module implementing geocoding + distance-based consolidation matching, plus an email report sender. Runnable directly (`python consolidation_detector.py`) as a cron-style batch job, and also imported live by the Streamlit "Consolidations" page. |
| `config.py` | Loads all secrets (`st.secrets`) and global constants (table IDs, weight limits, max consolidation distance). Single source of config truth. |
| `truck_builder.html` | Standalone, self-contained HTML/JS/CSS trailer-loading visualizer. Not served by Streamlit — hosted separately on GitHub Pages (`https://alejandrojsuarezp.github.io/alva-logistics-tracker/truck_builder.html`) and opened via a link button from the "Truck Builder" nav page. |
| `requirements.txt` | `requests`, `pandas`, `geopy`, `streamlit`, `streamlit-autorefresh`, `plotly`, `folium`, `streamlit-folium`. |
| `.streamlit/secrets.toml` | Local secrets file (gitignored) — Airtable token/base/table IDs, Gmail sender credentials for the consolidation email report. |
| `.gitignore` | Excludes `.streamlit/secrets.toml`, `__pycache__/`, `*.pyc`, `coords_cache.json` (an old local cache file, now superseded by storing coordinates directly on the Airtable Shipment record). |

**Working-tree state at time of writing (uncommitted):** `truck_builder_v2.html`
was deleted (825 lines removed — an older/duplicate version of the truck
builder tool cleaned up in favor of `truck_builder.html`), and `app.py` /
`airtable_connection.py` have uncommitted edits (+403/-... in app.py) plus a
new `.streamlit/` directory not yet tracked by git.

## 3. Airtable Base — Tables & Relationships

Base ID and table IDs are stored in `.streamlit/secrets.toml`. Tables (by
purpose, inferred from field usage in the code):

### Shipments (`SHIPMENTS_TABLE`)
Primary entity — one physical shipment of product.
- Fields: `Shipment Number`, `Customer`, `Customer Email`, `Warehouse` (Texas/Florida),
  `Address`, `City`, `State`, `ZIP Code`, `Weight`, `Bundles`, `Elbows`,
  `Dimensions`, `Trailer Type Needed`, `Warehouse Status` (Pending Print / In
  Progress / Ready / Shipped), `Pick Up` (Yes/No), `Requested Delivery Date`,
  `Order Date`, `Coordinates` (cached `"lat,lon"` string, written back by the
  geocoder), and a reverse-link field `Loads`.
- **Links to:** Loads (many-to-one, via reverse link), Pricing/quotes (via
  `Shipments` field on Pricing), Updates Log (via `Shipment` field on Updates Log).

### Loads (`LOADS_TABLE`)
An actual truck/carrier booking that carries one or more Shipments.
- Fields: `Load Number` (from broker), `Carrier` (lookup, array), `Warehouse`
  (lookup rolled up from linked shipments — Airtable auto-names it e.g.
  `"Warehouse (from Linked Shipments)"`), `Trailer Type`, `Total Weight`,
  `Total Bundles`, `Destinations`, `Load Status` (Ready / Scheduled / In
  Transit / Shipped), `ETA Pickup`, `Freight Cost` (lookup), `Sales Value`
  (lookup), `Freight %`, `Linked Shipments` (multipleRecordLinks → Shipments).
- **Links to:** Shipments (one-to-many via `Linked Shipments`).

### Pricing (`PRICING_TABLE`)
Freight quotes from carriers per shipment (or group of shipments).
- Fields: `Q-` (quote number), `Carrier`, `Freight Cost`, `Sales Value`,
  `Freight %`, `Profit $`, `Status` (Pending / Selected / Lost), `Shipments`
  (multipleRecordLinks), `Date`.
- **Links to:** Shipments (many-to-many via `Shipments`).
- A "Selected" quote is what gets turned into a Load via the "New Load" form
  (`app.py` line ~1443), which references `Selected Quote from Pricing`.

### Updates Log (`UPDATES_LOG_TABLE`)
Audit trail / activity log entries.
- Fields: `Update`, `Shipment` (multipleRecordLinks → Shipments), `Linked
  Load` (lookup), `Date/Time`, `Type` (Status Change / Delay / Documentation /
  Communication / Issue-Problem / Billing), `Description`, `Responsible`
  (Warehouse / Logistics / Customer Service / Carrier / Customer), `Attention
  Flag` (boolean).
- **Links to:** Shipments (many-to-one), Loads (lookup).

### Bundle Dimensions (`BUNDLE_DIMENSIONS_TABLE`, default `tblyRsVa2cEQNeWma`)
Reference table of standard pipe-bundle sizes for the Truck Builder tool.
- Fields: `Size`, `SCH` (schedule/pipe spec), `Length (ft)`, `Length (in)`,
  `Width (in)`, `Height (in)`.
- Read-only reference data — not directly linked to Shipments in the code
  shown (likely used by `truck_builder.html`'s logic, or fetched separately —
  worth confirming since `get_bundle_dimensions()` isn't called anywhere in
  `app.py` today per the grep results).

### Relationship summary
```
Pricing (quotes) --Shipments--> Shipments <--Linked Shipments-- Loads
                                     ^
                                     |
                          Updates Log --Shipment-->
```
A Shipment can have many Pricing quotes (only one typically "Selected"), ends
up linked to at most one active Load (code comment notes this assumption
explicitly), and can have many Updates Log entries.

## 4. Python Scripts

### `config.py`
Pulls all secrets/constants from `st.secrets`. No logic — pure configuration.
Constants: `DISTANCIA_MAX_MILLAS=250`, `PESO_MAX_FLATBED=48000`,
`PESO_MAX_STEPDECK=48000`, `PESO_MAX_HOTSHOT=15000`.

### `airtable_connection.py`
Thin Airtable REST API client + field-normalization layer.
- `get_records(table_id, filter_formula=None)` — generic paginated fetch.
- `_resolve_list_field` / `_resolve_scalar` / `_resolve_warehouse` — helpers
  that flatten Airtable's inconsistent field shapes (string / list / dict)
  for lookup and multi-select fields into clean strings.
- `get_active_shipments()` — shipments with status in {Pending Print, In
  Progress, Ready}; resolves linked Load numbers.
- `get_all_shipments()` — all shipments, enriched with Load Number/Carrier/
  Load Status/ETA Pickup by joining against Loads in-memory (avoids N+1 API
  calls).
- `get_shipment_number_map()` — id → Shipment Number lookup, built once and
  passed around to avoid re-fetching Shipments for every other table's join.
- `get_loads(id_to_shpt_number=None, debug=False)` — all loads, with
  Carrier/Warehouse/Freight/Sales resolved from lookup-field arrays and
  Linked Shipments resolved to human-readable shipment numbers.
- `get_pricing(id_to_shpt_number=None)` — all pricing quotes, linked
  shipments resolved.
- `get_updates_log(id_to_shpt_number=None)` — all log entries, linked
  shipment/load resolved.
- `get_bundle_dimensions()` — reference pipe/bundle size table (defined but
  currently unused by `app.py`).
- `update_record(table_id, record_id, fields)` — generic PATCH.

### `consolidation_detector.py`
Geocoding + nearest-neighbor matching engine, runnable standalone or imported
by the Streamlit UI.
- Coordinate caching strategy: coordinates are geocoded via **Nominatim**
  (OpenStreetMap, rate-limited to 1 req/sec) only once per shipment, then
  written back to the Shipment's `Coordinates` field in Airtable itself —
  no local cache file (an earlier `coords_cache.json` approach was replaced
  by this, per `.gitignore` still excluding that filename).
- `_filtrar_elegibles()` — excludes shipments marked `Pick Up = Yes` or with
  no Texas/Florida warehouse.
- `_agrupar_por_warehouse()` — splits eligible shipments into Texas/Florida
  groups; **Texas and Florida shipments are never cross-matched.**
- `_construir_matches()` — for each shipment, finds its top-3 closest other
  shipments (by geodesic distance) in the same warehouse group, within
  `DISTANCIA_MAX_MILLAS` (250 mi), sorted nearest-first.
- `detectar_consolidaciones()` — orchestrates the above, returns
  `{"Texas": [...], "Florida": [...], "excluded": [...]}`.
- `enviar_email_consolidacion()` — formats a plaintext report and sends it via
  Gmail SMTP (`smtp.gmail.com:587`) using the sender credentials in secrets.
- `if __name__ == "__main__":` block — CLI entry point that runs detection,
  prints results, and emails the report. Intended to be run as a scheduled
  job (e.g. cron) separate from the live Streamlit app's on-demand button.

### `app.py`
Single-file Streamlit app (2,082 lines) covering UI, styling, and business
actions. Structure (by section marker):

- **Lines 1–718**: Page config + a large embedded CSS block (custom "warm
  gray" design system — DM Sans font, custom topbar nav styled as buttons,
  badges, metric cards, tables, forms; sidebar hidden in favor of a topbar).
- **Lines 719–866**: Airtable headers/constants, reference option lists
  (`CARRIERS`, `TRAILER_TYPES`, `UPDATE_TYPES`, `RESPONSIBLE_OPTIONS`,
  `WAREHOUSE_OPTIONS`, `PICKUP_OPTIONS`, `US_STATES` — must mirror Airtable's
  single-select choices exactly), helper functions (`badge_html`,
  `fmt_weight`, `fmt_date`, `create_record`, `update_record_api`), and cached
  data-loading functions (`@st.cache_data`) for the Live Map, Dashboard/
  Shipments, and Pricing pages.
- **Lines 868–920**: Topbar navigation — custom-built nav bar (not
  `st.sidebar`) using styled `st.button`s to switch `st.session_state["pagina"]`,
  plus a context-aware "+ New" button that opens the right creation form per
  page (only enabled on Shipments/Loads/Pricing/Updates Log).
- **Lines 921–1004: Dashboard** — 5 metric cards (Pending Print, In Progress,
  Ready, Shipped, Active Loads) + two tables of the 8 most recent active
  Shipments and active Loads.
- **Lines 1005–1381: Shipments** — filterable/searchable table (status pill
  filter, warehouse pill filter, "Pick Up only"/"No load" extra filters, text
  search) with expandable rows. Clicking "More" opens an inline detail panel
  (auto-scrolls into view via a JS snippet) showing Product/Destination/
  Load & Carrier info plus inline **Actions**: update Warehouse Status, add an
  Updates Log entry, add a Pricing quote, and assign to an existing Load. Has
  a "New Shipment" form (triggered by the topbar "+ New" button).
- **Lines 1382–1506: Loads** — filterable list, status update action, and a
  "New Load" creation form that requires selecting a "Selected" quote from
  Pricing (i.e. Loads are meant to originate from a won quote).
- **Lines 1507–1779: Pricing** — summary metrics (Pending/Selected/Lost
  counts, average profit this month), filters (status/warehouse/sort),
  quotes grouped under their linked shipment, and a "New Quote" form.
- **Lines 1780–1881: Updates Log** — filterable log list (by type or
  "Flagged") and a "New Update" form linking to a Shipment (required) and
  optionally a Load.
- **Lines 1882–1999: Consolidations** — "Detect Opportunities" button runs
  `detectar_consolidaciones()` live, shows summary metrics, a warning listing
  excluded shipments with reasons, a filter (All/Texas/Florida/Ready
  only/No load only), and card-based top-3 match display per shipment with
  distance and combined weight.
- **Lines 2000–2077: Live Map** — Folium map (`cartodbpositron` tiles)
  centered on the TX/FL region, showing markers for shipments on "Ready"
  loads, color-coded by warehouse or orange if consolidated (≥2 shipments on
  one load); cached 60s via `_get_live_map_data()`.
- **Lines 2078–2082: Truck Builder** — just a link-out button to the
  standalone `truck_builder.html` hosted on GitHub Pages (not embedded in the
  Streamlit app).

## 5. Streamlit App Pages Summary

| Page | Purpose | Key Interactions |
|---|---|---|
| Dashboard | At-a-glance ops overview | Status metric cards, recent-activity tables |
| Shipments | CRUD + status workflow for shipments | Filter/search, expandable detail, status update, log entry, create quote, assign to load, new shipment form |
| Loads | Manage truck bookings | Filter by status, status update, new load form (from a Selected quote) |
| Pricing | Freight quote management | Filter/sort/search, profit metrics, new quote form |
| Updates Log | Activity/audit trail | Filter by type/flagged, new update form |
| Consolidations | Find truck-sharing opportunities | On-demand detection, distance/weight-based top-3 matches, warehouse filter |
| Live Map | Geographic view of Ready loads | Folium map with consolidated-load highlighting |
| Truck Builder | Visual trailer loading planner | Opens external standalone HTML tool in a new tab |

## 6. Pending Items / Things Worth Following Up

No `TODO`/`FIXME`/`XXX` comments exist in the codebase (grepped — none found).
Notable open items inferred from code state and comments:

- **Uncommitted changes on `master`** at time of writing: `truck_builder_v2.html`
  deleted, `app.py` and `airtable_connection.py` modified, `.streamlit/`
  untracked — should be reviewed and committed (or the user should confirm
  intent) rather than left dangling.
- **`get_bundle_dimensions()`** in `airtable_connection.py` is fully
  implemented but not called anywhere in `app.py` — the Truck Builder page is
  just a link-out to a static HTML file, so this Airtable-backed reference
  data doesn't appear to be wired into it yet. Worth confirming whether
  `truck_builder.html` pulls bundle dimensions itself (e.g., hardcoded) or
  whether this integration is planned but incomplete.
- **Single active Load per shipment assumption**: `get_all_shipments()`
  explicitly notes "a shipment is expected to have at most one active load;
  if linked to more than one, only the first is shown" — a known
  simplification, not a bug, but worth knowing if multi-load shipments ever
  become a real scenario.
- **`coords_cache.json`** is still gitignored even though the code comment
  says coordinates are now cached directly on the Airtable record — the
  gitignore entry is likely just leftover from a prior approach and could be
  removed, though it's harmless to keep.
- **No automated tests** exist in the repo.
- **Consolidation email job** (`consolidation_detector.py __main__`) appears
  designed to run as a separate scheduled process (e.g., cron/Task Scheduler)
  independent of the Streamlit app, but no scheduler config (e.g., GitHub
  Actions workflow, cron file) is present in the repo — likely run externally
  or manually today.
