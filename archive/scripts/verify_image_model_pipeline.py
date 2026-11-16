import urllib.request
import json
import time

BASE = "http://13.205.82.99"

TESTS = [
    {
        "label": "Property Broker | FLUX.2 Klein 4B | Christopher | Slow Motion",
        "payload": {
            "prompt": "MAKE AD FOR PROPERTY BROKER APP",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "image_model": "flux2_klein_4b",
            "duration_s": 15,
            "style": "Luxury Minimalist",
            "aspect_ratio": "16:9",
            "audio_voice": "en-US-ChristopherNeural",
            "motion_style": "kenburns_slow"
        },
        "expected_category": "realestate",
        "expected_image_model": "flux2_klein_4b"
    },
    {
        "label": "TerraStride Sneaker | Sana 1600M Diffusion | Aggressive Motion",
        "payload": {
            "prompt": "MAKE COMMERCIAL FOR TERRASTRIDE URBAN SNEAKER",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "image_model": "sana_1600m",
            "duration_s": 15,
            "style": "Kinetic Urban Commercial",
            "aspect_ratio": "16:9",
            "audio_voice": "en-US-ChristopherNeural",
            "motion_style": "kenburns_aggressive"
        },
        "expected_category": "sneaker",
        "expected_image_model": "sana_1600m"
    }
]

def run(tc):
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
        print(f"  [FAIL] Error: {e}")
        return False

    lat = round(time.time() - t0, 2)
    proj_id = data.get("project_id")
    category = data.get("category")
    entity = data.get("product_entity")
    img_model = data.get("image_model")
    voice = data.get("audio_voice")
    motion = data.get("motion_style")
    v_url = f"{BASE}{data.get('video_url')}"

    print(f"  Status:          {data.get('status')}")
    print(f"  Project ID:      {proj_id}")
    print(f"  Latency:         {lat}s")
    print(f"  Category:        {category}")
    print(f"  Entity:          {entity}")
    print(f"  Image Model:     {img_model}")
    print(f"  Audio Voice:     {voice}")
    print(f"  Motion Style:    {motion}")
    print(f"  Video URL:       {v_url}")

    assert category == tc["expected_category"]
    assert img_model == tc["expected_image_model"]

    # Check video head
    head = urllib.request.Request(v_url, method="HEAD")
    with urllib.request.urlopen(head) as hr:
        sz = int(hr.headers.get("Content-Length", 0))
        print(f"  Video Size:      {sz} bytes ({sz//1024}KB)")
        assert sz > 100000

    print("  [PASSED] Verified successfully!")
    return True

if __name__ == "__main__":
    for tc in TESTS:
        run(tc)
        time.sleep(1)
    print("\nALL IMAGE ENGINE TESTS PASSED!")
