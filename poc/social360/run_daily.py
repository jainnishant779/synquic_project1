"""Demo: five simulated days for two fictional tenants, then a call to the production API.

python -m poc.social360.run_daily
"""
import json
import secrets
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from ..common.labels import SIMULATED, SYNTHETIC_BANNER
from ..common.manifest import write_json
from .pipeline import run_day
from .service import Platform, create_app
from .synthetic import TENANTS, base_corpus, golden_set, records_with_pii_and_unapproved, tenant_records
from .tenancy import TenantContext, issue_token
from .trainers.tiny import DegradingTrainer, TinyAdapterTrainer, train_base

RUN_DIR = Path(__file__).resolve().parents[1] / "runs" / "social360"


def simulate_tenant(platform: Platform, tenant_id: str, other_canaries: list[str]) -> list[dict]:
    """Day 1 promoted, day 2 skipped, day 3 rejected, day 4 promoted, day 5 rollback."""
    ctx = TenantContext(tenant_id)
    golden = golden_set(tenant_id)
    trainer = TinyAdapterTrainer(platform.base_path)
    results = [run_day(platform, ctx, 1, tenant_records(tenant_id, 60, seed=1, day=1)
                       + records_with_pii_and_unapproved(tenant_id, 1), trainer, golden, other_canaries)]
    results.append(run_day(platform, ctx, 2, tenant_records(tenant_id, 5, seed=2, day=2),
                           trainer, golden, other_canaries))
    results.append(run_day(platform, ctx, 3, tenant_records(tenant_id, 40, seed=3, day=3),
                           DegradingTrainer(platform.base_path), golden, other_canaries))
    results.append(run_day(platform, ctx, 4, tenant_records(tenant_id, 40, seed=4, day=4),
                           trainer, golden, other_canaries))
    version = platform.registry.rollback(ctx, tenant_id)
    results.append({"day": 5, "tenant": tenant_id, "outcome": "rollback", "champion_after": version,
                    "reason": "simulated operator rollback"})
    return results


def main(run_dir: Path = RUN_DIR) -> int:
    print(SYNTHETIC_BANNER)
    print("A tiny CPU classifier exercises the pipeline. No LLM has been trained.")
    print(f"{SIMULATED} Days are simulated time, not a real schedule.\n")

    shutil.rmtree(run_dir, ignore_errors=True)
    base_path = train_base(base_corpus(), run_dir / "base.pt")
    platform = Platform(run_dir / "tenants", base_path)
    tenants = list(TENANTS)
    for tenant_id in tenants:
        platform.add_tenant(tenant_id)

    history = []
    for tenant_id in tenants:
        canaries = [TENANTS[t]["canary"] for t in tenants if t != tenant_id]
        for result in simulate_tenant(platform, tenant_id, canaries):
            history.append(result)
            quality = next((g["detail"] for g in result.get("gates", {}).get("gates", [])
                            if g["name"] == "G2_quality"), {})
            scores = f" accuracy {quality['champion_accuracy']:.2f} -> {quality['candidate_accuracy']:.2f}" if quality else ""
            print(f"{tenant_id:18} day {result['day']}: {result['outcome']:9}"
                  f" prod={result.get('champion_after', 'unchanged')}{scores}")

    secret = secrets.token_bytes(32)
    client = TestClient(create_app(platform, secret))
    headers = {"Authorization": f"Bearer {issue_token(tenants[0], secret)}"}
    served = client.post("/v1/infer", json={"text": "the sourdough is flaky this week"}, headers=headers)
    print("\nProduction API response:", json.dumps(served.json())[:200])
    write_json(run_dir / "history.json", {"labels": [SIMULATED], "history": history})
    return 0


if __name__ == "__main__":
    sys.exit(main())
