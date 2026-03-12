import os, time
# SUPABASE_URL set via environment variable
os.environ['SUPABASE_KEY'] = os.environ.get("SUPABASE_KEY")

from supabase import create_client
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

HERB_GENE_7 = {
    "Coptis chinensis": [
        ("PRKAA1", "activate",   "灏忔獥纰辨縺娲籄MPK闄嶈绯?,           0.93),
        ("NFKB1",  "inhibit",    "鎶戝埗NF-魏B鎶楃値鎶楄弻",              0.91),
        ("LDLR",   "upregulate", "涓婅皟LDLR闄嶄綆LDL闄嶈剛",            0.90),
        ("STAT3",  "inhibit",    "鎶戝埗STAT3鎶楄偪鐦?,                 0.88),
        ("MTOR",   "inhibit",    "鎶戝埗mTOR鎶楄偪鐦?,                  0.87),
        ("SCN5A",  "inhibit",    "鎶戝埗閽犻€氶亾鎶楀績寰嬪け甯?,            0.86),
    ],
    "Rehmannia glutinosa": [
        ("INS",    "modulate",   "鍦伴粍鑻疯皟鎺ц儼宀涚礌鍒嗘硨闄嶇硸",       0.88),
        ("RANKL",  "inhibit",    "鎶戝埗鐮撮缁嗚優娲诲寲琛ヨ偩澹",       0.86),
        ("ACHE",   "inhibit",    "鎶戝埗AChE鏀瑰杽璁ょ煡",                0.85),
        ("NRF2",   "activate",   "鎶楁哀鍖栦繚鑲?,                      0.84),
        ("EPO",    "upregulate", "淇冭繘绾㈢粏鑳炵敓鎴愯ˉ琛€",              0.83),
    ],
    "Dioscorea nipponica": [
        ("PTGS2",  "inhibit",    "绌垮北榫欑殏鑻锋姂鍒禖OX-2鎶楃値",        0.88),
        ("TNF",    "inhibit",    "鎶戝埗TNF-伪绫婚婀?,                0.87),
        ("IL6",    "inhibit",    "鎶戝埗IL-6",                        0.86),
        ("NFKB1",  "inhibit",    "鎶戝埗NF-魏B",                      0.85),
        ("PPARG",  "activate",   "婵€娲籔PAR纬鎶楀姩鑴夌‖鍖?,            0.83),
    ],
    "Curcuma longa": [
        ("NFKB1",  "inhibit",    "濮滈粍绱犲己鏁堟姂鍒禢F-魏B鎶楃値",       0.94),
        ("STAT3",  "inhibit",    "鎶戝埗STAT3鎶楄偪鐦?,                 0.92),
        ("BCL2",   "inhibit",    "淇冭偪鐦ゅ噵浜?,                      0.91),
        ("TGFB1",  "inhibit",    "鎶戝埗TGF-尾鎶楃氦缁村寲",             0.90),
        ("VEGFA",  "inhibit",    "鎶戝埗VEGF鎶楄绠＄敓鎴?,              0.89),
        ("MTOR",   "inhibit",    "鎶戝埗mTOR鎶楄偪鐦?,                  0.88),
    ],
    "Astragalus membranaceus": [
        ("MTOR",   "activate",   "榛勮姫澶氱硸婵€娲籱TOR澧炲己鍏嶇柅",       0.89),
        ("TGFB1",  "inhibit",    "鎶戝埗TGF-尾鍑忓皯鑲剧氦缁村寲",         0.88),
        ("VEGFA",  "upregulate", "淇冭繘琛€绠℃柊鐢熶繚鎶ゅ績鑲?,            0.87),
        ("TP53",   "modulate",   "璋冩帶p53鎶楄偪鐦?,                   0.85),
        ("IL12",   "upregulate", "婵€娲籒K缁嗚優澧炲己鍏嶇柅",              0.86),
        ("STAT3",  "modulate",   "璋冩帶JAK-STAT鍏嶇柅",               0.84),
    ],
    "Salvia rosmarinus": [
        ("ACHE",   "inhibit",    "杩疯凯棣欓吀鎶戝埗AChE鏀瑰杽璁ょ煡",       0.88),
        ("NRF2",   "activate",   "婵€娲籒rf2寮烘晥鎶楁哀鍖?,              0.90),
        ("NFKB1",  "inhibit",    "鎶戝埗NF-魏B绁炵粡淇濇姢",              0.87),
        ("PTGS2",  "inhibit",    "鎶戝埗COX-2鎶楃値",                  0.86),
        ("SIRT1",  "activate",   "婵€娲籗IRT1鎶楄“鑰?,                 0.85),
    ],
    "Nelumbo nucifera": [
        ("PPARG",  "activate",   "鑽峰彾纰辨縺娲籔PAR纬鍑忚偉",            0.88),
        ("AMPK",   "activate",   "婵€娲籄MPK闄嶈剛",                    0.87),
        ("FASN",   "inhibit",    "鎶戝埗鑴傝偑鍚堟垚閰?,                  0.86),
        ("NFKB1",  "inhibit",    "鎶戝埗NF-魏B姝㈣娑堣偪",              0.85),
        ("HTR2A",  "modulate",   "璋冩帶5-HT2A鍙椾綋瀹夌",              0.83),
    ],
}

existing = client.table("herb_gene_relations").select("herb_name,gene_symbol").execute()
existing_set = set((d["herb_name"], d["gene_symbol"]) for d in existing.data)

to_insert = []
for herb, relations in HERB_GENE_7.items():
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


