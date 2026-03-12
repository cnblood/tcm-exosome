import sqlite3
import os

db_path = os.environ.get('DB_PATH', 'data/tcm_exosome.db')
print(f"检查数据库: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("\n现有的表:")
for table in tables:
    print(f"  - {table[0]}")
    
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"      {col[1]} ({col[2]})")

conn.close()
