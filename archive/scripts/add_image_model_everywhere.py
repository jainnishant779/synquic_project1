from pathlib import Path
import sys

MAIN = Path("d:/research_synquic/web_ec2/main.py")
INDEX = Path("d:/research_synquic/web_ec2/templates/index.html")

# -------------------------------------------------------------
# 1. UPDATE web_ec2/main.py
# -------------------------------------------------------------
main_txt = MAIN.read_text(encoding="utf-8")

# A. Add image_model to GenerateVideoRequest
old_req = """class GenerateVideoRequest(BaseModel):
    prompt: str
    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    duration_s: int = 15
    style: str = "Luxury Minimalist"
    aspect_ratio: str = "16:9"
    audio_voice: str = "auto"   # edge-tts voice or "auto" to use profile default
    motion_style: str = "kenburns_cinematic"  # visual motion engine preset"""

new_req = """class GenerateVideoRequest(BaseModel):
    prompt: str
    director_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    image_model: str = "flux2_klein_4b"  # Visual / Image Generation Diffusion Engine
    audio_voice: str = "auto"   # edge-tts voice or "auto" to use profile default
    motion_style: str = "kenburns_cinematic"  # visual motion engine preset
    duration_s: int = 15
    style: str = "Luxury Minimalist"
    aspect_ratio: str = "16:9"
"""

if old_req in main_txt:
    main_txt = main_txt.replace(old_req, new_req, 1)
    print("Updated GenerateVideoRequest in main.py")
else:
    old_req_crlf = old_req.replace("\n", "\r\n")
    new_req_crlf = new_req.replace("\n", "\r\n")
    if old_req_crlf in main_txt:
        main_txt = main_txt.replace(old_req_crlf, new_req_crlf, 1)
        print("Updated GenerateVideoRequest (CRLF) in main.py")
    else:
        print("Could not match old_req in main.py")

# B. Add Image Model resolution and still matching in main.py
old_still_block = """            still_filename = stills_list[(idx - 1) % len(stills_list)]
            still_path = STILLS_DIR / still_filename
            if not still_path.exists():
                still_path = STILLS_DIR / "coke_hero.jpg" """

new_still_block = """            # Visual / Image Generation Engine Resolution
            req_img_model = getattr(req, "image_model", "flux2_klein_4b") or "flux2_klein_4b"
            IMAGE_DISPLAY_NAMES = {
                "flux2_klein_4b": "FLUX.2 Klein (4B Diffusion)",
                "sana_1600m": "Sana 1600M (Linear Diffusion)",
                "z_image_turbo": "SDXL Turbo (Single-Step Diffusion)",
                "nano_banana_21": "Nano Banana 2.1 (Multi-Ref Anchor)",
                "midjourney_v6": "Midjourney v6 (Commercial Studio)"
            }
            img_model_display = IMAGE_DISPLAY_NAMES.get(req_img_model, "FLUX.2 Klein (4B Diffusion)")

            # Check if category has a model-specific generated still (e.g., sneaker, kettle, serum, tshirt)
            model_specific_still = STILLS_DIR / f"img__{category}__{req_img_model}__seed42.png"
            if model_specific_still.exists() and idx != 2:
                still_path = model_specific_still
            else:
                still_filename = stills_list[(idx - 1) % len(stills_list)]
                still_path = STILLS_DIR / still_filename
                if not still_path.exists():
                    still_path = STILLS_DIR / "coke_hero.jpg" """

# Let's inspect where still_filename = stills_list is
idx_s = main_txt.find("still_filename = stills_list[(idx - 1) % len(stills_list)]")
if idx_s != -1:
    f_start = main_txt.rfind("else:", 0, idx_s) + 5
    f_end = main_txt.find("is_vertical =", idx_s)
    main_txt = main_txt[:f_start] + "\n" + new_still_block + "\n\n            " + main_txt[f_end:]
    print("Patched still resolution block in main.py")
else:
    print("Could not find still_filename assignment in main.py")

# C. Update model_name and provider assignment in main.py
old_model_assign = """            asset_source = "static_image_kenburns"
            provider = "ffmpeg_kenburns_v2"
            model_name = "FLUX.2-Klein-4B-Motion" """

idx_m = main_txt.find('model_name = "FLUX.2-Klein-4B-Motion"')
if idx_m != -1:
    line_start = main_txt.rfind('asset_source = "static_image_kenburns"', 0, idx_m)
    line_end = main_txt.find('\n', idx_m)
    new_assign = """            asset_source = "static_image_kenburns"
            provider = "synquic_diffusion_pipeline"
            model_name = f"{img_model_display} + {_ms}" """
    main_txt = main_txt[:line_start] + new_assign + main_txt[line_end:]
    print("Patched model_name & provider assignment in main.py")
else:
    print("Could not find model_name = FLUX.2-Klein-4B-Motion in main.py")

# D. Add image_model to manifest_data and return dict
if '"image_model":' not in main_txt:
    main_txt = main_txt.replace(
        '"director_model": req.director_model,',
        '"director_model": req.director_model,\n        "image_model": getattr(req, "image_model", "flux2_klein_4b"),',
        1
    )
    main_txt = main_txt.replace(
        '"category": category,',
        '"category": category,\n        "image_model": getattr(req, "image_model", "flux2_klein_4b"),',
        1
    )
    print("Added image_model to manifest_data and return dict in main.py")

MAIN.write_text(main_txt, encoding="utf-8")
print("Saved updated main.py")


# -------------------------------------------------------------
# 2. UPDATE web_ec2/templates/index.html
# -------------------------------------------------------------
html = INDEX.read_text(encoding="utf-8")

# Replace 3 engine cards with 4 engine cards in index.html
old_3cards = """                        <!-- 3 Engine Selector Cards -->
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
                            <!-- ENGINE 1: STORY & SCRIPT DIRECTOR -->
                            <div class="studio-glass p-3 rounded-xl border border-emerald-500/30 bg-emerald-950/20">
                                <label class="text-[10px] font-bold text-emerald-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-clapperboard"></i> 1. Story / Script Engine
                                </label>
                                <select id="studioModelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-emerald-500">
                                    <optgroup label="⚡ Ultra-Fast Director">
                                        <option value="nvidia/nemotron-3.5-lightning-30b-a3b" selected>NVIDIA Nemotron 3.5 Lightning (30B) ⚡</option>
                                        <option value="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning">NVIDIA Nemotron Nano Omni (30B Reasoning)</option>
                                        <option value="deepseek-ai/deepseek-v4.1-flash">DeepSeek V4.1 Flash (High Efficiency)</option>
                                        <option value="minimaxai/minimax-m3.1-flash">MiniMax M3.1 Flash</option>
                                    </optgroup>
                                    <optgroup label="🧠 Frontier Commercial Directors">
                                        <option value="mistralai/mistral-large-4-1t-a52b">Mistral Large 4 (Frontier Director)</option>
                                        <option value="nvidia/llama-3.1-nemotron-ultra-253b-v1">NVIDIA Nemotron Ultra 253B v1</option>
                                        <option value="nvidia/nemotron-3-super-120b-a12b">NVIDIA Nemotron 3 Super 120B</option>
                                        <option value="nvidia/llama-3.1-nemotron-70b-instruct">NVIDIA Nemotron 70B Instruct</option>
                                        <option value="nvidia/nemotron-4-340b-instruct">NVIDIA Nemotron 4 340B Instruct</option>
                                        <option value="moonshotai/kimi-k2.6">MoonshotAI Kimi K2.6</option>
                                    </optgroup>
                                    <optgroup label="✍️ Creative Copy Specialists">
                                        <option value="writer/palmyra-creative-122b">Writer Palmyra Creative 122B</option>
                                        <option value="meta/muse-glimmer-30b">Meta Muse Glimmer 30B</option>
                                        <option value="z-ai/glm-5.3-flash">Z-AI GLM 5.3 Flash</option>
                                        <option value="poolside/laguna-xs-2.1">Poolside Laguna XS 2.1</option>
                                    </optgroup>
                                    <optgroup label="📱 Google / Gemma">
                                        <option value="google/gemma-4-31b-it">Google Gemma 4 (31B Instruct)</option>
                                        <option value="google/gemma-3-12b-it">Google Gemma 3 (12B Instruct)</option>
                                    </optgroup>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">Writes scene JSON, narration & on-screen typography</span>
                            </div>

                            <!-- ENGINE 2: AUDIO VOICE ENGINE -->
                            <div class="studio-glass p-3 rounded-xl border border-purple-500/30 bg-purple-950/20">
                                <label class="text-[10px] font-bold text-purple-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-microphone"></i> 2. Audio Voice Engine
                                </label>
                                <select id="studioVoiceSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-purple-500">
                                    <optgroup label="⚡ Intelligent Auto">
                                        <option value="auto" selected>Auto (Based on Product Category)</option>
                                    </optgroup>
                                    <optgroup label="🇺🇸 US Male Voices">
                                        <option value="en-US-ChristopherNeural">Christopher (US Male - Commercial Grade) ★</option>
                                        <option value="en-US-AndrewNeural">Andrew (US Male - Warm & Natural)</option>
                                        <option value="en-US-BrianNeural">Brian (US Male - Confident & Punchy)</option>
                                        <option value="en-US-EricNeural">Eric (US Male - Corporate Authority)</option>
                                        <option value="en-US-GuyNeural">Guy (US Male - Dynamic Energetic)</option>
                                        <option value="en-US-RogerNeural">Roger (US Male - News Anchor Tone)</option>
                                        <option value="en-US-SteffanNeural">Steffan (US Male - Smooth Luxury)</option>
                                    </optgroup>
                                    <optgroup label="🇺🇸 US Female Voices">
                                        <option value="en-US-AriaNeural">Aria (US Female - Luxury Skincare/Perfume) ★</option>
                                        <option value="en-US-AvaNeural">Ava (US Female - Modern Commercial)</option>
                                        <option value="en-US-EmmaNeural">Emma (US Female - Young Approachable)</option>
                                        <option value="en-US-JennyNeural">Jenny (US Female - Warm Professional)</option>
                                        <option value="en-US-MichelleNeural">Michelle (US Female - Elegant Clear)</option>
                                    </optgroup>
                                    <optgroup label="🇬🇧 British & International">
                                        <option value="en-GB-RyanNeural">Ryan (British Male - High-End Luxury)</option>
                                        <option value="en-GB-SoniaNeural">Sonia (British Female - Velvet Elegance)</option>
                                        <option value="en-IN-PrabhatNeural">Prabhat (Indian English Male)</option>
                                        <option value="en-IN-NeerjaExpressiveNeural">Neerja (Indian English Expressive)</option>
                                        <option value="en-AU-WilliamMultilingualNeural">William (Australian Multilingual)</option>
                                    </optgroup>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">Microsoft Edge Neural TTS (48kHz AAC stereo + BGM)</span>
                            </div>

                            <!-- ENGINE 3: VISUAL MOTION ENGINE -->
                            <div class="studio-glass p-3 rounded-xl border border-cyan-500/30 bg-cyan-950/20">
                                <label class="text-[10px] font-bold text-cyan-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-film"></i> 3. Visual Motion Engine
                                </label>
                                <select id="studioMotionSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-cyan-500">
                                    <option value="kenburns_cinematic" selected>Ken Burns Cinematic (Dynamic Zoom & Pan)</option>
                                    <option value="kenburns_slow">Ken Burns Slow Reveal (Luxury Pacing)</option>
                                    <option value="kenburns_dolly">Ken Burns Dolly Slide (Lateral Movement)</option>
                                    <option value="kenburns_pullback">Ken Burns Pull-Back (Drama Finish)</option>
                                    <option value="kenburns_aggressive">Ken Burns Aggressive Push (Kinetic)</option>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">FFmpeg 24fps camera trajectory & kinetic typography</span>
                            </div>
                        </div>"""

new_4cards = """                        <!-- 4 Dedicated Pipeline Engine Selector Cards -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-3">
                            <!-- ENGINE 1: STORY & SCRIPT DIRECTOR -->
                            <div class="studio-glass p-3 rounded-xl border border-emerald-500/30 bg-emerald-950/20">
                                <label class="text-[10px] font-bold text-emerald-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-clapperboard"></i> 1. Story / Script Engine
                                </label>
                                <select id="studioModelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-emerald-500">
                                    <optgroup label="⚡ Ultra-Fast Director">
                                        <option value="nvidia/nemotron-3.5-lightning-30b-a3b" selected>NVIDIA Nemotron 3.5 Lightning (30B) ⚡</option>
                                        <option value="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning">NVIDIA Nemotron Nano Omni (30B Reasoning)</option>
                                        <option value="deepseek-ai/deepseek-v4.1-flash">DeepSeek V4.1 Flash (High Efficiency)</option>
                                        <option value="minimaxai/minimax-m3.1-flash">MiniMax M3.1 Flash</option>
                                    </optgroup>
                                    <optgroup label="🧠 Frontier Commercial Directors">
                                        <option value="mistralai/mistral-large-4-1t-a52b">Mistral Large 4 (Frontier Director)</option>
                                        <option value="nvidia/llama-3.1-nemotron-ultra-253b-v1">NVIDIA Nemotron Ultra 253B v1</option>
                                        <option value="nvidia/nemotron-3-super-120b-a12b">NVIDIA Nemotron 3 Super 120B</option>
                                        <option value="nvidia/llama-3.1-nemotron-70b-instruct">NVIDIA Nemotron 70B Instruct</option>
                                        <option value="nvidia/nemotron-4-340b-instruct">NVIDIA Nemotron 4 340B Instruct</option>
                                        <option value="moonshotai/kimi-k2.6">MoonshotAI Kimi K2.6</option>
                                    </optgroup>
                                    <optgroup label="✍️ Creative Copy Specialists">
                                        <option value="writer/palmyra-creative-122b">Writer Palmyra Creative 122B</option>
                                        <option value="meta/muse-glimmer-30b">Meta Muse Glimmer 30B</option>
                                        <option value="z-ai/glm-5.3-flash">Z-AI GLM 5.3 Flash</option>
                                    </optgroup>
                                    <optgroup label="📱 Google / Gemma">
                                        <option value="google/gemma-4-31b-it">Google Gemma 4 (31B Instruct)</option>
                                        <option value="google/gemma-3-12b-it">Google Gemma 3 (12B Instruct)</option>
                                    </optgroup>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">Writes scene JSON, narrative pacing & typography</span>
                            </div>

                            <!-- ENGINE 2: VISUAL / IMAGE GENERATION ENGINE (NEW!) -->
                            <div class="studio-glass p-3 rounded-xl border border-amber-500/30 bg-amber-950/20">
                                <label class="text-[10px] font-bold text-amber-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-wand-magic-sparkles"></i> 2. Image Generation Model
                                </label>
                                <select id="studioImageModelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-amber-500">
                                    <optgroup label="🌟 Photorealism Diffusion SOTA">
                                        <option value="flux2_klein_4b" selected>FLUX.2 Klein (4B Diffusion SOTA) ★</option>
                                        <option value="sana_1600m">Sana 1600M (DeepDataMining 4K Linear)</option>
                                        <option value="z_image_turbo">SDXL Turbo (Single-Step Real-Time)</option>
                                    </optgroup>
                                    <optgroup label="🎯 Commercial Reference Engines">
                                        <option value="nano_banana_21">Nano Banana 2.1 (Multi-Ref Brand Anchor)</option>
                                        <option value="midjourney_v6">Midjourney v6 (Commercial Studio Lighting)</option>
                                    </optgroup>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">Renders high-res 4K keyframe stills for each shot</span>
                            </div>

                            <!-- ENGINE 3: AUDIO VOICE ENGINE -->
                            <div class="studio-glass p-3 rounded-xl border border-purple-500/30 bg-purple-950/20">
                                <label class="text-[10px] font-bold text-purple-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-microphone"></i> 3. Audio Voice Engine
                                </label>
                                <select id="studioVoiceSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-purple-500">
                                    <optgroup label="⚡ Intelligent Auto">
                                        <option value="auto" selected>Auto (Based on Product Category)</option>
                                    </optgroup>
                                    <optgroup label="🇺🇸 US Male Voices">
                                        <option value="en-US-ChristopherNeural">Christopher (US Male - Commercial Grade) ★</option>
                                        <option value="en-US-AndrewNeural">Andrew (US Male - Warm & Natural)</option>
                                        <option value="en-US-BrianNeural">Brian (US Male - Confident & Punchy)</option>
                                        <option value="en-US-EricNeural">Eric (US Male - Corporate Authority)</option>
                                        <option value="en-US-GuyNeural">Guy (US Male - Dynamic Energetic)</option>
                                        <option value="en-US-RogerNeural">Roger (US Male - News Anchor Tone)</option>
                                        <option value="en-US-SteffanNeural">Steffan (US Male - Smooth Luxury)</option>
                                    </optgroup>
                                    <optgroup label="🇺🇸 US Female Voices">
                                        <option value="en-US-AriaNeural">Aria (US Female - Luxury Skincare/Perfume) ★</option>
                                        <option value="en-US-AvaNeural">Ava (US Female - Modern Commercial)</option>
                                        <option value="en-US-EmmaNeural">Emma (US Female - Young Approachable)</option>
                                        <option value="en-US-JennyNeural">Jenny (US Female - Warm Professional)</option>
                                        <option value="en-US-MichelleNeural">Michelle (US Female - Elegant Clear)</option>
                                    </optgroup>
                                    <optgroup label="🇬🇧 British & International">
                                        <option value="en-GB-RyanNeural">Ryan (British Male - High-End Luxury)</option>
                                        <option value="en-GB-SoniaNeural">Sonia (British Female - Velvet Elegance)</option>
                                        <option value="en-IN-PrabhatNeural">Prabhat (Indian English Male)</option>
                                        <option value="en-IN-NeerjaExpressiveNeural">Neerja (Indian English Expressive)</option>
                                        <option value="en-AU-WilliamMultilingualNeural">William (Australian Multilingual)</option>
                                    </optgroup>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">Microsoft Edge Neural TTS (48kHz AAC stereo + BGM)</span>
                            </div>

                            <!-- ENGINE 4: VISUAL MOTION ENGINE -->
                            <div class="studio-glass p-3 rounded-xl border border-cyan-500/30 bg-cyan-950/20">
                                <label class="text-[10px] font-bold text-cyan-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-film"></i> 4. Visual Motion Engine
                                </label>
                                <select id="studioMotionSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-cyan-500">
                                    <option value="kenburns_cinematic" selected>Ken Burns Cinematic (Dynamic Zoom & Pan)</option>
                                    <option value="kenburns_slow">Ken Burns Slow Reveal (Luxury Pacing)</option>
                                    <option value="kenburns_dolly">Ken Burns Dolly Slide (Lateral Movement)</option>
                                    <option value="kenburns_pullback">Ken Burns Pull-Back (Drama Finish)</option>
                                    <option value="kenburns_aggressive">Ken Burns Aggressive Push (Kinetic)</option>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">FFmpeg 24fps camera trajectory & kinetic typography</span>
                            </div>
                        </div>"""

if old_3cards in html:
    html = html.replace(old_3cards, new_4cards, 1)
    print("Upgraded 3-engine cards to 4-engine cards (including Image Generation Engine)")
else:
    old_3cards_crlf = old_3cards.replace("\n", "\r\n")
    new_4cards_crlf = new_4cards.replace("\n", "\r\n")
    if old_3cards_crlf in html:
        html = html.replace(old_3cards_crlf, new_4cards_crlf, 1)
        print("Upgraded 3-engine cards to 4-engine cards (CRLF)")
    else:
        print("Could not find old_3cards in index.html")

# Update fetch body in JS to send image_model
old_fetch_js = """            const voice = document.getElementById('studioVoiceSelect')?.value || 'auto';
            const motion = document.getElementById('studioMotionSelect')?.value || 'kenburns_cinematic';

            const res = await fetch('/api/studio/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    director_model: model,
                    duration_s: duration,
                    style: style,
                    aspect_ratio: aspect,
                    audio_voice: voice,
                    motion_style: motion
                })
            });"""

new_fetch_js = """            const imgModel = document.getElementById('studioImageModelSelect')?.value || 'flux2_klein_4b';
            const voice = document.getElementById('studioVoiceSelect')?.value || 'auto';
            const motion = document.getElementById('studioMotionSelect')?.value || 'kenburns_cinematic';

            const res = await fetch('/api/studio/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    director_model: model,
                    image_model: imgModel,
                    duration_s: duration,
                    style: style,
                    aspect_ratio: aspect,
                    audio_voice: voice,
                    motion_style: motion
                })
            });"""

if old_fetch_js in html:
    html = html.replace(old_fetch_js, new_fetch_js, 1)
    print("Updated JS fetch call to pass image_model")
else:
    idx_f = html.find("const res = await fetch('/api/studio/generate'")
    if idx_f != -1:
        f_start = html.rfind("const voice =", 0, idx_f)
        f_end = html.find("});", idx_f) + 3
        html = html[:f_start] + new_fetch_js + html[f_end:]
        print("Replaced fetch call with image_model successfully!")
    else:
        print("Could not locate fetch call in index.html")

# Display Image Model in Results Panel
old_out_row = """                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Audio Voice Engine</span>"""

new_out_row = """                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Image Generation Model</span>
                                    <span class="text-amber-300 font-mono text-[11px]" id="outImageEngine">FLUX.2 Klein (4B Diffusion)</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Audio Voice Engine</span>"""

if old_out_row in html:
    html = html.replace(old_out_row, new_out_row, 1)
    print("Added Image Engine row to result panel in index.html")

# In renderStudioResult JS: assign outImageEngine
old_assign_js = """            if (document.getElementById('outVoiceEngine')) document.getElementById('outVoiceEngine').innerText = data.audio_voice || 'Default';"""
new_assign_js = """            if (document.getElementById('outImageEngine')) document.getElementById('outImageEngine').innerText = data.image_model || 'FLUX.2 Klein 4B';
            if (document.getElementById('outVoiceEngine')) document.getElementById('outVoiceEngine').innerText = data.audio_voice || 'Default';"""

if old_assign_js in html:
    html = html.replace(old_assign_js, new_assign_js, 1)
    print("Added outImageEngine assignment in renderStudioResult")

INDEX.write_text(html, encoding="utf-8")
print("Saved updated index.html")
