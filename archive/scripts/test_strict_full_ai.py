import urllib.request
import json

payload = {
    "prompt": "test strict full ai without fallback",
    "generation_mode": "full_ai",
    "allow_fallback": False
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/studio/generate",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}
)

try:
    urllib.request.urlopen(req)
    print("Unexpected: should have failed!")
except urllib.error.HTTPError as e:
    print(f"Verified strict Full AI assertion: HTTP {e.code} -> {e.read().decode()}")
