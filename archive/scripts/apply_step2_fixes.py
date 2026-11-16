import re
from pathlib import Path

main_path = Path("web_ec2/main.py")
content = main_path.read_text(encoding="utf-8")

# 1. Add qc_engine import
if "from qc_engine import evaluate_qc_checks" not in content:
    content = "from qc_engine import evaluate_qc_checks\n" + content

# 2. Replace parking_barrier profile in PRODUCT_PROFILES
new_parking_barrier = '''    "parking_barrier": {
        "keywords": ["barrier", "parking", "parkfnb", "boom barrier", "gate", "toll", "rfid", "access control", "security gate", "turnstile", "smart parking", "boom", "anpr", "lpr"],
        "default_title": "ParkFnB Smart Automated Boom Barrier Commercial",
        "default_entity": "ParkFnB Smart Parking Barrier",
        "voice": "en-US-ChristopherNeural",
        "bgm": "bgm_energetic.mp3",
        "bgm_volume": 0.22,
        "style_mood": "High-Tech Industrial Security, Clean Architectural Daylight & Laser Precision",
        "stills": ["parkfnb_scene1_bottleneck.jpg", "parkfnb_scene2_anpr.jpg", "parkfnb_scene3_barrier.jpg", "parkfnb_scene4_app.jpg"],
        "default_shots": [
            {
                "shot_num": 1,
                "duration_s": 4,
                "type": "The Problem (Parking Bottleneck)",
                "visual_prompt": "Vehicle entering a crowded, congested multi-level parking facility, long queues and difficulty finding an empty space, high stress bottleneck",
                "camera": "Slow cinematic macro push-in on congested parking queue",
                "narration": "Circling endlessly in congested parking lots. Traditional parking is broken.",
                "on_screen_text": "PARKING BOTTLENECK",
                "search_terms": ["crowded parking lot cars", "parking congestion traffic", "parking garage queue"],
                "dialect_wan": "Vehicle entering crowded parking facility, brake lights glowing, full parking lanes",
                "dialect_veo": "Cinematic automotive shot of car stuck in busy multi-storey parking queue, dramatic natural lighting"
            },
            {
                "shot_num": 2,
                "duration_s": 4,
                "type": "Intelligence (ANPR & Detection)",
                "visual_prompt": "High-tech smart ANPR camera scanning vehicle license plate instantly, optical sensor recognition, digital occupancy display updating",
                "camera": "Dynamic macro zoom on AI license plate recognition scanner",
                "narration": "ParkFnB smart cameras detect vehicles instantly, scanning number plates in milliseconds.",
                "on_screen_text": "AI NUMBER PLATE RECOGNITION",
                "search_terms": ["Automated License Plate Reader ALPR", "license plate recognition camera", "automatic number plate recognition"],
                "dialect_wan": "Close up of ANPR camera scanner optical lens locking on license plate, green status indicator",
                "dialect_veo": "Futuristic commercial macro of smart AI camera scanning vehicle registration plate at parking entrance"
            },
            {
                "shot_num": 3,
                "duration_s": 4,
                "type": "Access Control (0.6s Rapid Lift)",
                "visual_prompt": "ParkFnB automated boom barrier with illuminated LED arm elevating rapidly in 0.6 seconds with brushless motor as luxury car glides through",
                "camera": "Low-angle kinetic tracking shot as boom barrier arm lifts smoothly",
                "narration": "High-speed brushless boom barrier clears in zero-point-six seconds for authorized vehicles.",
                "on_screen_text": "0.6S RAPID ACCESS",
                "search_terms": ["automated boom barrier", "parking boom barrier lift", "barrier gate vehicle entry"],
                "dialect_wan": "Illuminated boom barrier arm elevating smoothly, green LED guidance, car gliding through lane",
                "dialect_veo": "Cinematic automotive lane entrance, heavy-duty boom barrier arm lifting rapidly with LED indicator"
            },
            {
                "shot_num": 4,
                "duration_s": 3,
                "type": "Product Benefit & Brand Reveal",
                "visual_prompt": "Smartphone screen displaying ParkFnB live slot availability and instant booking app, corporate headquarters entrance packshot",
                "camera": "Subtle dolly back and focus pull on ParkFnB signature branding",
                "narration": "Live slot availability in your pocket. ParkFnB — parking, reimagined.",
                "on_screen_text": "PARKFNB APP",
                "search_terms": ["mobile parking app slot booking", "modern corporate parking entrance", "smart parking system"],
                "dialect_wan": "Smartphone displaying modern parking app slot reservation, corporate headquarters background",
                "dialect_veo": "Clean corporate packshot of smart parking system finish with glowing ParkFnB interface"
            }
        ]
    },'''

content = re.sub(r'    "parking_barrier": \{.*?\n    \},', new_parking_barrier, content, flags=re.DOTALL)

# 3. Use individual shot duration if present
target_dur = 'shot_duration = max(2, req.duration_s // len(shots))'
replacement_dur = '''# Use shot-specific duration or evenly distribute
    total_specified = sum(s.get("duration_s", 0) for s in shots)
    if total_specified != req.duration_s:
        shot_duration = max(2, req.duration_s // len(shots))
    else:
        shot_duration = None'''
content = content.replace(target_dur, replacement_dur)

content = content.replace(
    'for idx, shot in enumerate(shots, 1):',
    'for idx, shot in enumerate(shots, 1):\n        this_shot_dur = shot.get("duration_s") or shot_duration or max(2, req.duration_s // len(shots))'
)
content = content.replace('tot_frames = int(shot_duration * fps)', 'tot_frames = int(this_shot_dur * fps)')
content = content.replace('"-t", str(shot_duration),', '"-t", str(this_shot_dur),')

# 4. Connect QC evaluation
target_qc = '''    # 6. Report measured facts only. Visual quality still needs human review.
    gen_time = round(time.time() - t_start, 2)
    model_latency = round(video_generation_time_s, 2)
    cost_est = calculate_pipeline_cost(storyboard_data)
    qc_score = None  # No calibrated semantic or visual score is implemented.
    final_probe = probe_video(out_mp4)
    qc_verdict = (
        "Technical file check passed; visual review required"
        if final_probe["verified"]
        else "Technical check unavailable; visual review required"
    )'''

replacement_qc = '''    # 6. Independent Quality & Cost (QC) Engine Execution
    gen_time = round(time.time() - t_start, 2)
    model_latency = round(video_generation_time_s, 2)
    cost_est = calculate_pipeline_cost(storyboard_data)
    final_probe = probe_video(out_mp4)
    
    # Run comprehensive 7-point QC engine
    qc_results = evaluate_qc_checks(
        out_mp4=out_mp4,
        scene_traces=scene_traces,
        prompt_text=prompt_text,
        brand_display=brand_display,
        shots=shots,
        actual_video_gen_flag=use_nvidia_video
    )
    qc_score = qc_results["score"]
    qc_verdict = qc_results["verdict"]
    qc_checks = qc_results["checks"]'''

content = content.replace(target_qc, replacement_qc)

# 5. Add qc_checks to manifest_data
content = content.replace(
    '"qc_verdict": qc_verdict,\n        "qc_score": qc_score,',
    '"qc_verdict": qc_verdict,\n        "qc_score": qc_score,\n        "qc_checks": qc_checks,'
)

content = content.replace(
    '"verdict": qc_verdict,\n            "score": qc_score,',
    '"verdict": qc_verdict,\n            "score": qc_score,\n            "checks": qc_checks,'
)

main_path.write_text(content, encoding="utf-8")
print("Applied Step 2 fixes to web_ec2/main.py successfully.")
