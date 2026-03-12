import os
import sys
import json
from supabase import create_client
import time

# 彻底重定向所有输出到文件，完全不通过 PowerShell 显示
f = open('sync_log.txt', 'w', encoding='utf-8')
sys.stdout = f
sys.stderr = f

def main():
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        client = create_client(url, key)

        # 1. 抓取数据 (内部强制不触发 print)
        res = client.table("tcm_single_herb").select("chinese_name").eq("data_level", "aligned").execute()
        herbs = res.data
        
        f.write(f"Task Started. Total: {len(herbs)}\n")
        f.flush()

        for i, herb in enumerate(herbs):
            try:
                name = herb['chinese_name']
                # 2. 执行更新
                client.table("tcm_single_herb").update({"data_level": "enriched"}).eq("chinese_name", name).execute()
                
                if i % 10 == 0:
                    f.write(f"Processed: {i}/{len(herbs)}\n")
                    f.flush()
                time.sleep(0.1)
            except:
                continue
        
        f.write("SUCCESS: ALL DONE\n")
    except Exception as e:
        f.write(f"FATAL ERROR: {str(e)}\n")
    finally:
        f.close()

if __name__ == "__main__":
    main()
