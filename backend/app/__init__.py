import os
from flask import Flask, jsonify
from flasgger import Swagger
from .config import config_by_name
from .extensions import db, migrate, jwt, cors, init_celery
from .swagger_spec import SWAGGER_TEMPLATE, SWAGGER_CONFIG


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, supports_credentials=True, origins=app.config['CORS_ORIGINS'])
    init_celery(app)

    Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)

    # Register models so Flask-Migrate picks them up
    from .models import User, Account, Transaction, Category, MCCMapping, Budget, Notification, MonthlyBalance  # noqa: F401

    # Blueprints
    from .api.auth import auth_bp
    from .api.accounts import accounts_bp
    from .api.webhooks import webhooks_bp
    from .api.rates import rates_bp
    from .api.categories import categories_bp
    from .api.transactions import transactions_bp
    from .api.budgets import budgets_bp
    from .api.analytics import analytics_bp
    from .api.balance import balance_bp
    from .api.notifications import notifications_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(rates_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(balance_bp)
    app.register_blueprint(notifications_bp)

    # CLI
    from .seed_mcc import seed_mcc_command
    app.cli.add_command(seed_mcc_command)

    _register_jwt_handlers(jwt)

    return app


def _register_jwt_handlers(jwt_manager):
    @jwt_manager.expired_token_loader
    def expired_token(_jwt_header, _jwt_data):
        return jsonify({'error': 'Token has expired'}), 401

    @jwt_manager.invalid_token_loader
    def invalid_token(reason):
        return jsonify({'error': f'Invalid token: {reason}'}), 422

    @jwt_manager.unauthorized_loader
    def missing_token(reason):
        return jsonify({'error': reason}), 401

    @jwt_manager.needs_fresh_token_loader
    def needs_fresh(_jwt_header, _jwt_data):
        return jsonify({'error': 'Fresh token required'}), 401
