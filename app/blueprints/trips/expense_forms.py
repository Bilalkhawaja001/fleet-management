from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, StringField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

from ...models import TripExpenseType


class TripExpenseForm(FlaskForm):
    expense_type = SelectField(
        "Expense Type",
        choices=[(t.value, t.name.title()) for t in TripExpenseType],
        validators=[DataRequired()],
    )
    expense_date = DateField("Expense Date", validators=[Optional()], format="%Y-%m-%d")
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0)])
    description = StringField("Description", validators=[Optional()])
    submit = SubmitField("Save")
