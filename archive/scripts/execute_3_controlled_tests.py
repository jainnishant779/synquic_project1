import urllib.request, json, time

TESTS = [
    {
        "name": "Test A — Serum",
        "payload": {
            "prompt": "Create a luxury botanical serum commercial for AuraGlow 30ml Botanical Face Serum, golden hour morning light, soft bokeh, organic skincare ritual",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Luxury Minimalist",
            "aspect_ratio": "16:9"
        },
        "expected_product": "AuraGlow Botanical Serum",
        "forbidden_keywords": ["sneaker", "shoe", "kettle", "mug"]
    },
    {
        "name": "Test B — Sneaker",
        "payload": {
            "prompt": "High-energy urban commercial for TerraStride Eco-Runner sneaker on rain-slick city asphalt with neon reflections and slow-motion water splash",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Kinetic Urban Commercial",
            "aspect_ratio": "16:9"
        },
        "expected_product": "TerraStride Eco-Runner",
        "forbidden_keywords": ["serum", "skincare", "kettle", "botanical"]
    },
    {
        "name": "Test C — Kettle",
        "payload": {
            "prompt": "Artisanal morning commercial for Northwind Matte Enamel Kettle with walnut handle, steam rising, pouring hot water into pour-over in sunlit kitchen",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Warm Artisanal Lifestyle",
            "aspect_ratio": "16:9"
        },
        "expected_product": "Northwind Matte Enamel Kettle",
        "forbidden_keywords": ["serum", "sneaker", "shoe", "skin"]
    }
]

print("=== STARTING 3 CONTROLLED TESTS ===")
results = []

for t in TESTS:
    print(f"\n--- Running: {t['name']} ---")
    t0 = time.time()
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/studio/generate",
        data=json.dumps(t["payload"]).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        
    dt = round(time.time() - t0, 2)
    proj_id = data.get("project_id")
    entity = data.get("product_entity")
    video_url = data.get("video_url")
    manifest_url = data.get("manifest_url")
    traces = data.get("scene_traces", [])
    
    print(f"Project ID: {proj_id} ({dt}s)")
    print(f"Product Entity: {entity}")
    print(f"Video URL: {video_url}")
    print(f"Manifest URL: {manifest_url}")
    print(f"Scenes Count: {len(traces)}")
    
    # Audit assertions
    assert entity == t["expected_product"], f"Entity mismatch: expected {t['expected_product']}, got {entity}"
    assert len(traces) == 3, f"Expected 3 scenes, got {len(traces)}"
    
    for trc in traces:
        s_num = trc["scene_num"]
        p_name = trc["product"]
        c_prompt = trc["compiled_prompt"].lower()
        src = trc["asset_source"]
        fb = trc["fallback_used"]
        print(f"  Scene {s_num}: [{src}] {trc['provider']} ({trc['model']}) -> {trc['compiled_prompt'][:60]}... | Fallback: {fb}")
        
        assert p_name == t["expected_product"], f"Scene {s_num} product mismatch!"
        assert fb is False, f"Scene {s_num} had fallback_used = True!"
        
        # Check forbidden cross-contamination keywords
        for f_word in t["forbidden_keywords"]:
            assert f_word not in c_prompt, f"Contamination detected! '{f_word}' found in scene {s_num} prompt: {c_prompt}"
            
    print(f"RESULT: {t['name']} PASSED (Zero Contamination, Isolated Assets, Valid Traces)")
    results.append({
        "test": t["name"],
        "project_id": proj_id,
        "product_entity": entity,
        "video_url": video_url,
        "manifest_url": manifest_url,
        "dt": dt,
        "traces": traces
    })

print("\n=== ALL 3 CONTROLLED TESTS COMPLETED SUCCESSFULLY ===")
with open("/home/ubuntu/controlled_tests_report.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved report to /home/ubuntu/controlled_tests_report.json")
