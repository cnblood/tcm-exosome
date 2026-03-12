# -*- coding: utf-8 -*-
import os, json, re
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

TCM_HERBS = ["curcumin","berberine","astragalus","ginsenoside","ginger","resveratrol",
    "salvia","angelica","baicalein","baicalin","quercetin","luteolin","emodin",
    "tanshinone","puerarin","salvianolic","ligustilide","paeoniflorin","breviscapine",
    "lycium","cordyceps","ganoderma","panax","coptis","phellodendron","scutellaria",
    "lonicera","forsythia","taraxacum","dandelion","coix","atractylodes","poria",
    "glycyrrhizin","liquiritin","arctigenin","icariin","osthole","magnolol","honokiol",
    "wogonin","apigenin","kaempferol","naringenin","hesperidin","diosgenin","ursolic",
    "oleanolic","betulinic","celastrol","tripterygium","silibinin","silymarin",
    "schisandrin","ligustrin","rhein","aloe-emodin","physcion","chrysophanol",
    "matrine","oxymatrine","sophocarpine","tetrandrine","cepharanthine","sinomenine",
    "aconitine","lappaconitine","neferine","nuciferine","vinpocetine","huperzine",
    "traditional chinese medicine","chinese herbal","tcm","herbal medicine",
    "plant-derived","phytochemical","botanical"]

GENES = ["TP53","VEGFA","VEGFR","AKT1","AKT2","MTOR","BCL2","BAX","CASP3","CASP9",
    "NFKB1","NFKB","STAT3","STAT1","MAPK1","MAPK3","ERK1","ERK2","JNK","P38",
    "EGFR","HER2","MYC","KRAS","BRAF","PTEN","RB1","CDKN2A","MDM2","HIF1A",
    "TNF","IL6","IL1B","IL10","IL4","IL17","TGFB1","IFNG","CCL2","CXCL8",
    "MMP2","MMP9","CD44","CD63","CD9","CD81","RAB27A","TSG101","ALIX","HSP70",
    "SIRT1","SIRT3","FOXO3","NRF2","HMGB1","RAGE","TLR4","NLRP3","DNMT1",
    "HDAC","miR-21","miR-155","miR-126","miR-146a","miR-210","miR-122","BDNF",
    "MECP2","SOD2","CAT","GPX1","PCNA","KI67","CDK4","CDK6","CCND1"]

EXOSOME_TYPES = ["plant-derived exosome","plant exosome","nanoparticle",
    "extracellular vesicle","small extracellular vesicle","microvesicle",
    "exosome-like","ginger-derived","grape-derived","grapefruit","garlic",
    "mesenchymal stem cell exosome","msc-derived","tumor-derived exosome",
    "macrophage-derived","dendritic cell","platelet-derived"]

STUDY_KEYWORDS = {
    "in vitro": ["cell line","in vitro","cultured cells","HeLa","MCF-7","HepG2","A549","RAW264"],
    "animal": ["mice","mouse","rat","in vivo","animal model","xenograft","C57BL"],
    "clinical": ["patient","clinical trial","randomized","cohort","human subjects"],
    "review": ["review","meta-analysis","systematic review","overview"]
}

DISEASE_KEYWORDS = {
    "cancer": ["cancer","tumor","carcinoma","malignant","metastasis","oncology","apoptosis","proliferation"],
    "cardiovascular": ["cardiac","heart","myocardial","ischemia","atherosclerosis","stroke","vascular"],
    "neural": ["neural","neuron","brain","alzheimer","parkinson","neuroprotect","cognitive"],
    "inflammation": ["inflammation","inflammatory","arthritis","colitis","cytokine","macrophage","immune"],
    "liver": ["liver","hepatic","hepatitis","cirrhosis","fibrosis","NAFLD"],
    "diabetes": ["diabetes","glucose","insulin","pancreatic","glycemic"],
}

def extract_info(title, abstract):
    text = (title + " " + abstract).lower()

    herbs = [h for h in TCM_HERBS if h.lower() in text]
    genes = [g for g in GENES if re.search(r"\b" + re.escape(g) + r"\b", text, re.IGNORECASE)]
    exosomes = [e for e in EXOSOME_TYPES if e.lower() in text]

    study_type = "other"
    for stype, kws in STUDY_KEYWORDS.items():
        if any(k in text for k in kws):
            study_type = stype
            break

    disease_area = "other"
    disease_scores = {}
    for disease, kws in DISEASE_KEYWORDS.items():
        disease_scores[disease] = sum(1 for k in kws if k in text)
    if max(disease_scores.values()) > 0:
        disease_area = max(disease_scores, key=disease_scores.get)

    has_exosome = any(k in text for k in ["exosome","extracellular vesicle","nanoparticle"])
    has_tcm = any(k in text for k in ["chinese medicine","herbal","tcm","plant-derived"] + herbs[:3])
    confidence = 0.5
    if has_exosome and has_tcm: confidence = 0.85
    elif has_exosome or has_tcm: confidence = 0.6
    else: confidence = 0.3

    return {
        "tcm_herbs": list(set(herbs))[:5],
        "target_genes": list(set(genes))[:8],
        "exosome_types": list(set(exosomes))[:3],
        "key_findings": "",
        "study_type": study_type,
        "disease_area": disease_area,
        "confidence": confidence
    }

def run():
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    res = sb.table("paper_ai_analysis").select("paper_id").execute()
    existing_ids = {r["paper_id"] for r in res.data}
    print(f"Already analyzed: {len(existing_ids)}")

    all_papers = []
    for i in range(0, 3000, 1000):
        res = sb.table("research_papers").select("id,title,abstract").neq("abstract","").range(i,i+999).execute()
        if not res.data: break
        all_papers.extend(res.data)
        if len(res.data) < 1000: break

    papers = [p for p in all_papers if p["id"] not in existing_ids and len(p.get("abstract",""))>100]
    print(f"To analyze: {len(papers)}")

    success = 0
    batch = []
    for idx, paper in enumerate(papers):
        result = extract_info(paper["title"], paper["abstract"])
        batch.append({
            "paper_id": paper["id"],
            "tcm_herbs": json.dumps(result["tcm_herbs"], ensure_ascii=False),
            "target_genes": json.dumps(result["target_genes"], ensure_ascii=False),
            "exosome_types": json.dumps(result["exosome_types"], ensure_ascii=False),
            "key_findings": result["key_findings"],
            "study_type": result["study_type"],
            "disease_area": result["disease_area"],
            "confidence": result["confidence"],
        })
        if len(batch) >= 100:
            sb.table("paper_ai_analysis").insert(batch).execute()
            success += len(batch)
            print(f"  Inserted {success}/{len(papers)}...")
            batch = []

    if batch:
        sb.table("paper_ai_analysis").insert(batch).execute()
        success += len(batch)

    print(f"Done! Total analyzed: {success}")

if __name__ == "__main__":
    run()
