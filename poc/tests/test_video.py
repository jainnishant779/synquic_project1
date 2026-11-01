"""Video pipeline tests. Adapters get one shared contract; QC runs on real ffmpeg output."""
import json
import subprocess

import httpx
import pytest

from poc.video.adapters.api_http import ApiAdapter, ApiProviderConfig
from poc.video.adapters.base import AdapterError, Capabilities, ClipRequest, JobState, SpendCapExceeded
from poc.video.adapters.local_http import LocalAdapter
from poc.video.adapters.mock import BAND_HEIGHT, MockAdapter
from poc.video.credits import charge, load_rate_card
from poc.video.pipeline import run
from poc.video.planner import build_storyboard
from poc.video.qc import FAIL, NOT_EVALUATED, SEMANTIC_CHECKS, check_clip, probe
from poc.video.router import NoProviderAvailable, Requirements, route
from poc.video.schemas import Brief, CharacterProfile, ProductReference, StyleBible, VideoSpec

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
    first = run(make_brief(10), MockAdapter(tmp_path / "j"), tmp_path / "run")
    second = run(make_brief(10), MockAdapter(tmp_path / "j2"), tmp_path / "run")
    assert first["total_attempts"] == 2 and second["total_attempts"] == 0


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
    assert all(c["status"] != FAIL for c in manifest["final_qc"]["checks"])
    for timestamp in (1, 150, 299):
        assert _band_is_red(final, timestamp), f"watermark missing at {timestamp}s"


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


def test_router_fails_loudly_when_nothing_fits():
    with pytest.raises(NoProviderAvailable):
        route([ENTRY], Requirements(20, 1280, 720), {"a"})
