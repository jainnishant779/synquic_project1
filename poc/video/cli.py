"""Video demo CLI. Default route is the mock provider: no keys, no spend, no AI footage.

python -m poc.video.cli --brief poc/video/sample_brief.json --seconds 30
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from ..common.labels import MOCK
from .adapters.mock import MockAdapter
from .pipeline import run
from .router import Requirements, load_catalog, route
from .schemas import Brief

ROOT = Path(__file__).resolve().parents[1]


def parse_faults(items: list[str]) -> dict[tuple[str, int], str]:
    """Parse shot:attempt:fault, for example sc01_sh02:1:black."""
    faults = {}
    for item in items:
        shot_id, attempt, fault = item.split(":")
        faults[(shot_id, int(attempt))] = fault
    return faults


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", type=Path, default=ROOT / "video" / "sample_brief.json")
    parser.add_argument("--seconds", type=int, help="override the brief's duration")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "video")
    parser.add_argument("--fault", action="append", default=[], help="shot:attempt:fault, repeatable")
    parser.add_argument("--fresh", action="store_true", help="clear the run folder, so nothing comes from cache")
    parser.add_argument("--dialect", default="generic", help="prompt dialect from poc/prompts/dialects.json")
    args = parser.parse_args()
    if args.fresh:
        shutil.rmtree(args.run_dir, ignore_errors=True)

    brief = Brief.model_validate_json(args.brief.read_text(encoding="utf-8"))
    if args.seconds:
        brief.duration_seconds = args.seconds

    needs = Requirements(brief.shot_seconds, brief.spec.width, brief.spec.height,
                         needs_references=any(c.reference_images for c in brief.characters))
    # Dry run over the real catalog, to show the filters. Nothing below calls a paid route.
    catalog = load_catalog()
    names = {e["name"] for e in catalog if e["name"] != "mock"}
    choice, reasons = route([e for e in catalog if e["name"] != "mock"], needs, available=names)
    print(f"Dry run, no call made: would route to {choice['name']} ({choice['licence_verdict']})")
    print("Rejected:", json.dumps(reasons, indent=2))
    # Only the mock route runs without keys. Paid routes are not wired into this CLI.
    entry, _ = route(catalog, needs, available={"mock"})
    print(f"Running on: {entry['name']}")
    print(f"{MOCK} Clips are ffmpeg test patterns with a burned-in watermark. They are not AI generated.")

    manifest = run(brief, MockAdapter(args.run_dir / "jobs", parse_faults(args.fault)), args.run_dir,
                   dialect=args.dialect)
    print(json.dumps({k: manifest.get(k) for k in (
        "status", "provider", "real_generation", "duration_seconds", "total_attempts",
        "failed_shots", "semantic_qc", "credits", "final_video")}, indent=2))
    return 0 if manifest["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
