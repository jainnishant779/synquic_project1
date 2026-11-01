"""Mock provider: renders test-pattern clips with ffmpeg. Nothing here is AI generated.

Every frame carries a red band reading MOCK - NOT AI GENERATED, so a mock clip can never be
mistaken for generated footage. Faults can be injected per shot and attempt to exercise QC.
"""
import itertools
import subprocess
from pathlib import Path

from .base import Adapter, AdapterError, Capabilities, ClipRequest, JobState

WATERMARK = "MOCK - NOT AI GENERATED"
BAND_HEIGHT = 28
FONT = "C\\:/Windows/Fonts/arial.ttf"
FAULTS = ("black", "frozen", "wrong_duration", "wrong_aspect")


def _watermark_filter() -> str:
    return (
        f"drawbox=x=0:y=0:w=iw:h={BAND_HEIGHT}:color=red:t=fill,"
        f"drawtext=fontfile='{FONT}':text='{WATERMARK}':fontcolor=white:fontsize=18:x=10:y=5"
    )


class MockAdapter(Adapter):
    name = "mock"
    real_generation = False

    def __init__(self, work_dir: Path, faults: dict[tuple[str, int], str] | None = None):
        """faults maps (shot_id, attempt) to a name from FAULTS."""
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.faults = faults or {}
        self._ids = itertools.count(1)
        self._jobs: dict[str, Path] = {}

    def capabilities(self) -> Capabilities:
        return Capabilities(max_clip_seconds=30, max_width=1920, max_height=1080, supports_references=True)

    def estimate_cost(self, request: ClipRequest) -> float:
        return 0.0

    def submit(self, request: ClipRequest) -> str:
        job_id = f"mock-{next(self._ids)}"
        output = self.work_dir / f"{job_id}.mp4"
        self._render(request, output)
        self._jobs[job_id] = output
        return job_id

    def poll(self, job_id: str) -> JobState:
        return JobState.SUCCEEDED if job_id in self._jobs else JobState.FAILED

    def fetch(self, job_id: str, destination: Path) -> Path:
        destination = Path(destination)
        destination.write_bytes(self._jobs[job_id].read_bytes())
        return destination

    def _render(self, request: ClipRequest, output: Path) -> None:
        fault = self.faults.get((request.shot_id, request.attempt))
        duration = request.duration_seconds / 2 if fault == "wrong_duration" else request.duration_seconds
        width = request.height if fault == "wrong_aspect" else request.width
        size = f"{width}x{request.height}"
        if fault == "black":
            source = f"color=c=black:s={size}:r={request.fps}:d={duration}"
        elif fault == "frozen":
            source = f"color=c=0x445566:s={size}:r={request.fps}:d={duration}"
        else:
            source = f"testsrc2=s={size}:r={request.fps}:d={duration}"
        command = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", source,
            "-vf", _watermark_filter(), "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-r", str(request.fps), str(output),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise AdapterError(f"ffmpeg failed for {request.shot_id}: {result.stderr[-500:]}")
