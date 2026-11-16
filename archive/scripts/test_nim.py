import os
from openai import OpenAI

api_key = None
if os.path.exists('/home/ubuntu/synquic_app/.env'):
    for line in open('/home/ubuntu/synquic_app/.env'):
        if line.startswith('NVIDIA_API_KEY='):
            api_key = line.strip().split('=', 1)[1].strip('"\' ')

client = OpenAI(base_url='https://integrate.api.nvidia.com/v1', api_key=api_key)

prompt = "make ad for perfume brand name vishal"
sys_msg = """You are the Planning Director of Synquic AI Commercial Video Engine.
Generate a 15-second commercial storyboard with exactly 3 shots (5s each).
Return pure valid JSON without markdown fences:
{
  "title": str,
  "product": str,
  "shots": [
    {"shot_num": 1, "duration_s": 5, "type": str, "visual_prompt": str, "camera": str, "narration": str, "on_screen_text": str, "dialect_wan": str, "dialect_veo": str}
  ]
}"""

for m in ['nvidia/nemotron-3.5-lightning-30b-a3b', 'mistralai/mistral-large-2-instruct', 'meta/llama-3.1-70b-instruct', 'deepseek-ai/deepseek-r1']:
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': f"Brief: {prompt}"}],
            max_tokens=2048,
            temperature=0.2,
            timeout=20.0
        )
        msg = resp.choices[0].message
        print(f"=== Model: {m} ===")
        print("content is None?:", msg.content is None)
        print("content preview:", (msg.content or "")[:200])
        print("reasoning preview:", (getattr(msg, 'reasoning_content', '') or '')[:100])
    except Exception as e:
        print(f"=== Model: {m} Failed: {e} ===")
