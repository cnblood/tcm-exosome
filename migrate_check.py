import sqlite3, os, requests, json

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY"))

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# 读取本地数据
conn = sqlite3.connect(r'data/tcm_exosome.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT * FROM papers LIMIT 5")
rows = [dict(r) for r in c.fetchall()]
conn.close()

print("Sample row keys:", list(rows[0].keys()))
print("Sample title:", rows[0].get('title','')[:60])

# 检查Supabase是否已有papers表
r = requests.get(f"{SUPABASE_URL}/rest/v1/papers",
    headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
    params={"limit": 1}, timeout=10)
print("Supabase papers status:", r.status_code)


