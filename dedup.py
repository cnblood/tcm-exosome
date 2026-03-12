import sqlite3
conn = sqlite3.connect('data/tcm_exosome.db')
c = conn.cursor()

# ?????????id
c.execute('''
DELETE FROM herb_gene_relations
WHERE id NOT IN (
    SELECT MIN(id) FROM herb_gene_relations
    GROUP BY herb_name, gene_symbol
)
''')
conn.commit()
total = c.execute('SELECT COUNT(*) FROM herb_gene_relations').fetchone()[0]
print('After dedup:', total)
conn.close()
