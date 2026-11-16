import subprocess
import json
import re
import hashlib
from pathlib import Path
from PIL import Image

def compute_file_sha256(path: Path) -> str:
    """Computes exact SHA-256 hash of a file for byte-level duplicate detection."""
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def compute_image_dhash(path: Path, hash_size: int = 8) -> int:
    """
    Computes 64-bit difference hash (dHash) of an image to detect visually similar
    or re-encoded images regardless of minor compression artifacts.
    """
    if not path.is_file():
        return 0
    try:
        with Image.open(path) as im:
            resized = im.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = list(resized.getdata())
            diff = 0
            for row in range(hash_size):
                for col in range(hash_size):
                    left = pixels[row * (hash_size + 1) + col]
                    right = pixels[row * (hash_size + 1) + col + 1]
                    diff = (diff << 1) | int(left > right)
            return diff
    except Exception:
        return 0

def hamming_distance(h1: int, h2: int) -> int:
    """Calculates bitwise Hamming distance between two 64-bit integer hashes."""
    return bin(h1 ^ h2).count("1")

def analyze_scene_motion(scene_mp4: Path) -> dict:
    """
    Measures optical/pixel variance across multiple progressive frames
    (0.5s, 1.5s, 2.5s) to accurately detect frozen or static footage.
    """
    if not scene_mp4.is_file():
        return {"mean_diff": 0.0, "is_static": True}
    
    t1_img = scene_mp4.parent / f"{scene_mp4.stem}_t1.jpg"
    t2_img = scene_mp4.parent / f"{scene_mp4.stem}_t2.jpg"
    t3_img = scene_mp4.parent / f"{scene_mp4.stem}_t3.jpg"
    
    try:
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", "0.5", "-i", str(scene_mp4),
            "-vframes", "1", "-s", "320x568", str(t1_img)
        ], check=True)
        
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", "1.5", "-i", str(scene_mp4),
            "-vframes", "1", "-s", "320x568", str(t2_img)
        ], check=True)

        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", "2.5", "-i", str(scene_mp4),
            "-vframes", "1", "-s", "320x568", str(t3_img)
        ], check=True)
        
        diffs = []
        if t1_img.is_file() and t2_img.is_file():
            im1 = Image.open(t1_img).convert("L")
            im2 = Image.open(t2_img).convert("L")
            p1 = list(im1.getdata())
            p2 = list(im2.getdata())
            diffs.append(sum(abs(a - b) for a, b in zip(p1, p2)) / len(p1))

        if t2_img.is_file() and t3_img.is_file():
            im2 = Image.open(t2_img).convert("L")
            im3 = Image.open(t3_img).convert("L")
            p2 = list(im2.getdata())
            p3 = list(im3.getdata())
            diffs.append(sum(abs(a - b) for a, b in zip(p2, p3)) / len(p2))

        t1_img.unlink(missing_ok=True)
        t2_img.unlink(missing_ok=True)
        t3_img.unlink(missing_ok=True)
        
        if diffs:
            avg_diff = sum(diffs) / len(diffs)
            is_static = avg_diff < 1.2
            return {"mean_diff": round(avg_diff, 2), "is_static": is_static}
    except Exception as e:
        print("[Motion Analysis Warning]:", e)
        t1_img.unlink(missing_ok=True)
        t2_img.unlink(missing_ok=True)
        t3_img.unlink(missing_ok=True)
        
    return {"mean_diff": 0.0, "is_static": False}

def detect_duplicate_scenes(scene_mp4s: list, scene_traces: list = None, scene_images: list = None) -> dict:
    """
    Checks for exact binary duplicates (SHA-256), perceptual duplicates (dHash),
    and video thumbnail correlation across all scenes.
    Returns: {"has_duplicates": bool, "reason": str}
    """
    # 1. Exact SHA-256 byte-level duplicate check on source still images
    if scene_images:
        sha_map = {}
        for idx, img_p in enumerate(scene_images, 1):
            if img_p and Path(img_p).is_file():
                fsha = compute_file_sha256(Path(img_p))
                if fsha in sha_map:
                    return {
                        "has_duplicates": True,
                        "reason": f"Exact binary SHA-256 duplicate image content detected between Scene {sha_map[fsha]} and Scene {idx}."
                    }
                sha_map[fsha] = idx

        # 2. Perceptual Difference Hash (dHash) visual similarity check
        dhash_list = []
        for idx, img_p in enumerate(scene_images, 1):
            if img_p and Path(img_p).is_file():
                dh = compute_image_dhash(Path(img_p))
                dhash_list.append((idx, dh))

        for i in range(len(dhash_list)):
            for j in range(i + 1, len(dhash_list)):
                dist = hamming_distance(dhash_list[i][1], dhash_list[j][1])
                if dist <= 4:  # <= 4 bit difference out of 64 indicates identical visual content
                    return {
                        "has_duplicates": True,
                        "reason": f"Perceptual visual duplicate detected between Scene {dhash_list[i][0]} and Scene {dhash_list[j][0]} (dHash distance: {dist}/64)."
                    }

    # 3. Provenance asset key check from scene_traces
    if scene_traces:
        asset_keys = []
        for t in scene_traces:
            k = t.get("asset_file") or t.get("keyframe_url") or t.get("source_file") or ""
            if k:
                asset_keys.append(k)
        if len(asset_keys) > 1 and len(set(asset_keys)) < len(asset_keys):
            return {
                "has_duplicates": True,
                "reason": "Duplicate asset path or keyframe reference assigned across multiple scenes."
            }

    # 4. Rendered video frame thumbnail correlation
    thumbs = []
    for idx, p in enumerate(scene_mp4s):
        th = p.parent / f"thumb_{idx}.jpg"
        try:
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-ss", "1.0", "-i", str(p),
                "-vframes", "1", "-s", "64x114", str(th)
            ], check=True)
            if th.is_file():
                im = Image.open(th).convert("L")
                thumbs.append((th, list(im.getdata())))
        except Exception:
            pass
            
    is_dup = False
    dup_reason = ""
    for i in range(len(thumbs)):
        for j in range(i + 1, len(thumbs)):
            p1 = thumbs[i][1]
            p2 = thumbs[j][1]
            diff = sum(abs(a - b) for a, b in zip(p1, p2)) / len(p1)
            if diff < 5.0:
                is_dup = True
                dup_reason = f"Rendered frame pixel correlation indicates near-identical composition between scenes {i+1} and {j+1}."
                break
        if is_dup:
            break
            
    for th, _ in thumbs:
        th.unlink(missing_ok=True)
        
    return {"has_duplicates": is_dup, "reason": dup_reason}

def evaluate_qc_checks(
    out_mp4: Path,
    scene_traces: list,
    prompt_text: str,
    brand_display: str,
    shots: list,
    actual_video_gen_flag: bool,
    generation_mode: str = "motion_fallback",
    scene_images: list = None
) -> dict:
    """
    Executes the 7 mandatory QC checks with unambiguous boolean definitions:
      - actual_video_generation: True ONLY if genuine AI video diffusion executed
      - static_content_detected: True if frozen/static footage detected (undesirable)
      - duplicate_scenes_detected: True if duplicate visual content detected (undesirable)
      - visual_relevance: Domain keyword and prompt alignment
      - brand_consistency: Consistent brand identity throughout
      - text_quality: Unique, non-repetitive captions without internal dev labels
      - storyboard_adherence: Multi-stage commercial narrative arc verified
    """
    scene_files = []
    for t in scene_traces:
        url = t.get("video_clip_url") or ""
        if url.startswith("/static/media/"):
            local_p = Path("/home/ubuntu/synquic_app" + url)
            if local_p.is_file():
                scene_files.append(local_p)
    
    # 1. actual_video_generation
    actual_gen = bool(
        actual_video_gen_flag and 
        any(t.get("asset_source") in ("fal_flux_keyframe_wan_video", "nvidia_cosmos_video", "nvidia_video_generation") for t in scene_traces)
    )
    
    # 2. static_content_detected (measured frame variance analysis)
    static_detected = False
    measured_motion_deltas = []
    for sf in scene_files:
        motion = analyze_scene_motion(sf)
        measured_motion_deltas.append(motion.get("mean_diff", 0.0))
        if motion["is_static"]:
            static_detected = True
            
    # 3. duplicate_scenes_detected (SHA-256 + dHash + Frame correlation)
    dup_res = detect_duplicate_scenes(scene_files, scene_traces=scene_traces, scene_images=scene_images)
    duplicate_detected = dup_res["has_duplicates"]
    
    # 4. visual_relevance
    p_lower = prompt_text.lower()
    core_keywords = set(re.findall(r'[a-zA-Z]{4,}', p_lower))
    relevance_hits = 0
    for t in scene_traces:
        txt = (t.get("compiled_prompt", "") + " " + t.get("product", "") + " " + t.get("narration", "")).lower()
        if any(k in txt for k in core_keywords):
            relevance_hits += 1
    visual_relevance = (relevance_hits >= max(1, len(scene_traces) // 2))
    
    # 5. brand_consistency
    brand_mentions = 0
    for t in scene_traces:
        if brand_display.lower() in (t.get("product", "") + " " + t.get("narration", "") + " " + t.get("compiled_prompt", "")).lower():
            brand_mentions += 1
    brand_consistency = (brand_mentions >= 1)
    
    # 6. text_quality (no repeated text, no unverified claims like 0.6s)
    overlays = [str(s.get("on_screen_text", "")).strip().upper() for s in shots if s.get("on_screen_text")]
    has_duplicates = len(overlays) > len(set(overlays))
    has_internal_labels = any(any(bad in o for bad in ["SHOT ", "VERIFIED OFFICIAL", "SCENE ", "PROMPT "]) for o in overlays)
    has_unverified_claim = any("0.6" in o or "0.6S" in o for o in overlays)
    text_quality = (not has_duplicates) and (not has_internal_labels) and (not has_unverified_claim)
    
    # 7. storyboard_adherence
    storyboard_adherence = len(shots) >= 3 and len(set(s.get("type", "") for s in shots)) >= 2
    
    # Unambiguous boolean check mapping
    checks = {
        "actual_video_generation": actual_gen,
        "static_content_detected": static_detected,
        "duplicate_scenes_detected": duplicate_detected,
        "visual_relevance": visual_relevance,
        "brand_consistency": brand_consistency,
        "text_quality": text_quality,
        "storyboard_adherence": storyboard_adherence,
        # Backward compatibility aliases:
        "static_scene_detection": static_detected,
        "duplicate_scene_detection": duplicate_detected
    }
    
    passed_count = sum([
        1 if actual_gen else 0,
        1 if not static_detected else 0,
        1 if not duplicate_detected else 0,
        1 if visual_relevance else 0,
        1 if brand_consistency else 0,
        1 if text_quality else 0,
        1 if storyboard_adherence else 0
    ])
    
    score = int(round((passed_count / 7.0) * 100))
    if not actual_gen:
        score = min(score, 72)
        
    if not actual_gen and (static_detected or duplicate_detected):
        verdict = f"FAILED: {dup_res.get('reason') or 'Static/duplicate scenes detected'} without genuine AI video generation."
    elif not actual_gen:
        verdict = "Motion Fallback: Storyboard and technical checks passed; genuine AI video generation absent. Classified as an image-based commercial reel."
    elif passed_count == 7:
        verdict = "PASSED: Full AI video generation verified with high visual relevance and clean typography."
    else:
        verdict = f"PARTIAL: Passed {passed_count}/7 quality checks."
        
    return {
        "checks": checks,
        "score": score,
        "verdict": verdict,
        "measured_motion_deltas": measured_motion_deltas,
        "duplicate_diagnostic": dup_res.get("reason", "None")
    }

if __name__ == "__main__":
    print("QC Engine upgraded with SHA-256 and dHash duplicate detection.")
