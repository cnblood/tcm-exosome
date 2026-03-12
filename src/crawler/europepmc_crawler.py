import requests
import time
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

QUERIES = [
    "exosome traditional chinese medicine",
    "exosome herbal medicine",
    "plant exosome therapy",
    "exosome acupuncture moxibustion",
    "extracellular vesicles TCM",
    "exosome ginger curcumin",
    "exosome astragalus cancer",
    "exosome berberine inflammation",
]

def get_supabase_client():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            pass
    return None

def search_europepmc(query, page_size=50):
    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size,
        "resultType": "core",
        "sort": "CITED desc"
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=20)
        data = r.json()
        return data.get("resultList", {}).get("result", [])
    except Exception as e:
        print(f"  Error: {e}")
        return []

def parse_results(results, query):
    data = []
    for item in results:
        title = item.get("title", "")
        if not title:
            continue
        data.append({
            "title": title,
            "authors": item.get("authorString", ""),
            "abstract": item.get("abstractText", ""),
            "doi": item.get("doi", None),
            "pmid": item.get("pmid", None),
            "source": "EuropePMC",
            "pub_date": str(item.get("pubYear", "")),
            "keywords": query,
            "url": f"https://europepmc.org/article/{item.get('source','MED')}/{item.get('id','')}",
        })
    return data

def save_papers_supabase(client, results, query):
    data = parse_results(results, query)
    if not data:
        return 0
    added = 0
    try:
        for i in range(0, len(data), 50):
            client.table("research_papers").upsert(data[i:i+50], on_conflict="pmid").execute()
            added += len(data[i:i+50])
        client.table("crawler_logs").insert({
            "source": "EuropePMC", "status": "success",
            "records_found": len(results), "records_added": added
        }).execute()
    except Exception as e:
        print(f"  Supabase error: {e}")
    return added

def save_papers_sqlite(results, query):
    try:
        from src.database.init_db import get_connection
        conn = get_connection()
        c = conn.cursor()
        data = parse_results(results, query)
        added = 0
        for p in data:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO research_papers
                    (title, authors, abstract, pub_date, doi, pmid, source, keywords, url)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (p["title"], p["authors"], p["abstract"], p["pub_date"],
                      p["doi"], p["pmid"], p["source"], p["keywords"], p["url"]))
                if c.rowcount > 0:
                    added += 1
            except Exception as e:
                print(f"  DB error: {e}")
        conn.commit()
        conn.close()
        return added
    except Exception as e:
        print(f"  SQLite error: {e}")
        return 0

def save_papers(results, query):
    client = get_supabase_client()
    if client:
        return save_papers_supabase(client, results, query)
    return save_papers_sqlite(results, query)

def run():
    print("🔍 Starting EuropePMC crawler...")
    total = 0
    for q in QUERIES:
        print(f"  Query: {q}")
        results = search_europepmc(q)
        print(f"    Found {len(results)}")
        added = save_papers(results, q)
        total += added
        print(f"    Added {added}")
        time.sleep(1)
    print(f"✅ EuropePMC done. Total new: {total}")
    return total

if __name__ == "__main__":
    run()
