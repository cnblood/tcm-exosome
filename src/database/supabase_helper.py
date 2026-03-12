"""
src/database/supabase_helper.py
共享的 Supabase 工具函数，供所有爬虫使用。
"""
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_client = None

def get_supabase_client():
    global _client
    if _client:
        return _client
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
            return _client
        except ImportError:
            print("  ⚠️  supabase 未安装，回退到 SQLite")
    return None

def log_crawl(source, status, found, added, error=None):
    client = get_supabase_client()
    if client:
        try:
            client.table("crawler_logs").insert({
                "source": source,
                "status": status,
                "records_found": found,
                "records_added": added,
                "error_message": error
            }).execute()
        except Exception as e:
            print(f"  Log error: {e}")

def upsert_batch(table, data, on_conflict=None):
    """批量写入 Supabase，返回写入条数"""
    client = get_supabase_client()
    if not client or not data:
        return 0
    added = 0
    for i in range(0, len(data), 50):
        batch = data[i:i+50]
        try:
            if on_conflict:
                client.table(table).upsert(batch, on_conflict=on_conflict).execute()
            else:
                client.table(table).upsert(batch).execute()
            added += len(batch)
        except Exception as e:
            print(f"  Supabase upsert error ({table}): {e}")
    return added
