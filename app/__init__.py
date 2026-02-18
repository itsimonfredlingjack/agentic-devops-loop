"""
Flask application factory.
"""
import os

from flask import Flask

from app.business.news_service import NewsService
from app.data.repositories.news_repository import InMemoryNewsRepository
from config import config


def create_app(config_name='default'):
    """
    Application factory pattern.

    Args:
        config_name: Configuration to use (development, testing, production)

    Returns:
        Configured Flask application
    """
    # Set template folder to app/presentation/templates
    template_dir = os.path.join(os.path.dirname(__file__), 'presentation', 'templates')
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(config[config_name])

    # Initialize repository and service
    repository = InMemoryNewsRepository()
    service = NewsService(repository)

    # Store service in app config for access in routes
    app.config['news_service'] = service

    # Register blueprints
    from app.presentation.routes.news_routes import news_bp
    app.register_blueprint(news_bp)

    return app
