from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional


class BookingForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    employee_name = StringField("Employee Name", validators=[DataRequired()])
    department = StringField("Department", validators=[Optional()])

    start_at = DateTimeLocalField("Start Date/Time", validators=[DataRequired()], format="%Y-%m-%dT%H:%M")
    end_at = DateTimeLocalField("End Date/Time", validators=[Optional()], format="%Y-%m-%dT%H:%M")

    purpose = StringField("Purpose", validators=[Optional()])

    submit = SubmitField("Save")
