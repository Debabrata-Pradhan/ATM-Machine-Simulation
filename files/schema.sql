-- schema.sql
-- Run this once against your MySQL server to create the database and tables
-- used by the ATM simulation.

CREATE DATABASE IF NOT EXISTS atm_system;
USE atm_system;

CREATE TABLE IF NOT EXISTS accounts (
    account_number  VARCHAR(20)     PRIMARY KEY,
    holder_name     VARCHAR(100)    NOT NULL,
    pin_hash        VARCHAR(64)     NOT NULL,       -- SHA-256 hex digest, never store raw PIN
    balance         DECIMAL(12, 2)  NOT NULL DEFAULT 0.00,
    failed_attempts INT             NOT NULL DEFAULT 0,
    is_locked       BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
    account_number   VARCHAR(20)    NOT NULL,
    transaction_type ENUM('DEPOSIT', 'WITHDRAWAL', 'BALANCE_INQUIRY') NOT NULL,
    amount           DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    balance_after    DECIMAL(12, 2) NOT NULL,
    timestamp        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_account
        FOREIGN KEY (account_number) REFERENCES accounts(account_number)
        ON DELETE CASCADE
);

-- Sample seed data (PIN for both is "1234" — see database.py hash_pin() to
-- generate real hashes; this is illustrative only).
-- INSERT INTO accounts (account_number, holder_name, pin_hash, balance)
-- VALUES ('ACC1001', 'Jane Doe', SHA2('1234', 256), 500.00);
