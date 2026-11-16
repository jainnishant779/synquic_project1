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

models = ["nvidia/llama-3.1-nemotron-70b-instruct", "nv-mistralai/mistral-nemo-12b-instruct", "deepseek-ai/deepseek-v4.1-flash"]

prompt = "make ad for homingo app -an home service provider app. Brand: homingo"

for m in models:
    print(f"Testing {m}...")
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": "You are Commercial Director. Output pure valid JSON only matching schema: {\"title\": \"str\", \"shots\": [{\"shot_num\": 1, \"duration_s\": 5, \"type\": \"str\", \"visual_prompt\": \"str\", \"camera\": \"str\", \"narration\": \"str\", \"on_screen_text\": \"str\"}]}"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2
        )
        content = resp.choices[0].message.content
        print(f"SUCCESS {m} (len: {len(content)}):")
        print(content[:300])
        print("---")
        break
    except Exception as e:
        print(f"Failed {m}: {e}")
