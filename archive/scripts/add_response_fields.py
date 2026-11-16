from pathlib import Path

p = Path("d:/research_synquic/web_ec2/main.py")
txt = p.read_text(encoding="utf-8")

old_return_block = """    return {
        "status": "SUCCESS",
        "project_id": proj_id,
        "title": title,
        "category": category,
        "product_entity": product_entity,
        "duration_s": req.duration_s,
        "style": req.style,
        "video_url": f"/static/media/projects/{proj_id}/final.mp4","""

new_return_block = """    return {
        "status": "SUCCESS",
        "project_id": proj_id,
        "title": title,
        "category": category,
        "product_entity": product_entity,
        "duration_s": req.duration_s,
        "style": req.style,
        "aspect_ratio": req.aspect_ratio,
        "audio_voice": voice_actor,
        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),
        "video_url": f"/static/media/projects/{proj_id}/final.mp4","""

if old_return_block in txt:
    txt = txt.replace(old_return_block, new_return_block, 1)
    p.write_text(txt, encoding="utf-8")
    print("Updated return block with aspect_ratio, audio_voice, motion_style!")
else:
    old_crlf = old_return_block.replace("\n", "\r\n")
    new_crlf = new_return_block.replace("\n", "\r\n")
    if old_crlf in txt:
        txt = txt.replace(old_crlf, new_crlf, 1)
        p.write_text(txt, encoding="utf-8")
        print("Updated return block (CRLF) successfully!")
    else:
        print("Could not find old_return_block in main.py")
