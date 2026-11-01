"""Leak detectors. The negative control in the tests proves these can actually fire."""
from pathlib import Path
from typing import Callable

from .tenancy import TenantContext


class TenantIsolationBreachError(AssertionError):
    pass


def check_retrieval(search: Callable[[TenantContext, str], list[dict]], ctx: TenantContext,
                    foreign_canaries: list[str]) -> None:
    """Query with other tenants' canaries. No returned record may contain one."""
    for canary in foreign_canaries:
        for record in search(ctx, canary):
            if canary in record["text"]:
                raise TenantIsolationBreachError(f"{ctx.tenant_id} retrieved a foreign canary")


def check_bytes(root: Path, foreign_canaries: list[str]) -> None:
    """Scan every file under root for other tenants' canaries."""
    for path in Path(root).rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            for canary in foreign_canaries:
                if canary.encode() in data:
                    raise TenantIsolationBreachError(f"foreign canary found in {path.name}")


def check_text(text: str, forbidden: list[str]) -> None:
    for item in forbidden:
        if item in text:
            raise TenantIsolationBreachError("forbidden content found in logs or metrics")
