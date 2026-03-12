import sqlite3, os, requests, json

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY"))

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal"
}

conn = sqlite3.connect(r'data/tcm_exosome.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT * FROM papers")
rows = [dict(r) for r in c.fetchall()]
conn.close()

print(f"Total rows to migrate: {len(rows)}")

# 批量插入，每批50条
batch_size = 50
success = 0
for i in range(0, len(rows), batch_size):
    batch = rows[i:i+batch_size]
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/papers",
        headers=headers,
        data=json.dumps(batch),
        timeout=30
    )
    if r.status_code in [200, 201]:
        success += len(batch)
        print(f"[{i+len(batch)}/{len(rows)}] OK")
    else:
        print(f"[{i}] Error {r.status_code}: {r.text[:200]}")

print(f"Done! Migrated {success}/{len(rows)}")


