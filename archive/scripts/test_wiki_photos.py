import urllib.request
import urllib.parse
import json

def search_wiki_photos(term):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={urllib.parse.quote(term + ' incategory:Photographs')}&gsrlimit=5&prop=imageinfo&iiprop=url|mime|size&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "SynquicAI/2.0 (contact@synquic.ai)"})
    with urllib.request.urlopen(req, timeout=8) as r:
        pages = json.loads(r.read().decode()).get("query", {}).get("pages", {})
        res = []
        for pid, p in pages.items():
            for info in p.get("imageinfo", []):
                u = info.get("url", "")
                if ".jpg" in u.lower() or ".jpeg" in u.lower():
                    res.append((p.get("title"), u))
        return res

for term in ["plumbing", "faucet", "electrician", "living room", "smartphone", "cleaner"]:
    photos = search_wiki_photos(term)
    print(f"'{term}' -> {len(photos)} photos")
    for title, u in photos[:2]:
        print(f"   {title}: {u[:90]}...")
