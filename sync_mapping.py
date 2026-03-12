import sqlite3, os
from supabase import create_client

conn = sqlite3.connect('data/tcm_exosome.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS herb_name_mapping')
c.execute('''CREATE TABLE herb_name_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_en TEXT UNIQUE,
    name_cn TEXT,
    name_latin TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

mapping = {
    'Astragalus': '黄芪',
    'Curcumin': '姜黄',
    'Ginger': '生姜',
    'Berberine': '黄连',
    'Ginseng': '人参',
    'Resveratrol': '虎杖',
    'Acorus tatarinowii': '石菖蒲',
    'Poria cocos': '茯苓',
}
for en, cn in mapping.items():
    c.execute('INSERT INTO herb_name_mapping (name_en, name_cn) VALUES (?,?)', (en, cn))
conn.commit()

client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
data = [{'name_en': en, 'name_cn': cn} for en, cn in mapping.items()]
client.table('herb_name_mapping').upsert(data, on_conflict='name_en').execute()
print('Synced ' + str(len(data)) + ' mappings')

# 验证关联
rows = conn.execute('''
    SELECT m.name_cn, h.gene_symbol, h.interaction_type, h.mechanism
    FROM herb_gene_relations h
    JOIN herb_name_mapping m ON m.name_en = h.herb_name
    LIMIT 10
''').fetchall()
print()
print('=== 关联查询预览 ===')
for r in rows: print(r)
conn.close()
