import sqlite3
conn = sqlite3.connect(r'data/tcm_exosome.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM papers")
print('papers:', c.fetchone()[0])
c.execute("PRAGMA table_info(papers)")
cols = [r[1] for r in c.fetchall()]
print('columns:', cols)
conn.close()
