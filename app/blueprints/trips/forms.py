from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, IntegerField, StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length

from ...models import TripStatus, UsageType


CITIES = [
    ("Karachi", "Karachi"),
    ("Lahore", "Lahore"),
    ("Islamabad", "Islamabad"),
    ("Rawalpindi", "Rawalpindi"),
    ("Faisalabad", "Faisalabad"),
    ("Multan", "Multan"),
    ("Peshawar", "Peshawar"),
    ("Quetta", "Quetta"),
    ("Hyderabad", "Hyderabad"),
    ("Sukkur", "Sukkur"),
    ("Other", "Other"),
]


DEPARTMENTS = [
    ("Centralized", "Centralized"),
    ("Spinning", "Spinning"),
    ("Weaving", "Weaving"),
]


class TripForm(FlaskForm):
    usage_type = SelectField(
        "Trip Purpose",
        choices=[
            (UsageType.OFFICIAL.value, "Official"),
            (UsageType.PERSONAL.value, "Personal"),
            (UsageType.SCHOOL_VAN.value, "School Van"),
            (UsageType.EDUCATION.value, "Education"),
        ],
        validators=[DataRequired()],
        default=UsageType.OFFICIAL.value,
    )

    department = SelectField("Department", choices=DEPARTMENTS, validators=[DataRequired()])
    employee_name = StringField("Employee Name", validators=[DataRequired(), Length(min=2, max=120)])

    origin = StringField("Origin", validators=[DataRequired(), Length(min=2, max=120)], default="Nooriabad")
    destination_city = SelectField("Destination City", choices=CITIES, validators=[DataRequired()])
    destination = StringField("Destination", validators=[DataRequired(), Length(min=2, max=160)])

    time_out = DateTimeLocalField("Planned Time Out", validators=[DataRequired()], format="%Y-%m-%dT%H:%M")

    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    driver_id = SelectField("Driver", coerce=int, validators=[DataRequired()])
    odometer_start = IntegerField("Start Odometer", validators=[DataRequired(), NumberRange(min=0)])

    notes = TextAreaField("Notes", validators=[Optional(), Length(max=1000)])

    status = SelectField(
        "Status",
        choices=[(s.value, s.name.replace("_", " ").title()) for s in TripStatus],
        default=TripStatus.PLANNED.value,
        validators=[DataRequired()],
    )

    submit = SubmitField("Save Trip")


class EndTripForm(FlaskForm):
    end_time = DateTimeLocalField("End Date/Time", validators=[DataRequired()], format="%Y-%m-%dT%H:%M")
    end_odometer = IntegerField("End Odometer", validators=[DataRequired(), NumberRange(min=0)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("End Trip")

    def set_default_now(self):
        if not self.end_time.data:
            self.end_time.data = datetime.now()
