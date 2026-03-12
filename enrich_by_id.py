import os
import sys
from supabase import create_client
import time

def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing SUPABASE_URL or KEY")
        return

    client = create_client(url, key)

    try:
        # 关键修改 1：不仅查出中文名，同时查出它对应的数字 id！
        res = client.table("tcm_single_herb").select("id, chinese_name").eq("data_level", "aligned").execute()
        herbs = res.data
        
        total = len(herbs)
        print(f"Found {total} records to process.")

        for i, herb in enumerate(herbs):
            herb_id = herb['id']
            
            # 关键修改 2：使用数字 id 作为更新条件，彻底避免 URL 包含中文字符！
            client.table("tcm_single_herb").update({"data_level": "enriched"}).eq("id", herb_id).execute()
            
            if (i + 1) % 20 == 0:
                print(f"Progress: {i + 1} / {total}")
            
            time.sleep(0.1)

        print("SUCCESS: All updates finished perfectly!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
