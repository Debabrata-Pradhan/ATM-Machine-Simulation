"""
database.py
------------
Encapsulates all MySQL connectivity and CRUD operations. Keeping this in its
own module (a lightweight "repository" layer) means the rest of the app never
writes raw SQL directly -- it just calls methods like get_account() or
update_balance().

Requires: mysql-connector-python  (pip install mysql-connector-python)
"""

import hashlib
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error as MySQLError

from exceptions import (
    AccountNotFoundError,
    DatabaseConnectionError,
)


def hash_pin(pin: str) -> str:
    """One-way hash for PINs so raw PINs are never stored or compared directly."""
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


class Database:
    """
    Thin wrapper around a MySQL connection pool-of-one, providing
    CRUD access to the `accounts` and `transactions` tables.
    """

    def __init__(self, host="localhost", user="root", password="", database="atm_system"):
        self._config = dict(host=host, user=user, password=password, database=database)
        self._connection = None

    # ------------------------------------------------------------------ #
    # Connection management
    # ------------------------------------------------------------------ #
    def connect(self):
        try:
            self._connection = mysql.connector.connect(**self._config)
        except MySQLError as exc:
            raise DatabaseConnectionError(f"MySQL connection failed: {exc}") from exc

    def close(self):
        if self._connection and self._connection.is_connected():
            self._connection.close()

    @contextmanager
    def _cursor(self, dictionary=False):
        """Context manager that yields a cursor and commits/rolls back automatically."""
        if not self._connection or not self._connection.is_connected():
            self.connect()
        cursor = self._connection.cursor(dictionary=dictionary)
        try:
            yield cursor
            self._connection.commit()
        except MySQLError as exc:
            self._connection.rollback()
            raise DatabaseConnectionError(f"Database operation failed: {exc}") from exc
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    # CREATE
    # ------------------------------------------------------------------ #
    def create_account(self, account_number, holder_name, pin, initial_balance=0.0):
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO accounts (account_number, holder_name, pin_hash, balance)
                   VALUES (%s, %s, %s, %s)""",
                (account_number, holder_name, hash_pin(pin), initial_balance),
            )

    # ------------------------------------------------------------------ #
    # READ
    # ------------------------------------------------------------------ #
    def get_account(self, account_number):
        with self._cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT * FROM accounts WHERE account_number = %s", (account_number,)
            )
            row = cur.fetchone()
        if row is None:
            raise AccountNotFoundError(account_number)
        return row

    def get_transaction_history(self, account_number, limit=10):
        with self._cursor(dictionary=True) as cur:
            cur.execute(
                """SELECT * FROM transactions
                   WHERE account_number = %s
                   ORDER BY timestamp DESC
                   LIMIT %s""",
                (account_number, limit),
            )
            return cur.fetchall()

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    def update_balance(self, account_number, new_balance):
        with self._cursor() as cur:
            cur.execute(
                "UPDATE accounts SET balance = %s WHERE account_number = %s",
                (new_balance, account_number),
            )

    def record_failed_attempt(self, account_number, attempts, locked):
        with self._cursor() as cur:
            cur.execute(
                """UPDATE accounts
                   SET failed_attempts = %s, is_locked = %s
                   WHERE account_number = %s""",
                (attempts, locked, account_number),
            )

    def reset_failed_attempts(self, account_number):
        self.record_failed_attempt(account_number, 0, False)

    # ------------------------------------------------------------------ #
    # DELETE
    # ------------------------------------------------------------------ #
    def delete_account(self, account_number):
        with self._cursor() as cur:
            cur.execute(
                "DELETE FROM accounts WHERE account_number = %s", (account_number,)
            )

    # ------------------------------------------------------------------ #
    # Transaction logging (append-only, part of CRUD "create")
    # ------------------------------------------------------------------ #
    def log_transaction(self, account_number, transaction_type, amount, balance_after):
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO transactions
                   (account_number, transaction_type, amount, balance_after)
                   VALUES (%s, %s, %s, %s)""",
                (account_number, transaction_type, amount, balance_after),
            )
