from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Regexp

from ...models import Role


class UserCreateForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80), Regexp(r"^[A-Za-z0-9_.-]+$")])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    role = SelectField("Role", choices=[(r.value, r.name.replace("_", " ").title()) for r in Role], validators=[DataRequired()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Create")


class UserEditForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80), Regexp(r"^[A-Za-z0-9_.-]+$")])
    password = PasswordField("New Password (optional)", validators=[Optional(), Length(min=8, max=128)])
    role = SelectField("Role", choices=[(r.value, r.name.replace("_", " ").title()) for r in Role], validators=[DataRequired()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save")
