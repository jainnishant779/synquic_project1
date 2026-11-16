import urllib.request, json, time

payload = {
    "prompt": "MAKE AD FOR INSTAGRAM",
    "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "duration_s": 15,
    "style": "Kinetic Urban Commercial",
    "aspect_ratio": "16:9"
}

print("POSTing 'MAKE AD FOR INSTAGRAM' to /api/studio/generate...")
t0 = time.time()
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/studio/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

dt = round(time.time() - t0, 2)
print(f"Generated in {dt}s!")
print(f"Project ID: {data.get('project_id')}")
print(f"Title: {data.get('title')}")
print(f"Product Entity: {data.get('product_entity')}")
print(f"Aspect Ratio: {data.get('aspect_ratio')}")
print(f"Video URL: {data.get('video_url')}")
print(f"Manifest URL: {data.get('manifest_url')}")

traces = data.get("scene_traces", [])
print(f"Scenes Count: {len(traces)}")
for trc in traces:
    print(f"  Scene {trc['scene_num']}: [{trc['asset_source']}] {trc['provider']} -> {trc['compiled_prompt'][:60]}... | Narration: {trc['narration']}")
