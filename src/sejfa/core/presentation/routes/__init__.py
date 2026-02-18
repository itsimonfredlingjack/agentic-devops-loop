"""
Admin and Core routes.
"""
from flask import Blueprint, jsonify, request, Response
from typing import Callable, Any
from functools import wraps
from src.sejfa.core.admin_auth import AdminAuthService
from src.sejfa.newsflash.data.subscriber_repository import SubscriberRepository

def create_admin_blueprint(subscriber_repository: SubscriberRepository) -> Blueprint:
    """Create admin blueprint with dependencies."""
    bp = Blueprint('admin', __name__, url_prefix='/admin')

    @bp.route("/login", methods=["POST"])
    def admin_login():
        """Admin login endpoint."""
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
        """Decorator to require admin authentication token."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            token = None

            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]

            if not AdminAuthService.validate_session_token(token):
                return jsonify({"error": "Unauthorized"}), 401

            return f(*args, **kwargs)
        return decorated_function

    def _subscriber_to_dict(s):
        return {
            "id": s.id,
            "email": s.email,
            "name": s.name,
            "subscribed_date": s.subscribed_at.strftime("%Y-%m-%d"),
            "active": s.active,
        }

    @bp.route("", methods=["GET"])
    @require_admin_token
    def admin_dashboard():
        stats = subscriber_repository.get_statistics()
        return jsonify({"dashboard": "admin", "statistics": stats}), 200

    @bp.route("/statistics", methods=["GET"])
    @require_admin_token
    def admin_statistics():
        stats = subscriber_repository.get_statistics()
        return jsonify(stats), 200

    @bp.route("/subscribers", methods=["GET", "POST"])
    @require_admin_token
    def manage_subscribers():
        if request.method == "GET":
            subscribers = subscriber_repository.list_all()
            return jsonify(
                {"subscribers": [_subscriber_to_dict(s) for s in subscribers]}
            ), 200

        data = request.get_json()
        required_fields = {"email", "name", "subscribed_date"}
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        subscriber = subscriber_repository.create(
            email=data["email"],
            name=data["name"],
        )
        return jsonify(_subscriber_to_dict(subscriber)), 201

    @bp.route("/subscribers/<int:subscriber_id>", methods=["GET", "PUT", "DELETE"])
    @require_admin_token
    def manage_subscriber(subscriber_id: int):
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

    @bp.route("/subscribers/search", methods=["GET"])
    @require_admin_token
    def search_subscribers():
        query = request.args.get("q", "")
        if not query:
            return jsonify({"error": "Missing search query"}), 400

        results = subscriber_repository.search(query)
        return jsonify({"results": [_subscriber_to_dict(s) for s in results]}), 200

    @bp.route("/subscribers/export", methods=["GET"])
    @require_admin_token
    def export_subscribers():
        csv_data = subscriber_repository.export_csv()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=subscribers.csv"},
        )

    return bp
