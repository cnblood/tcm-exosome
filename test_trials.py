import os
# SUPABASE_URL set via environment variable
os.environ['SUPABASE_KEY'] = os.environ.get("SUPABASE_KEY")

from src.crawler.expanded_crawler import fetch_clinical_trials, save_trials, CLINICAL_QUERIES

total_ins = total_skip = 0
for q in CLINICAL_QUERIES:
    trials = fetch_clinical_trials(q, max_results=100)
    print(f"  Found {len(trials)} | {q}")
    ins, skip = save_trials(trials)
    total_ins += ins
    total_skip += skip
    if ins > 0:
        print(f"    +{ins} inserted")

print(f"\n瀹屾垚! 鏂板: {total_ins} | 璺宠繃: {total_skip}")


