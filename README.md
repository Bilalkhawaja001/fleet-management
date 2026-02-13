# Fleet-Management

Flask-based Fleet Management + Maintenance system.

## Modules (MVP)
- Fleet: Vehicles
- People: Drivers
- Trips/Dispatch
- Fuel logs
- Maintenance: preventive schedules + work orders + parts (no inventory mgmt)
- RBAC: Super Admin, Admin, Entry Operator

## Quickstart (dev)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask --app run.py --debug run
```
