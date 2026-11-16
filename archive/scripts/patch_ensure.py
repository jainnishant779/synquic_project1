with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    text = f.read()

target = """def ensure_bounded_keyframe(path: Path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.width > 1200 or im.height > 2100:
                im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
                im.save(path, "JPEG", quality=88)
    except Exception as ex:
        print(f"[Keyframe Bounding Warning]: {ex}")"""

replacement = """def ensure_bounded_keyframe(path: Path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            if im.width > 1200 or im.height > 2100:
                im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
            im.save(path, "JPEG", quality=88)
    except Exception as ex:
        print(f"[Keyframe Bounding Warning]: {ex}")"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open("web_ec2/main.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Successfully patched ensure_bounded_keyframe!")
else:
    print("target not found")
