import subprocess
from pathlib import Path

stills_dir = Path("/home/ubuntu/synquic_app/static/media/stills")
out_dir = Path("/home/ubuntu/synquic_app/static/media/projects")
serum_img = stills_dir / "img__serum__flux2_klein_4b__seed42.png"
out_clip = out_dir / "test_serum_macro.mp4"

# 5 seconds, 24fps (120 frames), slow smooth push-in
filter_str = (
    "zoompan=z='min(zoom+0.0012,1.20)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
)

cmd = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(serum_img),
    "-vf", filter_str,
    "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    str(out_clip)
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("FFmpeg returncode:", res.returncode)
if res.returncode == 0:
    print("Created smooth macro shot:", out_clip, "size:", out_clip.stat().st_size)
else:
    print("Error:", res.stderr)
