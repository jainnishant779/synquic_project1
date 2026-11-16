import urllib.request
import os
from PIL import Image

verified_homingo_images = [
    ("https://upload.wikimedia.org/wikipedia/commons/0/0d/Unprofessional_plumbing_pipe_repair.jpg", "homingo_scene1_leak.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/8/89/Smartphone_display_screen.jpg", "homingo_scene2_app.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/3/37/Electrician_Working.jpg", "homingo_scene3_expert.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/3/36/Living_room_in_apartment_of_Condom%C3%ADnio_do_Edif%C3%ADcio_Zaher%2C_Le_Blond%2C_Rio_de_Janeiro%2C_Brazil.jpg", "homingo_scene4_livingroom.jpg")
]

stills_dir = "/home/ubuntu/synquic_app/static/media/stills"
os.makedirs(stills_dir, exist_ok=True)

headers = {"User-Agent": "SynquicAI/2.0 (contact@synquic.ai; research and education)"}

for url, fname in verified_homingo_images:
    target_path = os.path.join(stills_dir, fname)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        with open(target_path, "wb") as f:
            f.write(data)
        with Image.open(target_path) as im:
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
            im.save(target_path, "JPEG", quality=88)
        print(f"Successfully saved {fname}: {os.path.getsize(target_path)} bytes, size {im.size}")
    except Exception as e:
        print(f"Failed {fname}: {e}")
