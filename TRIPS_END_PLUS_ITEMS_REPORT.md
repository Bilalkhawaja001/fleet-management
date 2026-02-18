# TRIPS_END_PLUS_ITEMS_REPORT

Date: 2026-02-18

## What was added

### 1) Trips status options fix
- `TripStatus` still includes and correctly supports:
  - `planned`
  - `assigned`
  - `in_transit`
  - `completed`
- Quick Trip form status dropdown still includes **In Transit** and **Completed** and saves/shows correctly in list.

### 2) New action button: End +
- Added **End +** button in `/trips/` table actions.
- Button enabled only when status is:
  - `in_transit`
  - `assigned`
- No navigation: opens modal popup on same page.

### 3) End + Items modal
- Modal includes:
  - End Date/Time (default now)
  - End Odometer (required)
  - Running KM (auto-calculated, read-only)
  - Notes
- Added **Carrying Items** repeatable table with Add Row:
  - Ownership (required): Personal, Company
  - Company-only required fields:
    - Gatepass No
    - Department
    - Item Description
    - Qty
    - UoM
    - Destination
    - Return Type
  - Personal minimal fields supported:
    - Item Description
    - Qty
    - UoM
    - Destination
    - Notes
  - UoM options:
    - pcs, kg, meter, roll, box, set, litre, bag, bundle, carton, other
  - Return type options:
    - Returnable, Not Returnable, Partial Return, Sample

### 4) Submit behavior
- Added endpoint:
  - `POST /trips/<id>/end-plus`
  - `POST /trips/<id>/end` also mapped to same logic for backward compatibility.
- On submit:
  - validates CSRF
  - validates odometer (`end >= start`)
  - validates item rows with clear row-specific messages
  - stores item rows linked to trip
  - stores optional expense rows
  - marks trip as `completed`
  - saves `end_time`, `end_odometer`, `running_km`
  - mirrors legacy fields (`time_in`, `odometer_end`)
- Returns JSON for modal and triggers page refresh.

## DB changes

### New model/table
- Added model: `TripItem`
- File: `app/models/trip_item.py`
- Fields include:
  - `trip_id`
  - `ownership`
  - `gatepass_no`
  - `department`
  - `item_description`
  - `qty`
  - `uom`
  - `destination`
  - `return_type`
  - `notes`

### Migration
- `migrations/versions/d4aa91be3321_add_trip_items_table.py`

## API/endpoint summary
- `POST /trips/<id>/end-plus` (new)
- `POST /trips/<id>/end` (kept, now same handler)

## CSRF + validation
- Modal form includes CSRF token (`{{ end_form.hidden_tag() }}`).
- All trip end POSTs protected by Flask-WTF CSRF.
- User-facing errors returned clearly, including row number for invalid entries.

## Tests added/updated
- `tests/test_trip_workflow.py`
  - Trip create
  - End+ success with company item save
  - End+ personal item save with minimal required fields
  - Status transition to completed
  - Odometer validation
  - CSRF enforcement

## Verification commands
```bash
flask db upgrade
pytest -q tests/test_trip_workflow.py
pytest -q
```

## Verification result
- `tests/test_trip_workflow.py`: ✅ 6 passed
- Full suite: ✅ 15 passed
