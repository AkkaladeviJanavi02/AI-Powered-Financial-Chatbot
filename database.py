"""
database.py - SQLite Database Layer
Handles all data persistence for transactions, categories, and predictions.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/finbot.db")


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row factory for dict-like access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    """Creates all tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT NOT NULL CHECK(type IN ('expense', 'income')),
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            description TEXT,
            date        TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT NOT NULL UNIQUE,
            monthly_limit REAL NOT NULL,
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            role        TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            message     TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()


# ── Transactions ──────────────────────────────────────────────────────────────

def add_transaction(type_: str, amount: float, category: str,
                    description: str = "", date: str = None) -> int:
    """Inserts a transaction and returns its new ID."""
    date = date or datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (type, amount, category, description, date) "
        "VALUES (?, ?, ?, ?, ?)",
        (type_, amount, category, description, date)
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_all_transactions() -> pd.DataFrame:
    """Returns all transactions as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM transactions ORDER BY date DESC", conn
    )
    conn.close()
    return df


def get_transactions_by_month(year: int, month: int) -> pd.DataFrame:
    """Returns transactions filtered to a specific month."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM transactions WHERE strftime('%Y', date) = ? "
        "AND strftime('%m', date) = ? ORDER BY date DESC",
        conn, params=(str(year), f"{month:02d}")
    )
    conn.close()
    return df


def get_monthly_summary() -> pd.DataFrame:
    """Aggregates income and expense totals grouped by year-month."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            strftime('%Y-%m', date) AS month,
            type,
            SUM(amount) AS total
        FROM transactions
        GROUP BY month, type
        ORDER BY month ASC
    """, conn)
    conn.close()
    return df


def get_category_spending() -> pd.DataFrame:
    """Returns total spending per category (expenses only)."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE type = 'expense'
        GROUP BY category
        ORDER BY total DESC
    """, conn)
    conn.close()
    return df


# ── Budgets ───────────────────────────────────────────────────────────────────

def set_budget(category: str, limit: float):
    """Upserts a monthly budget for a category."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
        "ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit, "
        "updated_at=datetime('now')",
        (category, limit)
    )
    conn.commit()
    conn.close()


def get_budgets() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM budgets", conn)
    conn.close()
    return df


# ── Chat History ──────────────────────────────────────────────────────────────

def save_message(role: str, message: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (role, message) VALUES (?, ?)", (role, message)
    )
    conn.commit()
    conn.close()


def get_chat_history(limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, message FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "message": r["message"]} for r in reversed(rows)]


def clear_chat_history():
    conn = get_connection()
    conn.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()
