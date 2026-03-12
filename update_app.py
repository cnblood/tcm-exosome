import re

# 读取当前 app.py
with open('src/dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加智能分类函数
smart_category_function = '''
# =========================
# Smart categorization functions
# =========================
def smart_categorize(title):
    """智能分类论文标题"""
    if not title or not isinstance(title, str):
        return 'Uncategorized'
    
    title_lower = title.lower()
    
    categories = {
        'Neurodegenerative': ['neurotransmitter', 'cerebellar', 'brain', 'neuron', 'synapse', 'cognitive', 'memory', 'alzheimer', 'parkinson'],
        'Bone Research': ['osteoclast', 'osteoporosis', 'bone', 'skeletal', 'fracture', 'calcification'],
        'Inflammation': ['inflammation', 'inflammatory', 'colitis', 'macrophage', 'cytokine', 'immune', 'immunomodulatory'],
        'Cancer': ['cancer', 'tumor', 'carcinoma', 'malignant', 'metastasis', 'oncology', 'proliferation'],
        'Cardiovascular': ['cardiac', 'heart', 'vascular', 'angiogenesis', 'endothelial', 'atherosclerosis'],
        'Metabolic': ['metabolic', 'diabetes', 'obesity', 'lipid', 'cholesterol', 'insulin', 'glucose'],
        'Pharmacokinetics': ['pharmacokinetic', 'bioavailability', 'absorption', 'metabolism', 'distribution'],
        'Exosome Biology': ['exosome', 'extracellular vesicle', 'nanovesicle', 'microparticle'],
        'Gastroenterology': ['colitis', 'intestinal', 'gut', 'gastric', 'digestive'],
    }
    
    matches = []
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in title_lower:
                matches.append(category)
                break
    
    if matches:
        priority = ['Exosome Biology', 'Inflammation', 'Cancer', 'Neurodegenerative', 'Bone Research']
        for cat in priority:
            if cat in matches:
                return cat
        return matches[0]
    
    return 'General TCM Research'

def generate_scholar_url(title):
    """生成Google Scholar搜索链接"""
    if not title or not isinstance(title, str):
        return '#'
    import urllib.parse
    encoded = urllib.parse.quote(title)
    return f"https://scholar.google.com/scholar?q={encoded}"

def fix_papers_display(df):
    """修复论文显示问题"""
    if df.empty:
        return df
    
    df_fixed = df.copy()
    
    # 修复source显示
    source_fixes = {
        'Pharmacopoeia_易根': 'Pharmacopoeia_葛根',
        'Pharmacopoeia_洋羊藿': 'Pharmacopoeia_淫羊藿',
    }
    
    for wrong, correct in source_fixes.items():
        if 'source' in df_fixed.columns:
            df_fixed['source'] = df_fixed['source'].replace(wrong, correct)
    
    # 智能分类
    if 'title' in df_fixed.columns:
        df_fixed['category'] = df_fixed['title'].apply(smart_categorize)
    
    # 生成URL
    if 'title' in df_fixed.columns and 'url' in df_fixed.columns:
        def fix_url(row):
            if pd.notna(row.get('url')) and str(row['url']) not in ['None', 'N/A', '', '#']:
                return row['url']
            return generate_scholar_url(row['title'])
        
        df_fixed['url'] = df_fixed.apply(fix_url, axis=1)
    
    return df_fixed
'''

# 插入函数到文件中
if 'def fix_papers_display' not in content:
    # 找到导入部分之后的位置
    import_pattern = r'(import.*?\n)+'
    import_match = re.search(import_pattern, content)
    if import_match:
        insert_pos = import_match.end()
        content = content[:insert_pos] + smart_category_function + '\n' + content[insert_pos:]

# 修改数据加载部分
old_pattern = r'(df_latest = sb_query\(\s*"papers",.*?\))'
new_pattern = r'\1\n    if not df_latest.empty:\n        df_latest = fix_papers_display(df_latest)'
content = re.sub(old_pattern, new_pattern, content, flags=re.DOTALL)

# 保存修改
with open('src/dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ app.py 已更新")
