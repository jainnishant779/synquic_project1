"""Customer credit charge. Rates come from rate_card.json, which the workbook build writes.

Automatic QC regenerations are not charged: their cost is already inside the per-second rate.
"""
import json
import math
from pathlib import Path

RATE_CARD = Path(__file__).resolve().parents[1] / "rate_card.json"


def load_rate_card(path: Path = RATE_CARD) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def charge(duration_seconds: int, rate_card: dict, tier: str = "standard") -> dict:
    operations = rate_card["operations"]
    minutes = math.ceil(duration_seconds / 60)
    lines = {
        "planning": operations["planning_per_video"],
        "generation": duration_seconds * operations["generation_per_second"][tier],
        "assembly": minutes * operations["assembly_per_minute"],
    }
    return {"lines": lines, "total_credits": sum(lines.values()), "rate_card_status": rate_card["status"]}
