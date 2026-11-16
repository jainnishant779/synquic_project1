import os
from openai import OpenAI

key = ""
with open("/home/ubuntu/synquic_app/.env") as f:
    for line in f:
        if line.startswith("NVIDIA_API_KEY="):
            key = line.split("=", 1)[1].strip()

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key)

models = [
    "mistralai/mistral-large-4-1t-a52b",
    "deepseek-ai/deepseek-v4.1-flash",
    "google/gemma-4-31b-it",
    "minimaxai/minimax-m3.1-flash",
    "nvidia/nemotron-3.5-lightning-30b-a3b"
]

for m in models:
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Return pure JSON only: {\"status\": \"ok\", \"shot_name\": \"macro_drop\"}"}],
            max_tokens=400,
            temperature=0.1
        )
        c = resp.choices[0]
        print(f"=== {m} ===")
        print("Finish reason:", c.finish_reason)
        print("Content:", repr(c.message.content)[:200])
        reasoning = ""
        if hasattr(c.message, "model_extra") and c.message.model_extra:
            reasoning = c.message.model_extra.get("reasoning_content") or ""
        print("Reasoning length:", len(reasoning))
        if reasoning:
            print("Reasoning snippet:", repr(reasoning[:100]))
    except Exception as e:
        print(f"=== {m} ERROR: {e}")
