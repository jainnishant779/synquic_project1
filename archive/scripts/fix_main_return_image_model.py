from pathlib import Path

p = Path("d:/research_synquic/web_ec2/main.py")
txt = p.read_text(encoding="utf-8")

# Clean manifest_data duplicate image_model
manifest_target = """    manifest_data = {
        "project_id": proj_id,
        "title": title,
        "category": category,
        "image_model": getattr(req, "image_model", "flux2_klein_4b"),
        "product_entity": product_entity,
        "aspect_ratio": req.aspect_ratio,
        "image_model": getattr(req, "image_model", "flux2_klein_4b"),
        "audio_voice": voice_actor,
        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),
        "user_prompt": prompt_text,
        "director_model": req.director_model,
        "image_model": getattr(req, "image_model", "flux2_klein_4b"),"""

manifest_clean = """    manifest_data = {
        "project_id": proj_id,
        "title": title,
        "category": category,
        "image_model": getattr(req, "image_model", "flux2_klein_4b"),
        "product_entity": product_entity,
        "aspect_ratio": req.aspect_ratio,
        "audio_voice": voice_actor,
        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),
        "user_prompt": prompt_text,
        "director_model": req.director_model,"""

if manifest_target in txt:
    txt = txt.replace(manifest_target, manifest_clean, 1)
    print("Cleaned manifest_data duplicates")

# Add image_model to the return block
old_return = """    return {
        "status": "SUCCESS",
        "project_id": proj_id,
        "title": title,
        "category": category,
        "product_entity": product_entity,
        "duration_s": req.duration_s,
        "style": req.style,
        "aspect_ratio": req.aspect_ratio,
        "audio_voice": voice_actor,
        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),"""

new_return = """    return {
        "status": "SUCCESS",
        "project_id": proj_id,
        "title": title,
        "category": category,
        "product_entity": product_entity,
        "duration_s": req.duration_s,
        "style": req.style,
        "aspect_ratio": req.aspect_ratio,
        "image_model": getattr(req, "image_model", "flux2_klein_4b"),
        "audio_voice": voice_actor,
        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),"""

if old_return in txt:
    txt = txt.replace(old_return, new_return, 1)
    print("Added image_model to return dict!")
else:
    print("Could not find old_return in main.py")

p.write_text(txt, encoding="utf-8")
print("Saved main.py")
