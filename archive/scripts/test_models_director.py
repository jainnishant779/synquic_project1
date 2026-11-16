import os, json
from openai import OpenAI
from pathlib import Path

env_file = Path("/home/ubuntu/synquic_app/.env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

api_key = os.environ.get("NVIDIA_API_KEY", "")
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
prompt = "make ad for homingo app -an home service provider app"

models_to_test = [
    "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-70b-instruct",
    "mistralai/mistral-large-2-instruct",
    "nvidia/nemotron-3.5-lightning-30b-a3b"
]

for m in models_to_test:
    print(f"Testing {m}...")
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": "You are Commercial Director. Output pure JSON matching schema: {\"title\": str, \"shots\": [{\"shot_num\": int, \"duration_s\": 5, \"type\": str, \"visual_prompt\": str, \"camera\": str, \"narration\": str, \"on_screen_text\": str}]}"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.2,
            timeout=15.0
        )
        c = resp.choices[0].message.content
        print(f"SUCCESS {m}: Content length = {len(c) if c else 0}")
        if c:
            print("Preview:", c[:200])
            break
    except Exception as e:
        print(f"FAILED {m}: {e}")
