import subprocess
from pathlib import Path

stills = Path("/home/ubuntu/synquic_app/static/media/stills")
clips = Path("/home/ubuntu/synquic_app/static/media/clips")
clips.mkdir(parents=True, exist_ok=True)

# 1. Sneaker Shot 1 (Macro Zoom)
sneaker_flux = stills / "img__sneaker__flux2_klein_4b__seed42.png"
f_zoom = "zoompan=z='min(zoom+0.0014,1.22)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
cmd1 = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(sneaker_flux), "-vf", f_zoom, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clips / "sneaker_sh1.mp4")
]
subprocess.run(cmd1, check=True)

# Sneaker Shot 3 (Hero Packshot)
sneaker_sana = stills / "img__sneaker__sana_1600m__seed42.png"
f_pan = "zoompan=z='min(zoom+0.001,1.15)':d=120:x='(iw-iw/zoom)*(1-on/120)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
cmd2 = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(sneaker_sana), "-vf", f_pan, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clips / "sneaker_sh3.mp4")
]
subprocess.run(cmd2, check=True)

# 2. Kettle Shot 1 (Macro Zoom)
kettle_flux = stills / "img__kettle__flux2_klein_4b__seed42.png"
cmd3 = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(kettle_flux), "-vf", f_zoom, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clips / "kettle_sh1.mp4")
]
subprocess.run(cmd3, check=True)

# Kettle Shot 3 (Hero Packshot)
kettle_sana = stills / "img__kettle__sana_1600m__seed42.png"
cmd4 = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(kettle_sana), "-vf", f_pan, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clips / "kettle_sh3.mp4")
]
subprocess.run(cmd4, check=True)

# 3. Serum shots
serum_flux = stills / "img__serum__flux2_klein_4b__seed42.png"
serum_sana = stills / "img__serum__sana_1600m__seed42.png"
cmd5 = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(serum_flux), "-vf", f_zoom, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clips / "serum_sh1.mp4")
]
subprocess.run(cmd5, check=True)

cmd6 = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(serum_sana), "-vf", f_pan, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clips / "serum_sh2.mp4")
]
subprocess.run(cmd6, check=True)

f_out = "zoompan=z='if(lte(zoom,1.0),1.15,max(1.001,zoom-0.0012))':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=768x448:fps=24"
cmd7 = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-i", str(serum_flux), "-vf", f_out, "-t", "5",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clips / "serum_sh3.mp4")
]
subprocess.run(cmd7, check=True)

print("Pre-rendered high quality cinematic clips in:", clips)
