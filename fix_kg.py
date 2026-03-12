import sqlite3, os, sys
sys.path.insert(0, '.')

# ???????knowledge_graph_page.py
with open('src/dashboard/knowledge_graph_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ??build_network_html??merge
old1 = '''    # ?????
    if not mapping_df.empty and "name_en" in mapping_df.columns:
        hg_df = hg_df.merge(mapping_df[["name_en","name_cn"]], left_on="herb_name", right_on="name_en", how="left")
        hg_df["display_herb"] = hg_df["name_cn"].fillna(hg_df["herb_name"])
    else:
        hg_df["display_herb"] = hg_df["herb_name"]'''
new1 = '''    # ????? - ????
    hg_df["display_herb"] = hg_df["herb_name"]
    try:
        if not mapping_df.empty:
            for en_col in [c for c in mapping_df.columns if "en" in c.lower()]:
                for cn_col in [c for c in mapping_df.columns if "cn" in c.lower()]:
                    tmp = mapping_df[[en_col, cn_col]].dropna()
                    mapping_dict = dict(zip(tmp[en_col], tmp[cn_col]))
                    hg_df["display_herb"] = hg_df["herb_name"].map(mapping_dict).fillna(hg_df["herb_name"])
                    break
    except Exception as e:
        pass'''

content = content.replace(old1, new1)

# ??render_knowledge_graph??merge
old2 = '''    if not mapping_df.empty:
        hg_merged = hg_df.merge(mapping_df[["name_en","name_cn"]], left_on="herb_name", right_on="name_en", how="left")
        hg_merged["display_herb"] = hg_merged["name_cn"].fillna(hg_merged["herb_name"])
    else:
        hg_merged = hg_df.copy()
        hg_merged["display_herb"] = hg_merged["herb_name"]'''
new2 = '''    hg_merged = hg_df.copy()
    hg_merged["display_herb"] = hg_merged["herb_name"]
    try:
        if not mapping_df.empty:
            for en_col in [c for c in mapping_df.columns if "en" in c.lower()]:
                for cn_col in [c for c in mapping_df.columns if "cn" in c.lower()]:
                    tmp = mapping_df[[en_col, cn_col]].dropna()
                    mapping_dict = dict(zip(tmp[en_col], tmp[cn_col]))
                    hg_merged["display_herb"] = hg_merged["herb_name"].map(mapping_dict).fillna(hg_merged["herb_name"])
                    break
    except Exception as e:
        pass'''

content = content.replace(old2, new2)

with open('src/dashboard/knowledge_graph_page.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed, size:', len(content))
