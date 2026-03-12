import os, time
# SUPABASE_URL set via environment variable
os.environ['SUPABASE_KEY'] = os.environ.get("SUPABASE_KEY")

from supabase import create_client
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# 鍏堟煡鐜版湁herb鍒楄〃
existing = client.table("herb_gene_relations").select("herb_name,gene_symbol").execute()
existing_set = set((d["herb_name"], d["gene_symbol"]) for d in existing.data)
print(f"宸叉湁璁板綍: {len(existing_set)} 鏉?)

from src.database.herb_gene_v2 import HERB_GENE_NEW

# 鍙彃鍏ヤ笉瀛樺湪鐨?to_insert = []
for herb, relations in HERB_GENE_NEW.items():
    for gene, itype, mechanism, score in relations:
        if (herb, gene) not in existing_set:
            to_insert.append({
                "herb_name": herb,
                "gene_symbol": gene,
                "interaction_type": itype,
                "mechanism": mechanism,
                "confidence_score": score,
                "evidence_level": "experimental",
                "source": "literature_review",
            })

print(f"寰呮彃鍏? {len(to_insert)} 鏉?)

inserted = 0
for i in range(0, len(to_insert), 50):
    batch = to_insert[i:i+50]
    try:
        client.table("herb_gene_relations").insert(batch).execute()
        inserted += len(batch)
        print(f"  {inserted}/{len(to_insert)}...")
    except Exception as e:
        print(f"  Error batch {i}: {e}")
    time.sleep(0.5)

r = client.table("herb_gene_relations").select("herb_name").execute()
herbs = set(d["herb_name"] for d in r.data)
total = client.table("herb_gene_relations").select("id", count="exact").execute()
print(f"\n瀹屾垚锛佹柊澧? {inserted} 鏉?| 鎬婚噺: {total.count} | 瑕嗙洊: {len(herbs)} 鍛充腑鑽?)


