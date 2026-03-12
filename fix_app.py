import re

with open('src/dashboard/app.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 修复所有破损的emoji和字符串
fixes = [
    # Overview metrics
    ('sb_count("papers")', 'sb_count("papers")'),
    # 修复破损的evidence行
    ('(evidence,"Herbs w/ Evidence",  "\u731b?),', '(evidence,"Herbs w/ Evidence",  "\u2b50"),'),
    # 修复Latest Papers - 改用Supabase
    ('df_r = qdf("SELECT title,authors,journal,pub_date,source FROM research_papers ORDER BY created_at DESC LIMIT 8")',
     'df_r = sb_query("papers", select="title,source,category,url", limit=8, order="created_at.desc")'),
    # 修复Literature Sources图表
    ('df_src = qdf("DUMMY")',
     'df_src_raw = sb_query("papers", select="source", limit=500)\n        if not df_src_raw.empty:\n            df_src = df_src_raw["source"].value_counts().reset_index()\n            df_src.columns = ["source","count"]\n        else:\n            df_src = pd.DataFrame()'),
]

for old, new in fixes:
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed: {old[:50]}")
    else:
        print(f"NOT FOUND: {old[:50]}")

with open('src/dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
