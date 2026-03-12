import sqlite3
conn = sqlite3.connect('data/tcm_exosome.db')
rows = conn.execute('SELECT herb_name, gene_symbol, interaction_type FROM herb_gene_relations').fetchall()
for r in rows: print(r)
print('Total:', len(rows))
