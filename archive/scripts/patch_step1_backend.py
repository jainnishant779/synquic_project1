import re

with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update imports for UploadFile and File if not already present
if "UploadFile" not in code:
    code = code.replace(
        "from fastapi import FastAPI, Request, HTTPException",
        "from fastapi import FastAPI, Request, HTTPException, UploadFile, File"
    )

# 2. Update GenerateVideoRequest
old_request_model = '''class GenerateVideoRequest(BaseModel):
    prompt: str
    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    image_model: str = "flux2_klein_4b"  # Visual / Image Generation Diffusion Engine
    audio_voice: str = "auto"   # edge-tts voice or "auto" to use profile default
    motion_style: str = "kenburns_cinematic"  # visual motion engine preset
    duration_s: int = 15
    style: str = "Luxury Minimalist"
    aspect_ratio: str = "16:9"'''

new_request_model = '''class GenerateVideoRequest(BaseModel):
    prompt: str
    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    image_model: str = "flux2_klein_4b"                 # Image Generation Model
    video_provider: str = "nvidia_nim"                  # Strictly NVIDIA NIM under Quality-First policy
    video_model: str = "wan-ai/wan2.2"                  # NVIDIA Wan2.2 14B Video NIM SOTA
    generation_mode: str = "full_ai"                    # "full_ai" or "hybrid_fallback"
    video_task: str = "image_to_video"                  # "image_to_video" (I2V) or "text_to_video" (T2V)
    resolution: str = "1080p"                           # "1080p" Full HD or "720p" HD
    aspect_ratio: str = "16:9"                          # "16:9" or "9:16"
    quality_preset: str = "high"                        # "high" (50 steps) or "standard" (30 steps)
    audio_voice: str = "auto"                           # edge-tts voice or "auto"
    motion_style: str = "kenburns_cinematic"            # Image Motion Fallback preset (FFmpeg)
    reference_assets: List[str] = []                    # Uploaded product reference asset IDs
    max_scene_attempts: int = 2
    allow_fallback: bool = False                        # When False, rejects execution if GPU host is unreachable
    duration_s: int = 15
    style: str = "Luxury Minimalist"'''

if old_request_model in code:
    code = code.replace(old_request_model, new_request_model)
    print("Replaced GenerateVideoRequest model successfully!")
else:
    print("Warning: old_request_model not found!")

# 3. Add upload reference asset endpoint right above generate_production_video
upload_endpoint_code = '''
@app.post("/api/studio/upload-reference")
async def upload_reference_asset(file: UploadFile = File(...)):
    """
    Uploads product reference imagery (packaging, bottle, sneaker, etc.)
    and stores it in the project reference vault for I2V anchoring.
    """
    REFERENCES_DIR = MEDIA_DIR / "references"
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    
    asset_id = f"ref_{uuid.uuid4().hex[:8]}"
    ext = Path(file.filename or "image.png").suffix or ".png"
    target_path = REFERENCES_DIR / f"{asset_id}{ext}"
    
    contents = await file.read()
    with open(target_path, "wb") as f:
        f.write(contents)
    os.chmod(target_path, 0o755)
        
    return {
        "status": "SUCCESS",
        "asset_id": asset_id,
        "filename": file.filename,
        "asset_url": f"/static/media/references/{asset_id}{ext}",
        "size_bytes": len(contents)
    }

'''

if "/api/studio/upload-reference" not in code:
    code = code.replace("async def generate_production_video(req: GenerateVideoRequest):", upload_endpoint_code + "async def generate_production_video(req: GenerateVideoRequest):")
    print("Added /api/studio/upload-reference endpoint!")

# 4. In generate_production_video: Add NVIDIA-only policy enforcement and Wan2.2 health check
policy_check_code = '''    # STRICT NVIDIA-ONLY QUALITY-FIRST POLICY ENFORCEMENT
    if req.video_provider != "nvidia_nim":
        raise HTTPException(
            status_code=400,
            detail=f"Provider policy violation: '{req.video_provider}' is not permitted. Only NVIDIA NIM providers ('nvidia_nim') are allowed under the Quality-First policy."
        )

    # Check NVIDIA Wan2.2 14B NIM Service Status
    wan_t2v_url = os.getenv("NVIDIA_NIM_T2V_URL", "http://127.0.0.1:8000/v1/health/ready")
    wan_i2v_url = os.getenv("NVIDIA_NIM_I2V_URL", "http://127.0.0.1:8001/v1/health/ready")
    target_wan_url = wan_i2v_url if req.video_task == "image_to_video" else wan_t2v_url
    
    is_wan_live = False
    try:
        import urllib.request
        check_req = urllib.request.Request(target_wan_url, headers={"User-Agent": "Synquic/2.0"})
        with urllib.request.urlopen(check_req, timeout=1.0) as check_resp:
            if check_resp.status == 200:
                is_wan_live = True
    except Exception:
        is_wan_live = False

    # Under Full AI mode without fallback allowed:
    if req.generation_mode == "full_ai" and not req.allow_fallback and not is_wan_live:
        return JSONResponse(
            status_code=503,
            content={
                "status": "PROVIDER_UNAVAILABLE",
                "error_code": "NVIDIA_WAN22_GPU_HOST_OFFLINE",
                "detail": (
                    f"NVIDIA Wan2.2 14B Video NIM endpoint is not accessible ({target_wan_url}). "
                    "Wan2.2 14B requires a dedicated 80GB Hopper GPU host (container: nvcr.io/nim/wan-ai/wan2.2:1.0.0). "
                    "Under Full AI Quality-First policy, silent Ken Burns substitution is prohibited. "
                    "To generate with Image Motion Fallback, enable 'Allow Image Motion Fallback' or set allow_fallback=true."
                ),
                "video_provider": "nvidia_nim",
                "video_model": req.video_model,
                "video_task": req.video_task,
                "generation_mode": req.generation_mode,
                "hardware_requirement": "NVIDIA 80GB Hopper GPU (H100/H200/A100-80GB)"
            }
        )
'''

target_policy_insert = '''    scenes_dir = project_dir / "scenes"
    project_dir.mkdir(parents=True, exist_ok=True)
    scenes_dir.mkdir(parents=True, exist_ok=True)'''

if "STRICT NVIDIA-ONLY QUALITY-FIRST POLICY ENFORCEMENT" not in code:
    code = code.replace(target_policy_insert, target_policy_insert + "\n\n" + policy_check_code)
    print("Added Policy check and Wan2.2 endpoint gate!")

with open("web_ec2/main.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Saved main.py part 1!")
