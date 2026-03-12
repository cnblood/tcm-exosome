import os
from supabase import create_client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
client = create_client(url, key)

all_herbs = []
for i in range(0, 700, 500):
    res = client.table('tcm_single_herb').select('name_cn,data_level,nature').range(i, i+499).execute()
    if not res.data: break
    all_herbs.extend(res.data)
    if len(res.data) < 500: break

aligned = [h['name_cn'] for h in all_herbs if h.get('data_level') == 'aligned']
print(f'Aligned (???): {len(aligned)}')
for n in aligned: print(n)
