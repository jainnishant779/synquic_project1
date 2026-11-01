"""Ingestion: approved records only, PII redacted before anything is stored."""
import re
from dataclasses import dataclass

from .store import TenantStore
from .tenancy import TenantContext

PII_PATTERNS = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "PHONE": re.compile(r"\+?\d[\d\s().-]{7,}\d"),
    "HANDLE": re.compile(r"(?<![\w@])@[A-Za-z0-9_]{2,}"),
}


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
        clean.append({"text": text, "label": record["label"], "day": record.get("day", 0)})
    if clean:
        store.add(ctx, clean)
    return report
