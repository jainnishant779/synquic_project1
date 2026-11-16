import urllib.request
import json

# Let's test Pexels or Pixabay or Unsplash direct search
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Test Unsplash HTML search extraction
try:
    url = "https://unsplash.com/s/photos/modern-kitchen-sink-faucet"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode("utf-8", errors="ignore")
        import re
        imgs = re.findall(r'https://images\.unsplash\.com/photo-[^"\'\s&?]+', html)
        print("Unsplash found photo URLs:", len(imgs))
        if imgs:
            print("Sample Unsplash URL:", imgs[0])
except Exception as e:
    print("Unsplash HTML error:", e)

# Test Unsplash plumber search
try:
    url = "https://unsplash.com/s/photos/plumber-repair"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode("utf-8", errors="ignore")
        imgs = re.findall(r'https://images\.unsplash\.com/photo-[^"\'\s&?]+', html)
        print("Unsplash plumber photos:", len(imgs))
        if imgs:
            print("Sample plumber URL:", imgs[0])
except Exception as e:
    print("Unsplash plumber error:", e)
