"""Split facts into verifier queues: every pricing and licence fact plus a seeded 20% sample."""
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "raw"
OUT = ROOT / "research" / "verify"
MUST_CHECK = re.compile(r"price|usd|credit|cost|licence|verdict|training_allowed|gpu_")
ASSIGNMENT = {"R1": "V1", "R2": "V1", "R3": "V1", "R5": "V2", "R6": "V2", "R7": "V2", "R4": "V2"}
SAMPLE_RATE = 0.20
SEED = 20261101


def main():
    OUT.mkdir(exist_ok=True)
    facts = [json.loads(line) for path in sorted(RAW.glob("R*.jsonl"))
             for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    required = [f for f in facts if MUST_CHECK.search(f["attribute"])]
    required_ids = {f["fact_id"] for f in required}
    others = [f for f in facts if f["fact_id"] not in required_ids]
    sample = random.Random(SEED).sample(others, round(len(others) * SAMPLE_RATE))

    queues = {"V1": {}, "V2": {}}
    for fact in required + sample:
        queues[ASSIGNMENT[fact["workstream"]]].setdefault(fact["source_url"], []).append(fact)

    for name, by_url in queues.items():
        lines = [json.dumps({"source_url": url, "facts": [
            {k: f[k] for k in ("fact_id", "entity", "attribute", "value", "unit", "conditions", "quote", "status")}
            for f in group]}, ensure_ascii=False) for url, group in by_url.items()]
        (OUT / f"{name}_queue.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(name, "urls", len(by_url), "facts", sum(len(g) for g in by_url.values()))


if __name__ == "__main__":
    main()
