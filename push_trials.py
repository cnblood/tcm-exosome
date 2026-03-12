import sqlite3
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

try:
    # 1. 从本地数据库读取临床试验数据
    conn = sqlite3.connect("data/tcm_exosome.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM clinical_trials").fetchall()
    
    if rows:
        print(f"📦 发现本地临床试验数据 {len(rows)} 条，正在上传到云端...")
        
        # 2. 清洗数据（去掉自增的 id，防止主键冲突）
        data = [{k: v for k, v in dict(row).items() if k != "id"} for row in rows]
        
        # 3. 上传到 Supabase
        res = requests.post(f"{SUPABASE_URL}/rest/v1/clinical_trials", headers=HEADERS, json=data)
        
        if res.status_code in [200, 201]:
            print(f"✅ 成功同步到 Supabase！现在去刷新网页吧！")
        else:
            print(f"❌ 上传报错: {res.status_code} - {res.text}")
    else:
        print("⚠️ 本地 SQLite 里也没有找到 clinical_trials 数据。需要重新运行临床爬虫。")
        
except Exception as e:
    print("错误:", e)


