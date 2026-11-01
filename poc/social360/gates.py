"""Promotion gates. A candidate reaches production only if every gate passes.

G1 data, G2 non-inferiority on a frozen golden set, G3 leakage, G4 latency.
"""
import hashlib
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from .ingest import contains_pii

MIN_NEW_EXAMPLES = 20
NON_INFERIORITY_MARGIN = 0.02
BOOTSTRAP_ROUNDS = 2000
LATENCY_BUDGET_MS = 200.0  # Demo budget for a shared CPU; says nothing about LLM serving latency.


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: dict = field(default_factory=dict)


def hash_dataset(examples: list[dict]) -> str:
    joined = "\n".join(sorted(f"{e['text']}|{e['label']}" for e in examples))
    return hashlib.sha256(joined.encode()).hexdigest()


def gate_data(examples: list[dict], golden: list[dict]) -> GateResult:
    golden_texts = {e["text"] for e in golden}
    overlap = sum(1 for e in examples if e["text"] in golden_texts)
    pii_hits = sum(1 for e in examples if contains_pii(e["text"]))
    passed = len(examples) >= MIN_NEW_EXAMPLES and overlap == 0 and pii_hits == 0
    return GateResult("G1_data", passed, {
        "examples": len(examples), "golden_overlap": overlap, "pii_hits": pii_hits,
        "dataset_sha256": hash_dataset(examples),
    })


def gate_quality(candidate_correct: list[bool], champion_correct: list[bool], seed: int = 0) -> GateResult:
    """Paired bootstrap: pass if the 5th percentile of (candidate - champion) is above -margin."""
    pairs = list(zip(candidate_correct, champion_correct))
    rng = random.Random(seed)
    deltas = []
    for _ in range(BOOTSTRAP_ROUNDS):
        sample = rng.choices(pairs, k=len(pairs))
        deltas.append(sum(a - b for a, b in sample) / len(sample))
    deltas.sort()
    lower = deltas[int(0.05 * BOOTSTRAP_ROUNDS)]
    return GateResult("G2_quality", lower > -NON_INFERIORITY_MARGIN, {
        "candidate_accuracy": sum(candidate_correct) / len(pairs),
        "champion_accuracy": sum(champion_correct) / len(pairs),
        "delta_lower_bound": round(lower, 4), "margin": NON_INFERIORITY_MARGIN,
    })


def gate_leakage(artefact: Path, canaries: list[str]) -> GateResult:
    """Scan the artefact for other tenants' canaries, as raw bytes and as stored byte tensors."""
    data = Path(artefact).read_bytes()
    hits = [c for c in canaries if c.encode() in data]
    return GateResult("G3_leakage", not hits, {"canaries_checked": len(canaries), "hits": len(hits)})


def gate_latency(infer: Callable[[], object], rounds: int = 50) -> GateResult:
    samples = []
    for _ in range(rounds):
        start = time.perf_counter()
        infer()
        samples.append((time.perf_counter() - start) * 1000)
    samples.sort()
    p95 = samples[int(0.95 * rounds) - 1]
    return GateResult("G4_latency", p95 <= LATENCY_BUDGET_MS, {"p95_ms": round(p95, 3), "budget_ms": LATENCY_BUDGET_MS})


def summarise(results: list[GateResult]) -> dict:
    return {"passed": all(r.passed for r in results), "gates": [asdict(r) for r in results]}
