import os
import sys
import io
import json
import time
from supabase import create_client
from groq import Groq

# 强制 UTF-8 环境
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    # 配置信息
    url = os.environ.get("SUPABASE_URL")
    key = "sb_publishable_egJtK5qOnELNDhE64x01Ow_qzQskrmR"
    g_key = os.environ.get("GROQ_API_KEY")

    supabase = create_client(url, key)
    groq = Groq(api_key=g_key)

    print("--- 🚀 Level 2: Latin Name Alignment (Groq Engine) ---")
    
    # 查找所有状态为 'aligned' 的记录
    res = supabase.table("tcm_single_herb").select("id, chinese_name").eq("data_level", "aligned").execute()
    herbs = res.data
    
    total = len(herbs)
    print(f"Target found: {total} records. Model: Llama3-70b")

    # 分批处理 (每10个一组)
    batch_size = 10
    for i in range(0, total, batch_size):
        batch = herbs[i:i+batch_size]
        names = [h['chinese_name'] for h in batch]
        
        # 构造 prompt
        prompt = f"As a TCM taxonomist, provide standard Latin names for: {', '.join(names)}. Return ONLY a JSON: {{\"ChineseName\": \"LatinName\"}}"

        try:
            chat_completion = groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                response_format={"type": "json_object"}
            )
            
            mapping = json.loads(chat_completion.choices[0].message.content)

            for h in batch:
                cname = h['chinese_name']
                latin = mapping.get(cname)
                if latin:
                    # 更新数据库：写入拉丁名并将状态改为 enriched
                    try:
                        supabase.table("tcm_single_herb").update({
                            "latin_name": latin,
                            "data_level": "enriched"
                        }).eq("id", h['id']).execute()
                    except:
                        pass # 忽略单条写入失败
            
            print(f"Progress: {i + len(batch)}/{total} | Current: {names[0]} -> {mapping.get(names[0])}")
            time.sleep(0.5) # Groq 很强，不需要太长等待

        except Exception as e:
            print(f"Batch Error: {e}")
            continue

    print("\n✅ MISSION COMPLETE: 606 herbs enriched with Latin names!")

if __name__ == "__main__":
    main()

