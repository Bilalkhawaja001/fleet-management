from flask_wtf import FlaskForm
from wtforms import DateField, SubmitField
from wtforms.validators import Optional


class DateRangeForm(FlaskForm):
    start_date = DateField("Start date", validators=[Optional()])
    end_date = DateField("End date", validators=[Optional()])
    submit = SubmitField("Apply")
