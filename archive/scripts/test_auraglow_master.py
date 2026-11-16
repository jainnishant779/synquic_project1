import asyncio, subprocess
from pathlib import Path
import edge_tts

stills_dir = Path("/home/ubuntu/synquic_app/static/media/stills")
projects_dir = Path("/home/ubuntu/synquic_app/static/media/projects")

serum_flux = stills_dir / "img__serum__flux2_klein_4b__seed42.png"
serum_sana = stills_dir / "img__serum__sana_1600m__seed42.png"

# 1. Shot 1: Macro Push-In (5s)
sh1 = projects_dir / "auraglow_sh1.mp4"
f1 = "zoompan=z='min(zoom+0.0015,1.25)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
subprocess.run([
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(serum_flux), "-vf", f1, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(sh1)
], check=True)

# 2. Shot 2: Smooth Pan & Zoom (5s)
sh2 = projects_dir / "auraglow_sh2.mp4"
f2 = "zoompan=z='min(zoom+0.001,1.15)':d=120:x='(iw-iw/zoom)*(1-on/120)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
subprocess.run([
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(serum_sana), "-vf", f2, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(sh2)
], check=True)

# 3. Shot 3: Hero Packshot Zoom-Out (5s)
sh3 = projects_dir / "auraglow_sh3.mp4"
f3 = "zoompan=z='if(lte(zoom,1.0),1.15,max(1.001,zoom-0.0012))':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
subprocess.run([
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(serum_flux), "-vf", f3, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(sh3)
], check=True)

print("Created 3 cinematic shots!")

# Concat shots
concat_file = projects_dir / "auraglow_concat.txt"
with open(concat_file, "w") as f:
    f.write(f"file '{sh1.resolve().as_posix()}'\n")
    f.write(f"file '{sh2.resolve().as_posix()}'\n")
    f.write(f"file '{sh3.resolve().as_posix()}'\n")

# 4. Generate Studio Voiceover (15s total)
script = (
    "Wake up to pure, organic botanical hydration. "
    "Infused with cold-pressed antioxidants for an all-day golden hour glow. "
    "AuraGlow. Your morning radiance ritual starts here."
)

voice_file = projects_dir / "auraglow_voice.mp3"
async def make_voice():
    comm = edge_tts.Communicate(script, "en-US-ChristopherNeural", rate="+4%")
    await comm.save(str(voice_file))
asyncio.run(make_voice())
print("Created voiceover audio!")

# 5. Assemble final 15s commercial with AAC audio and faststart
final_mp4 = projects_dir / "auraglow_master_commercial.mp4"
cmd = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", str(concat_file),
    "-i", str(voice_file),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    "-c:a", "aac", "-b:a", "192k",
    "-t", "15",
    str(final_mp4)
]
subprocess.run(cmd, check=True)
print("SUCCESS: Assembled AuraGlow Master Commercial:", final_mp4, "size:", final_mp4.stat().st_size)
