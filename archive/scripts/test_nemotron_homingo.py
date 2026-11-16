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
resp = client.chat.completions.create(
    model="nvidia/nemotron-3.5-lightning-30b-a3b",
    messages=[
        {"role": "system", "content": "You are Commercial Director. Output valid JSON with title, shots: [{shot_num: int, visual_prompt: str, narration: str, on_screen_text: str}]"},
        {"role": "user", "content": prompt}
    ],
    max_tokens=1000
)
msg = resp.choices[0].message
print("CONTENT:", msg.content)
print("EXTRA:", getattr(msg, "model_extra", None))
