"""Flask Blueprint for ExpenseTracker routes.

This module handles HTTP requests and delegates to the business service.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.expense_tracker.business.exceptions import ExpenseValidationError
from src.expense_tracker.business.service import ExpenseService


def create_expense_blueprint(service: ExpenseService) -> Blueprint:
    """Create a Flask Blueprint for expense tracker routes.

    Uses dependency injection to receive the service instance.

    Args:
        service: The ExpenseService to use for business operations.

    Returns:
        Configured Flask Blueprint.
    """
    bp = Blueprint(
        "expense_tracker",
        __name__,
        template_folder="../templates",
    )

    @bp.route("/")
    def index():
        """List all expenses."""
        expenses = service.get_all_expenses()
        return render_template("expense_tracker/index.html", expenses=expenses)

    @bp.route("/add", methods=["POST"])
    def add_expense():
        """Add a new expense from form data."""
        title = request.form.get("title", "")
        amount_str = request.form.get("amount", "0")
        category = request.form.get("category", "")

        try:
            amount = float(amount_str)
        except ValueError:
            flash("Ogiltigt belopp (Invalid amount)", "error")
            return redirect(url_for("expense_tracker.index"))

        try:
            service.add_expense(title=title, amount=amount, category=category)
            flash("Utgift tillagd! (Expense added)", "success")
        except ExpenseValidationError as e:
            flash(str(e), "error")

        return redirect(url_for("expense_tracker.index"))

    @bp.route("/summary")
    def summary():
        """Show summary with total amount."""
        total = service.get_total_amount()
        return render_template("expense_tracker/summary.html", total=total)

    return bp
