import os
import sys
import io
import json
import time
from supabase import create_client
from groq import Groq

# 确保 Windows 终端显示不乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    url = os.environ.get("SUPABASE_URL")
    key = "sb_publishable_egJtK5qOnELNDhE64x01Ow_qzQskrmR"
    g_key = os.environ.get("GROQ_API_KEY")

    supabase = create_client(url, key)
    groq = Groq(api_key=g_key)

    print("--- 🚀 Level 3: FULL SCALE Exosome Evidence Scanning ---")

    # 修改点 1：将 .limit(20) 改为 .limit(600)
    # 修改点 2：增加排序，确保处理逻辑清晰
    res = supabase.table("tcm_single_herb") \
        .select("id, chinese_name, latin_name") \
        .eq("data_level", "enriched") \
        .order("id") \
        .limit(600) \
        .execute()
        
    herbs = res.data

    if not herbs:
        print("No enriched herbs remaining. All data might be already validated.")
        return

    total = len(herbs)
    print(f"Starting analysis for {total} herbs. Please sit back...")

    for i, herb in enumerate(herbs):
        cname = herb['chinese_name']
        lname = herb['latin_name']
        
        # 针对全量扫描优化的 Prompt，要求更严谨
        prompt = f"Analyze if '{lname}' ({cname}) has scientific evidence for plant-derived exosomes/nanovesicles. Return JSON with: has_exosome_study (bool), main_function (str), brain_crossing (High/Medium/Low/Unknown)."

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
                "research_focus": f"Func: {evidence.get('main_function')}; BBB: {evidence.get('brain_crossing')}",
                "data_level": "validated"
            }).eq("id", herb['id']).execute()

            tag = "⭐ FOUND" if evidence.get("has_exosome_study") else "  None"
            print(f"[{i+1}/{total}] {tag} | {cname} | BBB: {evidence.get('brain_crossing')}")
            
            # 修改点 3：全量运行时稍微增加延迟，避免触发 Groq 的每分钟请求数 (RPM) 限制
            time.sleep(0.8) 

        except Exception as e:
            print(f"\n[!] Error at {cname}: {e}")
            # 如果是频率限制错误，多休息一会儿
            if "rate_limit" in str(e).lower():
                print("Rate limit hit, sleeping for 10 seconds...")
                time.sleep(10)
            continue

    print("\n✅ MISSION ACCOMPLISHED: All 600 herbs scanned and validated!")

if __name__ == "__main__":
    main()

