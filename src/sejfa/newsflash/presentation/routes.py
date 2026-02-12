"""Flask routes for News Flash newsletter."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.sejfa.newsflash.business.subscription_service import (
    SubscriptionService,
    ValidationError,
)


def create_newsflash_blueprint(
    subscription_service: SubscriptionService | None = None,
) -> Blueprint:
    """Create News Flash blueprint.

    Args:
        subscription_service: Optional injected SubscriptionService.
            If None, a default service without repository is created.

    Returns:
        Configured Flask Blueprint for News Flash newsletter.
    """
    service = subscription_service or SubscriptionService()

    bp = Blueprint(
        "newsflash",
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static/newsflash",
    )

    @bp.route("/")
    def index() -> str:
        """Display News Flash landing page with hero section.

        Returns:
            Rendered index template.
        """
        return render_template("newsflash/index.html")

    @bp.route("/subscribe")
    def subscribe() -> str:
        """Display subscription form.

        Returns:
            Rendered subscribe template.
        """
        return render_template("newsflash/subscribe.html")

    @bp.route("/subscribe/confirm", methods=["POST"])
    def subscribe_confirm() -> str:
        """Handle subscription form submission with validation.

        Uses service.subscribe() for the full flow: validate, normalize,
        check duplicates, and persist to database.

        Returns:
            Redirect on success, or subscribe form with error on failure.
        """
        email = request.form.get("email", "")
        name = request.form.get("name", "")

        try:
            result = service.subscribe(email, name)

            flash(f"Tack för din prenumeration, {result['name']}!", "success")
            return redirect(url_for("newsflash.subscribe"))

        except ValidationError as e:
            return render_template(
                "newsflash/subscribe.html",
                error=str(e),
                email_value=email,
                name_value=name,
            )

    return bp
