import urllib.request, json

data = {
    "prompt": "High-energy urban commercial for TerraStride Eco-Runner sneaker on wet city asphalt at dusk with neon reflections",
    "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "duration_s": 15,
    "style": "Kinetic Urban Commercial",
    "aspect_ratio": "16:9"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/studio/generate",
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("STATUS:", res.get("status"))
        print("PROJECT ID:", res.get("project_id"))
        print("VIDEO URL:", res.get("video_url"))
        print("QC REPORT:", res.get("qc_report"))
        print("SHOTS COUNT:", len(res.get("storyboard", [])))
        for s in res.get("storyboard", []):
            print(f"Shot {s.get('shot_num')}: {s.get('type')} | {s.get('narration')}")
except Exception as e:
    print("API Call Failed:", e)
