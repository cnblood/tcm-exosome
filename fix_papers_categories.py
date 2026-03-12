import sqlite3
import os
import re
from datetime import datetime

def smart_categorize(title):
    """根据标题智能分类论文"""
    if not title or not isinstance(title, str):
        return 'Uncategorized'
    
    title_lower = title.lower()
    
    # 分类规则
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
    
    # 检查匹配
    matches = []
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in title_lower:
                matches.append(category)
                break
    
    # 去重并返回第一个匹配，如果没有匹配则返回'General TCM Research'
    if matches:
        # 如果有多个匹配，返回最重要的（按列表顺序）
        for category in ['Exosome Biology', 'Inflammation', 'Cancer', 'Neurodegenerative', 'Bone Research']:
            if category in matches:
                return category
        return matches[0]
    
    return 'General TCM Research'

def generate_url(title):
    """根据标题生成搜索URL"""
    if not title or not isinstance(title, str):
        return '#'
    
    # 编码标题用于URL
    encoded_title = title.replace(' ', '+')
    # 返回Google Scholar搜索链接
    return f"https://scholar.google.com/scholar?q={encoded_title}"

def fix_papers_categories():
    """修复papers表中的分类和URL"""
    db_path = os.environ.get('DB_PATH', 'data/tcm_exosome.db')
    print(f"📁 连接数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有需要修复的论文
    cursor.execute('''
    SELECT id, title, category, url FROM papers 
    WHERE category IS NULL OR category = '' OR category = 'Uncategorized' OR url IS NULL OR url = '' OR url = 'N/A'
    ''')
    
    papers_to_fix = cursor.fetchall()
    print(f"📊 找到 {len(papers_to_fix)} 篇需要修复的论文")
    
    fixed_count = 0
    for paper_id, title, old_category, old_url in papers_to_fix:
        new_category = smart_categorize(title)
        new_url = generate_url(title)
        
        # 更新数据库
        cursor.execute('''
        UPDATE papers 
        SET category = ?, url = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (new_category, new_url, paper_id))
        
        fixed_count += 1
        if fixed_count <= 10:  # 只显示前10条的详细信息
            print(f"\n  ✅ 修复: {title[:50]}...")
            print(f"     分类: {old_category} -> {new_category}")
            print(f"     URL: {new_url}")
    
    conn.commit()
    print(f"\n✅ 成功修复 {fixed_count} 篇论文")
    
    # 显示统计
    cursor.execute('''
    SELECT category, COUNT(*) FROM papers GROUP BY category
    ''')
    
    print("\n📊 分类统计:")
    for category, count in cursor.fetchall():
        print(f"  {category}: {count}")
    
    conn.close()

if __name__ == "__main__":
    fix_papers_categories()
