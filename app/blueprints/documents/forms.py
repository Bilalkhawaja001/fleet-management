from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional

from ...models import VehicleDocType


class VehicleDocumentForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    doc_type = SelectField(
        "Document Type",
        choices=[(d.value, d.name.title()) for d in VehicleDocType],
        validators=[DataRequired()],
    )
    doc_name = StringField("Doc Name", validators=[Optional()])
    doc_number = StringField("Doc Number", validators=[Optional()])
    issue_date = DateField("Issue Date", validators=[Optional()], format="%Y-%m-%d")
    expiry_date = DateField("Expiry Date", validators=[DataRequired()], format="%Y-%m-%d")
    submit = SubmitField("Save")
