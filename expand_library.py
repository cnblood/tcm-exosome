import requests
from bs4 import BeautifulSoup
import time
import csv
import os
import sys

# 使用镜像站点
BASE_URL = "https://pubmed.ncbi.nlm.nih.gov.hk.ssl.cdn.cloudflare.net"

def search_pubmed(query, max_results=50):
    """搜索 PubMed，返回文章详情列表"""
    search_url = f"{BASE_URL}/?term={query}&size={max_results}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    articles = []
    
    print(f"正在请求: {search_url}")
    try:
        resp = requests.get(search_url, headers=headers, timeout=15)
        resp.raise_for_status()
        # 保存响应内容到文件，便于调试
        with open("debug_search.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("已保存搜索页 HTML 到 debug_search.html，可打开查看实际结构")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 方法1：尝试查找所有文章条目（根据 PubMed 常见结构）
        # 通常每个结果在一个 <div class="docsum-content"> 或 <article> 中
        result_elems = soup.select('div.docsum-content, article')
        if not result_elems:
            # 如果没有找到，尝试更广泛的选择器
            result_elems = soup.find_all(['div', 'article'], class_=lambda c: c and 'docsum' in c)
        
        print(f"找到 {len(result_elems)} 个可能的文章条目")
        
        for elem in result_elems:
            # 提取标题和链接
            title_link = elem.find('a', class_='docsum-title') or elem.find('a')
            if not title_link:
                continue
            title = title_link.get_text(strip=True)
            href = title_link.get('href')
            if not href:
                continue
            # 处理相对链接
            if href.startswith('/'):
                link = BASE_URL + href
            else:
                link = href
            
            # 提取 PMID
            pmid_elem = elem.find('span', class_='docsum-pmid') or elem.find(class_='pmid')
            pmid = pmid_elem.get_text(strip=True) if pmid_elem else ''
            
            articles.append({
                'title': title,
                'link': link,
                'pmid': pmid
            })
        
        return articles
    except Exception as e:
        print(f"搜索出错: {e}")
        return []

def fetch_abstract(url):
    """获取文章摘要"""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 尝试多个可能的摘要容器
        abstract_div = soup.find('div', class_='abstract-content') or \
                       soup.find('div', class_='abstr') or \
                       soup.find('div', {'id': 'abstract'})
        if abstract_div:
            return abstract_div.get_text(separator='\n', strip=True)
        return "无摘要"
    except Exception as e:
        print(f"获取摘要失败: {e}")
        return "获取失败"

def save_to_csv(articles, filename='tcm_exosome_results.csv'):
    """保存结果到CSV"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'link', 'pmid', 'abstract'])
        writer.writeheader()
        for art in articles:
            writer.writerow(art)
    print(f"结果已保存至 {os.path.abspath(filename)}")

def main():
    # 你的关键词（可以根据需要修改）
    query = "(traditional Chinese medicine OR TCM) AND exosome"
    print(f"搜索关键词: {query}")
    
    articles = search_pubmed(query, max_results=50)
    print(f"找到 {len(articles)} 篇文章")
    
    if not articles:
        print("未找到文章，请检查 debug_search.html 文件，确认页面结构，然后调整选择器。")
        return
    
    # 获取每篇摘要
    for i, art in enumerate(articles, 1):
        print(f"正在获取第 {i} 篇摘要: {art['title'][:50]}...")
        art['abstract'] = fetch_abstract(art['link'])
        time.sleep(0.5)  # 礼貌延时
    
    # 保存
    save_to_csv(articles)
    print("全部完成！")

if __name__ == "__main__":
    main()