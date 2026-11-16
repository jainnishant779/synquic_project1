import urllib.request
import urllib.parse
import json

queries = [
    "leaking pipe",
    "electrician working",
    "technician repair",
    "modern living room interior",
    "smartphone app screen",
    "house cleaning service"
]

for q in queries:
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={urllib.parse.quote(q)}&gsrlimit=3&prop=imageinfo&iiprop=url|mime|size&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "SynquicAI/2.0 (contact@synquic.ai)"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
            pages = data.get("query", {}).get("pages", {})
            urls = []
            for pid, pinfo in pages.items():
                for info in pinfo.get("imageinfo", []):
                    u = info.get("url", "")
                    if any(u.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                        urls.append(u)
            print(f"{q} -> Found {len(urls)} files. Sample: {urls[0] if urls else 'None'}")
    except Exception as e:
        print(f"{q} -> Error: {e}")
