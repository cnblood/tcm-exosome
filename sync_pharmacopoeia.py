import sqlite3, os
from supabase import create_client

client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
conn = sqlite3.connect('data/tcm_exosome.db')
conn.row_factory = sqlite3.Row

for table in ['tcm_single_herb', 'tcm_compound_formula', 'tcm_extracts']:
    try:
        rows = conn.execute('SELECT * FROM ' + table).fetchall()
        data = [dict(r) for r in rows]
        for r in data:
            r.pop('id', None)
        if data:
            for i in range(0, len(data), 50):
                batch = data[i:i+50]
                client.table(table).upsert(batch, on_conflict='name_cn').execute()
            print(table + ': ' + str(len(data)) + ' records synced')
        else:
            print(table + ': empty')
    except Exception as e:
        print(table + ' ERROR: ' + str(e))
conn.close()
