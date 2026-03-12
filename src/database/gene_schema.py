"""
Gene schema extension — creates 8 genomics tables.
Compatible with both SQLite (local) and PostgreSQL (Supabase).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.connection import get_connection, is_postgres

def extend_gene_schema():
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres():
        serial = "SERIAL PRIMARY KEY"
    else:
        serial = "INTEGER PRIMARY KEY AUTOINCREMENT"

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS genes (
            id {serial},
            gene_symbol TEXT UNIQUE,
            gene_name TEXT,
            ncbi_gene_id TEXT,
            uniprot_id TEXT,
            chromosome TEXT,
            gene_type TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS mirna (
            id {serial},
            mirna_id TEXT UNIQUE,
            mirna_name TEXT,
            sequence TEXT,
            target_genes TEXT,
            is_exosome_cargo BOOLEAN DEFAULT FALSE,
            tcm_herb TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS herb_gene_relations (
            id {serial},
            herb_name TEXT,
            active_compound TEXT,
            gene_symbol TEXT,
            interaction_type TEXT,
            mechanism TEXT,
            confidence_score REAL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS exosome_cargo (
            id {serial},
            cargo_type TEXT,
            cargo_name TEXT,
            tcm_herb TEXT,
            target_gene TEXT,
            target_pathway TEXT,
            biological_effect TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS pathway_enrichment (
            id {serial},
            herb_name TEXT,
            pathway_id TEXT,
            pathway_name TEXT,
            gene_list TEXT,
            enrichment_score REAL,
            p_value REAL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS disease_gene_network (
            id {serial},
            disease_name TEXT,
            gene_symbol TEXT,
            association_type TEXT,
            score REAL,
            tcm_herb TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS network_nodes (
            id {serial},
            node_id TEXT UNIQUE,
            node_type TEXT,
            node_label TEXT,
            degree INTEGER DEFAULT 0,
            betweenness REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS network_edges (
            id {serial},
            source_id TEXT,
            target_id TEXT,
            edge_type TEXT,
            weight REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Gene schema extended successfully")

if __name__ == "__main__":
    extend_gene_schema()
