def normalize_storyboard_shots(raw_shots, brand_name, product_entity):
    normalized = []
    for idx, s in enumerate(raw_shots, 1):
        num = s.get("shot_num") or s.get("shot_number") or idx
        dur = s.get("duration_s") or s.get("duration_seconds") or 5
        vis = s.get("visual_prompt") or s.get("description") or s.get("visual_direction") or f"Cinematic shot of {product_entity}"
        cam = s.get("camera") or s.get("camera_movement") or "Cinematic slow push-in"
        nar = s.get("narration") or s.get("audio_direction") or s.get("audio") or ""
        ost = s.get("on_screen_text") or s.get("tagline") or s.get("title") or ""
        
        # If audio_direction is musical instruction, synthesize a spoken commercial voiceover
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

sample_shots = [
    {
      "shot_number": 1,
      "description": "Macro close-up of the Vishal Perfume bottle being uncorked. Golden light refracts through the crystal glass, and a fine mist of fragrance spirals upward, catching the light.",
      "visual_direction": "Soft focus, warm directional lighting, slow-motion spray capture.",
      "audio_direction": "Gentle piano arpeggio with airy synth pads, subtle breath-like sounds.",
      "duration_seconds": 4,
      "camera_movement": "Static with slow gentle zoom-in to bottle neck"
    },
    {
      "shot_number": 2,
      "description": "A confident individual in modern attire walks through a sunlit urban corridor. They lightly apply the perfume to their wrist, and a delicate, golden-hued scent aura visualizes around them, fading into the city lights.",
      "visual_direction": "Natural daylight balanced with cool urban shadows, dynamic tracking shot, warm color grading.",
      "audio_direction": "Smooth bass line enters, light percussion, faint texture of rustling fabric and distant city hum.",
      "duration_seconds": 6,
      "camera_movement": "Tracking alongside subject, 35mm lens feel, slight dolly push-in"
    },
    {
      "shot_number": 3,
      "description": "Extreme close-up on the perfumed wrist. A soft glow emanates from the skin. The camera pulls back to reveal the Vishal Perfume logo centered, with the tagline \"Unveil Your Essence\" appearing in elegant serif type.",
      "visual_direction": "Minimalist high-contrast, slow fade to black, subtle lens flare.",
      "audio_direction": "Piano resolves into a sustained chord, followed by a short, memorable brand jingle.",
      "duration_seconds": 5,
      "camera_movement": "Slow pull-back, settle into static frame"
    }
]

res = normalize_storyboard_shots(sample_shots, "Vishal", "Vishal Luxury Perfume")
for r in res:
    print(r)
