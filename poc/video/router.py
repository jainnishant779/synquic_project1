"""Pick a provider from provider_catalog.json by capability, licence verdict and cost."""
import json
from dataclasses import dataclass
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "provider_catalog.json"


@dataclass(frozen=True)
class Requirements:
    clip_seconds: int
    width: int
    height: int
    needs_references: bool = False


class NoProviderAvailable(RuntimeError):
    pass


def load_catalog(path: Path = CATALOG) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["providers"]


def rejection_reason(entry: dict, needs: Requirements, available: set[str], allow_counsel: bool) -> str | None:
    if entry["licence_verdict"] == "Blocked":
        return "licence blocked"
    if entry["licence_verdict"] == "Counsel" and not allow_counsel:
        return "needs counsel"
    if entry["name"] not in available:
        return "not available in this run"
    if entry["max_clip_seconds"] < needs.clip_seconds:
        return "clip too long"
    if entry["max_width"] < needs.width or entry["max_height"] < needs.height:
        return "resolution too high"
    if needs.needs_references and not entry["supports_references"]:
        return "no reference support"
    return None


def route(catalog: list[dict], needs: Requirements, available: set[str],
          allow_counsel: bool = False) -> tuple[dict, dict[str, str]]:
    """Return the cheapest eligible entry, and why every other entry was rejected.

    Counsel routes stay excluded until someone has explicitly accepted that legal position.
    """
    rejected, eligible = {}, []
    for entry in catalog:
        reason = rejection_reason(entry, needs, available, allow_counsel)
        if reason:
            rejected[entry["name"]] = reason
        else:
            eligible.append(entry)
    if not eligible:
        raise NoProviderAvailable(f"no provider meets {needs}: {rejected}")
    return min(eligible, key=lambda e: e["price_per_second_usd"]), rejected
