from pathlib import Path

main_path = Path("web_ec2/main.py")
content = main_path.read_text(encoding="utf-8")

# 1. Add PIL helper function for generating branded cards if no reference image was uploaded
pil_helper = '''
def create_dynamic_brand_still(brand_name: str, headline: str, subtitle: str, shot_num: int, out_path: Path):
    from PIL import Image, ImageDraw, ImageFont
    width, height = 1080, 1920
    font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    im = Image.new("RGB", (width, height), (10, 15, 29))
    draw = ImageDraw.Draw(im)

    accents = [(16, 185, 129), (59, 130, 246), (245, 158, 11), (168, 85, 247)]
    accent = accents[(shot_num - 1) % len(accents)]

    for y in range(height):
        r = int(10 + (y / height) * 20)
        g = int(15 + (y / height) * 25)
        b = int(28 + (y / height) * 42)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    cx, cy = width // 2, height // 2 - 80
    card_w, card_h = 800, 1080
    x0, y0 = cx - card_w // 2, cy - card_h // 2
    x1, y1 = cx + card_w // 2, cy + card_h // 2

    draw.rounded_rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], radius=44, fill=(30, 41, 59), outline=accent, width=3)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=40, fill=(15, 23, 42))
    draw.rounded_rectangle([cx - 90, y0 + 16, cx + 90, y0 + 44], radius=14, fill=(2, 6, 23))

    try:
        f_title = ImageFont.truetype(font_bold, 64)
        f_badge = ImageFont.truetype(font_bold, 24)
        f_body = ImageFont.truetype(font_bold, 36)
        f_sub = ImageFont.truetype(font_reg, 28)
    except Exception:
        f_title = f_badge = f_body = f_sub = ImageFont.load_default()

    draw.ellipse([cx - 55, y0 + 100, cx + 55, y0 + 210], fill=accent)
    draw.text((cx, y0 + 155), brand_name[:1].upper() or "A", fill=(255, 255, 255), font=f_title, anchor="mm")

    draw.text((cx, y0 + 265), brand_name.upper(), fill=(255, 255, 255), font=f_title, anchor="mm")
    
    badge_label = f"VERIFIED OFFICIAL • SHOT {shot_num}"
    draw.rounded_rectangle([cx - 220, y0 + 315, cx + 220, y0 + 365], radius=16, fill=(30, 58, 138), outline=accent, width=2)
    draw.text((cx, y0 + 340), badge_label, fill=accent, font=f_badge, anchor="mm")

    draw.rounded_rectangle([x0 + 40, y0 + 415, x1 - 40, y0 + 640], radius=24, fill=(30, 41, 59))
    draw.text((cx, y0 + 490), (headline[:38] or "PREMIUM SMART SERVICE").upper(), fill=(241, 245, 249), font=f_body, anchor="mm")
    draw.text((cx, y0 + 565), "On-Demand • Instant Confirmation • 24/7", fill=(148, 163, 184), font=f_sub, anchor="mm")

    draw.rounded_rectangle([x0 + 40, y0 + 720, x1 - 40, y0 + 820], radius=20, fill=accent)
    draw.text((cx, y0 + 770), "GET STARTED TODAY", fill=(15, 23, 42), font=f_body, anchor="mm")

    sub_display = subtitle[:55] if len(subtitle) > 55 else subtitle
    draw.text((cx, y0 + 910), sub_display, fill=(226, 232, 240), font=f_sub, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(out_path, "PNG")
    return out_path
'''

if "def create_dynamic_brand_still" not in content:
    content = pil_helper + "\n" + content

# 2. Update max_tokens and timeout in Nemotron call
content = content.replace("max_tokens=2048,\n            temperature=0.2,\n            timeout=35.0", "max_tokens=4096,\n            temperature=0.1,\n            timeout=60.0")

# 3. Accept any shots count from LLM
old_norm = '''    # Storyboard Normalization & Dynamic Fallback Guarantee
    if storyboard_data and "shots" in storyboard_data and len(storyboard_data["shots"]) >= shots_count:
        shots = normalize_storyboard_shots(storyboard_data["shots"][:shots_count], brand_display, product_entity)
        title = storyboard_data.get("title") or computed_title
        if brand_display.lower() not in title.lower():
            title = f"{brand_display} - {title}"
    else:
        # Fallback dynamically injects the user's custom brand & product into every shot!
        shots = build_custom_storyboard(profile["default_shots"], category, brand_candidate, product_entity, req.duration_s)
        title = computed_title'''

new_norm = '''    # Storyboard Normalization & Dynamic Fallback Guarantee
    if storyboard_data and "shots" in storyboard_data and len(storyboard_data["shots"]) >= 1:
        shots = normalize_storyboard_shots(storyboard_data["shots"], brand_display, product_entity)
        title = storyboard_data.get("title") or computed_title
        if brand_display.lower() not in title.lower():
            title = f"{brand_display} - {title}"
    else:
        # Intelligent fallback matching the user's specific prompt
        shots = build_custom_storyboard(profile["default_shots"], category, brand_candidate, product_entity, req.duration_s)
        title = computed_title

    # Compute exact shot duration to guarantee final video length matches req.duration_s
    shot_duration = max(2, req.duration_s // len(shots))'''

assert old_norm in content, "old_norm not found!"
content = content.replace(old_norm, new_norm)

# 4. Update visual selection when no reference photo was uploaded:
old_vis_select = '''            fallback_image = keyframe_path if keyframe_path.is_file() else reference_path
            if fallback_image is None or not fallback_image.is_file():
                cat_stills = profile.get("stills", [])
                still_idx = (idx - 1) % len(cat_stills) if cat_stills else 0
                still_cand = MEDIA_DIR / "stills" / cat_stills[still_idx] if cat_stills else None
                if still_cand and still_cand.is_file():
                    fallback_image = still_cand
                elif reference_path and reference_path.is_file():
                    fallback_image = reference_path
                else:
                    any_stills = list((MEDIA_DIR / "stills").glob("*.jpg")) + list((MEDIA_DIR / "references").glob("*.png"))
                    fallback_image = any_stills[0] if any_stills else None'''

new_vis_select = '''            fallback_image = keyframe_path if keyframe_path.is_file() else reference_path
            if fallback_image is None or not fallback_image.is_file():
                # Dynamically synthesize a custom brand card still for this user's specific product!
                dyn_still = project_dir / f"dyn_still_{idx}.png"
                shot_headline = (shot.get("on_screen_text") or shot.get("type") or brand_display).strip()
                shot_sub = (shot.get("narration") or prompt_text).strip()
                try:
                    create_dynamic_brand_still(brand_display, shot_headline, shot_sub, idx, dyn_still)
                    fallback_image = dyn_still
                except Exception as ex_pil:
                    print("[PIL Dynamic Still Warning]:", ex_pil)
                    cat_stills = profile.get("stills", [])
                    still_idx = (idx - 1) % len(cat_stills) if cat_stills else 0
                    fallback_image = MEDIA_DIR / "stills" / cat_stills[still_idx] if cat_stills else None'''

assert old_vis_select in content, "old_vis_select not found!"
content = content.replace(old_vis_select, new_vis_select)

main_path.write_text(content, encoding="utf-8")
print("Successfully patched web_ec2/main.py with dynamic script and PIL brand stills!")
