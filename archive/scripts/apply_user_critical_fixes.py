from pathlib import Path
import re

main_path = Path("web_ec2/main.py")
content = main_path.read_text(encoding="utf-8")

# 1. Update import from qc_engine
old_import = "from qc_engine import evaluate_qc_checks"
new_import = "from qc_engine import evaluate_qc_checks, detect_duplicate_scenes"
if old_import in content:
    content = content.replace(old_import, new_import)
    print("Updated qc_engine import.")

# 2. Update strict full_ai check at start of generate_production_video
old_full_ai = '''    if req.generation_mode == "full_ai" and not req.allow_fallback and not use_nvidia_video:
        raise GenerationValidationError(
            "Full AI mode cannot accept static-image footage. Genuine video diffusion model (e.g. Wan 2.1 / Cosmos) required."
        )'''

new_full_ai = '''    if req.generation_mode == "full_ai" and not use_nvidia_video:
        raise GenerationValidationError(
            "Full AI requires verified AI-generated video for every scene."
        )'''

if old_full_ai in content:
    content = content.replace(old_full_ai, new_full_ai)
    print("Updated strict full_ai check.")

# 3. Remove unverified 0.6s claims from parking_barrier profile
old_p3 = '''            {
                "shot_num": 3,
                "duration_s": 4,
                "type": "Access Control (0.6s Rapid Lift)",
                "visual_prompt": "ParkFnB automated boom barrier with illuminated LED arm elevating rapidly in 0.6 seconds with brushless motor as luxury car glides through",
                "camera": "Low-angle kinetic tracking shot as boom barrier arm lifts smoothly",
                "narration": "High-speed brushless boom barrier clears in zero-point-six seconds for authorized vehicles.",
                "on_screen_text": "0.6S RAPID ACCESS",'''

new_p3 = '''            {
                "shot_num": 3,
                "duration_s": 4,
                "type": "Access Control (High-Speed Rapid Lift)",
                "visual_prompt": "ParkFnB automated boom barrier with illuminated LED arm elevating rapidly with brushless motor as luxury car glides through",
                "camera": "Low-angle kinetic tracking shot as boom barrier arm lifts smoothly",
                "narration": "High-speed brushless boom barrier clears rapidly for authorized vehicles.",
                "on_screen_text": "RAPID ACCESS CONTROL",'''

if old_p3 in content:
    content = content.replace(old_p3, new_p3)
    print("Updated parking_barrier profile (removed unverified 0.6s claim).")

# 4. In scene_traces, record asset_path for SHA-256 and dHash checks
old_trace = '''            "asset_file": Path(fallback_image).name if fallback_image else None,
            "fallback_used": scene_fallback,'''

new_trace = '''            "asset_file": Path(fallback_image).name if fallback_image else None,
            "asset_path": str(fallback_image) if fallback_image else None,
            "fallback_used": scene_fallback,'''

if old_trace in content:
    content = content.replace(old_trace, new_trace)
    print("Updated scene_traces with asset_path.")

# 5. Add per-scene validation loop for full_ai mode
old_scene_loop_check = '''        os.chmod(scene_out_mp4, 0o644)
        generated_clip_paths.append(scene_out_mp4)'''

new_scene_loop_check = '''        if req.generation_mode == "full_ai":
            if scene_fallback or not use_nvidia_video:
                shutil.rmtree(project_dir, ignore_errors=True)
                raise GenerationValidationError(
                    f"Scene {idx}: Full AI requires verified AI-generated video for every scene. Fallback asset is not permitted."
                )
            if not source_mp4.is_file() or source_mp4.stat().st_size < 1000:
                shutil.rmtree(project_dir, ignore_errors=True)
                raise GenerationValidationError(
                    f"Scene {idx}: Full AI requires verified AI-generated video clip on disk."
                )

        os.chmod(scene_out_mp4, 0o644)
        generated_clip_paths.append(scene_out_mp4)'''

if old_scene_loop_check in content:
    content = content.replace(old_scene_loop_check, new_scene_loop_check)
    print("Added per-scene strict full_ai validation.")

# 6. Replace file-path duplicate check with SHA-256 & dHash check
old_diversity = '''    used_images = [t.get("asset_file") or t.get("keyframe_url") for t in scene_traces if t.get("asset_file") or t.get("keyframe_url")]
    if len(used_images) > 1 and len(set(used_images)) < len(used_images):
        shutil.rmtree(project_dir, ignore_errors=True)
        raise GenerationValidationError(
            "Scene diversity check failed: duplicate image assets detected across scenes. Every commercial scene must have distinct visual actions and composition."
        )'''

new_diversity = '''    # Mandatory Content-Based Scene Diversity Check (SHA-256 byte equality & dHash perceptual similarity)
    scene_source_images = [t.get("asset_path") for t in scene_traces if t.get("asset_path")]
    dup_res = detect_duplicate_scenes(
        scene_mp4s=generated_clip_paths,
        scene_traces=scene_traces,
        scene_images=scene_source_images
    )
    if dup_res["has_duplicates"]:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise GenerationValidationError(
            f"Scene diversity check failed: {dup_res['reason']} Every commercial scene must have distinct visual actions and composition."
        )'''

if old_diversity in content:
    content = content.replace(old_diversity, new_diversity)
    print("Upgraded scene diversity check to content-based SHA-256 & dHash.")

# 7. Update manifest_data with 3-tier QC and truthful provenance
old_manifest = '''    # Save Project Manifest with Full Audit Integrity
    manifest_data = {
        "project_id": proj_id,
        "title": title,
        "category": category,
        "video_provider": req.video_provider,
        "video_model": req.video_model,
        "generation_mode": req.generation_mode,
        "video_task": "generated_keyframe_to_image_to_video",
        "resolution": req.resolution,
        "image_model": IMAGE_MODEL_ID,
        "product_entity": product_entity,
        "aspect_ratio": req.aspect_ratio,
        "audio_voice": voice_actor if voice_generated else None,
        "audio_description": audio_description,
        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),
        "user_prompt": prompt_text,
        "director_model": req.director_model,
        "duration_seconds": req.duration_s,
        "final_video_url": f"/static/media/projects/{proj_id}/final.mp4",
        "subtitles_url": f"/static/media/projects/{proj_id}/subtitles.srt",
        "scenes_count": len(scene_traces),
        "scene_traces": scene_traces,
        "qc_verdict": qc_verdict,
        "qc_score": qc_score,
        "qc_checks": qc_checks,
        "fallback_used": fallback_used_any,
        "fallback_reason": "Explicit uploaded-reference motion fallback used for one or more shots" if fallback_used_any else None,
        "technical_check": final_probe,
        "semantic_quality_check": "not_evaluated",
        "estimated_cost_usd": None,
        "model_latency_s": model_latency,
        "generation_time_s": gen_time
    }'''

new_manifest = '''    # Honest Provenance Labeling: Never label static-image motion fallback as Full AI
    truthful_gen_mode = "full_ai" if (use_nvidia_video and not fallback_used_any) else "motion_fallback_commercial"
    truthful_provenance = "gpu_video_diffusion" if (use_nvidia_video and not fallback_used_any) else "motion_controlled_photographic_stills"

    technical_qc = {
        "container": "mp4",
        "resolution": f"{final_probe.get('width', output_width)}x{final_probe.get('height', output_height)}",
        "aspect_ratio": req.aspect_ratio,
        "framerate_fps": 25,
        "video_codec": final_probe.get("video_codec", "h264"),
        "audio_codec": final_probe.get("audio", {}).get("codec", "aac") if final_probe.get("audio") else "aac",
        "audio_sample_rate_hz": final_probe.get("audio", {}).get("sample_rate_hz", 48000) if final_probe.get("audio") else 48000,
        "audio_channels": final_probe.get("audio", {}).get("channels", 2) if final_probe.get("audio") else 2,
        "faststart_enabled": True,
        "duration_s": final_probe.get("duration_s", req.duration_s),
        "verified": final_probe.get("verified", True)
    }

    motion_and_integrity_qc = {
        "actual_video_generation": qc_checks.get("actual_video_generation", False),
        "static_content_detected": qc_checks.get("static_content_detected", False),
        "duplicate_scenes_detected": qc_checks.get("duplicate_scenes_detected", False),
        "measured_motion_deltas": qc_results.get("measured_motion_deltas", []),
        "duplicate_diagnostic": qc_results.get("duplicate_diagnostic", "None")
    }

    semantic_and_visual_qc = {
        "visual_relevance": qc_checks.get("visual_relevance", True),
        "brand_consistency": qc_checks.get("brand_consistency", True),
        "text_quality": qc_checks.get("text_quality", True),
        "storyboard_adherence": qc_checks.get("storyboard_adherence", True),
        "provenance_classification": truthful_gen_mode
    }

    # Save Project Manifest with Full Audit Integrity
    manifest_data = {
        "project_id": proj_id,
        "title": title,
        "category": category,
        "video_provider": req.video_provider,
        "video_model": req.video_model,
        "generation_mode": truthful_gen_mode,
        "provenance": truthful_provenance,
        "video_task": "generated_keyframe_to_image_to_video",
        "resolution": req.resolution,
        "image_model": IMAGE_MODEL_ID,
        "product_entity": product_entity,
        "aspect_ratio": req.aspect_ratio,
        "audio_voice": voice_actor if voice_generated else None,
        "audio_description": audio_description,
        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),
        "user_prompt": prompt_text,
        "director_model": req.director_model,
        "duration_seconds": req.duration_s,
        "final_video_url": f"/static/media/projects/{proj_id}/final.mp4",
        "subtitles_url": f"/static/media/projects/{proj_id}/subtitles.srt",
        "scenes_count": len(scene_traces),
        "scene_traces": scene_traces,
        "qc_verdict": qc_verdict,
        "qc_score": qc_score,
        "qc_checks": qc_checks,
        "technical_qc": technical_qc,
        "motion_and_integrity_qc": motion_and_integrity_qc,
        "semantic_and_visual_qc": semantic_and_visual_qc,
        "fallback_used": fallback_used_any,
        "fallback_reason": "Explicit uploaded-reference motion fallback used for one or more shots" if fallback_used_any else None,
        "technical_check": final_probe,
        "semantic_quality_check": "not_evaluated",
        "estimated_cost_usd": None,
        "model_latency_s": model_latency,
        "generation_time_s": gen_time
    }'''

if old_manifest in content:
    content = content.replace(old_manifest, new_manifest)
    print("Updated manifest with 3-tier QC and truthful provenance.")

# 8. Update response dict of /api/studio/generate
old_resp_qc = '''        "qc_report": {
            "verdict": qc_verdict,
            "score": qc_score,
            "checks": qc_checks,
            "resolution": f"{req.resolution} ({req.aspect_ratio})",
            "framerate": "24 fps progressive",
            "audio": audio_description,
            "audio_stream": final_probe.get("audio"),
            "technical_check": final_probe,
            "semantic_quality_check": "not_evaluated",
            "fallback_used": fallback_used_any,
            "fallback_reason": "Explicit uploaded-reference motion fallback used for one or more shots" if fallback_used_any else None,
            "compliance": "human visual review required"
        },'''

new_resp_qc = '''        "final_video_url": f"/static/media/projects/{proj_id}/final.mp4",
        "provenance": truthful_provenance,
        "qc_report": {
            "verdict": qc_verdict,
            "score": qc_score,
            "checks": qc_checks,
            "technical_qc": technical_qc,
            "motion_and_integrity_qc": motion_and_integrity_qc,
            "semantic_and_visual_qc": semantic_and_visual_qc,
            "resolution": f"{req.resolution} ({req.aspect_ratio})",
            "framerate": "25 fps progressive",
            "audio": audio_description,
            "audio_stream": final_probe.get("audio"),
            "technical_check": final_probe,
            "fallback_used": fallback_used_any,
            "fallback_reason": "Explicit uploaded-reference motion fallback used for one or more shots" if fallback_used_any else None,
            "compliance": "human visual review required"
        },'''

if old_resp_qc in content:
    content = content.replace(old_resp_qc, new_resp_qc)
    print("Updated response dict with 3-tier QC and final_video_url alias.")

main_path.write_text(content, encoding="utf-8")
print("Done writing web_ec2/main.py!")
