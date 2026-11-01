"""Tenant isolation, attacked with per-tenant canaries.

Canaries deliberately survive PII redaction: a redacted canary cannot leak, which would make every
scan below pass vacuously.

Scope: application-level isolation on one machine. Cloud IAM, network, GPU memory and a shared
serving process are not covered here.
"""
import json

import pytest
import torch
from fastapi.testclient import TestClient

from poc.social360.gates import gate_leakage
from poc.social360.isolation import TenantIsolationBreachError, check_bytes, check_retrieval, check_text
from poc.social360.pipeline import run_day
from poc.social360.service import Platform, create_app
from poc.social360.store import decrypt
from poc.social360.synthetic import TENANTS, base_corpus, golden_set, records_with_pii_and_unapproved, tenant_records
from poc.social360.tenancy import AccessDenied, TenantContext, issue_token
from poc.social360.trainers.tiny import LeakyTrainer, TinyAdapterTrainer, featurize, load_model, train_base

A, B = "fictional_bakery", "fictional_bikes"
CANARY_A, CANARY_B = TENANTS[A]["canary"], TENANTS[B]["canary"]
SECRET = b"test-secret"


def headers(tenant, role="service"):
    return {"Authorization": f"Bearer {issue_token(tenant, SECRET, role)}"}


@pytest.fixture(scope="module")
def platform(tmp_path_factory):
    root = tmp_path_factory.mktemp("s360")
    base = train_base(base_corpus(), root / "base.pt")
    platform = Platform(root / "tenants", base)
    for tenant, canaries in ((A, [CANARY_B]), (B, [CANARY_A])):
        platform.add_tenant(tenant)
        records = tenant_records(tenant, 60, seed=1, day=1) + records_with_pii_and_unapproved(tenant, 1)
        run_day(platform, TenantContext(tenant), 1, records, TinyAdapterTrainer(base), golden_set(tenant), canaries)
    return platform


@pytest.fixture(scope="module")
def client(platform):
    return TestClient(create_app(platform, SECRET))


@pytest.fixture
def unsafe_shared_index(platform):
    """Negative control: a retriever that ignores tenant scope. Exists only in this test file."""
    def search(ctx, query):
        found = []
        for tenant in (A, B):
            found += platform.store(tenant).search(TenantContext(tenant), query)
        return found
    return search


def test_01_token_cannot_name_another_tenant(client):
    assert client.post("/v1/infer", json={"text": "hi", "tenant_id": B}, headers=headers(A)).status_code == 403
    assert client.get(f"/v1/tenants/{B}/versions", headers=headers(A)).status_code == 403
    assert client.get(f"/v1/tenants/{A}/versions", headers=headers(A)).status_code == 200


def test_01b_bad_or_missing_token_is_refused(client):
    assert client.post("/v1/infer", json={"text": "hi"}).status_code == 401
    forged = {"Authorization": "Bearer " + issue_token(B, b"wrong-secret")}
    assert client.post("/v1/infer", json={"text": "hi"}, headers=forged).status_code == 401


def test_02_retrieval_returns_only_own_records(platform, client):
    check_retrieval(platform.search, TenantContext(A), [CANARY_B])
    check_retrieval(platform.search, TenantContext(B), [CANARY_A])
    response = client.post("/v1/infer", json={"text": CANARY_B}, headers=headers(A))
    assert response.status_code == 200
    assert CANARY_B not in json.dumps(response.json())


def test_03_stores_are_keyed_and_encrypted(platform):
    with pytest.raises(AccessDenied):
        platform.store(B).records(TenantContext(A))
    blob = (platform.store(B).dir / "records.enc").read_bytes()
    assert CANARY_B.encode() not in blob
    with pytest.raises(AccessDenied):
        decrypt(platform.keyring.key_for(A), blob)
    assert any(CANARY_B in r["text"] for r in platform.store(B).records(TenantContext(B)))


def test_04_adapter_versions_resolve_only_for_owner(platform):
    ctx = TenantContext(A)
    with pytest.raises(AccessDenied):
        platform.registry.adapter_path(ctx, B, "v0001")
    with pytest.raises(AccessDenied):
        platform.registry.promote(ctx, B, "v0001")


@pytest.mark.parametrize("version", ["../../fictional_bikes/registry/v0001", "..", "v1", "v0001/../v0001", ""])
def test_04b_version_strings_cannot_traverse(platform, version):
    """Regression: a version string once reached another tenant's adapter and metadata."""
    ctx = TenantContext(A)
    before = platform.registry.prod_version(ctx, A)
    for call in (platform.registry.metadata, platform.registry.promote, platform.registry.adapter_path):
        with pytest.raises(AccessDenied):
            call(ctx, A, version)
    assert platform.registry.prod_version(ctx, A) == before


def test_05_tenant_artefacts_hold_no_foreign_canary(platform):
    check_bytes(platform.store(A).dir, [CANARY_B])
    check_bytes(platform.store(B).dir, [CANARY_A])
    # check_bytes cannot see inside ciphertext, so decrypted records are checked too.
    assert not any(CANARY_B in r["text"] for r in platform.store(A).records(TenantContext(A)))
    assert not any(CANARY_A in r["text"] for r in platform.store(B).records(TenantContext(B)))


def test_06_training_one_tenant_leaves_the_other_unchanged(platform, tmp_path):
    """The classifier returns a label, so it cannot echo text. This test proves separation of weights;
    probing an LLM for regurgitated canaries needs the real model."""
    features = featurize(["the saddle is stiff this week"])
    ctx_a, ctx_b = TenantContext(A), TenantContext(B)
    b_adapter = platform.registry.adapter_path(ctx_b, B, "v0001")
    with torch.no_grad():
        before = load_model(platform.base_path, b_adapter)(features)
        original_a = load_model(platform.base_path, platform.registry.adapter_path(ctx_a, A, "v0001"))(features)
    retrained = TinyAdapterTrainer(platform.base_path, epochs=30, seed=7).train(
        tenant_records(A, 20, seed=11), tmp_path / "a2.pt")
    with torch.no_grad():
        after = load_model(platform.base_path, b_adapter)(features)
        new_a = load_model(platform.base_path, retrained)(features)
    assert torch.equal(before, after)
    assert not torch.allclose(before, original_a)
    assert not torch.allclose(original_a, new_a)


def test_07_logs_and_metrics_hold_no_content(platform, client):
    text = "PRIVATE-QUERY-TEXT the sourdough is flaky"
    client.post("/v1/infer", json={"text": text}, headers=headers(A))
    telemetry = json.dumps(platform.audit) + json.dumps(platform.metrics)
    check_text(telemetry, ["PRIVATE-QUERY-TEXT", CANARY_A, CANARY_B, A, B])


def test_07b_model_cache_is_scoped_by_tenant(platform, client):
    client.post("/v1/infer", json={"text": "hi"}, headers=headers(A))
    client.post("/v1/infer", json={"text": "hi"}, headers=headers(B))
    keys = list(platform._models)
    assert (A, "v0001") in keys and (B, "v0001") in keys
    assert platform._models[(A, "v0001")] is not platform._models[(B, "v0001")]


@pytest.mark.parametrize("detector", ["retrieval", "bytes"])
def test_08_negative_control_detectors_catch_a_real_leak(platform, unsafe_shared_index, detector, tmp_path):
    if detector == "retrieval":
        with pytest.raises(TenantIsolationBreachError):
            check_retrieval(unsafe_shared_index, TenantContext(A), [CANARY_B])
    else:
        path = LeakyTrainer(platform.base_path, CANARY_B, epochs=2).train(
            [{"text": "a", "label": "positive"}], tmp_path / "leak.pt")
        with pytest.raises(TenantIsolationBreachError):
            check_bytes(path.parent, [CANARY_B])


def test_08a_log_detector_catches_content_in_telemetry():
    with pytest.raises(TenantIsolationBreachError):
        check_text('{"event": "infer", "text": "' + CANARY_B + '"}', [CANARY_B])


def test_08c_byte_scan_limit_is_real(platform, tmp_path):
    """Documents a limit: an adapter trained on a foreign canary passes G3, because a byte scan
    only finds literal strings. Detecting learned leakage needs a probe on the real model."""
    leaked = [{"text": f"the item is great {CANARY_B}", "label": "positive"}] * 20
    path = TinyAdapterTrainer(platform.base_path, epochs=30).train(leaked, tmp_path / "learned.pt")
    assert gate_leakage(path, [CANARY_B]).passed


def test_08b_leakage_gate_blocks_promotion(platform):
    ctx = TenantContext(A)
    before = platform.registry.prod_version(ctx, A)
    result = run_day(platform, ctx, 9, tenant_records(A, 40, seed=9, day=9),
                     LeakyTrainer(platform.base_path, CANARY_B, epochs=30), golden_set(A), [CANARY_B])
    assert result["outcome"] == "rejected"
    leakage = next(g for g in result["gates"]["gates"] if g["name"] == "G3_leakage")
    assert leakage["passed"] is False
    assert platform.registry.prod_version(ctx, A) == before
    assert not platform.registry.adapter_path(ctx, A, result["version"]).exists()
    assert any(entry["event"] == "leakage_incident" for entry in platform.audit)
    check_bytes(platform.store(A).dir, [CANARY_B])


def test_09_admin_sees_aggregates_only_and_break_glass_is_audited(platform, client):
    admin = headers("ops", role="admin")
    assert client.post("/v1/infer", json={"text": "hi"}, headers=admin).status_code == 403
    assert client.get(f"/v1/tenants/{A}/versions", headers=admin).status_code == 403
    assert client.get("/v1/admin/metrics", headers=headers(A)).status_code == 403
    assert client.get("/v1/admin/metrics", headers=admin).status_code == 200
    blank = client.post("/v1/admin/break-glass", json={"tenant_id": A, "reason": "  "}, headers=admin)
    assert blank.status_code == 400
    granted = client.post("/v1/admin/break-glass", json={"tenant_id": A, "reason": "ticket 42"}, headers=admin)
    assert set(granted.json()) == {"record_count"}
    assert platform.audit[-1]["event"] == "break_glass" and platform.audit[-1]["reason"] == "ticket 42"
    outside = client.post("/v1/admin/break-glass", json={"tenant_id": "../../x", "reason": "r"}, headers=admin)
    assert outside.status_code == 404
    assert not (platform.root.parent / "x").exists()


def test_10_offboarding_removes_everything(tmp_path):
    base = train_base(base_corpus(60), tmp_path / "base.pt", epochs=5)
    platform = Platform(tmp_path / "tenants", base)
    client = TestClient(create_app(platform, SECRET))
    for tenant in (A, B):
        ctx = TenantContext(tenant)
        platform.add_tenant(tenant).add(ctx, [{"text": TENANTS[tenant]["canary"], "label": "positive"}])
        adapter = TinyAdapterTrainer(base, epochs=2).train([{"text": "a", "label": "positive"}], tmp_path / f"{tenant}.pt")
        platform.registry.promote(ctx, tenant, platform.registry.register(ctx, tenant, adapter, {"examples": 1}))
    token = headers(B)
    assert client.post("/v1/infer", json={"text": "hi"}, headers=token).status_code == 200

    platform.offboard(B)

    assert not (platform.root / B).exists()
    with pytest.raises(AccessDenied):
        platform.keyring.key_for(B)
    assert not any(key[0] == B for key in platform._models)
    assert client.post("/v1/infer", json={"text": "hi"}, headers=token).status_code == 401
    assert client.get(f"/v1/tenants/{B}/versions", headers=token).status_code == 401
    assert not (platform.root / B).exists()
    assert platform.store(A).records(TenantContext(A))


def test_10b_offboarded_ids_are_never_reused(tmp_path):
    """Regression: a reused id once served the previous owner's cached adapter."""
    base = train_base(base_corpus(60), tmp_path / "base.pt", epochs=5)
    platform = Platform(tmp_path / "tenants", base)
    platform.add_tenant(B)
    platform.offboard(B)
    with pytest.raises(ValueError):
        platform.add_tenant(B)
