"""
Only patches main.py now (index.html fetch body already patched separately).
"""

from pathlib import Path
import sys

MAIN = Path("d:/research_synquic/web_ec2/main.py")
main_txt = MAIN.read_text(encoding="utf-8")

# =========================================================
# PART 1: Update main.py — GenerateVideoRequest model
# =========================================================
OLD_REQUEST_CRLF = (
    'class GenerateVideoRequest(BaseModel):\r\n'
    '    prompt: str\r\n'
    '    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"\r\n'
    '    duration_s: int = 15\r\n'
    '    style: str = "Luxury Minimalist"\r\n'
    '    aspect_ratio: str = "16:9"'
)
OLD_REQUEST_LF = OLD_REQUEST_CRLF.replace("\r\n", "\n")
NEW_REQUEST = (
    'class GenerateVideoRequest(BaseModel):\n'
    '    prompt: str\n'
    '    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"\n'
    '    duration_s: int = 15\n'
    '    style: str = "Luxury Minimalist"\n'
    '    aspect_ratio: str = "16:9"\n'
    '    audio_voice: str = "auto"   # edge-tts voice or "auto" to use profile default\n'
    '    motion_style: str = "kenburns_cinematic"  # visual motion engine preset'
)

if OLD_REQUEST_CRLF in main_txt:
    main_txt = main_txt.replace(OLD_REQUEST_CRLF, NEW_REQUEST, 1)
    print("[OK] Extended GenerateVideoRequest in main.py (CRLF)")
elif OLD_REQUEST_LF in main_txt:
    main_txt = main_txt.replace(OLD_REQUEST_LF, NEW_REQUEST, 1)
    print("[OK] Extended GenerateVideoRequest in main.py (LF)")
else:
    idx = main_txt.find("class GenerateVideoRequest")
    print("[DEBUG snippet]:", repr(main_txt[idx:idx+350]))
    print("[FAIL] Could not find GenerateVideoRequest in main.py")
    sys.exit(1)

# =========================================================
# PART 2: Update audio voice engine logic
# =========================================================
OLD_VOICE = '    voice_actor = profile.get("voice", "en-US-ChristopherNeural")'
NEW_VOICE = (
    '    # Audio Voice Engine: use user-selected voice or fall back to profile default\n'
    '    if getattr(req, "audio_voice", "auto") not in ("auto", "", None):\n'
    '        voice_actor = req.audio_voice\n'
    '    else:\n'
    '        voice_actor = profile.get("voice", "en-US-ChristopherNeural")'
)

if OLD_VOICE in main_txt:
    main_txt = main_txt.replace(OLD_VOICE, NEW_VOICE, 1)
    print("[OK] Updated audio voice engine logic in main.py")
else:
    print("[FAIL] Could not find voice_actor assignment in main.py")
    sys.exit(1)

# =========================================================
# PART 3: Update motion engine to use req.motion_style
# =========================================================
OLD_MOTION_TAG = "            # Motion Pan/Zoom Filter (dynamic for 9:16 vertical or 16:9 landscape)"
if OLD_MOTION_TAG not in main_txt:
    print("[FAIL] Could not find motion pan/zoom comment in main.py")
    sys.exit(1)

# Find the block end by locating the last filt_motion assignment
start_idx = main_txt.find(OLD_MOTION_TAG)
# The block ends after the 'else:' branch of zoompan
# Find next line that is NOT part of the if/elif/else block = line after zoom out
# Simple approach: replace from comment to end of the else block
# Find "else:" after the elif, then find the end of that filt_motion line
after_comment = main_txt[start_idx:]
# Locate end of else branch: after "fps=24}" which ends the last filt_motion
end_marker = "fps=24\""
# Find 3rd occurrence (one per if/elif/else)
occ1 = after_comment.find(end_marker)
occ2 = after_comment.find(end_marker, occ1 + 1)
occ3 = after_comment.find(end_marker, occ2 + 1)
block_end = start_idx + occ3 + len(end_marker)
old_motion_block = main_txt[start_idx:block_end]

NEW_MOTION_BLOCK = (
    '            # Motion Pan/Zoom Filter — driven by req.motion_style\n'
    '            _ms = getattr(req, "motion_style", "kenburns_cinematic")\n'
    '            _MOTION_PRESETS = {\n'
    '                "kenburns_cinematic":  [("zoom_in",  0.0014, 1.22), ("pan_right", 0.001,  1.15), ("zoom_out", 0.0014, 1.18)],\n'
    '                "kenburns_slow":       [("zoom_in",  0.0008, 1.12), ("pan_right", 0.0006, 1.10), ("zoom_out", 0.0008, 1.12)],\n'
    '                "kenburns_dolly":      [("pan_right",0.0005, 1.08), ("pan_left",  0.0005, 1.08), ("zoom_in",  0.0010, 1.14)],\n'
    '                "kenburns_pullback":   [("zoom_in",  0.0012, 1.18), ("zoom_in",  0.0010, 1.15), ("zoom_out", 0.0020, 1.22)],\n'
    '                "kenburns_aggressive": [("zoom_in",  0.0022, 1.28), ("pan_right", 0.0018, 1.22), ("zoom_out", 0.0020, 1.25)],\n'
    '            }\n'
    '            _style_shots = _MOTION_PRESETS.get(_ms, _MOTION_PRESETS["kenburns_cinematic"])\n'
    '            _motion_type, _zoom_step, _zoom_max = _style_shots[(idx - 1) % len(_style_shots)]\n'
    '            if _motion_type == "pan_right":\n'
    "                filt_motion = f\"zoompan=z='min(zoom+{_zoom_step},{_zoom_max})':d=120:x='(iw-iw/zoom)*(1-on/120)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\"\n"
    '            elif _motion_type == "pan_left":\n'
    "                filt_motion = f\"zoompan=z='min(zoom+{_zoom_step},{_zoom_max})':d=120:x='(iw-iw/zoom)*(on/120)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\"\n"
    '            elif _motion_type == "zoom_out":\n'
    "                filt_motion = f\"zoompan=z='if(lte(zoom,1.0),{_zoom_max},max(1.001,zoom-{_zoom_step}))':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\"\n"
    '            else:  # zoom_in\n'
    "                filt_motion = f\"zoompan=z='min(zoom+{_zoom_step},{_zoom_max})':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\""
)

main_txt = main_txt[:start_idx] + NEW_MOTION_BLOCK + main_txt[block_end:]
print("[OK] Updated motion engine filter logic in main.py")

# =========================================================
# PART 4: Expose motion_style + audio_voice in API response
# =========================================================
OLD_RESP2 = '"aspect_ratio": req.aspect_ratio,'
NEW_RESP2 = ('"aspect_ratio": req.aspect_ratio,\n'
             '        "audio_voice": voice_actor,\n'
             '        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),')

if OLD_RESP2 in main_txt and '"audio_voice": voice_actor,' not in main_txt:
    main_txt = main_txt.replace(OLD_RESP2, NEW_RESP2, 1)
    print("[OK] Added audio_voice + motion_style to response dict in main.py")
elif '"audio_voice": voice_actor,' in main_txt:
    print("[OK] audio_voice already in response dict")
else:
    print("[FAIL] Could not find aspect_ratio in response dict")
    sys.exit(1)

MAIN.write_text(main_txt, encoding="utf-8")
print("[OK] Saved updated main.py")
print("\nAll main.py changes applied successfully!")
