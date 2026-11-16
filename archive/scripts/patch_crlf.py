with open("web_ec2/main.py", "rb") as f:
    text = f.read().decode("utf-8")

old_ensure = """def ensure_bounded_keyframe(path: Path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.width > 1200 or im.height > 2100:
                im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
            im.save(path, "JPEG", quality=88)
    except Exception as ex:
        print(f"[Keyframe Bounding Warning]: {ex}")""".replace("\n", "\r\n")

new_ensure = """def ensure_bounded_keyframe(path: Path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            if im.width > 1200 or im.height > 2100:
                im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
            im.save(path, "JPEG", quality=88)
    except Exception as ex:
        print(f"[Keyframe Bounding Warning]: {ex}")""".replace("\n", "\r\n")

if old_ensure in text:
    text = text.replace(old_ensure, new_ensure)
    print("Successfully replaced ensure_bounded_keyframe!")
else:
    print("ensure_bounded_keyframe not found")

old_wiki = """def fetch_wikimedia_image(query: str, min_dim: int = 400) -> str | None:
    try:
        url = (
            "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrsearch={urllib.parse.quote(query)}&gsrlimit=3"
            "&prop=imageinfo&iiprop=url|mime|size&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for _, page in pages.items():
                infos = page.get("imageinfo", [])
                if infos:
                    u = infos[0]["url"]
                    mime = infos[0].get("mime", "")
                    w = infos[0].get("width", 0)
                    h = infos[0].get("height", 0)
                    if ("image/jpeg" in mime or "image/png" in mime) and w >= min_dim and h >= min_dim:
                        return u
    except Exception as e:
        print(f"[Wikimedia Search Warning for '{query}']: {e}")
    return None""".replace("\n", "\r\n")

new_wiki = """def fetch_wikimedia_image(query: str, min_dim: int = 400) -> str | None:
    try:
        clean_q = re.sub(r"[^a-zA-Z0-9\s]", " ", query).strip()
        words = [w for w in clean_q.split() if len(w) > 2]
        search_term = words[0] if words else query
        url = (
            "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(search_term)}"
            "&gsrlimit=5&prop=imageinfo&iiprop=url|mime|size&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "SynquicAI/2.0 (contact@synquic.ai)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for _, page in pages.items():
                infos = page.get("imageinfo", [])
                if infos:
                    u = infos[0].get("url", "")
                    clean_path = urllib.parse.urlparse(u).path.lower()
                    if clean_path.endswith((".jpg", ".jpeg", ".png", ".webp")):
                        return u
    except Exception as e:
        print(f"[Wikimedia Search Warning for '{query}']: {e}")
    return None""".replace("\n", "\r\n")

if old_wiki in text:
    text = text.replace(old_wiki, new_wiki)
    print("Successfully replaced fetch_wikimedia_image!")
else:
    print("fetch_wikimedia_image not found")

with open("web_ec2/main.py", "wb") as f:
    f.write(text.encode("utf-8"))
print("Done writing web_ec2/main.py")
