import urllib.request
import urllib.parse
import json

def search_wikimedia(query, count=3):
    encoded = urllib.parse.quote(query)
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={encoded}&gsrlimit={count}&prop=imageinfo&iiprop=url&format=json"
    req = urllib.request.Request(url, headers={
        "User-Agent": "SynquicVideoEngine/2.0 (research; contact@synquic.ai)"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            urls = []
            for pid, pdata in pages.items():
                infos = pdata.get("imageinfo", [])
                if infos and "url" in infos[0]:
                    u = infos[0]["url"]
                    if any(u.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        urls.append(u)
            return urls
    except Exception as e:
        print("Wikimedia error:", e)
        return []

print("Testing Wikimedia search for 'instagram':")
urls = search_wikimedia("instagram smartphone social media", 3)
print(f"Found {len(urls)} photos:")
for u in urls:
    print(" -", u)
