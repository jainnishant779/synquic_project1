with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    text = f.read()

target = "    render_project_ffmpeg(ffmpeg_cmd)\n    os.chmod(out_mp4, 0o644)"

replacement = """    # Mandatory Scene Diversity Check:
    # Different scenes must have distinct actions, environments or camera compositions.
    # Merely changing the caption is not a new scene!
    used_images = [t.get("asset_file") or t.get("keyframe_url") for t in scene_traces if t.get("asset_file") or t.get("keyframe_url")]
    if len(used_images) > 1 and len(set(used_images)) < len(used_images):
        shutil.rmtree(project_dir, ignore_errors=True)
        raise GenerationValidationError(
            "Scene diversity check failed: duplicate image assets detected across scenes. Every commercial scene must have distinct visual actions and composition."
        )

    render_project_ffmpeg(ffmpeg_cmd)
    os.chmod(out_mp4, 0o644)"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open("web_ec2/main.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added scene diversity check!")
else:
    print("target not found")
