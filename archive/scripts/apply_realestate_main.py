import sys
from pathlib import Path

main_path = Path("d:/research_synquic/web_ec2/main.py")
content = main_path.read_text(encoding="utf-8")

realestate_profile = '''    "realestate": {
        "keywords": ["property", "broker", "brokerage", "real estate", "realestate", "realtor", "housing", "house", "villa", "apartment", "penthouse", "home", "flat", "landlord", "rent", "residence", "estate", "building", "luxury home"],
        "default_title": "PrimeEstate Smart Property Broker Commercial",
        "default_entity": "PrimeEstate Smart Property Broker App",
        "voice": "en-US-ChristopherNeural",
        "bgm": "bgm_luxury.mp3",
        "bgm_volume": 0.22,
        "style_mood": "High-End Architectural Real Estate, Golden Sunlit Facade & Penthouse Luxury",
        "stills": ["realestate_villa.jpg", "realestate_keys.jpg", "realestate_interior.jpg"],
        "default_shots": [
            {
                "shot_num": 1, "duration_s": 5, "type": "Hero Villa Reveal",
                "visual_prompt": "Ultra-modern luxury architectural home with sunlit glass facade and infinity reflection pool, golden hour illumination",
                "camera": "Slow macro push-in",
                "narration": "Searching for your dream property shouldn't feel like an endless gamble.",
                "on_screen_text": "DISCOVER VERIFIED HOMES",
                "dialect_wan": "Slow tracking push-in across luxury modern glass villa with reflection pool",
                "dialect_veo": "Cinematic architectural real estate commercial, modern villa, golden hour, 35mm 4k"
            },
            {
                "shot_num": 2, "duration_s": 5, "type": "Broker Key Handover",
                "visual_prompt": "Real estate broker handing shiny house keys to happy homebuyer in front of modern sunlit residence",
                "camera": "High-speed tracking shot",
                "narration": "PrimeEstate connects you with verified brokers and exclusive listings in real time.",
                "on_screen_text": "INSTANT BROKER CONNECT",
                "dialect_wan": "Macro focus pull onto house keys with modern residential background",
                "dialect_veo": "Real estate broker handover, modern keys with blurred luxury townhouse background"
            },
            {
                "shot_num": 3, "duration_s": 5, "type": "Penthouse Balcony Packshot",
                "visual_prompt": "High-rise luxury penthouse interior with floor-to-ceiling glass windows and sunset city skyline view, PrimeEstate interface",
                "camera": "Subtle dolly back and focus pull",
                "narration": "Zero hidden fees. One hundred percent verified homes. Download PrimeEstate today.",
                "on_screen_text": "FIND YOUR DREAM HOME",
                "dialect_wan": "Static packshot of luxury penthouse balcony overlooking city skyline",
                "dialect_veo": "Modern property app commercial finish, luxury penthouse interior sunset glow"
            }
        ]
    },
'''

# 1. Insert realestate profile if not already present
if '"realestate":' not in content:
    target = 'PRODUCT_PROFILES = {\n'
    if target in content:
        content = content.replace(target, target + realestate_profile, 1)
        print("Inserted realestate profile into PRODUCT_PROFILES")
    else:
        print("Could not find PRODUCT_PROFILES target")
        sys.exit(1)
else:
    print("realestate profile already present in PRODUCT_PROFILES")

# 2. Update fallback category matching
old_fallback = '''    # If no explicit keyword matched, select closest aesthetic or dynamic brand
    if not matched_category:
        if any(w in p_lower for w in ["instagram", "reel", "social", "media", "creator", "influencer", "tiktok", "story"]):
            matched_category = "instagram"
        elif any(w in p_lower for w in ["luxury", "gold", "diamond", "jewelry"]):
            matched_category = "watch"
        elif any(w in p_lower for w in ["fast", "racing", "speed", "motor"]):
            matched_category = "car"
        elif any(w in p_lower for w in ["delicious", "eat", "meal", "fresh"]):
            matched_category = "burger"
        else:
            matched_category = "coke" if any(w in p_lower for w in ["can", "glass", "refresh", "ice", "bottle"]) else "instagram"'''

new_fallback = '''    # If no explicit keyword matched, select closest aesthetic or dynamic brand
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
            matched_category = "realestate" if any(w in p_lower for w in ["app", "broker", "property", "service"]) else "coke"'''

if old_fallback in content:
    content = content.replace(old_fallback, new_fallback, 1)
    print("Updated fallback category matching")
else:
    print("Could not find old_fallback block")

main_path.write_text(content, encoding="utf-8")
print("Saved updated main.py successfully!")
