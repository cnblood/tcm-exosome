import requests
import time
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

QUERIES = [
    "exosome traditional chinese medicine",
    "exosome herbal",
    "exosome acupuncture",
    "plant exosome therapy",
    "extracellular vesicle TCM",
    "exosome cancer herb",
]

def get_supabase_client():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            pass
    return None

def fetch_trials(query, page_size=20):
    params = {
        "query.term": query,
        "pageSize": page_size,
        "format": "json",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,Condition,InterventionName,LeadSponsorName,StartDate,PrimaryCompletionDate,EnrollmentCount"
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=20)
        data = r.json()
        return data.get("studies", [])
    except Exception as e:
        print(f"  Error: {e}")
        return []

def parse_studies(studies):
    parsed = []
    for s in studies:
        proto = s.get("protocolSection", {})
        id_mod = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        design_mod = proto.get("designModule", {})
        cond_mod = proto.get("conditionsModule", {})
        interv_mod = proto.get("armsInterventionsModule", {})
        sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
        nct_id = id_mod.get("nctId", "")
        if not nct_id:
            continue
        interventions = interv_mod.get("interventions", [])
        interv_names = ", ".join([i.get("name","") for i in interventions[:3]])
        parsed.append({
            "nct_id": nct_id,
            "title": id_mod.get("briefTitle",""),
            "status": status_mod.get("overallStatus",""),
            "phase": ", ".join(design_mod.get("phases",[])),
            "condition": ", ".join(cond_mod.get("conditions",[])),
            "intervention": interv_names,
            "sponsor": sponsor_mod.get("leadSponsor",{}).get("name",""),
            "start_date": status_mod.get("startDateStruct",{}).get("date",""),
            "completion_date": status_mod.get("primaryCompletionDateStruct",{}).get("date",""),
            "url": f"https://clinicaltrials.gov/study/{nct_id}"
        })
    return parsed

def save_trials_supabase(client, studies):
    parsed = parse_studies(studies)
    if not parsed:
        return 0
    added = 0
    try:
        for i in range(0, len(parsed), 50):
            client.table("clinical_trials").upsert(parsed[i:i+50], on_conflict="nct_id").execute()
            added += len(parsed[i:i+50])
        client.table("crawler_logs").insert({
            "source": "ClinicalTrials", "status": "success",
            "records_found": len(studies), "records_added": added
        }).execute()
    except Exception as e:
        print(f"  Supabase error: {e}")
    return added

def save_trials_sqlite(studies):
    try:
        from src.database.init_db import get_connection
        conn = get_connection()
        c = conn.cursor()
        parsed = parse_studies(studies)
        added = 0
        for p in parsed:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO clinical_trials
                    (nct_id,title,status,phase,condition,intervention,sponsor,start_date,completion_date,url)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (p["nct_id"],p["title"],p["status"],p["phase"],p["condition"],
                      p["intervention"],p["sponsor"],p["start_date"],p["completion_date"],p["url"]))
                if c.rowcount > 0:
                    added += 1
            except Exception as e:
                print(f"  DB: {e}")
        conn.commit()
        conn.close()
        return added
    except Exception as e:
        print(f"  SQLite error: {e}")
        return 0

def save_trials(studies):
    client = get_supabase_client()
    if client:
        return save_trials_supabase(client, studies)
    return save_trials_sqlite(studies)

def run():
    print("🔍 Starting ClinicalTrials crawler...")
    total = 0
    for q in QUERIES:
        print(f"  Query: {q}")
        studies = fetch_trials(q)
        print(f"    Found {len(studies)}")
        added = save_trials(studies)
        total += added
        print(f"    Added {added}")
        time.sleep(1)
    print(f"✅ ClinicalTrials done. Total new: {total}")
    return total

if __name__ == "__main__":
    run()
