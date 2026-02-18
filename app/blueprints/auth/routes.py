from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from ...extensions import db, limiter
from ...models import User
from ...audit import log_login
from .forms import LoginForm

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/health")
def health():
    return {"auth": "ok"}


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("fleet.vehicle_list"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.is_active or not user.check_password(form.password.data):
            log_login(form.username.data, success=False, remote_addr=request.remote_addr)
            flash("Invalid credentials", "danger")
        else:
            log_login(user.username, success=True, remote_addr=request.remote_addr)
            login_user(user)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("fleet.vehicle_list"))

    return render_template("auth/login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
