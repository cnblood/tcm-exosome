#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# src/crawler/fill_key_findings.py
# 姣忔杩愯濉厖50绡?key_findings锛岄泦鎴愯繘daemon寰幆

import os
import time
import requests
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

H = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json"
}

GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              "gemini-flash-latest:generateContent?key=")


def fetch_empty_papers(limit=60):
    all_empty = []
    for offset in range(0, 5000, 1000):
        r = requests.get(
            SUPABASE_URL + "/rest/v1/research_papers",
            params={
                "select": "id,title,abstract",
                "key_findings": "is.null",
                "offset": offset,
                "limit": 1000
            },
            headers=H, timeout=20
        )
        batch = r.json()
        if not isinstance(batch, list) or not batch:
            break
        for d in batch:
            if d.get("abstract") and len(d["abstract"]) > 50:
                all_empty.append(d)
        if len(all_empty) >= limit:
            break
        if len(batch) < 1000:
            break
    return all_empty[:limit]


def extract_findings(title, abstract):
    if not GEMINI_API_KEY:
        return None
    prompt = ("鐢?-3鍙ヤ腑鏂囨€荤粨杩欑瘒璁烘枃鐨勫叧閿彂鐜帮紝閲嶇偣鍖呮嫭锛氫富瑕佸彂鐜般€佷綔鐢ㄦ満鍒躲€佷复搴婃剰涔夈€俓n"
              "Title: " + title + "\nAbstract: " + abstract[:1500] + "\n"
              "鍙緭鍑轰腑鏂囨€荤粨锛屼笉瑕佹爣绛惧拰markdown銆?)
    for attempt in range(3):
        try:
            r = requests.post(
                GEMINI_URL + GEMINI_API_KEY,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300}
                },
                timeout=25
            )
            d = r.json()
            if r.status_code == 429:
                wait = 30 * (attempt + 1)
                logger.info("Gemini 429, waiting %ds", wait)
                time.sleep(wait)
                continue
            if "candidates" in d:
                return d["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.warning("Gemini error: %s", e)
            time.sleep(10)
    return None


def update_findings(paper_id, findings):
    for attempt in range(3):
        try:
            r = requests.patch(
                SUPABASE_URL + "/rest/v1/research_papers",
                params={"id": "eq." + str(paper_id)},
                headers={**H, "Prefer": "return=minimal"},
                json={"key_findings": findings},
                timeout=15
            )
            return r.status_code in (200, 204)
        except Exception as e:
            logger.warning("Update error: %s", e)
            time.sleep(10)
    return False


def run(batch_size=50):
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set, skipping key_findings fill")
        return 0

    logger.info("Fetching papers without key_findings...")
    papers = fetch_empty_papers(limit=batch_size + 10)
    logger.info("Found %d papers to fill", len(papers))

    success = 0
    for i, paper in enumerate(papers[:batch_size], 1):
        kf = extract_findings(paper.get("title", ""), paper["abstract"])
        if kf and len(kf) > 10:
            ok = update_findings(paper["id"], kf)
            if ok:
                success += 1
                logger.info("[%d/%d] Filled ID %s: %s...", i, batch_size, paper["id"], kf[:50])
        time.sleep(5)

    logger.info("key_findings fill done: %d/%d", success, batch_size)
    return success


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    run(n)
