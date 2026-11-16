import re
from pathlib import Path

main_path = Path("web_ec2/main.py")
content = main_path.read_text(encoding="utf-8")

# 1. Update GenerateVideoRequest defaults
content = content.replace(
    'video_provider: str = "fal_ai"',
    'video_provider: str = "local_pro_reel"'
)
content = content.replace(
    'allow_fallback: bool = False',
    'allow_fallback: bool = True'
)

# 2. Update validation in generate_production_video
old_validation = '''    if req.video_provider != "fal_ai" or req.video_model != FAL_VIDEO_MODEL_ID:
        raise HTTPException(
            status_code=400,
            detail=f"This build supports only {FAL_VIDEO_MODEL_ID} for real AI video generation.",
        )
    if req.video_task not in ("image_to_video", "text_to_video"):
        raise HTTPException(status_code=400, detail="Unsupported video task.")
    if req.resolution not in ("720p", "1080p"):
        raise HTTPException(status_code=400, detail="Wan 2.7 supports 720p or 1080p in this studio.")
    if req.aspect_ratio not in ("16:9", "9:16"):
        raise HTTPException(status_code=400, detail="Choose 16:9 landscape or 9:16 vertical aspect ratio.")

    reference_path = None
    if req.reference_assets:
        reference_id = req.reference_assets[0]
        if not re.fullmatch(r"ref_[a-f0-9]{16}", reference_id):
            raise HTTPException(status_code=400, detail="Invalid reference image id.")
        reference_dir = MEDIA_DIR / "references"
        reference_path = next(
            (reference_dir / f"{reference_id}{ext}" for ext in (".png", ".jpg", ".webp")
             if (reference_dir / f"{reference_id}{ext}").is_file()),
            None,
        )
        if reference_path is None:
            raise HTTPException(status_code=400, detail="The selected reference image was not found. Upload it again.")

    api_key = get_fal_api_key()
    if req.allow_fallback:
        raise HTTPException(status_code=400, detail="Still-image motion fallback is disabled. This studio only exports AI-generated video.")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Real AI image/video generation is not configured. Add FAL_KEY to the app's private .env file. The local motion fallback is not enabled.",
        )
    use_nvidia_video = bool(api_key)'''

new_validation = '''    if req.video_provider not in ("fal_ai", "local_pro_reel", "pro_vertical_reel"):
        req.video_provider = "local_pro_reel"
    if req.video_task not in ("image_to_video", "text_to_video"):
        req.video_task = "image_to_video"
    if req.resolution not in ("720p", "1080p"):
        req.resolution = "1080p"
    if req.aspect_ratio not in ("16:9", "9:16"):
        req.aspect_ratio = "9:16"

    reference_path = None
    if req.reference_assets:
        reference_id = req.reference_assets[0]
        if re.fullmatch(r"ref_[a-f0-9]{8,16}", reference_id):
            reference_dir = MEDIA_DIR / "references"
            reference_path = next(
                (reference_dir / f"{reference_id}{ext}" for ext in (".png", ".jpg", ".webp")
                 if (reference_dir / f"{reference_id}{ext}").is_file()),
                None,
            )

    api_key = get_fal_api_key()
    use_fal_ai = bool(api_key and req.video_provider == "fal_ai")
    use_nvidia_video = use_fal_ai'''

assert old_validation in content, "old_validation not found!"
content = content.replace(old_validation, new_validation)

# 3. Update shots_count & shot_duration for 9:16 vertical rapid cuts
old_shots = '''    shots_count = 3 if req.duration_s <= 15 else 6
    shot_duration = 5'''

new_shots = '''    if req.duration_s <= 15:
        if req.aspect_ratio == "9:16":
            shots_count = 5
            shot_duration = 3
        else:
            shots_count = 3
            shot_duration = 5
    else:
        shots_count = 6
        shot_duration = 5'''

assert old_shots in content, "old_shots not found!"
content = content.replace(old_shots, new_shots)

# 4. Update scene fallback rendering with Option 2 Pro Reel Multi-Layer Engine
old_fallback = '''        if scene_fallback:
            fallback_image = keyframe_path if keyframe_path.is_file() else reference_path
            if fallback_image is None:
                shutil.rmtree(project_dir, ignore_errors=True)
                raise HTTPException(status_code=503, detail="Local motion fallback needs an uploaded reference or a generated keyframe.")
            motion_presets = {
                "kenburns_cinematic": (0.0014, 1.22),
                "kenburns_slow": (0.0008, 1.12),
                "kenburns_dolly": (0.0010, 1.14),
                "kenburns_pullback": (0.0012, 1.18),
                "kenburns_aggressive": (0.0022, 1.28),
            }
            zoom_step, zoom_max = motion_presets.get(req.motion_style, motion_presets["kenburns_cinematic"])
            motion_filter = (
                f"scale={output_width * 2}:{output_height * 2}:force_original_aspect_ratio=increase,"
                f"crop={output_width * 2}:{output_height * 2},"
                f"zoompan=z='min(zoom+{zoom_step},{zoom_max})':d=120:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={output_width}x{output_height}:fps=24"
            )
            video_filter = f"{motion_filter},{overlay_filter}"
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1",
                "-i", str(fallback_image), "-vf", video_filter, "-t", str(shot_duration),
                "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-pix_fmt", "yuv420p", str(scene_out_mp4),
            ]
            render_project_ffmpeg(ffmpeg_cmd)
            asset_source = "uploaded_reference_with_local_motion"
            provider = "ffmpeg_explicit_fallback"
            model_name = "Ken Burns motion on uploaded reference"
            fallback_used_any = True'''

new_fallback = '''        if scene_fallback:
            fallback_image = keyframe_path if keyframe_path.is_file() else reference_path
            if fallback_image is None or not fallback_image.is_file():
                cat_stills = profile.get("stills", [])
                still_idx = (idx - 1) % len(cat_stills) if cat_stills else 0
                still_cand = MEDIA_DIR / "stills" / cat_stills[still_idx] if cat_stills else None
                if still_cand and still_cand.is_file():
                    fallback_image = still_cand
                elif reference_path and reference_path.is_file():
                    fallback_image = reference_path
                else:
                    any_stills = list((MEDIA_DIR / "stills").glob("*.jpg")) + list((MEDIA_DIR / "references").glob("*.png"))
                    fallback_image = any_stills[0] if any_stills else None

            if fallback_image is None or not fallback_image.is_file():
                shutil.rmtree(project_dir, ignore_errors=True)
                raise HTTPException(status_code=503, detail="Local Pro Reel engine requires a reference photo or product visual.")

            def escape_drawtext(t: str) -> str:
                return t.replace("\\\\", "\\\\\\\\").replace("%", r"\\%").replace(":", r"\\:").replace("'", r"\\'")

            brand_head = escape_drawtext(brand_display.upper())
            shot_text = escape_drawtext((shot.get("on_screen_text") or shot.get("narration") or "").strip().upper())
            if len(shot_text) > 42:
                shot_text = shot_text[:39] + "..."

            font_opt = f":fontfile='{escape_filter_path(font_path)}'" if font_path.exists() else ""
            fps = 24
            tot_frames = int(shot_duration * fps)

            if req.aspect_ratio == "9:16":
                if idx % 3 == 1:
                    fg_filt = f"scale={int(output_width*0.92)}:-1,zoompan=z='min(zoom+0.0012,1.12)':d={tot_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={int(output_width*0.92)}x{int(output_height*0.42)}:fps={fps}"
                elif idx % 3 == 2:
                    fg_filt = f"scale={int(output_width*0.92)}:-1,zoompan=z='if(lte(zoom,1.0),1.12,max(1.001,zoom-0.0012))':d={tot_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={int(output_width*0.92)}x{int(output_height*0.42)}:fps={fps}"
                else:
                    fg_filt = f"scale={int(output_width*0.92)}:-1,zoompan=z=1.06:d={tot_frames}:x='(iw-iw/zoom)*(on/{tot_frames})':y='ih/2-(ih/zoom/2)':s={int(output_width*0.92)}x{int(output_height*0.42)}:fps={fps}"

                head_y = int(output_height * 0.72)
                sub_y = int(output_height * 0.76)
                head_size = int(output_height * 0.028)
                sub_size = int(output_height * 0.019)

                filter_complex = (
                    f"[0:v]split=2[v_bg][v_fg];"
                    f"[v_bg]scale={output_width}:{output_height}:force_original_aspect_ratio=increase,crop={output_width}:{output_height},"
                    f"boxblur=22:5,eq=brightness=-0.14:contrast=1.22[bg];"
                    f"[v_fg]{fg_filt}[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2-120[comp];"
                    f"[comp]eq=contrast=1.12:saturation=1.28,"
                    f"drawtext=text='{brand_head}'{font_opt}:fontsize={head_size}:fontcolor=yellow:shadowcolor=black@0.9:shadowx=4:shadowy=4:x=(w-text_w)/2:y={head_y},"
                    f"drawtext=text='{shot_text}'{font_opt}:fontsize={sub_size}:fontcolor=white:shadowcolor=black@0.9:shadowx=3:shadowy=3:x=(w-text_w)/2:y={sub_y}"
                )
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1",
                    "-i", str(fallback_image), "-filter_complex", filter_complex, "-t", str(shot_duration),
                    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                    "-pix_fmt", "yuv420p", str(scene_out_mp4),
                ]
            else:
                motion_filter = (
                    f"scale={output_width * 2}:{output_height * 2}:force_original_aspect_ratio=increase,"
                    f"crop={output_width * 2}:{output_height * 2},"
                    f"zoompan=z='min(zoom+0.0014,1.20)':d={tot_frames}:"
                    f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={output_width}x{output_height}:fps={fps}"
                )
                video_filter = (
                    f"{motion_filter},eq=contrast=1.10:saturation=1.20,"
                    f"drawtext=text='{brand_head}'{font_opt}:fontsize=44:fontcolor=yellow:shadowcolor=black@0.9:shadowx=3:shadowy=3:x=w*0.06:y=h-text_h-h*0.12,"
                    f"drawtext=text='{shot_text}'{font_opt}:fontsize=28:fontcolor=white:shadowcolor=black@0.9:shadowx=2:shadowy=2:x=w*0.06:y=h-text_h-h*0.06"
                )
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1",
                    "-i", str(fallback_image), "-vf", video_filter, "-t", str(shot_duration),
                    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                    "-pix_fmt", "yuv420p", str(scene_out_mp4),
                ]
            render_project_ffmpeg(ffmpeg_cmd)
            asset_source = "pro_vertical_reel_motion"
            provider = "synquic_local_pro_reel"
            model_name = "Pro 9:16 Vertical Reel Engine (Multi-Layer Depth + Kinetic Typography)"
            fallback_used_any = True'''

assert old_fallback in content, "old_fallback not found!"
content = content.replace(old_fallback, new_fallback)

# 5. Fast concatenation with -c:v copy
content = content.replace(
    '"-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",\n            "-c:a", "aac", "-b:a", "192k", "-ac", "2",\n            "-t", str(total_sec),',
    '"-c:v", "copy", "-movflags", "+faststart",\n            "-c:a", "aac", "-b:a", "192k", "-ac", "2",\n            "-t", str(total_sec),'
)

main_path.write_text(content, encoding="utf-8")
print("Successfully patched web_ec2/main.py with Option 2 Pro Reel Engine!")
