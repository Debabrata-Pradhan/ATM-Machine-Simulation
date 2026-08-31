"""
exceptions.py
--------------
Custom exception hierarchy used throughout the ATM system.

Having dedicated exception types (instead of generic Exception/ValueError
everywhere) lets the calling code catch and handle specific failure modes
differently, and makes error messages consistent and predictable.
"""


class ATMError(Exception):
    """Base class for all ATM-related exceptions."""
    pass


class InvalidPinError(ATMError):
    """Raised when a PIN is malformed or does not match the account on file."""
    def __init__(self, message="Invalid PIN. Please try again."):
        super().__init__(message)


class AccountNotFoundError(ATMError):
    """Raised when an account number does not exist in the database."""
    def __init__(self, account_number):
        super().__init__(f"Account '{account_number}' was not found.")
        self.account_number = account_number


class InsufficientFundsError(ATMError):
    """Raised when a withdrawal exceeds the available balance."""
    def __init__(self, balance, requested):
        super().__init__(
            f"Insufficient funds: balance is {balance:.2f}, "
            f"requested {requested:.2f}."
        )
        self.balance = balance
        self.requested = requested


class InvalidAmountError(ATMError):
    """Raised when a deposit/withdrawal amount fails validation."""
    def __init__(self, message="Amount must be a positive number."):
        super().__init__(message)


class DatabaseConnectionError(ATMError):
    """Raised when the MySQL connection cannot be established or is lost."""
    def __init__(self, message="Could not connect to the database."):
        super().__init__(message)


class AccountLockedError(ATMError):
    """Raised when too many failed PIN attempts lock the account."""
    def __init__(self, account_number):
        super().__init__(
            f"Account '{account_number}' is locked due to too many failed PIN attempts."
        )
        self.account_number = account_number
