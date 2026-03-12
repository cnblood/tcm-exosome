content = '''# -*- coding: utf-8 -*-
import os, time, json
from google import genai
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

PROMPT = """Read this research abstract and summarize the KEY FINDING in one Chinese sentence (30 chars max).
Focus on: what TCM/herb/compound was studied, what effect was found, on what disease/target.
Return ONLY the Chinese sentence, nothing else.
Example: "???????NF-kB??????????"

Title: {title}
Abstract: {abstract}"""

def run(batch=200):
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = genai.Client(api_key=GEMINI_KEY)

    # ?key_findings?????
    res = sb.table("paper_ai_analysis").select("id,paper_id,key_findings").execute()
    empty = [r for r in res.data if not r.get("key_findings","").strip()]
    print(f"Empty key_findings: {len(empty)}, batch: {batch}")
    empty = empty[:batch]

    # ??????
    paper_ids = [r["paper_id"] for r in empty]
    papers = {}
    for i in range(0, len(paper_ids), 100):
        chunk = paper_ids[i:i+100]
        res2 = sb.table("research_papers").select("id,title,abstract").in_("id", chunk).execute()
        for p in res2.data:
            papers[p["id"]] = p

    success = failed = 0
    for idx, rec in enumerate(empty):
        paper = papers.get(rec["paper_id"])
        if not paper or not paper.get("abstract","").strip():
            continue
        print(f"  [{idx+1}/{len(empty)}] paper_id={rec[\'paper_id\']}...", end=" ", flush=True)
        try:
            prompt = PROMPT.format(title=paper["title"][:200], abstract=paper["abstract"][:800])
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            finding = resp.text.strip()[:100]
            sb.table("paper_ai_analysis").update({"key_findings": finding}).eq("id", rec["id"]).execute()
            print(f"OK: {finding[:40]}")
            success += 1
        except Exception as e:
            print(f"ERR: {e}")
            failed += 1
            time.sleep(10)
        time.sleep(5)

    print(f"Done! success={success} failed={failed}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=100)
    args = parser.parse_args()
    run(args.batch)
'''
with open("src/crawler/fill_key_findings.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Written OK")
