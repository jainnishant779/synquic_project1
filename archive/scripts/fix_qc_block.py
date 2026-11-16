from pathlib import Path

main_path = Path("web_ec2/main.py")
content = main_path.read_text(encoding="utf-8")

old_text = '''    # 6. Report measured facts only. Visual quality still needs human review.
    gen_time = round(time.time() - t_start, 2)
    model_latency = round(video_generation_time_s, 2)
    cost_est = None  # NVIDIA's preview endpoint does not return a per-request charge.
    qc_score = None  # No calibrated semantic or visual score is implemented.
    final_probe = probe_video(out_mp4)
    qc_verdict = (
        "Technical file check passed; visual review required"
        if final_probe["verified"]
        else "Technical check unavailable; visual review required"
    )'''

new_text = '''    # 6. Report measured facts only. Independent 7-Point QC Engine Execution.
    gen_time = round(time.time() - t_start, 2)
    model_latency = round(video_generation_time_s, 2)
    cost_est = None  # NVIDIA's preview endpoint does not return a per-request charge.
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

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    main_path.write_text(content, encoding="utf-8")
    print("Replaced QC execution block successfully.")
else:
    print("Error: old_text not found in web_ec2/main.py!")
