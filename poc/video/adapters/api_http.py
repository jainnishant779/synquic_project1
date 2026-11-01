"""Paid API route. Refuses to run without a key and always enforces a spend cap.

Status: exercised only against a fake transport in the tests. It has never called a live
provider, so the payload mapping must be confirmed against the provider's docs before first use.
"""
import itertools
from dataclasses import dataclass
from pathlib import Path

import httpx

from .base import Adapter, AdapterError, Capabilities, ClipRequest, JobState, SpendCapExceeded


@dataclass(frozen=True)
class ApiProviderConfig:
    name: str
    submit_url: str
    status_url: str  # contains {job_id}
    price_per_second_usd: float
    capabilities: Capabilities
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer "


class ApiAdapter(Adapter):
    real_generation = True

    def __init__(self, config: ApiProviderConfig, api_key: str | None, max_spend_usd: float,
                 client: httpx.Client | None = None):
        if not api_key:
            raise AdapterError(f"{config.name}: no API key set, refusing to start")
        if max_spend_usd <= 0:
            raise AdapterError(f"{config.name}: a positive --max-spend is required")
        self.config = config
        self.name = config.name
        self.max_spend_usd = max_spend_usd
        self.spent_usd = 0.0
        self._ids = itertools.count(1)
        self._client = client or httpx.Client(timeout=60)
        self._headers = {config.auth_header: f"{config.auth_prefix}{api_key}"}

    def capabilities(self) -> Capabilities:
        return self.config.capabilities

    def estimate_cost(self, request: ClipRequest) -> float:
        return request.duration_seconds * self.config.price_per_second_usd

    def submit(self, request: ClipRequest) -> str:
        cost = self.estimate_cost(request)
        if self.spent_usd + cost > self.max_spend_usd:
            raise SpendCapExceeded(
                f"{self.name}: {self.spent_usd + cost:.2f} USD would exceed the {self.max_spend_usd:.2f} USD cap"
            )
        payload = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "duration": request.duration_seconds,
            "width": request.width,
            "height": request.height,
            "fps": request.fps,
            "seed": request.seed,
            "reference_images": list(request.reference_images),
        }
        response = self._client.post(self.config.submit_url, json=payload, headers=self._headers)
        response.raise_for_status()
        # The provider may bill as soon as the job is accepted, so count it here.
        self.spent_usd += cost
        return response.json()["job_id"]

    def _status(self, job_id: str) -> dict:
        url = self.config.status_url.format(job_id=job_id)
        response = self._client.get(url, headers=self._headers)
        response.raise_for_status()
        return response.json()

    def poll(self, job_id: str) -> JobState:
        status = self._status(job_id).get("status", "").lower()
        return {
            "queued": JobState.QUEUED, "running": JobState.RUNNING,
            "succeeded": JobState.SUCCEEDED, "completed": JobState.SUCCEEDED,
        }.get(status, JobState.FAILED)

    def fetch(self, job_id: str, destination: Path) -> Path:
        url = self._status(job_id)["video_url"]
        response = self._client.get(url)
        response.raise_for_status()
        destination = Path(destination)
        destination.write_bytes(response.content)
        return destination
