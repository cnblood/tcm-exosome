import os
from supabase import create_client
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# ????
res = client.table('research_papers').select('*').limit(1).execute()
if res.data:
    print('Columns:', list(res.data[0].keys()))

# ?????
total = client.table('research_papers').select('id', count='exact').execute()
has_abstract = client.table('research_papers').select('id', count='exact').neq('abstract', '').execute()
print(f'Total: {total.count}')
print(f'Has abstract: {has_abstract.count}')
print(f'Coverage: {has_abstract.count*100//total.count}%')
