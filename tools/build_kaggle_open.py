"""Write notebooks/synquic_kaggle_1_open_models.ipynb: free open-weight image and video models on a Kaggle GPU."""
from kaggle_core import (FINISH_CELL, QC_CELL, RATE_CELL, RATE_MD, RUN_CELL, SETUP_HEAD, VIEW_CELL, write_notebook)

INTRO = r'''# Synquic Notebook 1: Free open-weight models (Kaggle GPU)

Yeh notebook **free open-weight models** test karta hai: pehle **product stills** (FLUX.2 klein, Z-Image, Sana), phir un stills ko **video mein animate** karta hai (Wan 2.2, Kandinsky 6). Yeh hamara asli use case hai: product photo se video.

**Kaise chalana hai**

1. Kaggle par: *Create > Import Notebook*, yeh file upload karo.
2. Right panel: **Accelerator: GPU T4 x2**, **Internet: On** (phone verification chahiye).
3. Cell 1 mein prompts aur models dekho. Apni asli product photo ho to `USER_PHOTOS` mein daalo (Kaggle dataset upload karke).
4. **Save Version > Save & Run All** chalao. Laptop band karke bhi chalega.
5. Khatam hone par Output tab se `synquic_results.zip` download karo. Phir videos dekhkar `RATINGS` bharo (Cell 8).

**Optional secret** (Add-ons > Secrets): `HF_TOKEN`, sirf gated models ke liye. Abhi ke default models gated nahi hain.

**Is notebook mein kya nahi hai, aur kyun**

| Model | Kyun nahi |
|---|---|
| Qwen-Image-Edit-2511, LTX-2.5 | GGUF aur ComfyUI chahiye, diffusers mein seedha nahi chalta. LTX-2.5 gated bhi hai aur $10M se upar revenue par paid licence |
| FLUX 3 Image Klein | 31 GB maangta hai, T4 par fit nahi hota |
| HunyuanVideo 1.5 | Licence EU, UK aur Korea ko exclude karta hai |
| FLUX.2 klein 9B, FLUX.1 dev | Non-commercial licence |
| CatVTON, IDM-VTON (try-on) | Sirf research licence |
| LTX-Video (purana) | Pehle test ho chuka hai: 3 mein se 3 clips ko 1 out of 5 |

**Dhyan rakho:** yeh sirf testing ke liye hai. Kandinsky 6 aur Wan 2.2 ke loader pehli baar chal rahe hain, to koi model fail ho sakta hai. Fail hua to `results.csv` mein wajah likhi hogi, baaki models chalte rahenge. Kisi model ki T4 par speed ka koi published number nahi mila, isliye yahi run uska pehla measurement hai.
'''

CONFIG = r'''# CELL 1: SIRF YAHAN BADLO
# Har prompt mein "still" (product photo ka description) aur "motion" (video mein kya hilna chahiye) hai.
PROMPTS = {
    "kettle": dict(still="A matte teal electric kettle on a kitchen counter, soft morning window light, clean commercial product photo",
                   motion="steam rises from the spout, slow push-in, photorealistic"),
    "tshirt": dict(still="Flat-lay of a white cotton T-shirt with a bold black printed graphic that reads NORTHWIND in block letters, studio product photo",
                   motion="a gentle breeze moves the fabric, slow camera tilt down"),
    "sneaker": dict(still="A white running sneaker with a neon green sole on wet city pavement at dusk, low angle, neon reflections, commercial photo",
                    motion="water ripples on the pavement, slow orbit around the shoe"),
    "serum": dict(still="A frosted glass skincare serum bottle with a clean label that reads GLOW 30ML on white marble, soft studio light",
                  motion="light slowly sweeps across the glass, subtle slow push-in"),
}
PROMPTS = {k: v for k, v in PROMPTS.items() if v["still"].strip()}

# Image models (stills). Options: flux2_klein_4b, z_image_turbo, sana_1600m
# Pehli run: klein 4B ne text sahi likha, Sana ne galat, Z-Image float16 mein black aaya (ab bfloat16 mein dobara test).
IMAGE_MODELS = ["flux2_klein_4b", "z_image_turbo"]
# Video models. wan22_5b_i2v, kandinsky6_lite animate a still. wan21_480p_t2v only reads text (baseline).
VIDEO_MODELS = ["wan22_5b_i2v", "kandinsky6_lite", "wan21_480p_t2v"]

STILL_SOURCE = "flux2_klein_4b"   # Video models is image ko pehla frame banate hain
USER_PHOTOS = {}                  # Asli photo se test: {"tshirt": "/kaggle/input/my-photos/tshirt.jpg"}

SEEDS = [42]                      # [42, 7] se har combination 2 baar chalega
ASPECT = "16:9"                   # "16:9" ya "9:16"
SECONDS = 3                       # Clip length. T4 par chhota rakho, 5 s bahut slow ho sakta hai
IMAGE_SIZE = 1024
NEGATIVE = "blurry, low quality, distorted, deformed, extra fingers, watermark, flicker, warped text"

MAX_RUNTIME_MINUTES = 480         # Itne time ke baad naye items band
GPU_USD_PER_HOUR = 0.89           # Sirf reference: RunPod RTX 4090. Kaggle free hai
SHOW_INLINE = True
'''

REGISTRY_CELL = r'''# CELL 3: MODEL REGISTRY
# verdict: Allowed = licence saaf, Counsel = lawyer chahiye (component licences abhi padhe nahi gaye).
REGISTRY = {
    "flux2_klein_4b": dict(task="image", kind="local", family="auto", repo="black-forest-labs/FLUX.2-klein-4B", verdict="Allowed", steps=4, guidance=1.0),
    # Z-Image gave all-black images in float16 on a T4 (first run), so it loads in bfloat16.
    "z_image_turbo":  dict(task="image", kind="local", family="auto", repo="Tongyi-MAI/Z-Image-Turbo", verdict="Allowed", steps=9, guidance=0.0, dtype="bf16"),
    "sana_1600m":     dict(task="image", kind="local", family="auto", repo="Efficient-Large-Model/Sana_1600M_1024px_diffusers", verdict="Allowed", steps=20, guidance=4.5),
    "wan22_5b_i2v":   dict(task="video", kind="local", family="wan_i2v", repo="Wan-AI/Wan2.2-TI2V-5B-Diffusers", verdict="Allowed", fps=24, steps=30, guidance=5.0,
                           needs_image=True, size={"16:9": (832, 480), "9:16": (480, 832)}),
    "kandinsky6_lite": dict(task="video", kind="local", family="auto_i2v", repo="kandinskylab/Kandinsky-6.0-Lite-distill-5s-Diffusers", verdict="Counsel", fps=24, steps=10,
                            guidance=1.0, needs_image=True, fixed_frames=121, size={"16:9": (864, 480), "9:16": (480, 864)}),
    "wan21_480p_t2v": dict(task="video", kind="local", family="wan_t2v", repo="Wan-AI/Wan2.1-T2V-1.3B-Diffusers", verdict="Allowed", fps=16, steps=30, guidance=5.0,
                           needs_image=False, size={"16:9": (832, 480), "9:16": (480, 832)}),
}
unknown = [m for m in MODELS if m not in REGISTRY]
if unknown:
    raise SystemExit(f"Galat model naam: {unknown}. Options: {list(REGISTRY)}")
api_spent = 0.0   # Is notebook mein koi paid API nahi


def frame_count(info):
    """Wan needs 4k+1 frames."""
    return round((SECONDS * info["fps"] - 1) / 4) * 4 + 1
'''

SETUP_LOCAL = r'''
HF_TOKEN = secret("HF_TOKEN")
if not DRY_RUN:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        subprocess.run("apt-get -qq update && apt-get -qq install -y ffmpeg", shell=True, check=True)
    # Newest models (FLUX.2 klein, Z-Image, Kandinsky 6) need the current diffusers from GitHub.
    pip("git+https://github.com/huggingface/diffusers", "transformers", "accelerate", "sentencepiece", "ftfy", "imageio", "imageio-ffmpeg", "pillow", "protobuf")
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    import torch
    # Read the GPU through nvidia-smi. Starting CUDA in this process would stop models running in child processes.
    query = subprocess.run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", shell=True, capture_output=True, text=True)
    GPUS = query.stdout.strip().splitlines() if query.returncode == 0 else []
    if not GPUS:
        raise SystemExit("GPU nahi mila. Right panel mein Accelerator: GPU T4 x2 chuno.")
    print("GPUs:", GPUS)
    # GPUs older than Ampere (such as T4) have no efficient bfloat16 attention, so use float16.
    OLD_GPU = any(name in GPUS[0] for name in ("T4", "P100", "K80"))
    DTYPE = torch.float16 if OLD_GPU else torch.bfloat16
    print("Model dtype:", DTYPE)
print("Prompts:", list(PROMPTS), "| Models:", MODELS, "| Dry run:", DRY_RUN)
'''

GENERATE_CELL = r'''# CELL 4: GENERATION (local, diffusers)
def reset_peak():
    if not DRY_RUN:
        import torch
        torch.cuda.reset_peak_memory_stats()


def peak_vram():
    if DRY_RUN:
        return None
    import torch
    return round(torch.cuda.max_memory_allocated() / 1e9, 1)


def free_gpu():
    gc.collect()
    if not DRY_RUN:
        import torch
        torch.cuda.empty_cache()


def missing_key(info):
    return None


def load_local(info):
    import torch
    from diffusers import DiffusionPipeline
    token = HF_TOKEN or None
    dtype = torch.bfloat16 if info.get("dtype") == "bf16" else DTYPE
    if info["family"] == "wan_i2v":
        from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
        vae = AutoencoderKLWan.from_pretrained(info["repo"], subfolder="vae", torch_dtype=torch.float32)
        pipe = WanImageToVideoPipeline.from_pretrained(info["repo"], vae=vae, torch_dtype=DTYPE)
    elif info["family"] == "wan_t2v":
        from diffusers import AutoencoderKLWan, WanPipeline, WanTransformer3DModel
        transformer = WanTransformer3DModel.from_pretrained(info["repo"], subfolder="transformer", torch_dtype=DTYPE)
        vae = AutoencoderKLWan.from_pretrained(info["repo"], subfolder="vae", torch_dtype=torch.float32)
        pipe = WanPipeline.from_pretrained(info["repo"], vae=vae, transformer=transformer, torch_dtype=DTYPE)
    else:
        # The model's own model_index.json picks the right pipeline class, so new releases load without a named class.
        pipe = DiffusionPipeline.from_pretrained(info["repo"], torch_dtype=dtype, token=token)
    pipe.enable_model_cpu_offload()
    for part in (getattr(pipe, "vae", None),):
        if part is not None and hasattr(part, "enable_tiling"):
            part.enable_tiling()
        if part is not None and hasattr(part, "enable_slicing"):
            part.enable_slicing()
    return pipe


def run_ladder(sizes, attempt, pipe=None):
    """Try the largest size first. On a CUDA out-of-memory error, free memory and try the next smaller one.

    Memory is freed after the except block, not inside it: inside, the error still holds the tensors, so the first
    Kaggle run kept 14.5 GB after one failure and every later item failed at once."""
    last = None
    for size in sizes:
        failed = False
        try:
            return attempt(size)
        except Exception as error:
            if "out of memory" not in str(error).lower():
                raise
            last = RuntimeError(str(error)[:300])
            failed = True
        if failed:
            if pipe is not None and hasattr(pipe, "maybe_free_model_hooks"):
                pipe.maybe_free_model_hooks()
            free_gpu()
    raise last


def clear_model_cache(info, cache_dir=None):
    """Delete this model's downloaded files. Kaggle's disk filled after a few 20 GB models and the next download hit a read-only file system."""
    if cache_dir is None:
        from huggingface_hub.constants import HF_HUB_CACHE
        cache_dir = HF_HUB_CACHE
    target = Path(cache_dir) / ("models--" + info["repo"].replace("/", "--"))
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
        return True
    return False


def after_model(info):
    if DRY_RUN:
        return
    cleared = clear_model_cache(info)
    free = shutil.disk_usage("/").free / 1e9
    print(f"{info['repo']}: cache cleared={cleared}, disk free {free:.0f} GB", flush=True)


def video_sizes(info, width, height, frames):
    """Wan 5B ran out of memory on a 14.5 GB T4 at 832x480 (first run), so it falls back to smaller sizes. Wan needs sides in 32s and 4k+1 frames."""
    sizes = [(width, height, frames)]
    if info["family"] == "wan_i2v":
        sizes += [(640, 352, min(frames, 49)), (512, 288, min(frames, 33))]
    return sizes


def prepare(info):
    if info["kind"] == "local" and not DRY_RUN:
        print("Loading", info["repo"], "...", flush=True)
        return load_local(info)
    return None


def release(pipe):
    del pipe
    free_gpu()


def generate(pipe, info, pid, seed, path):
    text = PROMPTS[pid]
    if info["task"] == "image":
        if DRY_RUN:
            dry_image(path, 256, "")
            return {"seconds": 0}
        import torch
        def attempt(size):
            out = pipe(prompt=text["still"], num_inference_steps=info["steps"], guidance_scale=info["guidance"], width=size, height=size,
                       generator=torch.Generator("cpu").manual_seed(seed))
            out.images[0].save(path)
            return {"seconds": 0, "note": f"{size}x{size}"}

        return run_ladder([IMAGE_SIZE, 768, 512], attempt, pipe)

    width, height = info["size"][ASPECT]
    frames = info.get("fixed_frames") or frame_count(info)
    frame, origin = first_frame(pid)
    if info["needs_image"] and frame is None:
        raise RuntimeError("koi still nahi mila: pehle image model chalao ya USER_PHOTOS do")
    prompt = text["motion"] if info["needs_image"] else f'{text["still"]}, {text["motion"]}'
    note = f"first frame: {origin}" if info["needs_image"] else "text only"
    if DRY_RUN:
        dry_clip(path, width, height, info["fps"], round(frames / info["fps"], 2))
        return {"seconds": round(frames / info["fps"], 2), "note": note}
    import torch
    from diffusers.utils import export_to_video, load_image
    source_image = load_image(str(frame)) if info["needs_image"] else None

    def attempt(size):
        w, h, n = size
        args = dict(prompt=prompt, negative_prompt=NEGATIVE, height=h, width=w, num_frames=n, num_inference_steps=info["steps"],
                    guidance_scale=info["guidance"], generator=torch.Generator("cpu").manual_seed(seed))
        if source_image is not None:
            args["image"] = source_image.resize((w, h))
        if info["family"] == "auto_i2v":
            args.pop("negative_prompt")   # Kandinsky's pipeline signature is unverified, so send only the basics.
        out = pipe(**args)
        export_to_video(out.frames[0] if hasattr(out, "frames") else out[0], str(path), fps=info["fps"])
        return {"seconds": round(n / info["fps"], 2), "note": f"{note}; {w}x{h}, {n} frames"}

    return run_ladder(video_sizes(info, width, height, frames), attempt, pipe)
'''


def main():
    cells = [
        ("markdown", INTRO),
        ("code", CONFIG),
        ("code", SETUP_HEAD + SETUP_LOCAL),
        ("code", REGISTRY_CELL),
        ("code", GENERATE_CELL),
        ("code", RUN_CELL),
        ("code", QC_CELL),
        ("code", VIEW_CELL),
        ("markdown", RATE_MD),
        ("code", RATE_CELL),
        ("code", FINISH_CELL),
    ]
    write_notebook("synquic_kaggle_1_open_models.ipynb", cells)


if __name__ == "__main__":
    main()
