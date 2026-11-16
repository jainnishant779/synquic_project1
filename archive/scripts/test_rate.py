import urllib.request, json

data = {
    "project_id": "proj_2039d986",
    "rating": 5,
    "feedback": "Cinematic morning lighting and accurate 15s pacing"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/studio/evaluate",
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode("utf-8"))
except Exception as e:
    print("Rating failed:", e)
