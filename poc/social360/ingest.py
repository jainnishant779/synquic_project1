"""Ingestion: approved records only, PII redacted, and each record tagged for training eligibility.

Platform API data can serve retrieval and reporting but is never eligible for training here.
See the data rights table in docs/04-social360-architecture.md.
"""
import re
from dataclasses import dataclass

from .store import TenantStore
from .tenancy import TenantContext

PII_PATTERNS = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    # Neither a match that starts inside a longer digit run, nor an ISO date such as 2026-10-21, is a phone number.
    "PHONE": re.compile(r"(?<!\d)(?!\d{4}-\d{2}-\d{2}(?!\d))\+?\d[\d\s().-]{7,}\d"),
    "HANDLE": re.compile(r"(?<![\w@])@[A-Za-z0-9_]{2,}"),
}


TRAINING_ELIGIBLE_SOURCES = {"first_party", "licensed", "synthetic_open_weight"}


@dataclass
class IngestReport:
    accepted: int = 0
    rejected_unapproved: int = 0
    redactions: int = 0


def redact(text: str) -> tuple[str, int]:
    total = 0
    for label, pattern in PII_PATTERNS.items():
        text, count = pattern.subn(f"[{label}]", text)
        total += count
    return text, total


def contains_pii(text: str) -> bool:
    return any(p.search(text) for p in PII_PATTERNS.values())


def ingest(ctx: TenantContext, store: TenantStore, records: list[dict]) -> IngestReport:
    report, clean = IngestReport(), []
    for record in records:
        if not record.get("approved"):
            report.rejected_unapproved += 1
            continue
        text, count = redact(record["text"])
        report.redactions += count
        report.accepted += 1
        source = record.get("source", "unknown")
        clean.append({"text": text, "label": record["label"], "day": record.get("day", 0), "source": source,
                      "training_eligible": source in TRAINING_ELIGIBLE_SOURCES})
    if clean:
        store.add(ctx, clean)
    return report
