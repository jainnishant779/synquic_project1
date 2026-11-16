with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    c = f.read()

old = """        if actual_fallback_used:
            actual_source = "static_image_kenburns"
            actual_provider = "ffmpeg_kenburns_fallback"
            actual_model = f"FLUX.2 Klein + Ken Burns Fallback ({_ms})" """

old = old.strip()

new = """        if actual_fallback_used:
            actual_source = "reference_image_anchor" if ref_image_path else "static_image_kenburns"
            actual_provider = "reference_anchor_motion" if ref_image_path else "ffmpeg_kenburns_fallback"
            actual_model = f"Product Reference Anchor + Ken Burns ({_ms})" if ref_image_path else f"FLUX.2 Klein + Ken Burns Fallback ({_ms})" """

new = new.strip()

c_norm = c.replace("\r\n", "\n")
assert old in c_norm, "old string not found"
c_norm = c_norm.replace(old, new, 1)

with open("web_ec2/main.py", "w", encoding="utf-8") as f:
    f.write(c_norm)

print("Updated scene audit tracking successfully!")
