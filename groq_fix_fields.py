import os
import sys
import io
import json
import time
from supabase import create_client
from groq import Groq

# 强制输出 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    # --- 配置区 ---
    url = os.environ.get("SUPABASE_URL")
    key = "sb_publishable_egJtK5qOnELNDhE64x01Ow_qzQskrmR" 
    g_key = os.environ.get("GROQ_API_KEY")

    try:
        supabase = create_client(url, key)
        groq = Groq(api_key=g_key)

        print("Testing Anon Key Access with corrected field names...")
        
        # 尝试查询，将 cn_name 改回 chinese_name
        # 如果还是错，脚本会捕获并提醒
        try:
            res = supabase.table("tcm_single_herb").select("id, chinese_name").eq("data_level", 1).limit(3).execute()
        except Exception as e:
            print(f"Query Error: {e}")
            print("Hint: Please check if the column is 'name' or 'chinese_name' in your Supabase dashboard.")
            return

        herbs = res.data
        if not herbs:
            print("No data found with data_level = 1.")
            return

        print(f"Success! Found {len(herbs)} samples. Processing first one...")

        herb = herbs[0]
        name = herb['chinese_name']
        
        # Groq 推理
        completion = groq.chat.completions.create(
            messages=[{"role": "user", "content": f"Latin name for {name}? Just the name."}],
            model="llama3-8b-8192",
        )
        latin = completion.choices[0].message.content.strip()
        print(f"AI Result: {name} -> {latin}")

        # 写入测试
        try:
            # 这里同时将 data_level 改为 2
            supabase.table("tcm_single_herb").update({"latin_name": latin, "data_level": 2}).eq("id", herb['id']).execute()
            print(f"🏆 UPDATE SUCCESS! Your Anon Key has write permissions.")
        except Exception as up_e:
            print(f"❌ UPDATE FAILED: {up_e}")
            print("Reason: Anon Key usually cannot update. Please use 'service_role' key for writing.")

    except Exception as e:
        print(f"System Error: {str(e)}")

if __name__ == "__main__":
    main()

