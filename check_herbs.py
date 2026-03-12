import sqlite3
conn = sqlite3.connect('data/tcm_exosome.db')
rows = conn.execute("""
    SELECT herb_name, COUNT(*) as cnt 
    FROM herb_gene_relations 
    GROUP BY herb_name 
    ORDER BY cnt DESC
""").fetchall()
print(f'Total herbs: {len(rows)}')
for r in rows: print(r)
conn.close()
