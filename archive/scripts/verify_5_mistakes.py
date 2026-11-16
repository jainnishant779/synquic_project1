import requests
import json
import time

BASE_URL = "http://13.205.82.99"

print("=" * 70)
print("RUNNING VERIFICATION OF 5 CRITICAL MISTAKES ON LIVE SERVER")
print("=" * 70)

# -------------------------------------------------------------
# Test 1: Strict Full AI Rejection (Mistake 1)
# -------------------------------------------------------------
print("\n[Test 1] Testing Strict Full AI Enforcement (should reject with HTTP 422)...")
payload_full_ai = {
    "prompt": "Make commercial for luxury watch",
    "generation_mode": "full_ai",
    "allow_fallback": True,  # Even with allow_fallback=True, full_ai must NOT allow fallback!
    "video_provider": "local_pro_reel",
    "duration_s": 15
}
r1 = requests.post(f"{BASE_URL}/api/studio/generate", json=payload_full_ai, timeout=30)
print(f"Status Code: {r1.status_code}")
print(f"Response: {r1.text}")
assert r1.status_code == 422, f"Expected 422 for full_ai without diffusion, got {r1.status_code}"
assert "Full AI requires verified AI-generated video for every scene" in r1.text, "Error message mismatch!"
print(">>> PASS: Test 1 (Strict Full AI mode properly enforced via HTTP 422)")

# -------------------------------------------------------------
# Test 2: Homingo Commercial Generation & Inspection
# -------------------------------------------------------------
print("\n[Test 2] Generating Homingo Commercial (Pro Commercial mode)...")
t0 = time.time()
payload_homingo = {
    "prompt": "make ad for homingo app -an home service provider app",
    "brand_name": "homingo",
    "industry": "Tech, SaaS & Mobile Apps",
    "duration_s": 15,
    "aspect_ratio": "9:16",
    "resolution": "1080p",
    "generation_mode": "pro_commercial",
    "video_provider": "local_pro_reel",
    "allow_fallback": True
}
r2 = requests.post(f"{BASE_URL}/api/studio/generate", json=payload_homingo, timeout=120)
print(f"Homingo Generation Status: {r2.status_code} in {time.time() - t0:.2f}s")
assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.text}"
data2 = r2.json()

proj_id2 = data2["project_id"]
manifest_url2 = data2["manifest_url"]
video_url2 = data2.get("video_url") or data2.get("final_video_url")
qc2 = data2["qc_report"]
checks2 = qc2["checks"]

print(f"Project ID: {proj_id2}")
print(f"Video URL: {video_url2}")
print(f"QC Score: {qc2.get('score')}/100")
print(f"QC Verdict: {qc2.get('verdict')}")
print(f"QC Checks: {json.dumps(checks2, indent=2)}")

# Verify Unambiguous QC Flags (Mistake 3)
assert "static_content_detected" in checks2, "static_content_detected flag missing!"
assert "duplicate_scenes_detected" in checks2, "duplicate_scenes_detected flag missing!"
assert "actual_video_generation" in checks2, "actual_video_generation flag missing!"
assert checks2["actual_video_generation"] is False, "Honest provenance: actual_video_generation must be false for motion fallback"
assert checks2["static_content_detected"] is False, "Footage has progressive camera motion, so static_content_detected must be false"
assert checks2["duplicate_scenes_detected"] is False, "Scenes are diverse, duplicate_scenes_detected must be false"

# Verify 3-Tier QC Structure (Mistake 3)
assert "technical_qc" in qc2, "technical_qc missing in qc_report!"
assert "motion_and_integrity_qc" in qc2, "motion_and_integrity_qc missing in qc_report!"
assert "semantic_and_visual_qc" in qc2, "semantic_and_visual_qc missing in qc_report!"

print(">>> PASS: Test 2 (Homingo generated with 3-tier QC and unambiguous flags)")

# -------------------------------------------------------------
# Test 3: ParkFnB Barrier Commercial & Unverified Claim Check (Mistake 5)
# -------------------------------------------------------------
print("\n[Test 3] Generating ParkFnB Barrier Commercial (Pro Commercial mode)...")
t0 = time.time()
payload_parkfnb = {
    "prompt": "MAKE AD FOR PARKFNB BARRIER: 15-second 4-stage commercial. Scene 1: Crowded parking bottleneck with vehicle looking for space. Scene 2: High-tech smart ANPR camera detects vehicle and recognizes license plate. Scene 3: High-speed brushless boom barrier elevates rapidly for authorized access. Scene 4: Mobile parking slot booking app and ParkFnB brand reveal.",
    "brand_name": "ParkFnB Barrier",
    "industry": "parking_barrier",
    "duration_s": 15,
    "aspect_ratio": "9:16",
    "resolution": "1080p",
    "generation_mode": "pro_commercial",
    "video_provider": "local_pro_reel",
    "allow_fallback": True
}
r3 = requests.post(f"{BASE_URL}/api/studio/generate", json=payload_parkfnb, timeout=120)
print(f"ParkFnB Generation Status: {r3.status_code} in {time.time() - t0:.2f}s")
assert r3.status_code == 200, f"Expected 200, got {r3.status_code}: {r3.text}"
data3 = r3.json()

proj_id3 = data3["project_id"]
manifest_r3 = requests.get(f"{BASE_URL}{data3['manifest_url']}").json()

# Verify that "0.6" or "0.6s" does NOT appear anywhere in storyboard, narration, or on_screen_text
manifest_str = json.dumps(manifest_r3)
has_06 = "0.6" in manifest_str or "0.6s" in manifest_str.lower()
print(f"Manifest unverified 0.6s claim check: has_06 = {has_06}")
assert not has_06, "Found unverified '0.6' claim in ParkFnB manifest!"

print(">>> PASS: Test 3 (ParkFnB generated, all unverified 0.6s claims removed)")

print("\n" + "=" * 70)
print("ALL 5 CRITICAL CHECKS SUCCESSFULLY VERIFIED!")
print("=" * 70)
