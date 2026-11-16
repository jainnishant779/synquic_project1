from openai import OpenAI
from pathlib import Path

env_file = Path("/home/ubuntu/synquic_app/.env")
api_key = None
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("NVIDIA_API_KEY="):
            api_key = line.split("=", 1)[1].strip()

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
models = client.models.list()
all_ids = sorted(m.id for m in models.data)
print(f"Total: {len(all_ids)}")
for mid in all_ids:
    print(mid)
