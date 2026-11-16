import urllib.request, urllib.parse, json

url = "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch=plumber&gsrlimit=3&prop=imageinfo&iiprop=url|mime&format=json"
req = urllib.request.Request(url, headers={"User-Agent": "SynquicAI/2.0 (contact@synquic.ai)"})
with urllib.request.urlopen(req, timeout=8) as r:
    data = json.loads(r.read().decode())
    pages = data.get("query", {}).get("pages", {})
    for pid, p in pages.items():
        print(pid, p.get("title"), p.get("imageinfo"))
