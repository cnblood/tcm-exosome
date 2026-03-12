#!/usr/bin/env python3
"""
中文文献爬虫 - 爬取中文外泌体+中医药相关文献
数据源：
  1. PubMed中文摘要（作者为中国机构）
  2. Europe PMC 中文关键词
  3. 百度学术公开接口
  4. 语义学者 Semantic Scholar（支持中文关键词）
"""
import os, time, requests, re

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# 中文关键词（用于PubMed/EuropePMC的中文作者搜索）
CHINESE_KEYWORDS_EN = [
    # 中药+外泌体 中文机构发表的英文文献
    "exosome traditional chinese medicine China",
    "extracellular vesicles herbal China",
    "plant exosome China university",
    "exosome acupuncture China",
    "TCM exosome Shanghai Beijing",

    # 具体中药英文检索（中国研究者发表）
    "astragalus exosome Chinese hospital",
    "berberine exosome China",
    "curcumin extracellular vesicles China",
    "ginseng exosome China institute",
    "salvia miltiorrhiza exosome",
    "angelica sinensis extracellular vesicles",
    "scutellaria baicalensis exosome",
    "panax notoginseng exosome",
    "lonicera japonica exosome",
    "cordyceps sinensis exosome",

    # 疾病+中药+外泌体
    "exosome liver fibrosis traditional chinese",
    "exosome stroke TCM China",
    "exosome cancer herb China",
    "exosome diabetes traditional medicine China",
    "exosome inflammation herbal China",

    # 外泌体药物递送+中药
    "plant derived nanoparticles drug delivery China",
    "exosome drug delivery herbal active compound",
    "nanoparticle ginger turmeric delivery",
]

# Semantic Scholar API（免费，支持大量文献）
SEMANTIC_SCHOLAR_KEYWORDS = [
    "exosome traditional chinese medicine",
    "plant derived exosome nanoparticles therapy",
    "herbal medicine extracellular vesicles",
    "TCM exosome cancer treatment",
    "plant exosome miRNA drug delivery",
    "astragalus polysaccharide exosome",
    "berberine exosome apoptosis",
    "curcumin nanoparticle exosome",
]

def get_supabase_client():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except:
            pass
    return None

def search_europepmc_chinese(query, page_size=100):
    """Europe PMC 支持中文机构过滤"""
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size,
        "resultType": "core",
        "sort": "CITED desc",
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
        results = []
        for item in data.get("resultList", {}).get("result", []):
            pmid = item.get("pmid", "")
            doi = item.get("doi", "")
            results.append({
                "title": item.get("title", "").rstrip("."),
                "authors": ", ".join([
                    a.get("fullName", "") for a in
                    item.get("authorList", {}).get("author", [])[:5]
                ]),
                "abstract": item.get("abstractText", ""),
                "pub_date": str(item.get("pubYear", ""))[:10],
                "doi": doi if doi else None,
                "pmid": pmid if pmid else None,
                "source": "EuropePMC_CN",
                "keywords": query,
                "url": f"https://europepmc.org/article/MED/{pmid}" if pmid else
                       f"https://doi.org/{doi}" if doi else "",
            })
        return results
    except Exception as e:
        print(f"  EuropePMC error: {e}")
        return []

def search_semantic_scholar(query, limit=100):
    """Semantic Scholar 免费API"""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,abstract,year,externalIds,url",
    }
    headers = {"User-Agent": "TCM-Exosome-Research/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        if r.status_code != 200:
            return []
        data = r.json()
        results = []
        for item in data.get("data", []):
            ext_ids = item.get("externalIds", {})
            pmid = ext_ids.get("PubMed", "")
            doi = ext_ids.get("DOI", "")
            authors = ", ".join([
                a.get("name", "") for a in item.get("authors", [])[:5]
            ])
            pub_year = item.get("year", "")
            results.append({
                "title": item.get("title", ""),
                "authors": authors,
                "abstract": item.get("abstract", "") or "",
                "pub_date": str(pub_year) if pub_year else "",
                "doi": doi if doi else None,
                "pmid": str(pmid) if pmid else None,
                "source": "SemanticScholar",
                "keywords": query,
                "url": item.get("url", "") or
                       (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""),
            })
        return results
    except Exception as e:
        print(f"  Semantic Scholar error: {e}")
        return []

def save_papers(papers):
    """保存到Supabase或SQLite"""
    if not papers:
        return 0

    client = get_supabase_client()
    if client:
        return _save_supabase(client, papers)
    else:
        return _save_sqlite(papers)

def _save_supabase(client, papers):
    added = 0
    # 按pmid去重，没有pmid的用doi
    data = []
    for p in papers:
        if not p.get("title"):
            continue
        record = {
            "title": p["title"][:500],
            "authors": p.get("authors", "")[:500],
            "abstract": p.get("abstract", "")[:2000],
            "doi": p.get("doi"),
            "pmid": p.get("pmid"),
            "source": p.get("source", "Unknown"),
            "pub_date": p.get("pub_date", "")[:10],
            "url": p.get("url", "")[:500],
            "keywords": p.get("keywords", "")[:200],
        }
        data.append(record)

    # 有pmid的用pmid去重
    pmid_records = [d for d in data if d.get("pmid")]
    no_pmid_records = [d for d in data if not d.get("pmid")]

    try:
        if pmid_records:
            for i in range(0, len(pmid_records), 50):
                client.table("research_papers").upsert(
                    pmid_records[i:i+50], on_conflict="pmid"
                ).execute()
                added += len(pmid_records[i:i+50])

        if no_pmid_records:
            # 无pmid的直接insert，用title去重
            for i in range(0, len(no_pmid_records), 50):
                batch = no_pmid_records[i:i+50]
                # 去掉pmid字段避免null冲突
                for r in batch:
                    r.pop("pmid", None)
                try:
                    client.table("research_papers").upsert(
                        batch, on_conflict="doi"
                    ).execute()
                    added += len(batch)
                except:
                    pass
    except Exception as e:
        print(f"  Save error: {e}")

    try:
        client.table("crawler_logs").insert({
            "source": "ChineseCrawler",
            "status": "success",
            "records_found": len(papers),
            "records_added": added
        }).execute()
    except:
        pass

    return added

def _save_sqlite(papers):
    try:
        import sqlite3
        db = os.environ.get("DB_PATH", "data/tcm_exosome.db")
        conn = sqlite3.connect(db)
        c = conn.cursor()
        added = 0
        for p in papers:
            if not p.get("title"):
                continue
            try:
                c.execute("""INSERT OR IGNORE INTO research_papers
                    (title, authors, abstract, pub_date, doi, pmid, source, keywords, url)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (p["title"][:500], p.get("authors","")[:500],
                     p.get("abstract","")[:2000], p.get("pub_date","")[:10],
                     p.get("doi"), p.get("pmid"),
                     p.get("source","Unknown"), p.get("keywords","")[:200],
                     p.get("url","")[:500]))
                if c.rowcount > 0:
                    added += 1
            except Exception as e:
                pass
        conn.commit()
        conn.close()
        return added
    except Exception as e:
        print(f"  SQLite error: {e}")
        return 0

def run():
    print("Starting Chinese Literature Crawler...")
    total_added = 0

    # 1. EuropePMC 中文机构检索
    print("\n[1/2] EuropePMC Chinese Institution Search")
    for kw in CHINESE_KEYWORDS_EN:
        print(f"  Query: {kw}")
        papers = search_europepmc_chinese(kw, page_size=50)
        if papers:
            added = save_papers(papers)
            total_added += added
            print(f"    Found {len(papers)}, Added {added}")
        time.sleep(0.5)

    # 2. Semantic Scholar
    print("\n[2/2] Semantic Scholar Search")
    for kw in SEMANTIC_SCHOLAR_KEYWORDS:
        print(f"  Query: {kw}")
        papers = search_semantic_scholar(kw, limit=50)
        if papers:
            added = save_papers(papers)
            total_added += added
            print(f"    Found {len(papers)}, Added {added}")
        time.sleep(1.0)  # Semantic Scholar有频率限制

    print(f"\nChinese Crawler done. Total new: {total_added}")
    return total_added

if __name__ == "__main__":
    run()
