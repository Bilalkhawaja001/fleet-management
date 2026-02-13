from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DateTimeLocalField, IntegerField, StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import Optional, NumberRange

from ...models import ItemsOwner, ItemsReturnStatus, TripStatus, UsageType


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


class TripForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[Optional()])
    driver_id = SelectField("Driver", coerce=int, validators=[Optional()])

    # Trip closure fields (can be entered at trip end)
    odometer_start = IntegerField("Start Odometer", validators=[Optional(), NumberRange(min=0)])
    odometer_end = IntegerField("End Odometer", validators=[Optional(), NumberRange(min=0)])
    time_out = DateTimeLocalField("Time Out", validators=[Optional()], format="%Y-%m-%dT%H:%M")
    time_in = DateTimeLocalField("Time In", validators=[Optional()], format="%Y-%m-%dT%H:%M")

    usage_type = SelectField(
        "Usage Type",
        choices=[(s.value, s.name.replace("_", " ").title()) for s in UsageType],
    )
    department = StringField("Department", validators=[Optional()])
    employee_name = StringField("Employee Name", validators=[Optional()])

    origin = StringField("Origin", validators=[Optional()])
    destination_city = SelectField("Destination City", choices=CITIES, validators=[Optional()])
    destination = StringField("Destination", validators=[Optional()])

    status = SelectField(
        "Status",
        choices=[(s.value, s.name.replace("_", " ").title()) for s in TripStatus],
    )

    carrying_items = BooleanField("Carrying Items?", default=False)
    items_owner = SelectField(
        "Items Owner",
        choices=[("", "--"), *[(s.value, s.name.title()) for s in ItemsOwner]],
        validators=[Optional()],
    )
    gatepass_no = StringField("Gatepass No", validators=[Optional()])
    items_reason = StringField("Reason for carrying items", validators=[Optional()])
    items_details = TextAreaField("Items details", validators=[Optional()])

    items_return_status = SelectField(
        "Items Returned Status",
        choices=[("", "--"), *[(s.value, s.name.replace("_", " ").title()) for s in ItemsReturnStatus]],
        validators=[Optional()],
    )
    items_not_returned_reason = TextAreaField("Not returned reason", validators=[Optional()])
    items_expected_return_date = DateField("Expected Return Date", validators=[Optional()], format="%Y-%m-%d")

    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save")
