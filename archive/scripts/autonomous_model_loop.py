import urllib.request, json, time, subprocess
from pathlib import Path

PROMPTS_TO_EVALUATE = [
    {
        "name": "Test 1 — Instagram Reel Ad (User Prompt)",
        "payload": {
            "prompt": "MAKE AD FOR INSTAGRAM",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Kinetic Urban Commercial",
            "aspect_ratio": "9:16"
        },
        "expected_entity": "InstaPulse AI Reel Creator Studio",
        "expected_format": "vertical",
        "forbidden": ["serum", "kettle", "sneaker", "burger"]
    },
    {
        "name": "Test 2 — Sizzling Gourmet Burger Commercial",
        "payload": {
            "prompt": "Gourmet flame-grilled Angus burger with melting aged cheddar cheese and crispy fries",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Sizzling Gourmet Food",
            "aspect_ratio": "16:9"
        },
        "expected_entity": "Prime Angus Gourmet Burger",
        "expected_format": "landscape",
        "forbidden": ["serum", "kettle", "sneaker", "instagram"]
    },
    {
        "name": "Test 3 — Apex AeroGT Sports Car Commercial",
        "payload": {
            "prompt": "Apex AeroGT twin-turbo sports car roaring through midnight city streets with neon light trails",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Hyper-Kinetic Automotive",
            "aspect_ratio": "16:9"
        },
        "expected_entity": "Apex AeroGT Twin-Turbo Sports Car",
        "expected_format": "landscape",
        "forbidden": ["serum", "kettle", "sneaker", "burger"]
    },
    {
        "name": "Test 4 — Luxury Watch Mechanical Chronograph",
        "payload": {
            "prompt": "Aethelgard titanium luxury watch with exposed mechanical tourbillon gears and sapphire glass",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "Luxury Minimalist",
            "aspect_ratio": "16:9"
        },
        "expected_entity": "Aethelgard Chronograph Luxury Timepiece",
        "expected_format": "landscape",
        "forbidden": ["serum", "burger", "coke", "sneaker"]
    },
    {
        "name": "Test 5 — Refreshing Coca-Cola Ice-Cold Commercial",
        "payload": {
            "prompt": "Ice cold Coca-Cola contour glass bottle covered in frost condensation with splashing ice cubes",
            "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "duration_s": 15,
            "style": "High-Energy Refreshment",
            "aspect_ratio": "16:9"
        },
        "expected_entity": "Coca-Cola Ice-Cold Refreshment",
        "expected_format": "landscape",
        "forbidden": ["serum", "kettle", "burger", "watch"]
    }
]

print("=================================================================")
print("  AUTONOMOUS AGENT MODEL EVALUATION & COMMERCIAL GENERATION LOOP")
print("=================================================================")

results = []

for idx, t in enumerate(PROMPTS_TO_EVALUATE, 1):
    print(f"\n[{idx}/{len(PROMPTS_TO_EVALUATE)}] Executing: {t['name']}")
    print(f"  Prompt: '{t['payload']['prompt']}'")
    
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
    
    print(f"  --> Rendered in {dt}s | Project: {proj_id}")
    print(f"  --> Entity Resolved: {entity}")
    print(f"  --> Video URL: {video_url}")
    
    # 1. Entity assertion
    assert entity == t["expected_entity"], f"Entity mismatch! Expected {t['expected_entity']}, got {entity}"
    
    # 2. Scene Traces & Contamination Check
    assert len(traces) == 3, f"Expected 3 scenes, got {len(traces)}"
    for trc in traces:
        s_num = trc["scene_num"]
        c_prompt = trc["compiled_prompt"].lower()
        print(f"     Shot {s_num}: [{trc['asset_source']}] {trc['provider']} -> {trc['compiled_prompt'][:55]}...")
        assert trc["product"] == t["expected_entity"], f"Shot {s_num} product mismatch!"
        for f_word in t["forbidden"]:
            assert f_word not in c_prompt, f"Contamination! '{f_word}' in shot {s_num} prompt: {c_prompt}"
            
    # 3. FFprobe Video & Audio Technical Verification
    local_mp4 = f"/home/ubuntu/synquic_app{video_url}"
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,codec_name,codec_type,channels,sample_rate",
        "-of", "json",
        local_mp4
    ]
    p_out = subprocess.check_output(probe_cmd).decode("utf-8")
    p_data = json.loads(p_out)
    
    v_stream = next(s for s in p_data["streams"] if s["codec_type"] == "video")
    a_stream = next(s for s in p_data["streams"] if s["codec_type"] == "audio")
    
    width = int(v_stream["width"])
    height = int(v_stream["height"])
    a_channels = int(a_stream["channels"])
    a_rate = int(a_stream["sample_rate"])
    
    print(f"  --> Technical Audit: Resolution={width}x{height} | Audio Channels={a_channels} (Stereo) | Sample Rate={a_rate}Hz")
    
    if t["expected_format"] == "vertical":
        assert height > width, f"Expected vertical 9:16 format, got {width}x{height}"
    else:
        assert width > height, f"Expected landscape 16:9 format, got {width}x{height}"
        
    assert a_channels == 2, f"Expected Stereo (2 channels), got {a_channels}"
    assert a_rate == 48000, f"Expected 48kHz audio, got {a_rate}"
    
    print(f"  [PASS] {t['name']} - VERIFIED (Correct Entity, No Contamination, Valid Video/Audio)")
    results.append({
        "test": t["name"],
        "prompt": t["payload"]["prompt"],
        "project_id": proj_id,
        "product_entity": entity,
        "video_url": video_url,
        "manifest_url": manifest_url,
        "resolution": f"{width}x{height}",
        "audio_channels": a_channels,
        "render_time_s": dt,
        "status": "PASSED"
    })

print("\n=================================================================")
print("  ALL 5 AUTONOMOUS TESTS PASSED WITH 100% RELIABILITY")
print("=================================================================")
with open("/home/ubuntu/autonomous_loop_report.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved audit report to /home/ubuntu/autonomous_loop_report.json")
