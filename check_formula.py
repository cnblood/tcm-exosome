import os
from supabase import create_client
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

res = sb.table('tcm_compound_formula').select('*').limit(3).execute()
if res.data:
    print('Columns:', list(res.data[0].keys()))
    for r in res.data:
        print(r)
total = sb.table('tcm_compound_formula').select('id', count='exact').execute()
print(f'Total: {total.count}')
