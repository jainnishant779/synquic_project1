import urllib.request
import urllib.parse
import time
import os
from PIL import Image

shots = [
    "Frustrated homeowner looking at sudden leaking kitchen pipe under sink water leaking emergency repair commercial photography vertical portrait",
    "Modern smartphone displaying sleek Homingo home services mobile app interface booking confirmed verified technician assigned glowing UI portrait",
    "Friendly certified home service technician in clean uniform with modern toolkit repairing faucet with precision in bright modern home",
    "Pristine sparkling modern living room and kitchen relaxed smiling homeowner holding phone peaceful clean luxury home five-star badge"
]

os.makedirs("/home/ubuntu/synquic_app/static/media/homingo_test", exist_ok=True)

for idx, prompt in enumerate(shots, 1):
    t0 = time.time()
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=576&height=1024&nologo=true&seed={idx*101}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SynquicAI/2.0"})
    out_p = f"/home/ubuntu/synquic_app/static/media/homingo_test/scene_{idx}.jpg"
    with urllib.request.urlopen(req, timeout=35) as resp:
        data = resp.read()
    with open(out_p, "wb") as f:
        f.write(data)
    with Image.open(out_p) as im:
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGB")
        im.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
        im.save(out_p, "JPEG", quality=88)
        size = im.size
    print(f"Shot {idx} generated in {time.time()-t0:.2f}s ({os.path.getsize(out_p)} bytes, {size})")
