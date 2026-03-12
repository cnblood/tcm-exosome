#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中药-基因关联扩展 v3.0：从77味扩展到100味
新增23味中药
运行：python src/database/herb_gene_v3.py
"""
import os, time
os.environ.setdefault('SUPABASE_URL', '')
os.environ.setdefault('SUPABASE_KEY', '')

HERB_GENE_NEW = {
    # ── 补虚药 ──
    "Panax quinquefolius": [
        ("AKT1",   "activate",   "西洋参皂苷激活AKT通路抗疲劳",    0.88),
        ("INSR",   "activate",   "改善胰岛素敏感性降血糖",          0.87),
        ("BDNF",   "upregulate", "上调BDNF改善认知",                0.86),
        ("NRF2",   "activate",   "抗氧化应激",                      0.84),
        ("IL6",    "inhibit",    "抑制炎症因子",                    0.83),
    ],
    "Angelica dahurica": [
        ("PTGS2",  "inhibit",    "白芷香豆素抑制COX-2镇痛",         0.87),
        ("CYP1A2", "inhibit",    "抑制肝药酶",                      0.85),
        ("TRPV1",  "modulate",   "调控痛觉感受器",                  0.83),
        ("NFKB1",  "inhibit",    "抑制NF-κB抗炎",                  0.82),
    ],
    "Ligusticum sinense": [
        ("NOS3",   "upregulate", "藁本内酯上调eNOS扩张血管",        0.87),
        ("CACNA1C","inhibit",    "钙拮抗舒张平滑肌",                0.86),
        ("PTGS2",  "inhibit",    "抑制COX-2止痛",                  0.85),
        ("HTR1B",  "modulate",   "调控5-HT受体治偏头痛",            0.83),
    ],
    "Paeonia lactiflora": [
        ("FOXP3",  "upregulate", "芍药苷上调Treg细胞抑制自免",      0.90),
        ("TGFB1",  "inhibit",    "抑制TGF-β肝纤维化",             0.88),
        ("CACNA1C","inhibit",    "钙拮抗解痉止痛",                  0.87),
        ("NFKB1",  "inhibit",    "抑制NF-κB抗炎",                  0.86),
        ("ESR1",   "modulate",   "调控雌激素受体调经",              0.85),
        ("IL17A",  "inhibit",    "抑制IL-17类风湿",                0.84),
    ],
    "Atractylodes lancea": [
        ("PPARG",  "activate",   "苍术酮激活PPARγ抗炎",            0.87),
        ("NFKB1",  "inhibit",    "抑制NF-κB燥湿",                  0.86),
        ("AMPK",   "activate",   "激活AMPK改善代谢",                0.85),
        ("IL6",    "inhibit",    "抑制IL-6",                        0.83),
        ("MUC5AC", "modulate",   "调控黏液分泌",                    0.81),
    ],
    # ── 清热泻火药 ──
    "Anemarrhena asphodeloides": [
        ("ACHE",   "inhibit",    "知母皂苷抑制AChE改善认知",        0.89),
        ("NFKB1",  "inhibit",    "抑制NF-κB清热泻火",              0.87),
        ("INS",    "modulate",   "调控胰岛素降血糖",                0.86),
        ("IL6",    "inhibit",    "抑制IL-6退热",                    0.85),
        ("SIRT1",  "activate",   "激活SIRT1抗衰老",                 0.83),
    ],
    "Gardenia jasminoides": [
        ("NFKB1",  "inhibit",    "栀子苷抑制NF-κB退黄疸",          0.89),
        ("IL6",    "inhibit",    "抑制IL-6退热",                    0.88),
        ("PTGS2",  "inhibit",    "抑制COX-2消肿",                  0.86),
        ("HIF1A",  "inhibit",    "抑制HIF-1α保护心肌",             0.84),
        ("BCL2",   "modulate",   "调控凋亡通路",                    0.83),
    ],
    "Pulsatilla chinensis": [
        ("NFKB1",  "inhibit",    "白头翁皂苷抑制NF-κB抗肠炎",     0.88),
        ("IL6",    "inhibit",    "抑制炎症因子",                    0.87),
        ("PTGS2",  "inhibit",    "抑制COX-2",                      0.86),
        ("BCL2",   "inhibit",    "抗阿米巴原虫促凋亡",              0.84),
        ("TNF",    "inhibit",    "抑制TNF-α",                      0.83),
    ],
    # ── 收涩药 ──
    "Schisandra chinensis": [
        ("NRF2",   "activate",   "五味子素激活Nrf2保肝",            0.92),
        ("TGFB1",  "inhibit",    "抑制TGF-β抗纤维化",             0.89),
        ("SIRT1",  "activate",   "激活SIRT1神经保护",               0.87),
        ("GABRA1", "activate",   "激活GABA受体安神",                0.85),
        ("CYP3A4", "modulate",   "调控药物代谢",                    0.83),
    ],
    "Rosa laevigata": [
        ("INSR",   "modulate",   "金樱子多糖改善胰岛素信号",        0.85),
        ("NFKB1",  "inhibit",    "抑制NF-κB缩尿涩肠",              0.84),
        ("AQP2",   "modulate",   "调控水通道蛋白",                  0.82),
        ("IL6",    "inhibit",    "抑制炎症",                        0.81),
    ],
    # ── 温里药 ──
    "Zingiber officinale": [
        ("HTR3A",  "inhibit",    "姜辣素抑制5-HT3受体止吐",        0.92),
        ("PTGS2",  "inhibit",    "抑制COX-2抗炎止痛",              0.90),
        ("TRPV1",  "activate",   "激活TRPV1产热散寒",               0.88),
        ("NFKB1",  "inhibit",    "抑制NF-κB抗炎",                  0.87),
        ("PPARG",  "activate",   "激活PPARγ改善代谢",              0.85),
        ("IL6",    "inhibit",    "抑制IL-6",                        0.84),
    ],
    "Aconitum carmichaelii": [
        ("SCN5A",  "modulate",   "乌头碱调控钠通道强心",            0.88),
        ("CACNA1C","modulate",   "调控钙通道",                      0.87),
        ("ADRB1",  "activate",   "激活β1受体强心",                  0.86),
        ("TRPV1",  "activate",   "激活TRPV1镇痛",                   0.85),
        ("KCNQ1",  "modulate",   "调控钾通道",                      0.83),
    ],
    "Alpinia officinarum": [
        ("TRPV1",  "activate",   "高良姜素激活TRPV1温中散寒",      0.87),
        ("PTGS2",  "inhibit",    "抑制COX-2止痛",                  0.86),
        ("HTR3A",  "inhibit",    "抑制5-HT3止呕",                  0.85),
        ("NFKB1",  "inhibit",    "抑制NF-κB消炎",                  0.84),
    ],
    # ── 化湿药 ──
    "Pogostemon cablin": [
        ("HTR3A",  "inhibit",    "广藿香醇抑制5-HT3止呕",          0.88),
        ("NFKB1",  "inhibit",    "抑制NF-κB化湿",                  0.86),
        ("TRPV1",  "modulate",   "调控TRPV1",                      0.84),
        ("IL6",    "inhibit",    "抑制IL-6",                        0.83),
    ],
    "Amomum villosum": [
        ("HTR4",   "activate",   "砂仁挥发油激活5-HT4促胃动力",    0.88),
        ("TRPV1",  "activate",   "激活TRPV1温中",                   0.86),
        ("PTGS2",  "inhibit",    "抑制COX-2止痛",                  0.85),
        ("NFKB1",  "inhibit",    "抑制NF-κB",                      0.83),
    ],
    # ── 驱虫药 ──
    "Artemisia scoparia": [
        ("NFKB1",  "inhibit",    "茵陈蒿素抑制NF-κB保肝退黄",     0.90),
        ("CYP2E1", "inhibit",    "抑制CYP2E1减少肝毒性",           0.88),
        ("TGFB1",  "inhibit",    "抑制肝纤维化",                    0.87),
        ("NRF2",   "activate",   "激活Nrf2抗氧化",                  0.86),
        ("IL6",    "inhibit",    "抑制炎症退黄",                    0.85),
    ],
    # ── 开窍药 ──
    "Acorus tatarinowii": [
        ("ACHE",   "inhibit",    "石菖蒲β细辛醚抑制AChE益智",     0.89),
        ("GABRA1", "modulate",   "调控GABA受体开窍",                0.87),
        ("BDNF",   "upregulate", "上调BDNF神经保护",                0.86),
        ("NFKB1",  "inhibit",    "抑制NF-κB神经炎症",              0.85),
        ("SLC6A4", "modulate",   "调控5-HT转运体",                  0.83),
    ],
    # ── 消食药 ──
    "Raphanus sativus": [
        ("HTR4",   "activate",   "莱菔子激活5-HT4受体促胃动力",    0.87),
        ("NFKB1",  "inhibit",    "抑制NF-κB消食化积",              0.85),
        ("ACE",    "inhibit",    "抑制ACE降压",                     0.83),
        ("MUC5AC", "modulate",   "调控气道黏液止咳",                0.82),
    ],
    # ── 外用药 ──
    "Tripterygium wilfordii": [
        ("NFKB1",  "inhibit",    "雷公藤甲素强效抑制NF-κB",        0.93),
        ("IL2",    "inhibit",    "抑制IL-2免疫抑制",                0.91),
        ("TNF",    "inhibit",    "抑制TNF-α类风湿",                0.90),
        ("FOXP3",  "upregulate", "上调Treg细胞免疫调节",            0.88),
        ("MAPK1",  "inhibit",    "抑制MAPK信号",                    0.87),
        ("IL17A",  "inhibit",    "抑制IL-17类风湿",                0.86),
    ],
    "Viola yedoensis": [
        ("NFKB1",  "inhibit",    "紫花地丁抑制NF-κB清热解毒",     0.87),
        ("IL6",    "inhibit",    "抑制IL-6消肿",                    0.86),
        ("BCL2",   "inhibit",    "促肿瘤凋亡",                      0.84),
        ("PTGS2",  "inhibit",    "抑制COX-2",                      0.83),
    ],
    # ── 利水渗湿 ──
    "Akebia quinata": [
        ("AQP2",   "upregulate", "木通苷促进利尿",                  0.86),
        ("NFKB1",  "inhibit",    "抑制NF-κB通淋",                  0.85),
        ("NOS3",   "upregulate", "上调eNOS",                        0.83),
        ("IL6",    "inhibit",    "抑制炎症",                        0.82),
    ],
    # ── 泻下药 ──
    "Linum usitatissimum": [
        ("FASN",   "inhibit",    "亚麻籽油抑制脂肪合成",            0.87),
        ("PPARA",  "activate",   "激活PPARα降脂",                  0.86),
        ("PTGS2",  "inhibit",    "omega-3抑制COX-2抗炎",           0.85),
        ("NFKB1",  "inhibit",    "抑制NF-κB",                      0.84),
        ("INSR",   "activate",   "改善胰岛素敏感性",                0.83),
    ],
    # ── 止咳平喘 ──
    "Aster tataricus": [
        ("MUC5AC", "inhibit",    "紫菀酮抑制黏蛋白分泌化痰",       0.87),
        ("ADRB2",  "activate",   "舒张支气管平滑肌",                0.86),
        ("NFKB1",  "inhibit",    "抑制NF-κB止咳",                  0.85),
        ("AKT1",   "inhibit",    "抑制AKT抗肺癌",                   0.83),
    ],
}

def run():
    from supabase import create_client
    client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

    # 获取已有记录
    existing = client.table("herb_gene_relations").select("herb_name,gene_symbol").execute()
    existing_set = set((d["herb_name"], d["gene_symbol"]) for d in existing.data)
    print(f"已有记录: {len(existing_set)} 条")

    to_insert = []
    for herb, relations in HERB_GENE_NEW.items():
        for gene, itype, mechanism, score in relations:
            if (herb, gene) not in existing_set:
                to_insert.append({
                    "herb_name": herb,
                    "gene_symbol": gene,
                    "interaction_type": itype,
                    "mechanism": mechanism,
                    "confidence_score": score,
                })

    print(f"待插入: {len(to_insert)} 条 ({len(HERB_GENE_NEW)} 味新中药)")

    inserted = 0
    for i in range(0, len(to_insert), 50):
        batch = to_insert[i:i+50]
        try:
            client.table("herb_gene_relations").insert(batch).execute()
            inserted += len(batch)
            print(f"  {inserted}/{len(to_insert)}...")
        except Exception as e:
            print(f"  Error: {e}")
        time.sleep(0.5)

    total = client.table("herb_gene_relations").select("id", count="exact").execute()
    r = client.table("herb_gene_relations").select("herb_name").execute()
    herbs = set(d["herb_name"] for d in r.data)
    print(f"\n完成！新增: {inserted} | 总量: {total.count} | 覆盖: {len(herbs)} 味中药")

if __name__ == "__main__":
    run()
