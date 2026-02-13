## RBAC

Roles:
- super_admin
- admin
- entry_operator

Rules (current):
- super_admin: full access (including user management)
- admin: all modules allowed; cannot create/manage users
- entry_operator:
  - Vehicles/Drivers: create + view (no edit/delete)
  - Trips: create + view + edit/status update (no delete)
  - Fuel: create + view (append-only; no edit/delete)
  - Maintenance:
    - Preventive schedules: create + view (no edit/delete)
    - Work orders: create + view; update status allowed; no edit/delete
    - Parts: add parts to a work order allowed
