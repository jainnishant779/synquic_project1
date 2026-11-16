import subprocess, time
from pathlib import Path

# Test multi-layer 9:16 vertical reel rendering on EC2 with ref_user_parkfnb.png or barrier_hero.jpg
input_image = Path("/home/ubuntu/synquic_app/static/media/references/ref_bc3a5bf8.png")
if not input_image.exists():
    input_image = Path("/home/ubuntu/synquic_app/static/media/stills/barrier_hero.jpg")

output_mp4 = Path("/tmp/test_pro_reel_scene.mp4")

# Multi-layer filter graph:
# [0:v] split into background [bg] and foreground [fg]
# [bg]: scale to fill 1080x1920, crop, blur heavily, darken slightly
# [fg]: scale to fit width 1000 in center with high quality
# Overlay [fg] on [bg] in center
# Add color grading (contrast/saturation boost)
# Add bold kinetic typography with drop shadow (no ugly black box)
filter_complex = (
    "[0:v]split=2[v_bg][v_fg];"
    "[v_bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "boxblur=20:5,eq=brightness=-0.12:contrast=1.2[bg];"
    "[v_fg]scale=1000:-1:force_original_aspect_ratio=decrease[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2-100[comp];"
    "[comp]eq=contrast=1.12:saturation=1.25,"
    "drawtext=text='PARKFNB BARRIER':fontsize=56:fontcolor=yellow:shadowcolor=black@0.9:shadowx=4:shadowy=4:x=(w-text_w)/2:y=1380,"
    "drawtext=text='INSTANT 0.6S RFID ACCESS':fontsize=38:fontcolor=white:shadowcolor=black@0.9:shadowx=3:shadowy=3:x=(w-text_w)/2:y=1450"
)

cmd = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(input_image),
    "-filter_complex", filter_complex,
    "-t", "3",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
    "-pix_fmt", "yuv420p", str(output_mp4)
]

print("Executing test FFmpeg Pro Reel multi-layer render...")
t0 = time.time()
subprocess.run(cmd, check=True)
dt = time.time() - t0
print(f"SUCCESS in {dt:.2f}s! Output size: {output_mp4.stat().st_size} bytes")

# Probe output
probe_cmd = [
    "ffprobe", "-v", "error", "-show_entries",
    "stream=width,height,codec_name,avg_frame_rate -show_entries format=duration,bit_rate",
    "-of", "json", str(output_mp4)
]
probe_out = subprocess.check_output(probe_cmd).decode()
print("Probe output:")
print(probe_out)
