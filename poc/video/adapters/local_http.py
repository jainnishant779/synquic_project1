"""Self-hosted route: a client for a GPU worker exposing POST /jobs, GET /jobs/{id}, GET /jobs/{id}/output.

Status: tested only against a fake server. It has never driven a real GPU worker.
"""
from pathlib import Path

import httpx

from .base import Adapter, AdapterError, Capabilities, ClipRequest, JobState


def wan_frame_count(seconds: float, fps: int) -> int:
    """Nearest frame count of the form 4n+1, which Wan's generate.py asks for (V-910)."""
    return round((seconds * fps - 1) / 4) * 4 + 1


class LocalAdapter(Adapter):
    name = "local"
    real_generation = True

    def __init__(self, base_url: str, gpu_usd_hr: float, render_sec_per_output_sec: float,
                 capabilities: Capabilities, client: httpx.Client | None = None):
        self.base_url = base_url.rstrip("/")
        self.gpu_usd_hr = gpu_usd_hr
        self.render_sec_per_output_sec = render_sec_per_output_sec
        self._capabilities = capabilities
        self._client = client or httpx.Client(timeout=60)

    def capabilities(self) -> Capabilities:
        return self._capabilities

    def estimate_cost(self, request: ClipRequest) -> float:
        render_seconds = request.duration_seconds * self.render_sec_per_output_sec
        return render_seconds * self.gpu_usd_hr / 3600

    def submit(self, request: ClipRequest) -> str:
        response = self._client.post(f"{self.base_url}/jobs", json={
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "seconds": request.duration_seconds,
            "frames": wan_frame_count(request.duration_seconds, request.fps),
            "width": request.width,
            "height": request.height,
            "fps": request.fps,
            "seed": request.seed,
        })
        response.raise_for_status()
        return response.json()["job_id"]

    def poll(self, job_id: str) -> JobState:
        response = self._client.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        try:
            return JobState(response.json()["state"])
        except ValueError as exc:
            raise AdapterError(f"unknown worker state for {job_id}") from exc

    def fetch(self, job_id: str, destination: Path) -> Path:
        response = self._client.get(f"{self.base_url}/jobs/{job_id}/output")
        response.raise_for_status()
        destination = Path(destination)
        destination.write_bytes(response.content)
        return destination
