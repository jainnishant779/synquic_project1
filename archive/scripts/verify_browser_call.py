import urllib.request
import json

payload = {
    "prompt": "MAKE AD FOR PROPERTY BROKER APP",
    "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "duration_s": 15,
    "style": "Luxury Minimalist",
    "aspect_ratio": "16:9",
    "audio_voice": "auto",
    "motion_style": "kenburns_slow"
}

req = urllib.request.Request(
    "http://13.205.82.99/api/studio/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

res = urllib.request.urlopen(req)
data = json.loads(res.read().decode("utf-8"))
print("Status:", data.get("status"))
print("Title:", data.get("title"))
print("Category:", data.get("category"))
print("Voice:", data.get("audio_voice"))
print("Motion:", data.get("motion_style"))
print("Video URL: http://13.205.82.99" + data.get("video_url"))
