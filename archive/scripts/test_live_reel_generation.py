import requests, time, json

url = "http://13.205.82.99/api/studio/generate"
payload = {
    "prompt": "MAKE AD FOR PARKFNB BARRIER: High-tech commercial for ParkFnB Intelligent Automated Boom Barrier, sleek illuminated LED barrier arm at modern corporate headquarters, 0.6 second high-speed RFID vehicle clearance, anti-crash radar protection, seamless multi-lane access.",
    "brand_name": "ParkFnB Barrier",
    "industry": "parking_barrier",
    "features": "0.6s Rapid Lift, RFID Access, Anti-Crash Radar Sensor",
    "target_audience": "Commercial & Facility Managers",
    "cta_text": "Install ParkFnB Barrier Today",
    "camera_dynamics": "macro_push",
    "lighting_mood": "studio_clean",
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
    "style": "Luxury Minimalist",
    "reference_assets": ["ref_bc3a5bf8"]
}

print("Calling /api/studio/generate on http://13.205.82.99 ...")
t0 = time.time()
try:
    res = requests.post(url, json=payload, timeout=180)
    dt = time.time() - t0
    print(f"Status Code: {res.status_code} in {dt:.2f}s")
    data = res.json()
    print(json.dumps(data, indent=2))
except Exception as e:
    print("Error:", e)
