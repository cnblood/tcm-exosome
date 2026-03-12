"""
Unified database connection factory.
Automatically uses PostgreSQL (Supabase) if DATABASE_URL is set,
otherwise falls back to SQLite for local development.
"""

import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = os.environ.get("DB_PATH", "data/tcm_exosome.db")

def get_connection():
    """Return a database connection (PostgreSQL or SQLite)."""
    if DATABASE_URL:
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = False
            return conn
        except ImportError:
            raise RuntimeError("psycopg2 not installed. Run: pip install psycopg2-binary")
        except Exception as e:
            raise RuntimeError(f"PostgreSQL connection failed: {e}")
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        return sqlite3.connect(DB_PATH)

def is_postgres():
    return bool(DATABASE_URL)

def placeholder():
    """Return the correct SQL placeholder for the active DB."""
    return "%s" if is_postgres() else "?"

def on_conflict_ignore():
    """Return the correct INSERT ignore syntax."""
    if is_postgres():
        return "ON CONFLICT DO NOTHING"
    return "OR IGNORE"
