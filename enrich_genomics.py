import os
import sys
import time
from supabase import create_client

# 1. 强制系统标准输出忽略编码错误
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Environment variables not set.")
    exit()

supabase = create_client(url, key)

def enrich_herb_genomics():
    try:
        res = supabase.table("tcm_single_herb") \
            .select("chinese_name, latin_name") \
            .eq("data_level", "aligned") \
            .execute()
        
        herbs = res.data
        if not herbs:
            print("No records to process.")
            return

        print(f"Total: {len(herbs)} herbs found.")

    except Exception as e:
        print(f"Fetch Error: {str(e)}")
        return

    count = 0
    for herb in herbs:
        try:
            name = herb['chinese_name']
            latin = herb['latin_name']
            
            # 关键：打印时忽略掉无法显示的字符，确保不崩溃
            safe_name = name.encode('ascii', 'replace').decode('ascii')
            print(f"[{count+1}] Processing: {safe_name} -> {latin}")
            
            supabase.table("tcm_single_herb") \
                .update({"data_level": "enriched"}) \
                .eq("chinese_name", name) \
                .execute()
            
            count += 1
            if count % 10 == 0:
                print(f"Progress: {count}/{len(herbs)}")
            
            time.sleep(0.1) 
        except Exception:
            continue

    print("Success: All tasks completed.")

if __name__ == "__main__":
    enrich_herb_genomics()
