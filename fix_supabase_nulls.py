import requests
import json
import urllib.parse

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def smart_categorize(title, abstract, source):
    """根据内容智能分类"""
    text = (title + ' ' + (abstract or '') + ' ' + (source or '')).lower()
    
    categories = {
        'Epigenetics': ['epigenetic', 'dna methylation', 'histone', 'chromatin'],
        'Metabolomics': ['metabolome', 'metabolite', 'biosynthesis', 'secondary metabolism'],
        'Pharmacology': ['pharmacological', 'therapeutic', 'drug', 'bioactive'],
        'Neurobiology': ['brain', 'neuron', 'neurotransmitter', 'cerebellar', 'cognitive'],
        'Immunology': ['immune', 'inflammation', 'macrophage', 'cytokine'],
        'Oncology': ['cancer', 'tumor', 'carcinoma', 'malignant'],
        'Bone Research': ['osteoclast', 'osteoporosis', 'bone', 'skeletal'],
        'Cardiovascular': ['cardiac', 'heart', 'vascular', 'angiogenesis'],
        'Gastroenterology': ['colitis', 'intestinal', 'gut', 'digestive'],
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category
    
    return 'General TCM Research'

def generate_url(title, external_id, source):
    """生成合适的URL"""
    if external_id and external_id.isdigit():
        return f"https://pubmed.ncbi.nlm.nih.gov/{external_id}/"
    elif title:
        encoded = urllib.parse.quote(title)
        return f"https://scholar.google.com/scholar?q={encoded}"
    else:
        return "#"

def fix_null_fields():
    """修复category和url为null的记录"""
    
    # 获取所有category或url为null的记录
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/papers?or=(category.is.null,url.is.null)&select=id,title,abstract,external_id,source",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 获取数据失败: {response.status_code}")
        print(response.text)
        return
    
    papers = response.json()
    print(f"📊 找到 {len(papers)} 篇需要修复的论文")
    
    fixed_count = 0
    for paper in papers:
        updates = {}
        
        # 修复category
        if paper.get('category') is None:
            category = smart_categorize(
                paper.get('title', ''),
                paper.get('abstract', ''),
                paper.get('source', '')
            )
            updates['category'] = category
        
        # 修复url
        if paper.get('url') is None:
            url = generate_url(
                paper.get('title', ''),
                paper.get('external_id', ''),
                paper.get('source', '')
            )
            updates['url'] = url
        
        if updates:
            # 更新记录
            update_response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/papers?id=eq.{paper['id']}",
                headers=headers,
                json=updates
            )
            
            if update_response.status_code in [200, 204]:
                fixed_count += 1
                if fixed_count <= 5:  # 只显示前5条
                    print(f"\n✅ 修复 ID {paper['id']}:")
                    if 'category' in updates:
                        print(f"   category: {updates['category']}")
                    if 'url' in updates:
                        print(f"   url: {updates['url']}")
            else:
                print(f"❌ 更新失败 ID {paper['id']}: {update_response.status_code}")
    
    print(f"\n✅ 成功修复 {fixed_count} 篇论文")

if __name__ == "__main__":
    fix_null_fields()


