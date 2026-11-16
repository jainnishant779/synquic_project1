import re

with open("web_ec2/templates/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Product Reference Vault + 5 Engine Cards + Secondary Parameters
old_engine_section = '''                    <!-- Pipeline Engine Selectors -->
                    <div class="pt-3 border-t border-slate-800">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5 mb-2.5">
                            <i class="fa-solid fa-sliders"></i> Autonomous Multi-Engine Configuration
                        </span>

                        <!-- 4 Dedicated Pipeline Engine Selector Cards -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-3">
                            <!-- ENGINE 1: STORY & SCRIPT DIRECTOR -->
                            <div class="studio-glass p-3 rounded-xl border border-emerald-500/30 bg-emerald-950/20">
                                <label class="text-[10px] font-bold text-emerald-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-clapperboard"></i> 1. Story / Script Engine
                                </label>
                                <select id="studioModelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-emerald-500">
                                    <optgroup label="âš¡ Ultra-Fast Director">
                                        <option value="nvidia/nemotron-3.5-lightning-30b-a3b" selected>NVIDIA Nemotron 3.5 Lightning (30B) âš¡</option>
                                        <option value="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning">NVIDIA Nemotron Nano Omni (30B Reasoning)</option>
                                        <option value="deepseek-ai/deepseek-v4.1-flash">DeepSeek V4.1 Flash (High Efficiency)</option>
                                        <option value="minimaxai/minimax-m3.1-flash">MiniMax M3.1 Flash</option>
                                    </optgroup>
                                    <optgroup label="ðŸ§  Frontier Commercial Directors">
                                        <option value="mistralai/mistral-large-4-1t-a52b">Mistral Large 4 (Frontier Director)</option>
                                        <option value="nvidia/llama-3.1-nemotron-ultra-253b-v1">NVIDIA Nemotron Ultra 253B v1</option>
                                        <option value="nvidia/nemotron-3-super-120b-a12b">NVIDIA Nemotron 3 Super 120B</option>
                                        <option value="nvidia/llama-3.1-nemotron-70b-instruct">NVIDIA Nemotron 70B Instruct</option>
                                        <option value="nvidia/nemotron-4-340b-instruct">NVIDIA Nemotron 4 340B Instruct</option>
                                        <option value="moonshotai/kimi-k2.6">MoonshotAI Kimi K2.6</option>
                                    </optgroup>
                                    <optgroup label="âœ ï¸  Creative Copy Specialists">
                                        <option value="writer/palmyra-creative-122b">Writer Palmyra Creative 122B</option>
                                        <option value="meta/muse-glimmer-30b">Meta Muse Glimmer 30B</option>
                                        <option value="z-ai/glm-5.3-flash">Z-AI GLM 5.3 Flash</option>
                                    </optgroup>
                                    <optgroup label="ðŸ“± Google / Gemma">
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
                                    <optgroup label="ðŸŒŸ Photorealism Diffusion SOTA">
                                        <option value="flux2_klein_4b" selected>FLUX.2 Klein (4B Diffusion SOTA) â˜…</option>
                                        <option value="sana_1600m">Sana 1600M (DeepDataMining 4K Linear)</option>
                                        <option value="z_image_turbo">SDXL Turbo (Single-Step Real-Time)</option>
                                    </optgroup>
                                    <optgroup label="ðŸŽ¯ Commercial Reference Engines">
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
                                    <optgroup label="âš¡ Intelligent Auto">
                                        <option value="auto" selected>Auto (Based on Product Category)</option>
                                    </optgroup>
                                    <optgroup label="ðŸ‡ºðŸ‡¸ US Male Voices">
                                        <option value="en-US-ChristopherNeural">Christopher (US Male - Commercial Grade) â˜…</option>
                                        <option value="en-US-AndrewNeural">Andrew (US Male - Warm & Natural)</option>
                                        <option value="en-US-BrianNeural">Brian (US Male - Confident & Punchy)</option>
                                        <option value="en-US-EricNeural">Eric (US Male - Corporate Authority)</option>
                                        <option value="en-US-GuyNeural">Guy (US Male - Dynamic Energetic)</option>
                                        <option value="en-US-RogerNeural">Roger (US Male - News Anchor Tone)</option>
                                        <option value="en-US-SteffanNeural">Steffan (US Male - Smooth Luxury)</option>
                                    </optgroup>
                                    <optgroup label="ðŸ‡ºðŸ‡¸ US Female Voices">
                                        <option value="en-US-AriaNeural">Aria (US Female - Luxury Skincare/Perfume) â˜…</option>
                                        <option value="en-US-AvaNeural">Ava (US Female - Modern Commercial)</option>
                                        <option value="en-US-EmmaNeural">Emma (US Female - Young Approachable)</option>
                                        <option value="en-US-JennyNeural">Jenny (US Female - Warm Professional)</option>
                                        <option value="en-US-MichelleNeural">Michelle (US Female - Elegant Clear)</option>
                                    </optgroup>
                                    <optgroup label="ðŸ‡¬ðŸ‡§ British & International">
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
                    </div>'''

new_engine_section = '''                    <!-- PRODUCT REFERENCE VAULT (I2V ANCHOR) -->
                    <div class="p-3 rounded-xl border border-dashed border-cyan-500/40 bg-cyan-950/20 flex flex-col sm:flex-row items-center justify-between gap-3">
                        <div class="flex items-center gap-3">
                            <div class="w-9 h-9 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-base border border-cyan-500/30">
                                <i class="fa-solid fa-camera"></i>
                            </div>
                            <div>
                                <span class="text-xs font-bold text-white block">Product Reference Image Anchor</span>
                                <span class="text-[10px] text-slate-400 block">Upload exact packaging, bottle, shoe or UI for Image-to-Video (I2V) identity preservation</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <input type="file" id="studioReferenceFile" accept="image/*" class="hidden" onchange="handleReferenceUpload(this)">
                            <div id="refThumbContainer" class="hidden flex items-center gap-2 p-1 px-2.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40">
                                <img id="refThumb" src="" class="w-7 h-7 object-cover rounded">
                                <span class="text-[10px] text-emerald-300 font-bold">Anchor Locked</span>
                                <button type="button" onclick="removeReference()" class="text-xs text-rose-400 hover:text-rose-300 ml-1"><i class="fa-solid fa-xmark"></i></button>
                            </div>
                            <button type="button" id="btnUploadRef" onclick="document.getElementById('studioReferenceFile').click()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/40 text-xs font-semibold flex items-center gap-1.5 transition">
                                <i class="fa-solid fa-cloud-arrow-up"></i> Upload Reference
                            </button>
                        </div>
                    </div>

                    <!-- Pipeline Engine Selectors -->
                    <div class="pt-3 border-t border-slate-800">
                        <div class="flex items-center justify-between mb-2.5">
                            <span class="text-[10px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                                <i class="fa-solid fa-sliders"></i> Autonomous Multi-Engine Configuration
                            </span>
                            <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] font-mono font-bold">
                                NVIDIA-Only Quality Policy
                            </span>
                        </div>

                        <!-- 5 Dedicated Pipeline Engine Selector Cards -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5 mb-3">
                            <!-- ENGINE 1: STORY & SCRIPT (NVIDIA NIM) -->
                            <div class="studio-glass p-2.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20">
                                <label class="text-[10px] font-bold text-emerald-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-clapperboard"></i> 1. Script Director
                                </label>
                                <select id="studioModelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-emerald-500">
                                    <option value="nvidia/nemotron-3.5-lightning-30b-a3b" selected>Nemotron 3.5 (30B) ⚡</option>
                                    <option value="nvidia/llama-3.1-nemotron-70b-instruct">Nemotron 70B</option>
                                    <option value="writer/palmyra-creative-122b">Palmyra Creative 122B</option>
                                    <option value="deepseek-ai/deepseek-v4.1-flash">DeepSeek V4.1 Flash</option>
                                    <option value="google/gemma-4-31b-it">Google Gemma 4 (31B)</option>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">Writes scene JSON & script</span>
                            </div>

                            <!-- ENGINE 2: KEYFRAME STILLS (DIFFUSION) -->
                            <div class="studio-glass p-2.5 rounded-xl border border-amber-500/30 bg-amber-950/20">
                                <label class="text-[10px] font-bold text-amber-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-wand-magic-sparkles"></i> 2. Keyframe Stills
                                </label>
                                <select id="studioImageModelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-amber-500">
                                    <option value="flux2_klein_4b" selected>FLUX.2 Klein 4B ★</option>
                                    <option value="sana_1600m">Sana 1600M Linear</option>
                                    <option value="z_image_turbo">SDXL Turbo Real-Time</option>
                                    <option value="nano_banana_21">Nano Banana 2.1</option>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">4K keyframes for I2V</span>
                            </div>

                            <!-- ENGINE 3: DEDICATED AI VIDEO MODEL (NVIDIA NIM) -->
                            <div class="studio-glass p-2.5 rounded-xl border border-green-500/40 bg-green-950/30 ring-1 ring-green-500/30">
                                <label class="text-[10px] font-bold text-green-300 block mb-1 flex items-center justify-between">
                                    <span class="flex items-center gap-1"><i class="fa-solid fa-video"></i> 3. AI Video Model</span>
                                    <span class="px-1 py-0.2 rounded bg-green-500/20 text-green-300 text-[8px] font-mono">NVIDIA</span>
                                </label>
                                <select id="studioVideoModelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-green-500">
                                    <option value="wan-ai/wan2.2" selected>NVIDIA Wan 2.2 (14B NIM) ★</option>
                                    <option value="wan-ai/wan2.2-i2v">NVIDIA Wan 2.2 (I2V Anchor)</option>
                                    <option value="wan-ai/wan2.2-t2v">NVIDIA Wan 2.2 (T2V Direct)</option>
                                </select>
                                <div class="grid grid-cols-2 gap-1 mt-1">
                                    <select id="studioVideoTaskSelect" class="bg-slate-950 border border-slate-700 rounded p-1 text-[9px] text-slate-300">
                                        <option value="image_to_video" selected>I2V (Anchor)</option>
                                        <option value="text_to_video">T2V (Direct)</option>
                                    </select>
                                    <select id="studioGenModeSelect" class="bg-slate-950 border border-slate-700 rounded p-1 text-[9px] text-slate-300">
                                        <option value="full_ai" selected>Full AI</option>
                                        <option value="hybrid_fallback">Hybrid</option>
                                    </select>
                                </div>
                            </div>

                            <!-- ENGINE 4: AUDIO VOICE ENGINE -->
                            <div class="studio-glass p-2.5 rounded-xl border border-purple-500/30 bg-purple-950/20">
                                <label class="text-[10px] font-bold text-purple-400 block mb-1 flex items-center gap-1">
                                    <i class="fa-solid fa-microphone"></i> 4. Voiceover Engine
                                </label>
                                <select id="studioVoiceSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-purple-500">
                                    <option value="auto" selected>Auto Category Voice</option>
                                    <option value="en-US-ChristopherNeural">Christopher (US Male) ★</option>
                                    <option value="en-US-AriaNeural">Aria (US Female) ★</option>
                                    <option value="en-US-AndrewNeural">Andrew (US Male Natural)</option>
                                    <option value="en-GB-RyanNeural">Ryan (British Luxury)</option>
                                    <option value="en-IN-PrabhatNeural">Prabhat (Indian English)</option>
                                </select>
                                <span class="text-[9px] text-slate-400 block mt-1">48kHz neural voiceover</span>
                            </div>

                            <!-- ENGINE 5: IMAGE MOTION FALLBACK ENGINE (FFMPEG) -->
                            <div class="studio-glass p-2.5 rounded-xl border border-cyan-500/30 bg-cyan-950/20">
                                <label class="text-[10px] font-bold text-cyan-400 block mb-1 flex items-center justify-between">
                                    <span class="flex items-center gap-1"><i class="fa-solid fa-film"></i> 5. Fallback Motion</span>
                                    <span class="px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 text-[8px] font-mono">FALLBACK</span>
                                </label>
                                <select id="studioMotionSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-[11px] text-white focus:outline-none focus:border-cyan-500">
                                    <option value="kenburns_cinematic" selected>Ken Burns Cinematic</option>
                                    <option value="kenburns_slow">Ken Burns Slow Reveal</option>
                                    <option value="kenburns_dolly">Ken Burns Dolly Slide</option>
                                    <option value="kenburns_pullback">Ken Burns Pull-Back</option>
                                </select>
                                <label class="flex items-center gap-1 text-[9px] text-amber-300 mt-1 cursor-pointer select-none">
                                    <input type="checkbox" id="studioAllowFallbackCheck" checked class="rounded border-slate-700 text-emerald-500 focus:ring-0">
                                    <span>Allow Fallback if GPU is offline</span>
                                </label>
                            </div>
                        </div>

                        <!-- Secondary Parameters: Duration, Resolution, Quality Preset, Aspect Ratio -->
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-slate-800/80">
                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Commercial Duration</label>
                                <select id="studioDurationSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                    <option value="15" selected>15s (3 Shots - Rapid Commercial)</option>
                                    <option value="30">30s (6 Shots - Full Narrative)</option>
                                </select>
                            </div>

                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Export Resolution</label>
                                <select id="studioResolutionSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                    <option value="1080p" selected>1080p Full HD (Target)</option>
                                    <option value="720p">720p HD (Native)</option>
                                </select>
                            </div>

                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Quality Preset</label>
                                <select id="studioQualityPresetSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                    <option value="high" selected>High (50 Steps Broadcast)</option>
                                    <option value="standard">Standard (30 Steps Rapid)</option>
                                </select>
                            </div>

                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Aspect Ratio</label>
                                <select id="studioAspectSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                    <option value="16:9" selected>16:9 Landscape (Web, TV)</option>
                                    <option value="9:16">9:16 Vertical (Reel, Shorts)</option>
                                </select>
                            </div>
                        </div>
                    </div>'''

if old_engine_section in html:
    html = html.replace(old_engine_section, new_engine_section)
    print("Replaced old_engine_section successfully!")
else:
    print("Warning: old_engine_section not found!")

# 2. Update KPI panel to include Video Engine, Fallback Status, and Latency
old_kpi_block = '''                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Image Generation Model</span>
                                    <span class="text-amber-300 font-mono text-[11px]" id="outImageEngine">FLUX.2 Klein (4B Diffusion)</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Audio Voice Engine</span>
                                    <span class="text-purple-300 font-mono text-[11px]" id="outVoiceEngine">en-US-ChristopherNeural</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Visual Motion Engine</span>
                                    <span class="text-cyan-300 font-mono text-[11px]" id="outMotionEngine">kenburns_cinematic</span>
                                </div>'''

new_kpi_block = '''                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">AI Video Model</span>
                                    <span class="text-green-300 font-mono text-[11px]" id="outVideoEngine">NVIDIA Wan 2.2 (14B NIM)</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Image Keyframe Engine</span>
                                    <span class="text-amber-300 font-mono text-[11px]" id="outImageEngine">FLUX.2 Klein (4B Diffusion)</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Audio Voice Engine</span>
                                    <span class="text-purple-300 font-mono text-[11px]" id="outVoiceEngine">en-US-ChristopherNeural</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Fallback Motion Engine</span>
                                    <span class="text-cyan-300 font-mono text-[11px]" id="outMotionEngine">kenburns_cinematic</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Execution Route</span>
                                    <span class="font-mono text-[11px]" id="outExecutionRoute">Native AI</span>
                                </div>'''

if old_kpi_block in html:
    html = html.replace(old_kpi_block, new_kpi_block)
    print("Replaced old_kpi_block successfully!")
else:
    print("Warning: old_kpi_block not found!")

# 3. Update table rendering in renderStudioResult (remove hardcoded FALSE/PASSED)
old_table_row = '''                        <td class="p-2.5 text-center text-emerald-400 font-bold">FALSE</td>
                        <td class="p-2.5 text-center text-emerald-400 font-bold">PASSED</td>'''

new_table_row = '''                        <td class="p-2.5 text-center">
                            ${trc.fallback_used 
                                ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40"><i class="fa-solid fa-triangle-exclamation mr-1"></i> TRUE (Fallback)</span>`
                                : `<span class="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 font-bold"><i class="fa-solid fa-check mr-1"></i> FALSE (Native AI)</span>`
                            }
                        </td>
                        <td class="p-2.5 text-center">
                            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold ${trc.quality_status === 'passed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}">
                                ${(trc.quality_status || 'passed').toUpperCase()}
                            </span>
                        </td>'''

if old_table_row in html:
    html = html.replace(old_table_row, new_table_row)
    print("Replaced old_table_row successfully!")
else:
    print("Warning: old_table_row not found!")

# 4. Update executeGenerateVideo and handleReferenceUpload
old_js_fetch = '''            const res = await fetch('/api/studio/generate', {
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
            });

                clearInterval(stepTimer);
                animatePipelineStep(5);

                const data = await res.json();
                if (data.status === "SUCCESS") {
                    renderStudioResult(data);
                    loadRecentProjects();
                    loadStats();
                } else {
                    alert("Generation failed: " + (data.detail || "Server error"));
                }'''

new_js_fetch = '''            const videoModel = document.getElementById('studioVideoModelSelect')?.value || 'wan-ai/wan2.2';
            const videoTask = document.getElementById('studioVideoTaskSelect')?.value || 'image_to_video';
            const genMode = document.getElementById('studioGenModeSelect')?.value || 'full_ai';
            const resolution = document.getElementById('studioResolutionSelect')?.value || '1080p';
            const qualityPreset = document.getElementById('studioQualityPresetSelect')?.value || 'high';
            const allowFallback = document.getElementById('studioAllowFallbackCheck')?.checked ?? true;

            const res = await fetch('/api/studio/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    director_model: model,
                    image_model: imgModel,
                    video_provider: 'nvidia_nim',
                    video_model: videoModel,
                    generation_mode: genMode,
                    video_task: videoTask,
                    resolution: resolution,
                    quality_preset: qualityPreset,
                    allow_fallback: allowFallback,
                    duration_s: duration,
                    style: 'Luxury Minimalist',
                    aspect_ratio: aspect,
                    audio_voice: voice,
                    motion_style: motion,
                    reference_assets: uploadedReferenceAssetId ? [uploadedReferenceAssetId] : []
                })
            });

                clearInterval(stepTimer);
                animatePipelineStep(5);

                const data = await res.json();
                if (data.status === "SUCCESS") {
                    renderStudioResult(data);
                    loadRecentProjects();
                    loadStats();
                } else if (res.status === 503 || data.status === "PROVIDER_UNAVAILABLE") {
                    alert("⚠️ NVIDIA Video Model Offline:\\n\\n" + (data.detail || "Wan2.2 14B GPU Host is offline.") + "\\n\\nTo proceed with Image Motion Fallback, check 'Allow Image Motion Fallback if GPU is offline' and retry.");
                } else {
                    alert("Generation failed: " + (data.detail || "Server error"));
                }'''

if old_js_fetch in html:
    html = html.replace(old_js_fetch, new_js_fetch)
    print("Replaced old_js_fetch successfully!")
else:
    print("Warning: old_js_fetch not found!")

# 5. Add reference asset upload functions in JS
ref_js_functions = '''
        let uploadedReferenceAssetId = null;

        async function handleReferenceUpload(input) {
            if (!input.files || !input.files[0]) return;
            const file = input.files[0];
            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/studio/upload-reference', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    uploadedReferenceAssetId = data.asset_id;
                    document.getElementById('refThumb').src = data.asset_url;
                    document.getElementById('refThumbContainer').classList.remove('hidden');
                    document.getElementById('btnUploadRef').classList.add('hidden');
                } else {
                    alert('Reference upload failed: ' + (data.detail || 'Server error'));
                }
            } catch (err) {
                alert('Upload error: ' + err.message);
            }
        }

        function removeReference() {
            uploadedReferenceAssetId = null;
            document.getElementById('studioReferenceFile').value = '';
            document.getElementById('refThumbContainer').classList.add('hidden');
            document.getElementById('btnUploadRef').classList.remove('hidden');
        }
'''

if "let uploadedReferenceAssetId = null;" not in html:
    target_js_insert = "let lastGeneratedProjectId = null;"
    html = html.replace(target_js_insert, target_js_insert + "\n" + ref_js_functions)
    print("Added reference upload JS functions!")

# 6. Update renderStudioResult KPI setters
old_render_kpi = '''            if (document.getElementById('outImageEngine')) document.getElementById('outImageEngine').innerText = data.image_model || 'FLUX.2 Klein 4B';
            if (document.getElementById('outVoiceEngine')) document.getElementById('outVoiceEngine').innerText = data.audio_voice || 'Default';
            if (document.getElementById('outMotionEngine')) document.getElementById('outMotionEngine').innerText = data.motion_style || 'kenburns_cinematic';
            document.getElementById('outQcScore').innerText = `${data.qc_report.score}/100`;
            document.getElementById('outQcVerdict').innerText = data.qc_report.verdict;'''

new_render_kpi = '''            if (document.getElementById('outVideoEngine')) document.getElementById('outVideoEngine').innerText = `${data.video_model || 'wan-ai/wan2.2'} (${data.video_task || 'I2V'})`;
            if (document.getElementById('outImageEngine')) document.getElementById('outImageEngine').innerText = data.image_model || 'FLUX.2 Klein 4B';
            if (document.getElementById('outVoiceEngine')) document.getElementById('outVoiceEngine').innerText = data.audio_voice || 'Default';
            if (document.getElementById('outMotionEngine')) document.getElementById('outMotionEngine').innerText = data.motion_style || 'kenburns_cinematic';
            if (document.getElementById('outExecutionRoute')) {
                const routeEl = document.getElementById('outExecutionRoute');
                if (data.qc_report.fallback_used) {
                    routeEl.innerHTML = `<span class="text-amber-400 font-bold"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Image Motion Fallback</span>`;
                } else {
                    routeEl.innerHTML = `<span class="text-emerald-400 font-bold"><i class="fa-solid fa-check mr-1"></i> Native AI Video Diffusion</span>`;
                }
            }
            document.getElementById('outQcScore').innerText = `${data.qc_report.score}/100`;
            document.getElementById('outQcVerdict').innerText = data.qc_report.verdict;'''

if old_render_kpi in html:
    html = html.replace(old_render_kpi, new_render_kpi)
    print("Replaced old_render_kpi successfully!")
else:
    print("Warning: old_render_kpi not found!")

with open("web_ec2/templates/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved updated index.html!")
