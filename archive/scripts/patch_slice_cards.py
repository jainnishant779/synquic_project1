with open("web_ec2/templates/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find start and end indices
start_idx = None
end_idx = None

for i, l in enumerate(lines):
    if "<!-- Pipeline Engine Selectors -->" in l:
        start_idx = i
    if "<!-- Action Button -->" in l:
        end_idx = i
        break

print(f"start_idx: {start_idx}, end_idx: {end_idx}")

new_section = '''                    <!-- PRODUCT REFERENCE VAULT (I2V ANCHOR) -->
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
                    </div>\n'''

if start_idx is not None and end_idx is not None:
    new_lines = lines[:start_idx] + [new_section] + lines[end_idx:]
    with open("web_ec2/templates/index.html", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("Successfully replaced lines with new 5-card deck + reference vault!")
else:
    print("Error: Could not locate bounds!")
