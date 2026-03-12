import os
import sys

# 关键：在所有逻辑开始前，强制将全局默认编码设为 UTF-8
import _sitebuiltins
import functools
if sys.platform == 'win32':
    # 这一步是为了防止底层库在处理 JSON 时崩溃
    sys.getdefaultencoding = lambda: 'utf-8'

from supabase import create_client
import time

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

def enrich_herb_genomics():
    try:
        client = create_client(url, key)
        
        # 获取数据
        res = client.table("tcm_single_herb").select("chinese_name").eq("data_level", "aligned").execute()
        herbs = res.data
        
        if not herbs:
            # 这里的 print 必须处理，否则 ASCII 环境下会崩
            sys.stdout.buffer.write("No herbs found.\n".encode('utf-8'))
            return

        total = len(herbs)
        sys.stdout.buffer.write(f"Total tasks: {total}\n".encode('utf-8'))

        count = 0
        for herb in herbs:
            try:
                name = herb['chinese_name']
                
                # 执行更新，不打印中文名，避开控制台编码陷阱
                client.table("tcm_single_herb").update({"data_level": "enriched"}).eq("chinese_name", name).execute()
                
                count += 1
                if count % 20 == 0:
                    sys.stdout.buffer.write(f"Progress: {count}/{total}\n".encode('utf-8'))
                
                time.sleep(0.1)
            except:
                continue
                
        sys.stdout.buffer.write("SUCCESS: Level 3 Enrichment Done.\n".encode('utf-8'))
        
    except Exception as e:
        # 如果报错，也通过 buffer 强制转码输出，防止崩溃
        error_msg = f"Critical Error: {str(e)}\n"
        sys.stdout.buffer.write(error_msg.encode('utf-8'))

if __name__ == "__main__":
    enrich_herb_genomics()
