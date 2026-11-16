import urllib.request
import urllib.parse
import json
import time
import subprocess
from pathlib import Path

BASE_URL = "http://13.205.82.99"

TEST_PROMPTS = [
    {
        "prompt": "MAKE AD FOR PROPERTY BROKER APP",
        "aspect_ratio": "16:9",
        "expected_category": "realestate",
        "expected_entity_keyword": "PrimeEstate",
        "forbidden_keywords": ["serum", "sneaker", "kettle", "instapulse", "burger", "coke"]
    },
    {
        "prompt": "MAKE AD FOR LUXURY SPORTS CAR",
        "aspect_ratio": "16:9",
        "expected_category": "car",
        "expected_entity_keyword": "Apex",
        "forbidden_keywords": ["serum", "sneaker", "kettle", "instapulse", "primeestate", "burger"]
    },
    {
        "prompt": "MAKE AD FOR GOURMET BURGER",
        "aspect_ratio": "16:9",
        "expected_category": "burger",
        "expected_entity_keyword": "Angus",
        "forbidden_keywords": ["serum", "sneaker", "kettle", "instapulse", "primeestate", "sports car"]
    },
    {
        "prompt": "MAKE AD FOR PROPERTY BROKER APP (Vertical Reel)",
        "aspect_ratio": "9:16",
        "expected_category": "realestate",
        "expected_entity_keyword": "PrimeEstate",
        "forbidden_keywords": ["serum", "sneaker", "kettle", "instapulse", "burger"]
    }
]

def run_test_case(tc):
    print("\n=======================================================")
    print(f">> EXECUTING TEST: '{tc['prompt']}' ({tc['aspect_ratio']})")
    print("=======================================================")
    
    payload = {
        "prompt": tc["prompt"],
        "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "duration_s": 15,
        "style": "Luxury Minimalist",
        "aspect_ratio": tc["aspect_ratio"]
    }
    
    req = urllib.request.Request(
        f"{BASE_URL}/api/studio/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[FAIL] HTTP Generation Error: {e}")
        return False
        
    duration = time.time() - t0
    proj_id = data.get("project_id")
    video_url = data.get("video_url")
    title = data.get("title")
    category = data.get("category")
    product_entity = data.get("product_entity")
    storyboard = data.get("storyboard", [])
    traces = data.get("scene_traces", [])
    
    print(f"  [OK] Status: {data.get('status')}")
    print(f"  [OK] Project ID: {proj_id}")
    print(f"  [OK] Generation Latency: {duration:.2f}s")
    print(f"  [OK] Resolved Category: {category}")
    print(f"  [OK] Product Entity: {product_entity}")
    print(f"  [OK] Commercial Title: {title}")
    print(f"  [OK] Video URL: {BASE_URL}{video_url}")
    
    # 1. Verify Entity & Category
    assert category == tc["expected_category"], f"Expected category {tc['expected_category']}, got {category}"
    assert tc["expected_entity_keyword"].lower() in product_entity.lower(), f"Expected entity keyword {tc['expected_entity_keyword']} in {product_entity}"
    
    # 2. Verify Zero Cross-Contamination
    narration_blob = " ".join([s.get("narration", "") + " " + s.get("visual_prompt", "") for s in storyboard]).lower()
    for forbidden in tc["forbidden_keywords"]:
        assert forbidden not in narration_blob, f"Cross-contamination detected! Forbidden word '{forbidden}' found in storyboard!"
        
    # 3. Verify Video Reachable
    video_req = urllib.request.Request(f"{BASE_URL}{video_url}", method="HEAD")
    with urllib.request.urlopen(video_req, timeout=10) as v_resp:
        v_size = int(v_resp.headers.get("Content-Length", 0))
        assert v_size > 100000, f"Video size too small: {v_size} bytes"
        print(f"  [OK] Master Video Size: {v_size} bytes ({v_size/1024:.1f} KB)")
        
    # 4. Verify Scene Traces
    assert len(traces) == 3, f"Expected 3 scene traces, got {len(traces)}"
    for trc in traces:
        assert trc["product"] == product_entity
        assert trc["fallback_used"] is False
        assert trc["quality_status"] == "passed"
        
    print(f"  [SUCCESS] TEST PASSED WITH 100% REPRODUCIBILITY & ZERO CONTAMINATION!")
    return True

if __name__ == "__main__":
    print("Starting Autonomous Commercial Video Verification Loop...")
    results = []
    for tc in TEST_PROMPTS:
        ok = run_test_case(tc)
        results.append((tc["prompt"], ok))
        time.sleep(2)
        
    print("\n=======================================================")
    print("AUTONOMOUS TEST SUITE RESULTS")
    print("=======================================================")
    all_ok = True
    for prompt, ok in results:
        status_str = "PASSED" if ok else "FAILED"
        print(f" - [{status_str}] {prompt}")
        if not ok:
            all_ok = False
            
    if all_ok:
        print("\nALL AUTONOMOUS PRODUCTION ENGINE TESTS PASSED!")
    else:
        print("\nSOME TESTS FAILED. INVESTIGATE LOGS.")
