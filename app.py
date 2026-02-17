"""
Flask application for Agentic Dev Loop demo.

This is a minimal Flask app used to demonstrate the TDD workflow
and test infrastructure of the project.
"""

import os
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import Flask, Response, jsonify, request
from flask_migrate import Migrate
from flask_socketio import SocketIO

from src.expense_tracker.business.service import ExpenseService
from src.expense_tracker.data.repository import InMemoryExpenseRepository
from src.expense_tracker.presentation.routes import create_expense_blueprint
from src.sejfa.core.admin_auth import AdminAuthService
from src.sejfa.monitor.monitor_routes import (
    create_monitor_blueprint,
    init_socketio_events,
)
from src.sejfa.monitor.monitor_service import MonitorService
from src.sejfa.newsflash.business.subscription_service import SubscriptionService
from src.sejfa.newsflash.data.models import db
from src.sejfa.newsflash.data.subscriber_repository import SubscriberRepository
from src.sejfa.newsflash.presentation.routes import create_newsflash_blueprint

# Global SocketIO instance
socketio = None


def create_app(config: dict | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional configuration overrides.

    Returns:
        Flask: Configured Flask application instance.
    """
    global socketio

    app = Flask(__name__)
    app.secret_key = "dev-secret-key"  # In production, use environment variable

    # Database configuration: DATABASE_URL env var, fallback to SQLite
    default_db_uri = os.environ.get("DATABASE_URL", "sqlite:///newsflash.db")
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", default_db_uri)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    # Apply config overrides
    if config:
        app.config.update(config)

    # Ensure instance directory exists for file-based SQLite
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize SQLAlchemy and Migrate (two-phase pattern)
    db.init_app(app)
    Migrate(app, db)

    # Create tables to ensure DB is usable (safe no-op if tables exist)
    with app.app_context():
        db.create_all()

    # Initialize SocketIO for real-time monitoring
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Initialize monitoring service
    monitor_service = MonitorService()

    # Create and register monitoring blueprint
    monitor_blueprint = create_monitor_blueprint(monitor_service, socketio)
    app.register_blueprint(monitor_blueprint)

    # Initialize SocketIO event handlers
    init_socketio_events()

    # Register News Flash blueprint at root with DI
    subscriber_repository = SubscriberRepository()
    subscription_service = SubscriptionService(repository=subscriber_repository)
    newsflash_blueprint = create_newsflash_blueprint(
        subscription_service=subscription_service
    )
    app.register_blueprint(newsflash_blueprint)

    @app.route("/api")
    def hello():
        """API endpoint returning a greeting.

        Returns:
            Response: JSON response with greeting message.
        """
        return jsonify({"message": "Hello, Agentic Dev Loop!"})

    @app.route("/health")
    def health():
        """Health check endpoint.

        Returns:
            Response: JSON response with health status and timestamp.
        """
        from datetime import datetime

        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

    @app.route("/version")
    def version():
        """Version endpoint showing current git SHA.

        The deployed container sets GIT_SHA at build-time via Docker build-arg.
        Local dev returns "unknown" unless GIT_SHA is provided in the env.
        """
        sha = os.environ.get("GIT_SHA", "").strip() or "unknown"
        return jsonify({"sha": sha})

    # Admin authentication routes
    @app.route("/admin/login", methods=["POST"])
    def admin_login():
        """Admin login endpoint.

        Expects JSON with username and password.

        Returns:
            Response: JSON with token or error message.
        """
        data = request.get_json()

        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "Missing username or password"}), 400

        username = data.get("username")
        password = data.get("password")

        if AdminAuthService.authenticate(username, password):
            token = AdminAuthService.generate_session_token(username)
            return jsonify({"token": token, "username": username}), 200

        return jsonify({"error": "Invalid credentials"}), 401

    def require_admin_token(f: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to require admin authentication token.

        Args:
            f: Route function to decorate.

        Returns:
            Callable: Decorated function.
        """

        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            token = None

            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove "Bearer " prefix

            if not AdminAuthService.validate_session_token(token):
                return jsonify({"error": "Unauthorized"}), 401

            return f(*args, **kwargs)

        return decorated_function

    def _subscriber_to_dict(s):
        """Serialize a Subscriber model to a JSON-safe dict."""
        return {
            "id": s.id,
            "email": s.email,
            "name": s.name,
            "subscribed_date": s.subscribed_at.strftime("%Y-%m-%d"),
            "active": s.active,
        }

    @app.route("/admin", methods=["GET"])
    @require_admin_token
    def admin_dashboard():
        """Admin dashboard endpoint.

        Returns:
            Response: JSON with dashboard data.
        """
        stats = subscriber_repository.get_statistics()
        return jsonify({"dashboard": "admin", "statistics": stats}), 200

    @app.route("/admin/statistics", methods=["GET"])
    @require_admin_token
    def admin_statistics():
        """Admin statistics endpoint.

        Returns:
            Response: JSON with statistics data.
        """
        stats = subscriber_repository.get_statistics()
        return jsonify(stats), 200

    # Subscriber management endpoints
    @app.route("/admin/subscribers", methods=["GET", "POST"])
    @require_admin_token
    def manage_subscribers():
        """Manage subscribers - list or create.

        Returns:
            Response: JSON with subscriber list or created subscriber.
        """
        if request.method == "GET":
            subscribers = subscriber_repository.list_all()
            return jsonify(
                {"subscribers": [_subscriber_to_dict(s) for s in subscribers]}
            ), 200

        # POST - Create new subscriber
        data = request.get_json()
        required_fields = {"email", "name", "subscribed_date"}
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        subscriber = subscriber_repository.create(
            email=data["email"],
            name=data["name"],
        )
        return jsonify(_subscriber_to_dict(subscriber)), 201

    @app.route(
        "/admin/subscribers/<int:subscriber_id>", methods=["GET", "PUT", "DELETE"]
    )
    @require_admin_token
    def manage_subscriber(subscriber_id: int):
        """Manage a specific subscriber - get, update, or delete.

        Args:
            subscriber_id: Subscriber ID.

        Returns:
            Response: JSON with subscriber data or status.
        """
        if request.method == "GET":
            subscriber = subscriber_repository.get_by_id(subscriber_id)
            if not subscriber:
                return jsonify({"error": "Subscriber not found"}), 404
            return jsonify(_subscriber_to_dict(subscriber)), 200

        if request.method == "PUT":
            subscriber = subscriber_repository.get_by_id(subscriber_id)
            if not subscriber:
                return jsonify({"error": "Subscriber not found"}), 404

            data = request.get_json()
            updated = subscriber_repository.update(
                subscriber_id,
                email=data.get("email"),
                name=data.get("name"),
                active=data.get("active"),
            )
            if not updated:
                return jsonify({"error": "Failed to update subscriber"}), 400

            return jsonify(_subscriber_to_dict(updated)), 200

        if request.method == "DELETE":
            deleted = subscriber_repository.delete(subscriber_id)
            if not deleted:
                return jsonify({"error": "Subscriber not found"}), 404
            return jsonify({"message": "Subscriber deleted"}), 204

    @app.route("/admin/subscribers/search", methods=["GET"])
    @require_admin_token
    def search_subscribers():
        """Search subscribers by email or name.

        Returns:
            Response: JSON with search results.
        """
        query = request.args.get("q", "")
        if not query:
            return jsonify({"error": "Missing search query"}), 400

        results = subscriber_repository.search(query)
        return jsonify({"results": [_subscriber_to_dict(s) for s in results]}), 200

    @app.route("/admin/subscribers/export", methods=["GET"])
    @require_admin_token
    def export_subscribers():
        """Export subscribers as CSV.

        Returns:
            Response: CSV file.
        """
        csv_data = subscriber_repository.export_csv()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=subscribers.csv"},
        )

    # Register ExpenseTracker blueprint with DI
    expense_repository = InMemoryExpenseRepository()
    expense_service = ExpenseService(expense_repository)
    expense_blueprint = create_expense_blueprint(expense_service)
    app.register_blueprint(expense_blueprint, url_prefix="/expenses")

    return app


# Create app instance for direct running
app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000, host="0.0.0.0", allow_unsafe_werkzeug=True)
