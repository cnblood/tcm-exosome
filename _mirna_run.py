import requests, os, re, json, time

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

def sb_headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

def sb_upsert(records):
    headers = {**sb_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"}
    r = requests.post(f"{SUPABASE_URL}/rest/v1/mirna", headers=headers, json=records, timeout=30)
    r.raise_for_status()

PROMPT = """从以下论文提取"中药/植物来源->miRNA"关联。

中药/植物包括：ginseng人参, berberine小檗碱, quercetin槲皮素, curcumin姜黄素, astragalus黄芪, coptis黄连, ginger姜, garlic大蒜, grape葡萄, broccoli西兰花, angelica当归, salvia丹参, tanshinone丹参酮, baicalin黄芩苷, resveratrol白藜芦醇, puerarin葛根素, licorice甘草, wolfberry枸杞, schisandra五味子等植物来源外泌体/纳米颗粒。

标题：{title}
摘要：{abstract}

返回JSON数组（无关联返回[]）：
[{{"mirna_id":"hsa-miR-168a-5p","mirna_name":"miR-168a-5p","tcm_herb":"ginger","tcm_herb_cn":"姜","target_genes":["HPGD","PTGS2"],"is_exosome_cargo":true,"regulation":"down","biological_effect":"Anti-inflammatory via HPGD suppression"}}]

注意：植物来源外泌体携带的miRNA都标is_exosome_cargo=true。只返回JSON。"""

def gemini(title, abstract):
    payload = {
        "contents": [{"parts": [{"text": PROMPT.format(title=title[:300], abstract=abstract[:2500])}]}],
        "generationConfig": {"temperature": 0.05, "maxOutputTokens": 2048}
    }
    for attempt in range(3):
        try:
            r = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                params={"key": GEMINI_KEY}, json=payload, timeout=30)
            if r.status_code == 429:
                print("  限速，等待60秒...")
                time.sleep(60); continue
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            text = re.sub(r"```json|```", "", text).strip()
            if not text or text == "[]": return []
            result = json.loads(text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError: return []
        except Exception as e:
            print(f"  错误: {e}")
            if attempt < 2: time.sleep(5)
    return []

KNOWN_SEQ = {
    "hsa-miR-168a-5p":"UCGCUUGGUGCAGGUCGGGAA",
    "hsa-miR-156a":"UUGACAGAAGAUAGAGAGCAC",
    "hsa-miR-21-5p":"UAGCUUAUCAGACUGAUGUUGA",
    "hsa-miR-146a-5p":"UGAGAACUGAAUUCCAUGGGUU",
    "hsa-miR-155-5p":"UUAAUGCUAAUUGUGAUAGGGGU",
    "hsa-miR-126-3p":"UCGUACCGUGAGUAAUAAUGCG",
    "hsa-miR-122-5p":"UGGAGUGUGACAAUGGUGUUUG",
    "hsa-miR-223-3p":"UGUCAGUUUGUCAAAUACCCCA",
    "hsa-miR-34a-5p":"UGGCAGUGUCUUAGCUGGUUGU",
    "hsa-miR-29a-3p":"UAGCACCAUCUGAAAUCGGUUA",
    "hsa-miR-210-3p":"CUGUGCGUGUGACAGCGGCUGA",
    "hsa-miR-182-5p":"UUUGGCAAUGGUAGAACUCACA",
    "hsa-miR-let-7a-5p":"UGAGGUAGUAGGUUGUAUAGUU",
    "hsa-miR-5106":"CAUCUUAUAAAGCUAAGUCCC",
}

with open("tcm_mirna_enriched.json", encoding="utf-8") as f:
    papers = json.load(f)

# 去重key
r = requests.get(f"{SUPABASE_URL}/rest/v1/mirna", headers=sb_headers(),
    params={"select":"mirna_id,tcm_herb"})
existing_keys = set(
    f"{x['mirna_id'].lower()}_{(x['tcm_herb'] or '').lower()}"
    for x in r.json()
)
print(f"已有记录: {len(existing_keys)} 条")
print(f"待处理文献: {len(papers)} 篇\n")

all_records = []
for i, paper in enumerate(papers):
    title = paper.get("title","")
    abstract = paper.get("abstract","")
    if len(abstract) < 20:
        abstract = title

    extracted = gemini(title, abstract)
    new_count = 0
    for item in extracted:
        mid = item.get("mirna_id","").strip()
        herb = item.get("tcm_herb","").strip()
        if not mid or not herb: continue
        if re.match(r"^miR-", mid, re.I) and not mid.startswith("hsa-"):
            mid = f"hsa-{mid.lower()}"
        key = f"{mid.lower()}_{herb.lower()}"
        if key in existing_keys: continue
        existing_keys.add(key)
        tg = item.get("target_genes",[])
        all_records.append({
            "mirna_id": mid,
            "mirna_name": item.get("mirna_name", mid),
            "sequence": KNOWN_SEQ.get(mid,""),
            "target_genes": ",".join(tg) if isinstance(tg,list) else str(tg),
            "is_exosome_cargo": item.get("is_exosome_cargo", True),
            "tcm_herb": herb,
            "source": f"Gemini/TCM-paper:{paper.get('id','')}",
        })
        new_count += 1

    status = f"+{new_count}条" if new_count else "无新增"
    print(f"[{i+1:3d}/{len(papers)}] {status:8s} | {title[:65]}")
    time.sleep(1.5)

print(f"\n✅ 提取完成: {len(all_records)} 条新记录")

if not all_records:
    print("无新记录"); exit()

herbs = set(r["tcm_herb"] for r in all_records)
mirnas = set(r["mirna_id"] for r in all_records)
exo = sum(1 for r in all_records if r["is_exosome_cargo"])
print(f"涉及中药: {len(herbs)} 种 | miRNA种类: {len(mirnas)} | 外泌体相关: {exo}")
print("\n样本:")
for rec in all_records[:8]:
    print(f"  {'🧬' if rec['is_exosome_cargo'] else '  '} {rec['mirna_id']:<25} | {rec['tcm_herb']:<15} | {rec['target_genes'][:30]}")

with open("mirna_final.json","w",encoding="utf-8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)
print(f"\n写入Supabase...")
written = 0
for i in range(0, len(all_records), 50):
    chunk = all_records[i:i+50]
    try:
        sb_upsert(chunk); written += len(chunk)
        print(f"  {written}/{len(all_records)}")
    except Exception as e:
        print(f"  块失败({e})，逐条写入...")
        for rec in chunk:
            try: sb_upsert([rec]); written += 1
            except Exception as e2: print(f"    跳过 {rec['mirna_id']}: {e2}")

print(f"\n🎉 完成！写入 {written} 条，数据库总计 {14+written} 条")
