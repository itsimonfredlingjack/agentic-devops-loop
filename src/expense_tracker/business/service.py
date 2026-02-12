"""Business service for ExpenseTracker.

This module contains pure Python business logic - no Flask dependencies allowed.
"""

from src.expense_tracker.business.exceptions import (
    InvalidAmountError,
    InvalidCategoryError,
    InvalidTitleError,
)
from src.expense_tracker.data.models import Expense
from src.expense_tracker.data.repository import ExpenseRepository

# Valid categories (Swedish)
VALID_CATEGORIES = frozenset({"Mat", "Transport", "Boende", "Övrigt"})


class ExpenseService:
    """Service for managing expenses with business rule validation.

    Uses dependency injection for the repository - no direct storage coupling.
    """

    def __init__(self, repository: ExpenseRepository) -> None:
        """Initialize the service with a repository.

        Args:
            repository: The expense repository to use for storage.
        """
        self._repository = repository

    def add_expense(self, title: str, amount: float, category: str) -> Expense:
        """Add a new expense after validating business rules.

        Args:
            title: Short description of the expense.
            amount: The cost amount.
            category: Category of expense.

        Returns:
            The created expense with assigned ID.

        Raises:
            InvalidAmountError: If amount is not greater than 0.
            InvalidTitleError: If title is empty or whitespace only.
            InvalidCategoryError: If category is not in valid list.
        """
        self._validate_amount(amount)
        self._validate_title(title)
        self._validate_category(category)

        expense = Expense(
            id=0,  # Will be assigned by repository
            title=title,
            amount=amount,
            category=category,
        )
        return self._repository.add(expense)

    def get_all_expenses(self) -> list[Expense]:
        """Get all expenses.

        Returns:
            List of all stored expenses.
        """
        return self._repository.get_all()

    def get_total_amount(self) -> float:
        """Calculate the total of all expense amounts.

        Returns:
            Sum of all expense amounts, or 0.0 if no expenses.
        """
        expenses = self._repository.get_all()
        return sum(expense.amount for expense in expenses)

    def _validate_amount(self, amount: float) -> None:
        """Validate that amount is greater than 0.

        Args:
            amount: The amount to validate.

        Raises:
            InvalidAmountError: If amount is not greater than 0.
        """
        if amount <= 0:
            raise InvalidAmountError(
                "Beloppet måste vara större än 0 (Amount must be greater than 0)"
            )

    def _validate_title(self, title: str) -> None:
        """Validate that title is not empty.

        Args:
            title: The title to validate.

        Raises:
            InvalidTitleError: If title is empty or whitespace only.
        """
        if not title or not title.strip():
            raise InvalidTitleError("Titeln får inte vara tom (Title cannot be empty)")

    def _validate_category(self, category: str) -> None:
        """Validate that category is in the allowed list.

        Args:
            category: The category to validate.

        Raises:
            InvalidCategoryError: If category is not valid.
        """
        if category not in VALID_CATEGORIES:
            valid_list = ", ".join(sorted(VALID_CATEGORIES))
            raise InvalidCategoryError(
                f"Ogiltig kategori: '{category}'. "
                f"Giltiga kategorier är: {valid_list} "
                f"(Invalid category: '{category}')"
            )
