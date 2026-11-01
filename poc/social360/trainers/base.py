"""Trainer interface, and the QLoRA specification that is deliberately not runnable here."""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class Trainer(Protocol):
    def train(self, examples: list[dict], output: Path, previous: Path | None = None) -> Path:
        """Train a tenant adapter and return its path."""
        ...


@dataclass(frozen=True)
class QloraTrainerSpec:
    """[DESIGN] Target configuration for a real LLM adapter. Needs a GPU, so it does not run here.

    Base model and values are finalised in docs/04-social360-architecture.md.
    """
    base_model: str = "see docs/04"
    rank: int = 16
    alpha: int = 32
    load_in_4bit: bool = True

    def train(self, examples, output, previous=None):
        raise NotImplementedError("[DESIGN] QLoRA training requires a GPU and is not implemented in this POC")
