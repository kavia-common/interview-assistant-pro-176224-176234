import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_smorest import Api
from .config import get_config
from .db import init_db_pool, close_db_pool
from .auth import jwt_required_middleware
from .routes.health import blp as health_blp
from .routes.auth import blp as auth_blp
from .routes.interview import blp as interview_blp
from .routes.question import blp as question_blp
from .routes.feedback import blp as feedback_blp
from .routes.report import blp as report_blp


def create_app():
    """
    Flask application factory.
    Configures CORS, OpenAPI via flask-smorest, DB pool, and registers routes.
    """
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # Load configuration from env
    cfg = get_config()
    app.config.update(
        API_TITLE="Interview Assistant API",
        API_VERSION="v1",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/docs",
        OPENAPI_SWAGGER_UI_PATH="",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
        PROPAGATE_EXCEPTIONS=True,
    )

    # CORS: allow frontend origin and Authorization header
    cors_origins = cfg.CORS_ORIGINS
    CORS(
        app,
        resources={r"/*": {"origins": cors_origins}},
        supports_credentials=True,
        expose_headers=["Authorization"],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # API and tags
    api = Api(app)
    api.spec.components.security_scheme(
        "bearerAuth",
        {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    )
    api.spec.options["info"]["description"] = (
        "API for virtual interview assistant. "
        "All protected routes require Authorization: Bearer <token>."
    )

    # DB pool
    init_db_pool(
        host=cfg.DB_HOST,
        port=cfg.DB_PORT,
        user=cfg.DB_USER,
        password=cfg.DB_PASSWORD,
        db=cfg.DB_NAME,
    )

    # Register blueprints
    api.register_blueprint(health_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(interview_blp)
    api.register_blueprint(question_blp)
    api.register_blueprint(feedback_blp)
    api.register_blueprint(report_blp)

    # JWT protect middleware for protected blueprints (handled per-route via decorator)
    app.before_request(jwt_required_middleware)

    @app.teardown_appcontext
    def _shutdown_session(exception=None):
        # Close pooled connections cleanly when app context ends
        close_db_pool()

    # Simple ping for uptime
    @app.get("/_ping")
    def _ping():
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

    return app


# Keep compatibility with existing run/generate_openapi scripts
app = create_app()
api = next((ext for ext in app.extensions.values() if isinstance(ext, Api)), None)
