"""Dry-run both model-testing notebooks with no GPU and no network.

Dry run swaps model output for test patterns and fal_client for a stand-in, so this checks the flow only: looping, first-frame
hand-off, resume, spend cap, field-error retry, QC, rating summary. It does not prove any model loads, and no endpoint was called.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"


def cells(name):
    data = json.loads((NOTEBOOKS / name).read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in data["cells"] if c["cell_type"] == "code"]


def run_all(name, config, ratings=None, patch=None):
    """patch maps a cell number to code run just before that cell."""
    namespace = {"__name__": "__main__"}
    for index, source in enumerate(cells(name), 1):
        if index == 2:
            exec(config, namespace)
        if patch and index in patch:
            exec(patch[index], namespace)
        if ratings is not None and index == 8:
            assert "RATINGS = {\n" in source
            source = source.replace("RATINGS = {\n", f"RATINGS = {ratings!r}\nUNUSED = {{\n")
        exec(compile(source, f"{name}_cell_{index}", "exec"), namespace)
    return namespace


def fresh(tag):
    root = Path(tempfile.mkdtemp(prefix=f"synquic_{tag}_")) / "synquic"
    os.environ["SYNQUIC_OUT"] = str(root)
    return root


def test_open():
    name = "synquic_kaggle_1_open_models.ipynb"
    os.environ.update(SYNQUIC_DRY_RUN="1")
    os.environ.pop("SYNQUIC_FAKE_422", None)
    root = fresh("open")
    config = "SHOW_INLINE = False\n"

    first = run_all(name, config)
    rows = first["rows"]
    assert len(rows) == (2 + 3) * 4 == 20, len(rows)
    assert all(r["status"] == "ok" for r in rows.values()), [r for r in rows.values() if r["status"] != "ok"]
    assert all(first["qc"][n][0] == "pass" for n in rows), first["qc"]
    video = [r for r in rows.values() if r["model"] == "wan22_5b_i2v"]
    assert all("flux2_klein_4b" in r["note"] for r in video), video
    assert [r["note"] for r in rows.values() if r["model"] == "wan21_480p_t2v"][0] == "text only"
    assert (root / "summary.csv").exists() and (root.parent / "synquic_results.zip").exists()

    # Resume: nothing that succeeded runs again.
    before = {n: float(r["render_seconds"]) for n, r in rows.items()}
    second = run_all(name, config)
    assert {n: float(r["render_seconds"]) for n, r in second["rows"].items()} == before

    # No still available: image-to-video fails with a clear note, text-only video still works.
    shutil.rmtree(root)
    third = run_all(name, config + 'IMAGE_MODELS = []\n')
    by_model = {r["model"]: r for r in third["rows"].values() if r["prompt_id"] == "kettle"}
    assert by_model["wan22_5b_i2v"]["status"] == "failed" and "koi still" in by_model["wan22_5b_i2v"]["note"], by_model
    assert by_model["wan21_480p_t2v"]["status"] == "ok"

    # Your own photo is used as the first frame.
    shutil.rmtree(root)
    photo = root.parent / "mine.png"
    photo.parent.mkdir(parents=True, exist_ok=True)
    fourth_cfg = config + f'IMAGE_MODELS = []\nUSER_PHOTOS = {{"kettle": {str(photo)!r}}}\n'
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=256x256:d=1", "-frames:v", "1", str(photo)], check=True)
    fourth = run_all(name, fourth_cfg)
    assert fourth["rows"]["vid__kettle__wan22_5b_i2v__seed42"]["note"] == "first frame: your photo", fourth["rows"]["vid__kettle__wan22_5b_i2v__seed42"]

    # Ratings give accept rate and cost per accepted unit.
    shutil.rmtree(root)
    ratings = {"img__kettle__flux2_klein_4b__seed42": 5, "img__tshirt__flux2_klein_4b__seed42": 2, "vid__kettle__wan22_5b_i2v__seed42": 4}
    fifth = run_all(name, config + "GPU_USD_PER_HOUR = 36000.0\n", ratings)
    table = fifth["summary"].set_index("model")
    assert table.loc["flux2_klein_4b", "rated"] == 2 and table.loc["flux2_klein_4b", "accept_rate"] == 0.5
    assert table.loc["wan22_5b_i2v", "accept_rate"] == 1.0 and table.loc["wan22_5b_i2v", "usd_per_accepted_unit"] > 0

    # A model that fails to load leaves its reason in results.csv (the first Kaggle run lost it: "worker exit code 1").
    shutil.rmtree(root)
    broken = run_all(name, config, patch={5: 'def prepare(info):\n    if info["repo"].startswith("kandinskylab"):\n        raise ImportError("No module named kandinsky_stub")\n    return None\n'})
    row = broken["rows"]["vid__kettle__kandinsky6_lite__seed42"]
    assert row["status"] == "failed" and "load failed: ImportError: No module named kandinsky_stub" in row["note"], row
    assert broken["rows"]["vid__kettle__wan22_5b_i2v__seed42"]["status"] == "ok"

    # Out-of-memory ladder: smaller size after each CUDA out-of-memory error, other errors pass straight through.
    ns = first
    tried = []

    def attempt(size):
        tried.append(size)
        if len(tried) < 3:
            raise RuntimeError("CUDA out of memory. Tried to allocate 108.00 MiB")
        return {"ok": size}

    sizes = ns["video_sizes"](ns["REGISTRY"]["wan22_5b_i2v"], 832, 480, 73)
    assert sizes == [(832, 480, 73), (640, 352, 49), (512, 288, 33)], sizes
    assert ns["run_ladder"](sizes, attempt) == {"ok": (512, 288, 33)} and len(tried) == 3
    assert ns["video_sizes"](ns["REGISTRY"]["kandinsky6_lite"], 864, 480, 121) == [(864, 480, 121)]
    try:
        ns["run_ladder"](sizes, lambda size: (_ for _ in ()).throw(ValueError("bad argument")))
        raise SystemExit("a non-memory error must not be swallowed")
    except ValueError:
        pass
    assert ns["REGISTRY"]["z_image_turbo"]["dtype"] == "bf16"

    # Memory is freed after each out-of-memory error, and the pipeline's offload hooks are released too.
    freed, hooks = [], []
    ns["free_gpu"] = lambda: freed.append(1)

    class Pipe:
        def maybe_free_model_hooks(self):
            hooks.append(1)

    calls = []

    def twice(size):
        calls.append(size)
        if len(calls) < 3:
            raise RuntimeError("CUDA out of memory")
        return "done"

    assert ns["run_ladder"]([1, 2, 3], twice, Pipe()) == "done" and len(freed) == 2 and len(hooks) == 2

    # A model's cache is deleted after use, and other models' files stay.
    cache = root.parent / "hfcache"
    (cache / "models--Wan-AI--Wan2.2-TI2V-5B-Diffusers" / "blobs").mkdir(parents=True)
    (cache / "models--other--keep").mkdir()
    assert ns["clear_model_cache"](ns["REGISTRY"]["wan22_5b_i2v"], cache) is True
    assert not (cache / "models--Wan-AI--Wan2.2-TI2V-5B-Diffusers").exists() and (cache / "models--other--keep").exists()
    assert ns["clear_model_cache"](ns["REGISTRY"]["wan22_5b_i2v"], cache) is False

    source = "".join(cells(name))
    assert "torch.cuda" not in cells(name)[1], "cell 2 must not start CUDA before models fork"
    assert 'get_context("fork")' in source and '("T4", "P100", "K80")' in source and "DiffusionPipeline.from_pretrained" in source
    shutil.rmtree(root.parent, ignore_errors=True)
    print("open-model notebook: 20 jobs, first-frame hand-off, resume, fallback, own photo, ratings, load-error note, memory ladder: ok")


def test_api():
    name = "synquic_kaggle_2_api_models.ipynb"
    os.environ.update(SYNQUIC_DRY_RUN="1")
    os.environ.pop("SYNQUIC_FAKE_422", None)
    root = fresh("api")
    config = "SHOW_INLINE = False\n"

    # Smoke test: one prompt, shortest clips, small cap.
    smoke = run_all(name, config)
    rows = smoke["rows"]
    assert len(rows) == 4 + 8 and set(r["prompt_id"] for r in rows.values()) == {"kettle"}, len(rows)
    assert all(r["status"] == "ok" for r in rows.values()), [r for r in rows.values() if r["status"] != "ok"]
    assert smoke["api_spent"] <= 5.0 and abs(smoke["api_spent"] - sum(float(r["api_cost_usd"]) for r in rows.values())) < 1e-6
    notes = {r["model"]: r["note"] for r in rows.values() if r["task"] == "video"}
    assert notes["wan3"].startswith("i2v from nano_banana_21") and notes["grok_lite_xai"].startswith("i2v from"), notes
    assert all(smoke["qc"][n][0] == "pass" for n in rows), smoke["qc"]
    assert (root / "raw_responses.jsonl").exists()

    # Duration and type rules found in the vendor docs.
    reg = smoke["REGISTRY"]
    assert reg["seedance25"]["duration"](5) == "5" and reg["veo31"]["duration"](6) == "6s" and reg["minimax_h3"]["duration"](5) == 5.0
    full = run_all(name, config + "SMOKE_TEST = False\nSECONDS = 5\nMAX_API_SPEND_USD = 100.0\nVIDEO_MODELS = ['veo31']\nIMAGE_MODELS = []\nUSER_PHOTOS = {}\n")
    assert full["pick_seconds"](full["REGISTRY"]["veo31"]) == 6
    assert full["pick_seconds"](full["REGISTRY"]["kling4"]) == 5

    # Spend cap: the call that would pass the cap is refused, and spend never passes it.
    shutil.rmtree(root)
    capped = run_all(name, config + "SMOKE_TEST = False\nSECONDS = 5\nMAX_API_SPEND_USD = 3.0\nIMAGE_MODELS = ['recraft_v41']\nVIDEO_MODELS = ['kling4', 'heygen_video1']\n"
                     "PROMPTS = {k: PROMPTS[k] for k in list(PROMPTS)[:4]}\n")
    assert capped["api_spent"] <= 3.0, capped["api_spent"]
    assert any("spend cap" in r["note"] for r in capped["rows"].values()), [r["note"] for r in capped["rows"].values()]

    # A field the vendor rejects: retry with essentials only, and count the worst-case price.
    shutil.rmtree(root)
    os.environ["SYNQUIC_FAKE_422"] = "1"
    retry = run_all(name, config + "VIDEO_MODELS = ['wan3']\nIMAGE_MODELS = ['nano_banana_21']\n")
    wan = retry["rows"]["vid__kettle__wan3__seed42"]
    assert wan["status"] == "ok" and "retried with minimal fields" in wan["note"], wan
    assert abs(float(wan["api_cost_usd"]) - 0.20 * 2) < 1e-9, wan   # price_max x min seconds (2 s)
    assert abs(retry["api_spent"] - sum(float(r["api_cost_usd"]) for r in retry["rows"].values())) < 1e-9
    os.environ.pop("SYNQUIC_FAKE_422")

    # URL search and key checks.
    ns = smoke
    assert ns["find_url"]({"video": {"url": "https://x/y.mp4?sig=1"}, "other": [{"url": "https://x/z.png"}]}, (".mp4",)) == "https://x/y.mp4?sig=1"
    assert ns["looks_like_validation"](ValueError("422 resolution must be one of")) and not ns["looks_like_validation"](ValueError("401 Unauthorized"))
    ns["FAL_KEY"], ns["XAI_API_KEY"] = None, None
    assert "FAL_KEY" in ns["missing_key"](ns["REGISTRY"]["wan3"]) and "XAI" in ns["missing_key"](ns["REGISTRY"]["grok_lite_xai"])

    # Ratings.
    shutil.rmtree(root)
    ratings = {"vid__kettle__kling4__seed42": 5, "vid__kettle__wan3__seed42": 2}
    rated = run_all(name, config, ratings)
    table = rated["summary"].set_index("model")
    assert table.loc["kling4", "accept_rate"] == 1.0 and table.loc["wan3", "accept_rate"] == 0.0, table

    source = "".join(cells(name))
    assert "torch" not in source, "the API notebook must not need a GPU or torch"
    shutil.rmtree(root.parent, ignore_errors=True)
    print("api notebook: smoke run, duration types, spend cap, field-error retry, key check, ratings: ok")


def main():
    import build_kaggle_api
    import build_kaggle_open
    build_kaggle_open.main()
    build_kaggle_api.main()
    test_open()
    test_api()
    return 0


if __name__ == "__main__":
    sys.exit(main())
