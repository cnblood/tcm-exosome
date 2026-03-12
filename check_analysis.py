import os, json
from supabase import create_client
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

res = sb.table("paper_ai_analysis").select("*").limit(5).execute()
for r in res.data:
    print(f"paper_id={r['paper_id']}")
    print(f"  herbs={r['tcm_herbs']}")
    print(f"  genes={r['target_genes']}")
    print(f"  type={r['study_type']} disease={r['disease_area']} conf={r['confidence']}")
    print()

# ??
total = sb.table("paper_ai_analysis").select("id", count="exact").execute()
print(f"Total: {total.count}")

res2 = sb.table("paper_ai_analysis").select("study_type").execute()
from collections import Counter
types = Counter(r['study_type'] for r in res2.data)
print("Study types:", dict(types))

res3 = sb.table("paper_ai_analysis").select("disease_area").execute()
diseases = Counter(r['disease_area'] for r in res3.data)
print("Disease areas:", dict(diseases))
