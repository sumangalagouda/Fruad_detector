from flask import Flask
from app.config import Config
from app.extensions import db, migrate, jwt, cors, limiter
from app.routes import (
    auth_bp,
    case_bp,
    statement_bp,
    transaction_bp,
    detector_bp,
    graph_bp,
    ai_bp,
    report_bp,
    audit_bp,
    mcp_bp,
)
from app.utils.responses import api_error
from app.utils.logger import logger


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    limiter.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(case_bp)
    app.register_blueprint(statement_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(detector_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(mcp_bp)

    # Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return api_error("The requested resource was not found.", code="NOT_FOUND", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return api_error("Method not allowed for this route.", code="METHOD_NOT_ALLOWED", status_code=405)

    @app.errorhandler(429)
    def handle_rate_limit(e):
        return api_error("Rate limit exceeded. Please slow down requests.", code="TOO_MANY_REQUESTS", status_code=429)

    @app.errorhandler(500)
    def handle_internal_server_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return api_error("An internal server error occurred.", code="SERVER_ERROR", status_code=500)

    # JWT Error handlers
    @jwt.unauthorized_loader
    def handle_unauthorized(e):
        return api_error("Authentication token missing or invalid.", code="UNAUTHORIZED", status_code=401)

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return api_error("Authentication token has expired.", code="TOKEN_EXPIRED", status_code=401)

    @jwt.invalid_token_loader
    def handle_invalid_token(e):
        return api_error("Invalid authentication token.", code="INVALID_TOKEN", status_code=401)

    # Ensure tables are created in database
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to auto-create database tables: {e}")

    return app
