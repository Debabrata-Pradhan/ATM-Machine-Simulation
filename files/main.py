"""
main.py
-------
Console entry point for the ATM simulation. Handles the user-facing menu
loop and input validation; all business logic lives in account.py, and all
persistence lives in database.py.

Run with:  python main.py
"""

from decimal import Decimal

from account import ATM
from database import Database
from exceptions import ATMError

DB_CONFIG = dict(
    host="localhost",
    user="root",
    password="Debabrata@1234",
    database="atm_system",
)


def prompt_amount(action: str) -> str:
    """Keep asking until the user enters something that at least looks numeric."""
    while True:
        raw = input(f"Enter amount to {action}: $").strip()
        try:
            Decimal(raw)
            return raw
        except Exception:
            print("  Please enter a valid number (e.g. 150.00).")


def login_flow(atm: ATM):
    account_number = input("Account number: ").strip()
    pin = input("PIN: ").strip()
    try:
        account = atm.authenticate(account_number, pin)
        print(f"\nWelcome, {account.holder_name}!\n")
        return True
    except ATMError as exc:
        print(f"  Login failed: {exc}")
        return False


def session_menu(atm: ATM):
    menu = """
========= ATM Menu =========
1. Deposit
2. Withdraw
3. Check balance
4. Mini statement (last 10 transactions)
5. Log out
=============================
"""
    while True:
        print(menu)
        choice = input("Select an option (1-5): ").strip()

        try:
            if choice == "1":
                amount = prompt_amount("deposit")
                new_balance = atm.deposit(amount)
                print(f"  Deposit successful. New balance: ${new_balance:.2f}")

            elif choice == "2":
                amount = prompt_amount("withdraw")
                new_balance = atm.withdraw(amount)
                print(f"  Withdrawal successful. New balance: ${new_balance:.2f}")

            elif choice == "3":
                balance = atm.check_balance()
                print(f"  Current balance: ${balance:.2f}")

            elif choice == "4":
                rows = atm.statement()
                if not rows:
                    print("  No transactions yet.")
                for row in rows:
                    print(
                        f"  [{row['timestamp']}] {row['transaction_type']:<16} "
                        f"amount=${row['amount']:.2f}  balance_after=${row['balance_after']:.2f}"
                    )

            elif choice == "5":
                atm.logout()
                print("  Logged out.\n")
                return

            else:
                print("  Invalid option, please choose 1-5.")

        except ATMError as exc:
            # Every domain-specific failure (bad amount, insufficient funds,
            # locked account, etc.) is caught here so the session loop never
            # crashes on a business-rule violation.
            print(f"  Error: {exc}")


def main():
    db = Database(**DB_CONFIG)
    atm = ATM(db)

    print("=== Welcome to PySim Bank ATM ===")
    try:
        while True:
            if login_flow(atm):
                session_menu(atm)

            again = input("Would you like to log in as another user? (y/n): ").strip().lower()
            if again != "y":
                break
    except ATMError as exc:
        # Catches infrastructure-level failures, e.g. the DB is unreachable.
        print(f"A system error occurred: {exc}")
    except KeyboardInterrupt:
        print("\nSession interrupted.")
    finally:
        db.close()
        print("Thank you for using PySim Bank ATM. Goodbye!")


if __name__ == "__main__":
    main()
