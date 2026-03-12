import sqlite3
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
client = create_client(SUPABASE_URL, SUPABASE_KEY)
db_path = 'data/tcm_exosome.db'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 明确本地字段和云端字段的映射关系
tables_config = {
    'tcm_single_herb': 'cn_name',        # 本地叫 cn_name
    'tcm_compound_formula': 'full_name', # 本地复方叫 full_name
    'tcm_extracts': 'cn_name'
}

print("🧹 正在清理云端的空白脏数据...")
for table in tables_config.keys():
    try:
        # 清除之前传入的那些没有中文名的空行
        client.table(table).delete().gt('id', 0).execute()
    except Exception as e:
        pass

batch_size = 500
for table, name_col in tables_config.items():
    try:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        clean_data = []
        for r in rows:
            r_dict = dict(r)
            
            # 💡 核心映射：把本地的不同叫法，统一转化为云端的 chinese_name
            chinese_name = r_dict.get(name_col)
            if not chinese_name: continue
            
            new_row = {'chinese_name': chinese_name}
            
            # 同步其他有用的字段
            if 'pinyin' in r_dict: new_row['pinyin'] = r_dict['pinyin']
            if 'pinyin_abbr' in r_dict: new_row['pinyin_abbr'] = r_dict['pinyin_abbr']
            if table == 'tcm_single_herb' and 'section' in r_dict:
                new_row['category'] = r_dict['section']
            if table == 'tcm_compound_formula' and 'dosage_form' in r_dict:
                new_row['dosage_form'] = r_dict['dosage_form']
                
            clean_data.append(new_row)

        if not clean_data:
            continue

        print(f"\n⏳ 正在正确映射并同步 [{table}]，共 {len(clean_data)} 条记录...")
        for i in range(0, len(clean_data), batch_size):
            batch = clean_data[i:i+batch_size]
            client.table(table).upsert(batch, on_conflict='chinese_name').execute()
            print(f"   ✔️ 成功上传 {min(i + batch_size, len(clean_data))} / {len(clean_data)}")
    except Exception as e:
        print(f"❌ 处理 {table} 时出错: {e}")

conn.close()
print("\n🎉 数据底层修复与同步完成！现在云端真正拥有药名了！")


