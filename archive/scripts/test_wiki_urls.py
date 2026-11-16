import urllib.request, urllib.parse, json

for w in ["plumbing", "faucet", "electrician", "smartphone", "cleaner", "living room interior"]:
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={urllib.parse.quote(w)}&gsrlimit=3&prop=imageinfo&iiprop=url|mime&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "SynquicAI/2.0 (contact@synquic.ai)"})
    with urllib.request.urlopen(req, timeout=8) as r:
        pages = json.loads(r.read().decode()).get("query", {}).get("pages", {})
        print(f"=== {w} ===")
        for pid, p in pages.items():
            for info in p.get("imageinfo", []):
                print(" ", p.get("title"), "->", info.get("url"))
