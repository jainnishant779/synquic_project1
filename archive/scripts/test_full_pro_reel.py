import subprocess, time, json
from pathlib import Path

scenes_dir = Path("/tmp/test_pro_reel_project/scenes")
scenes_dir.mkdir(parents=True, exist_ok=True)

input_image = Path("/home/ubuntu/synquic_app/static/media/references/ref_bc3a5bf8.png")
if not input_image.exists():
    input_image = Path("/home/ubuntu/synquic_app/static/media/stills/barrier_hero.jpg")

shots = [
    {"num": 1, "brand": "PARKFNB BARRIER", "text": "SMART PARKING REVOLUTION", "motion": "zoom_in"},
    {"num": 2, "brand": "0.6S RAPID LIFT", "text": "INSTANT RFID CLEARANCE", "motion": "pan_right"},
    {"num": 3, "brand": "MILITARY-GRADE RADAR", "text": "100% ANTI-CRASH PROTECTION", "motion": "zoom_in"},
    {"num": 4, "brand": "ALL-WEATHER DURABILITY", "text": "ZERO BOTTLENECK DELAYS", "motion": "zoom_out"},
    {"num": 5, "brand": "UPGRADE YOUR FACILITY", "text": "INSTALL PARKFNB TODAY", "motion": "zoom_in"}
]

clip_paths = []
t0 = time.time()
print("Starting 5-shot Pro Reel render...")

for s in shots:
    idx = s["num"]
    out_mp4 = scenes_dir / f"scene_{idx:03d}.mp4"
    brand = s["brand"]
    text = s["text"]
    
    # Motion presets for foreground
    if s["motion"] == "zoom_in":
        fg_filt = "scale=1000:-1,zoompan=z='min(zoom+0.0012,1.12)':d=72:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1000x800:fps=24"
    elif s["motion"] == "zoom_out":
        fg_filt = "scale=1000:-1,zoompan=z='if(lte(zoom,1.0),1.12,max(1.001,zoom-0.0012))':d=72:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1000x800:fps=24"
    else:
        fg_filt = "scale=1000:-1,zoompan=z=1.06:d=72:x='(iw-iw/zoom)*(on/72)':y='ih/2-(ih/zoom/2)':s=1000x800:fps=24"

    filter_complex = (
        f"[0:v]split=2[v_bg][v_fg];"
        f"[v_bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"boxblur=22:5,eq=brightness=-0.14:contrast=1.22[bg];"
        f"[v_fg]{fg_filt}[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2-120[comp];"
        f"[comp]eq=contrast=1.12:saturation=1.28,"
        f"drawtext=text='{brand}':fontsize=54:fontcolor=yellow:shadowcolor=black@0.9:shadowx=4:shadowy=4:x=(w-text_w)/2:y=1380,"
        f"drawtext=text='{text}':fontsize=36:fontcolor=white:shadowcolor=black@0.9:shadowx=3:shadowy=3:x=(w-text_w)/2:y=1455"
    )

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(input_image),
        "-filter_complex", filter_complex,
        "-t", "3",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-pix_fmt", "yuv420p", str(out_mp4)
    ]
    subprocess.run(cmd, check=True)
    clip_paths.append(out_mp4)
    print(f"Shot {idx}/5 done!")

# Concat
concat_txt = scenes_dir / "concat.txt"
with open(concat_txt, "w") as f:
    for p in clip_paths:
        f.write(f"file '{p.resolve().as_posix()}'\n")

final_mp4 = Path("/tmp/test_pro_reel_project/final_pro_reel.mp4")
bgm_path = Path("/home/ubuntu/synquic_app/static/media/bgm_energetic.mp3")

# Concat + mix BGM
filter_audio = "[1:a]volume=0.25,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[aout]"
cmd_final = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", str(concat_txt),
    "-i", str(bgm_path),
    "-filter_complex", filter_audio,
    "-map", "0:v", "-map", "[aout]",
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k",
    "-t", "15",
    "-movflags", "+faststart",
    str(final_mp4)
]
subprocess.run(cmd_final, check=True)
dt = time.time() - t0
print(f"ALL DONE in {dt:.2f}s! Final video: {final_mp4} (size: {final_mp4.stat().st_size} bytes)")

# Probe final
probe_cmd = [
    "ffprobe", "-v", "error", "-show_entries",
    "stream=width,height,codec_name,avg_frame_rate -show_entries format=duration,bit_rate",
    "-of", "json", str(final_mp4)
]
print(subprocess.check_output(probe_cmd).decode())
