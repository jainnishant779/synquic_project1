import re

with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Patch ensure_bounded_keyframe
old_ensure = """def ensure_bounded_keyframe(path: Path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.width > 1200 or im.height > 2100:
                im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
            im.save(path, "JPEG", quality=88)
    except Exception as ex:
        print(f"[Keyframe Bounding Warning]: {ex}")"""

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
        print(f"[Keyframe Bounding Warning]: {ex}")"""

if old_ensure in content:
    content = content.replace(old_ensure, new_ensure)
    print("Patched ensure_bounded_keyframe")
else:
    print("Could not find old_ensure")

# 2. Patch fetch_wikimedia_image
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
    return None"""

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
    return None"""

if old_wiki in content:
    content = content.replace(old_wiki, new_wiki)
    print("Patched fetch_wikimedia_image")
else:
    print("Could not find old_wiki")

# 3. Patch home_services profile
old_home_stills = '"stills": [],'
new_home_stills = '"stills": ["homingo_scene1_leak.jpg", "homingo_scene2_app.jpg", "homingo_scene3_expert.jpg", "homingo_scene4_livingroom.jpg"],'
if old_home_stills in content:
    content = content.replace(old_home_stills, new_home_stills, 1)
    print("Patched home_services stills")

# 4. Patch home_services shots to 4 scenes
old_home_shots = """        "default_shots": [
            {
                "shot_num": 1, "duration_s": 5, "type": "Urgent Home Emergency",
                "visual_prompt": "Frustrated homeowner facing sudden leaking pipe beneath kitchen sink, water dripping, urgent need",
                "camera": "Slow macro push-in on emergency leak",
                "narration": "Home emergencies don't wait. Neither should you.",
                "on_screen_text": "FAST 30-MIN ASSISTANCE",
                "search_terms": ["faucet leak", "plumbing leak", "pipe repair", "water leak"],
                "dialect_wan": "Water dripping from pipe beneath sink, homeowner checking phone",
                "dialect_veo": "Cinematic kitchen emergency, macro water drip on kitchen pipe, dramatic natural lighting"
            },
            {
                "shot_num": 2, "duration_s": 5, "type": "Verified Technician Arrives",
                "visual_prompt": "Friendly certified home service technician in clean uniform with toolkit smiling, modern home, crisp natural daylight",
                "camera": "Dynamic tracking shot of technician repairing with precision",
                "narration": "Verified background-checked technicians at your doorstep in thirty minutes.",
                "on_screen_text": "BACKGROUND-CHECKED EXPERTS",
                "search_terms": ["service technician", "electrician maintenance", "technician repair tools", "repairman"],
                "dialect_wan": "Service technician with toolkit inspecting equipment carefully, professional demeanor",
                "dialect_veo": "Friendly service professional fixing household installation, bright commercial lighting"
            },
            {
                "shot_num": 3, "duration_s": 5, "type": "Spotless Home & Booking Guarantee",
                "visual_prompt": "Spotless modern luxury living room, relaxed homeowner smiling with smartphone app, sunny afternoon",
                "camera": "Wide cinematic pull-back and hero finish",
                "narration": "Fixed right, guaranteed. Download Homingo today.",
                "on_screen_text": "DOWNLOAD HOMINGO APP",
                "search_terms": ["Luxury Living Room Interior Design in Kolkata", "modern luxury living room", "clean home interior"],
                "dialect_wan": "Sunlit luxury living room, spotless surfaces, relaxed homeowner with smartphone",
                "dialect_veo": "Commercial packshot of pristine modern living room, soft afternoon light, serene atmosphere"
            }
        ]"""

new_home_shots = """        "default_shots": [
            {
                "shot_num": 1,
                "duration_s": 4,
                "type": "The Problem (Urgent Repair Emergency)",
                "visual_prompt": "Frustrated homeowner facing sudden leaking plumbing pipe beneath kitchen sink, water dripping, urgent need",
                "camera": "Slow cinematic macro push-in on emergency leak",
                "narration": "Home emergencies don't wait. A leaking pipe or broken wiring needs immediate help.",
                "on_screen_text": "FAST 30-MIN ASSISTANCE",
                "search_terms": ["faucet", "plumbing", "water leak"],
                "dialect_wan": "Water dripping from pipe beneath sink, homeowner checking phone",
                "dialect_veo": "Cinematic kitchen emergency, macro water drip on kitchen pipe, dramatic natural lighting"
            },
            {
                "shot_num": 2,
                "duration_s": 4,
                "type": "Instant Mobile App Booking",
                "visual_prompt": "Modern smartphone displaying sleek Homingo home services mobile app interface, 1-tap booking confirmed",
                "camera": "Dynamic macro push-in on mobile app interface",
                "narration": "Book certified professionals in seconds directly from the Homingo app.",
                "on_screen_text": "1-TAP INSTANT BOOKING",
                "search_terms": ["smartphone", "mobile app"],
                "dialect_wan": "Smartphone displaying sleek home service booking app screen",
                "dialect_veo": "Macro product shot of smartphone booking confirmed notification"
            },
            {
                "shot_num": 3,
                "duration_s": 4,
                "type": "Verified Technician at Doorstep",
                "visual_prompt": "Friendly certified home service technician in clean uniform with toolkit repairing with precision in bright modern home",
                "camera": "Dynamic tracking shot of technician repairing with precision",
                "narration": "Verified background-checked technicians at your doorstep in thirty minutes.",
                "on_screen_text": "BACKGROUND-CHECKED EXPERTS",
                "search_terms": ["electrician", "plumber", "repairman"],
                "dialect_wan": "Service technician with toolkit inspecting equipment carefully, professional demeanor",
                "dialect_veo": "Friendly service professional fixing household installation, bright commercial lighting"
            },
            {
                "shot_num": 4,
                "duration_s": 3,
                "type": "Spotless Finish & Guarantee",
                "visual_prompt": "Spotless modern luxury living room, relaxed homeowner smiling with smartphone app, clean peaceful home",
                "camera": "Wide cinematic pull-back and hero finish",
                "narration": "Fixed right, guaranteed. Download the Homingo app today.",
                "on_screen_text": "DOWNLOAD HOMINGO APP",
                "search_terms": ["interior", "living room"],
                "dialect_wan": "Sunlit luxury living room, spotless surfaces, relaxed homeowner with smartphone",
                "dialect_veo": "Commercial packshot of pristine modern living room, soft afternoon light, serene atmosphere"
            }
        ]"""

if old_home_shots in content:
    content = content.replace(old_home_shots, new_home_shots)
    print("Patched home_services shots")

# 5. Patch Category Matching to prioritize domain intent
old_cat_match = """    # 1. Product Identity & Category Resolution (Dynamic Multi-Category Matching)
    p_lower = prompt_text.lower()
    matched_category = None

    # Check if user explicitly selected industry
    if getattr(req, "industry", None) and req.industry in PRODUCT_PROFILES:
        matched_category = req.industry
    else:
        for cat_name, p_data in PRODUCT_PROFILES.items():
            if any(k in p_lower for k in p_data["keywords"]):
                matched_category = cat_name
                break"""

new_cat_match = """    # 1. Product Identity & Category Resolution (Dynamic Multi-Category Matching)
    p_lower = prompt_text.lower()
    matched_category = None

    # Priority 1: Direct domain intent match from prompt text
    if any(w in p_lower for w in ["homingo", "home service", "plumber", "plumbing", "electrician", "handyman", "cleaning", "maid", "carpenter", "repair service", "appliance", "ac repair", "urban company", "leak", "pipe"]):
        matched_category = "home_services"
    elif any(w in p_lower for w in ["barrier", "parking", "parkfnb", "gate", "boom", "toll", "rfid", "turnstile", "security gate"]):
        matched_category = "parking_barrier"
    elif getattr(req, "industry", None) and req.industry in PRODUCT_PROFILES and req.industry not in ("", "instagram"):
        matched_category = req.industry
    else:
        for cat_name, p_data in PRODUCT_PROFILES.items():
            if any(k in p_lower for k in p_data["keywords"]):
                matched_category = cat_name
                break"""

if old_cat_match in content:
    content = content.replace(old_cat_match, new_cat_match)
    print("Patched category matching")

with open("web_ec2/main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Finished patching main.py")
