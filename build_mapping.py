import sqlite3, os

# 英文->中文映射
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

conn = sqlite3.connect('data/tcm_exosome.db')
c = conn.cursor()

# 建映射表
c.execute('''CREATE TABLE IF NOT EXISTS herb_name_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_en TEXT,
    name_cn TEXT,
    name_latin TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

for en, cn in mapping.items():
    c.execute('INSERT OR IGNORE INTO herb_name_mapping (name_en, name_cn) VALUES (?,?)', (en, cn))

conn.commit()

# 验证
rows = conn.execute('SELECT * FROM herb_name_mapping').fetchall()
for r in rows: print(r)
conn.close()
