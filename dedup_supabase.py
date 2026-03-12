import os
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
client = create_client(url, key)

# ?????????title
all_records = []
for i in range(0, 3000, 1000):
    res = client.table('research_papers').select('id,title,source,pmid').range(i, i+999).execute()
    if not res.data: break
    all_records.extend(res.data)
    if len(res.data) < 1000: break

# ???title?????id
from collections import defaultdict
title_groups = defaultdict(list)
for r in all_records:
    t = (r.get('title') or '').strip().lower()
    if t:
        title_groups[t].append(r)

to_delete = []
for title, records in title_groups.items():
    if len(records) > 1:
        records.sort(key=lambda x: x['id'])
        keep = records[0]
        for dup in records[1:]:
            to_delete.append(dup['id'])
            print(f"  DELETE id={dup['id']} source={dup.get('source')} | keep id={keep['id']}")

print(f"\nTotal to delete: {len(to_delete)}")

# ????
for del_id in to_delete:
    client.table('research_papers').delete().eq('id', del_id).execute()

print(f"Done! Deleted {len(to_delete)} duplicates")

# ??
total = client.table('research_papers').select('id', count='exact').execute()
print(f"Remaining: {total.count}")
