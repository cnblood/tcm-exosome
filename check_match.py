import sqlite3
conn = sqlite3.connect('data/tcm_exosome.db')

herbs = [r[0] for r in conn.execute('SELECT name_cn FROM tcm_single_herb LIMIT 20').fetchall()]
hg = [r[0] for r in conn.execute('SELECT DISTINCT herb_name FROM herb_gene_relations').fetchall()]

print('=== ?????? ===')
for h in herbs[:10]: print(' ', h)

print()
print('=== Herb-Gene???? ===')
for h in hg: print(' ', h)
