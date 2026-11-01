"""Run every code cell of the Kaggle notebook in dry-run mode, with no GPU and no network.

Dry run replaces model output with test patterns, so this checks the flow only: looping, resume,
spend cap, QC, summary, fallback and reel assembly. It does not prove any model loads or runs.
"""
import json
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "synquic_video_benchmark.ipynb"


def cells():
    data = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return ["".join(c["source"]) for c in data["cells"] if c["cell_type"] == "code"]


def run_all(root, config, ratings=None):
    namespace = {"__name__": "__main__"}
    for index, source in enumerate(cells(), 1):
        if index == 2:
            exec(config, namespace)
        if ratings is not None:
            assert "RATINGS = {\n" in source or index != 8
            source = source.replace("RATINGS = {\n", f"RATINGS = {ratings!r}\nUNUSED = {{\n")
        exec(compile(source, f"cell_{index}", "exec"), namespace)
    return namespace


def main():
    root = Path(tempfile.mkdtemp(prefix="synquic_nb_")) / "synquic"
    os.environ.update(SYNQUIC_DRY_RUN="1", SYNQUIC_OUT=str(root), FAL_KEY="dry")
    os.environ.pop("HF_TOKEN", None)
    config = ('MODEL_3 = "veo_fast_fal"\nMODEL_4 = "kling4_fal"\nSHOW_INLINE = False\nMAX_API_SPEND_USD = 1.0\n')

    first = run_all(root, config)
    rows = first["rows"]
    expected = len(first["MODELS"]) * len(first["PROMPTS"])
    assert len(rows) == expected == 12, len(rows)
    local = [r for r in rows.values() if r["kind"] == "local"]
    assert all(r["status"] == "ok" for r in local)
    assert all(first["qc"][r["clip"]][0] == "pass" for r in local), first["qc"]

    # Three 6 s Veo clips at $0.10 fit under $1.00; Kling must then hit the spend cap.
    api = [r for r in rows.values() if r["kind"] == "api"]
    assert first["api_spent"] <= 1.0
    assert any("spend cap" in r["note"] for r in api), api
    assert (root / "summary.csv").exists() and (root / "hybrid_reel.mp4").exists()

    reel = first["ffprobe"](root / "hybrid_reel.mp4")
    video = next(s for s in reel["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (1080, 1920)
    assert abs(float(reel["format"]["duration"]) - 30) < 0.6, reel["format"]["duration"]
    assert any(s["codec_type"] == "audio" for s in reel["streams"])

    # A dead worker must leave its clips marked, and the notebook must carry on.
    assert (root.parent / "synquic_results.zip").exists()

    # Resume: nothing that succeeded runs again.
    done = {n for n, r in rows.items() if r["status"] == "ok"}
    second = run_all(root, config + "SEEDS = [42]\n")
    assert done <= {n for n, r in second["rows"].items() if r["status"] == "ok"}

    # Fallback: a failed AI scene becomes an animated image, and the reel still completes.
    for path in (root / "clips").glob("prompt_1__*"):
        path.unlink()
    third = run_all(root, config + 'MODEL_1 = ""\nMODEL_2 = ""\nMODEL_3 = ""\nMODEL_4 = "wan21_480p"\nPROMPT_1 = ""\n')
    assert third["best_clip"]("prompt_1") is None
    assert (root / "hybrid_reel.mp4").exists()

    # Ratings produce accept rate and cost per accepted second.
    names = [n for n in first["rows"] if "wan21" in n]
    ratings = {names[0]: 5, names[1]: 4, names[2]: 2}
    # Dry-run clips render in a fraction of a second, so a high rate keeps the cost above rounding.
    fourth = run_all(root, config + "GPU_USD_PER_HOUR = 36000.0\n", ratings)
    wan = fourth["summary"].set_index("model").loc["wan21_480p"]
    assert wan["rated"] == 3 and wan["accept_rate"] == 0.67, wan
    assert wan["usd_per_accepted_s"] > wan["usd_per_generated_s"], wan

    # A gated or broken FLUX download must fall back, never stop the run (first Kaggle run died here).
    sys.modules["diffusers"] = types.ModuleType("diffusers")
    fourth["HF_TOKEN"] = "dry"
    assert fourth["load_flux"]() is None
    del sys.modules["diffusers"]

    # The notebook must pick float16 below sm80 and load Wan's transformer in that dtype.
    source = "".join(cells())
    assert '("T4", "P100", "K80")' in source
    assert "torch.cuda" not in source.split("# CELL 3")[0], "cell 2 must not touch CUDA before models fork"
    assert 'get_context("fork")' in source
    # Paid models must run with no GPU, and must not start CUDA in the notebook process.
    assert "        if local:\n            import torch\n            torch.cuda.reset_peak_memory_stats()" in source
    assert 'subfolder="transformer", torch_dtype=DTYPE' in source
    assert "from_pretrained(info[\"repo\"], torch_dtype=DTYPE)" in source

    shutil.rmtree(root.parent, ignore_errors=True)
    print("dry run passed: 12 jobs, spend cap, QC, summary, resume, fallback, 1080x1920 reel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
