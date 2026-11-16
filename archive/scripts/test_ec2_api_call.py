import urllib.request, json, time

url = 'http://127.0.0.1:8000/api/studio/generate'
payload = {
    'prompt': 'MAKE AD FOR PARKFNB BARRIER: High-tech commercial for ParkFnB Intelligent Automated Boom Barrier, sleek illuminated LED barrier arm at modern corporate headquarters, 0.6 second high-speed RFID vehicle clearance, anti-crash radar protection, seamless multi-lane access.',
    'brand_name': 'ParkFnB Barrier',
    'industry': 'parking_barrier',
    'features': '0.6s Rapid Lift, RFID Access, Anti-Crash Radar Sensor',
    'target_audience': 'Commercial & Facility Managers',
    'cta_text': 'Install ParkFnB Barrier Today',
    'camera_dynamics': 'macro_push',
    'lighting_mood': 'studio_clean',
    'bgm_genre': 'tech_ambient',
    'director_model': 'nvidia/nemotron-3.5-lightning-30b-a3b',
    'video_provider': 'local_pro_reel',
    'video_model': 'wan/v2.7/image-to-video',
    'generation_mode': 'full_ai',
    'video_task': 'image_to_video',
    'resolution': '1080p',
    'aspect_ratio': '9:16',
    'audio_voice': 'auto',
    'motion_style': 'pro_vertical_reel_motion',
    'allow_fallback': True,
    'duration_s': 15,
    'seed': 42,
    'style': 'Luxury Minimalist',
    'reference_assets': ['ref_bc3a5bf8']
}

print("Executing test on EC2 localhost...")
t0 = time.time()
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        print("HTTP", resp.status, f"in {time.time()-t0:.2f}s")
        out = json.loads(resp.read().decode('utf-8'))
        print("STATUS:", out.get("status"))
        print("PROJECT ID:", out.get("project_id"))
        print("VIDEO URL:", out.get("video_url"))
        print("RESOLUTION:", out.get("resolution"), out.get("aspect_ratio"))
        print("QC VERDICT:", out.get("qc_report", {}).get("verdict"))
        print("QC SCORE:", out.get("qc_report", {}).get("score"))
        print("TECH CHECK:", json.dumps(out.get("qc_report", {}).get("technical_check"), indent=2))
except Exception as e:
    print("FAILED:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
