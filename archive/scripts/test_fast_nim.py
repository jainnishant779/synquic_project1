import os, json, time
from openai import OpenAI
from pathlib import Path

env_file = Path("/home/ubuntu/synquic_app/.env")
for line in env_file.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip("'\"")

api_key = os.environ.get("NVIDIA_API_KEY")
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

models = [
    "nv-mistralai/mistral-nemo-12b-instruct",
    "deepseek-ai/deepseek-v4.1-flash",
    "openai/gpt-oss-20b",
    "meta/llama-3.2-11b-vision-instruct"
]

prompt = "make ad for homingo app -an home service provider app"

for m in models:
    t0 = time.time()
    print(f"Testing {m}...")
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": "You are Commercial Director. Output valid JSON with title, shots: [{shot_num, visual_prompt, narration, on_screen_text}]"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.2,
            timeout=10.0
        )
        content = resp.choices[0].message.content or ""
        print(f"-> SUCCESS {m} in {time.time()-t0:.2f}s! Len={len(content)}")
        print(content[:250])
        print("---")
    except Exception as e:
        print(f"-> FAILED {m} in {time.time()-t0:.2f}s: {e}")
