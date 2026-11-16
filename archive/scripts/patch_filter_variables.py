with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    text = f.read()

target = """            if req.aspect_ratio == "9:16":
                is_final_packshot = (idx == len(shots))
                cta_clean = cta_display.upper().replace("'", "\\\\\\'").replace(":", "\\\\:")[:36]

                if is_final_packshot:
                    # Final Packshot: Bold centered brand + call to action button pill
                    filter_complex = (
                        f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                        f"crop={output_width}:{output_height},{motion_filt},"
                        f"eq=contrast=1.10:saturation=1.20,"
                        f"drawtext=text='{brand_head}'{font_opt}:fontsize=int(h*0.036):fontcolor=white:x=(w-text_w)/2:y=int(h*0.74):shadowcolor=black@0.9:shadowx=3:shadowy=3,"
                        f"drawtext=text='{cta_clean}'{font_opt}:fontsize=int(h*0.020):fontcolor=white:x=(w-text_w)/2:y=int(h*0.83):box=1:boxcolor=#059669@0.92:boxborderw=14:shadowcolor=black@0.8:shadowx=2:shadowy=2"
                    )
                else:
                    # Action Scenes (1, 2, 3): Subtle top brand pill + centered compact action caption pill (NOT covering product!)
                    filter_complex = (
                        f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                        f"crop={output_width}:{output_height},{motion_filt},"
                        f"eq=contrast=1.10:saturation=1.20,"
                        f"drawtext=text='{brand_head}'{font_opt}:fontsize=int(h*0.016):fontcolor=white@0.90:x=(w-text_w)/2:y=int(h*0.045):box=1:boxcolor=black@0.45:boxborderw=8,"
                        f"drawtext=text='{shot_text}'{font_opt}:fontsize=int(h*0.022):fontcolor=white:x=(w-text_w)/2:y=int(h*0.84):box=1:boxcolor=black@0.60:boxborderw=12:shadowcolor=black@0.8:shadowx=2:shadowy=2"
                    )"""

replacement = """            if req.aspect_ratio == "9:16":
                is_final_packshot = (idx == len(shots))
                cta_clean = cta_display.upper().replace("'", "\\\\\\'").replace(":", "\\\\:")[:36]
                pack_brand_size = int(output_height * 0.036)
                pack_brand_y = int(output_height * 0.74)
                pack_cta_size = int(output_height * 0.022)
                pack_cta_y = int(output_height * 0.83)

                action_brand_size = int(output_height * 0.016)
                action_brand_y = int(output_height * 0.045)
                action_tag_size = int(output_height * 0.022)
                action_tag_y = int(output_height * 0.84)

                if is_final_packshot:
                    # Final Packshot: Bold centered brand + call to action button pill
                    filter_complex = (
                        f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                        f"crop={output_width}:{output_height},{motion_filt},"
                        f"eq=contrast=1.10:saturation=1.20,"
                        f"drawtext=text='{brand_head}'{font_opt}:fontsize={pack_brand_size}:fontcolor=white:x=(w-text_w)/2:y={pack_brand_y}:shadowcolor=black@0.9:shadowx=3:shadowy=3,"
                        f"drawtext=text='{cta_clean}'{font_opt}:fontsize={pack_cta_size}:fontcolor=white:x=(w-text_w)/2:y={pack_cta_y}:box=1:boxcolor=#059669@0.92:boxborderw=14:shadowcolor=black@0.8:shadowx=2:shadowy=2"
                    )
                else:
                    # Action Scenes (1, 2, 3): Subtle top brand pill + centered compact action caption pill (NOT covering product!)
                    filter_complex = (
                        f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                        f"crop={output_width}:{output_height},{motion_filt},"
                        f"eq=contrast=1.10:saturation=1.20,"
                        f"drawtext=text='{brand_head}'{font_opt}:fontsize={action_brand_size}:fontcolor=white@0.90:x=(w-text_w)/2:y={action_brand_y}:box=1:boxcolor=black@0.45:boxborderw=8,"
                        f"drawtext=text='{shot_text}'{font_opt}:fontsize={action_tag_size}:fontcolor=white:x=(w-text_w)/2:y={action_tag_y}:box=1:boxcolor=black@0.60:boxborderw=12:shadowcolor=black@0.8:shadowx=2:shadowy=2"
                    )"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open("web_ec2/main.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Successfully patched filter_complex variables in main.py!")
else:
    print("target not found")
