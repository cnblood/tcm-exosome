import requests
import time
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

HERB_GENE_KNOWLEDGE = [
    {"herb_name": "Astragalus", "active_compound": "Astragaloside IV", "gene_symbol": "TP53", "interaction_type": "activate", "mechanism": "激活p53通路诱导肿瘤细胞凋亡", "confidence_score": 0.85, "source": "TCMSP"},
    {"herb_name": "Astragalus", "active_compound": "Astragaloside IV", "gene_symbol": "VEGFA", "interaction_type": "inhibit", "mechanism": "抑制VEGF分泌，减少肿瘤血管生成", "confidence_score": 0.82, "source": "literature"},
    {"herb_name": "Astragalus", "active_compound": "Calycosin", "gene_symbol": "STAT3", "interaction_type": "inhibit", "mechanism": "抑制STAT3磷酸化，阻断炎症信号", "confidence_score": 0.88, "source": "HIT"},
    {"herb_name": "Astragalus", "active_compound": "Astragalus polysaccharide", "gene_symbol": "IL10", "interaction_type": "upregulate", "mechanism": "上调IL-10抗炎细胞因子", "confidence_score": 0.79, "source": "literature"},
    {"herb_name": "Astragalus", "active_compound": "Astragaloside IV", "gene_symbol": "RAB27A", "interaction_type": "upregulate", "mechanism": "促进RAB27A表达增加外泌体分泌", "confidence_score": 0.75, "source": "literature"},
    {"herb_name": "Curcumin", "active_compound": "Curcumin", "gene_symbol": "NFKB1", "interaction_type": "inhibit", "mechanism": "直接抑制NF-κB核转位，抗炎", "confidence_score": 0.95, "source": "TCMSP"},
    {"herb_name": "Curcumin", "active_compound": "Curcumin", "gene_symbol": "VEGFA", "interaction_type": "inhibit", "mechanism": "抑制HIF-1α/VEGF轴，抗血管生成", "confidence_score": 0.91, "source": "literature"},
    {"herb_name": "Curcumin", "active_compound": "Curcumin", "gene_symbol": "CD63", "interaction_type": "modulate", "mechanism": "调控外泌体CD63表达影响外泌体分泌", "confidence_score": 0.72, "source": "literature"},
    {"herb_name": "Ginger", "active_compound": "6-gingerol", "gene_symbol": "TNF", "interaction_type": "inhibit", "mechanism": "抑制TNF-α产生，抗炎", "confidence_score": 0.87, "source": "HIT"},
    {"herb_name": "Ginger", "active_compound": "Ginger exosome-miR-168a", "gene_symbol": "LDLRAP1", "interaction_type": "downregulate", "mechanism": "植物外泌体miRNA跨界调控肝脏基因", "confidence_score": 0.83, "source": "literature"},
    {"herb_name": "Berberine", "active_compound": "Berberine", "gene_symbol": "MAPK1", "interaction_type": "inhibit", "mechanism": "抑制ERK/MAPK信号通路", "confidence_score": 0.89, "source": "TCMSP"},
    {"herb_name": "Berberine", "active_compound": "Berberine", "gene_symbol": "AKT1", "interaction_type": "inhibit", "mechanism": "抑制PI3K/AKT通路激活", "confidence_score": 0.86, "source": "HIT"},
    {"herb_name": "Berberine", "active_compound": "Berberine", "gene_symbol": "DNMT1", "interaction_type": "inhibit", "mechanism": "抑制DNA甲基化酶，表观遗传调控", "confidence_score": 0.78, "source": "literature"},
    {"herb_name": "Berberine", "active_compound": "Berberine", "gene_symbol": "SIRT1", "interaction_type": "activate", "mechanism": "激活SIRT1延缓衰老", "confidence_score": 0.80, "source": "literature"},
    {"herb_name": "Ginseng", "active_compound": "Ginsenoside Rg1", "gene_symbol": "BCL2", "interaction_type": "upregulate", "mechanism": "上调Bcl-2抗凋亡，神经保护", "confidence_score": 0.84, "source": "TCMSP"},
    {"herb_name": "Ginseng", "active_compound": "Ginsenoside Rb1", "gene_symbol": "HIF1A", "interaction_type": "inhibit", "mechanism": "抑制HIF-1α，改善缺氧反应", "confidence_score": 0.81, "source": "literature"},
    {"herb_name": "Ginseng", "active_compound": "Ginseng exosome", "gene_symbol": "MECP2", "interaction_type": "modulate", "mechanism": "人参来源外泌体调控MECP2表达", "confidence_score": 0.68, "source": "literature"},
    {"herb_name": "Resveratrol", "active_compound": "Resveratrol", "gene_symbol": "SIRT1", "interaction_type": "activate", "mechanism": "激活SIRT1去乙酰化酶，抗衰老", "confidence_score": 0.92, "source": "TCMSP"},
    {"herb_name": "Resveratrol", "active_compound": "Resveratrol", "gene_symbol": "MTOR", "interaction_type": "inhibit", "mechanism": "抑制mTOR通路，自噬促进", "confidence_score": 0.88, "source": "HIT"},
    {"herb_name": "Acorus tatarinowii", "active_compound": "β-asarone", "gene_symbol": "SHANK3", "interaction_type": "modulate", "mechanism": "调节突触SHANK3蛋白表达，改善ASD行为", "confidence_score": 0.71, "source": "literature"},
    {"herb_name": "Poria cocos", "active_compound": "Pachymic acid", "gene_symbol": "NLGN3", "interaction_type": "upregulate", "mechanism": "上调突触后密度neuroligin-3", "confidence_score": 0.69, "source": "literature"},
    {"herb_name": "Astragalus", "active_compound": "APS", "gene_symbol": "RAB27B", "interaction_type": "upregulate", "mechanism": "黄芪多糖促进RAB27B调控外泌体出胞", "confidence_score": 0.73, "source": "literature"},
    {"herb_name": "Curcumin", "active_compound": "Curcumin", "gene_symbol": "ALIX", "interaction_type": "modulate", "mechanism": "调控ALIX参与外泌体生物发生", "confidence_score": 0.70, "source": "literature"},
]

DISEASE_GENE_DATA = [
    {"disease_name": "Autism Spectrum Disorder", "gene_symbol": "SHANK3", "association_type": "causal_mutation", "score": 0.9, "tcm_herb": "Acorus tatarinowii"},
    {"disease_name": "Autism Spectrum Disorder", "gene_symbol": "NLGN3", "association_type": "causal_mutation", "score": 0.85, "tcm_herb": "Poria cocos"},
    {"disease_name": "Autism Spectrum Disorder", "gene_symbol": "NRXN1", "association_type": "susceptibility", "score": 0.80, "tcm_herb": "Acorus tatarinowii"},
    {"disease_name": "Autism Spectrum Disorder", "gene_symbol": "MECP2", "association_type": "causal_mutation", "score": 0.95, "tcm_herb": "Ginseng"},
    {"disease_name": "Autism Spectrum Disorder", "gene_symbol": "FMR1", "association_type": "causal_mutation", "score": 0.92, "tcm_herb": ""},
    {"disease_name": "Colorectal Cancer", "gene_symbol": "TP53", "association_type": "driver_mutation", "score": 0.95, "tcm_herb": "Astragalus"},
    {"disease_name": "Breast Cancer", "gene_symbol": "VEGFA", "association_type": "biomarker", "score": 0.88, "tcm_herb": "Curcumin"},
    {"disease_name": "Lung Cancer", "gene_symbol": "EGFR", "association_type": "driver_mutation", "score": 0.93, "tcm_herb": "Berberine"},
    {"disease_name": "Inflammatory Bowel Disease", "gene_symbol": "TNF", "association_type": "susceptibility", "score": 0.87, "tcm_herb": "Berberine"},
    {"disease_name": "Alzheimer Disease", "gene_symbol": "SIRT1", "association_type": "protective", "score": 0.78, "tcm_herb": "Resveratrol"},
]

def get_supabase_client():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            pass
    return None

def save_herb_gene(client, data):
    if client:
        try:
            client.table("herb_gene_relations").upsert(data).execute()
            return True
        except Exception as e:
            print(f"  Supabase error: {e}")
            return False
    else:
        try:
            from src.database.init_db import get_connection
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT OR IGNORE INTO herb_gene_relations
                (herb_name, active_compound, gene_symbol, interaction_type, mechanism, confidence_score, source)
                VALUES (?,?,?,?,?,?,?)
            """, (data["herb_name"], data.get("active_compound",""), data["gene_symbol"],
                  data["interaction_type"], data.get("mechanism",""),
                  data.get("confidence_score",0.0), data.get("source","")))
            conn.commit()
            conn.close()
            return c.rowcount > 0
        except Exception as e:
            print(f"  DB error: {e}")
            return False

def save_disease_gene(client, data):
    if client:
        try:
            client.table("disease_gene_network").upsert(data).execute()
            return True
        except Exception as e:
            print(f"  Supabase error: {e}")
            return False
    else:
        try:
            from src.database.init_db import get_connection
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT OR IGNORE INTO disease_gene_network
                (disease_name, gene_symbol, association_type, score, tcm_herb)
                VALUES (?,?,?,?,?)
            """, (data["disease_name"], data["gene_symbol"],
                  data.get("association_type",""), data.get("score",0.0), data.get("tcm_herb","")))
            conn.commit()
            conn.close()
            return c.rowcount > 0
        except Exception as e:
            return False

def fetch_string_interactions(gene_symbol, min_score=700):
    try:
        r = requests.get("https://string-db.org/api/json/network", params={
            "identifiers": gene_symbol, "species": 9606,
            "required_score": min_score, "limit": 20
        }, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  STRING error: {e}")
    return []

def run():
    print("🌿 Starting Herb-Gene relations crawler...")
    client = get_supabase_client()

    print(f"\n  💊 Loading {len(HERB_GENE_KNOWLEDGE)} herb-gene relations...")
    hg_added = sum(1 for r in HERB_GENE_KNOWLEDGE if save_herb_gene(client, r))
    print(f"  ✅ Herb-gene added: {hg_added}")

    print(f"\n  🏥 Loading {len(DISEASE_GENE_DATA)} disease-gene associations...")
    dg_added = sum(1 for r in DISEASE_GENE_DATA if save_disease_gene(client, r))
    print(f"  ✅ Disease-gene added: {dg_added}")

    print(f"\n  🔗 Fetching protein interactions from STRING DB...")
    key_genes = ["TP53", "VEGFA", "NFKB1", "AKT1", "STAT3"]
    for gene in key_genes:
        interactions = fetch_string_interactions(gene)
        edges = []
        for item in interactions[:5]:
            edges.append({
                "source_id": item.get("preferredName_A", gene),
                "target_id": item.get("preferredName_B", ""),
                "edge_type": "protein_interaction",
                "weight": item.get("score", 0) / 1000.0,
            })
        if edges and client:
            try:
                client.table("network_edges").upsert(edges).execute()
            except Exception as e:
                print(f"  STRING save error: {e}")
        elif edges:
            try:
                from src.database.init_db import get_connection
                conn = get_connection()
                c = conn.cursor()
                for e in edges:
                    c.execute("INSERT OR IGNORE INTO network_edges (source_id,target_id,edge_type,weight) VALUES (?,?,?,?)",
                              (e["source_id"],e["target_id"],e["edge_type"],e["weight"]))
                conn.commit()
                conn.close()
            except:
                pass
        print(f"    {gene}: {len(interactions)} interactions")
        time.sleep(1)

    print(f"\n✅ Herb-gene crawler done. Total: {hg_added + dg_added}")
    return hg_added + dg_added

if __name__ == "__main__":
    run()
