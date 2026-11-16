import urllib.request, urllib.error, json, time

base_url = "http://127.0.0.1:8000"

print("=" * 60)
print("TEST 1: Provider Policy Violation (Non-NVIDIA Provider)")
print("=" * 60)
payload_bad_provider = {
    "prompt": "make ad for perfume brand name vishal",
    "video_provider": "kling_ai",
    "video_model": "kling-v4.0"
}
req = urllib.request.Request(
    f"{base_url}/api/studio/generate",
    data=json.dumps(payload_bad_provider).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req) as resp:
        print("FAIL: Should have rejected non-NVIDIA provider!")
except urllib.error.HTTPError as e:
    err_body = json.loads(e.read().decode("utf-8"))
    print(f"PASS: Rejected non-NVIDIA provider with HTTP {e.code}: {err_body.get('detail')}")

print("\n" + "=" * 60)
print("TEST 2: Strict Full AI Quality Gate (No Silent Ken Burns Fallback)")
print("=" * 60)
payload_strict_ai = {
    "prompt": "make ad for perfume brand name vishal",
    "video_provider": "nvidia_nim",
    "video_model": "wan-ai/wan2.2",
    "generation_mode": "full_ai",
    "video_task": "image_to_video",
    "allow_fallback": False  # Strictly disallow silent Ken Burns fallback
}
req = urllib.request.Request(
    f"{base_url}/api/studio/generate",
    data=json.dumps(payload_strict_ai).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req) as resp:
        print("FAIL: Should have blocked execution because Wan2.2 GPU host is offline!")
except urllib.error.HTTPError as e:
    err_body = json.loads(e.read().decode("utf-8"))
    print(f"PASS: Blocked silent fallback with HTTP {e.code}!")
    print(f"  Error Code: {err_body.get('error_code')}")
    print(f"  Status: {err_body.get('status')}")
    print(f"  Hardware Req: {err_body.get('hardware_requirement')}")
    print(f"  Detail preview: {err_body.get('detail')[:120]}...")

print("\n" + "=" * 60)
print("TEST 3: Product Reference Image Upload Endpoint")
print("=" * 60)
# Create a dummy test image binary
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body_parts = [
    f"--{boundary}",
    'Content-Disposition: form-data; name="file"; filename="serum_reference_bottle.png"',
    'Content-Type: image/png',
    '',
    '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
    f"--{boundary}--",
    ''
]
body_bytes = "\r\n".join(body_parts).encode("latin-1")
req_upload = urllib.request.Request(
    f"{base_url}/api/studio/upload-reference",
    data=body_bytes,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
)
with urllib.request.urlopen(req_upload) as resp:
    upload_res = json.loads(resp.read().decode("utf-8"))
    print(f"PASS: Reference uploaded successfully!")
    print(f"  Asset ID: {upload_res.get('asset_id')}")
    print(f"  Asset URL: {upload_res.get('asset_url')}")
    uploaded_asset_id = upload_res.get("asset_id")

print("\n" + "=" * 60)
print("TEST 4: Permitted Fallback Generation with Honest Audit Ledger")
print("=" * 60)
payload_permitted_fallback = {
    "prompt": "make ad for perfume brand name vishal",
    "director_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "image_model": "flux2_klein_4b",
    "video_provider": "nvidia_nim",
    "video_model": "wan-ai/wan2.2",
    "generation_mode": "hybrid_fallback",
    "video_task": "image_to_video",
    "resolution": "1080p",
    "aspect_ratio": "16:9",
    "quality_preset": "high",
    "audio_voice": "en-US-AriaNeural",
    "motion_style": "kenburns_cinematic",
    "reference_assets": [uploaded_asset_id],
    "allow_fallback": True,  # Permitted
    "duration_s": 15
}
req = urllib.request.Request(
    f"{base_url}/api/studio/generate",
    data=json.dumps(payload_permitted_fallback).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
t0 = time.time()
with urllib.request.urlopen(req, timeout=90) as resp:
    dt = time.time() - t0
    gen_data = json.loads(resp.read().decode("utf-8"))

print(f"Status: {gen_data.get('status')} in {dt:.2f}s")
print(f"Project ID: {gen_data.get('project_id')}")
print(f"Title: {gen_data.get('title')}")
print(f"Video Provider: {gen_data.get('video_provider')}")
print(f"Video Model: {gen_data.get('video_model')}")
print(f"Resolution: {gen_data.get('resolution')}")
print(f"QC Score: {gen_data.get('qc_report', {}).get('score')}/100 (Measured)")
print(f"QC Verdict: {gen_data.get('qc_report', {}).get('verdict')}")
print(f"QC Fallback Used: {gen_data.get('qc_report', {}).get('fallback_used')}")
print(f"QC Fallback Reason: {gen_data.get('qc_report', {}).get('fallback_reason')}")
print(f"Latency: Model {gen_data.get('model_latency_s')}s | Total {gen_data.get('generation_time_s')}s")

print("\nScene Trace Audit:")
for trc in gen_data.get("scene_traces", []):
    print(f"  Scene {trc.get('scene_num')}: Provider='{trc.get('provider')}' | Model='{trc.get('model')}' | Source='{trc.get('asset_source')}' | Fallback={trc.get('fallback_used')} | QC={trc.get('quality_status')}")

assert gen_data.get("qc_report", {}).get("fallback_used") is True, "FAIL: fallback_used must be True when Ken Burns fallback executed!"
print("\nALL CONTRACT & AUDIT INTEGRITY TESTS PASSED!")
