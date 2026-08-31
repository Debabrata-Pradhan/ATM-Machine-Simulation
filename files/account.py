"""
account.py
----------
Core object-oriented domain model for the ATM simulation.

  BankAccount  -- represents a single account, backed by the database.
                  Owns validation logic for deposits/withdrawals.
  ATM          -- orchestrates authentication and delegates operations
                  to a BankAccount, logging every transaction.

Separating "data + validation rules" (BankAccount) from "user-facing flow"
(ATM) keeps each class focused on one responsibility.
"""

from decimal import Decimal, InvalidOperation

from database import Database, hash_pin
from exceptions import (
    AccountLockedError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidPinError,
)

MAX_FAILED_ATTEMPTS = 3


class BankAccount:
    """In-memory representation of an account row, with business rules."""

    def __init__(self, account_number, holder_name, balance, failed_attempts=0, is_locked=False):
        self.account_number = account_number
        self.holder_name = holder_name
        self.balance = Decimal(str(balance))
        self.failed_attempts = failed_attempts
        self.is_locked = bool(is_locked)

    @classmethod
    def from_row(cls, row: dict):
        """Build a BankAccount from a database row (dict from a dictionary cursor)."""
        return cls(
            account_number=row["account_number"],
            holder_name=row["holder_name"],
            balance=row["balance"],
            failed_attempts=row["failed_attempts"],
            is_locked=row["is_locked"],
        )

    @staticmethod
    def _validate_amount(amount) -> Decimal:
        """Shared input validation for deposit/withdraw amounts."""
        try:
            value = Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError):
            raise InvalidAmountError("Amount must be a valid number.")
        if value <= 0:
            raise InvalidAmountError("Amount must be greater than zero.")
        # Guard against absurd/garbage input (e.g. more than 2 decimal places is fine,
        # but disallow unreasonably large single transactions).
        if value > Decimal("1000000"):
            raise InvalidAmountError("Amount exceeds the maximum allowed per transaction.")
        return value

    def deposit(self, amount) -> Decimal:
        value = self._validate_amount(amount)
        self.balance += value
        return self.balance

    def withdraw(self, amount) -> Decimal:
        value = self._validate_amount(amount)
        if value > self.balance:
            raise InsufficientFundsError(float(self.balance), float(value))
        self.balance -= value
        return self.balance

    def __repr__(self):
        return f"<BankAccount {self.account_number} balance={self.balance}>"


class ATM:
    """
    Facade the console UI talks to. Handles PIN authentication (with lockout
    after repeated failures) and wraps every operation with transaction
    logging to MySQL.
    """

    def __init__(self, db: Database):
        self.db = db
        self.current_account: BankAccount | None = None

    # ------------------------------------------------------------------ #
    # Authentication
    # ------------------------------------------------------------------ #
    def authenticate(self, account_number: str, pin: str) -> BankAccount:
        row = self.db.get_account(account_number)  # raises AccountNotFoundError if missing

        if row["is_locked"]:
            raise AccountLockedError(account_number)

        if row["pin_hash"] != hash_pin(pin):
            attempts = row["failed_attempts"] + 1
            locked = attempts >= MAX_FAILED_ATTEMPTS
            self.db.record_failed_attempt(account_number, attempts, locked)
            if locked:
                raise AccountLockedError(account_number)
            raise InvalidPinError(
                f"Invalid PIN. {MAX_FAILED_ATTEMPTS - attempts} attempt(s) remaining."
            )

        # Success: reset the failure counter and cache the authenticated account.
        self.db.reset_failed_attempts(account_number)
        self.current_account = BankAccount.from_row(row)
        return self.current_account

    # ------------------------------------------------------------------ #
    # Core operations -- each persists the new balance and logs a transaction
    # ------------------------------------------------------------------ #
    def deposit(self, amount) -> Decimal:
        account = self._require_session()
        new_balance = account.deposit(amount)
        self.db.update_balance(account.account_number, new_balance)
        self.db.log_transaction(account.account_number, "DEPOSIT", amount, new_balance)
        return new_balance

    def withdraw(self, amount) -> Decimal:
        account = self._require_session()
        new_balance = account.withdraw(amount)  # raises InsufficientFundsError as needed
        self.db.update_balance(account.account_number, new_balance)
        self.db.log_transaction(account.account_number, "WITHDRAWAL", amount, new_balance)
        return new_balance

    def check_balance(self) -> Decimal:
        account = self._require_session()
        self.db.log_transaction(account.account_number, "BALANCE_INQUIRY", 0, account.balance)
        return account.balance

    def statement(self, limit=10):
        account = self._require_session()
        return self.db.get_transaction_history(account.account_number, limit)

    def logout(self):
        self.current_account = None

    # ------------------------------------------------------------------ #
    def _require_session(self) -> BankAccount:
        if self.current_account is None:
            raise InvalidPinError("No authenticated session. Please log in first.")
        return self.current_account
