import asyncio, subprocess, time
from pathlib import Path
import edge_tts

app_dir = Path("/home/ubuntu/synquic_app")
media_dir = app_dir / "static" / "media"
projects_dir = media_dir / "projects"

async def gen_voice(text, out_path):
    comm = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="+5%")
    await comm.save(str(out_path))

text = (
    "Wake up to pure botanical hydration. "
    "Infused with cold-pressed active nutrients for an all-day natural radiance. "
    "AuraGlow. Your morning ritual starts here."
)

voice_mp3 = projects_dir / "demo_voice.mp3"
asyncio.run(gen_voice(text, voice_mp3))
print("Voice generated:", voice_mp3, "size:", voice_mp3.stat().st_size)

# Test assembling video with this voiceover
clip1 = media_dir / "prompt_1__ltx_video__seed42.mp4"
clip2 = media_dir / "prompt_2__ltx_video__seed42.mp4"
clip3 = media_dir / "prompt_3__ltx_video__seed42.mp4"

concat_txt = projects_dir / "demo_concat.txt"
with open(concat_txt, "w") as f:
    f.write(f"file '{clip1.resolve().as_posix()}'\n")
    f.write(f"file '{clip2.resolve().as_posix()}'\n")
    f.write(f"file '{clip3.resolve().as_posix()}'\n")

out_video = projects_dir / "demo_with_voice.mp4"

# Use FFmpeg to concat video and add the generated voiceover
cmd = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", str(concat_txt),
    "-i", str(voice_mp3),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    "-c:a", "aac", "-b:a", "192k",
    "-shortest",
    str(out_video)
]

proc = subprocess.run(cmd, capture_output=True, text=True)
print("FFmpeg return code:", proc.returncode)
if proc.returncode == 0:
    print("Created demo video with real voice:", out_video, "size:", out_video.stat().st_size)
else:
    print("FFmpeg error:", proc.stderr)
