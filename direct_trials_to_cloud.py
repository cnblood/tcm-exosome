import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-duplicates"
}

QUERIES = [
    "exosome traditional chinese medicine",
    "exosome herbal",
    "exosome acupuncture",
    "plant exosome therapy",
    "extracellular vesicle TCM",
    "exosome cancer herb",
]

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
all_trials = {}

print("🌐 正在直接从 ClinicalTrials.gov 获取最新数据...")

for q in QUERIES:
    try:
        r = requests.get(BASE_URL, params={"query.term": q, "pageSize": 20, "format": "json"})
        studies = r.json().get("studies", [])
        for s in studies:
            proto = s.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design_mod = proto.get("designModule", {})
            cond_mod = proto.get("conditionsModule", {})
            interv_mod = proto.get("armsInterventionsModule", {})
            sponsor_mod = proto.get("sponsorCollaboratorsModule", {})

            nct_id = id_mod.get("nctId", "")
            if not nct_id: continue

            interventions = interv_mod.get("interventions", [])
            interv_names = ", ".join([i.get("name","") for i in interventions[:3]])

            all_trials[nct_id] = {
                "nct_id": nct_id,
                "title": id_mod.get("briefTitle", ""),
                "status": status_mod.get("overallStatus", ""),
                "phase": ", ".join(design_mod.get("phases", [])),
                "condition": ", ".join(cond_mod.get("conditions", [])),
                "intervention": interv_names,
                "sponsor": sponsor_mod.get("leadSponsor", {}).get("name", ""),
                "start_date": status_mod.get("startDateStruct", {}).get("date", ""),
                "url": f"https://clinicaltrials.gov/study/{nct_id}"
            }
    except Exception as e:
        print(f"抓取 {q} 时出错: {e}")

data_to_push = list(all_trials.values())

if data_to_push:
    print(f"🚀 获取到 {len(data_to_push)} 条独立试验，正在直连 Supabase 云端...")
    res = requests.post(f"{SUPABASE_URL}/rest/v1/clinical_trials", headers=HEADERS, json=data_to_push)
    
    if res.status_code in [200, 201, 204]:
        print("✅ 完美击杀！数据已全部成功送达云端！")
        print("👉 现在去刷新你的大屏网页吧！那个 0 马上就会变了！")
    else:
        print(f"❌ 上传失败: HTTP {res.status_code} - {res.text}")
else:
    print("⚠️ 没抓到任何数据。")


