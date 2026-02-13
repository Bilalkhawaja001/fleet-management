from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Optional

from ...models import IncidentType, IncidentSeverity


class IncidentForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    driver_id = SelectField("Driver", coerce=int, validators=[Optional()])

    incident_no = StringField("Incident No", validators=[DataRequired()])
    incident_dt = DateTimeField("Incident Date/Time", validators=[DataRequired()], format="%Y-%m-%d %H:%M")

    location = StringField("Location", validators=[Optional()])
    incident_type = SelectField(
        "Incident Type",
        choices=[(t.value, t.name.title()) for t in IncidentType],
        validators=[DataRequired()],
    )
    severity = SelectField(
        "Severity",
        choices=[(s.value, s.name.replace('_',' ').title()) for s in IncidentSeverity],
        validators=[DataRequired()],
    )
    description = TextAreaField("Description", validators=[Optional()])

    submit = SubmitField("Save")


class IncidentDecisionForm(FlaskForm):
    decision = SelectField("Decision", choices=[("approve", "Approve"), ("reject", "Reject")], validators=[DataRequired()])
    note = TextAreaField("Note/Reason", validators=[Optional()])
    submit = SubmitField("Submit")
