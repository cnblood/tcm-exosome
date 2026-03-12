import os
# SUPABASE_URL set via environment variable
os.environ['SUPABASE_KEY'] = os.environ.get("SUPABASE_KEY")

from src.crawler.expanded_crawler import fetch_clinical_trials
from supabase import create_client

client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# 鑾峰彇褰撳墠琛ㄩ噷鏈夊灏戞潯
r = client.table('clinical_trials').select('id', count='exact').execute()
print(f"褰撳墠涓村簥璇曢獙鎬绘暟: {r.count}")

# 鎶撲竴鎵?trials = fetch_clinical_trials('plant nanoparticles clinical', 10)
print(f"鎶撳埌: {len(trials)} 鏉?)

for study in trials[:3]:
    proto = study.get("protocolSection", {})
    id_module = proto.get("identificationModule", {})
    nct_id = id_module.get("nctId", "")
    title = id_module.get("briefTitle", "")
    print(f"\n  NCT: {nct_id}")
    print(f"  Title: {title[:60]}")

    # 妫€鏌ユ槸鍚﹀凡瀛樺湪
    ex = client.table('clinical_trials').select('id').eq('nct_id', nct_id).execute()
    print(f"  Already exists: {bool(ex.data)}")

    if not ex.data:
        # 灏濊瘯鎻掑叆
        try:
            cond_module = proto.get("conditionsModule", {})
            arm_module = proto.get("armsInterventionsModule", {})
            design_module = proto.get("designModule", {})
            status_module = proto.get("statusModule", {})
            sponsor_module = proto.get("sponsorCollaboratorsModule", {})
            interventions = arm_module.get("interventions", [])
            interv_names = "; ".join([i.get("name","") for i in interventions[:5]])
            sponsor = sponsor_module.get("leadSponsor", {}).get("name", "")
            completion = status_module.get("completionDateStruct", {}).get("date", "")

            data = {
                "nct_id": nct_id,
                "title": title[:500],
                "condition": "; ".join(cond_module.get("conditions",[])[:5])[:300],
                "intervention": interv_names[:300],
                "phase": "; ".join(design_module.get("phaseList",{}).get("phase",[])),
                "status": status_module.get("overallStatus",""),
                "sponsor": sponsor[:200],
                "start_date": status_module.get("startDateStruct",{}).get("date",""),
                "completion_date": completion[:20],
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
            }
            print(f"  Inserting: {data}")
            res = client.table('clinical_trials').insert(data).execute()
            print(f"  Success: {res.data}")
        except Exception as e:
            print(f"  ERROR: {e}")


