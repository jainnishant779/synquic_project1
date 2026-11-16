import urllib.request
import urllib.parse
import json

def fetch_image_urls(query, count=3):
    encoded = urllib.parse.quote(query)
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={encoded}&gsrlimit={count*2}&prop=imageinfo&iiprop=url|mime&format=json"
    req = urllib.request.Request(url, headers={
        "User-Agent": "SynquicVideoEngine/2.0 (research; contact@synquic.ai)"
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            urls = []
            for pid, pdata in pages.items():
                infos = pdata.get("imageinfo", [])
                if infos and "url" in infos[0]:
                    u = infos[0]["url"]
                    mime = infos[0].get("mime", "")
                    if "image" in mime and any(u.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                        urls.append(u)
                        if len(urls) >= count:
                            break
            return urls
    except Exception as e:
        print("Fetch error:", e)
        return []

if __name__ == "__main__":
    queries = ["modern luxury house villa", "property real estate agent keys", "luxury penthouse apartment"]
    for q in queries:
        res = fetch_image_urls(q, 1)
        print(f"Query: {q} -> {res}")
