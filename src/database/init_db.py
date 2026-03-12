"""
Database initialization — creates the 5 base tables.
Compatible with both SQLite (local) and PostgreSQL (Supabase).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.connection import get_connection, is_postgres

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Use appropriate serial/autoincrement syntax
    if is_postgres():
        serial = "SERIAL PRIMARY KEY"
        text_pk = "TEXT PRIMARY KEY"
    else:
        serial = "INTEGER PRIMARY KEY AUTOINCREMENT"
        text_pk = "TEXT PRIMARY KEY"

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS research_papers (
            id {serial},
            title TEXT NOT NULL,
            authors TEXT,
            abstract TEXT,
            doi TEXT UNIQUE,
            pmid TEXT UNIQUE,
            source TEXT,
            pub_date TEXT,
            url TEXT,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS clinical_trials (
            id {serial},
            nct_id TEXT UNIQUE,
            title TEXT,
            status TEXT,
            phase TEXT,
            condition TEXT,
            intervention TEXT,
            sponsor TEXT,
            start_date TEXT,
            completion_date TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS herb_target_relations (
            id {serial},
            herb_name TEXT,
            target_gene TEXT,
            relation_type TEXT,
            confidence REAL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS tcm_exosome_relations (
            id {serial},
            subject TEXT,
            predicate TEXT,
            object TEXT,
            confidence REAL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS crawler_logs (
            id {serial},
            source TEXT,
            status TEXT,
            records_found INTEGER,
            records_added INTEGER,
            error_message TEXT,
            run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base schema initialized successfully")

if __name__ == "__main__":
    init_db()
