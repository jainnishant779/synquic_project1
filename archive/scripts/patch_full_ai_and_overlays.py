import re

# 1. Update qc_engine.py
with open("web_ec2/qc_engine.py", "r", encoding="utf-8") as f:
    qc_code = f.read()

old_dup_func = """def detect_duplicate_scenes(scene_mp4s: list) -> bool:
    \"\"\"Check if any two scenes share almost identical visual frames.\"\"\"
    thumbs = []
    for idx, p in enumerate(scene_mp4s):
        th = p.parent / f"thumb_{idx}.jpg"
        try:
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-ss", "1.0", "-i", str(p),
                "-vframes", "1", "-s", "64x114", str(th)
            ], check=True)
            if th.is_file():
                im = Image.open(th).convert("L")
                thumbs.append((th, list(im.getdata())))
        except Exception:
            pass
            
    is_duplicate = False
    for i in range(len(thumbs)):
        for j in range(i + 1, len(thumbs)):
            p1 = thumbs[i][1]
            p2 = thumbs[j][1]
            diff = sum(abs(a - b) for a, b in zip(p1, p2)) / len(p1)
            if diff < 3.0:
                is_duplicate = True
                break
        if is_duplicate:
            break
            
    for th, _ in thumbs:
        th.unlink(missing_ok=True)
        
    return is_duplicate"""

new_dup_func = """def detect_duplicate_scenes(scene_mp4s: list, scene_traces: list = None) -> bool:
    \"\"\"Check if any two scenes share identical source assets or visual frames.\"\"\"
    if scene_traces:
        asset_keys = []
        for t in scene_traces:
            k = t.get("asset_file") or t.get("keyframe_url") or t.get("source_file") or ""
            if k:
                asset_keys.append(k)
        if len(asset_keys) > 1 and len(set(asset_keys)) < len(asset_keys):
            return True

    thumbs = []
    for idx, p in enumerate(scene_mp4s):
        th = p.parent / f"thumb_{idx}.jpg"
        try:
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-ss", "1.0", "-i", str(p),
                "-vframes", "1", "-s", "64x114", str(th)
            ], check=True)
            if th.is_file():
                im = Image.open(th).convert("L")
                thumbs.append((th, list(im.getdata())))
        except Exception:
            pass
            
    is_duplicate = False
    for i in range(len(thumbs)):
        for j in range(i + 1, len(thumbs)):
            p1 = thumbs[i][1]
            p2 = thumbs[j][1]
            diff = sum(abs(a - b) for a, b in zip(p1, p2)) / len(p1)
            if diff < 6.0:
                is_duplicate = True
                break
        if is_duplicate:
            break
            
    for th, _ in thumbs:
        th.unlink(missing_ok=True)
        
    return is_duplicate"""

if old_dup_func in qc_code:
    qc_code = qc_code.replace(old_dup_func, new_dup_func, 1)
    print("Patched detect_duplicate_scenes in qc_engine.py")

old_call = "duplicate_detected = detect_duplicate_scenes(scene_files)"
new_call = "duplicate_detected = detect_duplicate_scenes(scene_files, scene_traces=scene_traces)"
if old_call in qc_code:
    qc_code = qc_code.replace(old_call, new_call, 1)
    print("Patched detect_duplicate_scenes call in qc_engine.py")

with open("web_ec2/qc_engine.py", "w", encoding="utf-8") as f:
    f.write(qc_code)


# 2. Update main.py
with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    main_code = f.read()

# Add GenerationValidationError definition if not present
if "class GenerationValidationError" not in main_code:
    main_code = main_code.replace(
        "class FalMediaError(RuntimeError):",
        "class GenerationValidationError(HTTPException):\n    def __init__(self, detail: str):\n        super().__init__(status_code=422, detail=detail)\n\nclass FalMediaError(RuntimeError):",
        1
    )
    print("Added GenerationValidationError class")

# Replace fallback_image logic in main.py
old_fallback_block = """        if scene_fallback:
            fallback_image = reference_path if (reference_path and reference_path.is_file()) else None
            if fallback_image is None or not fallback_image.is_file():
                try:
                    fetch_dynamic_scene_visual(shot, product_entity, category, brand_display, keyframe_path)
                    fallback_image = keyframe_path
                except Exception as ex_vis:
                    print(f"[Visual Engine Warning for shot {idx}]: {ex_vis}")
                    cat_stills = profile.get("stills", [])
                    still_idx = (idx - 1) % len(cat_stills) if cat_stills else 0
                    fallback_image = MEDIA_DIR / "stills" / cat_stills[still_idx] if cat_stills else None"""

new_fallback_block = """        if scene_fallback:
            fallback_image = None
            cat_stills = profile.get("stills", [])
            still_idx = (idx - 1) % len(cat_stills) if cat_stills else 0

            # 1. Action-specific scene stills take precedence to guarantee scene diversity!
            if cat_stills and still_idx < len(cat_stills):
                candidate_still = MEDIA_DIR / "stills" / cat_stills[still_idx]
                if candidate_still.is_file():
                    fallback_image = candidate_still

            # 2. If this is the final packshot and user provided a reference, allow using it for the packshot only:
            if fallback_image is None and idx == len(shots) and reference_path and reference_path.is_file():
                fallback_image = reference_path

            # 3. Dynamic visual generation/search
            if fallback_image is None or not fallback_image.is_file():
                try:
                    fetch_dynamic_scene_visual(shot, product_entity, category, brand_display, keyframe_path)
                    fallback_image = keyframe_path
                except Exception as ex_vis:
                    print(f"[Visual Engine Warning for shot {idx}]: {ex_vis}")
                    if cat_stills:
                        fallback_image = MEDIA_DIR / "stills" / cat_stills[still_idx]"""

if old_fallback_block in main_code:
    main_code = main_code.replace(old_fallback_block, new_fallback_block, 1)
    print("Patched fallback_image block in main.py")
else:
    print("Could not find old_fallback_block")

# Replace FFmpeg filter_complex overlay in main.py
old_filter_block = """            if req.aspect_ratio == "9:16":
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
                )"""

new_filter_block = """            if req.aspect_ratio == "9:16":
                is_final_packshot = (idx == len(shots))
                cta_clean = cta_display.upper().replace("'", "\\\\\\'").replace(":", "\\\\:")[:36]

                if is_final_packshot:
                    # Final Packshot: Bold centered brand + call to action button pill
                    filter_complex = (
                        f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                        f"crop={output_width}:{output_height},{motion_filt},"
                        f"eq=contrast=1.10:saturation=1.20,"
                        f"drawtext=text='{brand_head}'{font_opt}:fontsize=int(h*0.036):fontcolor=white:x=(w-text_w)/2:y=int(h*0.74):shadowcolor=black@0.9:shadowx=3:shadowy=3,"
                        f"drawtext=text='{cta_clean}'{font_opt}:fontsize=int(h*0.020):fontcolor=white:x=(w-text_w)/2:y=int(h*0.83):box=1:boxcolor=#059669@0.92:boxborderw=14:shadowcolor=black@0.8:shadowx=2:shadowy=2"
                    )
                else:
                    # Action Scenes (1, 2, 3): Subtle top brand pill + centered compact action caption pill (NOT covering product!)
                    filter_complex = (
                        f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                        f"crop={output_width}:{output_height},{motion_filt},"
                        f"eq=contrast=1.10:saturation=1.20,"
                        f"drawtext=text='{brand_head}'{font_opt}:fontsize=int(h*0.016):fontcolor=white@0.90:x=(w-text_w)/2:y=int(h*0.045):box=1:boxcolor=black@0.45:boxborderw=8,"
                        f"drawtext=text='{shot_text}'{font_opt}:fontsize=int(h*0.022):fontcolor=white:x=(w-text_w)/2:y=int(h*0.84):box=1:boxcolor=black@0.60:boxborderw=12:shadowcolor=black@0.8:shadowx=2:shadowy=2"
                    )"""

if old_filter_block in main_code:
    main_code = main_code.replace(old_filter_block, new_filter_block, 1)
    print("Patched filter_complex in main.py")
else:
    print("Could not find old_filter_block")

# Add asset_file tracking into scene_traces
old_trace_entry = """"keyframe_model": IMAGE_MODEL_ID if keyframe_path.is_file() else None,"""
new_trace_entry = """"keyframe_model": IMAGE_MODEL_ID if keyframe_path.is_file() else None,
            "asset_file": str(fallback_image.name) if fallback_image else None,"""

if old_trace_entry in main_code:
    main_code = main_code.replace(old_trace_entry, new_trace_entry, 1)
    print("Added asset_file to scene_traces in main.py")

with open("web_ec2/main.py", "w", encoding="utf-8") as f:
    f.write(main_code)

print("Patching complete.")
