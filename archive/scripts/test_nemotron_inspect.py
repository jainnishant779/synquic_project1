import os, time, json
from openai import OpenAI

api_key = None
if os.path.exists('/home/ubuntu/synquic_app/.env'):
    for line in open('/home/ubuntu/synquic_app/.env'):
        if line.startswith('NVIDIA_API_KEY='):
            api_key = line.strip().split('=', 1)[1].strip('"\' ')

client = OpenAI(base_url='https://integrate.api.nvidia.com/v1', api_key=api_key)

resp = client.chat.completions.create(
    model='nvidia/nemotron-3.5-lightning-30b-a3b',
    messages=[
        {"role": "user", "content": "Write a 3-shot commercial storyboard for Vishal Perfume in JSON"}
    ],
    max_tokens=2048,
    temperature=0.2,
    timeout=20.0
)
msg = resp.choices[0].message
print("Content:", msg.content)
print("Reasoning length:", len(getattr(msg, 'reasoning_content', '') or ''))
print("Model extra:", getattr(msg, 'model_extra', None))
