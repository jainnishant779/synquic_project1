import urllib.request, json

data = {
    "test_case_id": "TC_DIR_01",
    "selected_model_ids": ["nvidia/nemotron-3.5-lightning-30b-a3b"],
    "temperature": 0.2
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/arena/run",
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("ARENA STATUS:", res.get("status"))
        for r in res.get("results", []):
            print("Model:", r.get("model_id"))
            print("Status:", r.get("status"))
            print("Latency:", r.get("latency_s"))
            print("Is JSON Valid:", r.get("is_valid_json"))
            print("Output preview:", r.get("output_text")[:100].replace("\n", " "))
except Exception as e:
    print("Arena Call Failed:", e)
