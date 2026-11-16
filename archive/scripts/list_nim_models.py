import os
from openai import OpenAI
from pathlib import Path

env_file = Path("/home/ubuntu/synquic_app/.env")
api_key = None
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("NVIDIA_API_KEY="):
            api_key = line.split("=", 1)[1].strip()

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

try:
    models = client.models.list()
    ids = [m.id for m in models.data]
    print(f"Total available models: {len(ids)}")
    print("Sample models:")
    for mid in sorted(ids)[:40]:
        print(" -", mid)
except Exception as e:
    print("Failed to list models:", e)
