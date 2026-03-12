import sqlite3
import os

db_path = os.environ.get('DB_PATH', 'data/tcm_exosome.db')
print(f"📁 数据库路径: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建 clinical_trials 表
cursor.execute('''
CREATE TABLE IF NOT EXISTS clinical_trials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT UNIQUE,
    title TEXT,
    status TEXT,
    conditions TEXT,
    interventions TEXT,
    phase TEXT,
    study_type TEXT,
    enrollment INTEGER,
    start_date TEXT,
    completion_date TEXT,
    url TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print("✅ clinical_trials 表创建成功")

# 检查表是否创建成功
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clinical_trials'")
if cursor.fetchone():
    print("✅ 表已存在")
    
    # 显示表结构
    cursor.execute("PRAGMA table_info(clinical_trials)")
    columns = cursor.fetchall()
    print("\n📊 表结构:")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")

conn.commit()
conn.close()
