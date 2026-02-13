import click

from .extensions import db
from .models import User, Role


def register_cli(app):
    @app.cli.command("create-user")
    @click.option("--username", required=True)
    @click.option("--password", required=True)
    @click.option(
        "--role",
        type=click.Choice([r.value for r in Role], case_sensitive=False),
        default=Role.SUPER_ADMIN.value,
        show_default=True,
    )
    def create_user(username: str, password: str, role: str):
        """Create a user (initial Super Admin etc)."""
        if User.query.filter_by(username=username).first():
            raise click.ClickException("username already exists")
        u = User(username=username, role=Role(role))
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        click.echo(f"created user: {u.username} ({u.role.value})")
