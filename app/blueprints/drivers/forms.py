from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField
from wtforms.validators import DataRequired, Optional, Length, Regexp


class DriverForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30), Regexp(r"^[0-9+\-() ]*$")])
    license_no = StringField("License No", validators=[Optional(), Length(max=60)])
    license_expiry = DateField("License Expiry", validators=[Optional()], format="%Y-%m-%d")
    status = StringField("Status", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("Save")
