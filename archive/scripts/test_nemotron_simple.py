import os, json
from openai import OpenAI
from pathlib import Path

env_file = Path("/home/ubuntu/synquic_app/.env")
for line in env_file.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("'\"")

api_key = os.environ.get("NVIDIA_API_KEY")
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

prompt = "make ad for homingo app -an home service provider app"

sys_msg = (
    "You are an expert commercial director. When given a product brief, create a 3-shot high-impact video commercial.\n"
    "Output MUST be raw valid JSON only with NO markdown and NO explanations:\n"
    "{\"title\": \"...\", \"shots\": ["
    "{\"shot_num\": 1, \"duration_s\": 5, \"type\": \"Hook\", \"visual_prompt\": \"...\", \"camera\": \"...\", \"narration\": \"...\", \"on_screen_text\": \"...\"},"
    "{\"shot_num\": 2, \"duration_s\": 5, \"type\": \"Features\", \"visual_prompt\": \"...\", \"camera\": \"...\", \"narration\": \"...\", \"on_screen_text\": \"...\"},"
    "{\"shot_num\": 3, \"duration_s\": 5, \"type\": \"Call to Action\", \"visual_prompt\": \"...\", \"camera\": \"...\", \"narration\": \"...\", \"on_screen_text\": \"...\"}"
    "]}"
)

resp = client.chat.completions.create(
    model="nvidia/nemotron-3.5-lightning-30b-a3b",
    messages=[
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": prompt}
    ],
    max_tokens=4096,
    temperature=0.1
)
raw = resp.choices[0].message.content or ""
print("RAW CONTENT:")
print(raw)
data = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
print("PARSED SUCCESSFULLY:", data["title"], len(data["shots"]), "shots")
for s in data["shots"]:
    print(f"Shot {s['shot_num']}: {s['on_screen_text']} | {s['narration']}")
