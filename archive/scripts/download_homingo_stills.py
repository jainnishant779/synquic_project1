import urllib.request
import urllib.parse
import json
import os
from PIL import Image

def get_wiki_img(query):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}&gsrlimit=5&prop=imageinfo&iiprop=url|mime&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "SynquicAI/2.0 (contact@synquic.ai)"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            pages = json.loads(r.read().decode()).get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                for info in pdata.get("imageinfo", []):
                    u = info.get("url", "")
                    clean_path = urllib.parse.urlparse(u).path.lower()
                    if clean_path.endswith((".jpg", ".jpeg", ".png", ".webp")):
                        return u
    except Exception as e:
        print(f"Error for {query}: {e}")
    return None

scenes = [
    ("plumbing pipe", "homingo_scene1_leak.jpg"),
    ("smartphone app", "homingo_scene2_app.jpg"),
    ("plumber", "homingo_scene3_expert.jpg"),
    ("luxury interior", "homingo_scene4_livingroom.jpg")
]

stills_dir = "/home/ubuntu/synquic_app/static/media/stills"

for q, fname in scenes:
    img_url = get_wiki_img(q)
    print(f"Query '{q}' -> {img_url}")
    if img_url:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        target_path = os.path.join(stills_dir, fname)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        with open(target_path, "wb") as f:
            f.write(data)
        with Image.open(target_path) as im:
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
            im.save(target_path, "JPEG", quality=88)
        print(f"Saved {fname} ({os.path.getsize(target_path)} bytes, size {im.size})")
