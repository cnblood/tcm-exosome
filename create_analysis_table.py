import os
from supabase import create_client
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# ?????AI????
client.rpc('exec_sql', {'sql': '''
CREATE TABLE IF NOT EXISTS paper_ai_analysis (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES research_papers(id),
    tcm_herbs TEXT,
    target_genes TEXT,
    exosome_types TEXT,
    key_findings TEXT,
    study_type TEXT,
    disease_area TEXT,
    confidence FLOAT,
    analyzed_at TIMESTAMP DEFAULT NOW()
);
'''}).execute()
print('Table created')
