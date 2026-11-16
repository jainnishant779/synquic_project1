"""Shared cells for the two model-testing notebooks (open models, API models). Each builder adds its own config, registry and generation cells."""
import json
from pathlib import Path

NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"

SETUP_HEAD = r'''# CELL 2: SETUP
import csv, gc, html, json, math, multiprocessing, os, re, shutil, subprocess, sys, time, types, urllib.request
from pathlib import Path

DRY_RUN = os.environ.get("SYNQUIC_DRY_RUN") == "1"
ROOT = Path(os.environ.get("SYNQUIC_OUT", "/kaggle/working/synquic"))
STILLS, CLIPS = ROOT / "stills", ROOT / "clips"
for folder in (STILLS, CLIPS):
    folder.mkdir(parents=True, exist_ok=True)
RESULTS_CSV = ROOT / "results.csv"
START = time.time()
MODELS = [m for m in IMAGE_MODELS + VIDEO_MODELS if m]
SEEDS = list(SEEDS)


def secret(name):
    try:
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret(name)
    except Exception:
        return os.environ.get(name)


def pip(*packages):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *packages], check=True)


def run(command):
    return subprocess.run(command, capture_output=True, text=True)


def save_zip():
    archive = shutil.make_archive(str(ROOT.parent / "synquic_results"), "zip", ROOT)
    print("Results saved:", archive, round(Path(archive).stat().st_size / 1e6, 1), "MB")
    return archive


FONT = next((f for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arial.ttf") if Path(f).exists()), None)


def dry_image(path, size, label):
    """Dry run only: a labelled test pattern, so the flow can be tested with no GPU and no network."""
    result = run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=s={size}x{size}:r=1:d=1", "-frames:v", "1", str(path)])
    if result.returncode:
        raise RuntimeError(result.stderr[-400:])


def dry_clip(path, width, height, fps, seconds):
    result = run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=s={width}x{height}:r={fps}:d={seconds}",
                  "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "ultrafast", str(path)])
    if result.returncode:
        raise RuntimeError(result.stderr[-400:])
'''

RUN_CELL = r'''# CELL 5: RUN. Pehle stills (images), phir videos, taaki video stills se bane.
FIELDS = ["clip", "task", "prompt_id", "model", "seed", "kind", "licence", "status", "render_seconds", "clip_seconds", "api_cost_usd", "peak_vram_gb", "note"]


def job_name(task, pid, model, seed):
    return f"{'img' if task == 'image' else 'vid'}__{pid}__{model}__seed{seed}"


def out_path(name, task):
    return STILLS / f"{name}.png" if task == "image" else CLIPS / f"{name}.mp4"


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


def first_frame(pid):
    """The first frame for image-to-video: your own photo if given, else the still from STILL_SOURCE."""
    if pid in USER_PHOTOS and Path(USER_PHOTOS[pid]).exists():
        return Path(USER_PHOTOS[pid]), "your photo"
    if STILL_SOURCE:
        path = STILLS / f"img__{pid}__{STILL_SOURCE}__seed{SEEDS[0]}.png"
        if path.exists():
            return path, STILL_SOURCE
    return None, ""


def run_model(model, todo):
    """Make every item for one model. Local models run this in a child process."""
    info = REGISTRY[model]
    try:
        state = prepare(info)
    except Exception as error:
        # A load failure must leave its reason in results.csv, not just an exit code.
        note = f"load failed: {type(error).__name__}: {str(error)[:260]}"
        print(model, note, flush=True)
        for pid, seed in todo:
            name = job_name(info["task"], pid, model, seed)
            rows[name] = dict(clip=name, task=info["task"], prompt_id=pid, model=model, seed=seed, kind=info["kind"], licence=info["verdict"],
                              status="failed", render_seconds=0, clip_seconds=0, api_cost_usd=0, note=note)
        save_rows()
        return
    for pid, seed in todo:
        if out_of_time():
            print("Time limit: baaki items skip", flush=True)
            break
        name = job_name(info["task"], pid, model, seed)
        row = dict(clip=name, task=info["task"], prompt_id=pid, model=model, seed=seed, kind=info["kind"], licence=info["verdict"],
                   status="ok", api_cost_usd=0, clip_seconds=0, note="")
        began = time.time()
        reset_peak()
        oom = False
        try:
            made = generate(state, info, pid, seed, out_path(name, info["task"])) or {}
            row["api_cost_usd"], row["clip_seconds"], row["note"] = made.get("cost", 0), made.get("seconds", 0), made.get("note", "")
        except Exception as error:
            row["status"] = "failed"
            row["note"] = f"{type(error).__name__}: {str(error)[:220]}"
            if "out of memory" in str(error).lower():
                row["status"] = "out_of_memory"
                oom = True
        if oom:
            # Free after the except block: while it runs, the error still holds the tensors, so freeing inside it frees nothing.
            free_gpu()
        row["render_seconds"] = round(time.time() - began, 1)
        row["peak_vram_gb"] = peak_vram()
        rows[name] = row
        save_rows()
        print(f'{name}: {row["status"]} in {row["render_seconds"]} s {row["note"]}', flush=True)
    release(state)


def run_isolated(model, todo):
    """A child process gives RAM back when it ends, and its crash cannot kill the notebook."""
    global rows
    info = REGISTRY[model]
    worker = multiprocessing.get_context("fork").Process(target=run_model, args=(model, todo))
    worker.start()
    worker.join()
    after_model(info)
    rows = load_rows()
    if worker.exitcode != 0:
        status = "out_of_ram" if worker.exitcode in (-9, 137) else "failed"
        print(f"{model} worker stopped: {status}, exit code {worker.exitcode}. Baaki models chalte rahenge.")
        for pid, seed in todo:
            name = job_name(info["task"], pid, model, seed)
            if name not in rows:
                rows[name] = dict(clip=name, task=info["task"], prompt_id=pid, model=model, seed=seed, kind=info["kind"], licence=info["verdict"],
                                  status=status, render_seconds=0, clip_seconds=0, api_cost_usd=0, note=f"worker exit code {worker.exitcode}")
        save_rows()


def todo_for(model):
    info = REGISTRY[model]
    items = [(pid, seed) for pid in PROMPTS for seed in SEEDS]
    return [(p, s) for p, s in items if rows.get(job_name(info["task"], p, model, s), {}).get("status") != "ok"]


print(f"{len(MODELS)} models x {len(PROMPTS)} prompts x {len(SEEDS)} seeds")
for stage in ("image", "video"):
    for model in MODELS:
        info = REGISTRY[model]
        todo = todo_for(model) if info["task"] == stage else []
        if not todo:
            continue
        missing = missing_key(info)
        if missing and not DRY_RUN:
            print(model, "skip:", missing)
            continue
        if info["kind"] == "local" and not DRY_RUN:
            run_isolated(model, todo)
        else:
            run_model(model, todo)
print("API spend so far: $", round(api_spent, 2))
'''

QC_CELL = r'''# CELL 6: QC. Sirf technical checks. Asli quality aap Cell 8 mein rating se doge.
def ffprobe(path):
    result = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    return json.loads(result.stdout) if result.returncode == 0 else None


def filter_log(path, video_filter):
    return run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", video_filter, "-f", "null", "-"]).stderr


def check_item(row):
    path = out_path(row["clip"], row["task"])
    if row["status"] != "ok" or not path.exists():
        return "no_file", row["status"]
    if row["task"] == "image":
        from PIL import Image, ImageStat
        with Image.open(path) as image:
            grey = ImageStat.Stat(image.convert("L"))
            note = f"{image.width}x{image.height}"
        if grey.stddev[0] < 6:
            return "fail", note + " blank or flat image (black output can mean fp16 trouble)"
        return "pass", note
    info = ffprobe(path)
    if not info:
        return "fail", "unreadable file"
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        return "fail", "no video stream"
    notes = []
    duration = float(info["format"]["duration"])
    wanted = float(row["clip_seconds"] or 0)
    if wanted and abs(duration - wanted) > 0.7:
        notes.append(f"duration {duration:.1f}s, asked {wanted:.1f}s")
    if "black_start" in filter_log(path, "blackdetect=d=0.5:pix_th=0.10"):
        notes.append("black frames")
    if "freeze_start" in filter_log(path, "freezedetect=n=0.003:d=1.5"):
        notes.append("frozen frames")
    return ("fail" if notes else "pass"), f'{video["width"]}x{video["height"]} ' + ", ".join(notes)


qc = {name: check_item(row) for name, row in rows.items()}
for name, (status, note) in qc.items():
    print(f"{name}: {status} | {note}")
'''

VIEW_CELL = r'''# CELL 7: DEKHO. Pehle stills, phir videos.
from IPython.display import HTML, Image as ShowImage, Video, display

if SHOW_INLINE:
    for pid, text in PROMPTS.items():
        display(HTML(f"<h3>{pid}</h3><p>{html.escape(text['still'])}</p><p><i>motion: {html.escape(text['motion'])}</i></p>"))
        for name, row in rows.items():
            path = out_path(name, row["task"])
            if row["prompt_id"] != pid or not path.exists():
                continue
            display(HTML(f'<b>{row["model"]}</b> ({row["task"]}), seed {row["seed"]}, {row["render_seconds"]} s, QC: {qc[name][0]}'))
            display(ShowImage(filename=str(path), width=300) if row["task"] == "image" else Video(str(path), embed=True, width=380))
'''

RATE_MD = r'''## Rating do

Stills aur videos dekhkar neeche `RATINGS` bharo: `1` se `5`. Rating `ACCEPT_AT` ya upar ho to item accepted. Yeh hamara asli **accept rate** hai, jo poori cost decide karta hai. Rating dene ke baad Cell 8 dobara chalao.

Naam upar print hue hain, jaise `vid__kettle__wan22_5b_i2v__seed42`. Dhyan do: product text (jaise T-shirt par NORTHWIND, serum label) sahi padha ja raha hai ya nahi, yeh sabse zaroori check hai.
'''

RATE_CELL = r'''# CELL 8: RATING AUR COMPARISON
ACCEPT_AT = 4
RATINGS = {
    # "img__tshirt__flux2_klein_4b__seed42": 4,
    # "vid__kettle__wan22_5b_i2v__seed42": 3,
}

import pandas as pd

table = pd.DataFrame(rows.values())
if len(table):
    for column in ("render_seconds", "clip_seconds", "api_cost_usd"):
        table[column] = pd.to_numeric(table[column], errors="coerce").fillna(0)
    table["peak_vram_gb"] = pd.to_numeric(table.get("peak_vram_gb"), errors="coerce")
    table["qc"] = table["clip"].map(lambda c: qc.get(c, ("no_file", ""))[0])
    table["rating"] = table["clip"].map(RATINGS)
    table["accepted"] = table["rating"] >= ACCEPT_AT
    table["cost_usd"] = table["api_cost_usd"] + (table["kind"] == "local") * table["render_seconds"] * GPU_USD_PER_HOUR / 3600

    summary = []
    for (task, model), group in table.groupby(["task", "model"], sort=False):
        made = group[group["status"] == "ok"]
        rated = group[group["rating"].notna()]
        accepted = rated[rated["accepted"]]
        unit = made["clip_seconds"].sum() if task == "video" else len(made)
        kept = accepted["clip_seconds"].sum() if task == "video" else len(accepted)
        summary.append({
            "task": task, "model": model, "licence": group["licence"].iloc[0], "items": len(group), "made": len(made),
            "qc_pass": int((group["qc"] == "pass").sum()), "avg_render_s": round(made["render_seconds"].mean() or 0, 1),
            "usd_per_generated_unit": round(group["cost_usd"].sum() / unit, 4) if unit else None,
            "rated": len(rated), "accept_rate": round(len(accepted) / len(rated), 2) if len(rated) else None,
            "usd_per_accepted_unit": round(group["cost_usd"].sum() / kept, 4) if kept else None,
            "peak_vram_gb": group["peak_vram_gb"].max(),
        })
    summary = pd.DataFrame(summary)
    summary.to_csv(ROOT / "summary.csv", index=False)
    table.to_csv(ROOT / "items_rated.csv", index=False)
    display(summary)
    print("Unit: image ke liye 1 image, video ke liye 1 second. Local cost sirf reference hai: render time x", GPU_USD_PER_HOUR, "USD per hour. Kaggle par free hai.")
    if not RATINGS:
        print("RATINGS khali hain, isliye accept rate abhi nahi nikla.")
save_zip()
'''

FINISH_CELL = r'''# CELL 9: RESULTS DOWNLOAD
print("Download karo:", save_zip())
print("Total time:", round((time.time() - START) / 60, 1), "minutes | API spend: $", round(api_spent, 2))
'''


def write_notebook(name, cells):
    out = []
    for kind, text in cells:
        cell = {"cell_type": kind, "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}
        if kind == "code":
            cell |= {"execution_count": None, "outputs": []}
        out.append(cell)
    notebook = {"cells": out, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                           "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    NOTEBOOKS.mkdir(exist_ok=True)
    path = NOTEBOOKS / name
    path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", path, len(out), "cells")
