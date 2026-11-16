from pathlib import Path

index_path = Path("d:/research_synquic/web_ec2/templates/index.html")
html = index_path.read_text(encoding="utf-8")

old_selectors_block = """                    <!-- Pipeline Engine Selectors -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800">
                        <div>
                            <label class="text-[11px] font-bold text-slate-300 block mb-1">Director Engine Model</label>
                            <select id="studioModelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-emerald-500">
                                <option value="nvidia/nemotron-3.5-lightning-30b-a3b" selected>NVIDIA Nemotron 3.5 Lightning (30B)</option>
                                <option value="mistralai/mistral-large-4-1t-a52b">Mistral Large 4 (Frontier Director)</option>
                                <option value="deepseek-ai/deepseek-v4.1-flash">DeepSeek V4.1 Flash (High Efficiency)</option>
                                <option value="google/gemma-4-31b-it">Google Gemma 4 (31B Instruct)</option>
                            </select>
                        </div>

                        <div>
                            <label class="text-[11px] font-bold text-slate-300 block mb-1">Commercial Duration</label>
                            <select id="studioDurationSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-emerald-500">
                                <option value="15" selected>15 Seconds (3 Shots - Rapid Commercial)</option>
                                <option value="30">30 Seconds (6 Shots - Full Narrative)</option>
                            </select>
                        </div>

                        <div>
                            <label class="text-[11px] font-bold text-slate-300 block mb-1">Commercial Style</label>
                            <select id="studioStyleSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-emerald-500">
                                <option value="Luxury Minimalist" selected>Luxury Minimalist (Soft Light & Bokeh)</option>
                                <option value="Kinetic Urban Commercial">Kinetic Urban (High Energy Streetwear)</option>
                                <option value="Warm Artisanal Lifestyle">Warm Artisanal (Morning Kitchen Ritual)</option>
                                <option value="High-Tech Sci-Fi">High-Tech Sci-Fi (Neon Reflections)</option>
                            </select>
                        </div>

                        <div>
                            <label class="text-[11px] font-bold text-slate-300 block mb-1">Aspect Ratio</label>
                            <select id="studioAspectSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-emerald-500">
                                <option value="16:9" selected>16:9 Landscape (YouTube, Web, TV)</option>
                                <option value="9:16">9:16 Vertical (Reels, TikTok, Shorts)</option>
                            </select>
                        </div>
                    </div>"""

new_selectors_block = """                    <!-- Pipeline Engine Selectors -->
                    <div class="pt-3 border-t border-slate-800">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5 mb-2.5">
                            <i class="fa-solid fa-sliders"></i> Autonomous Multi-Engine Configuration
                        </span>

                        <!-- 3 Engine Selector Cards -->
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
                        </div>

                        <!-- Secondary Parameters: Duration, Style, Aspect Ratio -->
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-800/80">
                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Commercial Duration</label>
                                <select id="studioDurationSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                    <option value="15" selected>15s (3 Shots - Rapid Commercial)</option>
                                    <option value="30">30s (6 Shots - Full Narrative)</option>
                                </select>
                            </div>

                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Commercial Style</label>
                                <select id="studioStyleSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                    <option value="Luxury Minimalist" selected>Luxury Minimalist (Soft Light & Bokeh)</option>
                                    <option value="Kinetic Urban Commercial">Kinetic Urban (High Energy Streetwear)</option>
                                    <option value="Warm Artisanal Lifestyle">Warm Artisanal (Morning Kitchen Ritual)</option>
                                    <option value="High-Tech Sci-Fi">High-Tech Sci-Fi (Neon Reflections)</option>
                                </select>
                            </div>

                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Aspect Ratio</label>
                                <select id="studioAspectSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                    <option value="16:9" selected>16:9 Landscape (YouTube, Web, TV)</option>
                                    <option value="9:16">9:16 Vertical (Reels, TikTok, Shorts)</option>
                                </select>
                            </div>
                        </div>
                    </div>"""

if old_selectors_block in html:
    html = html.replace(old_selectors_block, new_selectors_block, 1)
    print("Replaced selectors block (LF)")
else:
    old_crlf = old_selectors_block.replace("\n", "\r\n")
    new_crlf = new_selectors_block.replace("\n", "\r\n")
    if old_crlf in html:
        html = html.replace(old_crlf, new_crlf, 1)
        print("Replaced selectors block (CRLF)")
    else:
        print("Could not match old_selectors_block! Searching...")
        idx = html.find("Pipeline Engine Selectors")
        print("Snippet around selectors:", repr(html[idx:idx+300]))

# Also ensure JS safely reads voice & motion with optional chaining
old_js_call = """            const res = await fetch('/api/studio/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    director_model: model,
                    duration_s: duration,
                    style: style,
                    aspect_ratio: aspect,
                    audio_voice: document.getElementById('studioVoiceSelect').value,
                    motion_style: document.getElementById('studioMotionSelect').value
                })
            });"""

safe_js_call = """            const voice = document.getElementById('studioVoiceSelect')?.value || 'auto';
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

if old_js_call in html:
    html = html.replace(old_js_call, safe_js_call, 1)
    print("Updated JS with safe optional chaining (LF)")
else:
    old_js_crlf = old_js_call.replace("\n", "\r\n")
    safe_js_crlf = safe_js_call.replace("\n", "\r\n")
    if old_js_crlf in html:
        html = html.replace(old_js_crlf, safe_js_crlf, 1)
        print("Updated JS with safe optional chaining (CRLF)")
    else:
        # Search for studioVoiceSelect in fetch call
        idx = html.find("audio_voice: document.getElementById('studioVoiceSelect')")
        if idx != -1:
            print("Found studioVoiceSelect in fetch call at:", idx)
            # Find the fetch block and replace it
            f_start = html.rfind("const res = await fetch", 0, idx)
            f_end = html.find("});", idx) + 3
            print("Replacing fetch block:", repr(html[f_start:f_end]))
            html = html[:f_start] + safe_js_call + html[f_end:]
            print("Replaced fetch block safely!")
        else:
            print("studioVoiceSelect not found in fetch call")

index_path.write_text(html, encoding="utf-8")
print("Saved index.html successfully!")
