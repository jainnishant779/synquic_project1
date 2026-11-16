import os, subprocess, uuid
from pathlib import Path

app_dir = Path("/home/ubuntu/synquic_app")
media_dir = app_dir / "static" / "media"
projects_dir = media_dir / "projects"
projects_dir.mkdir(parents=True, exist_ok=True)

test_id = f"test_{uuid.uuid4().hex[:6]}"
out_mp4 = projects_dir / f"{test_id}.mp4"
concat_txt = projects_dir / f"{test_id}_concat.txt"

clip1 = media_dir / "prompt_1__ltx_video__seed42.mp4"
clip2 = media_dir / "prompt_2__ltx_video__seed42.mp4"
clip3 = media_dir / "prompt_3__ltx_video__seed42.mp4"

with open(concat_txt, "w") as f:
    f.write(f"file '{clip1.resolve().as_posix()}'\n")
    f.write(f"file '{clip2.resolve().as_posix()}'\n")
    f.write(f"file '{clip3.resolve().as_posix()}'\n")

# Assembly command with audio tone and faststart
cmd = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", str(concat_txt),
    "-f", "lavfi", "-i", "sine=frequency=220:sample_rate=48000:duration=15",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    "-c:a", "aac", "-b:a", "128k", "-shortest", str(out_mp4)
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("FFmpeg return code:", res.returncode)
if res.returncode != 0:
    print("Error:", res.stderr)
else:
    print("Success! Created:", out_mp4)
    print("Size:", out_mp4.stat().st_size)
    os.chmod(out_mp4, 0o755)
