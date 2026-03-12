import os, time
# SUPABASE_URL set via environment variable
os.environ['SUPABASE_KEY'] = os.environ.get("SUPABASE_KEY")

from supabase import create_client
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

HERB_GENE_FINAL = {
    "Bupleurum chinense": [
        ("NFKB1",  "inhibit",    "鏌磋儭鐨傝嫹鎶戝埗NF-魏B鐤忚倽瑙ｉ儊",     0.91),
        ("TGFB1",  "inhibit",    "鎶戝埗TGF-尾鑲濈氦缁村寲",             0.89),
        ("IL6",    "inhibit",    "鎶戝埗IL-6閫€鐑?,                    0.88),
        ("STAT3",  "inhibit",    "鎶戝埗STAT3鎶楄偪鐦?,                 0.86),
        ("CYP3A4", "modulate",   "璋冩帶鑲濊嵂閰朵唬璋?,                  0.84),
    ],
    "Reynoutria japonica": [
        ("SIRT1",  "activate",   "铏庢潠鐧借棞鑺﹂唶婵€娲籗IRT1鎶楄“鑰?,   0.91),
        ("NFKB1",  "inhibit",    "鎶戝埗NF-魏B鎶楃値",                  0.89),
        ("MTOR",   "inhibit",    "鎶戝埗mTOR鎶楄偪鐦?,                  0.88),
        ("TGFB1",  "inhibit",    "鎶戝埗鑲濈氦缁村寲",                    0.87),
        ("AMPK",   "activate",   "婵€娲籄MPK鏀瑰杽浠ｈ阿",                0.86),
    ],
    "Ligustrum lucidum": [
        ("SIRT1",  "activate",   "濂宠礊瀛愰綈澧╂灉閰告縺娲籗IRT1鎶楄“",   0.88),
        ("BCL2",   "upregulate", "淇濇姢鑲濈粏鑳炴姉鍑嬩骸",                0.86),
        ("IL2",    "upregulate", "澧炲己鍏嶇柅鍔熻兘",                    0.85),
        ("NRF2",   "activate",   "鎶楁哀鍖栦繚鎶よ鍔?,                  0.84),
        ("RANKL",  "inhibit",    "鎶戝埗鐮撮缁嗚優琛ヨ偩",                0.83),
    ],
    "Panax notoginseng": [
        ("PTGIS",  "upregulate", "涓変竷鐨傝嫹涓婅皟鍓嶅垪鐜礌鎶楄鏍?,     0.92),
        ("ITGA2B", "inhibit",    "鎶戝埗琛€灏忔澘GPIIb鑱氶泦",            0.91),
        ("VEGFA",  "modulate",   "璋冩帶VEGF姝㈣淇冩剤鍚?,              0.89),
        ("NOS3",   "upregulate", "涓婅皟eNOS鎵╁紶琛€绠?,                0.88),
        ("BCL2",   "upregulate", "淇濇姢绁炵粡缁嗚優鎶楀噵浜?,              0.86),
        ("NFKB1",  "inhibit",    "鎶戝埗NF-魏B娑堣偪姝㈢棝",              0.85),
    ],
    "Paeonia suffruticosa": [
        ("CYP19A1","inhibit",    "鐗′腹鐨腹鐨厷鎶戝埗鑺抽鍖栭叾",       0.89),
        ("PTGS2",  "inhibit",    "鎶戝埗COX-2娓呯儹鍑夎",              0.88),
        ("NFKB1",  "inhibit",    "鎶戝埗NF-魏B鎶楃値",                  0.87),
        ("IL17A",  "inhibit",    "鎶戝埗IL-17绫婚婀?,                0.85),
        ("BCL2",   "modulate",   "璋冩帶鍑嬩骸閫氳矾",                    0.83),
    ],
    "Glycyrrhiza uralensis": [
        ("NFKB1",  "inhibit",    "鐢樿崏閰告姂鍒禢F-魏B骞胯氨鎶楃値",       0.93),
        ("HSD11B1","inhibit",    "鎶戝埗11尾-HSD璋冭妭鐨川婵€绱?,       0.90),
        ("CYP3A4", "inhibit",    "鎶戝埗鑲濊嵂閰跺鏁堝噺姣?,              0.88),
        ("PTGS2",  "inhibit",    "鎶戝埗COX-2",                      0.87),
        ("IL6",    "inhibit",    "鎶戝埗IL-6",                        0.86),
        ("TGFB1",  "inhibit",    "鎶戝埗TGF-尾淇濊倽",                 0.85),
    ],
    "Atractylodes macrocephala": [
        ("PPARG",  "activate",   "鐧芥湳鍐呴叝婵€娲籔PAR纬鍋ヨ劸",          0.89),
        ("AMPK",   "activate",   "婵€娲籄MPK鏀瑰杽浠ｈ阿",                0.87),
        ("NFKB1",  "inhibit",    "鎶戝埗NF-魏B鐕ユ箍",                  0.86),
        ("AQP3",   "modulate",   "璋冩帶姘撮€氶亾铔嬬櫧鍒╂按",              0.84),
        ("IL6",    "inhibit",    "鎶戝埗IL-6",                        0.83),
        ("TGFB1",  "inhibit",    "鎶戝埗TGF-尾",                     0.82),
    ],
}

existing = client.table("herb_gene_relations").select("herb_name,gene_symbol").execute()
existing_set = set((d["herb_name"], d["gene_symbol"]) for d in existing.data)

to_insert = []
for herb, relations in HERB_GENE_FINAL.items():
    for gene, itype, mechanism, score in relations:
        if (herb, gene) not in existing_set:
            to_insert.append({
                "herb_name": herb,
                "gene_symbol": gene,
                "interaction_type": itype,
                "mechanism": mechanism,
                "confidence_score": score,
            })

print(f"寰呮彃鍏? {len(to_insert)} 鏉?)
inserted = 0
for i in range(0, len(to_insert), 50):
    try:
        client.table("herb_gene_relations").insert(to_insert[i:i+50]).execute()
        inserted += len(to_insert[i:i+50])
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(0.5)

total = client.table("herb_gene_relations").select("id", count="exact").execute()
r = client.table("herb_gene_relations").select("herb_name").execute()
herbs = set(d["herb_name"] for d in r.data)
print(f"瀹屾垚锛佹柊澧? {inserted} | 鎬婚噺: {total.count} | 瑕嗙洊: {len(herbs)} 鍛充腑鑽?)


