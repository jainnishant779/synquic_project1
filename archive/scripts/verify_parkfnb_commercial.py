import urllib.request, json, time

url = "http://13.205.82.99/api/studio/generate"
payload = {
    "prompt": "MAKE AD FOR PARKFNB BARRIER",
    "brand_name": "ParkFnB Barrier",
    "industry": "parking_barrier",
    "features": "0.6s Rapid Lift, RFID Vehicle Clearance, Anti-Crash Radar Sensor",
    "target_audience": "Commercial & Facility Managers",
    "cta_text": "Install ParkFnB Barrier Today",
    "camera_dynamics": "macro_push",
    "lighting_mood": "daylight",
    "bgm_genre": "tech_ambient",
    "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "image_model": "flux2_klein_4b",
    "video_provider": "nvidia_nim",
    "video_model": "wan-ai/wan2.2",
    "generation_mode": "full_ai",
    "video_task": "image_to_video",
    "resolution": "1080p",
    "quality_preset": "high",
    "allow_fallback": True,
    "duration_s": 15,
    "style": "Modern Architectural",
    "aspect_ratio": "16:9",
    "audio_voice": "en-US-ChristopherNeural",
    "motion_style": "kenburns_cinematic",
    "reference_assets": ["ref_bc3a5bf8"]
}

req_data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})

print("Submitting ParkFnB Barrier ad request with reference asset ref_bc3a5bf8...")
t0 = time.time()
with urllib.request.urlopen(req, timeout=120) as resp:
    dt = time.time() - t0
    data = json.loads(resp.read().decode("utf-8"))

print(f"Status: {data.get('status')} in {dt:.2f}s")
print("Project ID:", data.get("project_id"))
print("Title:", data.get("title"))
print("Category:", data.get("category"))
print("Product Entity:", data.get("product_entity"))
print("Video URL:", data.get("video_url"))
print("Storyboard shots count:", len(data.get("storyboard", [])))
for s in data.get("storyboard", []):
    print(f" - Shot {s.get('shot_num')}: {s.get('narration')} | Visual: {s.get('visual_prompt')[:60]}...")
print("QC Score:", data.get("qc_report", {}).get("score"))
print("Fallback Used:", data.get("qc_report", {}).get("fallback_used"))
print("Cross contamination detected:", data.get("qc_report", {}).get("cross_contamination_detected"))
print("Scene traces:")
for trc in data.get("scene_traces", []):
    print(f" * Scene {trc.get('scene_num')}: {trc.get('product')} | source={trc.get('asset_source')} | model={trc.get('model')}")
