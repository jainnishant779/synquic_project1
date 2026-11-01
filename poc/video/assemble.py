"""Final assembly with ffmpeg: concatenate clips, add placeholder audio and a caption track."""
import subprocess
from pathlib import Path

from .schemas import Shot


def _timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def write_captions(shots: list[Shot], path: Path) -> Path:
    blocks, start = [], 0.0
    for index, shot in enumerate(shots, 1):
        end = start + shot.duration_seconds
        blocks.append(f"{index}\n{_timestamp(start)} --> {_timestamp(end)}\n{shot.narration}\n")
        start = end
    path.write_text("\n".join(blocks), encoding="utf-8")
    return path


def assemble(clips: list[Path], shots: list[Shot], output: Path) -> Path:
    work_dir = output.parent
    concat_list = work_dir / "concat.txt"
    concat_list.write_text(
        "".join(f"file '{Path(clip).resolve().as_posix()}'\n" for clip in clips), encoding="utf-8"
    )
    captions = write_captions(shots, work_dir / "captions.srt")
    total = sum(shot.duration_seconds for shot in shots)
    # Placeholder tone standing in for narration and music.
    audio = f"sine=frequency=220:sample_rate=48000:duration={total}"
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-f", "lavfi", "-i", audio, "-i", str(captions),
        "-map", "0:v", "-map", "1:a", "-map", "2:s",
        "-c:v", "copy", "-af", "volume=0.1", "-c:a", "aac", "-c:s", "mov_text", str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"assembly failed: {result.stderr[-800:]}")
    return output
