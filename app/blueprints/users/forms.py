from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

from ...models import Role


class UserCreateForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    role = SelectField("Role", choices=[(r.value, r.name.replace("_", " ").title()) for r in Role], validators=[DataRequired()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Create")


class UserEditForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("New Password (optional)", validators=[Optional()])
    role = SelectField("Role", choices=[(r.value, r.name.replace("_", " ").title()) for r in Role], validators=[DataRequired()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save")
