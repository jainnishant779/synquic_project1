from pathlib import Path

p = Path("d:/research_synquic/web_ec2/main.py")
lines = p.read_text(encoding="utf-8").splitlines()

for i, line in enumerate(lines):
    if 'asset_source = "static_image_kenburns"' in line:
        lines[i] = '            asset_source = "static_image_kenburns"'
    if 'provider = "synquic_diffusion_pipeline"' in line:
        lines[i] = '            provider = "synquic_diffusion_pipeline"'
    if 'model_name = f"{img_model_display} + {_ms}"' in line:
        lines[i] = '            model_name = f"{img_model_display} + {_ms}"'

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Fixed indentation!")
