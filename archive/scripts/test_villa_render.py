import subprocess
from pathlib import Path

still = "/home/ubuntu/synquic_app/static/media/stills/realestate_villa.jpg"
out_mp4 = "/home/ubuntu/synquic_app/test_villa_scene.mp4"
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

filt = (
    "zoompan=z='min(zoom+0.0014,1.22)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24,"
    f"drawtext=text='DISCOVER VERIFIED HOMES':fontfile={font_path}:fontcolor=white:fontsize=22:box=1:boxcolor=black@0.65:boxborderw=8:x=(w-text_w)/2:y=h-55"
)

cmd = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", still, "-vf", filt, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", out_mp4
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("FFmpeg return code:", res.returncode)
if res.stderr:
    print("FFmpeg stderr:", res.stderr)
else:
    print("Success! File size:", Path(out_mp4).stat().st_size)
