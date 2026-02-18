from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from ...models import User, Role
from ...rbac import role_required
from .forms import UserCreateForm, UserEditForm

bp = Blueprint("users", __name__, url_prefix="/users")


@bp.get("/")
@login_required
@role_required(Role.SUPER_ADMIN)
def user_list():
    users = User.query.order_by(User.id.desc()).all()
    return render_template("users/users_list.html", users=users)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN)
def user_create():
    form = UserCreateForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash("Username already exists", "warning")
        else:
            u = User(username=form.username.data.strip(), role=Role(form.role.data), is_active=form.is_active.data)
            try:
                u.set_password(form.password.data)
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("users/user_form.html", form=form, title="New User")

            db.session.add(u)
            db.session.commit()
            flash("User created", "success")
            return redirect(url_for("users.user_list"))

    return render_template("users/user_form.html", form=form, title="New User")


@bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN)
def user_edit(user_id: int):
    u = db.session.get(User, user_id)
    if not u:
        flash("User not found", "warning")
        return redirect(url_for("users.user_list"))

    form = UserEditForm(obj=u)
    if form.validate_on_submit():
        u.username = form.username.data.strip()
        u.role = Role(form.role.data)
        u.is_active = form.is_active.data
        if form.password.data:
            try:
                u.set_password(form.password.data)
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("users/user_form.html", form=form, title=f"Edit User #{u.id}")
        db.session.commit()
        flash("User updated", "success")
        return redirect(url_for("users.user_list"))

    return render_template("users/user_form.html", form=form, title=f"Edit User #{u.id}")
