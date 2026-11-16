with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update Category Resolution in main.py
old_cat_block = """    # 1. Product Identity & Category Resolution (Dynamic Multi-Category Matching)
    p_lower = prompt_text.lower()
    matched_category = None
    for cat_name, p_data in PRODUCT_PROFILES.items():
        if any(k in p_lower for k in p_data["keywords"]):
            matched_category = cat_name
            break

    # If no explicit keyword matched, select closest aesthetic or dynamic brand
    if not matched_category:
        if any(w in p_lower for w in ["property", "broker", "brokerage", "estate", "realtor", "home", "house", "villa", "apartment", "penthouse", "flat", "land", "rent", "realty"]):
            matched_category = "realestate"
        elif any(w in p_lower for w in ["instagram", "reel", "social", "media", "creator", "influencer", "tiktok", "story", "viral"]):
            matched_category = "instagram"
        elif any(w in p_lower for w in ["luxury", "gold", "diamond", "jewelry", "watch", "time"]):
            matched_category = "watch"
        elif any(w in p_lower for w in ["fast", "racing", "speed", "motor", "car", "drive", "vehicle"]):
            matched_category = "car"
        elif any(w in p_lower for w in ["delicious", "eat", "meal", "fresh", "food", "burger"]):
            matched_category = "burger"
        elif any(w in p_lower for w in ["coffee", "cafe", "espresso", "latte", "roast", "brew"]):
            matched_category = "coffee"
        elif any(w in p_lower for w in ["perfume", "fragrance", "scent", "cologne"]):
            matched_category = "perfume"
        elif any(w in p_lower for w in ["headphone", "audio", "sound", "earphone", "music"]):
            matched_category = "headphones"
        elif any(w in p_lower for w in ["skin", "beauty", "cosmetic", "serum", "glow"]):
            matched_category = "serum"
        elif any(w in p_lower for w in ["fashion", "clothing", "wear", "shirt", "tshirt", "hoodie"]):
            matched_category = "tshirt"
        elif any(w in p_lower for w in ["shoe", "sneaker", "footwear", "runner"]):
            matched_category = "sneaker"
        elif any(w in p_lower for w in ["tea", "kettle", "kitchen", "boil"]):
            matched_category = "kettle"
        else:
            matched_category = "realestate" if any(w in p_lower for w in ["app", "broker", "property", "service"]) else "coke"

    profile = PRODUCT_PROFILES[matched_category]
    category = matched_category
    brand_candidate, product_entity, computed_title = extract_brand_and_entity(prompt_text, category, profile["default_entity"])
    brand_display = brand_candidate or product_entity.split()[0]"""

new_cat_block = """    # 1. Product Identity & Category Resolution (Dynamic Multi-Category Matching)
    p_lower = prompt_text.lower()
    matched_category = None

    # Check if user explicitly selected industry
    if getattr(req, "industry", None) and req.industry in PRODUCT_PROFILES:
        matched_category = req.industry
    else:
        for cat_name, p_data in PRODUCT_PROFILES.items():
            if any(k in p_lower for k in p_data["keywords"]):
                matched_category = cat_name
                break

    # If no explicit keyword matched, select closest category — NEVER default to Coke!
    if not matched_category:
        if any(w in p_lower for w in ["barrier", "parking", "parkfnb", "gate", "boom", "toll", "rfid", "turnstile", "security gate"]):
            matched_category = "parking_barrier"
        elif any(w in p_lower for w in ["property", "broker", "brokerage", "estate", "realtor", "home", "house", "villa", "apartment", "penthouse", "flat", "land", "rent", "realty"]):
            matched_category = "realestate"
        elif any(w in p_lower for w in ["instagram", "reel", "social", "media", "creator", "influencer", "tiktok", "story", "viral"]):
            matched_category = "instagram"
        elif any(w in p_lower for w in ["luxury", "gold", "diamond", "jewelry", "watch", "time"]):
            matched_category = "watch"
        elif any(w in p_lower for w in ["fast", "racing", "speed", "motor", "car", "drive", "vehicle"]):
            matched_category = "car"
        elif any(w in p_lower for w in ["delicious", "eat", "meal", "fresh", "food", "burger"]):
            matched_category = "burger"
        elif any(w in p_lower for w in ["coffee", "cafe", "espresso", "latte", "roast", "brew"]):
            matched_category = "coffee"
        elif any(w in p_lower for w in ["perfume", "fragrance", "scent", "cologne"]):
            matched_category = "perfume"
        elif any(w in p_lower for w in ["headphone", "audio", "sound", "earphone", "music"]):
            matched_category = "headphones"
        elif any(w in p_lower for w in ["skin", "beauty", "cosmetic", "serum", "glow"]):
            matched_category = "serum"
        elif any(w in p_lower for w in ["fashion", "clothing", "wear", "shirt", "tshirt", "hoodie"]):
            matched_category = "tshirt"
        elif any(w in p_lower for w in ["shoe", "sneaker", "footwear", "runner"]):
            matched_category = "sneaker"
        elif any(w in p_lower for w in ["tea", "kettle", "kitchen", "boil"]):
            matched_category = "kettle"
        elif any(w in p_lower for w in ["coke", "soda", "drink", "cola", "beverage", "soft drink"]):
            matched_category = "coke"
        else:
            # Smart Universal Fallback - NEVER default to Coke!
            matched_category = "parking_barrier" if any(w in p_lower for w in ["hardware", "device", "barrier", "system", "tech", "iot", "machine"]) else "realestate"

    profile = PRODUCT_PROFILES[matched_category]
    category = matched_category

    # Support explicit Brand Name from user parameter
    if getattr(req, "brand_name", None) and req.brand_name.strip():
        brand_display = req.brand_name.strip()
        product_entity = f"{brand_display} {profile['default_entity'].split()[-1]}"
        computed_title = f"{brand_display} Commercial"
    else:
        brand_candidate, product_entity, computed_title = extract_brand_and_entity(prompt_text, category, profile["default_entity"])
        brand_display = brand_candidate or product_entity.split()[0]"""

# 2. Update Director Prompt & Timeout
old_dir_block = """    # 2. Director Engine: Call NVIDIA NIM LLM
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
            timeout=12.0
        )"""

new_dir_block = """    # 2. Director Engine: Call NVIDIA NIM LLM with Advanced Production Parameters
    director_system_prompt = (
        "You are the Commercial Director of Synquic AI Autonomous Video Engine.\\n"
        f"Client Creative Brief: {prompt_text}\\n"
        f"Brand Name: {brand_display}\\n"
        f"Product Entity: {product_entity}\\n"
        f"Target Category / Industry: {category}\\n"
        f"Core Features / Value Proposition: {getattr(req, 'features', '') or 'High-speed clearance, 100% reliability, military-grade sensor'}\\n"
        f"Target Audience: {getattr(req, 'target_audience', '') or 'Commercial & Enterprise Facility Managers'}\\n"
        f"Camera Movement Dynamics: {getattr(req, 'camera_dynamics', 'Cinematic Macro Push-in')}\\n"
        f"Lighting & Mood Aesthetic: {getattr(req, 'lighting_mood', 'High-Tech Studio Clean')}\\n"
        f"Call To Action (CTA): {getattr(req, 'cta_text', '') or f'Upgrade to {brand_display} today'}\\n"
        f"Commercial Duration: {req.duration_s} seconds (exactly {shots_count} shots, {shot_duration}s each).\\n"
        f"Visual Style: {req.style}\\n"
        "MANDATORY BRAND & SCRIPT REQUIREMENTS:\\n"
        f"1. The product brand '{brand_display}' MUST be prominently featured in the narration voiceover and on-screen text.\\n"
        "2. Do NOT invent unrelated brand names or switch to different products.\\n"
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
            timeout=35.0
        )"""

# 3. Reference Image Usage in Scene Generation Loop
old_still_block = """            # Check if category has a model-specific generated still (e.g., sneaker, kettle, serum, tshirt)
            model_specific_still = STILLS_DIR / f"img__{category}__{req_img_model}__seed42.png"
            if model_specific_still.exists() and idx != 2:
                still_path = model_specific_still
            else:
                still_filename = stills_list[(idx - 1) % len(stills_list)]
                still_path = STILLS_DIR / still_filename
                if not still_path.exists():
                    still_path = STILLS_DIR / "coke_hero.jpg" """

new_still_block = """            # Check if user provided an uploaded reference image asset
            ref_image_path = None
            if req.reference_assets and len(req.reference_assets) > 0:
                ref_id = req.reference_assets[0]
                REFERENCES_DIR = MEDIA_DIR / "references"
                for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                    c = REFERENCES_DIR / f"{ref_id}{ext}"
                    if c.exists():
                        ref_image_path = c
                        break

            if ref_image_path:
                still_path = ref_image_path
                img_model_display = f"Product Reference Anchor ({ref_image_path.name})"
            else:
                # Check if category has a model-specific generated still (e.g., sneaker, kettle, serum, tshirt)
                model_specific_still = STILLS_DIR / f"img__{category}__{req_img_model}__seed42.png"
                if model_specific_still.exists() and idx != 2:
                    still_path = model_specific_still
                else:
                    still_filename = stills_list[(idx - 1) % len(stills_list)]
                    still_path = STILLS_DIR / still_filename
                    if not still_path.exists():
                        still_path = STILLS_DIR / "barrier_hero.jpg" if category == "parking_barrier" else STILLS_DIR / "coke_hero.jpg" """

# Normalize CRLF
code_norm = code.replace("\r\n", "\n")
old_cat_norm = old_cat_block.replace("\r\n", "\n")
new_cat_norm = new_cat_block.replace("\r\n", "\n")

assert old_cat_norm in code_norm, "old_cat_block not found!"
code_norm = code_norm.replace(old_cat_norm, new_cat_norm, 1)

old_dir_norm = old_dir_block.replace("\r\n", "\n")
new_dir_norm = new_dir_block.replace("\r\n", "\n")
assert old_dir_norm in code_norm, "old_dir_block not found!"
code_norm = code_norm.replace(old_dir_norm, new_dir_norm, 1)

old_still_norm = old_still_block.replace("\r\n", "\n")
new_still_norm = new_still_block.replace("\r\n", "\n")
assert old_still_norm in code_norm, "old_still_block not found!"
code_norm = code_norm.replace(old_still_norm, new_still_norm, 1)

with open("web_ec2/main.py", "w", encoding="utf-8") as f:
    f.write(code_norm)

print("Successfully updated web_ec2/main.py with advanced parameters, reference image anchoring, and anti-coke guards!")
