from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, IntegerField, StringField, DateField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, NumberRange

from ...models import FuelType


class FuelEntryForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    driver_id = SelectField("Driver", coerce=int, validators=[Optional()])
    trip_id = SelectField("Trip", coerce=int, validators=[Optional()])

    slip_no = StringField("Slip No", validators=[DataRequired()])
    fuel_date = DateField("Fuel Date", validators=[DataRequired()], format="%Y-%m-%d")

    odometer_at_fuel = IntegerField("Odometer", validators=[Optional(), NumberRange(min=0)])
    liters = DecimalField("Liters", validators=[DataRequired(), NumberRange(min=0)])
    rate = DecimalField("Rate", validators=[Optional(), NumberRange(min=0)])
    amount = DecimalField("Amount", validators=[Optional(), NumberRange(min=0)])

    fuel_type = SelectField(
        "Fuel Type",
        choices=[(s.value, s.name.title()) for s in FuelType],
        validators=[DataRequired()],
    )

    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save")
