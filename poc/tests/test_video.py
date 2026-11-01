"""Video pipeline tests. Adapters get one shared contract; QC runs on real ffmpeg output."""
import json
import subprocess

import httpx
import pytest

from poc.video.adapters.api_http import ApiAdapter, ApiProviderConfig
from poc.video.adapters.base import AdapterError, Capabilities, ClipRequest, JobState, SpendCapExceeded
from poc.video.adapters.local_http import LocalAdapter, wan_frame_count
from poc.video.adapters.mock import BAND_HEIGHT, MockAdapter
from poc.video.credits import charge, load_rate_card
from poc.video.pipeline import run
from poc.video.planner import PROMPTS_DIR, build_storyboard
from poc.video.qc import FAIL, NOT_EVALUATED, SEMANTIC_CHECKS, check_clip, probe
from poc.video.router import NoProviderAvailable, Requirements, load_catalog, route
from poc.video.schemas import Brief, CharacterProfile, ProductReference, Storyboard, StyleBible, VideoSpec

CAPS = Capabilities(max_clip_seconds=10, max_width=1280, max_height=720)
REQUEST = ClipRequest("sh1", "a prompt", "", 2, 320, 180, 24, seed=1)


def make_brief(seconds=20) -> Brief:
    return Brief(
        title="Test film", objective="Show the kettle", audience="testers", tone="plain",
        duration_seconds=seconds,
        characters=[CharacterProfile(id="maya", name="Maya", canonical_description="curly black hair",
                                     wardrobe="mustard cardigan", reference_images=["maya.png"])],
        products=[ProductReference(id="kettle", name="Kettle", canonical_description="matte teal body",
                                   reference_images=["kettle.png"])],
        style=StyleBible(visual_style="film grain", palette="teal", lighting="soft", lens="35mm"),
    )


@pytest.fixture(scope="module")
def clip_bytes(tmp_path_factory) -> bytes:
    work = tmp_path_factory.mktemp("clip")
    adapter = MockAdapter(work)
    return adapter._jobs[adapter.submit(REQUEST)].read_bytes()


def fake_worker(clip: bytes) -> httpx.MockTransport:
    """One fake server for both HTTP adapters: accepts a job, reports it done, returns a clip."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST":
            return httpx.Response(200, json={"job_id": "j1"})
        if path.endswith("/output") or path.endswith("/video"):
            return httpx.Response(200, content=clip)
        return httpx.Response(200, json={
            "state": "succeeded", "status": "completed", "video_url": "https://fake.test/video",
        })
    return httpx.MockTransport(handler)


def make_api(clip, max_spend=100.0):
    config = ApiProviderConfig("fake-api", "https://fake.test/submit", "https://fake.test/status/{job_id}", 0.5, CAPS)
    return ApiAdapter(config, "key", max_spend, httpx.Client(transport=fake_worker(clip)))


def make_local(clip):
    return LocalAdapter("http://worker.test", 2.0, 30.0, CAPS, httpx.Client(transport=fake_worker(clip)))


@pytest.mark.parametrize("kind", ["mock", "api", "local"])
def test_adapter_contract(kind, tmp_path, clip_bytes):
    adapter = {"mock": lambda: MockAdapter(tmp_path / "w"), "api": lambda: make_api(clip_bytes),
               "local": lambda: make_local(clip_bytes)}[kind]()
    assert adapter.capabilities().max_clip_seconds > 0
    assert adapter.estimate_cost(REQUEST) >= 0
    job_id = adapter.submit(REQUEST)
    assert adapter.poll(job_id) is JobState.SUCCEEDED
    output = adapter.fetch(job_id, tmp_path / "out.mp4")
    assert probe(output)["streams"][0]["codec_type"] == "video"


@pytest.mark.parametrize("seconds,fps,frames", [(5, 16, 81), (5, 24, 121), (1, 24, 25)])
def test_wan_frame_counts_follow_4n_plus_1(seconds, fps, frames):
    assert wan_frame_count(seconds, fps) == frames
    assert (frames - 1) % 4 == 0


@pytest.mark.parametrize("status", ["pending", "generating_video", "qc_evaluation", "something_new"])
def test_api_adapter_keeps_polling_unfamiliar_statuses(status, clip_bytes):
    def handler(request):
        return httpx.Response(200, json={"status": status})
    config = ApiProviderConfig("fake", "https://fake.test/s", "https://fake.test/{job_id}", 0.5, CAPS)
    adapter = ApiAdapter(config, "key", 10.0, httpx.Client(transport=httpx.MockTransport(handler)))
    assert adapter.poll("j1") is JobState.RUNNING


def test_api_adapter_refuses_without_key(clip_bytes):
    config = ApiProviderConfig("fake", "https://fake.test/s", "https://fake.test/{job_id}", 0.5, CAPS)
    with pytest.raises(AdapterError):
        ApiAdapter(config, None, 10.0)


def test_api_adapter_enforces_spend_cap(clip_bytes):
    adapter = make_api(clip_bytes, max_spend=1.5)
    adapter.submit(REQUEST)  # 2 s at 0.5 USD/s = 1.00 USD
    with pytest.raises(SpendCapExceeded):
        adapter.submit(REQUEST)
    assert adapter.spent_usd == 1.0


@pytest.mark.parametrize("fault,failed_check", [
    ("black", "black_frames"), ("frozen", "frozen_frames"),
    ("wrong_duration", "duration"), ("wrong_aspect", "resolution"),
])
def test_qc_catches_each_injected_fault(fault, failed_check, tmp_path):
    adapter = MockAdapter(tmp_path, {("sh1", 1): fault})
    request = ClipRequest("sh1", "a prompt", "", 2, 640, 360, 24, seed=1)
    clip = adapter.fetch(adapter.submit(request), tmp_path / "clip.mp4")
    assert failed_check in check_clip(clip, 2, VideoSpec()).failures


def test_qc_fails_a_file_with_no_video(tmp_path):
    audio = tmp_path / "audio.m4a"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=duration=1", str(audio)], check=True)
    assert "has_video_stream" in check_clip(audio, 1, VideoSpec()).failures


def test_clean_clip_passes_and_semantic_checks_are_not_passes(tmp_path):
    adapter = MockAdapter(tmp_path)
    clip = adapter.fetch(adapter.submit(REQUEST), tmp_path / "clip.mp4")
    result = check_clip(clip, 2, VideoSpec(width=320, height=180))
    assert result.passed
    statuses = {c["name"]: c["status"] for c in result.checks}
    assert all(statuses[name] == NOT_EVALUATED for name in SEMANTIC_CHECKS)


def test_every_prompt_carries_canonical_references():
    storyboard = build_storyboard(make_brief(60))
    for shot in storyboard.shots:
        assert "curly black hair" in shot.prompt and "mustard cardigan" in shot.prompt
        assert "matte teal body" in shot.prompt and "film grain" in shot.prompt
        assert shot.reference_images == ["maya.png", "kettle.png"]


def test_master_prompt_example_validates_against_the_schema():
    plan = Storyboard.model_validate_json((PROMPTS_DIR / "example_plan.json").read_text(encoding="utf-8"))
    assert sum(s.duration_seconds for s in plan.shots) == 10
    assert all(s.audio for s in plan.shots)


def test_dialects_render_exclusions_their_own_way():
    brief = make_brief(5)
    veo = build_storyboard(brief, dialect_name="veo").shots[0]
    assert "No " not in veo.prompt and "watermark" in veo.negative_prompt

    local = build_storyboard(brief, dialect_name="wan_local").shots[0]
    assert "watermark" in local.negative_prompt

    wan = build_storyboard(brief, dialect_name="wan").shots[0]
    assert "No watermark." in wan.prompt and wan.negative_prompt == ""

    omni = build_storyboard(brief, dialect_name="omni_flash").shots[0]
    assert omni.prompt.startswith("Single continuous shot")


def test_image_to_video_dialect_is_motion_only():
    shot = build_storyboard(make_brief(5), dialect_name="wan_i2v").shots[0]
    assert "curly black hair" not in shot.prompt
    assert shot.reference_images == ["maya.png", "kettle.png"]


def test_regeneration_recovers_from_fault(tmp_path):
    adapter = MockAdapter(tmp_path / "j", {("sc01_sh02", 1): "black", ("sc01_sh03", 1): "frozen"})
    manifest = run(make_brief(20), adapter, tmp_path / "run")
    assert manifest["status"] == "complete"
    assert manifest["total_attempts"] == 6
    assert manifest["real_generation"] is False and manifest["labels"] == ["[MOCK]"]


def test_attempts_are_bounded_and_run_fails_cleanly(tmp_path):
    faults = {("sc01_sh01", attempt): "black" for attempt in range(1, 10)}
    manifest = run(make_brief(10), MockAdapter(tmp_path / "j", faults), tmp_path / "run", max_attempts=3)
    assert manifest["status"] == "failed_qc"
    assert manifest["failed_shots"] == ["sc01_sh01"]
    assert len(manifest["shots"][0]["attempts"]) == 3
    assert "credits" not in manifest
    assert not (tmp_path / "run" / "final.mp4").exists()


def test_resume_reuses_passed_shots(tmp_path):
    faults = {("sc01_sh02", attempt): "black" for attempt in range(1, 10)}
    failed = run(make_brief(10), MockAdapter(tmp_path / "j", faults), tmp_path / "run", max_attempts=2)
    assert failed["status"] == "failed_qc" and failed["total_attempts"] == 3
    resumed = run(make_brief(10), MockAdapter(tmp_path / "j2"), tmp_path / "run")
    assert resumed["status"] == "complete" and resumed["total_attempts"] == 1


def test_changed_references_are_not_served_from_cache(tmp_path):
    run(make_brief(5), MockAdapter(tmp_path / "j"), tmp_path / "run")
    changed = make_brief(5)
    changed.characters[0].reference_images = ["someone_else.png"]
    assert run(changed, MockAdapter(tmp_path / "j2"), tmp_path / "run")["total_attempts"] == 1


def _band_is_red(video, timestamp: float, width=640) -> bool:
    command = ["ffmpeg", "-v", "error", "-ss", str(timestamp), "-i", str(video), "-frames:v", "1",
               "-vf", f"crop={width}:4:0:{BAND_HEIGHT - 8}", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-"]
    data = subprocess.run(command, capture_output=True, check=True).stdout
    # Sample the far right of the band, clear of the text.
    red, green, blue = data[-30], data[-29], data[-28]
    return red > 180 and green < 80 and blue < 80


def test_five_minute_mock_run(tmp_path):
    manifest = run(make_brief(300), MockAdapter(tmp_path / "j"), tmp_path / "run")
    assert manifest["status"] == "complete"
    assert len(manifest["shots"]) == 60
    storyboard = json.loads((tmp_path / "run" / "storyboard.json").read_text())
    orders = [s["order"] for scene in storyboard["scenes"] for s in scene["shots"]]
    assert orders == sorted(orders)
    final = tmp_path / "run" / "final.mp4"
    assert abs(float(probe(final)["format"]["duration"]) - 300) < 1
    checks = {c["name"]: c["status"] for c in manifest["final_qc"]["checks"]}
    assert set(checks) >= {"has_video_stream", "has_audio_stream", "has_captions", "duration", "silent_audio"}
    assert FAIL not in checks.values()
    shots = Storyboard.model_validate(storyboard).shots
    listed = (tmp_path / "run" / "concat.txt").read_text().splitlines()
    assert len(listed) == len(shots) and len(set(listed)) == len(shots)
    for timestamp in (1, 150, 299):
        assert _band_is_red(final, timestamp), f"watermark missing at {timestamp}s"


def test_rate_card_matches_the_workbook():
    openpyxl = pytest.importorskip("openpyxl")
    book = openpyxl.load_workbook("workbook/synquic_comparison_pricing.xlsx", data_only=True)
    rows = {row[5]: row[2] for row in book["Credits"].iter_rows(values_only=True) if len(row) > 5 and row[5]}
    operations = load_rate_card()["operations"]
    assert operations["planning_per_video"] == rows["planning_per_video"]
    assert operations["assembly_per_minute"] == rows["assembly_per_minute"]
    for tier, credits in operations["generation_per_second"].items():
        assert credits == rows[f"generation_per_second.{tier}"]


def test_credits_follow_the_rate_card():
    card = {"status": "t", "operations": {"planning_per_video": 2, "assembly_per_minute": 3,
                                          "generation_per_second": {"standard": 5}}}
    assert charge(90, card)["total_credits"] == 2 + 90 * 5 + 2 * 3
    assert charge(90, load_rate_card())["total_credits"] > 0


ENTRY = {"name": "a", "price_per_second_usd": 0.1, "max_clip_seconds": 8, "max_width": 1920,
         "max_height": 1080, "supports_references": True, "licence_verdict": "Allowed"}


def test_router_picks_cheapest_eligible_and_skips_blocked():
    catalog = [ENTRY, ENTRY | {"name": "b", "price_per_second_usd": 0.05, "licence_verdict": "Blocked"},
               ENTRY | {"name": "c", "price_per_second_usd": 0.08}]
    chosen, rejected = route(catalog, Requirements(5, 1280, 720), {"a", "b", "c"})
    assert chosen["name"] == "c" and rejected == {"b": "licence blocked"}


def test_router_excludes_counsel_routes_unless_accepted():
    catalog = [ENTRY | {"name": "clear", "price_per_second_usd": 0.2},
               ENTRY | {"name": "legal", "price_per_second_usd": 0.1, "licence_verdict": "Counsel"}]
    names = {"clear", "legal"}
    chosen, rejected = route(catalog, Requirements(5, 1280, 720), names)
    assert chosen["name"] == "clear" and rejected == {"legal": "needs counsel"}
    assert route(catalog, Requirements(5, 1280, 720), names, allow_counsel=True)[0]["name"] == "legal"


def test_real_catalog_routes_only_to_allowed_and_rejects_blocked():
    catalog = [e for e in load_catalog() if e["name"] != "mock"]
    chosen, rejected = route(catalog, Requirements(5, 640, 360), {e["name"] for e in catalog})
    assert chosen["licence_verdict"] == "Allowed"
    assert "licence blocked" in rejected.values() and "needs counsel" in rejected.values()


def test_router_fails_loudly_when_nothing_fits():
    with pytest.raises(NoProviderAvailable):
        route([ENTRY], Requirements(20, 1280, 720), {"a"})
