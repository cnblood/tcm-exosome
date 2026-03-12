import requests
import os

# 配置信息（从你之前的脚本自动继承环境或手动填入）
SUPABASE_URL = os.environ.get("SUPABASE_URL")
# 注意：这里直接使用了你终端记录中出现的 Key
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"  # 关键：这行开启 Upsert 功能
}

QUERIES = ["Exosome Traditional Chinese Medicine", "Herbal Exosome"]
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

all_trials = {}

print("🌐 正在从 ClinicalTrials.gov 抓取数据并准备同步（Upsert 模式）...")

for q in QUERIES:
    try:
        r = requests.get(BASE_URL, params={"query.term": q, "pageSize": 20, "format": "json"})
        studies = r.json().get("studies", [])
        for s in studies:
            proto = s.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            nct_id = id_mod.get("nctId", "")
            if not nct_id: continue

            status_mod = proto.get("statusModule", {})
            design_mod = proto.get("designModule", {})
            cond_mod = proto.get("conditionsModule", {})
            interv_mod = proto.get("armsInterventionsModule", {})
            sponsor_mod = proto.get("sponsorCollaboratorsModule", {})

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
    # URL 尾部添加 on_conflict=nct_id 明确告诉 Supabase 用哪个字段判断重复
    upsert_url = f"{SUPABASE_URL}/rest/v1/clinical_trials?on_conflict=nct_id"
    res = requests.post(upsert_url, headers=HEADERS, json=data_to_push)

    if res.status_code in [200, 201, 204]:
        print(f"✅ 同步成功！处理了 {len(data_to_push)} 条数据（新增或覆盖更新）。")
    else:
        print(f"❌ 依然报错: HTTP {res.status_code} - {res.text}")
else:
    print("⚠️ 未获取到新数据。")


