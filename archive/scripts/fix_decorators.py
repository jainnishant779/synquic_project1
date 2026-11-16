with open("web_ec2/main.py", "r", encoding="utf-8") as f:
    code = f.read()

target = '''@app.post("/api/studio/generate")

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

async def generate_production_video(req: GenerateVideoRequest):'''

replacement = '''@app.post("/api/studio/upload-reference")
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

@app.post("/api/studio/generate")
async def generate_production_video(req: GenerateVideoRequest):'''

if target in code:
    code = code.replace(target, replacement)
    with open("web_ec2/main.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Fixed decorator order cleanly!")
else:
    print("Warning: target pattern not matched!")
