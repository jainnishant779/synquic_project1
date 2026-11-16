with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    text = f.read()

target = "    use_nvidia_video = use_fal_ai\n\n    project_dir.mkdir(parents=True, exist_ok=True)"

replacement = """    use_nvidia_video = use_fal_ai

    if req.generation_mode == "full_ai" and not req.allow_fallback and not use_nvidia_video:
        raise GenerationValidationError(
            "Full AI mode cannot accept static-image footage. Genuine video diffusion model (e.g. Wan 2.1 / Cosmos) required."
        )

    project_dir.mkdir(parents=True, exist_ok=True)"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open("web_ec2/main.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added full_ai assertion!")
else:
    print("target not found")
