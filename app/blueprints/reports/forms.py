from flask_wtf import FlaskForm
from wtforms import DateField, SubmitField, SelectField
from wtforms.validators import Optional

from ...models import FuelPurpose


class DateRangeForm(FlaskForm):
    start_date = DateField("Start date", validators=[Optional()])
    end_date = DateField("End date", validators=[Optional()])
    vehicle_id = SelectField("Vehicle (plate)", coerce=int, validators=[Optional()])
    driver_id = SelectField("Driver", coerce=int, validators=[Optional()])
    fuel_purpose = SelectField(
        "Fuel Purpose",
        choices=[("", "All")] + [(s.value, s.name.replace("_", " ").title()) for s in FuelPurpose],
        validators=[Optional()],
    )
    submit = SubmitField("Apply")
