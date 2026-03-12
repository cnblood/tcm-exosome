import os
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
client = create_client(url, key)

# ????????
all_pmids = []
all_titles = []
all_dois = []

for i in range(0, 3000, 1000):
    res = client.table('research_papers').select('id,pmid,title,doi').range(i, i+999).execute()
    if not res.data: break
    for r in res.data:
        if r.get('pmid'): all_pmids.append(r['pmid'])
        if r.get('title'): all_titles.append(r['title'].strip().lower())
        if r.get('doi'): all_dois.append(r['doi'])
    print(f"  Fetched {i+len(res.data)} records...")
    if len(res.data) < 1000: break

print(f"\nTotal fetched: {len(all_titles)}")
print(f"Unique pmids: {len(set(all_pmids))} / Total pmids: {len(all_pmids)}")
print(f"Unique titles: {len(set(all_titles))} / Total titles: {len(all_titles)}")
print(f"Unique dois: {len(set(all_dois))} / Total dois: {len(all_dois)}")
print(f"\nDuplicate pmids: {len(all_pmids)-len(set(all_pmids))}")
print(f"Duplicate titles: {len(all_titles)-len(set(all_titles))}")
print(f"Duplicate dois: {len(all_dois)-len(set(all_dois))}")
