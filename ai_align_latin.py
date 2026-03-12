import os
import json
import time
from supabase import create_client
from openai import OpenAI

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def get_pending_herbs():
    response = supabase.table('tcm_single_herb').select('id, chinese_name').is_('latin_name', 'null').execute()
    return response.data

def fetch_latin_names_from_ai(herb_names):
    prompt = f"""
    你是一个权威的《中国药典》生药学专家。
    请为以下中药材提供标准的【拉丁学名】(Latin Name, 包含命名者，如 Panax ginseng C. A. Mey.) 和【植物科属】(Taxonomy Family, 如 五加科)。
    
    待处理中药列表：
    {', '.join(herb_names)}
    
    必须严格以 JSON 格式输出，包含一个 "data" 数组，格式如下：
    {{
      "data": [
        {{"chinese_name": "人参", "latin_name": "Panax ginseng C. A. Mey.", "taxonomy_family": "五加科"}}
      ]
    }}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个只输出合法 JSON 格式数据的中医药接口。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        result_str = response.choices[0].message.content
        return json.loads(result_str).get("data", [])
    except Exception as e:
        print(f"❌ AI 请求或解析失败: {e}")
        return []

def main():
    print("🔍 正在扫描 Supabase 中缺少拉丁名的中药...")
    pending_herbs = get_pending_herbs()
    if not pending_herbs:
        print("✅ 所有单方药材都已经拥有拉丁名，无需处理！")
        return
        
    total_count = len(pending_herbs)
    print(f"📦 发现 {total_count} 个待处理记录。启动 DeepSeek 生药学引擎...")
    
    batch_size = 30 
    for i in range(0, total_count, batch_size):
        batch = pending_herbs[i:i+batch_size]
        
        # 💡 [关键修复]：过滤掉数据库中可能存在的 Null 或是空字符串的脏数据
        herb_names = [h.get('chinese_name') for h in batch if h.get('chinese_name')]
        
        if not herb_names:
            continue
            
        print(f"\n⏳ 正在请求 AI 处理第 {i+1} 到 {min(i+batch_size, total_count)} 个药材...")
        print(f"   💊 包含: {', '.join(herb_names[:5])} 等...")
        
        ai_results = fetch_latin_names_from_ai(herb_names)
        if not ai_results:
            print("⚠️ 本批次未能成功解析，跳过。")
            continue
            
        update_count = 0
        for item in ai_results:
            c_name = item.get("chinese_name")
            l_name = item.get("latin_name")
            t_family = item.get("taxonomy_family")
            
            if c_name and l_name:
                try:
                    supabase.table('tcm_single_herb').update({
                        'latin_name': l_name,
                        'taxonomy_family': t_family,
                        'data_level': 'aligned'
                    }).eq('chinese_name', c_name).execute()
                    update_count += 1
                except Exception as e:
                    print(f"   ❌ 更新 {c_name} 失败: {e}")
                
        print(f"   ✔️ 成功将 {update_count} 条国际标准映射写入 Supabase。")
        time.sleep(2)

    print("\n🎉 Level 2：中英/拉丁文国际映射对齐全部完成！")

if __name__ == "__main__":
    main()



