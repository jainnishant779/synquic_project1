import re
from pathlib import Path

main_path = Path("web_ec2/main.py")
content = main_path.read_text(encoding="utf-8")

# 1. Replace create_dynamic_brand_still
replacement_head = '''import urllib.request
import urllib.parse

def fetch_wikimedia_image(query: str, min_dim: int = 600):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit=20&prop=imageinfo&iiprop=url|size|mime"
    req = urllib.request.Request(url, headers={"User-Agent": "SynquicStudio/2.0 (contact@synquic.com)"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read().decode("utf-8"))
            pages = d.get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                infos = pdata.get("imageinfo", [])
                if infos and "url" in infos[0]:
                    u = infos[0]["url"]
                    mime = infos[0].get("mime", "")
                    w = infos[0].get("width", 0)
                    h = infos[0].get("height", 0)
                    if ("image/jpeg" in mime or "image/png" in mime) and w >= min_dim and h >= min_dim:
                        return u
    except Exception as e:
        print(f"[Wikimedia Search Warning for '{query}']: {e}")
    return None

def fetch_dynamic_scene_visual(shot: dict, product_entity: str, category: str, brand_display: str, out_path: Path) -> Path:
    candidates = []
    if shot.get("search_terms"):
        candidates.extend(shot["search_terms"])
    
    vp = shot.get("visual_prompt", "")
    if vp:
        clean_vp = re.sub(r'[^a-zA-Z0-9\s]', ' ', vp)
        words = [w for w in clean_vp.split() if len(w) > 3 and w.lower() not in {"ultra", "sleek", "modern", "cinematic", "photorealistic", "commercial", "high", "crisp", "natural", "slow", "macro", "hero"}]
        if len(words) >= 2:
            candidates.append(" ".join(words[:4]))
            candidates.append(" ".join(words[:2]))
    
    st_type = shot.get("type", "")
    if st_type:
        candidates.append(st_type)
        
    candidates.extend([product_entity, category.replace("_", " ")])
    
    for term in candidates:
        if not term:
            continue
        img_url = fetch_wikimedia_image(term)
        if img_url:
            try:
                req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    out_path.write_bytes(resp.read())
                if out_path.stat().st_size > 5000:
                    return out_path
            except Exception as ex_down:
                print(f"[Image Download Warning for '{term}']: {ex_down}")
                
    cat_stills = PRODUCT_PROFILES.get(category, {}).get("stills", [])
    if cat_stills:
        still_name = cat_stills[(shot.get("shot_num", 1) - 1) % len(cat_stills)]
        still_p = MEDIA_DIR / "stills" / still_name
        if still_p.is_file():
            shutil.copyfile(still_p, out_path)
            return out_path
            
    from PIL import Image
    im = Image.new("RGB", (1080, 1920), (15, 23, 42))
    im.save(out_path, "JPEG", quality=90)
    return out_path
'''

content = re.sub(r'def create_dynamic_brand_still\(.*?\n    return out_path\n', lambda m: replacement_head, content, flags=re.DOTALL)

# 2. Add home_services to PRODUCT_PROFILES
home_services_profile = '''    "home_services": {
        "keywords": ["homingo", "home service", "plumber", "plumbing", "electrician", "cleaning", "handyman", "maid", "carpenter", "repair service", "appliance repair", "ac repair", "urban company", "leak", "pipe", "water leak"],
        "default_title": "Homingo On-Demand Home Services Commercial",
        "default_entity": "Homingo Home Services App",
        "voice": "en-US-ChristopherNeural",
        "bgm": "bgm_energetic.mp3",
        "bgm_volume": 0.22,
        "style_mood": "Contemporary Home Service Lifestyle, Crisp Natural Daylight & Verified Experts",
        "stills": [],
        "default_shots": [
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
        ]
    },
'''

content = content.replace('PRODUCT_PROFILES = {\n', 'PRODUCT_PROFILES = {\n' + home_services_profile)

# 3. Category auto-detection: check home_services before realestate
target_detect = '''    # If no explicit keyword matched, select closest category — NEVER default to Coke!
    if not matched_category:'''

replacement_detect = '''    # If no explicit keyword matched, select closest category — NEVER default to Coke!
    if not matched_category:
        if any(w in p_lower for w in ["homingo", "home service", "plumber", "plumbing", "electrician", "handyman", "cleaning", "maid", "carpenter", "repair service", "appliance", "ac repair", "urban company", "leak", "pipe", "water leak"]):
            matched_category = "home_services"'''

content = content.replace(target_detect, replacement_detect)

# 4. Replace scene_fallback rendering
target_fallback_block = re.search(r'if scene_fallback:.*?render_project_ffmpeg\(ffmpeg_cmd\)\s+asset_source = "pro_vertical_reel_motion"\s+provider = "synquic_local_pro_reel"\s+model_name = "Pro 9:16 Vertical Reel Engine \(Multi-Layer Depth \+ Kinetic Typography\)"\s+fallback_used_any = True', content, re.DOTALL)

if target_fallback_block:
    new_fallback_block = '''if scene_fallback:
            fallback_image = reference_path if (reference_path and reference_path.is_file()) else None
            if fallback_image is None or not fallback_image.is_file():
                try:
                    fetch_dynamic_scene_visual(shot, product_entity, category, brand_display, keyframe_path)
                    fallback_image = keyframe_path
                except Exception as ex_vis:
                    print(f"[Visual Engine Warning for shot {idx}]: {ex_vis}")
                    cat_stills = profile.get("stills", [])
                    still_idx = (idx - 1) % len(cat_stills) if cat_stills else 0
                    fallback_image = MEDIA_DIR / "stills" / cat_stills[still_idx] if cat_stills else None

            if fallback_image is None or not fallback_image.is_file():
                shutil.rmtree(project_dir, ignore_errors=True)
                raise HTTPException(status_code=503, detail="Dynamic Visual Engine could not resolve a scene asset.")

            font_opt = f":fontfile='{escape_filter_path(font_path)}'" if font_path.exists() else ""
            fps = 25
            tot_frames = int(shot_duration * fps)

            # 3 Distinct Cinematic Camera Motions
            if idx % 3 == 1:
                motion_filt = f"zoompan=z='min(zoom+0.0014,1.18)':d={tot_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={output_width}x{output_height}:fps={fps}"
            elif idx % 3 == 2:
                motion_filt = f"zoompan=z=1.08:d={tot_frames}:x='(iw-iw/zoom)*(on/{tot_frames})':y='ih/2-(ih/zoom/2)':s={output_width}x{output_height}:fps={fps}"
            else:
                motion_filt = f"zoompan=z='max(1.001,1.16-0.0012*on)':d={tot_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={output_width}x{output_height}:fps={fps}"

            brand_head = brand_display.upper().replace("'", "\\\\'").replace(":", "\\\\:")
            shot_text = (shot.get("on_screen_text") or shot.get("narration") or "").strip().upper()
            if len(shot_text) > 42:
                shot_text = shot_text[:39] + "..."
            shot_text = shot_text.replace("'", "\\\\'").replace(":", "\\\\:")

            if req.aspect_ratio == "9:16":
                bar_y = int(output_height * 0.77)
                bar_h = int(output_height * 0.17)
                brand_y = int(output_height * 0.80)
                tag_y = int(output_height * 0.85)
                brand_size = int(output_height * 0.030)
                tag_size = int(output_height * 0.017)

                filter_complex = (
                    f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                    f"crop={output_width}:{output_height},{motion_filt},"
                    f"eq=contrast=1.12:saturation=1.22,"
                    f"drawbox=x=0:y={bar_y}:w={output_width}:h={bar_h}:color=black@0.60:t=fill,"
                    f"drawtext=text='{brand_head}'{font_opt}:fontsize={brand_size}:fontcolor=white:x=(w-text_w)/2:y={brand_y}:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
                    f"drawtext=text='{shot_text}'{font_opt}:fontsize={tag_size}:fontcolor=#38bdf8:x=(w-text_w)/2:y={tag_y}:shadowcolor=black@0.9:shadowx=2:shadowy=2"
                )
            else:
                filter_complex = (
                    f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                    f"crop={output_width}:{output_height},{motion_filt},"
                    f"eq=contrast=1.12:saturation=1.22,"
                    f"drawbox=x=0:y=h-160:w=w:h=160:color=black@0.60:t=fill,"
                    f"drawtext=text='{brand_head}'{font_opt}:fontsize=44:fontcolor=white:x=60:y=h-120:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
                    f"drawtext=text='{shot_text}'{font_opt}:fontsize=26:fontcolor=#38bdf8:x=60:y=h-60:shadowcolor=black@0.9:shadowx=2:shadowy=2"
                )

            ffmpeg_cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1",
                "-i", str(fallback_image), "-filter_complex", filter_complex, "-t", str(shot_duration),
                "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                "-pix_fmt", "yuv420p", str(scene_out_mp4),
            ]
            render_project_ffmpeg(ffmpeg_cmd)
            asset_source = "dynamic_photographic_motion" if not (reference_path and reference_path.is_file()) else "uploaded_reference_motion"
            provider = "synquic_dynamic_reel"
            model_name = "Cinematic 9:16 Full-Bleed Reel Engine"
            fallback_used_any = True'''
    content = content[:target_fallback_block.start()] + new_fallback_block + content[target_fallback_block.end():]
    print("Replaced fallback block successfully.")
else:
    print("Warning: target_fallback_block not found!")

# 5. Add -ar 48000 to audio commands
content = content.replace('"-c:a", "aac", "-b:a", "192k", "-ac", "2",', '"-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",')
content = content.replace('"-map", "0:v", "-map", "1:a",\n            "-c:v", "copy",', '"-af", "aresample=48000",\n            "-map", "0:v", "-map", "1:a",\n            "-c:v", "copy",')

main_path.write_text(content, encoding="utf-8")
print("Finished updating web_ec2/main.py")
