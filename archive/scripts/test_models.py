import os, time
from openai import OpenAI
from pathlib import Path

env_file = Path("/home/ubuntu/synquic_app/.env")
api_key = None
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("NVIDIA_API_KEY="):
            api_key = line.split("=", 1)[1].strip()

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

models_to_test = [
    "meta/llama-3.3-70b-instruct",
    "mistralai/mistral-large-2-instruct",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "deepseek-ai/deepseek-v3",
    "google/gemma-2-27b-it",
    "nvidia/nemotron-3.5-lightning-30b-a3b"
]

prompt = "You are an AI video director. Respond in valid JSON only with keys 'title' and 'tagline' for an organic green tea brand."

for m in models_to_test:
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,
            timeout=8.0
        )
        dt = round(time.time() - t0, 2)
        msg = resp.choices[0].message
        content = msg.content or ""
        reasoning = (msg.model_extra or {}).get("reasoning_content", "") if hasattr(msg, "model_extra") else ""
        print(f"[{m}] {dt}s -> content_len={len(content)}, reasoning_len={len(reasoning)}")
        if content:
            print(f"   Sample: {content[:100]}...")
    except Exception as e:
        dt = round(time.time() - t0, 2)
        print(f"[{m}] {dt}s -> FAILED: {str(e)[:80]}")
