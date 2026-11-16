"""
Applies per-engine model selectors to index.html and updates GenerateVideoRequest in main.py.
"""

from pathlib import Path
import sys

HTML = Path("d:/research_synquic/web_ec2/templates/index.html")
MAIN = Path("d:/research_synquic/web_ec2/main.py")

# =========================================================
# PART 1: Update executeGenerateVideo() JS to send new fields
# =========================================================
html = HTML.read_text(encoding="utf-8")

OLD_FETCH_BODY = (
    "                        body: JSON.stringify({\r\n"
    "                        prompt: prompt,\r\n"
    "                        director_model: model,\r\n"
    "                        duration_s: duration,\r\n"
    "                        style: style,\r\n"
    "                        aspect_ratio: aspect\r\n"
    "                    })"
)

NEW_FETCH_BODY = (
    "                        body: JSON.stringify({\r\n"
    "                        prompt: prompt,\r\n"
    "                        director_model: model,\r\n"
    "                        duration_s: duration,\r\n"
    "                        style: style,\r\n"
    "                        aspect_ratio: aspect,\r\n"
    "                        audio_voice: document.getElementById('studioVoiceSelect').value,\r\n"
    "                        motion_style: document.getElementById('studioMotionSelect').value\r\n"
    "                    })"
)

if OLD_FETCH_BODY in html:
    html = html.replace(OLD_FETCH_BODY, NEW_FETCH_BODY, 1)
    print("[OK] Updated fetch body in index.html")
else:
    # Try \n version
    OLD_NL = OLD_FETCH_BODY.replace("\r\n", "\n")
    NEW_NL = NEW_FETCH_BODY.replace("\r\n", "\n")
    if OLD_NL in html:
        html = html.replace(OLD_NL, NEW_NL, 1)
        print("[OK] Updated fetch body in index.html (LF)")
    else:
        # Print a portion of the file around the fetch call for debugging
        idx = html.find("body: JSON.stringify")
        print("[DEBUG] Found stringify at index:", idx)
        print(repr(html[idx:idx+200]))
        print("[FAIL] Could not find fetch body in index.html")
        sys.exit(1)

HTML.write_text(html, encoding="utf-8")
print("[OK] Saved updated index.html")

# =========================================================
# PART 2: Update main.py — GenerateVideoRequest model
# =========================================================
main_txt = MAIN.read_text(encoding="utf-8")

OLD_REQUEST = 'class GenerateVideoRequest(BaseModel):\r\n    prompt: str\r\n    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"\r\n    duration_s: int = 15\r\n    style: str = "Luxury Minimalist"\r\n    aspect_ratio: str = "16:9"'

NEW_REQUEST = ('class GenerateVideoRequest(BaseModel):\r\n'
               '    prompt: str\r\n'
               '    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"\r\n'
               '    duration_s: int = 15\r\n'
               '    style: str = "Luxury Minimalist"\r\n'
               '    aspect_ratio: str = "16:9"\r\n'
               '    audio_voice: str = "auto"   # edge-tts voice or "auto" to use profile default\r\n'
               '    motion_style: str = "kenburns_cinematic"  # visual motion engine preset')

if OLD_REQUEST in main_txt:
    main_txt = main_txt.replace(OLD_REQUEST, NEW_REQUEST, 1)
    print("[OK] Extended GenerateVideoRequest in main.py")
else:
    # LF fallback
    OLD_LF = OLD_REQUEST.replace("\r\n", "\n")
    NEW_LF = NEW_REQUEST.replace("\r\n", "\n")
    if OLD_LF in main_txt:
        main_txt = main_txt.replace(OLD_LF, NEW_LF, 1)
        print("[OK] Extended GenerateVideoRequest in main.py (LF)")
    else:
        print("[FAIL] Could not find GenerateVideoRequest in main.py")
        idx = main_txt.find("class GenerateVideoRequest")
        print(repr(main_txt[idx:idx+300]))
        sys.exit(1)

# =========================================================
# PART 3: Update audio engine to use req.audio_voice
# =========================================================
OLD_VOICE = '    voice_actor = profile.get("voice", "en-US-ChristopherNeural")'

NEW_VOICE = ('    # Audio Voice Engine: use user-selected voice or fall back to profile default\r\n'
             '    if hasattr(req, "audio_voice") and req.audio_voice and req.audio_voice != "auto":\r\n'
             '        voice_actor = req.audio_voice\r\n'
             '    else:\r\n'
             '        voice_actor = profile.get("voice", "en-US-ChristopherNeural")')

if OLD_VOICE in main_txt:
    main_txt = main_txt.replace(OLD_VOICE, NEW_VOICE, 1)
    print("[OK] Updated audio voice engine logic in main.py")
else:
    OLD_LF_V = OLD_VOICE.replace("\r\n", "\n")
    NEW_LF_V = NEW_VOICE.replace("\r\n", "\n")
    if OLD_LF_V in main_txt:
        main_txt = main_txt.replace(OLD_LF_V, NEW_LF_V, 1)
        print("[OK] Updated audio voice engine logic in main.py (LF)")
    else:
        print("[FAIL] Could not find voice_actor assignment in main.py")
        sys.exit(1)

# =========================================================
# PART 4: Update motion engine to use req.motion_style
# =========================================================
OLD_MOTION = (
    '            # Motion Pan/Zoom Filter (dynamic for 9:16 vertical or 16:9 landscape)\r\n'
    '            if idx == 1:\r\n'
    "                filt_motion = f\"zoompan=z='min(zoom+0.0014,1.22)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\"\r\n"
    '            elif idx == 2:\r\n'
    "                filt_motion = f\"zoompan=z='min(zoom+0.001,1.15)':d=120:x='(iw-iw/zoom)*(1-on/120)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\"\r\n"
    '            else:\r\n'
    "                filt_motion = f\"zoompan=z='if(lte(zoom,1.0),1.18,max(1.001,zoom-0.0014))':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\""
)

NEW_MOTION = (
    '            # Motion Pan/Zoom Filter — driven by req.motion_style\r\n'
    '            _ms = getattr(req, "motion_style", "kenburns_cinematic")\r\n'
    '            _MOTION_PRESETS = {\r\n'
    '                "kenburns_cinematic":  [("zoom_in",  0.0014, 1.22), ("pan_right", 0.001,  1.15), ("zoom_out", 0.0014, 1.18)],\r\n'
    '                "kenburns_slow":       [("zoom_in",  0.0008, 1.12), ("pan_right", 0.0006, 1.10), ("zoom_out", 0.0008, 1.12)],\r\n'
    '                "kenburns_dolly":      [("pan_right",0.0005, 1.08), ("pan_left",  0.0005, 1.08), ("zoom_in",  0.0010, 1.14)],\r\n'
    '                "kenburns_pullback":   [("zoom_in",  0.0012, 1.18), ("zoom_in",  0.0010, 1.15), ("zoom_out", 0.0020, 1.22)],\r\n'
    '                "kenburns_aggressive": [("zoom_in",  0.0022, 1.28), ("pan_right", 0.0018, 1.22), ("zoom_out", 0.0020, 1.25)],\r\n'
    '            }\r\n'
    '            _style_shots = _MOTION_PRESETS.get(_ms, _MOTION_PRESETS["kenburns_cinematic"])\r\n'
    '            _motion_type, _zoom_step, _zoom_max = _style_shots[(idx - 1) % len(_style_shots)]\r\n'
    '            if _motion_type == "pan_right":\r\n'
    "                filt_motion = f\"zoompan=z='min(zoom+{_zoom_step},{_zoom_max})':d=120:x='(iw-iw/zoom)*(1-on/120)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\"\r\n"
    '            elif _motion_type == "pan_left":\r\n'
    "                filt_motion = f\"zoompan=z='min(zoom+{_zoom_step},{_zoom_max})':d=120:x='(iw-iw/zoom)*(on/120)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\"\r\n"
    '            elif _motion_type == "zoom_out":\r\n'
    "                filt_motion = f\"zoompan=z='if(lte(zoom,1.0),{_zoom_max},max(1.001,zoom-{_zoom_step}))':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\"\r\n"
    '            else:  # zoom_in\r\n'
    "                filt_motion = f\"zoompan=z='min(zoom+{_zoom_step},{_zoom_max})':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=24\""
)

if OLD_MOTION in main_txt:
    main_txt = main_txt.replace(OLD_MOTION, NEW_MOTION, 1)
    print("[OK] Updated motion engine filter logic in main.py")
else:
    OLD_LF_M = OLD_MOTION.replace("\r\n", "\n")
    NEW_LF_M = NEW_MOTION.replace("\r\n", "\n")
    if OLD_LF_M in main_txt:
        main_txt = main_txt.replace(OLD_LF_M, NEW_LF_M, 1)
        print("[OK] Updated motion engine filter logic in main.py (LF)")
    else:
        idx = main_txt.find("# Motion Pan/Zoom Filter")
        print("[DEBUG] Found motion filter at:", idx)
        print(repr(main_txt[idx:idx+500]))
        print("[FAIL] Could not find motion filter block in main.py")
        sys.exit(1)

# =========================================================
# PART 5: Expose motion_style + audio_voice in API response
# =========================================================
OLD_RESP = (
    '        "style": req.style,\r\n'
    '        "aspect_ratio": req.aspect_ratio,\r\n'
    '        "audio_voice": voice_actor,\r\n'
    '        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),'
)

if OLD_RESP in main_txt:
    print("[OK] Audio/motion_style already in response dict")
else:
    # Add after aspect_ratio
    OLD_RESP2 = '        "style": req.style,\r\n        "aspect_ratio": req.aspect_ratio,'
    NEW_RESP2 = ('        "style": req.style,\r\n'
                 '        "aspect_ratio": req.aspect_ratio,\r\n'
                 '        "audio_voice": voice_actor,\r\n'
                 '        "motion_style": getattr(req, "motion_style", "kenburns_cinematic"),')
    if OLD_RESP2 in main_txt:
        main_txt = main_txt.replace(OLD_RESP2, NEW_RESP2, 1)
        print("[OK] Added audio_voice + motion_style to response dict in main.py")
    else:
        OLD_LF_R2 = OLD_RESP2.replace("\r\n", "\n")
        NEW_LF_R2 = NEW_RESP2.replace("\r\n", "\n")
        if OLD_LF_R2 in main_txt:
            main_txt = main_txt.replace(OLD_LF_R2, NEW_LF_R2, 1)
            print("[OK] Added audio_voice + motion_style to response dict in main.py (LF)")
        else:
            idx = main_txt.find('"style": req.style,')
            print("[DEBUG] Found response style at:", idx)
            print(repr(main_txt[idx:idx+200]))
            print("[FAIL] Could not find response style block in main.py")
            sys.exit(1)

MAIN.write_text(main_txt, encoding="utf-8")
print("[OK] Saved updated main.py")
print("\nAll changes applied successfully!")
