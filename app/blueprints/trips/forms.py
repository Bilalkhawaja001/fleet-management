from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import Optional

from ...models import TripStatus


class TripForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[Optional()])
    driver_id = SelectField("Driver", coerce=int, validators=[Optional()])

    origin = StringField("Origin", validators=[Optional()])
    destination = StringField("Destination", validators=[Optional()])

    status = SelectField(
        "Status",
        choices=[(s.value, s.name.replace("_", " ").title()) for s in TripStatus],
    )

    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save")
