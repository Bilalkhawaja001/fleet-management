from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, IntegerField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange


class FuelLogForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    liters = DecimalField("Liters", validators=[DataRequired(), NumberRange(min=0)])
    amount = DecimalField("Amount", validators=[Optional(), NumberRange(min=0)])
    odometer_km = IntegerField("Odometer (km)", validators=[Optional(), NumberRange(min=0)])
    vendor = StringField("Vendor", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save")
