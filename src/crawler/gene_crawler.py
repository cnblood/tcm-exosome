import requests
import time
import sys, os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 设置路径
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

TCM_EXOSOME_GENES = [
    "TNF", "IL6", "IL1B", "IL10", "NFKB1", "STAT3", "TLR4",
    "TP53", "BCL2", "BAX", "CASP3", "CASP9",
    "VEGFA", "HIF1A", "MMP2", "MMP9",
    "PIK3CA", "AKT1", "MTOR", "PTEN",
    "MAPK1", "MAPK3", "EGFR", "KRAS",
    "SHANK3", "NLGN3", "NRXN1", "MECP2", "FMR1",
    "RAB27A", "RAB27B", "ALIX", "TSG101", "CD63", "CD9", "CD81",
    "CYP1A2", "CYP3A4", "PTGS2", "NOS2", "HMOX1",
    "DNMT1", "HDAC1", "SIRT1",
    "DICER1", "DROSHA", "AGO2",
]

NCBI_ESEARCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
UNIPROT_API   = "https://rest.uniprot.org/uniprotkb/search"

# 创建带重试机制的 Session，解决 SSL 和连接中断问题
def get_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

session = get_session()

def get_supabase_client():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            pass
    return None

def fetch_gene_info_ncbi(gene_symbol):
    try:
        # 1. 搜索基因 ID
        r = session.get(NCBI_ESEARCH, params={
            "db": "gene", "term": f"{gene_symbol}[Gene Name] AND Homo sapiens[Organism]",
            "retmax": 1, "retmode": "json"
        }, timeout=20)
        
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return None
        
        gene_id = ids[0]
        time.sleep(1.0) # NCBI 频率限制：无 Key 建议每秒不超过 3 次
        
        # 2. 获取基因详情
        r2 = session.get(NCBI_ESUMMARY, params={
            "db": "gene", "id": gene_id, "retmode": "json"
        }, timeout=20)
        
        result_data = r2.json().get("result", {}).get(gene_id, {})
        
        return {
            "gene_symbol": gene_symbol,
            "gene_name": result_data.get("description", ""),
            "ncbi_gene_id": gene_id,
            "chromosome": result_data.get("chromosome", ""),
            # 这里的 summary 才是核心功能描述
            "description": result_data.get("summary", "")[:1000] if result_data.get("summary") else "",
            # 备选：如果 summary 为空，使用 aliases
            "function_summary": result_data.get("summary", "")[:500] if result_data.get("summary") else result_data.get("otheraliases", "")
        }
    except Exception as e:
        print(f"    NCBI connection error for {gene_symbol}: {e}")
        return None

def fetch_uniprot_id(gene_symbol):
    try:
        r = session.get(UNIPROT_API, params={
            "query": f"gene_exact:{gene_symbol} AND organism_id:9606 AND reviewed:true",
            "format": "json", "size": 1,
            "fields": "accession,id,protein_name"
        }, timeout=15)
        results = r.json().get("results", [])
        if results:
            return results[0].get("primaryAccession", "")
    except Exception:
        pass
    return ""

def save_gene_supabase(client, gene_data):
    try:
        # 即使 Supabase 报错缺失字段，这里也会捕获错误并跳过，不影响脚本运行
        client.table("genes").upsert(gene_data, on_conflict="gene_symbol").execute()
        return True
    except Exception as e:
        print(f"    Supabase error (可能需要运行 ALTER TABLE): {e}")
        return False

def save_gene_sqlite(gene_data):
    try:
        from src.database.init_db import get_connection
        conn = get_connection()
        c = conn.cursor()
        # 确保 SQLite 表结构一致
        c.execute("""
            INSERT OR REPLACE INTO genes 
            (gene_symbol, gene_name, ncbi_gene_id, uniprot_id, chromosome, description, function_summary)
            VALUES (?,?,?,?,?,?,?)
        """, (
            gene_data["gene_symbol"], 
            gene_data.get("gene_name",""),
            gene_data.get("ncbi_gene_id",""), 
            gene_data.get("uniprot_id",""),
            gene_data.get("chromosome",""), 
            gene_data.get("description",""),
            gene_data.get("function_summary","")
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"    SQLite DB error: {e}")
        return False

def run():
    print("🧬 Starting Robust NCBI Gene crawler...")
    client = get_supabase_client()
    if client:
        print("🔗 Supabase client connected.")
    
    added = 0
    for i, gene in enumerate(TCM_EXOSOME_GENES):
        print(f"  [{i+1}/{len(TCM_EXOSOME_GENES)}] {gene}")
        
        info = fetch_gene_info_ncbi(gene)
        if info:
            info["uniprot_id"] = fetch_uniprot_id(gene)
            
            # 同时存入两个数据库以保持同步
            sqlite_ok = save_gene_sqlite(info)
            supabase_ok = False
            if client:
                supabase_ok = save_gene_supabase(client, info)
            
            if sqlite_ok or supabase_ok:
                added += 1
                status = "Both" if (sqlite_ok and supabase_ok) else ("SQLite" if sqlite_ok else "Supabase")
                print(f"    ✓ Saved to {status}: {info['gene_name'][:40]}...")
        
        # 严格遵守 API 访问间隔
        time.sleep(1.2)
        
    print(f"\n✅ Gene crawler done. Total records processed: {added}")
    return added

if __name__ == "__main__":
    run()