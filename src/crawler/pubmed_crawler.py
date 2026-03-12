#!/usr/bin/env python3
import os, time, requests

KEYWORDS = [
    # 核心主题
    "exosome traditional chinese medicine",
    "exosome TCM herb",
    "extracellular vesicles chinese medicine",
    "plant derived exosome nanoparticles",
    "plant exosome anti-inflammatory",

    # 具体中药
    "exosome astragalus membranaceus",
    "exosome berberine",
    "exosome curcumin",
    "exosome ginger zingiber",
    "exosome ginseng panax",
    "exosome resveratrol",
    "exosome salvia miltiorrhiza",
    "exosome angelica sinensis",
    "exosome scutellaria baicalensis",
    "exosome glycyrrhiza licorice",
    "exosome rheum rhubarb",
    "exosome lonicera japonica",
    "exosome cordyceps sinensis",
    "exosome lycium barbarum",
    "exosome bupleurum",
    "exosome panax notoginseng",
    "exosome atractylodes",
    "exosome coptis chinensis",

    # 疾病方向
    "TCM exosome cancer tumor",
    "TCM exosome liver disease",
    "TCM exosome cardiovascular",
    "TCM exosome neurological",
    "TCM exosome diabetes",
    "TCM exosome inflammation",
    "TCM exosome kidney disease",
    "TCM exosome lung disease",
    "TCM exosome autism spectrum",
    "TCM exosome Alzheimer",

    # 机制方向
    "plant exosome miRNA delivery",
    "herbal exosome drug delivery",
    "TCM exosome immune regulation",
    "plant nanoparticles gut microbiota",
    "herbal extracellular vesicles wound healing",
    "TCM exosome apoptosis",
    "TCM exosome angiogenesis VEGF",
    "herbal medicine exosome biomarker",

    # 外泌体通用
    "exosome nanoparticles drug delivery TCM",
    "extracellular vesicles herbal medicine",
    "exosome microRNA traditional medicine",
    "plant derived nanoparticles anti-cancer",
    "exosome stem cell traditional medicine",
]

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

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

def search_pubmed(query, retmax=100):
    try:
        params = {
            "db": "pubmed", "term": query,
            "retmax": retmax, "retmode": "json",
            "sort": "relevance",
        }
        r = requests.get(PUBMED_SEARCH, params=params, timeout=15)
        data = r.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"  Search error: {e}")
        return []

def fetch_summaries(pmids):
    if not pmids:
        return []
    results = []
    try:
        params = {
            "db": "pubmed", "id": ",".join(pmids),
            "retmode": "json",
        }
        r = requests.get(PUBMED_SUMMARY, params=params, timeout=20)
        data = r.json()
        uids = data.get("result", {}).get("uids", [])
        for uid in uids:
            article = data["result"].get(uid, {})
            authors_list = article.get("authors", [])
            authors = ", ".join([a.get("name", "") for a in authors_list[:5]])
            pub_date = article.get("pubdate", "")[:10]
            results.append({
                "title": article.get("title", ""),
                "authors": authors,
                "abstract": "",
                "pub_date": pub_date,
                "doi": next((a.get("value") for a in article.get("articleids", []) if a.get("idtype") == "doi"), None),
                "pmid": uid,
                "source": "PubMed",
                "keywords": "",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
            })
    except Exception as e:
        print(f"  Fetch error: {e}")
    return results

def save_papers_supabase(client, papers):
    added = 0
    data = []
    for p in papers:
        data.append({
            "title": p["title"],
            "authors": p.get("authors", ""),
            "abstract": p.get("abstract", ""),
            "doi": p.get("doi"),
            "pmid": p.get("pmid"),
            "source": p.get("source", "PubMed"),
            "pub_date": p.get("pub_date", ""),
            "url": p.get("url", ""),
            "keywords": p.get("keywords", ""),
        })
    try:
        for i in range(0, len(data), 50):
            client.table("research_papers").upsert(
                data[i:i+50], on_conflict="pmid"
            ).execute()
            added += len(data[i:i+50])
    except Exception as e:
        print(f"  Supabase error: {e}")
    try:
        client.table("crawler_logs").insert({
            "source": "PubMed",
            "status": "success",
            "records_found": len(papers),
            "records_added": added
        }).execute()
    except:
        pass
    return added

def save_papers_sqlite(papers):
    try:
        from src.database.init_db import get_connection
        conn = get_connection()
        c = conn.cursor()
        added = 0
        for p in papers:
            try:
                c.execute("""INSERT OR IGNORE INTO research_papers
                    (title, authors, abstract, pub_date, doi, pmid, source, keywords, url)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (p["title"], p.get("authors",""), p.get("abstract",""),
                     p.get("pub_date",""), p.get("doi"), p.get("pmid"),
                     p.get("source","PubMed"), p.get("keywords",""), p.get("url","")))
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

def save_papers(papers):
    client = get_supabase_client()
    if client:
        return save_papers_supabase(client, papers)
    else:
        return save_papers_sqlite(papers)

def run():
    print("Starting PubMed crawler...")
    total_added = 0
    for kw in KEYWORDS:
        print(f"  Query: {kw}")
        pmids = search_pubmed(kw, retmax=100)
        print(f"    Found {len(pmids)} IDs")
        if pmids:
            papers = fetch_summaries(pmids)
            added = save_papers(papers)
            total_added += added
            print(f"    Added {added} new papers")
        time.sleep(0.4)
    print(f"PubMed done. Total new: {total_added}")
    return total_added

if __name__ == "__main__":
    run()
