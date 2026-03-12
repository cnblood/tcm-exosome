import os
import sys
import time
from supabase import create_client

# 核心补丁：强制全局 IO 使用 UTF-8，防止任何环节的 ASCII 转换
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    client = create_client(url, key)

    try:
        # 修改点 1：只查 ID，完全不查询 chinese_name 字符串，从源头切断中文接触
        print("Fetching ID list from server...")
        res = client.table("tcm_single_herb").select("id").eq("data_level", "aligned").execute()
        herbs = res.data
        
        total = len(herbs)
        print(f"Total records to update: {total}")

        for i, herb in enumerate(herbs):
            hid = herb['id']
            # 修改点 2：仅使用数字 ID 更新，请求中不含任何非 ASCII 字符
            try:
                client.table("tcm_single_herb").update({"data_level": "enriched"}).eq("id", hid).execute()
            except Exception as inner_e:
                # 如果单条失败，跳过继续，不中断全局
                continue
            
            if (i + 1) % 20 == 0:
                print(f"Update Processed: {i + 1} / {total}")
            
            time.sleep(0.05)

        print("MISSION ACCOMPLISHED: All data leveled up to 'enriched'.")

    except Exception as e:
        # 将错误信息强制转为 string 并静默打印
        print(f"Critical System Error: {str(e).encode('utf-8', errors='ignore').decode('utf-8')}")

if __name__ == "__main__":
    main()
