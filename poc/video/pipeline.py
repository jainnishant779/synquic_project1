"""Run the whole flow: brief, storyboard, clips with QC and bounded regeneration, final video."""
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..common.labels import MOCK
from ..common.manifest import sha256_file, sha256_text, write_json
from .adapters.base import Adapter, AdapterError, ClipRequest, JobState
from .assemble import assemble
from .credits import charge, load_rate_card
from .planner import MASTER_PROMPT, build_storyboard
from .qc import check_clip, check_final
from .schemas import Brief, Shot

MAX_ATTEMPTS = 3
POLL_SECONDS = 2
POLL_LIMIT = 300


@dataclass
class ShotOutcome:
    shot_id: str
    path: Path | None = None
    cached: bool = False
    attempts: list[dict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.path is not None


def _wait(adapter: Adapter, job_id: str) -> JobState:
    for _ in range(POLL_LIMIT):
        state = adapter.poll(job_id)
        if state in (JobState.SUCCEEDED, JobState.FAILED):
            return state
        time.sleep(POLL_SECONDS)
    return JobState.FAILED


def _cache_key(adapter: Adapter, shot: Shot, brief: Brief) -> str:
    return sha256_text("|".join([adapter.name, shot.prompt, shot.negative_prompt,
                                 str(shot.duration_seconds), brief.spec.model_dump_json()]))


def generate_shot(adapter: Adapter, shot: Shot, brief: Brief, run_dir: Path, cache_dir: Path,
                  max_attempts: int = MAX_ATTEMPTS, base_seed: int = 1000) -> ShotOutcome:
    outcome = ShotOutcome(shot.id)
    cached = cache_dir / f"{_cache_key(adapter, shot, brief)}.mp4"
    if cached.exists():
        return ShotOutcome(shot.id, path=cached, cached=True)

    spec = brief.spec
    for attempt in range(1, max_attempts + 1):
        request = ClipRequest(
            shot_id=shot.id, prompt=shot.prompt, negative_prompt=shot.negative_prompt,
            duration_seconds=shot.duration_seconds, width=spec.width, height=spec.height, fps=spec.fps,
            seed=base_seed + shot.order * 100 + attempt, attempt=attempt,
            reference_images=tuple(shot.reference_images),
        )
        record = {"attempt": attempt, "seed": request.seed, "estimated_cost_usd": adapter.estimate_cost(request)}
        outcome.attempts.append(record)
        job_id = adapter.submit(request)
        if _wait(adapter, job_id) is not JobState.SUCCEEDED:
            record["provider_state"] = "failed"
            continue
        clip = run_dir / "clips" / f"{shot.id}_a{attempt}.mp4"
        adapter.fetch(job_id, clip)
        qc = check_clip(clip, shot.duration_seconds, spec)
        record["qc"] = qc.to_dict()
        if qc.passed:
            shutil.copyfile(clip, cached)
            outcome.path = cached
            break
    return outcome


def run(brief: Brief, adapter: Adapter, run_dir: Path, cache_dir: Path | None = None,
        max_attempts: int = MAX_ATTEMPTS) -> dict:
    run_dir = Path(run_dir)
    cache_dir = Path(cache_dir) if cache_dir else run_dir / "cache"
    (run_dir / "clips").mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    storyboard = build_storyboard(brief)
    write_json(run_dir / "storyboard.json", storyboard.model_dump())

    outcomes = [generate_shot(adapter, shot, brief, run_dir, cache_dir, max_attempts) for shot in storyboard.shots]
    failed = [o.shot_id for o in outcomes if not o.passed]

    manifest = {
        "title": brief.title,
        "provider": adapter.name,
        "real_generation": adapter.real_generation,
        "labels": [] if adapter.real_generation else [MOCK],
        "master_prompt_sha256": sha256_file(MASTER_PROMPT),
        "duration_seconds": brief.duration_seconds,
        "shots": [
            {
                "id": o.shot_id,
                "prompt_sha256": sha256_text(shot.prompt),
                "cached": o.cached,
                "attempts": o.attempts,
                "passed": o.passed,
            }
            for o, shot in zip(outcomes, storyboard.shots)
        ],
        "failed_shots": failed,
        "total_attempts": sum(len(o.attempts) for o in outcomes),
        "estimated_cost_usd": sum(a["estimated_cost_usd"] for o in outcomes for a in o.attempts),
        "semantic_qc": "not_evaluated",
    }

    if failed:
        manifest["status"] = "failed_qc"
        write_json(run_dir / "manifest.json", manifest)
        return manifest

    final = assemble([o.path for o in outcomes], storyboard.shots, run_dir / "final.mp4")
    final_qc = check_final(final, brief.duration_seconds, brief.spec)
    manifest["final_qc"] = final_qc.to_dict()
    manifest["final_video"] = str(final)
    manifest["final_sha256"] = sha256_file(final)
    manifest["status"] = "complete" if final_qc.passed else "failed_final_qc"
    manifest["credits"] = charge(brief.duration_seconds, load_rate_card())
    write_json(run_dir / "manifest.json", manifest)
    return manifest


__all__ = ["run", "generate_shot", "AdapterError"]
