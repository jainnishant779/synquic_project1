import urllib.request, urllib.parse, re, json

def search_ddg_images(query, count=3):
    init_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(init_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
        m = re.search(r'vqd=([\d-]+)', content) or re.search(r'vqd="([^"]+)"', content)
        if not m:
            return []
        vqd = m.group(1)
        api_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,&p=1"
        req2 = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            data = json.loads(resp2.read().decode("utf-8"))
        results = [r["image"] for r in data.get("results", []) if "image" in r and r["image"].startswith("http")]
        return results[:count]
    except Exception as e:
        print("DDG error:", e)
        return []

for q in ["tesla cyber truck neon city", "luxury diamond ring jewelry", "gaming laptop rgb backlit"]:
    res = search_ddg_images(q, 2)
    print(f"Query: {q} -> Found {len(res)}:")
    for r in res:
        print("   ", r[:90] + "...")
