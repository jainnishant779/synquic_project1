from pathlib import Path

p = Path("d:/research_synquic/web_ec2/main.py")
txt = p.read_text(encoding="utf-8")

old_str = '"aspect_ratio": req.aspect_ratio,\n        "audio_voice": voice_actor,'
new_str = '"aspect_ratio": req.aspect_ratio,\n        "image_model": getattr(req, "image_model", "flux2_klein_4b"),\n        "audio_voice": voice_actor,'

if old_str in txt:
    txt = txt.replace(old_str, new_str, 1)
    p.write_text(txt, encoding="utf-8")
    print("Added image_model to return block (LF)")
else:
    old_crlf = old_str.replace("\n", "\r\n")
    new_crlf = new_str.replace("\n", "\r\n")
    if old_crlf in txt:
        txt = txt.replace(old_crlf, new_crlf, 1)
        p.write_text(txt, encoding="utf-8")
        print("Added image_model to return block (CRLF)")
    else:
        print("Could not match old_str")
