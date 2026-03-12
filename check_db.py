import sqlite3
conn = sqlite3.connect(r'data/tcm_exosome.db')
c = conn.cursor()
for t in ['research_papers','clinical_trials']:
    c.execute(f'SELECT COUNT(*) FROM {t}')
    print(t, ':', c.fetchone()[0])
conn.close()
