# Quick Fixes - Day 0/1 Priority

## CRITICAL Fixes (Do Today)

### 1. Generate Strong SECRET_KEY

```bash
# Run this to generate a new key
python -c "import secrets; print(secrets.token_hex(32))"
```

Then update `.env`:
```bash
SECRET_KEY=<paste-generated-key-here>
```

### 2. Add CSRF Protection to Templates

All form templates must include:
```html
<form method="POST">
    {{ form.hidden_tag() }}
    <!-- rest of form fields -->
</form>
```

Check these templates:
- `templates/auth/login.html`
- `templates/fleet/vehicle_form.html`
- `templates/drivers/driver_form.html`
- `templates/trips/trip_form.html`
- `templates/fuel/fuel_form.html`
- `templates/incidents/incident_form.html`
- `templates/maintenance/wo_form.html`
- `templates/bookings/booking_form.html`
- `templates/documents/doc_form.html`
- `templates/users/user_form.html`

### 3. Add Rate Limiting

Install flask-limiter:
```bash
pip install flask-limiter==3.5.0
```

Update `app/__init__.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # ... existing init ...
    
    # Add rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    
    # ... rest of init ...
    return app
```

Update `app/blueprints/auth/routes.py`:
```python
from flask_limiter import Limiter
limiter = Limiter()  # Will be initialized in create_app

@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    # ... existing code ...
```

## HIGH Priority Fixes (Do Tomorrow)

### 4. Add Input Validation to Forms

Update `app/blueprints/fleet/forms.py`:
```python
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
    # ... rest of fields
```

### 5. Configure Secure Session Cookies

Update `app/config.py`:
```python
class Config:
    # ... existing config ...
    
    # Session cookie security
    SESSION_COOKIE_SECURE = True  # Set False for local HTTP dev
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
```

### 6. Add Password Validation

Update `app/models/user.py`:
```python
import re

class User(UserMixin, db.Model):
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

### 7. Fix Broad Exception Handling

Update `app/blueprints/trips/routes.py`:
```python
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

    # ... rest of code
```

### 8. Add Audit Logging

Already created `app/audit.py`. Now use it in routes:

Update `app/blueprints/fleet/routes.py`:
```python
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
```

### 9. Fix N+1 Queries

Update `app/blueprints/fleet/routes.py`:
```python
from sqlalchemy.orm import selectinload

@bp.get("/vehicles")
@login_required
def vehicle_list():
    vehicles = Vehicle.query.options(
        selectinload(Vehicle.current_driver)
    ).order_by(Vehicle.id.desc()).all()
    return render_template("fleet/vehicles_list.html", vehicles=vehicles)
```

### 10. Add Database Constraints (Migration)

Create Alembic migration:
```bash
flask db migrate -m "Add data integrity constraints"
```

Edit the migration file:
```python
def upgrade():
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
```

## Verification Checklist

After applying fixes:

- [ ] Generate and set strong SECRET_KEY
- [ ] Test login rate limiting (6th attempt should fail)
- [ ] Verify CSRF tokens in all forms
- [ ] Test password validation (weak passwords rejected)
- [ ] Check session cookies have Secure/HttpOnly flags
- [ ] Verify audit logs are created for CRUD operations
- [ ] Test N+1 fix (query count should be 1-2, not N+1)
- [ ] Run `bandit -r app/` to verify security improvements
- [ ] Run `pip-audit` to check for vulnerabilities

## Estimated Time

- Critical fixes: 2-3 hours
- High priority fixes: 4-6 hours
- Total Day 0/1: 6-9 hours

## Next Steps

After completing these fixes, move to Moderate priority items from the full audit report.
