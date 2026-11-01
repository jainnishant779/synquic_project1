"""One daily cycle for one tenant: ingest, learn, evaluate, then promote or keep the champion."""
import tempfile
from collections import Counter
from pathlib import Path

from ..common.manifest import sha256_file
from .gates import MIN_NEW_EXAMPLES, gate_data, gate_latency, gate_leakage, gate_quality, summarise
from .ingest import ingest
from .service import Platform
from .store import tokenize
from .tenancy import TenantContext
from .trainers.tiny import load_model, predict


def extract_insights(records: list[dict], top: int = 5) -> dict:
    """Rule-based term counts per label. A real deployment would use an LLM here [DESIGN]."""
    terms: dict[str, Counter] = {}
    for record in records:
        terms.setdefault(record["label"], Counter()).update(
            t for t in tokenize(record["text"]) if len(t) > 3 and not t.startswith("ref")
        )
    return {label: [t for t, _ in counter.most_common(top)] for label, counter in terms.items()}


def build_dataset(records: list[dict]) -> list[dict]:
    """Only records from training-eligible sources can reach a trainer."""
    return [{"text": r["text"], "label": r["label"]} for r in records if r.get("training_eligible")]


def _correct(model, golden: list[dict]) -> list[bool]:
    predictions = predict(model, [e["text"] for e in golden])
    return [p == e["label"] for p, e in zip(predictions, golden)]


def run_day(platform: Platform, ctx: TenantContext, day: int, new_records: list[dict], trainer,
            golden: list[dict], other_tenant_canaries: list[str]) -> dict:
    tenant_id = ctx.tenant_id
    store = platform.store(tenant_id)
    report = ingest(ctx, store, new_records)
    result = {"day": day, "tenant": tenant_id, "ingested": report.accepted,
              "refused_unapproved": report.rejected_unapproved, "redactions": report.redactions}

    records = store.records(ctx)
    examples = build_dataset(records)
    registry = platform.registry
    versions = registry.versions(ctx, tenant_id)
    trained = registry.metadata(ctx, tenant_id, versions[-1])["examples"] if versions else 0
    if len(examples) - trained < MIN_NEW_EXAMPLES:
        return result | {"outcome": "skipped", "reason": f"under {MIN_NEW_EXAMPLES} eligible examples since the last run"}

    # Bad data is refused before any compute is spent on it.
    data_gate = gate_data(examples, golden)
    if not data_gate.passed:
        platform.log("data_gate_failed", tenant_id, day=day)
        return result | {"outcome": "rejected", "reason": "data gate", "gates": summarise([data_gate])}

    champion_version = registry.prod_version(ctx, tenant_id)
    champion_adapter = registry.adapter_path(ctx, tenant_id, champion_version) if champion_version else None

    with tempfile.TemporaryDirectory() as temporary:
        candidate_path = trainer.train(examples, Path(temporary) / "candidate.pt", champion_adapter)
        candidate = load_model(platform.base_path, candidate_path)
        champion = load_model(platform.base_path, champion_adapter)
        leakage = gate_leakage(candidate_path, other_tenant_canaries)
        gates = summarise([
            data_gate,
            gate_quality(_correct(candidate, golden), _correct(champion, golden)),
            leakage,
            gate_latency(lambda: predict(candidate, [golden[0]["text"]])),
        ])
        # A leaking artefact is evidence of a breach, so only its metadata is kept.
        version = registry.register(ctx, tenant_id, candidate_path if leakage.passed else None, {
            "day": day, "base_sha256": sha256_file(platform.base_path), "previous": champion_version,
            "examples": len(examples),
            "gates": gates, "insights": extract_insights(records),
        })

    if not leakage.passed:
        platform.log("leakage_incident", tenant_id, day=day, version=version)
    if gates["passed"]:
        registry.promote(ctx, tenant_id, version)
    platform.log("cycle", tenant_id, day=day, version=version, promoted=gates["passed"])
    return result | {"outcome": "promoted" if gates["passed"] else "rejected", "version": version,
                     "champion_after": registry.prod_version(ctx, tenant_id), "gates": gates}
