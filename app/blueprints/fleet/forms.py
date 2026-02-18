from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional, Length, Regexp, NumberRange


VEHICLE_CATEGORIES = [
    ("General", "General / Standard"),
    ("Ambulance", "Ambulance (Emergency Medical Vehicle)"),
    ("PublicTransport", "Public Transport (Bus/Van/Coaster)"),
    ("SchoolVan", "School Van"),
    ("DeliveryVan", "Delivery Van"),
    ("Pickup", "Pickup Truck"),
    ("Truck", "Truck"),
    ("BoxTruck", "Box Truck"),
    ("Flatbed", "Flatbed Truck"),
    ("DumpTruck", "Dump Truck / Tipper"),
    ("Trailer", "Trailer"),
    ("Refrigerated", "Refrigerated / Cold-chain Vehicle"),
    ("TowTruck", "Tow Truck"),
    ("Construction", "Construction / Heavy Equipment"),
]


class VehicleForm(FlaskForm):
    plate_no = StringField("Plate No", validators=[DataRequired(), Length(min=3, max=20), Regexp(r"^[A-Za-z0-9\- ]+$")])
    make_model = StringField("Make/Model", validators=[DataRequired(), Length(min=2, max=120)])
    year = IntegerField("Year", validators=[Optional(), NumberRange(min=1950, max=2100)])
    category = SelectField("Category", choices=VEHICLE_CATEGORIES, validators=[DataRequired()])
    status = SelectField(
        "Status",
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("maintenance", "Maintenance"),
            ("retired", "Retired"),
        ],
        validators=[DataRequired()],
    )
    current_driver_id = SelectField("Current Driver", coerce=int)
    submit = SubmitField("Save")
