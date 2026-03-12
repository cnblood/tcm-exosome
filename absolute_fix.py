import sys
import io

# 强制锁死整个运行环境为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
from supabase import create_client

def main():
    # 彻底弃用环境变量，直接在这里写死字符串
    # 并在字符串前加 'u' 确保它们是 unicode 对象
    url = uos.environ.get("SUPABASE_URL")
    key = u"你的_SERVICE_ROLE_KEY_粘贴在这里"

    print("--- SYSTEM DEBUG ---")
    print(f"Python Version: {sys.version}")
    
    try:
        # 手动创建 client，跳过一切自动检测逻辑
        client = create_client(url, key)
        
        print("Connecting to Supabase...")
        
        # 尝试最基础的数字更新测试 (假设 ID 为 1)
        # 我们甚至不进行 select，直接尝试 update 一个范围
        # 这是为了测试到底是不是 HTTP 通讯层崩了
        try:
            # 这里的 .filter 是 Supabase 最底层的调用方式，绕过所有中文检索
            res = client.table("tcm_single_herb").update({"data_level": "enriched"}).filter("data_level", "eq", "aligned").execute()
            print("SUCCESS: Remote server accepted the batch update command!")
        except Exception as e:
            # 如果这里还报 ASCII 错误，那就是你电脑里的 httpx 库或者 ssl 库坏了
            print(f"Remote Update Error: {str(e)}")

    except Exception as e:
        print(f"Fatal Initialization Error: {str(e)}")

if __name__ == "__main__":
    main()

