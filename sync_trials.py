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
    # 1. 连接刚刚写入数据的本地数据库
    conn = sqlite3.connect("data/tcm_exosome.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM clinical_trials").fetchall()
    
    # 2. 清洗数据准备上传
    data = [{k: v for k, v in dict(row).items() if k != "id" and v is not None} for row in rows]
    
    # 3. 推送到 Supabase 云端
    res = requests.post(f"{SUPABASE_URL}/rest/v1/clinical_trials", headers=HEADERS, json=data)
    
    if res.status_code in [200, 201, 204]:
        print(f"✅ 完美！成功将 {len(data)} 条临床试验数据推送到 Supabase 云端！")
    else:
        print(f"❌ 上传报错: {res.status_code} - {res.text}")
        
except Exception as e:
    print(f"发生错误: {e}")


