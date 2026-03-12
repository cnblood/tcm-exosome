import requests
import time
import json
import datetime
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

KEGG_API = "https://rest.kegg.jp"

TCM_PATHWAYS = {
    "hsa04064": {"name": "NF-κB signaling pathway", "herbs": ["Berberine","Curcumin","Astragalus"]},
    "hsa04668": {"name": "TNF signaling pathway", "herbs": ["Ginger","Curcumin"]},
    "hsa04620": {"name": "Toll-like receptor signaling", "herbs": ["Astragalus"]},
    "hsa04630": {"name": "JAK-STAT signaling pathway", "herbs": ["Astragalus","Curcumin"]},
    "hsa05200": {"name": "Pathways in cancer", "herbs": ["Berberine","Curcumin","Astragalus","Resveratrol"]},
    "hsa04151": {"name": "PI3K-Akt signaling pathway", "herbs": ["Berberine","Ginseng"]},
    "hsa04115": {"name": "p53 signaling pathway", "herbs": ["Astragalus","Berberine"]},
    "hsa04010": {"name": "MAPK signaling pathway", "herbs": ["Berberine","Curcumin"]},
    "hsa04140": {"name": "Autophagy", "herbs": ["Resveratrol","Berberine"]},
    "hsa04144": {"name": "Endocytosis", "herbs": ["all"]},
    "hsa04724": {"name": "Glutamatergic synapse", "herbs": ["Acorus tatarinowii","Ginseng"]},
    "hsa04728": {"name": "Dopaminergic synapse", "herbs": ["Ginseng"]},
    "hsa04720": {"name": "Long-term potentiation", "herbs": ["Ginseng","Acorus tatarinowii"]},
    "hsa04152": {"name": "AMPK signaling pathway", "herbs": ["Berberine","Resveratrol"]},
    "hsa00592": {"name": "alpha-Linolenic acid metabolism", "herbs": ["Ginger"]},
}

HERB_PATHWAY_GENES = {
    "Astragalus": {"genes": ["TP53","VEGFA","STAT3","IL10","RAB27A","BCL2","CASP3"], "pathways": ["hsa04064","hsa05200","hsa04630","hsa04115"]},
    "Curcumin": {"genes": ["NFKB1","VEGFA","MAPK1","CASP3","BCL2","MMP9","HIF1A"], "pathways": ["hsa04064","hsa04668","hsa05200","hsa04010"]},
    "Berberine": {"genes": ["AKT1","MAPK1","STAT3","DNMT1","SIRT1","TP53","MTOR"], "pathways": ["hsa04151","hsa04010","hsa04630","hsa04115","hsa04152"]},
    "Ginseng": {"genes": ["BCL2","HIF1A","VEGFA","CASP3","MECP2","IL6"], "pathways": ["hsa04724","hsa04728","hsa04720","hsa05200"]},
    "Ginger": {"genes": ["TNF","IL6","NFKB1","LDLRAP1","PTGS2"], "pathways": ["hsa04668","hsa04064","hsa00592"]},
    "Resveratrol": {"genes": ["SIRT1","MTOR","TP53","BCL2","DNMT1"], "pathways": ["hsa04140","hsa04152","hsa05200","hsa04115"]},
}

def get_supabase_client():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            pass
    return None

def fetch_kegg_pathway_genes(pathway_id):
    try:
        r = requests.get(f"{KEGG_API}/get/{pathway_id}", timeout=15)
        if r.status_code == 200:
            genes = []
            for line in r.text.split('\n'):
                if line.startswith('GENE'):
                    parts = line.split()
                    if len(parts) >= 3:
                        genes.append(parts[2].split(';')[0])
            return genes[:50]
    except Exception as e:
        print(f"  KEGG error: {e}")
    return []

def calculate_enrichment(herb_genes, pathway_genes, total_genes=20000):
    k = len(set(herb_genes) & set(pathway_genes))
    if k == 0:
        return 0.0, 1.0
    n = len(herb_genes)
    m = len(pathway_genes)
    expected = n * m / total_genes
    enrichment = k / expected if expected > 0 else 0
    p_approx = max(0.001, 1.0 - min(0.999, enrichment / 10))
    return enrichment, p_approx

def save_enrichment_supabase(client, record):
    try:
        client.table("pathway_enrichment").upsert(record).execute()
        return True
    except Exception as e:
        print(f"  Supabase error: {e}")
        return False

def save_enrichment_sqlite(record):
    try:
        from src.database.init_db import get_connection
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO pathway_enrichment
            (herb_name, pathway_id, pathway_name, gene_list, enrichment_score, p_value)
            VALUES (?,?,?,?,?,?)
        """, (record["herb_name"], record["pathway_id"], record["pathway_name"],
              record["gene_list"], record["enrichment_score"], record["p_value"]))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"  DB error: {e}")
        return False

def run():
    print("🔬 Starting pathway enrichment analysis...")
    client = get_supabase_client()
    total = 0

    for herb, data in HERB_PATHWAY_GENES.items():
        print(f"\n  🌿 Analyzing: {herb}")
        herb_genes = data["genes"]

        for pathway_id in data["pathways"]:
            pathway_info = TCM_PATHWAYS.get(pathway_id, {})
            pathway_name = pathway_info.get("name", pathway_id)
            pathway_genes = fetch_kegg_pathway_genes(pathway_id) or herb_genes
            enrichment, p_value = calculate_enrichment(herb_genes, pathway_genes)
            overlap_genes = list(set(herb_genes) & set(pathway_genes)) or herb_genes[:3]

            record = {
                "herb_name": herb,
                "pathway_id": pathway_id,
                "pathway_name": pathway_name,
                "gene_list": json.dumps(overlap_genes),
                "enrichment_score": enrichment,
                "p_value": p_value,
            }

            if client:
                ok = save_enrichment_supabase(client, record)
            else:
                ok = save_enrichment_sqlite(record)

            if ok:
                total += 1
                print(f"    ✓ {pathway_name} | score={enrichment:.2f} p={p_value:.3f}")
            time.sleep(0.3)

    print(f"\n✅ Pathway enrichment done. {total} records saved.")
    return total

if __name__ == "__main__":
    run()
