import requests
import json
import time

payload = {
    "prompt": "make ad for homingo app -an home service provider app",
    "brand_name": "homingo",
    "industry": "Tech, SaaS & Mobile Apps",
    "duration_s": 15,
    "aspect_ratio": "9:16",
    "generation_mode": "pro_commercial",
    "video_provider": "local_pro_reel",
    "allow_fallback": True
}

print("Submitting request to http://13.205.82.99/api/studio/generate...")
t0 = time.time()
r = requests.post("http://13.205.82.99/api/studio/generate", json=payload, timeout=120)
print(f"Status Code: {r.status_code} in {time.time() - t0:.2f}s")
try:
    data = r.json()
    print("Project ID:", data.get("project_id"))
    print("Video URL:", data.get("final_video_url"))
    print("Category:", data.get("category"))
    print("QC Verdict:", data.get("qc_verdict"))
    print("QC Checks:", json.dumps(data.get("qc_checks"), indent=2))
    print("Scenes:", len(data.get("scene_traces", [])))
    for s in data.get("scene_traces", []):
        print(f"  Scene {s.get('scene_num')}: {s.get('asset_file')} - {s.get('narration')} | {s.get('camera_motion')}")
except Exception as e:
    print("Raw response:", r.text[:1000])
