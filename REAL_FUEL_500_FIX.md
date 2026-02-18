# REAL_FUEL_500_FIX

Date: 2026-02-18

## Reproduction (live, local)
Commands used from project root:
```bash
set FLASK_DEBUG=1
flask run
```
Then authenticated request to `/fuel/` was made.

### Browser/network status during failure
- `GET /fuel/` -> **500 Internal Server Error**

### Full terminal traceback (captured)
```text
127.0.0.1 - - [18/Feb/2026 18:45:32] "GET /fuel/ HTTP/1.1" 500 -
Traceback (most recent call last):
  File "...\sqltypes.py", line 1709, in _object_value_for_elem
    return self._object_lookup[elem]
KeyError: 'official'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "...\flask\app.py", line 865, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)
  File "...\flask_login\utils.py", line 290, in decorated_view
    return current_app.ensure_sync(func)(*args, **kwargs)
  File "...\app\blueprints\fuel\routes.py", line 51, in fuel_list
    pagination = q.order_by(FuelEntry.id.desc()).paginate(...)
  ...
LookupError: 'official' is not among the defined enum values. Enum name: fuelpurpose. Possible values: OFFICIAL, PERSONAL, SCHOOL_VAN, EDUCATION
```

## Root cause
`fuel_entries.fuel_purpose` contained lowercase values (`official`, etc.) while SQLAlchemy Enum mapping expected enum-name style values (`OFFICIAL`, ...).
This enum coercion mismatch crashed `/fuel/` query deserialization.

## Fix implemented

### 1) Stabilized schema/type (preferred)
Converted enum-backed fields to **String** for compatibility and resilience with historical data:
- `Trip.usage_type` -> `db.String(32)`
- `FuelEntry.fuel_purpose` -> `db.String(32)`

### 2) Data normalization migrations
Added migration to normalize trip values and convert usage type handling path:
- `migrations/versions/f9c2de11ab44_normalize_trip_usage_type_to_string.py`
  - `school` -> `school_van`
  - `educational/education` -> `education`
  - `medical_emergency` -> `official`
  - uppercase enum-name values normalized to lowercase values

Added migration to normalize fuel purpose values:
- `migrations/versions/a2b4ce778d91_normalize_fuel_purpose_to_string.py`
  - `OFFICIAL/PERSONAL/SCHOOL_VAN/EDUCATION` -> lowercase equivalents
  - `school` -> `school_van`

### 3) Code updates
- Fuel list/filter logic updated for string comparisons.
- Reports fuel-purpose filters/aggregations updated for string values.
- Trip/fuel code paths adjusted to store/read `.value` strings consistently.
- Templates updated where `.value` access was used on now-string fields.

## Regression tests
- Existing fuel regression test retained and passing:
  - `tests/test_fuel_page.py` -> `GET /fuel/` returns 200
- Additional route smoke + report tests pass under updated model.

## Verification
Commands:
```bash
flask db upgrade
pytest -q
```
Result:
- ✅ migrations applied
- ✅ tests passed (`16 passed`)

### Live proof log line (after fix)
```text
127.0.0.1 - - [18/Feb/2026 18:48:41] "GET /fuel/ HTTP/1.1" 200 -
```

### Browser/network status after fix
- `GET /fuel/` -> **200 OK**
