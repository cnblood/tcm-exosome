import sqlite3
import os
from supabase import create_client

def check():
    print("🔍 Comparing Local (SQLite) vs Cloud (Supabase)...")
    
    # 1. 连接本地数据库
    db_path = 'data/tcm_exosome.db'
    if not os.path.exists(db_path):
        print(f"❌ Local database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 2. 连接 Supabase
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    sb = None
    if url and key:
        sb = create_client(url, key)
    else:
        print("⚠️  Supabase env variables not found, skipping cloud check.")

    tables = ['genes', 'mirna', 'exosome_cargo', 'herb_gene_relations']
    
    print(f"\n{'Table Name':<20} | {'Local (SQLite)':<15} | {'Cloud (Supabase)':<15}")
    print("-" * 55)

    for t in tables:
        # 获取本地数量
        try:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            l_count = c.fetchone()[0]
        except Exception:
            l_count = "Table Error"

        # 获取云端数量
        s_count = "N/A"
        if sb:
            try:
                res = sb.table(t).select("count", count="exact").execute()
                s_count = res.count
            except Exception:
                s_count = "Check SQL"

        print(f"{t:<20} | {l_count:<15} | {s_count:<15}")

    conn.close()

if __name__ == "__main__":
    check()