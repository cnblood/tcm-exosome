#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCM-Exosome 扩展多语言爬虫 v2.0
覆盖：更多关键词 + 更多期刊 + 中文/日文/俄语文献 + 临床试验
运行：python src/crawler/expanded_crawler.py
"""
import os, time, requests
from xml.etree import ElementTree as ET

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
NCBI_EMAIL   = os.environ.get("NCBI_EMAIL", "research@tcm-exosome.com")

# ─────────────────────────────────────────────
# 1. 扩展PubMed关键词
# ─────────────────────────────────────────────
PUBMED_KEYWORDS = [
    # 中药单体扩展
    "exosome quercetin flavonoid",
    "exosome baicalein scutellaria",
    "exosome emodin anthraquinone",
    "exosome tanshinone danshen",
    "exosome astragaloside astragalus",
    "exosome ginsenoside panax",
    "exosome puerarin kudzu",
    "exosome paeoniflorin peony",
    "exosome ligustrazine chuanxiong",
    "exosome icariin epimedium",
    "exosome matrine sophora alkaloid",
    "exosome schisandrin wuweizi",
    "exosome notoginsenoside sanqi",
    "exosome cryptotanshinone salvia",
    "exosome artemisinin artemisia",
    "exosome tetrandrine stephania",
    "exosome andrographolide andrographis",
    "exosome wogonin baicalin flavone",
    "exosome naringenin citrus flavanone",
    "exosome apigenin luteolin flavone",
    "exosome kaempferol flavonol herb",
    "exosome oridonin rabdosia",
    "exosome celastrol tripterygium",
    "exosome polydatin resveratrol herb",
    # 植物来源纳米颗粒
    "plant derived exosome-like nanoparticles cancer",
    "plant exosome-like nanoparticles gut microbiota",
    "ginger derived nanoparticles exosome colitis",
    "grape derived nanoparticles exosome liver",
    "garlic derived nanoparticles exosome",
    "aloe vera exosome wound healing",
    "green tea exosome EGCG nanoparticles",
    "ganoderma mushroom exosome polysaccharide",
    "wolfberry lycium exosome nanoparticles",
    "lotus exosome nanoparticles",
    # 机制方向扩展
    "exosome miRNA tumor microenvironment TCM",
    "exosome lncRNA traditional medicine",
    "exosome circular RNA herb",
    "exosome autophagy traditional medicine",
    "exosome ferroptosis herbal compound",
    "exosome pyroptosis Chinese medicine",
    "exosome immunotherapy TCM combination",
    "exosome PD-L1 checkpoint TCM",
    "exosome macrophage polarization herb",
    "exosome dendritic cell TCM immunology",
    "exosome gut microbiota TCM interaction",
    "exosome blood-brain barrier TCM",
    "exosome liver fibrosis herbal",
    "exosome kidney fibrosis TCM",
    # 疾病方向扩展
    "TCM exosome NAFLD non-alcoholic fatty liver",
    "TCM exosome Parkinson neuroprotection",
    "TCM exosome rheumatoid arthritis",
    "TCM exosome lupus erythematosus",
    "TCM exosome inflammatory bowel disease",
    "TCM exosome acute lung injury",
    "TCM exosome myocardial infarction",
    "TCM exosome atherosclerosis",
    "TCM exosome wound healing skin",
    "TCM exosome bone fracture repair",
    "TCM exosome spinal cord injury",
    "TCM exosome COVID-19",
    "TCM exosome aging senescence",
    "TCM exosome polycystic ovary",
    # 技术应用
    "exosome drug delivery TCM active ingredient targeting",
    "exosome biomarker diagnosis TCM herb",
    "exosome proteomics herbal compound",
    "exosome metabolomics TCM",
    "exosome clinical trial herbal treatment outcome",
    # 中文文献（PubMed中文收录）
    "外泌体 中药 肿瘤",
    "外泌体 中医药 机制",
    "exosome traditional chinese medicine[Title/Abstract]",
    "细胞外囊泡 中药",
    # 日文相关（PubMed收录日文研究）
    "exosome kampo japanese herbal medicine",
    "exosome Rheum japonicum",
    "exosome Angelica acutiloba",
    "exosome traditional japanese medicine",
    "exosome Glycyrrhiza japonicum",
    # 俄语/东欧传统医学
    "exosome adaptogen eleutherococcus",
    "exosome rhodiola rosea adaptogen",
    "exosome schisandra chinensis Russia",
    "exosome Siberian ginseng eleutherococcus",
    "exosome propolis bee product",
    "exosome chaga mushroom inonotus",
    "exosome sea buckthorn hippophae",
]

# ─────────────────────────────────────────────
# 2. 更多专业期刊
# ─────────────────────────────────────────────
MORE_JOURNALS = [
    # 纳米/递药
    ("Nano Letters",                        "Nano Lett",                   "exosome OR extracellular vesicle"),
    ("Advanced Healthcare Materials",       "Adv Healthc Mater",           "exosome OR extracellular vesicle"),
    ("Nanomedicine",                        "Nanomedicine",                "exosome OR extracellular vesicle"),
    ("Drug Delivery",                       "Drug Deliv",                  "exosome OR extracellular vesicle"),
    ("Journal of Drug Delivery Science and Technology", "J Drug Deliv Sci Technol", "exosome OR extracellular vesicle"),
    ("Acta Biomaterialia",                  "Acta Biomater",               "exosome OR extracellular vesicle"),
    ("Molecular Pharmaceutics",             "Mol Pharm",                   "exosome OR extracellular vesicle"),
    ("ACS Applied Materials & Interfaces",  "ACS Appl Mater Interfaces",   "exosome AND (herb OR plant OR TCM)"),
    # 中医药专业
    ("Evidence-Based Complementary and Alternative Medicine", "Evid Based Complement Alternat Med", "exosome OR extracellular vesicle"),
    ("American Journal of Chinese Medicine","Am J Chin Med",               "exosome OR extracellular vesicle OR nanoparticle"),
    ("Journal of Traditional Chinese Medicine", "J Tradit Chin Med",       "exosome OR extracellular vesicle"),
    ("Chinese Herbal Medicines",            "Chin Herb Med",               "exosome OR extracellular vesicle OR nanoparticle"),
    ("Traditional Medicine Research",       "Tradit Med Res",              ""),
    ("Journal of Traditional and Complementary Medicine", "J Tradit Complement Med", "exosome OR vesicle"),
    # 肿瘤/疾病高分
    ("Cancer Research",                     "Cancer Res",                  "exosome AND (herb OR plant OR TCM OR traditional)"),
    ("Oncogene",                            "Oncogene",                    "exosome AND (herb OR plant OR TCM)"),
    ("Molecular Cancer",                    "Mol Cancer",                  "exosome AND (herb OR plant OR TCM)"),
    ("Journal of Hepatology",               "J Hepatol",                   "exosome AND (herb OR plant OR TCM)"),
    ("Hepatology",                          "Hepatology",                  "exosome AND (herb OR TCM OR traditional)"),
    ("Gut",                                 "Gut",                         "exosome AND (herb OR TCM OR plant)"),
    ("Cardiovascular Research",             "Cardiovasc Res",              "exosome AND (herb OR TCM OR traditional)"),
    # 日本汉方/俄罗斯传统医学期刊
    ("Journal of Natural Medicines",        "J Nat Med",                   "exosome OR extracellular vesicle"),
    ("Natural Product Research",            "Nat Prod Res",                "exosome OR extracellular vesicle"),
    ("Journal of Natural Products",         "J Nat Prod",                  "exosome OR extracellular vesicle"),
    ("Phytochemistry",                      "Phytochemistry",              "exosome OR extracellular vesicle OR nanoparticle"),
    ("Planta Medica",                       "Planta Med",                  "exosome OR extracellular vesicle"),
    ("Molecules",                           "Molecules",                   "exosome AND (TCM OR herb OR plant-derived)"),
    ("International Journal of Molecular Sciences", "Int J Mol Sci",       "exosome AND (TCM OR herb OR plant)"),
]

# ─────────────────────────────────────────────
# 3. 临床试验扩展关键词
# ─────────────────────────────────────────────
CLINICAL_QUERIES = [
    "exosome traditional chinese medicine",
    "extracellular vesicles herbal medicine",
    "TCM exosome cancer treatment",
    "Chinese herbal medicine biomarker exosome",
    "plant nanoparticles clinical",
    "curcumin exosome clinical trial",
    "berberine extracellular vesicle",
    "astragalus exosome immune",
    "ginseng exosome aging",
    "TCM formula exosome",
]

# ─────────────────────────────────────────────
# 通用工具函数
# ─────────────────────────────────────────────
def search_pubmed(query, retmax=100, lang_filter=None):
    q = query
    if lang_filter:
        q += f' AND {lang_filter}[Language]'
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db":"pubmed","term":q,"retmax":retmax,"retmode":"json",
              "email":NCBI_EMAIL,"tool":"tcm-expanded-crawler"}
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        ids = data.get("esearchresult",{}).get("idlist",[])
        total = data.get("esearchresult",{}).get("count","0")
        return ids, int(total)
    except: return [], 0

def search_pubmed_journal(journal_abbr, extra_query="", retmax=150, min_year=2015):
    base = f'"{journal_abbr}"[Journal]'
    query = f'({base}) AND ({extra_query})' if extra_query else base
    query += f' AND {min_year}:2026[PDAT]'
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db":"pubmed","term":query,"retmax":retmax,"retmode":"json","email":NCBI_EMAIL}
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        return data.get("esearchresult",{}).get("idlist",[]), int(data.get("esearchresult",{}).get("count",0))
    except: return [], 0

def fetch_details(pmids):
    if not pmids: return []
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db":"pubmed","id":",".join(pmids),"rettype":"xml","retmode":"xml","email":NCBI_EMAIL}
    try:
        r = requests.get(url, params=params, timeout=60)
        return parse_xml(r.text)
    except: return []

def parse_xml(xml_text):
    results = []
    try: root = ET.fromstring(xml_text)
    except: return results
    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = getattr(article.find(".//PMID"), "text", "")
            title_el = article.find(".//ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else ""
            abstract = " ".join("".join(p.itertext()) for p in article.findall(".//AbstractText"))
            authors = []
            for a in article.findall(".//Author"):
                ln = a.find("LastName"); fn = a.find("ForeName")
                if ln is not None: authors.append(ln.text+(" "+fn.text if fn is not None else ""))
            authors_str = ", ".join(authors[:6]) + (" et al." if len(authors)>6 else "")
            year_el = article.find(".//PubDate/Year"); month_el = article.find(".//PubDate/Month")
            pub_date = (year_el.text if year_el is not None else "")+(" "+month_el.text if month_el is not None else "")
            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else "PubMed"
            doi = next((a.text for a in article.findall(".//ArticleId") if a.get("IdType")=="doi"), "")
            lang_els = article.findall(".//Language")
            language = lang_els[0].text if lang_els else "eng"
            kws = [k.text for k in article.findall(".//Keyword") if k.text]
            if title and len(title) > 10:
                results.append({
                    "title": title[:500],
                    "authors": authors_str[:300],
                    "abstract": abstract[:3000],
                    "pub_date": pub_date[:20],
                    "source": journal[:100],
                    "pmid": pmid,
                    "doi": doi[:100] if doi else "",
                    "keywords": "; ".join(kws[:10])[:500],
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                })
        except: continue
    return results

def fetch_clinical_trials(query, max_results=100):
    """从ClinicalTrials.gov抓取TCM相关试验"""
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": query,
        "filter.overallStatus": "COMPLETED,RECRUITING,ACTIVE_NOT_RECRUITING",
        "pageSize": max_results,
        "format": "json",
        "fields": "NCTId,BriefTitle,OfficialTitle,Condition,InterventionName,Phase,EnrollmentCount,StartDate,CompletionDate,BriefSummary"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        return data.get("studies", [])
    except Exception as e:
        print(f"    ClinicalTrials error: {e}")
        return []

def save_papers(papers):
    if not papers or not SUPABASE_URL: return 0, 0
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return 0, 0
    inserted = skipped = 0
    for p in papers:
        try:
            if p.get("pmid"):
                ex = client.table("research_papers").select("id").eq("pmid", p["pmid"]).execute()
                if ex.data: skipped += 1; continue
            client.table("research_papers").insert(p).execute()
            inserted += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower(): skipped += 1
    return inserted, skipped

def save_trials(trials):
    if not trials or not SUPABASE_URL: return 0, 0
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return 0, 0
    inserted = skipped = 0
    for study in trials:
        try:
            proto = study.get("protocolSection", {})
            id_module = proto.get("identificationModule", {})
            desc_module = proto.get("descriptionModule", {})
            cond_module = proto.get("conditionsModule", {})
            arm_module = proto.get("armsInterventionsModule", {})
            design_module = proto.get("designModule", {})
            status_module = proto.get("statusModule", {})
            nct_id = id_module.get("nctId", "")
            if not nct_id: continue
            ex = client.table("clinical_trials").select("id").eq("nct_id", nct_id).execute()
            if ex.data: skipped += 1; continue
            interventions = arm_module.get("interventions", [])
            interv_names = "; ".join([i.get("name","") for i in interventions[:5]])
            client.table("clinical_trials").insert({
                "nct_id": nct_id,
                "title": id_module.get("briefTitle","")[:500],
                "conditions": "; ".join(cond_module.get("conditions",[])[:5])[:300],
                "interventions": interv_names[:300],
                "phase": "; ".join(design_module.get("phaseList",{}).get("phase",[])),
                "status": status_module.get("overallStatus",""),
                "enrollment": design_module.get("enrollmentInfo",{}).get("count"),
                "start_date": status_module.get("startDateStruct",{}).get("date",""),
                "summary": desc_module.get("briefSummary","")[:1000],
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
            }).execute()
            inserted += 1
        except Exception as e:
            if "duplicate" in str(e).lower(): skipped += 1
    return inserted, skipped

def run():
    print("=" * 65)
    print("TCM-Exosome 扩展多语言爬虫 v2.0")
    print("=" * 65)
    total_ins = total_skip = 0

    # ── Part 1: 扩展关键词 (英文/中文/日文/俄语) ──
    print("\n【Part 1】扩展PubMed关键词")
    # 英文
    print("  英文关键词...")
    for kw in PUBMED_KEYWORDS:
        pmids, total = search_pubmed(kw, retmax=100)
        if pmids:
            papers = fetch_details(pmids)
            ins, skip = save_papers(papers)
            total_ins += ins; total_skip += skip
            if ins > 0: print(f"    +{ins} | {kw[:50]}")
        time.sleep(1)

    # 中文文献（language=chi）
    print("  中文文献...")
    cn_queries = [
        "exosome traditional chinese medicine",
        "extracellular vesicles herb",
        "plant derived nanoparticles TCM",
        "exosome cancer herb treatment",
        "exosome liver disease herbal",
    ]
    for q in cn_queries:
        pmids, _ = search_pubmed(q, retmax=100, lang_filter="chi")
        if pmids:
            papers = fetch_details(pmids)
            ins, skip = save_papers(papers)
            total_ins += ins; total_skip += skip
            if ins > 0: print(f"    +{ins} [中文] {q[:40]}")
        time.sleep(1)

    # 日文文献（language=jpn）
    print("  日文文献...")
    jp_queries = [
        "exosome kampo herbal",
        "extracellular vesicles japanese medicine",
        "exosome traditional medicine japan",
        "plant exosome nanoparticles japan",
    ]
    for q in jp_queries:
        pmids, _ = search_pubmed(q, retmax=50, lang_filter="jpn")
        if pmids:
            papers = fetch_details(pmids)
            ins, skip = save_papers(papers)
            total_ins += ins; total_skip += skip
            if ins > 0: print(f"    +{ins} [日文] {q[:40]}")
        time.sleep(1)

    # 俄语文献（language=rus）
    print("  俄语文献...")
    ru_queries = [
        "exosome adaptogen rhodiola eleutherococcus",
        "extracellular vesicles russian herbal medicine",
        "exosome schisandra siberian plant",
        "exosome chaga inonotus mushroom",
        "plant nanoparticles traditional medicine russia",
    ]
    for q in ru_queries:
        pmids, _ = search_pubmed(q, retmax=50, lang_filter="rus")
        if pmids:
            papers = fetch_details(pmids)
            ins, skip = save_papers(papers)
            total_ins += ins; total_skip += skip
            if ins > 0: print(f"    +{ins} [俄语] {q[:40]}")
        time.sleep(1)

    # ── Part 2: 更多期刊 ──
    print("\n【Part 2】更多专业期刊 (28本)")
    for journal_name, journal_abbr, extra_query in MORE_JOURNALS:
        pmids, total = search_pubmed_journal(journal_abbr, extra_query, retmax=150)
        if pmids:
            ins = skip = 0
            for i in range(0, len(pmids), 50):
                papers = fetch_details(pmids[i:i+50])
                a, b = save_papers(papers)
                ins += a; skip += b
                time.sleep(1)
            total_ins += ins; total_skip += skip
            if ins > 0: print(f"  +{ins} | {journal_name[:45]}")
        time.sleep(2)

    # ── Part 3: 临床试验扩展 ──
    print("\n【Part 3】临床试验扩展")
    ct_ins = ct_skip = 0
    for q in CLINICAL_QUERIES:
        trials = fetch_clinical_trials(q, max_results=100)
        ins, skip = save_trials(trials)
        ct_ins += ins; ct_skip += skip
        if ins > 0: print(f"  +{ins} trials | {q}")
        time.sleep(2)
    print(f"  临床试验新增: {ct_ins} | 跳过: {ct_skip}")

    print("\n" + "=" * 65)
    print(f"完成！")
    print(f"  文献新增: {total_ins} | 跳过(已存在): {total_skip}")
    print(f"  临床试验新增: {ct_ins}")
    print("=" * 65)

if __name__ == "__main__":
    run()
