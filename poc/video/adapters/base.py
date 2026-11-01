"""Provider contract. Every route (mock, API, local GPU) is an async job: submit, poll, fetch."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class Capabilities:
    max_clip_seconds: int
    max_width: int
    max_height: int
    supports_references: bool = False
    native_audio: bool = False


@dataclass(frozen=True)
class ClipRequest:
    shot_id: str
    prompt: str
    negative_prompt: str
    duration_seconds: int
    width: int
    height: int
    fps: int
    seed: int
    attempt: int = 1
    reference_images: tuple[str, ...] = field(default_factory=tuple)


class AdapterError(RuntimeError):
    """A provider call failed or was refused."""


class SpendCapExceeded(AdapterError):
    """Submitting this job would exceed the configured spend cap."""


class Adapter(ABC):
    name: str
    # False for anything that does not produce generated footage; recorded in the manifest.
    real_generation: bool = False

    @abstractmethod
    def capabilities(self) -> Capabilities: ...

    @abstractmethod
    def estimate_cost(self, request: ClipRequest) -> float:
        """Estimated provider cost in USD for one attempt."""

    @abstractmethod
    def submit(self, request: ClipRequest) -> str:
        """Start a job and return its id."""

    @abstractmethod
    def poll(self, job_id: str) -> JobState: ...

    @abstractmethod
    def fetch(self, job_id: str, destination: Path) -> Path:
        """Download a finished clip to destination."""
