"""The sample must match the data request spec: system fields, no personal data, and no training on API data."""
import json

from poc.social360.ingest import TRAINING_ELIGIBLE_SOURCES, contains_pii
from poc.social360.sample_dataset import BRANDS, OUT, build, brand_id

SYSTEM_FIELDS = {"record_id", "brand_id", "type", "source", "approved", "collected_at", "training_eligible"}
KINDS = {"brand_document", "post", "metric", "comment", "support_ticket", "reviewer_edit"}
API_KINDS = {"post", "metric", "comment"}


def test_same_seed_gives_the_same_sample():
    assert build(seed=7) == build(seed=7) and build(seed=7) != build(seed=8)


def test_every_record_carries_the_system_fields_and_every_type_appears():
    records = build()
    assert all(SYSTEM_FIELDS <= set(r) for r in records)
    assert {r["type"] for r in records} == KINDS
    assert len({r["record_id"] for r in records}) == len(records)


def test_no_record_contains_personal_data_or_a_brand_name():
    names = set(BRANDS)
    for record in build():
        for value in record.values():
            if isinstance(value, str):
                assert not contains_pii(value), (record["record_id"], value)
                assert not any(name in value for name in names)
        for field in ("text", "draft", "edit"):
            assert "@" not in record.get(field, "")
        assert record["brand_id"].startswith("brand_") and record["brand_id"] not in names


def test_platform_api_data_is_never_training_eligible():
    for record in build():
        assert record["training_eligible"] == (record["source"] in TRAINING_ELIGIBLE_SOURCES)
        if record["type"] in API_KINDS:
            assert record["source"] == "platform_api" and record["training_eligible"] is False


def test_first_party_types_are_eligible_and_brand_ids_are_stable():
    records = build()
    assert all(r["training_eligible"] for r in records if r["type"] not in API_KINDS)
    assert {r["brand_id"] for r in records} == {brand_id(name) for name in BRANDS}


def test_committed_sample_file_matches_the_generator():
    if OUT.exists():
        assert [json.loads(line) for line in OUT.read_text(encoding="utf-8").splitlines()] == json.loads(json.dumps(build()))
