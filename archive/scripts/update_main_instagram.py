# Script to add instagram profile and dynamic 9:16 vertical reel support to web_ec2/main.py
with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add instagram profile to PRODUCT_PROFILES
insta_profile = '''    "instagram": {
        "keywords": ["instagram", "reel", "social", "creator", "influencer", "tiktok", "story", "viral", "post", "insta"],
        "default_title": "InstaPulse AI Reel Creator Studio Commercial",
        "default_entity": "InstaPulse AI Reel Creator Studio",
        "voice": "en-US-ChristopherNeural",
        "bgm": "bgm_energetic.mp3",
        "bgm_volume": 0.24,
        "style_mood": "High-Energy Social Media Reel, Neon UI & Creator Aesthetic",
        "stills": ["insta_hero.jpg", "insta_creator.jpg", "insta_lifestyle.jpg"],
        "default_shots": [
            {
                "shot_num": 1, "duration_s": 5, "type": "Viral Hook Reveal",
                "visual_prompt": "Smartphone screen glowing in neon studio, displaying viral Instagram Reel interface with surging likes and follower counters",
                "camera": "Dynamic macro push-in",
                "narration": "Stop scrolling. Turn your ideas into viral reels in seconds.",
                "on_screen_text": "STOP SCROLLING",
                "dialect_wan": "Fast push-in on smartphone displaying viral Instagram feed",
                "dialect_veo": "Neon studio lighting, creator filming reel on smartphone with ring light"
            },
            {
                "shot_num": 2, "duration_s": 5, "type": "Creator In Action",
                "visual_prompt": "Young aesthetic content creator filming dynamic viral reel in front of ring light with smooth camera gimbal moves",
                "camera": "High-speed tracking dolly",
                "narration": "AI-powered pacing, trending audio, and automatic cinematic cuts.",
                "on_screen_text": "AI VIRAL CUTS",
                "dialect_wan": "Smooth gimbal orbit around creator gesturing to camera with glowing neon backdrop",
                "dialect_veo": "High-speed 60fps tracking shot of video creator in studio"
            },
            {
                "shot_num": 3, "duration_s": 5, "type": "CTA Packshot",
                "visual_prompt": "Sleek smartphone floating in neon purple space with InstaPulse app interface glowing, vibrant follower notification bursts",
                "camera": "Subtle dolly back and focus pull",
                "narration": "InstaPulse. Create content that converts. Start free today.",
                "on_screen_text": "CREATE YOUR NEXT REEL",
                "dialect_wan": "Static hero frame with pulsing neon notifications",
                "dialect_veo": "Social media app commercial finish, floating phone with trending notification sparkles"
            }
        ]
    },
'''

if '"instagram":' not in code:
    code = code.replace('PRODUCT_PROFILES = {\n', 'PRODUCT_PROFILES = {\n' + insta_profile)
    print("Added instagram profile to PRODUCT_PROFILES")

# 2. Update category resolution fallback to prefer instagram
old_fallback = '''    # If no explicit keyword matched, select closest aesthetic or dynamic brand
    if not matched_category:
        if any(w in p_lower for w in ["luxury", "gold", "diamond", "jewelry"]):
            matched_category = "watch"
        elif any(w in p_lower for w in ["fast", "racing", "speed", "motor"]):
            matched_category = "car"
        elif any(w in p_lower for w in ["delicious", "eat", "meal", "fresh"]):
            matched_category = "burger"
        else:
            matched_category = "coke" if any(w in p_lower for w in ["can", "glass", "refresh", "ice", "bottle"]) else "serum"'''

new_fallback = '''    # If no explicit keyword matched, select closest aesthetic or dynamic brand
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

if old_fallback in code:
    code = code.replace(old_fallback, new_fallback)
    print("Updated fallback category logic")

# 3. Update aspect ratio logic to handle 9:16 vertical reels
old_res_code = '''            # Motion Pan/Zoom Filter
            if idx == 1:
                filt_motion = "zoompan=z='min(zoom+0.0014,1.22)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
            elif idx == 2:
                filt_motion = "zoompan=z='min(zoom+0.001,1.15)':d=120:x='(iw-iw/zoom)*(1-on/120)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
            else:
                filt_motion = "zoompan=z='if(lte(zoom,1.0),1.18,max(1.001,zoom-0.0014))':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"

            # On-screen typography overlay
            ost = s.get("on_screen_text", "").replace("'", "").replace(":", "-").replace('"', '').strip()
            if not ost and idx <= len(profile["default_shots"]):
                ost = profile["default_shots"][idx - 1].get("on_screen_text", "")

            if ost:
                filt = f"{filt_motion},drawtext=text='{ost}'{font_arg}:fontcolor=white:fontsize=22:box=1:boxcolor=black@0.65:boxborderw=8:x=(w-text_w)/2:y=h-55"
            else:
                filt = filt_motion'''

new_res_code = '''            is_vertical = (req.aspect_ratio == "9:16") or any(k in p_lower for k in ["reel", "instagram", "tiktok", "shorts", "vertical", "story"])
            out_w, out_h = (448, 768) if is_vertical else (768, 448)
            y_text = "h-110" if is_vertical else "h-55"
            font_size = "24" if is_vertical else "22"

            # Motion Pan/Zoom Filter (dynamic for 9:16 vertical or 16:9 landscape)
            if idx == 1:
                filt_motion = f"zoompan=z='min(zoom+0.0014,1.22)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24"
            elif idx == 2:
                filt_motion = f"zoompan=z='min(zoom+0.001,1.15)':d=120:x='(iw-iw/zoom)*(1-on/120)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24"
            else:
                filt_motion = f"zoompan=z='if(lte(zoom,1.0),1.18,max(1.001,zoom-0.0014))':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24"

            # On-screen typography overlay
            ost = s.get("on_screen_text", "").replace("'", "").replace(":", "-").replace('"', '').strip()
            if not ost and idx <= len(profile["default_shots"]):
                ost = profile["default_shots"][idx - 1].get("on_screen_text", "")

            if ost:
                filt = f"{filt_motion},drawtext=text='{ost}'{font_arg}:fontcolor=white:fontsize={font_size}:box=1:boxcolor=black@0.65:boxborderw=8:x=(w-text_w)/2:y={y_text}"
            else:
                filt = filt_motion'''

if old_res_code in code:
    code = code.replace(old_res_code, new_res_code)
    print("Updated aspect ratio and rendering code for 9:16 vertical")

# 4. Include detected aspect ratio in response
code = code.replace('"aspect_ratio": req.aspect_ratio,', '"aspect_ratio": "9:16" if is_vertical else req.aspect_ratio,')

with open("web_ec2/main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Saved updated web_ec2/main.py!")
