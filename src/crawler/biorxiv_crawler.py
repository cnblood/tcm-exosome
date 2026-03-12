import requests
import time
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def get_supabase_client():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            pass
    return None

def fetch_recent(server="biorxiv", interval="2024-01-01/2025-12-31", cursor=0):
    url = f"https://api.biorxiv.org/details/{server}/{interval}/{cursor}/json"
    try:
        r = requests.get(url, timeout=20)
        data = r.json()
        return data.get("collection", []), data.get("messages", [{}])[0].get("total", 0)
    except Exception as e:
        print(f"  Error: {e}")
        return [], 0

def is_relevant(paper):
    text = (paper.get("title","") + " " + paper.get("abstract","")).lower()
    tcm_terms = ["exosome","extracellular vesicle","traditional chinese","herbal","tcm","acupuncture","herb"]
    return any(t in text for t in tcm_terms)

def save_papers_supabase(client, papers, source):
    data = []
    for p in papers:
        if not is_relevant(p):
            continue
        doi = p.get("doi","")
        data.append({
            "title": p.get("title",""),
            "authors": p.get("authors",""),
            "abstract": p.get("abstract",""),
            "doi": doi if doi else None,
            "source": source,
            "pub_date": p.get("date",""),
            "keywords": p.get("category",""),
            "url": f"https://doi.org/{doi}" if doi else "",
            "pmid": None,
        })
    if not data:
        return 0
    added = 0
    try:
        for i in range(0, len(data), 50):
            client.table("research_papers").upsert(data[i:i+50], on_conflict="doi").execute()
            added += len(data[i:i+50])
        client.table("crawler_logs").insert({
            "source": source, "status": "success",
            "records_found": len(papers), "records_added": added
        }).execute()
    except Exception as e:
        print(f"  Supabase error: {e}")
    return added

def save_papers_sqlite(papers, source):
    try:
        from src.database.init_db import get_connection
        conn = get_connection()
        c = conn.cursor()
        added = 0
        for p in papers:
            if not is_relevant(p):
                continue
            doi = p.get("doi","")
            try:
                c.execute("""
                    INSERT OR IGNORE INTO research_papers
                    (title, authors, abstract, pub_date, doi, source, keywords, url)
                    VALUES (?,?,?,?,?,?,?,?)
                """, (p.get("title",""), p.get("authors",""), p.get("abstract",""),
                      p.get("date",""), doi if doi else None, source,
                      p.get("category",""), f"https://doi.org/{doi}" if doi else ""))
                if c.rowcount > 0:
                    added += 1
            except Exception as e:
                print(f"  DB: {e}")
        conn.commit()
        conn.close()
        return added
    except Exception as e:
        print(f"  SQLite error: {e}")
        return 0

def save_papers(papers, source):
    client = get_supabase_client()
    if client:
        return save_papers_supabase(client, papers, source)
    return save_papers_sqlite(papers, source)

def run():
    print("🔍 Starting bioRxiv/medRxiv crawler...")
    total = 0
    for server in ["biorxiv", "medrxiv"]:
        print(f"  Server: {server}")
        papers, count = fetch_recent(server)
        print(f"    Fetched {len(papers)} papers")
        added = save_papers(papers, server)
        total += added
        print(f"    Relevant & added: {added}")
        time.sleep(2)
    print(f"✅ bioRxiv/medRxiv done. Total new: {total}")
    return total

if __name__ == "__main__":
    run()
