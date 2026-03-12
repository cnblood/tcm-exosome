import sqlite3
conn = sqlite3.connect('data/tcm_exosome.db')
cols = conn.execute("PRAGMA table_info(tcm_single_herb)").fetchall()
for c in cols: print(c)
conn.close()
