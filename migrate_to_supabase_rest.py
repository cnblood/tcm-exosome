import os
import sqlite3

SQLITE_PATH = os.environ.get("DB_PATH", "data/tcm_exosome.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

TABLES = ["research_papers","clinical_trials","herb_target_relations","tcm_exosome_relations","crawler_logs","genes","mirna","herb_gene_relations","exosome_cargo","pathway_enrichment","disease_gene_network","network_nodes","network_edges"]

def migrate():
    try:
        from supabase import create_client
    except ImportError:
        print("请先安装: pip install supabase")
        return
    print(f"来源: {SQLITE_PATH}")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    for table in TABLES:
        check = sqlite_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        if not check:
            print(f"  跳过 {table}: 不存在")
            continue
        rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  跳过 {table}: 空表")
            continue
        data = [{k: v for k, v in dict(row).items() if k != "id"} for row in rows]
        inserted = 0
        for i in range(0, len(data), 50):
            try:
                client.table(table).upsert(data[i:i+50]).execute()
                inserted += len(data[i:i+50])
            except Exception as e:
                print(f"  错误 {table}: {e}")
        print(f"  完成 {table}: {inserted} 条")
    sqlite_conn.close()
    print("迁移完成!")

if __name__ == "__main__":
    migrate()


