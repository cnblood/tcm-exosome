import requests
import time
import json
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

TCM_EXOSOME_MIRNA = [
    {"mirna_id": "hsa-miR-168a-5p", "source": "ginger", "targets": ["LDLRAP1","SOCS1"], "effect": "肝保护"},
    {"mirna_id": "hsa-miR-396", "source": "ginger", "targets": ["GRF"], "effect": "抗肿瘤"},
    {"mirna_id": "hsa-miR-23a-3p", "source": "ginseng", "targets": ["PTEN","PDCD4"], "effect": "神经保护"},
    {"mirna_id": "hsa-miR-21-5p", "source": "astragalus", "targets": ["PTEN","PDCD4","RECK"], "effect": "抗炎/抗肿瘤"},
    {"mirna_id": "hsa-miR-146a-5p", "source": "astragalus", "targets": ["TRAF6","IRAK1"], "effect": "抗炎免疫调节"},
    {"mirna_id": "hsa-miR-155-5p", "source": "berberine_induced", "targets": ["SHIP1","SOCS1"], "effect": "免疫调节"},
    {"mirna_id": "ath-miR-159a", "source": "plant_exosome", "targets": ["TCF7"], "effect": "抗肿瘤"},
    {"mirna_id": "osa-miR-168a", "source": "rice_exosome", "targets": ["LDLRAP1"], "effect": "脂质代谢"},
    {"mirna_id": "hsa-miR-126-3p", "source": "tcm_general", "targets": ["VEGFA","PIK3R2"], "effect": "血管生成抑制"},
    {"mirna_id": "hsa-miR-34a-5p", "source": "tcm_general", "targets": ["BCL2","CDK6","MET"], "effect": "促凋亡"},
    {"mirna_id": "hsa-miR-106b-5p", "source": "tcm_neuro", "targets": ["MECP2","SHANK3"], "effect": "神经发育"},
    {"mirna_id": "hsa-miR-132-3p", "source": "tcm_neuro", "targets": ["DNMT3A","MECP2"], "effect": "突触可塑性"},
    {"mirna_id": "hsa-miR-137", "source": "tcm_neuro", "targets": ["SHANK2","NRXN1"], "effect": "ASD相关神经调控"},
    {"mirna_id": "hsa-miR-193a-3p", "source": "exosome_biogenesis", "targets": ["RAB27A","SMPD3"], "effect": "外泌体分泌调控"},
]

EXOSOME_CARGO_DATA = [
    {"cargo_type": "protein", "cargo_name": "CD63 Tetraspanin", "tcm_herb": "", "target_gene": "ITGB1", "target_pathway": "cell adhesion", "biological_effect": "外泌体标志物，参与膜融合"},
    {"cargo_type": "protein", "cargo_name": "CD9 Tetraspanin", "tcm_herb": "", "target_gene": "EGFR", "target_pathway": "cell signaling", "biological_effect": "外泌体标志物，信号转导"},
    {"cargo_type": "protein", "cargo_name": "Heat Shock Protein 70", "tcm_herb": "", "target_gene": "HSPA1A", "target_pathway": "protein folding", "biological_effect": "应激反应，免疫激活"},
    {"cargo_type": "protein", "cargo_name": "TSG101", "tcm_herb": "", "target_gene": "TP53", "target_pathway": "ESCRT pathway", "biological_effect": "外泌体生物发生关键蛋白"},
    {"cargo_type": "miRNA", "cargo_name": "miR-21-5p", "tcm_herb": "astragalus", "target_gene": "PTEN", "target_pathway": "PI3K/AKT", "biological_effect": "黄芪处理后外泌体富集，靶向PTEN抗炎"},
    {"cargo_type": "miRNA", "cargo_name": "miR-146a-5p", "tcm_herb": "astragalus", "target_gene": "IRAK1", "target_pathway": "NF-κB", "biological_effect": "调节NF-κB信号，抗炎"},
    {"cargo_type": "miRNA", "cargo_name": "miR-168a-5p", "tcm_herb": "ginger", "target_gene": "LDLRAP1", "target_pathway": "lipid metabolism", "biological_effect": "植物外泌体跨界调控肝脏脂质代谢"},
    {"cargo_type": "lncRNA", "cargo_name": "HOTAIR", "tcm_herb": "", "target_gene": "HOXD10", "target_pathway": "epigenetics", "biological_effect": "表观遗传调控，中药可干预"},
    {"cargo_type": "protein", "cargo_name": "VEGF", "tcm_herb": "curcumin_inhibited", "target_gene": "VEGFR2", "target_pathway": "angiogenesis", "biological_effect": "姜黄素抑制肿瘤外泌体VEGF分泌"},
    {"cargo_type": "protein", "cargo_name": "SHANK3", "tcm_herb": "tcm_neuro", "target_gene": "SHANK3", "target_pathway": "synapse", "biological_effect": "突触蛋白，ASD核心靶点"},
    {"cargo_type": "miRNA", "cargo_name": "miR-137", "tcm_herb": "tcm_neuro", "target_gene": "SHANK2", "target_pathway": "neuronal development", "biological_effect": "ASD风险miRNA，中药可能调控"},
]

def get_supabase_client():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            pass
    return None

def save_mirna_supabase(client, mirna_data):
    try:
        client.table("mirna").upsert({
            "mirna_id": mirna_data["mirna_id"],
            "source": mirna_data.get("source", ""),
            "target_genes": json.dumps(mirna_data.get("targets", [])),
            "function_note": mirna_data.get("effect", ""),
            "is_exosome_cargo": True,
        }, on_conflict="mirna_id").execute()
        return True
    except Exception as e:
        print(f"    Supabase mirna error: {e}")
        return False

def save_mirna_sqlite(mirna_data):
    try:
        from src.database.init_db import get_connection
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO mirna
            (mirna_id, source_organism, target_genes, function_note, is_exosome_cargo)
            VALUES (?,?,?,?,?)
        """, (mirna_data["mirna_id"], mirna_data.get("source",""),
              json.dumps(mirna_data.get("targets",[])),
              mirna_data.get("effect",""), 1))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"    DB error: {e}")
        return False

def save_cargo_supabase(client, cargo_data):
    try:
        client.table("exosome_cargo").upsert(cargo_data).execute()
        return True
    except Exception as e:
        print(f"    Supabase cargo error: {e}")
        return False

def save_cargo_sqlite(cargo_data):
    try:
        from src.database.init_db import get_connection
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO exosome_cargo
            (cargo_type, cargo_name, tcm_herb, target_gene, target_pathway, biological_effect)
            VALUES (?,?,?,?,?,?)
        """, (cargo_data["cargo_type"], cargo_data["cargo_name"],
              cargo_data.get("tcm_herb",""), cargo_data.get("target_gene",""),
              cargo_data.get("target_pathway",""), cargo_data.get("biological_effect","")))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"    DB error: {e}")
        return False

def run():
    print("🧬 Starting miRNA & ExoCarta crawler...")
    client = get_supabase_client()

    print(f"\n  📌 Loading {len(TCM_EXOSOME_MIRNA)} miRNA records...")
    mirna_added = 0
    for m in TCM_EXOSOME_MIRNA:
        if client:
            if save_mirna_supabase(client, m):
                mirna_added += 1
        else:
            if save_mirna_sqlite(m):
                mirna_added += 1
    print(f"  ✅ miRNA added: {mirna_added}")

    print(f"\n  📦 Loading {len(EXOSOME_CARGO_DATA)} exosome cargo records...")
    cargo_added = 0
    for c in EXOSOME_CARGO_DATA:
        if client:
            if save_cargo_supabase(client, c):
                cargo_added += 1
        else:
            if save_cargo_sqlite(c):
                cargo_added += 1
    print(f"  ✅ Cargo added: {cargo_added}")

    print(f"\n✅ miRNA/Cargo crawler done.")
    return mirna_added + cargo_added

if __name__ == "__main__":
    run()
