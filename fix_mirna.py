import sqlite3, os
db = os.environ.get('DB_PATH', 'data/tcm_exosome.db')
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS mirna')
c.execute('''CREATE TABLE mirna (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mirna_id TEXT UNIQUE,
    mirna_acc TEXT,
    sequence TEXT,
    source_organism TEXT,
    target_genes TEXT,
    function_note TEXT,
    is_exosome_cargo INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()
conn.close()
print('mirna table recreated!')
