import os
# SUPABASE_URL set via environment variable
os.environ['SUPABASE_KEY'] = os.environ.get("SUPABASE_KEY")

import requests, time
from supabase import create_client

client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# 绮惧噯TCM涓村簥璇曢獙鏌ヨ
TCM_TRIAL_QUERIES = [
    "traditional chinese medicine cancer",
    "chinese herbal medicine randomized controlled trial",
    "TCM treatment liver disease clinical trial",
    "acupuncture randomized controlled trial",
    "curcumin clinical trial inflammation",
    "berberine clinical trial diabetes",
    "astragalus clinical trial immune",
    "ginseng clinical trial randomized",
    "herbal medicine cardiovascular clinical trial",
    "TCM formula randomized controlled",
    "chinese medicine lung disease",
    "TCM kidney disease clinical",
    "herbal extract tumor clinical trial",
    "TCM exosome biomarker clinical",
    "plant extract nanoparticle drug delivery clinical",
    "salvia miltiorrhiza clinical trial",
    "panax notoginseng clinical trial",
    "ligustrazine clinical trial stroke",
    "compound danshen clinical trial",
    "liuwei dihuang clinical trial",
]

def fetch_trials(query, max_results=100):
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": query,
        "pageSize": max_results,
        "format": "json",
        "fields": "NCTId,BriefTitle,Condition,InterventionName,Phase,OverallStatus,LeadSponsorName,StartDate,CompletionDate,BriefSummary"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        return r.json().get("studies", [])
    except Exception as e:
        print(f"  Error: {e}")
        return []

def is_tcm_related(study):
    """杩囨护锛氬彧淇濈暀鐪熸TCM/鑽夎嵂/澶栨硨浣撶浉鍏宠瘯楠?""
    proto = study.get("protocolSection", {})
    id_mod = proto.get("identificationModule", {})
    arm_mod = proto.get("armsInterventionsModule", {})
    desc_mod = proto.get("descriptionModule", {})

    title = id_mod.get("briefTitle", "").lower()
    summary = desc_mod.get("briefSummary", "").lower()
    interventions = " ".join([i.get("name","") for i in arm_mod.get("interventions",[])]).lower()

    tcm_keywords = [
        "chinese medicine", "chinese herbal", "tcm", "herbal medicine",
        "acupuncture", "moxibustion", "curcumin", "berberine", "astragalus",
        "ginseng", "salvia", "danshen", "notoginseng", "licorice", "glycyrrhiza",
        "coptis", "scutellaria", "angelica", "paeonia", "rehmannia", "poria",
        "exosome", "extracellular vesicle", "plant nanoparticle", "herb",
        "traditional medicine", "phytotherapy", "botanical", "natural product",
        "kampo", "ayurvedic", "turmeric", "ginger zingiber", "green tea",
        "quercetin", "resveratrol", "baicalin", "tanshinone", "ginsenoside",
    ]
    text = title + " " + summary + " " + interventions
    return any(kw in text for kw in tcm_keywords)

total_ins = total_skip = total_filtered = 0

for q in TCM_TRIAL_QUERIES:
    trials = fetch_trials(q, max_results=100)
    relevant = [t for t in trials if is_tcm_related(t)]
    total_filtered += (len(trials) - len(relevant))
    print(f"  [{len(relevant)}/{len(trials)}] {q}")

    for study in relevant:
        try:
            proto = study.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            cond_mod = proto.get("conditionsModule", {})
            arm_mod = proto.get("armsInterventionsModule", {})
            design_mod = proto.get("designModule", {})
            status_mod = proto.get("statusModule", {})
            sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
            desc_mod = proto.get("descriptionModule", {})

            nct_id = id_mod.get("nctId", "")
            if not nct_id: continue

            ex = client.table('clinical_trials').select('id').eq('nct_id', nct_id).execute()
            if ex.data:
                total_skip += 1
                continue

            interventions = arm_mod.get("interventions", [])
            interv_names = "; ".join([i.get("name","") for i in interventions[:5]])
            sponsor = sponsor_mod.get("leadSponsor", {}).get("name", "")
            phases = design_mod.get("phaseList", {}).get("phase", [])

            client.table('clinical_trials').insert({
                "nct_id": nct_id,
                "title": id_mod.get("briefTitle","")[:500],
                "condition": "; ".join(cond_mod.get("conditions",[])[:5])[:300],
                "intervention": interv_names[:300],
                "phase": "; ".join(phases),
                "status": status_mod.get("overallStatus",""),
                "sponsor": sponsor[:200],
                "start_date": status_mod.get("startDateStruct",{}).get("date",""),
                "completion_date": status_mod.get("completionDateStruct",{}).get("date","")[:20],
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
            }).execute()
            total_ins += 1
        except Exception as e:
            if "duplicate" in str(e).lower():
                total_skip += 1

    time.sleep(1)

# 鍒犻櫎涔嬪墠璇彃鍏ョ殑鏃犲叧璇曢獙
print("\n娓呯悊鏃犲叧璇曢獙...")
junk_ncts = ["NCT01652079", "NCT04266249"]
for nct in junk_ncts:
    try:
        client.table('clinical_trials').delete().eq('nct_id', nct).execute()
        print(f"  鍒犻櫎: {nct}")
    except: pass

r = client.table('clinical_trials').select('id', count='exact').execute()
print(f"\n瀹屾垚!")
print(f"  鏂板TCM璇曢獙: {total_ins}")
print(f"  宸插瓨鍦ㄨ烦杩? {total_skip}")
print(f"  杩囨护鏃犲叧: {total_filtered}")
print(f"  鏁版嵁搴撴€婚噺: {r.count}")


