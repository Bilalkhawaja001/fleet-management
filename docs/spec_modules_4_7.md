# Fleet Management — Spec (Modules 4–7)

Date: 2026-02-13 (Asia/Karachi)

This document locks requirements for:
- 4️⃣ Vehicle Document Management
- 5️⃣ Maintenance System
- 6️⃣ Accident / Incident Module
- 7️⃣ Reporting

---

## 4️⃣ Vehicle Document Management

### 4.1 Document Types (mandatory per vehicle)
Each vehicle must be tracked for these document types:
- Insurance
- Fitness
- Registration
- Permit
- Tax

### 4.2 Core Rules
- **Only 1 Active record per `doc_type` per vehicle**.
- **Renewal archives previous record** (old Active → Archived/Inactive; new record becomes Active).
- **Attachment is optional**.

### 4.3 Suggested Data Model (minimum)
A `vehicle_documents` record should contain:
- `vehicle_id`
- `doc_type` (enum: Insurance/Fitness/Registration/Permit/Tax)
- `expiry_date` (required)
- `status` (Active | Archived)
- `attachment` (optional: file_id/url)
- audit fields: `created_at`, `updated_at`, `created_by` (if applicable)

### 4.4 Missing Documents
- **Immediately upon vehicle creation**, missing documents are **flagged/shown**.
- “Missing” means: for that vehicle + doc_type, there is **no Active record**.

### 4.5 Expiry Alerts (Popup)
- Alert window starts **30 days before expiry**.
- Popup shown **daily** during the alert window.
- **Throttle**: **max 1 popup per document per day** (vehicle_id + doc_type).
- **Expired** docs are shown as **Critical**.

Popup content:
- Vehicle Number
- Document Name
- Expiry Date
- Days remaining

Implementation note (recommended): keep an `alert_log`/`last_alerted_on` per vehicle+doc_type to enforce throttle.

### 4.6 Acceptance Criteria
- Creating a renewal for same vehicle+doc_type automatically archives previous Active record.
- Dashboard/list distinguishes:
  - Missing docs
  - Expiring in 0–30 days
  - Expired (Critical)
- Same document does not produce more than 1 popup/day.

---

## 5️⃣ Maintenance System (Professional Grade)

### 5.1 Work Order Types
- Preventive
- Breakdown
- Accident

### 5.2 Work Source
- Internal
- External

### 5.3 Required Fields (each Work Order)
- `odometer_in` (required)
- `odometer_out` (required)
- `in_workshop_at` timestamp (required)
- `out_workshop_at` timestamp (required)

### 5.4 Downtime (non-editable, auto-calculated)
- `downtime` must be **auto-calculated** as:
  - `out_workshop_at - in_workshop_at`
- `downtime` must be **read-only** (not manually editable via UI/API).

Validation rules:
- `out_workshop_at >= in_workshop_at`
- `odometer_out >= odometer_in`

### 5.5 Maintenance Categories (Industry Standard)
- Engine & Powertrain
- Transmission & Driveline
- Cooling System
- Electrical
- Brake System
- Suspension & Steering
- Tires & Wheels
- HVAC
- Body & Exterior
- Interior
- Chassis & Frame
- Fluids & Preventive Service
- Safety & Compliance

Each category must include:
- predefined subsystems
- “Other” subsystem option
- If “Other” selected → **Description required**

### 5.6 KPIs Required
- Preventive vs Breakdown **downtime**
- Preventive vs Breakdown **cost**
- Downtime per vehicle
- Overdue PM
- PM Compliance %

### 5.7 Acceptance Criteria
- Downtime cannot be edited (attempts are rejected/ignored).
- Work Order cannot be closed with invalid timestamps/odometer values.
- KPI queries can filter by vehicle/date range/type.

---

## 6️⃣ Accident / Incident Module

### 6.1 Workflow (locked)
- **Reported → Approved (auto) → Closed**

### 6.2 Rules
- **Approval is automatic** (no manual approval gate).
- **Auto-create Work Order** when accident is reported:
  - Work Order Type = **Accident**
- Attachments are **optional**.

### 6.3 Tracking Fields
- Claim No
- Claim Status (Pending/Approved/Rejected/Paid) *(claim status can still be used for insurance workflow even if incident approval is auto)*
- Estimated cost vs Actual cost
- Attachments (optional)

### 6.4 Acceptance Criteria
- Creating an incident auto-creates linked Accident work order.
- Incident defaults to Approved automatically.

---

## 7️⃣ Reporting (Daily Focus)

### 7.1 Daily Dashboard Must Show
- Trips by status
- Vehicles under maintenance
- Fuel pending verification
- Documents expiring/expired
- Maintenance due/overdue
- Accident pending approval *(with auto-approval this should normally be 0; keep tile if needed for future toggle)*

### 7.2 Exports
- Excel
- PDF

### 7.3 Cost Reporting
- Per vehicle
- Preventive vs Breakdown
- **Official only** (exclude personal)

### 7.4 Acceptance Criteria
- Exports match the same filters as on-screen.
- “Official only” views exclude personal trips.

---

## Trip Closure + Reporting Note (from conversation)
This is captured **at Trip End (Trip Closure)**.

### Trip must record (odometer + timestamps)
- `odometer_start` (required)
- `odometer_end` (required)
- `time_out` (required)
- `time_in` (required)

Derived/validation (recommended):
- `distance_km = odometer_end - odometer_start` (**auto-derived** from odometer start/end)
- Validate: `odometer_end >= odometer_start`
- Validate: `time_in >= time_out`

### Expense entry at Trip End (manual) + attachments
Fuel entry requires **liters + amount** (rate optional):
- `fuel_liters` *(mandatory)*
- `fuel_amount` *(mandatory)*
- `fuel_rate` *(optional; if not provided, can be computed as `fuel_amount / fuel_liters` for display/reporting)*

Other expenses:
- `toll_amount`
- `other_amount`

Receipt images upload (optional, multiple):
- `trip_expense_attachments`: `trip_id`, `type` (fuel|toll|other|general), `file_url/file_id`, `uploaded_at`

### Trip-level computed fields
- **Total Expenses** per trip:
  - `total_expenses = fuel_amount + toll_amount + other_amount`
- **Fuel Average (km/L)**:
  - `fuel_avg_km_per_l = distance_km / fuel_liters`

Edge handling (recommended):
- if `fuel_liters` is 0/null → `fuel_avg_km_per_l` blank (avoid divide-by-zero)
