"""
TCM-Exosome miRNA Expander v2
从558篇miRNA相关文献中批量提取 TCM herb -> miRNA -> target gene 三元组
目标：300+ 条有中药关联的miRNA记录

运行：
  python mirna_expander_v2.py --dry-run   # 测试，不写库
  python mirna_expander_v2.py             # 正式写入
"""

import os, re, sys, json, time, requests
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

DRY_RUN = "--dry-run" in sys.argv

# ── Supabase ──────────────────────────────────────────────────

def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def sb_get_all(table, params):
    results = []
    offset = 0
    while True:
        p = params + f"&limit=1000&offset={offset}"
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{p}", headers=sb_headers(), timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        results.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return results

def sb_upsert(table, records):
    headers = {**sb_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"}
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers, json=records, timeout=30)
    r.raise_for_status()

# ── Gemini ────────────────────────────────────────────────────

PROMPT = """你是TCM外泌体miRNA专家。从以下论文标题+摘要中，提取所有"中药/中药成分 → miRNA"关联。

规则：
1. 必须有明确中药或中药活性成分（如berberine/小檗碱, quercetin/槲皮素, curcumin/姜黄素, ginsenoside/人参皂苷, astragaloside/黄芪甲苷等）
2. miRNA格式：优先hsa-miR-XXX-Xp，无法确定则用miR-XXX
3. target_genes：官方基因符号列表，没有则[]
4. is_exosome_cargo：摘要明确提到exosome/EV携带则true
5. regulation：up=上调, down=下调, unknown=不明确
6. biological_effect：一句话描述功能（英文）

标题：{title}
摘要：{abstract}

只返回JSON数组，无其他文字：
[{{"mirna_id":"hsa-miR-21-5p","mirna_name":"miR-21","tcm_herb":"berberine","tcm_herb_cn":"小檗碱","target_genes":["PTEN","PDCD4"],"is_exosome_cargo":false,"regulation":"down","biological_effect":"Suppresses tumor growth via PTEN upregulation"}}]

无关联则返回: []"""

def gemini_extract(title, abstract):
    if not GEMINI_API_KEY:
        return []
    payload = {
        "contents": [{"parts": [{"text": PROMPT.format(
            title=title[:200],
            abstract=abstract[:2000]
        )}]}],
        "generationConfig": {"temperature": 0.05, "maxOutputTokens": 2048}
    }
    for attempt in range(3):
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                params={"key": GEMINI_API_KEY},
                json=payload, timeout=30
            )
            if r.status_code == 429:
                time.sleep(30)
                continue
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            text = re.sub(r"```json|```", "", text).strip()
            if text == "[]" or not text:
                return []
            result = json.loads(text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            return []
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                return []
    return []

# ── miRBase 序列查询 ──────────────────────────────────────────

SEQ_CACHE = {}

def get_sequence(mirna_id):
    if mirna_id in SEQ_CACHE:
        return SEQ_CACHE[mirna_id]
    # 已知常见miRNA序列（离线缓存，减少API调用）
    KNOWN = {
        "hsa-miR-21-5p":    "UAGCUUAUCAGACUGAUGUUGA",
        "hsa-miR-21-3p":    "CAACACCAGUCGAUGGGCUGU",
        "hsa-miR-146a-5p":  "UGAGAACUGAAUUCCAUGGGUU",
        "hsa-miR-155-5p":   "UUAAUGCUAAUUGUGAUAGGGGU",
        "hsa-miR-126-3p":   "UCGUACCGUGAGUAAUAAUGCG",
        "hsa-miR-210-3p":   "CUGUGCGUGUGACAGCGGCUGA",
        "hsa-miR-122-5p":   "UGGAGUGUGACAAUGGUGUUUG",
        "hsa-miR-223-3p":   "UGUCAGUUUGUCAAAUACCCCA",
        "hsa-miR-29a-3p":   "UAGCACCAUCUGAAAUCGGUUA",
        "hsa-miR-34a-5p":   "UGGCAGUGUCUUAGCUGGUUGU",
        "hsa-miR-92a-3p":   "UAUUGCACUUGUCCCGGCCUGU",
        "hsa-miR-141-3p":   "UAACACUGUCUGGUAAAGAUGG",
        "hsa-miR-200a-3p":  "UAACACUGCCUGGUAAUGAUGA",
        "hsa-miR-23a-3p":   "AUCACAUUGCCAGGGAUUUCC",
        "hsa-miR-let-7a-5p":"UGAGGUAGUAGGUUGUAUAGUU",
        "hsa-miR-168a-5p":  "UCGCUUGGUGCAGGUCGGGAA",  # plant miRNA
    }
    seq = KNOWN.get(mirna_id, "")
    SEQ_CACHE[mirna_id] = seq
    return seq

# ── 主流程 ────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  TCM-Exosome miRNA Expander v2")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  模式: {'DRY-RUN（不写库）' if DRY_RUN else '正式写入'}")
    print("=" * 60)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ 缺少 SUPABASE_URL / SUPABASE_KEY"); sys.exit(1)
    if not GEMINI_API_KEY:
        print("❌ 缺少 GEMINI_API_KEY"); sys.exit(1)

    # 1. 拉取miRNA相关文献
    print("\n📚 拉取miRNA相关文献...")
    papers = sb_get_all("research_papers",
        "select=id,title,abstract&or=(title.ilike.*mirna*,abstract.ilike.*mirna*,title.ilike.*miR-*,abstract.ilike.*miR-*)")
    print(f"  找到 {len(papers)} 篇")

    # 2. 过滤有摘要的
    papers = [p for p in papers if p.get("abstract") and len(p["abstract"]) > 100]
    print(f"  有效摘要: {len(papers)} 篇")

    # 3. 获取已有记录（去重用）
    existing = sb_get_all("mirna", "select=mirna_id,tcm_herb")
    existing_keys = set(
        f"{r['mirna_id'].lower()}_{(r['tcm_herb'] or '').lower()}"
        for r in existing
    )
    print(f"  已有记录: {len(existing)} 条")

    # 4. Gemini批量提取
    print(f"\n🤖 Gemini批量提取（{len(papers)} 篇）...")
    all_records = []
    errors = 0

    for i, paper in enumerate(papers):
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")

        extracted = gemini_extract(title, abstract)

        for item in extracted:
            mirna_id = item.get("mirna_id", "").strip()
            tcm_herb = item.get("tcm_herb", "").strip()
            if not mirna_id or not tcm_herb:
                continue

            # 标准化miRNA ID
            if re.match(r"^miR-\d+", mirna_id, re.I):
                mirna_id = f"hsa-{mirna_id.lower()}"

            key = f"{mirna_id.lower()}_{tcm_herb.lower()}"
            if key in existing_keys:
                continue
            existing_keys.add(key)

            target_genes = item.get("target_genes", [])
            record = {
                "mirna_id": mirna_id,
                "mirna_name": item.get("mirna_name", mirna_id),
                "sequence": get_sequence(mirna_id),
                "target_genes": ",".join(target_genes) if isinstance(target_genes, list) else str(target_genes),
                "is_exosome_cargo": item.get("is_exosome_cargo", False),
                "tcm_herb": tcm_herb,
                "source": f"Gemini/PubMed:{paper['id']}",
                "biological_effect": item.get("biological_effect", ""),
                "regulation": item.get("regulation", "unknown"),
                "tcm_herb_cn": item.get("tcm_herb_cn", ""),
            }
            all_records.append(record)

        # 进度显示
        if (i + 1) % 20 == 0 or i == len(papers) - 1:
            print(f"  [{i+1}/{len(papers)}] 已提取新记录: {len(all_records)} 条")

        time.sleep(1.5)  # Gemini限速

        # 每100篇临时保存一次
        if (i + 1) % 100 == 0 and all_records:
            with open("mirna_progress.json", "w", encoding="utf-8") as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 提取完成: {len(all_records)} 条新记录")

    if not all_records:
        print("没有新记录，退出")
        return

    # 5. 预览
    print("\n📋 样本预览（前8条）:")
    for r in all_records[:8]:
        exo = "🧬" if r["is_exosome_cargo"] else "  "
        print(f"  {exo} {r['mirna_id']:<25} | {r['tcm_herb']:<20} | {r['regulation']:<7} | {r['target_genes'][:30]}")

    # 统计
    herbs = set(r["tcm_herb"] for r in all_records)
    mirnas = set(r["mirna_id"] for r in all_records)
    exo_count = sum(1 for r in all_records if r["is_exosome_cargo"])
    print(f"\n📊 统计:")
    print(f"  涉及中药: {len(herbs)} 种")
    print(f"  涉及miRNA: {len(mirnas)} 个")
    print(f"  外泌体相关: {exo_count} 条")

    # 6. 保存JSON
    with open("mirna_extracted.json", "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    print(f"\n💾 已保存到 mirna_extracted.json")

    # 7. 写入数据库
    if DRY_RUN:
        print("🔍 Dry-run模式，不写入数据库")
        return

    print(f"\n💾 写入Supabase（{len(all_records)} 条）...")

    # 检查mirna表是否有新字段，没有则用基础字段
    base_records = []
    for r in all_records:
        base = {
            "mirna_id": r["mirna_id"],
            "mirna_name": r["mirna_name"],
            "sequence": r["sequence"],
            "target_genes": r["target_genes"],
            "is_exosome_cargo": r["is_exosome_cargo"],
            "tcm_herb": r["tcm_herb"],
            "source": r["source"],
        }
        base_records.append(base)

    written = 0
    for i in range(0, len(base_records), 50):
        chunk = base_records[i:i+50]
        try:
            sb_upsert("mirna", chunk)
            written += len(chunk)
            print(f"  写入: {written}/{len(base_records)}")
        except Exception as e:
            print(f"  ❌ 写入错误: {e}")
            # 尝试逐条写入找出问题记录
            for rec in chunk:
                try:
                    sb_upsert("mirna", [rec])
                    written += 1
                except Exception as e2:
                    print(f"    跳过: {rec['mirna_id']} - {e2}")

    print(f"\n🎉 完成！写入 {written} 条")
    print(f"   数据库总量: {14 + written} 条")

if __name__ == "__main__":
    main()
