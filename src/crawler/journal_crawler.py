#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外泌体专业期刊爬虫
针对顶级EV期刊，抓取所有相关文章（不限于TCM关键词）
运行：python src/crawler/journal_crawler.py
"""
import os, time, requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "research@tcm-exosome.com")

# 顶级外泌体/细胞外囊泡期刊 + 搜索策略
# 格式: (期刊名, PubMed期刊缩写或全名, 附加关键词过滤)
JOURNALS = [
    # 专业EV期刊
    ("Journal of Extracellular Vesicles",   "J Extracell Vesicles",        ""),
    ("Extracellular Vesicles and Circulating Nucleic Acids", "Extracell Vesicles Circ Nucleic Acids", ""),
    ("Journal of Extracellular Biology",    "J Extracell Biol",            ""),
    ("Small",                               "Small",                       "exosome OR extracellular vesicle"),
    ("Theranostics",                        "Theranostics",                "exosome OR extracellular vesicle"),
    ("ACS Nano",                            "ACS Nano",                    "exosome OR extracellular vesicle"),
    ("Nanoscale",                           "Nanoscale",                   "exosome OR extracellular vesicle"),
    ("Biomaterials",                        "Biomaterials",                "exosome OR extracellular vesicle"),
    ("Journal of Controlled Release",       "J Control Release",           "exosome OR extracellular vesicle"),
    ("Advanced Materials",                  "Adv Mater",                   "exosome OR extracellular vesicle"),
    # 高影响综合期刊（EV相关）
    ("Nature Communications",              "Nat Commun",                  "exosome AND (TCM OR herbal OR traditional chinese medicine)"),
    ("Science Advances",                   "Sci Adv",                     "exosome AND (TCM OR herbal OR plant-derived)"),
    ("Cell Reports",                       "Cell Rep",                    "exosome AND (TCM OR herbal OR plant)"),
    ("Molecular Therapy",                  "Mol Ther",                    "exosome OR extracellular vesicle"),
    ("Journal of Nanobiotechnology",       "J Nanobiotechnology",         "exosome OR extracellular vesicle"),
    # 中医药+EV交叉期刊
    ("Phytomedicine",                      "Phytomedicine",               "exosome OR extracellular vesicle OR nanoparticle"),
    ("Phytotherapy Research",              "Phytother Res",               "exosome OR extracellular vesicle"),
    ("Journal of Ethnopharmacology",       "J Ethnopharmacol",            "exosome OR extracellular vesicle OR nanoparticle"),
    ("Chinese Medicine",                   "Chin Med",                    "exosome OR extracellular vesicle"),
    ("Chinese Journal of Natural Medicines","Chin J Nat Med",             "exosome OR extracellular vesicle"),
    ("Journal of Integrative Medicine",    "J Integr Med",                "exosome OR extracellular vesicle"),
    ("Frontiers in Pharmacology",          "Front Pharmacol",             "exosome AND (TCM OR herbal OR plant)"),
    # 癌症/疾病高分期刊
    ("Cancer Letters",                     "Cancer Lett",                 "exosome AND (herb OR plant OR TCM OR traditional)"),
    ("Biomedicine & Pharmacotherapy",      "Biomed Pharmacother",         "exosome AND (herb OR plant OR TCM)"),
    ("International Journal of Nanomedicine","Int J Nanomedicine",        "exosome OR extracellular vesicle"),
]

def search_pubmed_journal(journal_abbr, extra_query="", retmax=200, min_year=2015):
    """按期刊名搜索PubMed"""
    base = f'"{journal_abbr}"[Journal]'
    if extra_query:
        query = f'({base}) AND ({extra_query})'
    else:
        query = base
    query += f' AND {min_year}:{2026}[PDAT]'

    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed", "term": query,
        "retmax": retmax, "retmode": "json",
        "email": NCBI_EMAIL, "tool": "tcm-exosome-journal-crawler"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        total = data.get("esearchresult", {}).get("count", 0)
        return ids, int(total)
    except Exception as e:
        print(f"    Search error: {e}")
        return [], 0

def fetch_details(pmids):
    """批量获取文章详情"""
    if not pmids:
        return []
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed", "id": ",".join(pmids),
        "rettype": "xml", "retmode": "xml",
        "email": NCBI_EMAIL
    }
    try:
        r = requests.get(url, params=params, timeout=60)
        return parse_xml(r.text)
    except Exception as e:
        print(f"    Fetch error: {e}")
        return []

def parse_xml(xml_text):
    """解析PubMed XML"""
    import xml.etree.ElementTree as ET
    results = []
    try:
        root = ET.fromstring(xml_text)
    except:
        return results

    for article in root.findall(".//PubmedArticle"):
        try:
            # PMID
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""

            # Title
            title_el = article.find(".//ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else ""

            # Abstract
            abstract_parts = article.findall(".//AbstractText")
            abstract = " ".join("".join(p.itertext()) for p in abstract_parts)

            # Authors
            authors = []
            for author in article.findall(".//Author"):
                ln = author.find("LastName")
                fn = author.find("ForeName")
                if ln is not None:
                    name = ln.text + (" " + fn.text if fn is not None else "")
                    authors.append(name)
            authors_str = ", ".join(authors[:6]) + (" et al." if len(authors) > 6 else "")

            # Date
            pub_date = ""
            year_el = article.find(".//PubDate/Year")
            month_el = article.find(".//PubDate/Month")
            if year_el is not None:
                pub_date = year_el.text
                if month_el is not None:
                    pub_date += f" {month_el.text}"

            # Journal
            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else ""

            # DOI
            doi = ""
            for aid in article.findall(".//ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = aid.text
                    break

            # Keywords
            kws = [k.text for k in article.findall(".//Keyword") if k.text]
            keywords = "; ".join(kws[:10])

            if title and len(title) > 10:
                results.append({
                    "title": title[:500],
                    "authors": authors_str[:300],
                    "abstract": abstract[:3000],
                    "pub_date": pub_date[:20],
                    "source": journal[:100] if journal else "PubMed",
                    "pmid": pmid,
                    "doi": doi[:100] if doi else "",
                    "keywords": keywords[:500],
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                })
        except Exception as e:
            continue
    return results

def save_to_supabase(papers):
    """保存到Supabase，跳过已存在的PMID"""
    if not papers or not SUPABASE_URL:
        return 0, 0
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        print("    Supabase connection failed")
        return 0, 0

    inserted = skipped = 0
    for p in papers:
        try:
            # 检查PMID是否已存在
            if p.get("pmid"):
                existing = client.table("research_papers").select("id").eq("pmid", p["pmid"]).execute()
                if existing.data:
                    skipped += 1
                    continue
            client.table("research_papers").insert(p).execute()
            inserted += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                skipped += 1
            else:
                print(f"    Insert error: {e}")
    return inserted, skipped

def run():
    print("=" * 60)
    print("外泌体期刊专项爬虫")
    print("=" * 60)

    total_inserted = 0
    total_skipped = 0

    for journal_name, journal_abbr, extra_query in JOURNALS:
        print(f"\n📰 {journal_name}")
        pmids, total_count = search_pubmed_journal(journal_abbr, extra_query, retmax=200)
        print(f"   PubMed总量: {total_count} | 本次获取: {len(pmids)}")

        if not pmids:
            time.sleep(1)
            continue

        # 分批获取详情
        new_ins = new_skip = 0
        for i in range(0, len(pmids), 50):
            batch = pmids[i:i+50]
            papers = fetch_details(batch)
            ins, skip = save_to_supabase(papers)
            new_ins += ins
            new_skip += skip
            time.sleep(1.5)

        total_inserted += new_ins
        total_skipped += new_skip
        print(f"   ✅ 新增: {new_ins} | 已存在跳过: {new_skip}")
        time.sleep(2)

    print("\n" + "=" * 60)
    print(f"完成！总新增: {total_inserted} | 总跳过: {total_skipped}")
    print("=" * 60)

if __name__ == "__main__":
    run()
