from pathlib import Path

main_path = Path("web_ec2/main.py")
content = main_path.read_text(encoding="utf-8")

old_func = '''def fetch_dynamic_scene_visual(shot: dict, product_entity: str, category: str, brand_display: str, out_path: Path) -> Path:'''

new_func = '''def ensure_bounded_keyframe(path: Path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.width > 1200 or im.height > 2100:
                im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
                im.save(path, "JPEG", quality=88)
    except Exception as ex:
        print(f"[Keyframe Bounding Warning]: {ex}")

def fetch_dynamic_scene_visual(shot: dict, product_entity: str, category: str, brand_display: str, out_path: Path) -> Path:'''

content = content.replace(old_func, new_func)

# Call ensure_bounded_keyframe before returning out_path
content = content.replace(
    'if out_path.stat().st_size > 5000:\n                    return out_path',
    'if out_path.stat().st_size > 5000:\n                    ensure_bounded_keyframe(out_path)\n                    return out_path'
)

content = content.replace(
    'shutil.copyfile(still_p, out_path)\n            return out_path',
    'shutil.copyfile(still_p, out_path)\n            ensure_bounded_keyframe(out_path)\n            return out_path'
)

main_path.write_text(content, encoding="utf-8")
print("Added ensure_bounded_keyframe to web_ec2/main.py successfully.")
