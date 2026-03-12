import os
from supabase import create_client
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

for level in ['enriched', 'aligned', 'skeleton']:
    res = client.table('tcm_single_herb').select('id', count='exact').eq('data_level', level).execute()
    print(f'{level}: {res.count}')
total = client.table('tcm_single_herb').select('id', count='exact').execute()
print(f'Total: {total.count}')
