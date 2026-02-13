from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional


class VehicleForm(FlaskForm):
    plate_no = StringField("Plate No", validators=[DataRequired()])
    make_model = StringField("Make/Model", validators=[DataRequired()])
    year = IntegerField("Year", validators=[Optional()])
    status = StringField("Status", validators=[DataRequired()])
    submit = SubmitField("Save")
