# Fleet-Management Security & Code Audit Report

**Audit Date:** 2026-02-17  
**Auditor:** OpenClaw AI Assistant  
**Scope:** Critical + High Severity Findings Only

---

## Executive Summary

### Findings Count

| Severity | Count |
|----------|-------|
| **Critical** | 3 |
| **High** | 8 |
| **Total** | **11** |

### Top 10 Priority Issues

1. **CRITICAL** - Hardcoded SECRET_KEY in .env (FLASK-AUD-001)
2. **CRITICAL** - Missing CSRF protection on POST endpoints (FLASK-AUD-002)
3. **CRITICAL** - No rate limiting on auth endpoints (FLASK-AUD-003)
4. **HIGH** - Missing input validation on user-controlled fields (FLASK-AUD-004)
5. **HIGH** - Session cookies missing Secure/HttpOnly flags (FLASK-AUD-005)
6. **HIGH** - No password complexity requirements (FLASK-AUD-006)
7. **HIGH** - Broad exception handling masking errors (FLASK-AUD-007)
8. **HIGH** - Missing audit logs for sensitive operations (FLASK-AUD-008)
9. **HIGH** - N+1 queries in list views (FLASK-AUD-009)
10. **HIGH** - Missing database constraints for data integrity (FLASK-AUD-010)

---

## CRITICAL Severity Findings

---

### ID: FLASK-AUD-001
**Severity:** Critical  
**Category:** Security - Configuration  
**Title:** Hardcoded SECRET_KEY in .env file  
**Impact:** If .env is committed or leaked, attackers can forge session cookies, bypass authentication, and compromise all user sessions.  
**Evidence:** `.env` contains `SECRET_KEY=change-me` (line 2)  
**Repro:** 
1. Check .env file: `cat .env`
2. SECRET_KEY is a weak default value
3. Same value likely used across deployments

**Fix (Exact):**
```bash
# Generate strong key
python -c "import secrets; print(secrets.token_hex(32))"

# Update .env
SECRET_KEY=<paste-64-char-key-here>
```

```python
# config.py - Add validation
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY or SECRET_KEY == "change-me":
        raise ValueError("SECRET_KEY must be set to a secure random value")
```

**Verification:**
- [ ] SECRET_KEY is 64+ characters
- [ ] .env is in .gitignore
- [ ] Config raises error if SECRET_KEY is default

**Estimated Effort:** 30 minutes

---

### ID: FLASK-AUD-002
**Severity:** Critical  
**Category:** Security - CSRF  
**Title:** Missing CSRF Protection on State-Changing Endpoints  
**Impact:** Attackers can trick authenticated users into performing unwanted actions (delete vehicles, approve incidents, change settings) via CSRF attacks.  
**Evidence:** 
- `auth/routes.py` logout endpoint: `@bp.post("/logout")` - no CSRF token
- `fuel/routes.py` verify/reject endpoints use POST without CSRF
- Form templates may not include `{{ form.hidden_tag() }}`

**Repro:**
1. Create malicious HTML page with auto-submitting form to `/auth/logout` (POST)
2. Victim visits page while logged in
3. Victim is logged out without consent

**Fix (Exact):**
```html
<!-- All form templates must include: -->
<form method="POST">
    {{ form.hidden_tag() }}
    <!-- rest of form -->
</form>
```

```python
# For POST-only routes without forms (logout):
from flask_wtf.csrf import validate_csrf
from flask import request

@bp.post("/logout")
@login_required
def logout():
    validate_csrf(request.form.get('csrf_token') or request.headers.get('X-CSRFToken'))
    logout_user()
    return redirect(url_for("auth.login"))
```

**Verification:**
- [ ] All POST forms include `{{ form.hidden_tag() }}`
- [ ] CSRF_ENABLED = True in config
- [ ] Test CSRF bypass attempts fail

**Estimated Effort:** 2 hours

---

### ID: FLASK-AUD-003
**Severity:** Critical  
**Category:** Security - Authentication  
**Title:** No Rate Limiting on Login Endpoint  
**Impact:** Attackers can perform brute-force password attacks without restriction.  
**Evidence:** `auth/routes.py` login endpoint has no rate limiting  
**Repro:**
1. Send 100 login requests with different passwords in 1 minute
2. No throttling or blocking occurs

**Fix (Exact):**
```bash
# Install flask-limiter
pip install flask-limiter==3.5.0
```

```python
# app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Add rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    
    from . import models
    from .cli import register_cli
    register_cli(app)
    
    # Register blueprints...
    
    return app
```

```python
# app/blueprints/auth/routes.py
from flask_limiter import Limiter
limiter = Limiter()  # Initialized in create_app

@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # Add this decorator
def login():
    if current_user.is_authenticated:
        return redirect(url_for("fleet.vehicle_list"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.is_active or not user.check_password(form.password.data):
            flash("Invalid credentials", "danger")
        else:
            login_user(user)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("fleet.vehicle_list"))

    return render_template("auth/login.html", form=form)
```

**Verification:**
- [ ] 6th login attempt within 1 minute returns 429
- [ ] Rate limit headers present in response

**Estimated Effort:** 1 hour

---

## HIGH Severity Findings

---

### ID: FLASK-AUD-004
**Severity:** High  
**Category:** Security - Input Validation  
**Title:** Missing Input Validation on User-Controlled Fields  
**Impact:** Potential XSS, data corruption, or injection attacks through unvalidated inputs.  
**Evidence:** 
- `fleet/routes.py`: `plate_no` uses `.strip().upper()` but no length/format validation
- `incidents/routes.py`: `incident_no` has no uniqueness or format validation
- `drivers/routes.py`: `phone`, `license_no` have no format validation

**Repro:**
1. Submit vehicle with plate_no = 500 character string
2. Submit driver with phone = SQL injection payload
3. Both accepted without error

**Fix (Exact):**
```python
# app/blueprints/fleet/forms.py
from wtforms.validators import DataRequired, Optional, Regexp, Length

class VehicleForm(FlaskForm):
    plate_no = StringField(
        "Plate No", 
        validators=[
            DataRequired(),
            Length(min=1, max=20, message="Plate number must be 1-20 characters"),
            Regexp(r'^[A-Z0-9\- ]+$', message="Invalid plate format")
        ]
    )
    make_model = StringField(
        "Make/Model", 
        validators=[
            DataRequired(),
            Length(min=1, max=120, message="Make/Model must be 1-120 characters")
        ]
    )
    # ... rest of form
```

```python
# app/blueprints/incidents/forms.py
class IncidentForm(FlaskForm):
    incident_no = StringField(
        "Incident No", 
        validators=[
            DataRequired(),
            Length(min=1, max=50),
            Regexp(r'^[A-Z0-9\-]+$', message="Invalid incident number format")
        ]
    )
```

**Verification:**
- [ ] Long strings rejected with validation error
- [ ] Invalid formats rejected
- [ ] Error messages are user-friendly

**Estimated Effort:** 3 hours

---

### ID: FLASK-AUD-005
**Severity:** High  
**Category:** Security - Session Security  
**Title:** Session Cookies Missing Secure/HttpOnly/SameSite Flags  
**Impact:** Session cookies vulnerable to XSS theft and CSRF attacks.  
**Evidence:** `app/extensions.py` login_manager has no cookie security configuration  
**Repro:**
1. Check response headers for Set-Cookie
2. Flags Secure, HttpOnly, SameSite are missing

**Fix (Exact):**
```python
# app/config.py
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///fleet.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session cookie security
    SESSION_COOKIE_SECURE = True  # Only send over HTTPS (set False for local HTTP dev)
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
```

```python
# app/extensions.py
login_manager.session_protection = 'strong'
```

**Verification:**
- [ ] Set-Cookie header includes Secure, HttpOnly, SameSite
- [ ] Cookies not sent over HTTP (in production)
- [ ] JavaScript cannot access session cookie

**Estimated Effort:** 30 minutes

---

### ID: FLASK-AUD-006
**Severity:** High  
**Category:** Security - Authentication  
**Title:** No Password Complexity Requirements  
**Impact:** Users can set weak passwords (e.g., "123456"), making accounts easy to compromise.  
**Evidence:** `app/models/user.py` set_password() has no validation  
**Repro:**
1. Create user with password "123"
2. User created successfully

**Fix (Exact):**
```python
# app/models/user.py
import re
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    # ... existing code ...
    
    def set_password(self, password: str) -> None:
        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one number")
        
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
```

```python
# app/blueprints/users/routes.py - Handle validation errors
@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN)
def user_create():
    form = UserCreateForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash("Username already exists", "warning")
        else:
            try:
                u = User(username=form.username.data.strip(), role=Role(form.role.data), is_active=form.is_active.data)
                u.set_password(form.password.data)
                db.session.add(u)
                db.session.commit()
                flash("User created", "success")
                return redirect(url_for("users.user_list"))
            except ValueError as e:
                flash(str(e), "danger")
    return render_template("users/user_form.html", form=form, title="New User")
```

**Verification:**
- [ ] Short passwords rejected
- [ ] Simple passwords rejected
- [ ] Strong passwords accepted
- [ ] Error messages shown to user

**Estimated Effort:** 1 hour

---

### ID: FLASK-AUD-007
**Severity:** High  
**Category:** Correctness - Error Handling  
**Title:** Broad Exception Handling Masking Errors  
**Impact:** Errors are silently ignored, making debugging impossible and potentially hiding security issues.  
**Evidence:** 
- `trips/routes.py`: `except Exception: pass` in filter handling (lines 33-36)
- `maintenance/routes.py`: Same pattern (line 23)

**Repro:**
1. Send invalid date format to trips endpoint
2. Exception caught and ignored silently
3. No logging of the error

**Fix (Exact):**
```python
# app/blueprints/trips/routes.py
import logging
logger = logging.getLogger(__name__)

@bp.get("/")
@login_required
def trip_list():
    q = Trip.query

    status = (request.args.get("status") or "").strip()
    if status:
        try:
            q = q.filter(Trip.status == TripStatus(status))
        except ValueError as e:
            logger.warning(f"Invalid status filter: {status}, error: {e}")
            flash("Invalid status filter", "warning")

    day = (request.args.get("date") or "").strip()
    if day:
        try:
            d = date.fromisoformat(day)
            start_dt = datetime.combine(d, time.min)
            end_dt = datetime.combine(d, time.max)
            q = q.filter(Trip.time_out >= start_dt, Trip.time_out <= end_dt)
        except ValueError as e:
            logger.warning(f"Invalid date filter: {day}, error: {e}")
            flash("Invalid date format", "warning")

    trips = q.order_by(Trip.id.desc()).all()
    return render_template(
        "trips/trips_list.html",
        trips=trips,
        filter_status=status,
        filter_date=day,
    )
```

**Verification:**
- [ ] Invalid filters logged
- [ ] Errors visible in application logs
- [ ] User-friendly error messages shown
- [ ] Application doesn't crash on bad input

**Estimated Effort:** 2 hours

---

### ID: FLASK-AUD-008
**Severity:** High  
**Category:** Observability - Audit Logging  
**Title:** Missing Audit Logs for Sensitive Operations  
**Impact:** No trail of who did what, making incident investigation impossible.  
**Evidence:** 
- User creation, deletion not logged
- Vehicle deletion not logged
- Incident approval/rejection not logged with user context
- Fuel verification not logged

**Repro:**
1. Delete a vehicle
2. Check database/logs for audit trail
3. No record of who deleted it or when

**Fix (Exact):**
```python
# app/audit.py (already created - see separate file)
# Usage in routes:

# app/blueprints/fleet/routes.py
from ..audit import log_audit

@bp.post("/vehicles/<int:vehicle_id>/delete")
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN)
def vehicle_delete(vehicle_id: int):
    v = db.session.get(Vehicle, vehicle_id)
    if not v:
        flash("Vehicle not found", "warning")
        return redirect(url_for("fleet.vehicle_list"))
    
    log_audit('DELETE', 'vehicle', vehicle_id, {'plate_no': v.plate_no})
    
    db.session.delete(v)
    db.session.commit()
    flash("Vehicle deleted", "success")
    return redirect(url_for("fleet.vehicle_list"))


# app/blueprints/incidents/routes.py
from ..audit import log_audit

@bp.route("/<int:incident_id>", methods=["GET", "POST"])
@login_required
def incident_detail(incident_id: int):
    inc = db.session.get(Incident, incident_id)
    if not inc:
        flash("Incident not found", "warning")
        return redirect(url_for("incidents.incident_list"))

    decision_form = IncidentDecisionForm()
    can_decide = current_user.role.value in [Role.SUPER_ADMIN.value, Role.ADMIN.value]

    if can_decide and decision_form.validate_on_submit():
        if decision_form.decision.data == "approve":
            inc.status = IncidentStatus.APPROVED
            inc.approver_user_id = current_user.id
            inc.approved_at = datetime.utcnow()
            inc.approval_note = (decision_form.note.data or "").strip() or None
            inc.reject_reason = None
            
            log_audit('APPROVE', 'incident', inc.id, {
                'incident_no': inc.incident_no,
                'type': inc.incident_type.value
            })

            # Auto create Work Order for accident approval
            if inc.incident_type == IncidentType.ACCIDENT:
                wo = WorkOrder(
                    vehicle_id=inc.vehicle_id,
                    wo_type=WorkOrderType.ACCIDENT,
                    work_source=WorkSource.INTERNAL,
                    status=WorkOrderStatus.OPEN,
                    title=f"Accident Incident #{inc.incident_no}",
                    description=inc.description,
                )
                db.session.add(wo)
                log_audit('CREATE', 'work_order', None, {'incident_id': inc.id})

            db.session.commit()
            flash("Incident approved", "success")
        else:
            inc.status = IncidentStatus.REJECTED
            inc.approver_user_id = current_user.id
            inc.approved_at = datetime.utcnow()
            inc.reject_reason = (decision_form.note.data or "").strip() or "Rejected"
            
            log_audit('REJECT', 'incident', inc.id, {
                'incident_no': inc.incident_no,
                'reason': inc.reject_reason
            })
            
            db.session.commit()
            flash("Incident rejected", "success")

        return redirect(url_for("incidents.incident_detail", incident_id=inc.id))

    return render_template("incidents/incident_detail.html", inc=inc, decision_form=decision_form, can_decide=can_decide)
```

**Verification:**
- [ ] Audit logs created for all sensitive operations
- [ ] Logs include user, timestamp, action, entity
- [ ] Logs stored securely and retained

**Estimated Effort:** 4 hours

---

### ID: FLASK-AUD-009
**Severity:** High  
**Category:** Performance - Database  
**Title:** N+1 Queries in List Views  
**Impact:** Poor performance with large datasets, potential timeout on list pages.  
**Evidence:** 
- `fleet/routes.py`: `Vehicle.query.order_by(Vehicle.id.desc()).all()` - no eager loading
- `drivers/routes.py`: Same pattern
- Dashboard queries without optimization

**Repro:**
1. Create 100 vehicles with drivers
2. Load vehicle list page
3. 100+ database queries executed (one per vehicle for driver lookup)

**Fix (Exact):**
```python
# app/blueprints/fleet/routes.py
from sqlalchemy.orm import selectinload

@bp.get("/vehicles")
@login_required
def vehicle_list():
    vehicles = Vehicle.query.options(
        selectinload(Vehicle.current_driver)
    ).order_by(Vehicle.id.desc()).all()
    return render_template("fleet/vehicles_list.html", vehicles=vehicles)


@bp.route("/vehicles/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def vehicle_create():
    form = VehicleForm(status="active", category="General")
    
    # Eager load drivers for dropdown
    drivers = Driver.query.order_by(Driver.name).all()
    form.current_driver_id.choices = [(0, "--")]
    form.current_driver_id.choices += [(d.id, d.name) for d in drivers]

    if form.validate_on_submit():
        # ... existing code ...
```

```python
# app/blueprints/drivers/routes.py
from sqlalchemy.orm import selectinload

@bp.get("/")
@login_required
def driver_list():
    drivers = Driver.query.options(
        selectinload(Driver.current_vehicles)
    ).order_by(Driver.id.desc()).all()
    return render_template("drivers/drivers_list.html", drivers=drivers)
```

**Verification:**
- [ ] Query count reduced to O(1) or O(2)
- [ ] Page load time improved significantly
- [ ] SQL query logging shows optimized queries

**Estimated Effort:** 2 hours

---

### ID: FLASK-AUD-010
**Severity:** High  
**Category:** Correctness - Database  
**Title:** Missing Database Constraints for Data Integrity  
**Impact:** Invalid data can be inserted, leading to data corruption and application errors.  
**Evidence:** 
- No CHECK constraints on status fields
- No foreign key cascade rules defined
- No unique constraints on business keys (relies on app logic)
- No NOT NULL constraints on critical fields

**Repro:**
1. Insert trip with odometer_end < odometer_start directly in DB
2. Insert fuel entry with negative liters
3. Database accepts invalid data

**Fix (Exact):**
```bash
# Create Alembic migration
flask db migrate -m "Add data integrity constraints"
```

```python
# Alembic migration file
"""Add database constraints for data integrity

Revision ID: add_constraints
Revises: previous_revision
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add CHECK constraints
    op.create_check_constraint(
        'ck_fuel_entries_liters_positive',
        'fuel_entries',
        'liters >= 0'
    )
    op.create_check_constraint(
        'ck_fuel_entries_amount_positive',
        'fuel_entries',
        'amount >= 0'
    )
    op.create_check_constraint(
        'ck_trips_odometer_valid',
        'trips',
        'odometer_end IS NULL OR odometer_start IS NULL OR odometer_end >= odometer_start'
    )
    op.create_check_constraint(
        'ck_trips_time_valid',
        'trips',
        'time_in IS NULL OR time_out IS NULL OR time_in >= time_out'
    )
    
    # Add explicit foreign key actions
    op.create_foreign_key(
        'fk_fuel_entries_vehicle',
        'fuel_entries', 'vehicles',
        ['vehicle_id'], ['id'],
        ondelete='RESTRICT'  # Prevent deletion of vehicles with fuel entries
    )
    op.create_foreign_key(
        'fk_trips_vehicle',
        'trips', 'vehicles',
        ['vehicle_id'], ['id'],
        ondelete='RESTRICT'
    )

def downgrade():
    op.drop_constraint('ck_fuel_entries_liters_positive', 'fuel_entries', type_='check')
    op.drop_constraint('ck_fuel_entries_amount_positive', 'fuel_entries', type_='check')
    op.drop_constraint('ck_trips_odometer_valid', 'trips', type_='check')
    op.drop_constraint('ck_trips_time_valid', 'trips', type_='check')
    op.drop_constraint('fk_fuel_entries_vehicle', 'fuel_entries', type_='foreignkey')
    op.drop_constraint('fk_trips_vehicle', 'trips', type_='foreignkey')
```

**Verification:**
- [ ] Invalid data rejected at database level
- [ ] Application errors include constraint violation messages
- [ ] Data integrity maintained even with direct DB access

**Estimated Effort:** 3 hours

---

## Quick Fix Plan

### Day 0 (Critical - Do Immediately)

| # | Issue | Effort | Status |
|---|-------|--------|--------|
| 1 | FLASK-AUD-001: Generate strong SECRET_KEY | 30 min | [ ] |
| 2 | FLASK-AUD-002: Ensure CSRF tokens in all forms | 2 hours | [ ] |
| 3 | FLASK-AUD-003: Add rate limiting to login | 1 hour | [ ] |

**Total Day 0:** ~3.5 hours

### Day 1-2 (High Priority)

| # | Issue | Effort | Status |
|---|-------|--------|--------|
| 4 | FLASK-AUD-004: Add input validation to forms | 3 hours | [ ] |
| 5 | FLASK-AUD-005: Configure secure session cookies | 30 min | [ ] |
| 6 | FLASK-AUD-006: Add password strength validation | 1 hour | [ ] |
| 7 | FLASK-AUD-007: Replace broad exception handling | 2 hours | [ ] |
| 8 | FLASK-AUD-008: Implement audit logging | 4 hours | [ ] |
| 9 | FLASK-AUD-009: Add eager loading to list views | 2 hours | [ ] |
| 10 | FLASK-AUD-010: Add database constraints | 3 hours | [ ] |

**Total Day 1-2:** ~15.5 hours

---

## Security Hardening Baseline

### Required Environment Variables

```bash
# .env (update immediately)
SECRET_KEY=<64-char-random-hex-from-python-secrets>
DATABASE_URL=sqlite:///fleet.db  # Change to PostgreSQL for production
FLASK_ENV=development
FLASK_DEBUG=True  # Set False in production
```

### Security Checklist

- [ ] Strong SECRET_KEY (64+ chars)
- [ ] CSRF tokens in all POST forms
- [ ] Rate limiting on auth endpoints
- [ ] Secure session cookies (Secure, HttpOnly, SameSite)
- [ ] Password complexity validation
- [ ] Input validation on all forms
- [ ] Audit logging enabled for sensitive operations
- [ ] Database constraints for data integrity
- [ ] No broad exception handling

---

## Verification Commands

```bash
# Install security tools
pip install bandit safety pip-audit

# Run security scan
bandit -r app/

# Check for known vulnerabilities
safety check
pip-audit

# Test rate limiting
# Send 6 login requests in 1 minute, 6th should return 429

# Check session cookies
# Inspect Set-Cookie header in browser dev tools
```

---

**End of Critical + High Severity Report**

See `QUICK_FIXES.md` for step-by-step fix instructions.
See `security_audit.json` for machine-readable findings.
