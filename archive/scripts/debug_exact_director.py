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

brand_display = "homingo"
product_entity = "homingo App"
category = "instagram"
prompt_text = "make ad for homingo app -an home service provider app"
features = "all type of home service, fast in 30min, well trained professionals"
target_audience = "Homeowners & Urban Families"
cta_text = "Download Homingo Today"

director_system_prompt = (
    "You are the Commercial Director of Synquic AI Autonomous Video Engine.\n"
    f"Brand Name: {brand_display}\n"
    f"Product Entity: {product_entity}\n"
    f"Target Category / Industry: {category}\n"
    f"Core Features / Value Proposition: {features}\n"
    f"Target Audience: {target_audience}\n"
    "Camera Movement Dynamics: Cinematic Macro Push-in\n"
    "Lighting & Mood Aesthetic: High-Tech Studio Clean\n"
    f"Call To Action (CTA): {cta_text}\n"
    "Commercial Duration: 15 seconds (exactly 3 shots, 5s each).\n"
    "Visual Style: Modern Architectural\n"
    "Return pure valid JSON:\n"
    "{\n"
    '  "title": str,\n'
    '  "product": str,\n'
    '  "shots": [\n'
    '    {"shot_num": 1, "duration_s": 5, "type": str, "visual_prompt": str, "camera": str, "narration": str, "on_screen_text": str}\n'
    "  ]\n"
    "}"
)

print("Calling Nemotron...")
try:
    resp = client.chat.completions.create(
        model="nvidia/nemotron-3.5-lightning-30b-a3b",
        messages=[
            {"role": "system", "content": director_system_prompt},
            {"role": "user", "content": f"Creative brief: {prompt_text}\nFeatures: {features}\nAudience: {target_audience}\nCall to action: {cta_text}"}
        ],
        max_tokens=4096,
        temperature=0.1,
        timeout=60.0
    )
    choice = resp.choices[0]
    raw_text = (choice.message.content or "").strip()
    reasoning = getattr(choice.message, "model_extra", {}).get("reasoning_content", "") or ""
    print("RAW TEXT LEN:", len(raw_text))
    print("REASONING LEN:", len(reasoning))
    print("RAW TEXT:")
    print(raw_text)
except Exception as e:
    print("EXCEPTION:", e)
