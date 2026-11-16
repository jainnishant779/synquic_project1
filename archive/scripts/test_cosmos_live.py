import sys, urllib.request, urllib.error, json
from pathlib import Path

sys.path.insert(0, "/home/ubuntu/synquic_app")
from main import get_api_key

api_key = get_api_key()
url = "https://ai.api.nvidia.com/v1/cosmos/nvidia/cosmos3-nano"
req = urllib.request.Request(
    url,
    data=b"{}",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
)
try:
    with urllib.request.urlopen(req) as resp:
        print("Response:", resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Headers:", dict(e.headers))
    print("Body:", e.read().decode())
