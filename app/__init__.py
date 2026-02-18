"""
Flask application factory.
"""

import os

from flask import Flask

from app.business.news_service import NewsService
from app.data.repositories.news_repository import InMemoryNewsRepository
from config import config


def create_app(config_name="default"):
    """
    Application factory pattern.

    Args:
        config_name: Configuration to use (development, testing, production)

    Returns:
        Configured Flask application
    """
    # Set template folder to app/presentation/templates
    template_dir = os.path.join(os.path.dirname(__file__), "presentation", "templates")
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(config[config_name])

    # Initialize repository and service
    repository = InMemoryNewsRepository()
    service = NewsService(repository)

    # Store service in app config for access in routes
    app.config["news_service"] = service

    # Register blueprints
    from app.presentation.routes.news_routes import news_bp
    from app.presentation.routes.system_routes import system_bp
    from src.expense_tracker.business.service import ExpenseService
    from src.expense_tracker.data.repository import InMemoryExpenseRepository
    from src.expense_tracker.presentation.routes import create_expense_blueprint
    from src.sejfa.core.presentation.routes import create_admin_blueprint
    from src.sejfa.newsflash.business.subscription_service import SubscriptionService
    from src.sejfa.newsflash.data.models import db
    from src.sejfa.newsflash.data.subscriber_repository import SubscriberRepository
    from src.sejfa.newsflash.presentation.routes import create_newsflash_blueprint

    # Initialize extensions
    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(news_bp, url_prefix="/legacy")
    app.register_blueprint(system_bp)

    # Register News Flash blueprint
    subscriber_repository = SubscriberRepository()
    subscription_service = SubscriptionService(repository=subscriber_repository)
    newsflash_blueprint = create_newsflash_blueprint(
        subscription_service=subscription_service
    )
    app.register_blueprint(newsflash_blueprint)

    # Register Admin Blueprint
    admin_blueprint = create_admin_blueprint(subscriber_repository)
    app.register_blueprint(admin_blueprint)

    # Register Expense Tracker blueprint
    expense_repository = InMemoryExpenseRepository()
    expense_service = ExpenseService(expense_repository)
    expense_blueprint = create_expense_blueprint(expense_service)
    app.register_blueprint(expense_blueprint, url_prefix="/expenses")

    return app
