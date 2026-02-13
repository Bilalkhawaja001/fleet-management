from flask_wtf import FlaskForm
from wtforms import DateField, SubmitField, SelectField
from wtforms.validators import Optional


class DateRangeForm(FlaskForm):
    start_date = DateField("Start date", validators=[Optional()])
    end_date = DateField("End date", validators=[Optional()])
    vehicle_id = SelectField("Vehicle (plate)", coerce=int, validators=[Optional()])
    submit = SubmitField("Apply")
