import sqlite3
import os
import pandas as pd

db_path = os.environ.get('DB_PATH', 'data/tcm_exosome.db')
conn = sqlite3.connect(db_path)

print("🔍 验证临床试验数据...\n")

# 检查表是否存在
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clinical_trials'")
if not cursor.fetchone():
    print("❌ clinical_trials 表不存在！")
    exit(1)

# 查询数据
df = pd.read_sql_query("SELECT * FROM clinical_trials", conn)
print(f"✅ clinical_trials 表中有 {len(df)} 条数据")
print(f"✅ 表字段: {', '.join(df.columns.tolist())}")

if len(df) > 0:
    print("\n📊 数据预览:")
    print(df[['nct_id', 'title', 'status', 'conditions', 'phase']].head(10).to_string())
    
    # 统计状态分布
    print("\n📈 状态分布:")
    status_counts = df['status'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # 统计分期分布
    print("\n📈 分期分布:")
    phase_counts = df['phase'].value_counts()
    for phase, count in phase_counts.items():
        print(f"  {phase}: {count}")
else:
    print("⚠️ 表中没有数据")

conn.close()
