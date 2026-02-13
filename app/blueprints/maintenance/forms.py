from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, IntegerField, TextAreaField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

from ...models import WorkOrderStatus


class PreventiveScheduleForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    interval_km = IntegerField("Interval (km)", validators=[Optional(), NumberRange(min=0)])
    interval_days = IntegerField("Interval (days)", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Save")


class WorkOrderForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    status = SelectField(
        "Status",
        choices=[(s.value, s.name.replace("_", " ").title()) for s in WorkOrderStatus],
    )
    submit = SubmitField("Save")


class PartForm(FlaskForm):
    name = StringField("Part Name", validators=[DataRequired()])
    qty = DecimalField("Qty", validators=[DataRequired(), NumberRange(min=0)])
    unit_cost = DecimalField("Unit Cost", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Add")
