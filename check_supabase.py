import requests
import os
import json

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# 检查papers表结构
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/papers?limit=1",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    if data:
        print("✅ 成功连接到Supabase")
        print(f"📊 papers表字段: {list(data[0].keys())}")
        print(f"\n第一条数据示例:")
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
    else:
        print("⚠️ papers表为空")
else:
    print(f"❌ 连接失败: {response.status_code}")
    print(response.text)


