import os
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
client = create_client(url, key)

# ??
total = client.table('research_papers').select('id', count='exact').execute()
print(f'Total: {total.count}')

# pmid??
dup = client.rpc('check_duplicates', {}).execute() if False else None

# ?SQL???pmid
res = client.table('research_papers').select('pmid').not_.is_('pmid', 'null').execute()
pmids = [r['pmid'] for r in res.data if r.get('pmid')]
dup_pmids = len(pmids) - len(set(pmids))
print(f'Duplicate pmid count: {dup_pmids}')

# ?SQL???title
res2 = client.table('research_papers').select('title').execute()
titles = [r['title'] for r in res2.data if r.get('title')]
dup_titles = len(titles) - len(set(titles))
print(f'Duplicate title count: {dup_titles}')
print(f'Unique titles: {len(set(titles))}')
