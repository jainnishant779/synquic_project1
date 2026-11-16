import os, time, json
from openai import OpenAI
from pathlib import Path

env_file = Path("/home/ubuntu/synquic_app/.env")
api_key = None
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("NVIDIA_API_KEY="):
            api_key = line.split("=", 1)[1].strip()

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

models = ["mistralai/mistral-7b-instruct-v0.3", "nvidia/nemotron-3.5-lightning-30b-a3b", "deepseek-ai/deepseek-v4.1-flash"]

prompt = "Generate a JSON object with keys 'title', 'tagline', and 'shots' (array of 3 shot descriptions) for a luxury watch commercial. Output ONLY JSON."

for m in models:
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": "You are a professional video director. Always output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.2
        )
        dt = round(time.time() - t0, 2)
        choice = resp.choices[0]
        content = choice.message.content or ""
        reasoning = (choice.message.model_extra or {}).get("reasoning_content", "") if hasattr(choice.message, "model_extra") else ""
        print(f"=== Model: {m} (time: {dt}s) ===")
        print(f"Content length: {len(content)}")
        print(f"Reasoning length: {len(reasoning)}")
        if content:
            print("Content preview:\n", content[:300])
        elif reasoning:
            print("Reasoning preview:\n", reasoning[:300])
    except Exception as e:
        print(f"=== Model {m} FAILED in {round(time.time() - t0, 2)}s: {e}")
