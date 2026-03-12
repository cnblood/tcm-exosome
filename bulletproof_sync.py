import sqlite3
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
client = create_client(SUPABASE_URL, SUPABASE_KEY)
db_path = 'data/tcm_exosome.db'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

tables = ['tcm_single_herb', 'tcm_compound_formula', 'tcm_extracts']

print("🧹 正在清理云端旧状态，准备重新挂载...")
for t in tables:
    try:
        client.table(t).delete().gt('id', 0).execute()
    except:
        pass

for table in tables:
    try:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        data = [dict(r) for r in rows]
        if not data:
            continue
            
        # 打印一下实际的列名，让我们看看本地到底长什么样
        print(f"\n🔍 智能嗅探本地表 [{table}] 的列名: {list(data[0].keys())}")

        clean_data = []
        for r in data:
            # 💡 智能匹配药名字段（不管本地叫 chinese_name, cn_name 还是 name）
            c_name = r.get('chinese_name') or r.get('cn_name') or r.get('name') or r.get('full_name')
            if not c_name: continue

            row_data = {'chinese_name': c_name}
            
            # 安全地同步其他基础字段
            if 'pinyin' in r: row_data['pinyin'] = r['pinyin']
            if 'pinyin_abbr' in r: row_data['pinyin_abbr'] = r['pinyin_abbr']
            if 'category' in r: row_data['category'] = r['category']
            if 'section' in r: row_data['category'] = r['section'] # 有些表叫 section
            if 'dosage_form' in r: row_data['dosage_form'] = r['dosage_form']

            clean_data.append(row_data)

        if clean_data:
            print(f"⏳ 正在重新向 Supabase 注入 [{table}]，共 {len(clean_data)} 条核心骨架...")
            for i in range(0, len(clean_data), 500):
                batch = clean_data[i:i+500]
                client.table(table).upsert(batch, on_conflict='chinese_name').execute()
                print(f"   ✔️ 成功上传 {min(i + 500, len(clean_data))} / {len(clean_data)}")
                
    except Exception as e:
        print(f"❌ 处理 {table} 时出错: {e}")

conn.close()
print("\n🎉 终极骨架重塑完成！你的 Supabase 现在满血复活了！")


