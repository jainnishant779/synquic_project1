import urllib.request
import urllib.parse
import json
import re

def search_ddg_images(query):
    # Step 1: get vqd token
    url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode("utf-8", errors="ignore")
    vqd_match = re.search(r'vqd=([0-9-]+)', html)
    if not vqd_match:
        return []
    vqd = vqd_match.group(1)
    
    # Step 2: query i.js
    img_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,&p=1"
    req2 = urllib.request.Request(img_url, headers=headers)
    with urllib.request.urlopen(req2, timeout=10) as r2:
        data = json.loads(r2.read().decode("utf-8"))
        return [res.get("image") for res in data.get("results", []) if res.get("image")]

for q in ["leaking faucet under kitchen sink commercial", "friendly plumber technician in uniform repair"]:
    try:
        results = search_ddg_images(q)
        print(f"DDG '{q}' -> found {len(results)} images. Sample: {results[0] if results else None}")
    except Exception as e:
        print(f"DDG '{q}' error: {e}")
