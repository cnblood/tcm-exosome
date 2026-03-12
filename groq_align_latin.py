import os
import sys
import io
import time
import json
from supabase import create_client
from groq import Groq

# 强制环境为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_ascii(s):
    return "".join(i for i in s if ord(i) < 128).strip()

def main():
    # 1. 初始化客户端
    s_url = clean_ascii(os.environ.get("SUPABASE_URL"))
    s_key = clean_ascii(os.environ.get("SUPABASE_KEY"))
    g_key = clean_ascii(os.environ.get("GROQ_API_KEY"))
    
    supabase = create_client(s_url, s_key)
    groq = Groq(api_key=g_key)

    # 2. 扫描待处理数据 (Level 1 -> Level 2)
    print("Scanning database for herbs missing Latin names...")
    res = supabase.table("tcm_single_herb").select("id, cn_name").eq("data_level", 1).limit(600).execute()
    herbs = res.data
    
    if not herbs:
        print("No herbs found to process.")
        return

    print(f"Total: {len(herbs)} herbs. Starting Groq reasoning (Llama3-70b)...")

    # 3. 分批处理 (每 10 个一批，防止 Token 溢出)
    batch_size = 10
    for i in range(0, len(herbs), batch_size):
        batch = herbs[i:i+batch_size]
        names = [h['cn_name'] for h in batch]
        
        prompt = f"As a TCM expert, provide the standard Latin scientific names for these Chinese herbs: {', '.join(names)}. Return ONLY a JSON object: {{\"HerbName\": \"LatinName\"}}"

        try:
            chat_completion = groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                response_format={"type": "json_object"}
            )
            
            mapping = json.loads(chat_completion.choices[0].message.content)
            
            # 4. 回写数据库
            for h in batch:
                cn_name = h['cn_name']
                latin = mapping.get(cn_name)
                if latin:
                    supabase.table("tcm_single_herb").update({
                        "latin_name": latin,
                        "data_level": 2
                    }).eq("id", h['id']).execute()
            
            print(f"Processed: {i + len(batch)} / {len(herbs)} | Latest: {names[-1]} -> {mapping.get(names[-1])}")
            time.sleep(1) # 频率限制保护

        except Exception as e:
            print(f"Error in batch {i}: {str(e)}")
            continue

    print("SUCCESS: All Latin names aligned via Groq!")

if __name__ == "__main__":
    main()
