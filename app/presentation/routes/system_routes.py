"""
System routes for health checks and API info.
"""

import os
from datetime import datetime

from flask import Blueprint, jsonify

system_bp = Blueprint("system", __name__)


@system_bp.route("/api")
def hello():
    """API endpoint returning a greeting.

    Returns:
        Response: JSON response with greeting message.
    """
    return jsonify({"message": "Hello, Agentic Dev Loop!"})


@system_bp.route("/health")
def health():
    """Health check endpoint.

    Returns:
        Response: JSON response with health status and timestamp.
    """
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@system_bp.route("/version")
def version():
    """Version endpoint showing current git SHA.

    The deployed container sets GIT_SHA at build-time via Docker build-arg.
    Local dev returns "unknown" unless GIT_SHA is provided in the env.
    """
    sha = os.environ.get("GIT_SHA", "").strip() or "unknown"
    return jsonify({"sha": sha})
