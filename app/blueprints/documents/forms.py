from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import SelectField, StringField, DateField, SubmitField, MultipleFileField, TextAreaField
from wtforms.validators import DataRequired, Optional

from ...models import Trip, VehicleDocType


class VehicleDocumentForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    trip_id = SelectField("Trip", coerce=int, validators=[Optional()])
    doc_type = SelectField(
        "Document Type",
        choices=[(d.value, d.name.title()) for d in VehicleDocType],
        validators=[DataRequired()],
    )
    doc_name = StringField("Doc Name", validators=[Optional()])
    doc_number = StringField("Doc Number", validators=[Optional()])
    issue_date = DateField("Issue Date", validators=[Optional()], format="%Y-%m-%d")
    expiry_date = DateField("Expiry Date", validators=[DataRequired()], format="%Y-%m-%d")
    attachments = MultipleFileField(
        "Attachments",
        validators=[FileAllowed(["pdf", "jpg", "jpeg", "png", "webp"], "Only pdf/jpg/jpeg/png/webp allowed")],
    )
    submit = SubmitField("Save")


class DocumentAttachmentEditForm(FlaskForm):
    display_name = StringField("Display Name", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    trip_id = SelectField("Trip", coerce=int, validators=[Optional()])
    submit = SubmitField("Save")
