# PySim Bank — Console ATM Simulation

A console-based ATM simulation built with object-oriented Python and a MySQL
backend for persistent transaction records.

## Features

- **OOP design** — `BankAccount` models account state and validation rules;
  `ATM` is a facade that handles authentication and orchestrates operations.
- **Structured exception handling & input validation** — a custom exception
  hierarchy (`exceptions.py`) covers invalid PINs, invalid amounts,
  insufficient funds, locked accounts, and database failures, so the console
  loop never crashes on bad input or a business-rule violation.
- **MySQL persistence with CRUD** — `database.py` wraps `mysql-connector-python`
  to create accounts, read balances/history, update balances, and delete
  accounts, plus an append-only `transactions` log for every deposit,
  withdrawal, and balance inquiry.
- **PIN security** — PINs are hashed (SHA-256) before storage/comparison;
  accounts lock automatically after 3 failed attempts.

## Project structure

```
atm_simulation/
├── main.py          # console entry point / menu loop
├── account.py        # BankAccount + ATM classes (OOP core)
├── database.py       # MySQL connection + CRUD layer
├── exceptions.py      # custom exception hierarchy
├── schema.sql         # MySQL schema (accounts, transactions)
├── requirements.txt
└── README.md
```

## Setup

1. Install MySQL Server and create the schema:
   ```bash
   mysql -u root -p < schema.sql
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Update the credentials in `DB_CONFIG` at the top of `main.py`.
4. Seed a test account (example, in a MySQL shell):
   ```sql
   INSERT INTO accounts (account_number, holder_name, pin_hash, balance)
   VALUES ('ACC1001', 'Jane Doe', SHA2('1234', 256), 500.00);
   ```
5. Run it:
   ```bash
   python main.py
   ```

## Notes on the Git/Agile workflow bullet

The code itself can't demonstrate collaboration, but this repo is structured
to make that easy to show in practice:
- Small, single-responsibility modules (`account.py`, `database.py`,
  `exceptions.py`) that are easy to review independently in a pull request.
- `schema.sql` kept separate from application code, as you'd version a
  migration.
- Suggested next steps if you want to build out the Git/Agile story further:
  create a GitHub repo, open feature branches per capability (deposit,
  withdrawal, MySQL integration, exception handling), and use PRs + issues to
  simulate sprint-style commits and code review history.
