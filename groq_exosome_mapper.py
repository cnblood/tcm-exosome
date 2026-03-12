import os
import sys
import io
import json
import time
from supabase import create_client
from groq import Groq

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    url = os.environ.get("SUPABASE_URL")
    key = "sb_publishable_egJtK5qOnELNDhE64x01Ow_qzQskrmR"
    g_key = os.environ.get("GROQ_API_KEY")

    supabase = create_client(url, key)
    groq = Groq(api_key=g_key)

    print("--- 🔍 Level 3: Exosome Research Mapping ---")

    # 拉取已完成拉丁名对齐的数据
    res = supabase.table("tcm_single_herb").select("id, chinese_name, latin_name").eq("data_level", "enriched").limit(50).execute()
    herbs = res.data

    if not herbs:
        print("No enriched herbs found. Please run Level 2 script first.")
        return

    for herb in herbs:
        cname = herb['chinese_name']
        lname = herb['latin_name']
        
        # 构造深度扫描 Prompt
        prompt = f"""
        Analyze the research status of plant-derived nanovesicles (exosomes) for '{lname}' ({cname}).
        Provide details in JSON format:
        {{
            "has_exosome_study": boolean,
            "main_function": "summary of therapeutic potential (e.g., neuroprotection, anti-tumor) or 'N/A'",
            "brain_crossing": "potential to cross blood-brain barrier (High/Medium/Low/Unknown)"
        }}
        """

        try:
            completion = groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            
            evidence = json.loads(completion.choices[0].message.content)
            
            # 更新数据库
            supabase.table("tcm_single_herb").update({
                "exosome_evidence": evidence.get("has_exosome_study", False),
                "research_focus": f"Function: {evidence.get('main_function')}; BBB: {evidence.get('brain_crossing')}",
                "data_level": "validated" # 晋升至验证层
            }).eq("id", herb['id']).execute()

            status = "✅ Found" if evidence.get("has_exosome_study") else "⏳ Sparse"
            print(f"[{status}] {cname} ({lname}): {evidence.get('brain_crossing')} BBB potential")
            
            time.sleep(0.5)

        except Exception as e:
            print(f"Error scanning {cname}: {e}")

    print("\n✅ Level 3 Batch Scan Finished!")

if __name__ == "__main__":
    main()

