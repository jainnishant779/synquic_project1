"""
Autonomous test: verify per-engine model selectors work end-to-end.
Tests:
1. Property Broker with British Voice (en-GB-RyanNeural) + Slow Motion
2. Sports Car with Aggressive Motion + Christopher (Male US)
3. Gourmet Burger with Dolly Motion + Aria (Female US)
"""
import urllib.request
import json
import time

BASE = "http://13.205.82.99"

TESTS = [
    {
        "label": "Property Broker | British Voice + Slow Motion",
        "payload": {
            "prompt": "MAKE AD FOR PROPERTY BROKER APP",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Luxury Minimalist",
            "aspect_ratio": "16:9",
            "audio_voice": "en-GB-RyanNeural",
            "motion_style": "kenburns_slow"
        },
        "expected_category": "realestate",
        "expected_entity": "PrimeEstate",
        "expected_voice": "en-GB-RyanNeural",
        "expected_motion": "kenburns_slow"
    },
    {
        "label": "Sports Car | Aggressive Motion + Christopher",
        "payload": {
            "prompt": "MAKE AD FOR LUXURY SPORTS CAR",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Kinetic Urban Commercial",
            "aspect_ratio": "16:9",
            "audio_voice": "en-US-ChristopherNeural",
            "motion_style": "kenburns_aggressive"
        },
        "expected_category": "car",
        "expected_entity": "Apex",
        "expected_voice": "en-US-ChristopherNeural",
        "expected_motion": "kenburns_aggressive"
    },
    {
        "label": "Gourmet Burger | Dolly Motion + Aria (auto voice)",
        "payload": {
            "prompt": "MAKE AD FOR GOURMET BURGER",
            "director_model": "writer/palmyra-creative-122b",
            "duration_s": 15,
            "style": "Warm Artisanal Lifestyle",
            "aspect_ratio": "16:9",
            "audio_voice": "auto",
            "motion_style": "kenburns_dolly"
        },
        "expected_category": "burger",
        "expected_entity": "Angus",
        "expected_voice": None,  # auto = profile default
        "expected_motion": "kenburns_dolly"
    }
]

def run_test(tc):
    print(f"\n{'='*60}")
    print(f"TEST: {tc['label']}")
    print(f"{'='*60}")

    req = urllib.request.Request(
        f"{BASE}/api/studio/generate",
        data=json.dumps(tc["payload"]).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [FAIL] HTTP error: {e}")
        return False

    lat = round(time.time() - t0, 2)
    proj_id = data.get("project_id")
    category = data.get("category")
    entity = data.get("product_entity", "")
    voice = data.get("audio_voice", "")
    motion = data.get("motion_style", "")
    video_url = f"{BASE}{data.get('video_url', '')}"

    print(f"  Status:          {data.get('status')}")
    print(f"  Project ID:      {proj_id}")
    print(f"  Latency:         {lat}s")
    print(f"  Category:        {category}")
    print(f"  Entity:          {entity}")
    print(f"  Audio Voice:     {voice}")
    print(f"  Motion Style:    {motion}")
    print(f"  Director Model:  {tc['payload']['director_model']}")
    print(f"  Video URL:       {video_url}")

    # Assertions
    assert category == tc["expected_category"], f"Category mismatch: {category} != {tc['expected_category']}"
    assert tc["expected_entity"].lower() in entity.lower(), f"Entity mismatch: {entity}"
    assert motion == tc["expected_motion"], f"Motion style mismatch: {motion} != {tc['expected_motion']}"
    if tc["expected_voice"]:
        assert voice == tc["expected_voice"], f"Voice mismatch: {voice} != {tc['expected_voice']}"

    # Verify video accessible
    head_req = urllib.request.Request(video_url, method="HEAD")
    with urllib.request.urlopen(head_req, timeout=10) as vr:
        size = int(vr.headers.get("Content-Length", 0))
        assert size > 100000, f"Video too small: {size} bytes"
        print(f"  Video Size:      {size} bytes ({size//1024}KB)")

    print(f"  [SUCCESS] All assertions passed!")
    return True

if __name__ == "__main__":
    print("Synquic Per-Engine Model Selector — Autonomous Verification")
    results = []
    for tc in TESTS:
        ok = run_test(tc)
        results.append((tc["label"], ok))
        time.sleep(1)

    print(f"\n{'='*60}")
    print("RESULTS SUMMARY")
    print(f"{'='*60}")
    for label, ok in results:
        print(f"  [{'PASSED' if ok else 'FAILED'}] {label}")
    
    if all(ok for _, ok in results):
        print("\nALL TESTS PASSED — Per-engine model selector working perfectly!")
    else:
        print("\nSOME TESTS FAILED")
