"""Learning loop tests: ingestion, gates, registry and the five-day sequence."""
import pytest

from poc.social360.gates import gate_data, gate_quality
from poc.social360.ingest import contains_pii, ingest, redact
from poc.social360.run_daily import simulate_tenant
from poc.social360.service import Platform
from poc.social360.synthetic import TENANTS, base_corpus, golden_set, records_with_pii_and_unapproved, tenant_records
from poc.social360.tenancy import TenantContext
from poc.social360.trainers.base import QloraTrainerSpec
from poc.social360.trainers.tiny import train_base
from poc.common.manifest import sha256_file

TENANT = "fictional_bakery"


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    root = tmp_path_factory.mktemp("daily")
    base = train_base(base_corpus(), root / "base.pt")
    platform = Platform(root / "tenants", base)
    platform.add_tenant(TENANT)
    digest = sha256_file(base)
    return platform, simulate_tenant(platform, TENANT, [TENANTS["fictional_bikes"]["canary"]]), digest


def test_redaction_removes_email_phone_and_handle():
    text, count = redact("mail jo@example.test or +1 202 555 0143, thanks @someone")
    assert count == 3 and not contains_pii(text)


def test_ingest_refuses_unapproved_and_stores_no_pii(tmp_path):
    platform = Platform(tmp_path, tmp_path / "unused.pt")
    store = platform.add_tenant(TENANT)
    ctx = TenantContext(TENANT)
    report = ingest(ctx, store, records_with_pii_and_unapproved(TENANT, 1))
    assert report.rejected_unapproved == 1 and report.accepted == 2 and report.redactions == 3
    stored = store.records(ctx)
    assert not any(contains_pii(r["text"]) or "UNAPPROVED" in r["text"] for r in stored)


def test_day_sequence(run):
    _, results, _ = run
    assert [r["outcome"] for r in results] == ["promoted", "skipped", "rejected", "promoted", "rollback"]
    assert results[2]["champion_after"] == "v0001"
    assert results[3]["champion_after"] == "v0003"
    assert results[4]["champion_after"] == "v0001"


def test_learning_improves_on_the_base_model(run):
    quality = next(g for g in run[1][0]["gates"]["gates"] if g["name"] == "G2_quality")["detail"]
    assert quality["candidate_accuracy"] > quality["champion_accuracy"] + 0.1


def test_tenant_training_never_changes_the_shared_base(run):
    platform, _, digest = run
    assert sha256_file(platform.base_path) == digest


def test_versions_are_immutable_and_record_lineage(run):
    platform, _, _ = run
    ctx = TenantContext(TENANT)
    assert platform.registry.versions(ctx, TENANT) == ["v0001", "v0002", "v0003"]
    metadata = platform.registry.metadata(ctx, TENANT, "v0003")
    assert metadata["previous"] == "v0001" and metadata["gates"]["passed"]
    assert metadata["gates"]["gates"][0]["detail"]["dataset_sha256"]


def test_data_gate_rejects_golden_overlap_and_pii():
    golden = golden_set(TENANT, 30)
    assert not gate_data(golden, golden).passed
    examples = [{"text": f"item {i} jo@example.test", "label": "positive"} for i in range(30)]
    assert not gate_data(examples, golden).passed


def test_quality_gate_decisions():
    same = [True, False] * 100
    assert gate_quality(same, same).passed
    assert not gate_quality([False] * 200, [True] * 200).passed


def test_qlora_is_a_specification_only():
    with pytest.raises(NotImplementedError):
        QloraTrainerSpec().train([], None)
