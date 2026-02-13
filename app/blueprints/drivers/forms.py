from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired, Optional


class DriverForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    phone = StringField("Phone", validators=[Optional()])
    license_no = StringField("License No", validators=[Optional()])
    license_expiry = DateField("License Expiry", validators=[Optional()], format="%Y-%m-%d")
    status = StringField("Status", validators=[DataRequired()])
    submit = SubmitField("Save")
