content = '''# -*- coding: utf-8 -*-
import os, time, json
from google import genai
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

SYSTEM_PROMPT = """You are a TCM exosome research literature analyst. Extract info from abstracts and return ONLY JSON, no other output.
Format: {"tcm_herbs":["herb/compound"],"target_genes":["gene symbol"],"exosome_types":["exosome type"],"key_findings":"main finding in Chinese within 50 chars","study_type":"in vitro/animal/clinical/review/other","disease_area":"cancer/cardiovascular/neural/inflammation/other","confidence":0.0-1.0}
Rules: no herbs->[], no genes->[], no exosomes->[], unrelated->confidence<0.3"""

def analyze_abstract(client, title, abstract):
    prompt = SYSTEM_PROMPT + "\\n\\nTitle: " + title + "\\n\\nAbstract: " + abstract
    try:
        response = client.models.generate_content(model="gemini-2.0-flash-lite", contents=prompt)
        text = response.text.strip().replace("`json","").replace("`","").strip()
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f" JSON error:{e}")
        return None
    except Exception as e:
        print(f" API error:{e}")
        time.sleep(10)
        return None

def run(batch_size=20):
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = genai.Client(api_key=GEMINI_KEY)

    res = sb.table("paper_ai_analysis").select("paper_id").execute()
    existing_ids = {r["paper_id"] for r in res.data}
    print(f"Already analyzed: {len(existing_ids)}")

    all_papers = []
    for i in range(0, 3000, 1000):
        res = sb.table("research_papers").select("id,title,abstract").neq("abstract","").range(i,i+999).execute()
        if not res.data: break
        all_papers.extend(res.data)
        if len(res.data) < 1000: break

    papers = [p for p in all_papers if p["id"] not in existing_ids and len(p.get("abstract",""))>100]
    print(f"To analyze: {len(papers)}, batch: {batch_size}")
    papers = papers[:batch_size]

    success = failed = 0
    for idx, paper in enumerate(papers):
        print(f"  [{idx+1}/{len(papers)}] id={paper[\'id\']}...", end=" ", flush=True)
        result = analyze_abstract(client, paper["title"], paper["abstract"])
        if result:
            try:
                sb.table("paper_ai_analysis").insert({
                    "paper_id": paper["id"],
                    "tcm_herbs": json.dumps(result.get("tcm_herbs",[]), ensure_ascii=False),
                    "target_genes": json.dumps(result.get("target_genes",[]), ensure_ascii=False),
                    "exosome_types": json.dumps(result.get("exosome_types",[]), ensure_ascii=False),
                    "key_findings": result.get("key_findings",""),
                    "study_type": result.get("study_type","other"),
                    "disease_area": result.get("disease_area","other"),
                    "confidence": float(result.get("confidence",0.5)),
                }).execute()
                print(f"OK herbs={result.get(\'tcm_herbs\',[])} genes={result.get(\'target_genes\',[])} conf={result.get(\'confidence\',0):.2f}")
                success += 1
            except Exception as e:
                print(f"DB error:{e}")
                failed += 1
        else:
            print("FAILED")
            failed += 1
        time.sleep(4.5)

    print(f"Done! success={success} failed={failed} total={len(existing_ids)+success}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=20)
    args = parser.parse_args()
    run(batch_size=args.batch)
'''
with open('src/crawler/ai_paper_analysis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Written OK')
