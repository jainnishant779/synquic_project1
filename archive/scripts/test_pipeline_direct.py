import os, sys
from pathlib import Path

# Add app dir
sys.path.insert(0, "/home/ubuntu/synquic_app")
from main import run_semantic_qc, generate_storyboard_plan

# Test QC
frame = Path("/home/ubuntu/synquic_app/static/media/p2.png")
qc = run_semantic_qc(frame, "AuraGlow Botanical Face Serum commercial")
print("QC Result:")
print("Verdict:", qc["verdict"])
print("Report:", qc["report"])

# Test Storyboard Plan
sb = generate_storyboard_plan("AuraGlow Serum", "Beauty", "Urban women", "Highlight natural morning glow", 15, "Luxury Minimalist")
print("\nStoryboard Result:")
print("Title:", sb.get("title"))
print("Shots count:", len(sb.get("shots", [])))
for s in sb.get("shots", []):
    print(f"Shot {s.get('shot_num')}: {s.get('type')} | {s.get('narration')}")
