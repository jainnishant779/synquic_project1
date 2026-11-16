import subprocess
from pathlib import Path

media_dir = Path("/home/ubuntu/synquic_app/static/media")
for mp4 in list(media_dir.glob("*.mp4")) + list(media_dir.glob("projects/*.mp4")):
    tmp = mp4.with_suffix(".tmp.mp4")
    cmd = ["ffmpeg", "-y", "-i", str(mp4), "-c", "copy", "-movflags", "+faststart", str(tmp)]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
        tmp.replace(mp4)
        print(f"Faststarted: {mp4.name} ({mp4.stat().st_size} bytes)")
    else:
        print(f"Failed {mp4.name}: {res.stderr.decode()[:100]}")
