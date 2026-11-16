import urllib.request, json, time

url = "http://127.0.0.1:8000/api/studio/generate"
payload = {
    "prompt": "MAKE AD FOR PROPERTY BROKER APP",
    "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "image_model": "flux2_klein_4b",
    "audio_voice": "en-US-ChristopherNeural",
    "motion_style": "kenburns_cinematic",
    "duration_s": 15,
    "style": "Modern Architectural",
    "aspect_ratio": "16:9"
}

req_data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})

print("Submitting property broker ad request to:", url)
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        dt = time.time() - t0
        data = json.loads(resp.read().decode("utf-8"))

    print(f"Status: SUCCESS in {dt:.2f}s")
    print("Project ID:", data.get("project_id"))
    print("Title:", data.get("title"))
    print("Entity:", data.get("product_entity"))
    print("Category:", data.get("category"))
    print("Video URL:", data.get("video_url"))
    print("Storyboard shots:")
    for s in data.get("storyboard", []):
        print(f"  Shot {s.get('shot_num')}: OST='{s.get('on_screen_text')}' | Narration='{s.get('narration')}'")
except Exception as e:
    print(f"Request failed in {time.time()-t0:.2f}s: {e}")
