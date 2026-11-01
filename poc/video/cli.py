"""Video demo CLI. Default route is the mock provider: no keys, no spend, no AI footage.

python -m poc.video.cli --brief poc/video/sample_brief.json --seconds 30
"""
import argparse
import json
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
    args = parser.parse_args()

    brief = Brief.model_validate_json(args.brief.read_text(encoding="utf-8"))
    if args.seconds:
        brief.duration_seconds = args.seconds

    needs = Requirements(brief.shot_seconds, brief.spec.width, brief.spec.height,
                         needs_references=any(c.reference_images for c in brief.characters))
    # Only the mock route is available without keys; paid routes need an explicit key and spend cap.
    entry, rejected = route(load_catalog(), needs, available={"mock"})
    print(f"Route: {entry['name']}  rejected: {rejected}")
    print(f"{MOCK} Clips are ffmpeg test patterns with a burned-in watermark. They are not AI generated.")

    manifest = run(brief, MockAdapter(args.run_dir / "jobs", parse_faults(args.fault)), args.run_dir)
    print(json.dumps({k: manifest.get(k) for k in (
        "status", "provider", "real_generation", "duration_seconds", "total_attempts",
        "failed_shots", "semantic_qc", "credits", "final_video")}, indent=2))
    return 0 if manifest["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
