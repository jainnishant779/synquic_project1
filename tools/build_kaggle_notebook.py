"""Write notebooks/synquic_video_benchmark.ipynb. Edit the cells here, then rebuild."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "notebooks" / "synquic_video_benchmark.ipynb"

CELLS = [
("markdown", r'''# Synquic Video Benchmark

Yeh notebook har **prompt** ko har **model** se chalata hai, phir quality check, cost comparison aur ek 30-second hybrid reel banata hai.

**Kaggle par kaise chalana hai**

1. Is notebook ko Kaggle par upload karo: *Create > Import Notebook*.
2. Right panel mein **Accelerator: GPU T4 x2** chuno, aur **Internet: On** karo. Internet ke liye phone verification chahiye hota hai.
3. Neeche Cell 1 mein `PROMPT_1`, `PROMPT_2`, `MODEL_1`, `MODEL_2` apne hisaab se badlo.
4. **Save Version > Save & Run All** chalao. Isse laptop band karke bhi run chalta rahega.
5. Khatam hone par Output tab se `synquic_results.zip` download karo.

**Optional secrets** (Add-ons > Secrets)

| Secret | Kis liye |
|---|---|
| `HF_TOKEN` | Hybrid reel ki images. Pehle Hugging Face par FLUX.1-schnell ki terms accept karo. Bina iske clip ke frame use honge |
| `FAL_KEY` | Paid models: Veo aur Kling. Bina iske paid models skip honge |

**Dhyan rakho:** yeh sirf testing ke liye hai. LTX ke liye lawyer ki rai baaki hai, aur `edge-tts` voice sirf test ke liye hai.
'''),

("code", r'''# CELL 1: SIRF YAHAN BADLO
PROMPT_1 = "Close-up of a matte teal electric kettle on a kitchen counter, steam rising from the spout, soft morning window light, slow push-in, photorealistic commercial"
PROMPT_2 = "A young woman in a mustard cardigan pours hot water into a mug in a sunlit home office and smiles, medium shot, gentle dolly right, photorealistic"
PROMPT_3 = "Fast montage feel: a sneaker lands on wet city pavement at dusk, water splashes in slow motion, neon reflections, low angle, cinematic"
PROMPT_4 = ""   # Khali chhodo to skip
PROMPT_5 = ""

# Options: ltx_video, wan21_480p, wan22_5b (GPU 24 GB maangta hai, T4 par fail ho sakta hai)
# Paid, FAL_KEY chahiye: veo_fast_fal, veo_std_fal, kling4_fal
MODEL_1 = "ltx_video"
MODEL_2 = "wan21_480p"
MODEL_3 = ""
MODEL_4 = ""
MODEL_5 = ""

SEEDS = [42]               # [42, 7, 123] se har combination 3 baar chalega
ASPECT = "16:9"            # "16:9" ya "9:16"
SECONDS = 5                # Target clip length
NEGATIVE = "blurry, low quality, distorted, deformed hands, extra fingers, text, watermark, flicker"

MAX_API_SPEND_USD = 2.00   # Paid models ki hard limit
MAX_RUNTIME_MINUTES = 240  # Itne time ke baad naye clips band
GPU_USD_PER_HOUR = 0.89    # Sirf reference: RunPod RTX 4090. Kaggle free hai
SHOW_INLINE = True         # Notebook mein videos dikhao

MAKE_REEL = True           # 30-second hybrid reel banao
VOICE = "en-IN-NeerjaNeural"   # Hindi ke liye "hi-IN-SwaraNeural"
REEL_SCENES = [
    {"type": "ai",    "prompt": "prompt_1", "seconds": 5, "text": "Your morning starts here"},
    {"type": "image", "prompt": "A matte teal electric kettle with a walnut handle on a marble counter, studio product photo", "seconds": 5, "text": "Boils in moments"},
    {"type": "ai",    "prompt": "prompt_2", "seconds": 5, "text": "Made for busy days"},
    {"type": "image", "prompt": "Cozy home office desk with a steaming mug beside a laptop, warm morning light", "seconds": 5, "text": "Calm before the first meeting"},
    {"type": "image", "prompt": "Close-up of a brushed steel kettle base with soft blue indicator light, macro product photo", "seconds": 5, "text": "Simple. Quiet. Beautiful."},
    {"type": "image", "prompt": "Teal kettle centered on a plain warm background, minimal advertising photo, empty space", "seconds": 5, "text": "Northwind Kettle"},
]
'''),

("code", r'''# CELL 2: SETUP
import csv, gc, html, json, math, multiprocessing, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

DRY_RUN = os.environ.get("SYNQUIC_DRY_RUN") == "1"
ROOT = Path(os.environ.get("SYNQUIC_OUT", "/kaggle/working/synquic"))
CLIPS, STILLS, REEL = ROOT / "clips", ROOT / "stills", ROOT / "reel"
for folder in (CLIPS, STILLS, REEL):
    folder.mkdir(parents=True, exist_ok=True)
RESULTS_CSV = ROOT / "results.csv"
START = time.time()

PROMPTS = {f"prompt_{i}": p.strip() for i, p in enumerate([PROMPT_1, PROMPT_2, PROMPT_3, PROMPT_4, PROMPT_5], 1) if p.strip()}
MODELS = [m for m in (MODEL_1, MODEL_2, MODEL_3, MODEL_4, MODEL_5) if m]


def secret(name):
    try:
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret(name)
    except Exception:
        return os.environ.get(name)


def pip(*packages):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *packages], check=True)


if not DRY_RUN:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        subprocess.run("apt-get -qq update && apt-get -qq install -y ffmpeg", shell=True, check=True)
    source = "git+https://github.com/huggingface/diffusers" if "wan22_5b" in MODELS else "diffusers"
    pip(source, "transformers", "accelerate", "sentencepiece", "ftfy", "imageio", "imageio-ffmpeg", "edge-tts", "fal-client")
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    import torch
    # Read the GPU through nvidia-smi. Starting CUDA in this process would stop models running in child processes.
    query = subprocess.run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", shell=True, capture_output=True, text=True)
    GPUS = query.stdout.strip().splitlines() if query.returncode == 0 else []
    if not GPUS and any(not m.endswith("_fal") for m in MODELS):
        raise SystemExit("GPU nahi mila. Right panel mein Accelerator: GPU T4 x2 chuno.")
    print("GPUs:", GPUS)
    # GPUs older than Ampere (such as T4) have no efficient attention for bfloat16. PyTorch then falls
    # back to a full n x n matrix, which asked for 48 GB on Wan. float16 keeps the efficient path.
    OLD_GPU = any(name in GPUS[0] for name in ("T4", "P100", "K80")) if GPUS else False
    DTYPE = torch.float16 if OLD_GPU else torch.bfloat16
    print("Model dtype:", DTYPE)

HF_TOKEN, FAL_KEY = secret("HF_TOKEN"), secret("FAL_KEY")
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY
print("Prompts:", list(PROMPTS), "| Models:", MODELS, "| Dry run:", DRY_RUN)


def save_zip():
    archive = shutil.make_archive(str(ROOT.parent / "synquic_results"), "zip", ROOT)
    print("Results saved:", archive, round(Path(archive).stat().st_size / 1e6, 1), "MB")
    return archive
'''),

("code", r'''# CELL 3: MODEL REGISTRY
# verdict: Allowed = licence clear, Counsel = lawyer chahiye. Prices USD per second.
WIDE = "16:9"
REGISTRY = {
    "ltx_video":  dict(kind="local", family="ltx", repo="Lightricks/LTX-Video", verdict="Counsel", fps=24, steps=40, guidance=5.0,
                       size={"16:9": (768, 448), "9:16": (448, 768)}),
    "wan21_480p": dict(kind="local", family="wan", repo="Wan-AI/Wan2.1-T2V-1.3B-Diffusers", verdict="Allowed", fps=16, steps=30, guidance=5.0,
                       size={"16:9": (832, 480), "9:16": (480, 832)}),
    "wan22_5b":   dict(kind="local", family="wan", repo="Wan-AI/Wan2.2-TI2V-5B-Diffusers", verdict="Allowed", fps=24, steps=30, guidance=5.0,
                       size={"16:9": (960, 544), "9:16": (544, 960)}),
    "veo_fast_fal": dict(kind="api", family="veo", endpoint="fal-ai/veo3.1/fast", verdict="Counsel", price=0.10, durations=(4, 6, 8)),
    "veo_std_fal":  dict(kind="api", family="veo", endpoint="fal-ai/veo3.1", verdict="Counsel", price=0.20, durations=(4, 6, 8)),
    "kling4_fal":   dict(kind="api", family="kling", endpoint="kling/v4/text-to-video", verdict="Counsel", price=0.235, durations=None),
}
unknown = [m for m in MODELS if m not in REGISTRY]
if unknown:
    raise SystemExit(f"Galat model naam: {unknown}. Options: {list(REGISTRY)}")


def frame_count(info):
    """LTX needs 8k+1 frames, Wan needs 4k+1."""
    step = 8 if info["family"] == "ltx" else 4
    return round((SECONDS * info["fps"] - 1) / step) * step + 1
'''),

("code", r'''# CELL 4: GENERATION
FONT = next((f for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arial.ttf") if Path(f).exists()), None)
api_spent = 0.0


def run(command):
    return subprocess.run(command, capture_output=True, text=True)


def font_arg():
    return "fontfile='" + FONT.replace(":", "\\:") + "'"


def dry_clip(path, width, height, fps, seconds):
    """Dry run only: a labelled test pattern, so the flow can be tested with no GPU."""
    label = f",drawtext={font_arg()}:text='DRY RUN':fontsize=24:fontcolor=white:box=1:boxcolor=red:x=10:y=10" if FONT else ""
    result = run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=s={width}x{height}:r={fps}:d={seconds}",
                  "-vf", "format=yuv420p" + label, "-c:v", "libx264", "-preset", "ultrafast", str(path)])
    if result.returncode:
        raise RuntimeError(result.stderr[-400:])


def load_local(info):
    import torch
    from diffusers import AutoencoderKLWan, LTXPipeline, WanPipeline, WanTransformer3DModel
    if info["family"] == "ltx":
        pipe = LTXPipeline.from_pretrained(info["repo"], torch_dtype=DTYPE)
    else:
        transformer = WanTransformer3DModel.from_pretrained(info["repo"], subfolder="transformer", torch_dtype=DTYPE)
        vae = AutoencoderKLWan.from_pretrained(info["repo"], subfolder="vae", torch_dtype=torch.float32)
        pipe = WanPipeline.from_pretrained(info["repo"], vae=vae, transformer=transformer, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
    if hasattr(pipe.vae, "enable_tiling"):
        pipe.vae.enable_tiling()
    return pipe


def unload(pipe):
    del pipe
    gc.collect()
    if not DRY_RUN:
        import torch
        torch.cuda.empty_cache()


def generate_local(pipe, info, prompt, seed, path):
    width, height = info["size"][ASPECT]
    if DRY_RUN:
        return dry_clip(path, width, height, info["fps"], SECONDS)
    import torch
    from diffusers.utils import export_to_video
    frames = pipe(prompt=prompt, negative_prompt=NEGATIVE, width=width, height=height, num_frames=frame_count(info),
                  num_inference_steps=info["steps"], guidance_scale=info["guidance"],
                  generator=torch.Generator("cpu").manual_seed(seed)).frames[0]
    export_to_video(frames, str(path), fps=info["fps"])


def api_seconds(info):
    return min(info["durations"], key=lambda d: (d < SECONDS, abs(d - SECONDS))) if info["durations"] else SECONDS


def generate_api(info, prompt, path):
    """Never run live while building this notebook. Check fal's docs if a call fails."""
    global api_spent
    seconds = api_seconds(info)
    cost = seconds * info["price"]
    if api_spent + cost > MAX_API_SPEND_USD:
        raise RuntimeError(f"spend cap: {api_spent + cost:.2f} USD would pass {MAX_API_SPEND_USD:.2f} USD")
    if DRY_RUN:
        width, height = (1280, 720) if ASPECT == WIDE else (720, 1280)
        dry_clip(path, width, height, 24, seconds)
        api_spent += cost
        return cost
    import fal_client
    arguments = {"prompt": prompt, "aspect_ratio": ASPECT, "resolution": "1080p"}
    if info["family"] == "veo":
        arguments |= {"duration": f"{seconds}s", "generate_audio": False, "negative_prompt": NEGATIVE}
    else:
        arguments |= {"duration": seconds}
    api_spent += cost  # A vendor may bill once the job is accepted.
    result = fal_client.subscribe(info["endpoint"], arguments=arguments)
    urllib.request.urlretrieve(result["video"]["url"], path)
    return cost
'''),

("code", r'''# CELL 5: RUN. Har prompt x har model x har seed.
FIELDS = ["clip", "prompt_id", "model", "seed", "kind", "licence", "status", "render_seconds", "clip_seconds", "api_cost_usd", "peak_vram_gb", "note"]


def load_rows():
    return {r["clip"]: r for r in csv.DictReader(RESULTS_CSV.open(encoding="utf-8"))} if RESULTS_CSV.exists() else {}


rows = load_rows()


def save_rows():
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows.values())


def out_of_time():
    return (time.time() - START) / 60 > MAX_RUNTIME_MINUTES


def run_model(model, todo):
    """Make every clip for one model. Local models run this in a child process."""
    info = REGISTRY[model]
    pipe = None
    if info["kind"] == "local" and not DRY_RUN:
        print("Loading", model, "...", flush=True)
        pipe = load_local(info)
    for pid, seed in todo:
        if out_of_time():
            print("Time limit: baaki clips skip", flush=True)
            break
        name = f"{pid}__{model}__seed{seed}"
        path = CLIPS / f"{name}.mp4"
        row = dict(clip=name, prompt_id=pid, model=model, seed=seed, kind=info["kind"], licence=info["verdict"], status="ok",
                   api_cost_usd=0, note="")
        began = time.time()
        local = info["kind"] == "local" and not DRY_RUN
        if local:
            import torch
            torch.cuda.reset_peak_memory_stats()
        try:
            if info["kind"] == "api":
                row["api_cost_usd"] = generate_api(info, PROMPTS[pid], path)
            else:
                generate_local(pipe, info, PROMPTS[pid], seed, path)
        except Exception as error:
            row["status"] = "failed"
            row["note"] = f"{type(error).__name__}: {str(error)[:160]}"
            if local and "out of memory" in str(error).lower():
                row["status"] = "out_of_memory"
                torch.cuda.empty_cache()
        row["render_seconds"] = round(time.time() - began, 1)
        row["clip_seconds"] = api_seconds(info) if info["kind"] == "api" else round(frame_count(info) / info["fps"], 2)
        if local:
            row["peak_vram_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 1)
        rows[name] = row
        save_rows()
        print(f'{name}: {row["status"]} in {row["render_seconds"]} s {row["note"]}', flush=True)


def run_isolated(model, todo):
    """A child process gives RAM back when it ends, and its crash cannot kill the notebook."""
    global rows
    info = REGISTRY[model]
    worker = multiprocessing.get_context("fork").Process(target=run_model, args=(model, todo))
    worker.start()
    worker.join()
    rows = load_rows()
    if worker.exitcode != 0:
        status = "out_of_ram" if worker.exitcode in (-9, 137) else "failed"
        print(f"{model} worker stopped: {status}, exit code {worker.exitcode}. Baaki models chalte rahenge.")
        for pid, seed in todo:
            name = f"{pid}__{model}__seed{seed}"
            if name not in rows:
                rows[name] = dict(clip=name, prompt_id=pid, model=model, seed=seed, kind=info["kind"], licence=info["verdict"], status=status,
                                  render_seconds=0, clip_seconds=0, api_cost_usd=0, note=f"worker exit code {worker.exitcode}")
        save_rows()


jobs = [(model, pid, seed) for model in MODELS for pid in PROMPTS for seed in SEEDS]
print(f"{len(jobs)} clips banenge")
for model in MODELS:
    info = REGISTRY[model]
    todo = [(pid, seed) for m, pid, seed in jobs if m == model and rows.get(f"{pid}__{model}__seed{seed}", {}).get("status") != "ok"]
    if not todo:
        continue
    if info["kind"] == "api" and not FAL_KEY and not DRY_RUN:
        print(model, "skip: FAL_KEY secret nahi mila")
        continue
    if info["kind"] == "local" and not DRY_RUN:
        run_isolated(model, todo)
    else:
        run_model(model, todo)
print("API spend so far: $", round(api_spent, 2))
'''),

("code", r'''# CELL 6: QC. Sirf technical checks. Quality aap Cell 8 mein doge.
def ffprobe(path):
    result = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    return json.loads(result.stdout) if result.returncode == 0 else None


def filter_log(path, video_filter):
    return run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", video_filter, "-f", "null", "-"]).stderr


def check_clip(row):
    path = CLIPS / f'{row["clip"]}.mp4'
    if row["status"] != "ok" or not path.exists():
        return "no_clip", row["status"]
    info = ffprobe(path)
    if not info:
        return "fail", "unreadable file"
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        return "fail", "no video stream"
    notes = []
    duration = float(info["format"]["duration"])
    if abs(duration - float(row["clip_seconds"])) > 0.5:
        notes.append(f"duration {duration:.1f}s")
    if "black_start" in filter_log(path, "blackdetect=d=0.5:pix_th=0.10"):
        notes.append("black frames")
    if "freeze_start" in filter_log(path, "freezedetect=n=0.003:d=1.5"):
        notes.append("frozen frames")
    return ("fail" if notes else "pass"), f'{video["width"]}x{video["height"]} ' + ", ".join(notes)


qc = {name: check_clip(row) for name, row in rows.items()}
for name, (status, note) in qc.items():
    print(f"{name}: {status} | {note}")
'''),

("code", r'''# CELL 7: VIDEOS DEKHO
from IPython.display import HTML, Video, display

if SHOW_INLINE:
    for pid, text in PROMPTS.items():
        display(HTML(f"<h3>{pid}</h3><p>{html.escape(text)}</p>"))
        for name, row in rows.items():
            path = CLIPS / f"{name}.mp4"
            if row["prompt_id"] == pid and path.exists():
                display(HTML(f'<b>{row["model"]}</b>, seed {row["seed"]}, {row["render_seconds"]} s render, QC: {qc[name][0]}'))
                display(Video(str(path), embed=True, width=420))
'''),

("markdown", r'''## Rating do

Videos dekhkar neeche `RATINGS` bharo: `1` se `5`. Rating `ACCEPT_AT` ya upar ho to shot accepted mana jayega. Yeh hamara asli **accept rate** hai, jo poori cost decide karta hai. Rating dene ke baad Cell 8 dobara chalao.

Clip ka naam upar print hua hai, jaise `prompt_1__ltx_video__seed42`.
'''),

("code", r'''# CELL 8: RATING AUR COMPARISON
ACCEPT_AT = 4
RATINGS = {
    # "prompt_1__ltx_video__seed42": 4,
    # "prompt_1__wan21_480p__seed42": 3,
}

import pandas as pd

table = pd.DataFrame(rows.values())
if len(table):
    table["render_seconds"] = pd.to_numeric(table["render_seconds"], errors="coerce").fillna(0)
    table["clip_seconds"] = pd.to_numeric(table["clip_seconds"], errors="coerce").fillna(0)
    table["api_cost_usd"] = pd.to_numeric(table["api_cost_usd"], errors="coerce").fillna(0)
    # Rows reloaded from results.csv on a resumed run arrive as text.
    table["peak_vram_gb"] = pd.to_numeric(table.get("peak_vram_gb"), errors="coerce")
    table["qc"] = table["clip"].map(lambda c: qc.get(c, ("no_clip", ""))[0])
    table["rating"] = table["clip"].map(RATINGS)
    table["accepted"] = table["rating"] >= ACCEPT_AT
    table["cost_usd"] = table["api_cost_usd"] + (table["kind"] == "local") * table["render_seconds"] * GPU_USD_PER_HOUR / 3600

    summary = []
    for model, group in table.groupby("model", sort=False):
        made = group[group["status"] == "ok"]
        rated = group[group["rating"].notna()]
        accepted = rated[rated["accepted"]]
        seconds = made["clip_seconds"].sum() or 1
        kept = accepted["clip_seconds"].sum()
        summary.append({
            "model": model, "licence": group["licence"].iloc[0], "clips": len(group), "made": len(made),
            "qc_pass": int((group["qc"] == "pass").sum()), "avg_render_s": round(made["render_seconds"].mean() or 0, 1),
            "render_s_per_output_s": round(made["render_seconds"].sum() / seconds, 1),
            "usd_per_generated_s": round(group["cost_usd"].sum() / seconds, 4),
            "rated": len(rated), "accept_rate": round(len(accepted) / len(rated), 2) if len(rated) else None,
            "usd_per_accepted_s": round(group["cost_usd"].sum() / kept, 4) if kept else None,
            "peak_vram_gb": group["peak_vram_gb"].max(),
        })
    summary = pd.DataFrame(summary)
    summary.to_csv(ROOT / "summary.csv", index=False)
    table.to_csv(ROOT / "clips_rated.csv", index=False)
    display(summary)
    print("Local cost sirf reference hai: render time x", GPU_USD_PER_HOUR, "USD per hour. Kaggle par yeh free hai.")
    if not RATINGS:
        print("RATINGS khali hain, isliye accept rate abhi nahi nikla.")
save_zip()  # Saved before the reel, so a crash there cannot lose the clips.
'''),

("code", r'''# CELL 9: HYBRID REEL. 30 second, 1080x1920. AI clip nahi mila to animated image lagegi.
def best_clip(prompt_id):
    """Highest rated clip for this prompt that passed QC."""
    options = [n for n, r in rows.items() if r["prompt_id"] == prompt_id and qc.get(n, ("",))[0] == "pass"]
    return max(options, key=lambda n: RATINGS.get(n, 0), default=None)


def load_flux():
    """Images are optional. Any failure here must leave the reel running on the fallback."""
    try:
        import torch
        from diffusers import FluxPipeline
        from huggingface_hub import login
        login(HF_TOKEN)
        pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
        pipe.enable_model_cpu_offload()
        return pipe
    except Exception as error:
        print("FLUX load nahi hua, clip frames use honge:", type(error).__name__, str(error)[:200])
        print("Gated error ho to huggingface.co/black-forest-labs/FLUX.1-schnell par terms accept karo.")
        return None


def make_image(prompt, path, pipe):
    if pipe is not None:
        try:
            import torch
            image = pipe(prompt, guidance_scale=0.0, num_inference_steps=4, max_sequence_length=256, width=576, height=1024,
                         generator=torch.Generator("cpu").manual_seed(42)).images[0]
            image.save(path)
            return "flux"
        except Exception as error:
            print("FLUX image fail:", type(error).__name__, str(error)[:200])
    # The fallback must never fail: a frame from any clip on disk, or else a plain colour.
    clip = next(iter(sorted(CLIPS.glob("*.mp4"))), None)
    if clip is not None:
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", str(clip), "-frames:v", "1", str(path)])
        if path.exists():
            return "frame from clip"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x224455:s=768x1344", "-frames:v", "1", str(path)])
    return "plain colour"


def caption_filter(text, index):
    if not FONT:
        return ""
    note = REEL / f"caption_{index}.txt"
    note.write_text(text, encoding="utf-8")
    path = note.as_posix().replace(":", "\\:")
    return f",drawtext={font_arg()}:textfile='{path}':fontsize=64:fontcolor=white:borderw=4:bordercolor=black:x=(w-text_w)/2:y=h-360"


def scene_clip(scene, index, flux):
    output = REEL / f"scene_{index}.mp4"
    frames = scene["seconds"] * 24
    text = caption_filter(scene["text"], index)
    source = best_clip(scene["prompt"]) if scene["type"] == "ai" else None
    if source:
        command = ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(CLIPS / f"{source}.mp4"), "-t", str(scene["seconds"]),
                   "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=24,format=yuv420p{text}"]
        used = f"ai clip {source}"
    else:
        still = STILLS / f"scene_{index}.png"
        prompt = PROMPTS.get(scene["prompt"], scene["prompt"])
        origin = make_image(prompt, still, flux)
        zoom = f"zoompan=z='min(zoom+0.0007,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=24"
        command = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(still), "-vf",
                   f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,{zoom},format=yuv420p{text}", "-frames:v", str(frames)]
        used = ("fallback " if scene["type"] == "ai" else "") + f"animated image ({origin})"
    result = run(command + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(output)])
    if result.returncode:
        raise RuntimeError(result.stderr[-500:])
    return output, used


def narration(path, seconds):
    text = ". ".join(s["text"] for s in REEL_SCENES)
    if not DRY_RUN:
        try:
            done = run([sys.executable, "-m", "edge_tts", "--voice", VOICE, "--text", text, "--write-media", str(path)])
            if done.returncode == 0:
                return "edge-tts, test only"
        except Exception:
            pass
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={seconds}", "-c:a", "libmp3lame", str(path)])
    return "silent"


def make_reel():
    flux = load_flux() if HF_TOKEN and not DRY_RUN else None
    built = [scene_clip(scene, index, flux) for index, scene in enumerate(REEL_SCENES, 1)]
    if flux is not None:
        unload(flux)
    for index, (_, used) in enumerate(built, 1):
        print(f"Scene {index}: {used}")
    (REEL / "list.txt").write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p, _ in built), encoding="utf-8")
    total = sum(s["seconds"] for s in REEL_SCENES)
    voice = REEL / "voice.mp3"
    print("Voice:", narration(voice, total))
    final = ROOT / "hybrid_reel.mp4"
    result = run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(REEL / "list.txt"), "-i", str(voice),
                  "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-af", "apad", "-t", str(total), str(final)])
    if result.returncode:
        raise RuntimeError(result.stderr[-500:])
    info = ffprobe(final)
    print("Reel:", info["streams"][0]["width"], "x", info["streams"][0]["height"], round(float(info["format"]["duration"]), 1), "s")
    if SHOW_INLINE:
        display(Video(str(final), embed=True, width=320))


if MAKE_REEL:
    # A reel failure must never stop Cell 10, which saves everything already made.
    try:
        make_reel()
    except Exception as error:
        print("Reel nahi bani:", type(error).__name__, str(error)[:300])
'''),

("code", r'''# CELL 10: RESULTS DOWNLOAD
print("Download karo:", save_zip())
print("Total time:", round((time.time() - START) / 60, 1), "minutes | API spend: $", round(api_spent, 2))
'''),
]


def main():
    cells = []
    for kind, text in CELLS:
        source = text.strip("\n").splitlines(keepends=True)
        cell = {"cell_type": kind, "metadata": {}, "source": source}
        if kind == "code":
            cell |= {"execution_count": None, "outputs": []}
        cells.append(cell)
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                             "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT, len(cells), "cells")


if __name__ == "__main__":
    main()
