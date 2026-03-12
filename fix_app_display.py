"""
修复应用显示问题
- 修复分类映射
- 修复URL显示
- 修复source编码
"""

import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

def fix_papers_data(df):
    """修复论文数据"""
    if df.empty:
        return df
    
    df_fixed = df.copy()
    
    # 修复source字段（处理乱码）
    source_mapping = {
        'Pharmacopoeia_易根': 'Pharmacopoeia_葛根',
        'Pharmacopoeia_洋羊藿': 'Pharmacopoeia_淫羊藿',
        # 添加更多映射
    }
    
    for wrong, correct in source_mapping.items():
        df_fixed['source'] = df_fixed['source'].replace(wrong, correct)
    
    # 修复分类
    category_mapping = {
        'exosome': 'Exosome Research',
        'nanovesicle': 'Nanovesicle Research',
        'extracellular vesicle': 'Extracellular Vesicle',
        'osteoclast': 'Bone Research',
        'inflammation': 'Inflammation Research',
        'neurotransmitter': 'Neuroscience',
        'pharmacokinetics': 'Pharmacokinetics',
        'default': 'Uncategorized'
    }
    
    # 根据标题自动分类
    def categorize_title(title):
        if not isinstance(title, str):
            return 'Uncategorized'
        title_lower = title.lower()
        for key, category in category_mapping.items():
            if key in title_lower and key != 'default':
                return category
        return 'Uncategorized'
    
    df_fixed['category'] = df_fixed['title'].apply(categorize_title)
    
    # 修复URL（如果有DOI或PMID可以生成链接）
    def fix_url(row):
        if pd.notna(row.get('url')) and row['url'] not in ['None', 'N/A', '#', '']:
            return row['url']
        
        # 尝试从标题生成搜索链接
        if pd.notna(row.get('title')):
            title_encoded = requests.utils.quote(row['title'])
            return f"https://scholar.google.com/scholar?q={title_encoded}"
        
        return '#'
    
    df_fixed['url'] = df_fixed.apply(fix_url, axis=1)
    
    return df_fixed

def fix_herb_data(df):
    """修复草药数据"""
    if df.empty:
        return df
    
    df_fixed = df.copy()
    
    # 修复拉丁名
    latin_fixes = {
        'pueraria lobata': 'Pueraria lobata',
        'epimedium brevicornu': 'Epimedium brevicornu',
        'curculigo orchioides': 'Curculigo orchioides',
    }
    
    if 'latin_name' in df_fixed.columns:
        for wrong, correct in latin_fixes.items():
            df_fixed['latin_name'] = df_fixed['latin_name'].str.replace(
                wrong, correct, case=False, regex=False
            )
    
    return df_fixed

# 主函数
def main():
    print("🔧 开始修复应用显示问题...")
    
    # 这里放你的修复逻辑
    print("✅ 修复完成！")
    
if __name__ == "__main__":
    main()
