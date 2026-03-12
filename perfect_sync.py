import sqlite3
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
client = create_client(SUPABASE_URL, SUPABASE_KEY)
db_path = 'data/tcm_exosome.db'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("🧹 正在清理云端旧状态...")
for t in ['tcm_single_herb', 'tcm_compound_formula', 'tcm_extracts']:
    try:
        client.table(t).delete().gt('id', 0).execute()
    except:
        pass

# ================= 1. 同步单方药材 =================
rows = conn.execute("SELECT * FROM tcm_single_herb").fetchall()
clean_data = []
for r in rows:
    d = dict(r)
    if not d.get('name_cn'): continue
    clean_data.append({
        'chinese_name': d.get('name_cn'),           # 本地 name_cn -> 云端 chinese_name
        'pinyin': d.get('pinyin'),                  # 本地 pinyin -> 云端 pinyin
        'pinyin_abbr': d.get('pinyin_initial'),     # 本地 pinyin_initial -> 云端 pinyin_abbr
        'category': d.get('category'),
        'latin_name': d.get('name_latin')           # 把本地的空拉丁名也传上去占位
    })
if clean_data:
    for i in range(0, len(clean_data), 500):
        client.table('tcm_single_herb').upsert(clean_data[i:i+500], on_conflict='chinese_name').execute()
    print(f"✅ 单方药材同步成功: 完美上传 {len(clean_data)} 条！")

# ================= 2. 同步复方制剂 =================
rows = conn.execute("SELECT * FROM tcm_compound_formula").fetchall()
clean_data = []
for r in rows:
    d = dict(r)
    if not d.get('name_cn'): continue
    clean_data.append({
        'chinese_name': d.get('name_cn'),
        'pinyin': d.get('pinyin'),
        'pinyin_abbr': d.get('pinyin_initial'),
        'dosage_form': d.get('dosage_form')
    })
if clean_data:
    for i in range(0, len(clean_data), 500):
        client.table('tcm_compound_formula').upsert(clean_data[i:i+500], on_conflict='chinese_name').execute()
    print(f"✅ 复方制剂同步成功: 完美上传 {len(clean_data)} 条！")

# ================= 3. 同步提取物 =================
rows = conn.execute("SELECT * FROM tcm_extracts").fetchall()
clean_data = []
for r in rows:
    d = dict(r)
    if not d.get('name_cn'): continue
    clean_data.append({
        'chinese_name': d.get('name_cn'),
        'pinyin': d.get('pinyin'),
        'pinyin_abbr': d.get('pinyin_initial')
    })
if clean_data:
    for i in range(0, len(clean_data), 500):
        client.table('tcm_extracts').upsert(clean_data[i:i+500], on_conflict='chinese_name').execute()
    print(f"✅ 提取物同步成功: 完美上传 {len(clean_data)} 条！")

conn.close()
print("\n🎉 终极骨架重塑彻底完成！现在不仅有坑位，里面还有真金白银的数据了！")


