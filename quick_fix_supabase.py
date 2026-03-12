import requests
import time
from urllib.parse import quote
import sys

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

def quick_fix():
    """快速修复category和url的null值"""
    print("=" * 60)
    print("🔧 TCM-Exosome 快速修复工具")
    print("=" * 60)
    
    try:
        # 步骤1: 检查需要修复的记录
        print("\n📊 正在检查需要修复的记录...")
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/papers",
            params={
                "or": "(category.is.null,url.is.null)",
                "select": "id,title,external_id,source",
                "limit": 200
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 获取数据失败: {response.status_code}")
            return
        
        papers = response.json()
        total_needed = len(papers)
        print(f"📊 找到 {total_needed} 篇需要修复的论文")
        
        if total_needed == 0:
            print("✅ 没有需要修复的论文，所有字段都已填写")
            return
        
        # 步骤2: 显示预览
        print("\n📋 前5条需要修复的记录:")
        for i, paper in enumerate(papers[:5]):
            print(f"\n  {i+1}. ID: {paper['id']}")
            print(f"     标题: {paper.get('title', 'N/A')[:50]}...")
            print(f"     当前category: {paper.get('category', 'None')}")
            print(f"     当前url: {paper.get('url', 'None')}")
        
        # 步骤3: 确认修复
        print(f"\n⚠️  即将修复 {total_needed} 篇论文的category和url字段")
        confirm = input("是否继续？(y/n): ").strip().lower()
        
        if confirm != 'y':
            print("❌ 已取消")
            return
        
        # 步骤4: 开始修复
        print("\n🔧 开始修复...")
        fixed_count = 0
        error_count = 0
        
        for i, paper in enumerate(papers):
            try:
                updates = {}
                
                # 根据source设置category
                source = paper.get('source', '')
                if paper.get('category') is None:
                    if '丹参' in source:
                        category = 'Cardiovascular Research'
                    elif '淫羊藿' in source:
                        category = 'Bone Research'
                    elif '葛根' in source:
                        category = 'Metabolic Research'
                    elif '刺五加' in source:
                        category = 'Neurobiology'
                    else:
                        category = 'TCM Research'
                    updates['category'] = category
                
                # 设置URL
                if paper.get('url') is None:
                    external_id = paper.get('external_id', '')
                    if external_id and str(external_id).isdigit():
                        url = f"https://pubmed.ncbi.nlm.nih.gov/{external_id}/"
                    else:
                        title = paper.get('title', '')
                        if title:
                            encoded = quote(title)
                            url = f"https://scholar.google.com/scholar?q={encoded}"
                        else:
                            url = "#"
                    updates['url'] = url
                
                if updates:
                    # 更新记录
                    update_response = requests.patch(
                        f"{SUPABASE_URL}/rest/v1/papers?id=eq.{paper['id']}",
                        headers=headers,
                        json=updates,
                        timeout=30
                    )
                    
                    if update_response.status_code in [200, 204]:
                        fixed_count += 1
                        print(f"  ✅ [{i+1}/{total_needed}] ID {paper['id']}: 已更新")
                    else:
                        error_count += 1
                        print(f"  ❌ [{i+1}/{total_needed}] ID {paper['id']}: 更新失败 {update_response.status_code}")
                
                # 每10条记录暂停一下
                if (i + 1) % 10 == 0:
                    print(f"  ...已处理 {i+1} 条，暂停2秒...")
                    time.sleep(2)
                
                # 每条记录间隔0.3秒
                time.sleep(0.3)
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ [{i+1}/{total_needed}] ID {paper['id']}: {e}")
                time.sleep(1)
                continue
        
        # 步骤5: 显示结果
        print("\n" + "=" * 60)
        print("📊 修复结果统计")
        print("=" * 60)
        print(f"✅ 成功修复: {fixed_count} 篇")
        print(f"❌ 修复失败: {error_count} 篇")
        print(f"📊 总计处理: {total_needed} 篇")
        
        # 步骤6: 验证修复结果
        print("\n🔍 验证修复结果...")
        verify_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/papers",
            params={
                "or": "(category.is.null,url.is.null)",
                "select": "id",
                "limit": 10
            },
            headers=headers,
            timeout=30
        )
        
        if verify_response.status_code == 200:
            remaining = len(verify_response.json())
            if remaining == 0:
                print("✅ 所有字段都已修复完成！")
            else:
                print(f"⚠️ 仍有 {remaining} 篇需要修复（可能是新数据）")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

def check_status():
    """检查当前状态"""
    print("\n📊 检查数据库状态...")
    
    try:
        # 获取总数
        count_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/papers?select=count",
            headers={**headers, "Prefer": "count=exact"},
            timeout=30
        )
        
        if count_response.status_code == 200:
            total = count_response.headers.get("Content-Range", "0/0").split("/")[-1]
            print(f"📊 论文总数: {total}")
        else:
            print(f"⚠️ 无法获取总数: {count_response.status_code}")
        
        # 获取null值统计
        null_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/papers",
            params={
                "or": "(category.is.null,url.is.null)",
                "select": "id,category,url",
                "limit": 1000
            },
            headers=headers,
            timeout=30
        )
        
        if null_response.status_code == 200:
            null_papers = null_response.json()
            category_null = sum(1 for p in null_papers if p.get('category') is None)
            url_null = sum(1 for p in null_papers if p.get('url') is None)
            
            print(f"\n📊 null值统计:")
            print(f"  category为null: {category_null}")
            print(f"  url为null: {url_null}")
            
            if null_papers:
                print(f"\n📋 示例数据:")
                for p in null_papers[:3]:
                    print(f"  ID {p['id']}: category={p.get('category')}, url={p.get('url')}")
        else:
            print(f"⚠️ 无法获取null值统计: {null_response.status_code}")
            
    except Exception as e:
        print(f"❌ 检查状态时出错: {e}")

if __name__ == "__main__":
    print("\n请选择操作:")
    print("1. 快速修复category和url")
    print("2. 仅查看状态")
    print("3. 退出")
    
    choice = input("\n输入选择 (1-3): ").strip()
    
    if choice == "1":
        quick_fix()
    elif choice == "2":
        check_status()
    else:
        print("退出")


