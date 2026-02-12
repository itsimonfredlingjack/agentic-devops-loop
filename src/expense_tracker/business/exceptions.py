"""Business layer exceptions for ExpenseTracker."""


class ExpenseValidationError(ValueError):
    """Base exception for expense validation errors."""

    pass


class InvalidAmountError(ExpenseValidationError):
    """Raised when expense amount is invalid."""

    pass


class InvalidTitleError(ExpenseValidationError):
    """Raised when expense title is invalid."""

    pass


class InvalidCategoryError(ExpenseValidationError):
    """Raised when expense category is invalid."""

    pass
