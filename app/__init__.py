import logging

from flask import Flask, render_template
from .config import Config
from .extensions import db, migrate, login_manager, csrf, limiter


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # models (ensure imported for migrations)
    from . import models  # noqa: F401

    # cli
    from .cli import register_cli

    register_cli(app)

    # blueprints
    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.fleet.routes import bp as fleet_bp
    from .blueprints.drivers.routes import bp as drivers_bp
    from .blueprints.trips.routes import bp as trips_bp
    from .blueprints.fuel.routes import bp as fuel_bp
    from .blueprints.maintenance.routes import bp as maintenance_bp
    from .blueprints.users.routes import bp as users_bp
    from .blueprints.reports.routes import bp as reports_bp
    from .blueprints.documents.routes import bp as documents_bp
    from .blueprints.incidents.routes import bp as incidents_bp
    from .blueprints.bookings.routes import bp as bookings_bp
    from .blueprints.dashboard.routes import bp as dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(fleet_bp)
    app.register_blueprint(drivers_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(fuel_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(bookings_bp)

    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'")
        return response

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html", title="Access Denied"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html", title="Not Found"), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.exception("Unhandled server error", exc_info=e)
        db.session.rollback()
        return render_template("errors/500.html", title="Server Error"), 500

    return app
