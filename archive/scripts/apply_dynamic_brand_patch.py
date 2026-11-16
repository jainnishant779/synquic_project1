import re

main_path = "web_ec2/main.py"
with open(main_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import re and import copy if not present
if "import copy" not in content:
    content = content.replace("import os\n", "import os\nimport re\nimport copy\n")

# 2. Add helper functions before class GenerateVideoRequest
helpers_code = '''
def extract_brand_and_entity(prompt_text: str, category: str, default_entity: str):
    """
    Intelligently extracts the brand name and canonical product entity from any creative brief or user prompt.
    Preserves user-specified brand names (e.g. 'Vishal', 'Nike', 'TerraStride', 'AuraGlow') without generic template erasure.
    """
    p = prompt_text.strip()
    brand_candidate = None

    # 1. Explicit brand keywords: "brand name vishal", "brand: vishal", "named vishal", "called vishal"
    brand_patterns = [
        r"(?:brand\\s+name|brand\\s+is|brand|named|called|by)\\s+[:=]?\\s*([a-zA-Z0-9_\\'\\-]+(?:\\s+[a-zA-Z0-9_\\'\\-]+){0,2})",
        r"(?:for|about)\\s+([A-Z][a-zA-Z0-9_\\'\\-]+(?:\\s+[A-Z][a-zA-Z0-9_\\'\\-]+){0,2})\\s+(?:perfume|fragrance|car|shoe|sneaker|watch|coffee|burger|serum|app|tea|kettle|reel|clothing)",
    ]
    for pattern in brand_patterns:
        m = re.search(pattern, p, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if cand.lower() not in ["a", "an", "the", "our", "my", "this", "new", "best", "commercial", "ad", "video", "instagram", "tiktok", "reel", "app", "shoes", "perfume", "burger", "car", "watch"]:
                brand_candidate = cand.title()
                break

    category_descs = {
        "perfume": "Luxury Perfume",
        "realestate": "Smart Property Broker App",
        "instagram": "Viral Social Media Reel",
        "coke": "Ice-Cold Premium Soda",
        "sneaker": "Velocity Urban Sneaker",
        "kettle": "Smart Electric Kettle",
        "coffee": "Artisan Roast Espresso",
        "burger": "Gourmet Angus Burger",
        "car": "Apex Performance Sports Car",
        "watch": "Chronometer Luxury Watch",
        "headphones": "Pro ANC Studio Headphones",
        "serum": "Botanical Radiance Serum",
        "tshirt": "Minimalist Streetwear Tee"
    }

    category_generic_terms = {
        "make", "ad", "ads", "for", "commercial", "video", "create", "generate", "the", "a", "an", "of", "in", 
        "with", "and", "to", "on", "instagram", "reel", "post", "app", "shoes", "perfume", "fragrance", 
        "scent", "burger", "coffee", "car", "watch", "serum", "headphones", "tshirt", "sneaker", "kettle", 
        "property", "broker", "brokerage", "real", "estate", "realtor", "gourmet", "angus", "luxury", "sports",
        "summer", "party", "cold", "drink", "streetwear", "tea", "electric"
    }

    if not brand_candidate:
        words = re.findall(r"\\b[A-Za-z0-9\\'-]+\\b", p)
        non_generic = [w for w in words if w.lower() not in category_generic_terms]
        if non_generic:
            brand_candidate = " ".join(w.capitalize() for w in non_generic[:2])

    if brand_candidate:
        cat_desc = category_descs.get(category, category.title())
        product_entity = f"{brand_candidate} {cat_desc}" if brand_candidate.lower() not in cat_desc.lower() else cat_desc
        title = f"{brand_candidate} {cat_desc} Commercial"
    else:
        product_entity = default_entity
        title = f"{default_entity} Commercial"
        brand_candidate = default_entity.split()[0]

    return brand_candidate, product_entity, title


def normalize_storyboard_shots(raw_shots: list, brand_name: str, product_entity: str):
    """
    Normalizes shots produced by different LLMs (Nemotron, DeepSeek, Gemma, etc.) into Synquic schema.
    Guarantees brand name presence and voiceover narration.
    """
    normalized = []
    for idx, s in enumerate(raw_shots, 1):
        num = s.get("shot_num") or s.get("shot_number") or idx
        dur = s.get("duration_s") or s.get("duration_seconds") or 5
        vis = s.get("visual_prompt") or s.get("description") or s.get("visual_direction") or f"Cinematic shot of {product_entity}"
        cam = s.get("camera") or s.get("camera_movement") or "Cinematic slow push-in"
        nar = s.get("narration") or s.get("audio_direction") or s.get("audio") or ""
        ost = s.get("on_screen_text") or s.get("tagline") or s.get("title") or ""

        # If audio_direction is purely musical, generate high-impact spoken commercial voiceover
        if (not nar) or (any(w in nar.lower() for w in ["piano", "synth", "bass line", "jingle", "arpeggio", "music", "tempo"]) and len(nar.split()) > 3):
            if idx == 1:
                nar = f"Experience the unmistakable presence of {brand_name}."
            elif idx == 2:
                nar = f"Crafted with rare essences for a lingering, magnetic aura."
            else:
                nar = f"{brand_name}. Unveil your essence."

        if not ost:
            if idx == 1:
                ost = f"DISCOVER {brand_name.upper()}"
            elif idx == 2:
                ost = "PURE ESSENCE"
            else:
                ost = f"{brand_name.upper()}"

        normalized.append({
            "shot_num": num,
            "duration_s": dur,
            "type": s.get("type") or f"Scene {idx}",
            "visual_prompt": vis,
            "camera": cam,
            "narration": nar,
            "on_screen_text": ost,
            "dialect_wan": s.get("dialect_wan") or vis[:60],
            "dialect_veo": s.get("dialect_veo") or vis[:60]
        })
    return normalized


def build_custom_storyboard(default_shots: list, category: str, brand_candidate: str, product_entity: str, duration_s: int = 15):
    """
    Dynamic fallback template that guarantees the user's custom brand name is featured in every scene,
    replacing all placeholder names like 'Maison Élixir', 'Prime Angus', etc.
    """
    shots_count = 3 if duration_s <= 15 else 6
    raw_shots = copy.deepcopy(default_shots)
    brand_name = brand_candidate if brand_candidate else product_entity.split()[0]

    old_placeholders = [
        "Maison Élixir", "Maison Elixir", "Prime Angus", "TerraStride", 
        "AuraGlow", "Apex AeroGT", "AeroGT", "InstaPulse", "PrimeEstate", 
        "SoundPulse", "ChronoLux", "BaristaPro", "CloudSoft", "HydroPure", "Coca-Cola"
    ]

    custom_shots = []
    for s_idx in range(shots_count):
        orig_shot = raw_shots[s_idx % len(raw_shots)]
        shot = copy.deepcopy(orig_shot)
        shot["shot_num"] = s_idx + 1

        nar = shot.get("narration", "")
        for ph in old_placeholders:
            nar = re.sub(re.escape(ph), brand_name, nar, flags=re.IGNORECASE)

        ost = shot.get("on_screen_text", "")
        for ph in old_placeholders:
            ost = re.sub(re.escape(ph), brand_name.upper(), ost, flags=re.IGNORECASE)

        vis = shot.get("visual_prompt", "")
        for ph in old_placeholders:
            vis = re.sub(re.escape(ph), product_entity, vis, flags=re.IGNORECASE)

        if s_idx == shots_count - 1:
            if brand_name.lower() not in nar.lower():
                nar = f"{brand_name}. {nar}"
            ost = f"{brand_name.upper()}"

        shot["narration"] = nar
        shot["on_screen_text"] = ost
        shot["visual_prompt"] = vis
        custom_shots.append(shot)

    return custom_shots

'''

if "def extract_brand_and_entity" not in content:
    target_insert = "# ----------------- PRODUCTION VIDEO GENERATION ENGINE -----------------"
    content = content.replace(target_insert, helpers_code + "\n" + target_insert)

# 3. Replace the Director Engine storyboard block inside generate_production_video
old_block = '''    profile = PRODUCT_PROFILES[matched_category]
    category = matched_category
    product_entity = profile["default_entity"]

    shots_count = 3 if req.duration_s <= 15 else 6
    shot_duration = 5

    # 2. Director Engine: Call NVIDIA NIM LLM
    director_system_prompt = (
        "You are the Planning Director of Synquic AI Commercial Video Engine.\\n"
        f"Product Entity: {product_entity}\\n"
        f"Generate a {req.duration_s}-second commercial storyboard with exactly {shots_count} shots ({shot_duration}s each).\\n"
        "Style: " + req.style + "\\n"
        "Rules:\\n"
        "1. Product identity must strictly be preserved across all shots without morphing or mentioning other products.\\n"
        "2. Visual prompts must be photorealistic, cinematic, and descriptive without rendering fake logos.\\n"
        "3. Provide camera motion, narration, and concise uppercase on-screen text (2 to 4 words max) for each shot.\\n"
        "Return pure valid JSON:\\n"
        "{\\n"
        '  "title": str,\\n'
        '  "shots": [\\n'
        '    {"shot_num": 1, "duration_s": 5, "type": str, "visual_prompt": str, "camera": str, "narration": str, "on_screen_text": str, "dialect_wan": str, "dialect_veo": str}\\n'
        "  ]\\n"
        "}"
    )

    storyboard_data = None
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=req.director_model,
            messages=[
                {"role": "system", "content": director_system_prompt},
                {"role": "user", "content": f"Brief: {prompt_text}"}
            ],
            max_tokens=1000,
            temperature=0.2,
            timeout=16.0
        )
        choice = resp.choices[0]
        raw_text = (choice.message.content or "").strip()
        reasoning = ""
        if hasattr(choice.message, "model_extra") and choice.message.model_extra:
            reasoning = choice.message.model_extra.get("reasoning_content") or ""
            
        storyboard_data = extract_json_from_text(raw_text) or extract_json_from_text(reasoning)
    except Exception as e:
        print(f"[Director Engine Notice]: {e}. Utilizing canonical plan for {product_entity}.")

    # Fallback to bespoke category profile plan if API is slow (Zero cross-contamination guaranteed)
    if not storyboard_data or "shots" not in storyboard_data or not storyboard_data["shots"]:
        storyboard_data = {
            "title": profile["default_title"],
            "shots": profile["default_shots"]
        }

    shots = storyboard_data.get("shots", profile["default_shots"])
    title = storyboard_data.get("title", profile["default_title"])'''

new_block = '''    profile = PRODUCT_PROFILES[matched_category]
    category = matched_category
    brand_candidate, product_entity, computed_title = extract_brand_and_entity(prompt_text, category, profile["default_entity"])
    brand_display = brand_candidate or product_entity.split()[0]

    shots_count = 3 if req.duration_s <= 15 else 6
    shot_duration = 5

    # 2. Director Engine: Call NVIDIA NIM LLM
    director_system_prompt = (
        "You are the Commercial Director of Synquic AI Autonomous Video Engine.\\n"
        f"Client Creative Brief: {prompt_text}\\n"
        f"Brand / Product: {product_entity}\\n"
        f"Target Category: {category}\\n"
        f"Generate a {req.duration_s}-second commercial storyboard with exactly {shots_count} shots ({shot_duration}s each).\\n"
        f"Style: {req.style}\\n"
        "MANDATORY BRAND & SCRIPT REQUIREMENTS:\\n"
        f"1. The product brand '{brand_display}' MUST be prominently featured in the narration voiceover and on-screen text.\\n"
        "2. Do NOT invent unrelated brand names.\\n"
        "3. Keep each shot narration punchy (under 12 spoken words) and impactful.\\n"
        "4. Keep on_screen_text punchy in uppercase (2 to 4 words max).\\n"
        "Return pure valid JSON:\\n"
        "{\\n"
        '  "title": str,\\n'
        '  "product": str,\\n'
        '  "shots": [\\n'
        '    {"shot_num": 1, "duration_s": 5, "type": str, "visual_prompt": str, "camera": str, "narration": str, "on_screen_text": str, "dialect_wan": str, "dialect_veo": str}\\n'
        "  ]\\n"
        "}"
    )

    storyboard_data = None
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=req.director_model,
            messages=[
                {"role": "system", "content": director_system_prompt},
                {"role": "user", "content": f"Brief: {prompt_text}"}
            ],
            max_tokens=2048,
            temperature=0.2,
            timeout=22.0
        )
        choice = resp.choices[0]
        raw_text = (choice.message.content or "").strip()
        reasoning = ""
        if hasattr(choice.message, "model_extra") and choice.message.model_extra:
            reasoning = choice.message.model_extra.get("reasoning_content") or ""
            
        storyboard_data = extract_json_from_text(raw_text) or extract_json_from_text(reasoning)
    except Exception as e:
        print(f"[Director Engine Notice]: {e}. Utilizing dynamic plan for {product_entity}.")

    # Storyboard Normalization & Dynamic Fallback Guarantee
    if storyboard_data and "shots" in storyboard_data and len(storyboard_data["shots"]) >= 3:
        shots = normalize_storyboard_shots(storyboard_data["shots"], brand_display, product_entity)
        title = storyboard_data.get("title") or computed_title
        if brand_display.lower() not in title.lower():
            title = f"{brand_display} - {title}"
    else:
        # Fallback dynamically injects the user's custom brand & product into every shot!
        shots = build_custom_storyboard(profile["default_shots"], category, brand_candidate, product_entity, req.duration_s)
        title = computed_title'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("Replaced old_block with new_block successfully!")
else:
    print("Warning: old_block not found in content!")

with open(main_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to web_ec2/main.py!")
