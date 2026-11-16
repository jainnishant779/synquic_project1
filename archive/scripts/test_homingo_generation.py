import urllib.request, json, time

url = "http://127.0.0.1:8000/api/studio/generate"
payload = {
    "prompt": "make ad for homingo app -an home service provider app",
    "brand_name": "homingo",
    "industry": "instagram",
    "features": "all type of home service, fast in 30min, well trained professionals",
    "target_audience": "Homeowners & Urban Families",
    "cta_text": "Download Homingo Today",
    "camera_dynamics": "macro_push",
    "lighting_mood": "daylight",
    "bgm_genre": "tech_ambient",
    "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "video_provider": "local_pro_reel",
    "video_model": "wan/v2.7/image-to-video",
    "generation_mode": "full_ai",
    "video_task": "image_to_video",
    "resolution": "1080p",
    "aspect_ratio": "9:16",
    "audio_voice": "auto",
    "motion_style": "pro_vertical_reel_motion",
    "allow_fallback": True,
    "duration_s": 15,
    "seed": 42,
    "style": "Modern Architectural",
    "reference_assets": []
}

print("Executing Homingo generation test on EC2 localhost...")
t0 = time.time()
req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        dt = time.time() - t0
        print(f"Status Code: {resp.status} in {dt:.2f}s")
        data = json.loads(resp.read().decode("utf-8"))
        print("TITLE:", data.get("title"))
        print("VIDEO URL:", data.get("video_url"))
        print("DURATION:", data.get("duration_s"))
        print("STORYBOARD SHOTS:")
        for s in data.get("storyboard", []):
            print(f"  Shot {s['shot_num']}: {s.get('on_screen_text')} | {s.get('narration')}")
        print("SCENE TRACES:")
        for t in data.get("scene_traces", []):
            print(f"  Scene {t['scene_num']}: Model = {t.get('model')}, Fallback = {t.get('fallback_used')}")
except Exception as e:
    print("Error:", e)
    if hasattr(e, "read"):
        print(e.read().decode("utf-8"))
