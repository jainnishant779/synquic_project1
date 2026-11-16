import urllib.request
import urllib.parse
import json

# Test 1: Lexica
try:
    url = "https://lexica.art/api/v1/search?q=home+service+plumbing+repair"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
        images = data.get("images", [])
        print("Lexica count:", len(images))
        if images:
            print("Lexica sample:", images[0].get("src"))
except Exception as e:
    print("Lexica error:", e)

# Test 2: Unsplash Source / direct search
try:
    url = "https://unsplash.com/napi/search/photos?query=plumber&per_page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
        results = data.get("results", [])
        print("Unsplash count:", len(results))
        if results:
            print("Unsplash sample:", results[0].get("urls", {}).get("regular"))
except Exception as e:
    print("Unsplash error:", e)

# Test 3: Pexels API without key / public
try:
    url = "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch=plumber&gsrlimit=5&prop=imageinfo&iiprop=url|mime&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "SynquicAI/2.0 (contact@synquic.ai)"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
        pages = data.get("query", {}).get("pages", {})
        print("Wikimedia pages count:", len(pages))
        for pid, pinfo in pages.items():
            for info in pinfo.get("imageinfo", []):
                print("Wikimedia file:", info.get("url"))
except Exception as e:
    print("Wikimedia error:", e)
