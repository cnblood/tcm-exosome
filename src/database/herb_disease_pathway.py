# -*- coding: utf-8 -*-
"""
中药-疾病 / 中药-通路 关联数据录入
运行：python src/database/herb_disease_pathway.py
"""
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# herb_name -> [(disease, effect, mechanism, confidence, evidence_level)]
HERB_DISEASE = {
    "Curcuma longa": [
        ("肝癌", "抑制增殖，促进凋亡", "抑制NF-κB/STAT3通路", 0.92, "临床前"),
        ("结直肠癌", "抑制肿瘤生长", "调控Wnt/β-catenin", 0.89, "临床前"),
        ("阿尔茨海默病", "减少β淀粉样蛋白沉积", "抗氧化，抗炎", 0.85, "临床前"),
        ("2型糖尿病", "改善胰岛素抵抗", "激活AMPK通路", 0.83, "临床"),
        ("类风湿关节炎", "减轻关节炎症", "抑制COX-2/NF-κB", 0.87, "临床"),
        ("非酒精性脂肪肝", "改善肝脏脂肪变性", "调控脂质代谢", 0.84, "临床前"),
    ],
    "Astragalus membranaceus": [
        ("肿瘤", "增强免疫，抑制转移", "激活NK细胞，调控mTOR", 0.88, "临床"),
        ("心力衰竭", "改善心功能", "抗氧化，保护心肌", 0.85, "临床"),
        ("慢性肾病", "减少蛋白尿，保护肾功能", "抑制TGF-β纤维化", 0.86, "临床"),
        ("糖尿病肾病", "延缓肾病进展", "调控VEGF/AKT", 0.83, "临床前"),
        ("病毒性感染", "抗病毒，免疫调节", "干扰素诱导", 0.82, "临床前"),
    ],
    "Panax ginseng": [
        ("阿尔茨海默病", "改善认知功能", "调控BDNF/SIRT1", 0.87, "临床"),
        ("肿瘤", "抑制增殖，诱导凋亡", "多靶点抗肿瘤", 0.85, "临床前"),
        ("糖尿病", "降低血糖，改善胰岛素敏感性", "激活AMPK", 0.86, "临床"),
        ("心血管疾病", "保护心肌，抗动脉硬化", "抗氧化，抗炎", 0.84, "临床"),
        ("疲劳综合征", "抗疲劳，提高耐力", "线粒体保护", 0.82, "临床"),
    ],
    "Salvia miltiorrhiza": [
        ("冠心病", "扩张冠状动脉，改善心肌缺血", "抑制血小板聚集", 0.93, "临床"),
        ("肝纤维化", "抑制肝星状细胞活化", "抑制TGF-β/Smad", 0.90, "临床前"),
        ("脑卒中", "保护神经，减少梗死面积", "抗氧化，促血管新生", 0.88, "临床前"),
        ("肝癌", "抑制肿瘤血管生成", "抑制VEGF", 0.86, "临床前"),
        ("骨质疏松", "促进成骨细胞增殖", "激活Wnt通路", 0.82, "临床前"),
    ],
    "Berberis vulgaris": [
        ("2型糖尿病", "降低血糖，改善胰岛素抵抗", "激活AMPK，抑制PTP1B", 0.91, "临床"),
        ("高脂血症", "降低LDL，升高HDL", "上调LDLR表达", 0.89, "临床"),
        ("结直肠癌", "抑制肿瘤增殖", "激活p53，抑制mTOR", 0.87, "临床前"),
        ("肠道炎症", "抑制肠道炎症，调节菌群", "抑制NF-κB", 0.88, "临床前"),
        ("非酒精性脂肪肝", "改善肝脏脂肪变性", "调控脂质代谢", 0.86, "临床"),
        ("心律失常", "抗心律失常", "调控离子通道", 0.83, "临床"),
    ],
    "Zingiber officinale": [
        ("恶心呕吐", "止吐，化疗后恶心", "调控5-HT受体", 0.92, "临床"),
        ("骨关节炎", "减轻关节疼痛", "抑制COX-2/PGE2", 0.87, "临床"),
        ("肿瘤", "抑制肿瘤增殖，诱导凋亡", "抑制NF-κB/MAPK", 0.84, "临床前"),
        ("2型糖尿病", "降低血糖，抗氧化", "激活PPAR-γ", 0.82, "临床前"),
        ("心血管疾病", "抗血小板，抗动脉硬化", "抑制血小板聚集", 0.83, "临床"),
    ],
    "Angelica sinensis": [
        ("月经不调", "调经止痛，补血活血", "调控雌激素受体", 0.90, "临床"),
        ("贫血", "补血，促进造血", "促进EPO生成", 0.87, "临床"),
        ("肝纤维化", "抑制肝纤维化", "抑制TGF-β/Smad", 0.85, "临床前"),
        ("骨质疏松", "促进骨形成", "激活Wnt/BMP通路", 0.83, "临床前"),
        ("脑缺血", "神经保护，改善认知", "抗氧化，抗凋亡", 0.84, "临床前"),
    ],
    "Glycyrrhiza uralensis": [
        ("病毒性肝炎", "抗病毒，保肝", "甘草酸抑制病毒复制", 0.91, "临床"),
        ("消化性溃疡", "保护胃黏膜，抗溃疡", "抑制H.pylori，促黏膜修复", 0.88, "临床"),
        ("哮喘", "抗炎，平喘", "抑制炎症介质释放", 0.85, "临床"),
        ("肾上腺功能不全", "调节肾上腺皮质功能", "皮质激素样作用", 0.83, "临床"),
        ("肿瘤", "抗肿瘤，增效减毒", "多靶点抗肿瘤", 0.82, "临床前"),
    ],
    "Paeonia lactiflora": [
        ("类风湿关节炎", "抑制关节炎症，减轻疼痛", "抑制T细胞活化", 0.89, "临床"),
        ("肝病", "保肝，抗纤维化", "调控TGF-β/Smad", 0.86, "临床"),
        ("月经不调", "调经，缓解痛经", "解痉止痛", 0.88, "临床"),
        ("高血压", "降压，扩张血管", "钙拮抗作用", 0.84, "临床前"),
        ("神经保护", "保护神经，抗焦虑", "调控GABA受体", 0.83, "临床前"),
    ],
    "Ligusticum chuanxiong": [
        ("脑卒中", "改善脑血流，神经保护", "抑制血小板聚集，扩血管", 0.91, "临床"),
        ("冠心病", "扩张冠脉，抗心肌缺血", "钙拮抗，抗血栓", 0.89, "临床"),
        ("头痛偏头痛", "止痛，改善头痛", "调控5-HT，扩血管", 0.87, "临床"),
        ("月经不调", "活血调经，行气止痛", "调节子宫收缩", 0.85, "临床"),
    ],
    "Ganoderma lucidum": [
        ("肿瘤", "增强免疫，抑制肿瘤", "激活NK/T细胞，抑制NF-κB", 0.90, "临床"),
        ("糖尿病", "降血糖，改善胰岛素抵抗", "调控胰岛素信号", 0.85, "临床前"),
        ("高血压", "降压，保护心血管", "抑制ACE，抗氧化", 0.84, "临床前"),
        ("肝病", "保肝，抗纤维化", "抗氧化，抗炎", 0.86, "临床前"),
        ("神经退行性疾病", "神经保护，抗氧化", "调控BDNF/SIRT1", 0.83, "临床前"),
        ("失眠", "改善睡眠质量", "调控GABA/5-HT", 0.82, "临床"),
    ],
    "Scutellaria baicalensis": [
        ("肺癌", "抑制肿瘤增殖，促凋亡", "调控STAT3/PI3K", 0.88, "临床前"),
        ("病毒性感染", "抗病毒，抗流感", "抑制病毒复制", 0.87, "临床前"),
        ("肠道炎症", "抑制结肠炎，保护肠黏膜", "抑制NF-κB/MAPK", 0.86, "临床前"),
        ("焦虑抑郁", "抗焦虑，改善情绪", "调控GABA/5-HT", 0.83, "临床前"),
        ("动脉硬化", "抗动脉粥样硬化", "抗氧化，抗炎", 0.85, "临床前"),
    ],
    "Lonicera japonica": [
        ("病毒性感染", "抗病毒，退热解毒", "抑制病毒复制，抗炎", 0.90, "临床"),
        ("细菌感染", "广谱抗菌", "破坏细菌细胞膜", 0.87, "临床前"),
        ("肠道炎症", "抑制肠道炎症", "抑制NF-κB", 0.85, "临床前"),
        ("糖尿病", "降血糖，抗氧化", "调控肠道菌群", 0.82, "临床前"),
    ],
    "Coptis chinensis": [
        ("2型糖尿病", "降血糖，改善胰岛素抵抗", "激活AMPK，抑制PTP1B", 0.93, "临床"),
        ("高脂血症", "降低血脂，抗动脉硬化", "上调LDLR", 0.90, "临床"),
        ("结直肠癌", "抑制肿瘤增殖，诱导凋亡", "调控Wnt/mTOR", 0.88, "临床前"),
        ("心律失常", "抗心律失常，保护心肌", "调控离子通道", 0.86, "临床"),
        ("肠道炎症", "抑制炎症，调节菌群", "抑制NF-κB，调节微生物组", 0.89, "临床"),
    ],
    "Poria cocos": [
        ("肿瘤", "免疫调节，增强抗肿瘤", "激活巨噬细胞，NK细胞", 0.87, "临床前"),
        ("失眠", "安神，改善睡眠", "调控GABA受体", 0.85, "临床"),
        ("脾胃虚弱", "健脾益胃，改善消化", "调节肠道功能", 0.88, "临床"),
        ("水肿", "利水渗湿，消肿", "利尿作用", 0.84, "临床"),
    ],
    "Rehmannia glutinosa": [
        ("糖尿病", "降血糖，保护胰岛β细胞", "调控胰岛素分泌", 0.87, "临床前"),
        ("骨质疏松", "促进骨形成，抑制骨吸收", "调控OPG/RANKL", 0.85, "临床前"),
        ("肾病", "保护肾功能，减少蛋白尿", "抗氧化，抗炎", 0.84, "临床前"),
        ("贫血", "补血，促进造血", "促进EPO生成", 0.83, "临床"),
        ("阿尔茨海默病", "改善认知，神经保护", "抑制ChE，抗氧化", 0.82, "临床前"),
    ],
}

# herb_name -> [(pathway_name, pathway_id, regulation, key_genes, confidence)]
HERB_PATHWAY = {
    "Curcuma longa": [
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,RELA,IKK,IκB", 0.93),
        ("PI3K-AKT信号通路", "hsa04151", "抑制", "AKT1,PI3K,PTEN,mTOR", 0.90),
        ("MAPK信号通路", "hsa04010", "抑制", "MAPK1,MAPK3,JNK,p38", 0.89),
        ("细胞凋亡通路", "hsa04210", "激活", "BCL2,BAX,CASP3,CASP9,TP53", 0.91),
        ("Wnt信号通路", "hsa04310", "抑制", "CTNNB1,GSK3B,APC", 0.85),
        ("AMPK信号通路", "hsa04152", "激活", "AMPK,ACC,HMGCR", 0.87),
    ],
    "Astragalus membranaceus": [
        ("mTOR信号通路", "hsa04150", "激活", "MTOR,S6K1,4EBP1", 0.88),
        ("JAK-STAT信号通路", "hsa04630", "激活", "STAT3,JAK1,JAK2", 0.86),
        ("TGF-β信号通路", "hsa04350", "抑制", "TGFB1,SMAD2,SMAD3", 0.87),
        ("细胞凋亡通路", "hsa04210", "抑制", "BCL2,BAX,CASP3", 0.84),
        ("HIF-1信号通路", "hsa04066", "调节", "HIF1A,VEGFA,EPO", 0.83),
    ],
    "Panax ginseng": [
        ("PI3K-AKT信号通路", "hsa04151", "激活", "AKT1,PI3K,PDK1", 0.89),
        ("MAPK信号通路", "hsa04010", "调节", "MAPK1,ERK1,JNK", 0.86),
        ("神经营养因子通路", "hsa04722", "激活", "BDNF,NTRK2,CREB", 0.87),
        ("胰岛素信号通路", "hsa04910", "激活", "INSR,IRS1,AKT1,GLUT4", 0.85),
        ("SIRT1去乙酰化通路", "hsa04152", "激活", "SIRT1,PGC1A,FOXO3", 0.84),
    ],
    "Salvia miltiorrhiza": [
        ("VEGF信号通路", "hsa04370", "抑制", "VEGFA,VEGFR2,eNOS", 0.91),
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,TNF,IL6", 0.90),
        ("TGF-β信号通路", "hsa04350", "抑制", "TGFB1,SMAD2,SMAD3,COL1A1", 0.89),
        ("血小板激活通路", "hsa04611", "抑制", "PTGS2,TXA2,PDGFR", 0.88),
        ("细胞凋亡通路", "hsa04210", "激活", "TP53,BCL2,BAX,CASP3", 0.86),
    ],
    "Berberis vulgaris": [
        ("AMPK信号通路", "hsa04152", "激活", "AMPK,ACC,CPT1,GLUT4", 0.93),
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,IKK,TNF", 0.90),
        ("细胞凋亡通路", "hsa04210", "激活", "TP53,BCL2,BAX,CASP3", 0.88),
        ("PI3K-AKT信号通路", "hsa04151", "抑制", "AKT1,mTOR,S6K1", 0.87),
        ("肠道菌群代谢通路", "hsa00190", "调节", "FXR,TGR5,GLP1", 0.85),
    ],
    "Zingiber officinale": [
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,COX2,PTGS2", 0.89),
        ("花生四烯酸代谢", "hsa00590", "抑制", "COX1,COX2,LOX5,PGE2", 0.88),
        ("MAPK信号通路", "hsa04010", "抑制", "MAPK1,JNK,p38", 0.86),
        ("5-羟色胺信号通路", "hsa04726", "调节", "HTR3,HTR4,TPH1", 0.85),
    ],
    "Ganoderma lucidum": [
        ("mTOR信号通路", "hsa04150", "抑制", "MTOR,S6K1,AKT1", 0.88),
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,TNF,IL6", 0.87),
        ("免疫调节通路", "hsa04660", "激活", "IL2,IFNG,NK细胞激活", 0.89),
        ("细胞凋亡通路", "hsa04210", "激活", "BCL2,BAX,CASP3,TP53", 0.86),
        ("SIRT1去乙酰化通路", "hsa04152", "激活", "SIRT1,PGC1A,FOXO3", 0.85),
        ("外泌体分泌通路", "hsa04144", "调节", "RAB27A,CD63,TSG101,ALIX", 0.82),
    ],
    "Scutellaria baicalensis": [
        ("JAK-STAT信号通路", "hsa04630", "抑制", "STAT3,JAK2,SOCS3", 0.89),
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,IKK,RELA", 0.88),
        ("PI3K-AKT信号通路", "hsa04151", "抑制", "PI3K,AKT1,mTOR", 0.87),
        ("MAPK信号通路", "hsa04010", "抑制", "MAPK1,ERK1,JNK,p38", 0.86),
        ("GABA信号通路", "hsa04727", "激活", "GABRA,GABRB,GAD1", 0.83),
    ],
    "Lonicera japonica": [
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,TNF,IL1B,IL6", 0.90),
        ("病毒感染通路", "hsa05161", "抑制", "TLR3,IFNA,IFNB,IRF3", 0.88),
        ("MAPK信号通路", "hsa04010", "抑制", "MAPK1,JNK,p38", 0.86),
        ("肠道菌群通路", "hsa05150", "调节", "TLR4,NF-κB,黏膜屏障", 0.84),
    ],
    "Coptis chinensis": [
        ("AMPK信号通路", "hsa04152", "激活", "AMPK,ACC,GLUT4,INSR", 0.93),
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,IKK,COX2", 0.91),
        ("Wnt信号通路", "hsa04310", "抑制", "CTNNB1,GSK3B,MYC", 0.88),
        ("mTOR信号通路", "hsa04150", "抑制", "MTOR,S6K1,4EBP1", 0.87),
        ("离子通道通路", "hsa04020", "调节", "KCNH2,SCN5A,CACNA1C", 0.85),
    ],
    "Ligusticum chuanxiong": [
        ("血小板激活通路", "hsa04611", "抑制", "PTGS2,TXA2,P2RY12", 0.91),
        ("VEGF信号通路", "hsa04370", "激活", "VEGFA,eNOS,FGF2", 0.88),
        ("钙信号通路", "hsa04020", "抑制", "CACNA1C,CALM1,CaMKII", 0.87),
        ("神经营养因子通路", "hsa04722", "激活", "BDNF,NGF,NTRK2", 0.85),
    ],
    "Angelica sinensis": [
        ("雌激素信号通路", "hsa04915", "调节", "ESR1,ESR2,GPER", 0.89),
        ("TGF-β信号通路", "hsa04350", "抑制", "TGFB1,SMAD2,SMAD3", 0.86),
        ("造血干细胞通路", "hsa04640", "激活", "EPO,SCF,EPOR", 0.87),
        ("Wnt/BMP通路", "hsa04310", "激活", "BMP2,RUNX2,SP7", 0.84),
    ],
    "Paeonia lactiflora": [
        ("T细胞受体通路", "hsa04660", "抑制", "TCR,CD4,IL2,NFAT", 0.88),
        ("TGF-β信号通路", "hsa04350", "抑制", "TGFB1,SMAD3,COL1A1", 0.86),
        ("钙/GABA信号通路", "hsa04020", "调节", "GABRA,CACNA1,CALM", 0.84),
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,TNF,IL6", 0.85),
    ],
    "Rehmannia glutinosa": [
        ("胰岛素分泌通路", "hsa04911", "激活", "INS,PDX1,GLUT2,GCK", 0.86),
        ("骨重塑通路", "hsa04380", "调节", "RANKL,OPG,RUNX2,BMP2", 0.85),
        ("AMPK信号通路", "hsa04152", "激活", "AMPK,PGC1A,SIRT1", 0.84),
        ("神经退行性通路", "hsa05010", "抑制", "APP,BACE1,MAPT,ACHE", 0.83),
    ],
    "Glycyrrhiza uralensis": [
        ("NF-κB信号通路", "hsa04064", "抑制", "NFKB1,TNF,IL6,COX2", 0.91),
        ("HPA轴通路", "hsa04927", "调节", "CRH,ACTH,皮质醇,11β-HSD", 0.87),
        ("病毒感染通路", "hsa05161", "抑制", "甘草酸,HBsAg,HCV复制", 0.89),
        ("胃黏膜保护通路", "hsa04978", "激活", "PGE2,黏液素,EGF", 0.86),
    ],
    "Poria cocos": [
        ("免疫调节通路", "hsa04660", "激活", "TLR4,NF-κB,IL12,TNF", 0.87),
        ("GABA信号通路", "hsa04727", "激活", "GABRA,GABRB,5-HT", 0.85),
        ("外泌体分泌通路", "hsa04144", "调节", "RAB27A,CD63,MVB", 0.75),
        ("mTOR信号通路", "hsa04150", "激活", "MTOR,S6K1,免疫细胞活化", 0.83),
    ],
}

def run():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 写入中药-疾病关联
    print("Step1: 写入中药-疾病关联...")
    disease_data = []
    for herb, relations in HERB_DISEASE.items():
        for disease, effect, mechanism, score, evidence in relations:
            disease_data.append({
                "herb_name": herb,
                "disease": disease,
                "effect": effect,
                "mechanism": mechanism,
                "confidence_score": score,
                "evidence_level": evidence,
            })

    inserted_d = 0
    for i in range(0, len(disease_data), 50):
        batch = disease_data[i:i+50]
        client.table("herb_disease_relations").upsert(
            batch, on_conflict="herb_name,disease"
        ).execute()
        inserted_d += len(batch)
        print(f"  {inserted_d}/{len(disease_data)}...")
    print(f"  Done: {inserted_d} herb-disease relations")

    # 写入中药-通路关联
    print("Step2: 写入中药-通路关联...")
    pathway_data = []
    for herb, relations in HERB_PATHWAY.items():
        for pathway, pid, regulation, genes, score in relations:
            pathway_data.append({
                "herb_name": herb,
                "pathway_name": pathway,
                "pathway_id": pid,
                "regulation": regulation,
                "key_genes": genes,
                "confidence_score": score,
            })

    inserted_p = 0
    for i in range(0, len(pathway_data), 50):
        batch = pathway_data[i:i+50]
        client.table("herb_pathway_relations").upsert(
            batch, on_conflict="herb_name,pathway_name"
        ).execute()
        inserted_p += len(batch)
        print(f"  {inserted_p}/{len(pathway_data)}...")
    print(f"  Done: {inserted_p} herb-pathway relations")

    print(f"\n完成！")
    print(f"  中药-疾病: {inserted_d} 条 ({len(HERB_DISEASE)} 味中药)")
    print(f"  中药-通路: {inserted_p} 条 ({len(HERB_PATHWAY)} 味中药)")

if __name__ == "__main__":
    run()
