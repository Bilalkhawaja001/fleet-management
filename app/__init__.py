from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

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

    return app
