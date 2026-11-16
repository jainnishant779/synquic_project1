import re
import copy

def build_custom_storyboard(default_shots, category, brand_candidate, product_entity, duration_s=15):
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

perfume_default_shots = [
    {
        "shot_num": 1, "duration_s": 5, "type": "Hero Flacon Reveal",
        "visual_prompt": "Sculpted crystal flacon of luxury perfume illuminated by golden amber sunlight",
        "camera": "Slow macro push-in",
        "narration": "An unforgettable presence in every whispered drop.",
        "on_screen_text": "MAISON ÉLIXIR",
    },
    {
        "shot_num": 2, "duration_s": 5, "type": "Atomizer Mist Spray",
        "visual_prompt": "Slow-motion 120fps spray from gold atomizer nozzle, fine fragrant mist suspended",
        "camera": "High-speed macro tracking",
        "narration": "Rare floral absolutes and deep warm sandalwood.",
        "on_screen_text": "GOLDEN AMBER ACCORD",
    },
    {
        "shot_num": 3, "duration_s": 5, "type": "Luxury Packshot",
        "visual_prompt": "Center-framed luxury perfume bottle on marble pedestal with soft golden bokeh background",
        "camera": "Subtle dolly back and focus pull",
        "narration": "Maison Élixir. Wear your aura.",
        "on_screen_text": "MAISON ÉLIXIR",
    }
]

res = build_custom_storyboard(perfume_default_shots, "perfume", "Vishal", "Vishal Luxury Perfume")
for s in res:
    print(f"Shot {s['shot_num']}: OST='{s['on_screen_text']}' | Narration='{s['narration']}'")
