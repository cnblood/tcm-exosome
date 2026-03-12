import sqlite3
conn = sqlite3.connect('data/tcm_exosome.db')
rows = conn.execute("""
    SELECT name_cn, pinyin FROM tcm_single_herb 
    WHERE name_latin IS NULL OR name_latin = ''
    ORDER BY name_cn
""").fetchall()
print('Missing:', len(rows))
for r in rows: print(r[0])
conn.close()
