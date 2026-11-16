import urllib.request, urllib.parse, json

single_words = ["plumbing", "electrician", "faucet", "interior", "smartphone", "cleaner"]
for w in single_words:
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={w}&gsrlimit=3&prop=imageinfo&iiprop=url|mime&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "SynquicAI/2.0 (contact@synquic.ai)"})
    with urllib.request.urlopen(req, timeout=8) as r:
        pages = json.loads(r.read().decode()).get("query", {}).get("pages", {})
        print(w, "->", len(pages))
