# FUEL_500_FIX_REPORT

Date: 2026-02-18

## 1) Reproduction and traceback

I reproduced the `/fuel/` Internal Server Error using a local repro where legacy trip enum data (`usage_type='school'`) still existed in DB after enum refactor.

### Repro method
- Seeded a Trip/FuelEntry pair
- Force-updated trip `usage_type` to legacy value `school`
- Requested `GET /fuel/`

### Full traceback captured
```text
Traceback (most recent call last):
  File "C:\Users\Bilal\clawd\Fleet-Management\.venv\Lib\site-packages\sqlalchemy\sql\sqltypes.py", line 1709, in _object_value_for_elem
    return self._object_lookup[elem]  # type: ignore[return-value]
KeyError: 'school'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\Bilal\clawd\Fleet-Management\tmp_repro_fuel500.py", line 57, in <module>
    r = client.get('/fuel/')
  ...
  File "C:\Users\Bilal\clawd\Fleet-Management\app\blueprints\fuel\routes.py", line 52, in fuel_list
    pagination = q.order_by(FuelEntry.id.desc()).paginate(
  ...
LookupError: 'school' is not among the defined enum values. Enum name: usagetype. Possible values: OFFICIAL, PERSONAL, SCHOOL_VAN, EDUCATION
```

## 2) Root cause
`/fuel/` list query used `selectinload(FuelEntry.trip)`. For records linked to trips containing legacy enum values (`school`, `educational`, etc.), SQLAlchemy failed enum deserialization and raised `LookupError`, resulting in 500.

## 3) Fix implemented

### A) Fuel list query hardening
- File: `app/blueprints/fuel/routes.py`
- Removed unnecessary eager load of `FuelEntry.trip` in `/fuel/` list query.
  - The fuel list template does not require trip object fields.
  - This prevents `/fuel/` from crashing when stale legacy trip enum values exist.

### B) Data migration alignment
- Existing migration mapping already in place (from previous task):
  - `medical_emergency -> official`
  - `school -> school_van`
  - `educational -> education`
- Reapplied migrations cleanly.

### C) Minor cleanup
- Fixed trip label formatting in fuel form choices for readability (`origin -> destination`).

## 4) Regression test added
- File: `tests/test_fuel_page.py`
- Test: `test_fuel_page_renders_200`
  - Logs in test user
  - Calls `GET /fuel/`
  - Asserts status 200 and page content renders

## 5) Verification commands
```bash
flask db upgrade
pytest -q tests/test_fuel_page.py
pytest -q
```

## 6) Verification results
- `/fuel/` no longer throws 500 in repro scenario after fix.
- Regression test: ✅ pass
- Full suite: ✅ 15 passed
