"""Automated QC. Technical checks use ffprobe and ffmpeg filters on the real file.

Semantic checks (does the clip show the right action, is it the same character) are not
implemented. They report not_evaluated, which is never counted as a pass.
"""
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .schemas import VideoSpec

PASS, FAIL, NOT_EVALUATED = "pass", "fail", "not_evaluated"
DURATION_TOLERANCE_SECONDS = 0.25
SEMANTIC_CHECKS = ("action_matches_prompt", "character_identity", "product_fidelity", "text_legibility")


@dataclass
class QCResult:
    checks: list[dict] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.checks.append({"name": name, "status": status, "detail": detail})

    @property
    def passed(self) -> bool:
        return not any(c["status"] == FAIL for c in self.checks)

    @property
    def failures(self) -> list[str]:
        return [c["name"] for c in self.checks if c["status"] == FAIL]

    def to_dict(self) -> dict:
        return asdict(self) | {"technical_pass": self.passed}


def probe(path: Path) -> dict:
    command = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _filter_log(path: Path, video_filter: str | None = None, audio_filter: str | None = None) -> str:
    command = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path)]
    if video_filter:
        command += ["-vf", video_filter]
    if audio_filter:
        command += ["-af", audio_filter]
    command += ["-f", "null", "-"]
    return subprocess.run(command, capture_output=True, text=True).stderr


def check_clip(path: Path, duration_seconds: float, spec: VideoSpec) -> QCResult:
    result = QCResult()
    info = probe(path)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        result.add("has_video_stream", FAIL)
        return result
    result.add("has_video_stream", PASS)

    actual = float(info["format"]["duration"])
    in_range = abs(actual - duration_seconds) <= DURATION_TOLERANCE_SECONDS
    result.add("duration", PASS if in_range else FAIL, f"{actual:.2f}s, expected {duration_seconds}s")

    size = (video["width"], video["height"])
    expected = (spec.width, spec.height)
    result.add("resolution", PASS if size == expected else FAIL, f"{size}, expected {expected}")

    # pic_th allows for burned-in overlays such as the mock watermark band.
    log = _filter_log(path, video_filter="blackdetect=d=0.5:pix_th=0.10:pic_th=0.90")
    result.add("black_frames", FAIL if "black_start" in log else PASS)

    log = _filter_log(path, video_filter="freezedetect=n=0.003:d=1.5")
    result.add("frozen_frames", FAIL if "freeze_start" in log else PASS)

    for name in SEMANTIC_CHECKS:
        result.add(name, NOT_EVALUATED, "semantic QC is not implemented in this POC")
    return result


def check_final(path: Path, duration_seconds: float, spec: VideoSpec) -> QCResult:
    result = QCResult()
    info = probe(path)
    kinds = {s["codec_type"] for s in info["streams"]}
    result.add("has_video_stream", PASS if "video" in kinds else FAIL)
    result.add("has_audio_stream", PASS if "audio" in kinds else FAIL)
    result.add("has_captions", PASS if "subtitle" in kinds else FAIL)

    actual = float(info["format"]["duration"])
    in_range = abs(actual - duration_seconds) <= 1.0
    result.add("duration", PASS if in_range else FAIL, f"{actual:.2f}s, expected {duration_seconds}s")

    log = _filter_log(path, audio_filter="silencedetect=n=-50dB:d=2")
    silent = re.findall(r"silence_duration: ([\d.]+)", log)
    result.add("silent_audio", FAIL if silent else PASS, f"{len(silent)} silent spans")
    return result
