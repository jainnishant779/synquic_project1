"""Validate research\\raw\\*.jsonl against the schema in research\\RESEARCH_RULES.md and write research\\facts.csv."""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "raw"
VERIFY = ROOT / "research" / "verify"
OUT = ROOT / "research" / "facts.csv"

KEYS = [
    "fact_id", "workstream", "entity", "attribute", "value", "unit", "currency",
    "conditions", "source_url", "source_type", "quote", "date_checked",
    "source_updated", "status", "verified_by", "verified_date", "notes",
]
SOURCE_TYPES = {"primary_pricing", "primary_docs", "licence_text", "paper", "secondary"}
STATUSES = {"single_source", "conflict", "unverifiable", "verified", "failed"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check(fact):
    errors = []
    missing = [k for k in KEYS if k not in fact]
    if missing:
        return [f"missing keys {missing}"]
    for key in ("fact_id", "workstream", "entity", "attribute", "source_url"):
        if not fact[key]:
            errors.append(f"empty {key}")
    if fact["value"] is None and fact["status"] != "unverifiable":
        errors.append("value is null but status is not unverifiable")
    if fact["source_type"] not in SOURCE_TYPES:
        errors.append(f"bad source_type {fact['source_type']!r}")
    if fact["status"] not in STATUSES:
        errors.append(f"bad status {fact['status']!r}")
    if not DATE.match(str(fact["date_checked"] or "")):
        errors.append(f"bad date_checked {fact['date_checked']!r}")
    if str(fact["source_url"]).split(":")[0] not in ("http", "https"):
        errors.append("source_url is not http(s)")
    # A fact recording that something is absent has nothing to quote.
    records_absence = str(fact["value"]).startswith("none ")
    needs_quote = (is_number(fact["value"]) or "licence" in str(fact["attribute"])) and not records_absence
    if needs_quote and fact["status"] != "unverifiable" and not fact["quote"]:
        errors.append("numeric or licence fact without a quote")
    if fact["quote"] and len(str(fact["quote"]).split()) > 25:
        errors.append("quote over 25 words")
    if ("price" in str(fact["attribute"]) or fact["currency"]) and not fact["conditions"]:
        errors.append("price without conditions")
    return errors


def merge_verification(facts, problems):
    """Apply verifier verdicts. A failed fact takes the verifier's value, and keeps the old one in notes."""
    by_id = {fact["fact_id"]: fact for fact in facts}
    counts = Counter()
    for path in sorted(VERIFY.glob("*_results.jsonl")):
        verifier = path.name.split("_")[0]
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            result = json.loads(line)
            fact_id = result.get("fact_id", "")
            if "attribute" in result:  # A new fact found by the verifier.
                for error in check(result):
                    problems.append(f"{path.name}:{number} {fact_id}: {error}")
                facts.append(result)
                by_id[fact_id] = result
                counts["new"] += 1
                continue
            fact = by_id.get(fact_id)
            if fact is None:
                problems.append(f"{path.name}:{number}: unknown fact_id {fact_id}")
                continue
            verdict = result["verdict"]
            counts[verdict] += 1
            fact["status"] = verdict
            fact["verified_by"] = verifier
            fact["verified_date"] = result.get("verified_date")
            note = result.get("note")
            if verdict == "failed":
                note = f"Researcher value was {fact['value']!r}. {note or ''}"
                if result.get("value_seen") is not None:
                    fact["value"] = result["value_seen"]
            if note:
                fact["notes"] = f"{fact.get('notes') or ''} [{verifier}] {note}".strip()
    return counts


def main():
    facts, problems, seen = [], [], set()
    for path in sorted(RAW.glob("*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            where = f"{path.name}:{number}"
            try:
                fact = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"{where}: invalid JSON: {exc}")
                continue
            for error in check(fact):
                problems.append(f"{where} {fact.get('fact_id')}: {error}")
            if fact.get("fact_id") in seen:
                problems.append(f"{where}: duplicate fact_id {fact['fact_id']}")
            seen.add(fact.get("fact_id"))
            facts.append(fact)

    counts = merge_verification(facts, problems)
    if counts:
        print("verification:", dict(counts))

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=KEYS, extrasaction="ignore")
        writer.writeheader()
        for fact in facts:
            writer.writerow({k: fact.get(k) for k in KEYS})

    for problem in problems:
        print(problem)
    print(f"{len(facts)} facts, {len(problems)} problems, wrote {OUT}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
