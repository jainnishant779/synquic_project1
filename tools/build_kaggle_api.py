"""Write notebooks/synquic_kaggle_2_api_models.ipynb: paid image and video APIs through one fal key (plus xAI direct)."""
from kaggle_core import (FINISH_CELL, QC_CELL, RATE_CELL, RATE_MD, RUN_CELL, SETUP_HEAD, VIEW_CELL, write_notebook)

INTRO = r'''# Synquic Notebook 2: Paid API models

Yeh notebook **paid API models** test karta hai: product stills (Nano Banana 2.1, GPT Image 2, Recraft, FLUX 3), phir un stills ko video banata hai (MiniMax H3, Wan 3.0, Gemini Omni Flash, HeyGen, FLUX 3 Video, Seedance 2.5, Kling 4.0, Grok Lite). **GPU ki zaroorat nahi**, isliye Kaggle ka GPU quota bachta hai.

**Kaise chalana hai**

1. Kaggle par: *Create > Import Notebook*. Right panel: Accelerator **None**, **Internet: On**.
2. **Add-ons > Secrets** mein keys daalo (chat mein kabhi paste mat karna):

| Secret | Kis liye | Kahan se |
|---|---|---|
| `FAL_KEY` | Zyadatar models (ek key se) | fal.ai dashboard, Keys. Billing mein credit daalna padega |
| `XAI_API_KEY` | Sirf Grok Imagine Lite (sabse sasta) | console.x.ai |

3. **Pehle `SMOKE_TEST = True` chalao** (default). Yeh har model ko sabse chhoti clip se ek baar chalata hai, kul kharcha lagbhag $3.2 (4 stills samet). Isse pata chalta hai ki har endpoint sahi chal raha hai ya nahi.
4. Sab theek ho to `SMOKE_TEST = False` karke poora test chalao. Kul kharcha tab lagbhag $35 se $45 tak ho sakta hai. `MAX_API_SPEND_USD` is se upar jaane se rokta hai.
5. Output tab se `synquic_results.zip` download karo, phir `RATINGS` bharo (Cell 8).

**Free tier ke baare mein (2026-11-02 ko jaanch):** koi bhi yahan listed model API se free nahi hai. Alibaba Wan 3.0 ka 30 second free quota sirf Alibaba Cloud ke Singapore region ke apne API se milta hai, fal se nahi, aur woh is notebook mein jodha nahi gaya. Gemini API ka free tier Nano Banana aur Omni Flash ko cover nahi karta. Isliye is notebook ka kharcha sach mein paid hai.

**Pehli baar chalne par:** yeh endpoints research se liye gaye hain, kisi ne abhi live call nahi ki. Agar kisi model par field ka error aaya, notebook khud sirf zaroori fields ke saath ek baar dobara koshish karta hai, aur wajah `results.csv` ke `note` column mein likhta hai. Har paid call ka jawab `raw_responses.jsonl` mein bhi save hota hai.

**Dhyan rakho:** sirf testing. Koi customer data, logo ya asli logon ki photo mat bhejo. Har vendor ke API terms testing par bhi lagu hote hain. MiniMax aur HeyGen ke API terms hum padh nahi sake.
'''

CONFIG = r'''# CELL 1: SIRF YAHAN BADLO
SMOKE_TEST = True   # True: har model ek chhoti clip, sirf pehla prompt (lagbhag $3). Sab chale to False karo.

PROMPTS = {
    "kettle": dict(still="A matte teal electric kettle on a kitchen counter, soft morning window light, clean commercial product photo",
                   motion="steam rises from the spout, slow push-in, photorealistic"),
    "tshirt": dict(still="Flat-lay of a white cotton T-shirt with a bold black printed graphic that reads NORTHWIND in block letters, studio product photo",
                   motion="a gentle breeze moves the fabric, slow camera tilt down"),
    "sneaker": dict(still="A white running sneaker with a neon green sole on wet city pavement at dusk, low angle, neon reflections, commercial photo",
                    motion="water ripples on the pavement, slow orbit around the shoe"),
    "serum": dict(still="A frosted glass skincare serum bottle with a clean label that reads GLOW 30ML on white marble, soft studio light",
                  motion="light slowly sweeps across the glass, subtle slow push-in"),
    "watch": dict(still="A silver wristwatch with a dark blue dial on a wrist, shallow depth of field, soft daylight, lifestyle product photo",
                  motion="the second hand ticks, the wrist turns slightly toward the camera"),
    "coffee": dict(still="A kraft paper coffee bag with a printed logo that reads EMBER ROAST on a wooden table, beans scattered, warm light",
                   motion="a few coffee beans roll across the table, slow dolly in"),
    "backpack": dict(still="A charcoal grey backpack standing on a city street at golden hour, urban commercial photo",
                     motion="the camera slowly walks around the bag, soft wind"),
    "headphones": dict(still="Matte black over-ear headphones on a pastel pink background, studio product photo, soft shadows",
                       motion="slow rotation of the headphones, light glints on the ear cups"),
}

# Image models (stills): nano_banana_21, gpt_image_2, recraft_v41, flux3_image
IMAGE_MODELS = ["nano_banana_21", "gpt_image_2", "recraft_v41", "flux3_image"]
# Video models. Default = hamari shortlist. Extra options: veo31, pixverse6, grok15_fal
VIDEO_MODELS = ["minimax_h3", "wan3", "omni_flash", "heygen_video1", "flux3_video", "seedance25", "kling4", "grok_lite_xai"]

STILL_SOURCE = "nano_banana_21"   # Video models is image ko pehla frame banate hain
USE_IMAGE_TO_VIDEO = True         # False: sirf text se video (product photo ke bina)
USER_PHOTOS = {}                  # Asli photo se test: {"tshirt": "/kaggle/input/my-photos/tshirt.jpg"}

SEEDS = [42]
ASPECT = "16:9"                   # "16:9" ya "9:16"
SECONDS = 5                       # Full test ki clip length (smoke test mein sabse chhoti allowed length)

MAX_API_SPEND_USD = 5.00 if SMOKE_TEST else 45.00   # Hard limit. Isse upar koi call nahi jayegi
MAX_RUNTIME_MINUTES = 240
GPU_USD_PER_HOUR = 0.0
SHOW_INLINE = True
'''

SETUP_API = r'''
FAL_KEY, XAI_API_KEY = secret("FAL_KEY"), secret("XAI_API_KEY")
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY
print("Keys:", {"FAL_KEY": bool(FAL_KEY), "XAI_API_KEY": bool(XAI_API_KEY)})
if not DRY_RUN:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        subprocess.run("apt-get -qq update && apt-get -qq install -y ffmpeg", shell=True, check=True)
    pip("fal-client", "requests", "pillow")
else:
    # Dry run uses a stand-in for fal_client, so the real call, retry and download code still runs with no network.
    fake = types.ModuleType("fal_client")

    def _subscribe(endpoint, arguments=None, **kwargs):
        arguments = arguments or {}
        if os.environ.get("SYNQUIC_FAKE_422") and "resolution" in arguments:
            raise ValueError("422 Unprocessable Entity: resolution must be one of the allowed values")
        folder = ROOT / "_fake"
        folder.mkdir(exist_ok=True)
        if any(word in endpoint for word in ("video", "veo", "h3", "wan", "omni", "kling", "seedance", "pixverse")):
            target = folder / f"{len(list(folder.iterdir()))}.mp4"
            seconds = float(re.search(r"[0-9.]+", str(arguments.get("duration", 2))).group())
            dry_clip(target, 320, 180, 12, seconds)
            return {"video": {"url": target.as_uri()}}
        target = folder / f"{len(list(folder.iterdir()))}.png"
        dry_image(target, 256, "")
        return {"images": [{"url": target.as_uri()}]}

    fake.subscribe = _subscribe
    fake.upload_file = lambda path: Path(path).as_uri()
    sys.modules["fal_client"] = fake
print("Prompts:", list(PROMPTS), "| Models:", MODELS, "| Dry run:", DRY_RUN)
'''

REGISTRY_CELL = r'''# CELL 3: MODEL REGISTRY
# price = USD per second (video) or per image, at the tier used here. price_max = worst case if the call falls back to defaults.
# verdict: Allowed = licence saaf, Counsel = lawyer chahiye. origin sirf record ke liye hai, kisi ko exclude nahi kiya.
def vid(t2v, i2v, price, price_max, min_s, max_s, extra, image_field="image_url", duration=int, durations=None, origin="", verdict="Counsel"):
    return dict(task="video", kind="api", route="fal", t2v=t2v, i2v=i2v, price=price, price_max=price_max, min_s=min_s, max_s=max_s, extra=extra,
                image_field=image_field, duration=duration, durations=durations, origin=origin, verdict=verdict)


def img(t2i, price, price_max, extra, origin="", verdict="Counsel"):
    return dict(task="image", kind="api", route="fal", t2i=t2i, price=price, price_max=price_max, extra=extra, origin=origin, verdict=verdict)


REGISTRY = {
    "nano_banana_21": img("google/nano-banana-2.1", 0.04, 0.06, lambda a: {"num_images": 1, "aspect_ratio": "1:1"}, origin="US"),
    "gpt_image_2":    img("openai/gpt-image-2", 0.053, 0.21, lambda a: {"image_size": "1024x1024", "quality": "medium", "num_images": 1}, origin="US"),
    "recraft_v41":    img("fal-ai/recraft/v4.1/text-to-image", 0.035, 0.05, lambda a: {"image_size": "square_hd"}, origin="UK"),
    "flux3_image":    img("blackforestlabs/flux-3/text-to-image", 0.048, 0.10, lambda a: {}, origin="Germany"),

    "minimax_h3":    vid("minimax/h3-max/text-to-video", "minimax/h3-max/image-to-video", 0.08, 0.13, 1, 15,
                         lambda a: {"resolution": "768P", "aspect_ratio": a}, duration=float, origin="China"),
    "wan3":          vid("alibaba/wan-3.0/text-to-video", "alibaba/wan-3.0/image-to-video", 0.10, 0.20, 2, 30,
                         lambda a: {"resolution": "720p", "aspect_ratio": a}, image_field="start_image_url", origin="China"),
    "omni_flash":    vid("google/gemini-omni-flash", "google/gemini-omni-flash/image-to-video", 0.125, 0.15, 3, 10,
                         lambda a: {"aspect_ratio": a}, origin="US"),
    "heygen_video1": vid("heygen/heygen-video/text-to-video", "heygen/heygen-video/image-to-video", 0.03, 0.09, 5, 15,
                         lambda a: {"resolution": "768p", "aspect_ratio": a}, origin="US"),
    "flux3_video":   vid("blackforestlabs/flux-3-max/text-to-video", "blackforestlabs/flux-3/image-to-video", 0.17, 0.29, 5, 20,
                         lambda a: {"resolution": "720p", "generate_audio": False}, origin="Germany"),
    "seedance25":    vid("bytedance/seedance-2.5/text-to-video", "bytedance/seedance-2.5/us/image-to-video", 0.22, 1.16, 4, 30,
                         lambda a: {"resolution": "480p", "generate_audio": False, "aspect_ratio": a}, duration=str, origin="China"),
    "kling4":        vid("kling/v4/text-to-video", "kling/v4/image-to-video", 0.157, 0.235, 3, 30,
                         lambda a: {"resolution": "720p", "aspect_ratio": a}, image_field="start_image_url", origin="China"),
    "grok15_fal":    vid("xai/grok-imagine-video/v1.5/text-to-video", "xai/grok-imagine-video/v1.5/image-to-video", 0.14, 0.25, 1, 15,
                         lambda a: {"resolution": "720p", "aspect_ratio": a}, origin="US"),
    "veo31":         vid("fal-ai/veo3.1", "fal-ai/veo3.1/image-to-video", 0.20, 0.40, 4, 8,
                         lambda a: {"resolution": "720p", "generate_audio": False, "aspect_ratio": a}, duration=lambda s: f"{s}s", durations=(4, 6, 8), origin="US"),
    "pixverse6":     vid("fal-ai/pixverse/v6/text-to-video", "fal-ai/pixverse/v6/image-to-video", 0.045, 0.115, 1, 15,
                         lambda a: {"resolution": "720p", "generate_audio_switch": False, "aspect_ratio": a}, origin="unverified"),
    # xAI direct: Lite is not on fal. Needs XAI_API_KEY.
    "grok_lite_xai": dict(task="video", kind="api", route="xai", model="grok-imagine-video-1.5-lite", price=0.02, price_max=0.05, min_s=1, max_s=15,
                          durations=None, origin="US", verdict="Counsel"),
}
unknown = [m for m in MODELS if m not in REGISTRY]
if unknown:
    raise SystemExit(f"Galat model naam: {unknown}. Options: {list(REGISTRY)}")
if SMOKE_TEST:
    PROMPTS = dict(list(PROMPTS.items())[:1])
    print("SMOKE_TEST: sirf pehla prompt, sabse chhoti clip, cap $", MAX_API_SPEND_USD)
'''

GENERATE_CELL = r'''# CELL 4: GENERATION (paid APIs)
import base64

api_spent = 0.0
RAW = ROOT / "raw_responses.jsonl"


def reset_peak():
    pass


def peak_vram():
    return None


def free_gpu():
    pass


def prepare(info):
    return None


def release(state):
    pass


def after_model(info):
    pass


def missing_key(info):
    if info["route"] == "xai":
        return None if XAI_API_KEY else "XAI_API_KEY secret nahi mila"
    return None if FAL_KEY else "FAL_KEY secret nahi mila"


def charge(cost):
    """Count the cost before the call, because a vendor may bill once the job is accepted."""
    global api_spent
    if api_spent + cost > MAX_API_SPEND_USD:
        raise RuntimeError(f"spend cap: ${api_spent + cost:.2f} would pass ${MAX_API_SPEND_USD:.2f}")
    api_spent += cost


def refund(cost):
    global api_spent
    api_spent -= cost


def pick_seconds(info):
    wanted = info["min_s"] if SMOKE_TEST else SECONDS
    wanted = max(info["min_s"], min(info["max_s"], wanted))
    if info.get("durations"):
        wanted = next((d for d in info["durations"] if d >= wanted), info["durations"][-1])
    return wanted


def looks_like_validation(error):
    text = f"{type(error).__name__} {error}".lower()
    if any(word in text for word in ("401", "403", "unauthorized", "forbidden", "balance", "insufficient", "credit", "quota", "rate limit", "429")):
        return False
    return any(word in text for word in ("422", "validation", "unprocessable", "must be one of", "not a valid", "enum", "unexpected", "not permitted"))


def find_url(result, suffixes):
    """First url in the result that looks like a file of this type. Page summaries of the schemas may be off, so search, not index."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "url" and isinstance(value, str):
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(result)
    return next((u for u in found if u.lower().split("?")[0].endswith(suffixes)), found[0] if found else None)


def log_raw(model, endpoint, args, result):
    with RAW.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"model": model, "endpoint": endpoint, "args": {k: v for k, v in args.items() if k != "prompt"}, "result": result}, default=str)[:4000] + "\n")


def paid_call(model, endpoint, units, info, full_args, minimal_args):
    """Call fal. If it rejects a field, retry once with only the essentials and count the worst-case price."""
    import fal_client
    cost = info["price"] * units
    charge(cost)
    try:
        result, note = fal_client.subscribe(endpoint, arguments=full_args), ""
    except Exception as error:
        if not looks_like_validation(error) or full_args == minimal_args:
            raise
        refund(cost)
        cost = info["price_max"] * units
        charge(cost)
        result = fal_client.subscribe(endpoint, arguments=minimal_args)
        note = "retried with minimal fields after: " + str(error)[:100].replace("\n", " ")
    log_raw(model, endpoint, full_args, result)
    return result, cost, note


def fetch(url, path):
    urllib.request.urlretrieve(url, path)


def call_xai(info, prompt, seconds, frame):
    import requests
    headers = {"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"}
    body = {"model": info["model"], "prompt": prompt, "duration": seconds}
    if frame is not None:
        body["image"] = {"url": "data:image/png;base64," + base64.b64encode(Path(frame).read_bytes()).decode()}
    reply = requests.post("https://api.x.ai/v1/videos/generations", headers=headers, json=body, timeout=120)
    reply.raise_for_status()
    request_id = reply.json().get("request_id") or reply.json().get("id")
    deadline = time.time() + 600
    while time.time() < deadline:
        time.sleep(5)
        status = requests.get(f"https://api.x.ai/v1/videos/{request_id}", headers=headers, timeout=60).json()
        url = (status.get("video") or {}).get("url")
        if url:
            return url
        if str(status.get("status", "")).lower() in ("failed", "expired", "error"):
            raise RuntimeError("xAI job " + str(status)[:150])
    raise TimeoutError("xAI job took over 10 minutes")


def generate(state, info, pid, seed, path):
    text = PROMPTS[pid]
    model = next(m for m, i in REGISTRY.items() if i is info)
    if info["task"] == "image":
        args = {"prompt": text["still"], **info["extra"](ASPECT)}
        result, cost, note = paid_call(model, info["t2i"], 1, info, args, {"prompt": text["still"]})
        fetch(find_url(result, (".png", ".jpg", ".jpeg", ".webp")), path)
        return {"cost": cost, "note": note}

    frame, origin = first_frame(pid)
    use_image = USE_IMAGE_TO_VIDEO and frame is not None and (info["route"] == "xai" or info.get("i2v"))
    prompt = text["motion"] if use_image else f'{text["still"]}, {text["motion"]}'
    seconds = pick_seconds(info)
    label = f"i2v from {origin}" if use_image else "text to video"
    if info["route"] == "xai":
        if DRY_RUN:
            charge(info["price"] * seconds)
            dry_clip(path, 320, 180, 12, seconds)
            return {"cost": info["price"] * seconds, "seconds": seconds, "note": label}
        charge(info["price"] * seconds)
        fetch(call_xai(info, prompt, seconds, frame if use_image else None), path)
        return {"cost": info["price"] * seconds, "seconds": seconds, "note": label}

    import fal_client
    essentials = {"prompt": prompt, "duration": info["duration"](seconds)}
    if use_image:
        essentials[info["image_field"]] = fal_client.upload_file(str(frame))
    full = {**essentials, **info["extra"](ASPECT)}
    endpoint = info["i2v"] if use_image else info["t2v"]
    result, cost, note = paid_call(model, endpoint, seconds, info, full, essentials)
    fetch(find_url(result, (".mp4", ".mov", ".webm")), path)
    return {"cost": cost, "seconds": seconds, "note": (label + "; " + note).strip("; ")}
'''


def main():
    cells = [
        ("markdown", INTRO),
        ("code", CONFIG),
        ("code", SETUP_HEAD + SETUP_API),
        ("code", REGISTRY_CELL),
        ("code", GENERATE_CELL),
        ("code", RUN_CELL),
        ("code", QC_CELL),
        ("code", VIEW_CELL),
        ("markdown", RATE_MD),
        ("code", RATE_CELL),
        ("code", FINISH_CELL),
    ]
    write_notebook("synquic_kaggle_2_api_models.ipynb", cells)


if __name__ == "__main__":
    main()
