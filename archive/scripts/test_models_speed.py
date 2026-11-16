import os, time
from openai import OpenAI

api_key = None
if os.path.exists('/home/ubuntu/synquic_app/.env'):
    for line in open('/home/ubuntu/synquic_app/.env'):
        if line.startswith('NVIDIA_API_KEY='):
            api_key = line.strip().split('=', 1)[1].strip('"\' ')

client = OpenAI(base_url='https://integrate.api.nvidia.com/v1', api_key=api_key)

prompt_text = "make ad for perfume brand name vishal"
product_entity = "Vishal Luxury Perfume"
brand_candidate = "Vishal"
category = "perfume"
shots_count = 3
shot_duration = 5

director_system_prompt = (
    "You are the Commercial Director of Synquic AI Autonomous Video Engine.\n"
    f"Client Brief: {prompt_text}\n"
    f"Brand / Product: {product_entity}\n"
    f"Target Category: {category}\n"
    f"Generate a 15-second commercial storyboard with exactly {shots_count} shots ({shot_duration}s each).\n"
    "CRITICAL BRAND REQUIREMENTS:\n"
    f"1. The product brand '{brand_candidate}' MUST be prominently featured in the narration voiceover and on-screen text.\n"
    "2. Do NOT invent unrelated brand names.\n"
    "3. Keep each shot narration punchy (under 12 spoken words) and impactful.\n"
    "4. Keep on_screen_text punchy in uppercase (2 to 4 words max).\n"
    "Return pure valid JSON:\n"
    "{\n"
    '  "title": str,\n'
    '  "product": str,\n'
    '  "shots": [\n'
    '    {"shot_num": 1, "duration_s": 5, "type": str, "visual_prompt": str, "camera": str, "narration": str, "on_screen_text": str, "dialect_wan": str, "dialect_veo": str}\n'
    "  ]\n"
    "}"
)

models = [
    'deepseek-ai/deepseek-v4.1-flash',
    'nvidia/nemotron-3.5-lightning-30b-a3b',
    'google/gemma-4-31b-it',
    'writer/palmyra-creative-122b'
]

for m in models:
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": director_system_prompt},
                {"role": "user", "content": f"Brief: {prompt_text}"}
            ],
            max_tokens=1500,
            temperature=0.2,
            timeout=20.0
        )
        dt = time.time() - t0
        content = resp.choices[0].message.content or ""
        print(f"[{m}] Time: {dt:.2f}s | Content len: {len(content)}")
        print(content[:300])
        print("-" * 50)
    except Exception as e:
        print(f"[{m}] Failed in {time.time()-t0:.2f}s: {e}")
