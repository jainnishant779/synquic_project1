import os, time, sys
from openai import OpenAI

api_key = None
if os.path.exists('/home/ubuntu/synquic_app/.env'):
    for line in open('/home/ubuntu/synquic_app/.env'):
        if line.startswith('NVIDIA_API_KEY='):
            api_key = line.strip().split('=', 1)[1].strip('"\' ')

client = OpenAI(base_url='https://integrate.api.nvidia.com/v1', api_key=api_key)

models = ['deepseek-ai/deepseek-v4.1-flash', 'nvidia/nemotron-3.5-lightning-30b-a3b']

for m in models:
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[{'role': 'user', 'content': 'Generate 3 shot names for a perfume ad'}],
            max_tokens=60,
            timeout=8.0
        )
        print(f"[{m}] Success in {time.time()-t0:.2f}s", flush=True)
    except Exception as e:
        print(f"[{m}] Error in {time.time()-t0:.2f}s: {e}", flush=True)
