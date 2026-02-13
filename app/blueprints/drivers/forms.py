from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Optional


class DriverForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    phone = StringField("Phone", validators=[Optional()])
    license_no = StringField("License No", validators=[Optional()])
    status = StringField("Status", validators=[DataRequired()])
    submit = SubmitField("Save")
