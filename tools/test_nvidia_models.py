import os
import time
import json
import base64
from pathlib import Path
from openai import OpenAI

API_KEY = os.environ["NVIDIA_API_KEY"]  # never hardcode the key; set it in your environment
BASE_URL = "https://integrate.api.nvidia.com/v1"

client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=120.0)

USER_IMG = Path(r"C:\Users\nishant\.gemini\antigravity\brain\48cc587b-2b3a-4a83-bcc6-8438f11e1d78\.user_uploaded\media_1793701919007_651253de.png")
if not USER_IMG.exists():
    USER_IMG = Path("diagrams/01-video-pipeline.png")

with open(USER_IMG, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")
img_data_url = f"data:image/png;base64,{img_b64}"

results = {
    "vision_qc_tests": [],
    "social360_bakeoff": [],
    "storyboard_planner": []
}

def clean_output(msg):
    txt = msg.content or ""
    if not txt and hasattr(msg, "reasoning_content") and msg.reasoning_content:
        txt = f"[REASONING ONLY]: {msg.reasoning_content[:200]}..."
    return txt.strip()

print("="*60)
print("TEST 1: VISION & OCR / SEMANTIC QC (Task 1 Video)")
print("="*60)

vision_candidates = [
    "deepseek-ai/deepseek-v4.1-flash",
    "mistralai/mistral-large-4-1t-a52b",
    "meta/llama-3.2-11b-vision-instruct",
    "nvidia/nemotron-3.5-super-vl-120b-a12b"
]

prompt_vision = (
    "Look at this screenshot very carefully. "
    "1. What is the active popup modal in the top left? What does the main heading say? "
    "2. Transcribe any visible key or title in that modal. "
    "3. What web browser tabs are open? "
    "Keep answer structured and concise."
)

for model in vision_candidates:
    print(f"\n---> Testing Vision Model: {model}...")
    start_t = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_vision},
                    {"type": "image_url", "image_url": {"url": img_data_url}}
                ]
            }],
            max_tokens=600
        )
        dur = round(time.time() - start_t, 2)
        ans = clean_output(resp.choices[0].message)
        print(f"Latency: {dur}s")
        print(f"Output snippet:\n{ans[:300]}...\n")
        results["vision_qc_tests"].append({
            "model": model,
            "latency_s": dur,
            "status": "PASS",
            "output": ans
        })
    except Exception as e:
        dur = round(time.time() - start_t, 2)
        print(f"Error ({dur}s): {e}")
        results["vision_qc_tests"].append({
            "model": model,
            "latency_s": dur,
            "status": "FAIL",
            "error": str(e)
        })

print("="*60)
print("TEST 2: SOCIAL 360 BASE MODEL BAKE-OFF (Task 2 Brand Voice)")
print("="*60)

brand_candidates = [
    "google/gemma-4-31b-it",
    "openai/gpt-oss-20b",
    "meta/muse-glimmer-30b",
    "writer/palmyra-creative-122b",
    "deepseek-ai/deepseek-v4.1-flash"
]

social_prompt = (
    "Brand: 'AuraGlow' - Clean organic vegan face serum (30ml, $38).\n"
    "Target: Gen-Z / Millennials, urban, aesthetic-conscious.\n"
    "Task: Write 1 high-converting Instagram caption (with hook, benefit, CTA) "
    "and 1 punchy brand tagline. Tone: witty, aesthetic, confident, anti-hype."
)

for model in brand_candidates:
    print(f"\n---> Testing Social360 Candidate: {model}...")
    start_t = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are Social360, a premium brand AI copywriter."},
                {"role": "user", "content": social_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        dur = round(time.time() - start_t, 2)
        ans = clean_output(resp.choices[0].message)
        print(f"Latency: {dur}s")
        print(f"Output snippet:\n{ans[:250]}...\n")
        results["social360_bakeoff"].append({
            "model": model,
            "latency_s": dur,
            "status": "PASS",
            "output": ans
        })
    except Exception as e:
        dur = round(time.time() - start_t, 2)
        print(f"Error ({dur}s): {e}")
        results["social360_bakeoff"].append({
            "model": model,
            "latency_s": dur,
            "status": "FAIL",
            "error": str(e)
        })

print("="*60)
print("TEST 3: VIDEO STORYBOARD JSON PLANNER (Task 1 Video Pipeline)")
print("="*60)

planner_candidates = [
    "mistralai/mistral-large-4-1t-a52b",
    "google/gemma-4-31b-it",
    "deepseek-ai/deepseek-v4.1-flash"
]

planner_prompt = (
    "You are the Synquic Video Director. Break down a 15-second commercial for AuraGlow Serum into 3 shots (5s each).\n"
    "Return pure JSON with this schema:\n"
    "[\n"
    "  {\"shot\": 1, \"duration_s\": 5, \"type\": \"hero_product|lifestyle|macro\", \"visual_prompt\": \"...\", \"camera\": \"...\", \"audio_narration\": \"...\"},\n"
    "  ...\n"
    "]\n"
    "Rules: Never mention vendor names. Keep visuals photorealistic."
)

for model in planner_candidates:
    print(f"\n---> Testing Planner Model: {model}...")
    start_t = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You output valid JSON only. No prose markdown around it."},
                {"role": "user", "content": planner_prompt}
            ],
            max_tokens=600,
            temperature=0.3
        )
        dur = round(time.time() - start_t, 2)
        ans = clean_output(resp.choices[0].message)
        print(f"Latency: {dur}s")
        print(f"Output snippet:\n{ans[:250]}...\n")
        results["storyboard_planner"].append({
            "model": model,
            "latency_s": dur,
            "status": "PASS",
            "output": ans
        })
    except Exception as e:
        dur = round(time.time() - start_t, 2)
        print(f"Error ({dur}s): {e}")
        results["storyboard_planner"].append({
            "model": model,
            "latency_s": dur,
            "status": "FAIL",
            "error": str(e)
        })

out_file = Path("tools/nvidia_test_results.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\n" + "="*60)
print(f"ALL TESTS FINISHED. Saved to {out_file}")
print("="*60)
