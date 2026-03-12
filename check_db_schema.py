import os
from supabase import create_client

def main():
    url = os.environ.get("SUPABASE_URL")
    key = "sb_publishable_egJtK5qOnELNDhE64x01Ow_qzQskrmR" 
    supabase = create_client(url, key)

    try:
        # 1. 尝试拉取所有字段，不带任何过滤条件
        print("--- Scanning Table Structure ---")
        res = supabase.table("tcm_single_herb").select("*").limit(3).execute()
        
        if res.data:
            print("Successfully found data!")
            print("First record structure:")
            import json
            print(json.dumps(res.data[0], indent=2, ensure_ascii=False))
            
            # 2. 统计不同 data_level 的分布情况
            print("\n--- Data Level Distribution ---")
            all_res = supabase.table("tcm_single_herb").select("data_level").execute()
            levels = [str(d['data_level']) for d in all_res.data]
            from collections import Counter
            print(Counter(levels))
        else:
            print("Table is empty.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

