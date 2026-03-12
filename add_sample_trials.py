import sqlite3
import os

db_path = os.environ.get('DB_PATH', 'data/tcm_exosome.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 添加一些测试临床试验数据
sample_trials = [
    ('NCT001', 'Ginseng for Cancer-Related Fatigue', 'Completed', 'Cancer', 'Ginseng extract'),
    ('NCT002', 'Astragalus for Immune Function', 'Recruiting', 'Immunology', 'Astragalus membranaceus'),
    ('NCT003', 'Curcumin for Inflammation', 'Active', 'Inflammation', 'Curcuma longa'),
]

for trial in sample_trials:
    cursor.execute('''
    INSERT OR IGNORE INTO clinical_trials (nct_id, title, status, conditions, interventions)
    VALUES (?, ?, ?, ?, ?)
    ''', trial)

conn.commit()
conn.close()
print("Added sample clinical trials")
