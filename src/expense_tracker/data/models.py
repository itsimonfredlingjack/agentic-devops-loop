"""Data models for ExpenseTracker."""

from dataclasses import dataclass


@dataclass
class Expense:
    """Represents an expense entry.

    Attributes:
        id: Unique identifier for the expense.
        title: Short description of the expense.
        amount: The cost amount (must be > 0).
        category: Category of expense (Mat, Transport, Boende, Övrigt).
    """

    id: int
    title: str
    amount: float
    category: str
