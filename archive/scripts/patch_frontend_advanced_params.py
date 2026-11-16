with open("web_ec2/templates/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add ParkFnB preset button to Quick Presets
old_presets_btn = """                        <div class="flex flex-wrap gap-2">
                                                        <button onclick="loadStudioPreset('realestate')" class="px-3 py-1 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 text-xs text-emerald-200 border border-emerald-800/60 transition flex items-center gap-1.5 font-semibold">
                                🏢 Property Broker App
                            </button>"""

new_presets_btn = """                        <div class="flex flex-wrap gap-2">
                            <button onclick="loadStudioPreset('parkfnb')" class="px-3 py-1 rounded-lg bg-cyan-950/70 hover:bg-cyan-900/90 text-xs text-cyan-200 border border-cyan-500/60 transition flex items-center gap-1.5 font-bold shadow-md shadow-cyan-500/20">
                                🅿️ ParkFnB Barrier ★
                            </button>
                            <button onclick="loadStudioPreset('realestate')" class="px-3 py-1 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 text-xs text-emerald-200 border border-emerald-800/60 transition flex items-center gap-1.5 font-semibold">
                                🏢 Property Broker App
                            </button>"""

# 2. Add Product Identity & Strategy section right after Product Reference Vault
old_ref_vault_end = """                            <button type="button" id="btnUploadRef" onclick="document.getElementById('studioReferenceFile').click()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/40 text-xs font-semibold flex items-center gap-1.5 transition">
                                <i class="fa-solid fa-cloud-arrow-up"></i> Upload Reference
                            </button>
                        </div>
                    </div>

                    <!-- Pipeline Engine Selectors -->"""

new_ref_vault_end = """                            <button type="button" id="btnUploadRef" onclick="document.getElementById('studioReferenceFile').click()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/40 text-xs font-semibold flex items-center gap-1.5 transition">
                                <i class="fa-solid fa-cloud-arrow-up"></i> Upload Reference
                            </button>
                        </div>
                    </div>

                    <!-- 2. PRODUCT IDENTITY & ADVANCED COMMERCIAL STRATEGY -->
                    <div class="p-3.5 rounded-xl border border-amber-500/30 bg-amber-950/15 space-y-3">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                                <i class="fa-solid fa-sliders"></i> Product Strategy & Commercial Controls
                            </span>
                            <span class="text-[9px] text-amber-300/80 font-mono font-semibold px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">Pro Commercial Parameters</span>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Brand / Product Name</label>
                                <input type="text" id="studioBrandInput" placeholder="e.g. ParkFnB Barrier" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500">
                            </div>
                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Industry / Category</label>
                                <select id="studioIndustrySelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-amber-500">
                                    <option value="" selected>Auto-Detect from Brief & Anchor</option>
                                    <option value="parking_barrier">🅿️ Smart Hardware & IoT / Parking Systems</option>
                                    <option value="realestate">🏢 Real Estate & Architecture</option>
                                    <option value="instagram">📱 Tech, SaaS & Mobile Apps</option>
                                    <option value="car">🏎️ Automotive & Transport</option>
                                    <option value="watch">⌚ Luxury Watches & Jewelry</option>
                                    <option value="headphones">🎧 Consumer Electronics & Audio</option>
                                    <option value="serum">🌿 Skincare, Cosmetics & Health</option>
                                    <option value="perfume">✨ Haute Perfumes & Fragrances</option>
                                    <option value="burger">🍔 Gourmet Food & Hospitality</option>
                                    <option value="coffee">☕ Artisanal Coffee & Beverages</option>
                                    <option value="sneaker">👟 Fashion, Footwear & Apparel</option>
                                </select>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Core Features / USP</label>
                                <input type="text" id="studioFeaturesInput" placeholder="e.g. 0.6s Rapid Lift, RFID, Radar Sensor" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500">
                            </div>
                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Target Audience</label>
                                <select id="studioAudienceSelect" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-amber-500">
                                    <option value="Commercial & Facility Managers" selected>B2B Commercial & Facility Managers</option>
                                    <option value="Modern Urban Consumers">Modern Urban Consumers</option>
                                    <option value="Luxury & High Net-Worth">Luxury & High Net-Worth Affluent</option>
                                    <option value="Youth & Trendsetters">Youth, Trendsetters & Creators</option>
                                    <option value="Mass Consumer Market">Mass Consumer Market</option>
                                </select>
                            </div>
                            <div>
                                <label class="text-[10px] font-bold text-slate-300 block mb-1">Call To Action (CTA)</label>
                                <input type="text" id="studioCtaInput" placeholder="e.g. Install ParkFnB Barrier Today" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500">
                            </div>
                        </div>
                    </div>

                    <!-- Pipeline Engine Selectors -->"""

# 3. Replace Secondary Parameters row with Full Cinematography & Audio Suite
old_secondary_params = """                        <!-- Secondary Parameters: Duration, Style, Resolution, Quality Preset, Aspect Ratio -->
                        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 pt-2 border-t border-slate-800/80">
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
                                    <option value="Modern Architectural">Modern Architectural (Real Estate & Tech)</option>
                                    <option value="High-Energy Dynamic">High-Energy Dynamic (Fast Cuts)</option>
                                    <option value="Cinematic 35mm">Cinematic 35mm (Moody Film Grain)</option>
                                    <option value="Artisanal Warm">Artisanal Warm (Organic & Sunlit)</option>
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
                        </div>"""

new_secondary_params = """                        <!-- Advanced Cinematography & Audio Suite Parameters -->
                        <div class="pt-2.5 border-t border-slate-800/80 space-y-2">
                            <span class="text-[10px] font-bold uppercase tracking-wider text-teal-400 flex items-center gap-1.5">
                                <i class="fa-solid fa-camera-movie"></i> Cinematography, Lighting & Sound Controls
                            </span>
                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                                <div>
                                    <label class="text-[10px] font-bold text-slate-300 block mb-1">Camera Dynamics</label>
                                    <select id="studioCameraSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-teal-500">
                                        <option value="macro_push" selected>Cinematic Macro Push-In</option>
                                        <option value="drone_sweep">Dynamic Drone Aerial Sweep</option>
                                        <option value="orbit_360">360° Product Orbit</option>
                                        <option value="tracking_fast">High-Speed Kinetic Tracking</option>
                                        <option value="hero_tilt">Low-Angle Hero Tilt</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="text-[10px] font-bold text-slate-300 block mb-1">Lighting & Mood</label>
                                    <select id="studioLightingSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-teal-500">
                                        <option value="studio_clean" selected>Commercial Studio Clean</option>
                                        <option value="golden_hour">Golden Hour Sunlit Warmth</option>
                                        <option value="neon_cyber">Cyberpunk Neon & Night Glow</option>
                                        <option value="moody_contrast">Dramatic Moody Film Noir</option>
                                        <option value="daylight">Architectural Crisp Daylight</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="text-[10px] font-bold text-slate-300 block mb-1">Background Music (BGM)</label>
                                    <select id="studioBgmSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-teal-500">
                                        <option value="tech_ambient" selected>Modern Tech Ambient Beat</option>
                                        <option value="energetic">High-Energy Electronic</option>
                                        <option value="luxury">Luxury Lo-Fi & Smooth Piano</option>
                                        <option value="none">Pure Voiceover (No BGM)</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="text-[10px] font-bold text-slate-300 block mb-1">Commercial Style</label>
                                    <select id="studioStyleSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-teal-500">
                                        <option value="Luxury Minimalist" selected>Luxury Minimalist (Soft Light & Bokeh)</option>
                                        <option value="Modern Architectural">Modern Architectural (Real Estate & Tech)</option>
                                        <option value="High-Energy Dynamic">High-Energy Dynamic (Fast Cuts)</option>
                                        <option value="Cinematic 35mm">Cinematic 35mm (Moody Film Grain)</option>
                                        <option value="Artisanal Warm">Artisanal Warm (Organic & Sunlit)</option>
                                    </select>
                                </div>
                            </div>
                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
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
                        </div>"""

# 4. Update PRESETS
old_presets_marker = "const PRESETS = {\n"
new_presets_marker = """const PRESETS = {
            parkfnb: "MAKE AD FOR PARKFNB BARRIER: High-tech commercial for ParkFnB Intelligent Automated Boom Barrier, sleek illuminated LED barrier arm at modern corporate headquarters, 0.6 second high-speed RFID vehicle clearance, anti-crash radar protection, seamless multi-lane access.",\n"""

# 5. Update loadStudioPreset
old_load_preset = """        function loadStudioPreset(key) {
            if (PRESETS[key]) {
                document.getElementById('studioPromptInput').value = PRESETS[key];
            }
        }"""

new_load_preset = """        function loadStudioPreset(key) {
            if (PRESETS[key]) {
                document.getElementById('studioPromptInput').value = PRESETS[key];
                if (key === 'parkfnb') {
                    if (document.getElementById('studioBrandInput')) document.getElementById('studioBrandInput').value = 'ParkFnB Barrier';
                    if (document.getElementById('studioIndustrySelect')) document.getElementById('studioIndustrySelect').value = 'parking_barrier';
                    if (document.getElementById('studioFeaturesInput')) document.getElementById('studioFeaturesInput').value = '0.6s Rapid Lift, RFID Access, Anti-Crash Radar Sensor';
                    if (document.getElementById('studioCtaInput')) document.getElementById('studioCtaInput').value = 'Install ParkFnB Barrier Today';
                    if (document.getElementById('studioCameraSelect')) document.getElementById('studioCameraSelect').value = 'macro_push';
                    if (document.getElementById('studioLightingSelect')) document.getElementById('studioLightingSelect').value = 'daylight';
                    if (document.getElementById('studioBgmSelect')) document.getElementById('studioBgmSelect').value = 'tech_ambient';
                    if (document.getElementById('studioStyleSelect')) document.getElementById('studioStyleSelect').value = 'Modern Architectural';
                } else if (key === 'realestate') {
                    if (document.getElementById('studioBrandInput')) document.getElementById('studioBrandInput').value = 'PrimeEstate';
                    if (document.getElementById('studioIndustrySelect')) document.getElementById('studioIndustrySelect').value = 'realestate';
                    if (document.getElementById('studioFeaturesInput')) document.getElementById('studioFeaturesInput').value = 'Verified Listings, Direct Broker Handover, Virtual Tours';
                    if (document.getElementById('studioCtaInput')) document.getElementById('studioCtaInput').value = 'Download PrimeEstate Today';
                }
            }
        }"""

# 6. Update executeGenerateVideo to pass all parameters
old_exec_fetch = """            const res = await fetch('/api/studio/generate', {
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
                    style: style,
                    aspect_ratio: aspect,
                    audio_voice: voice,
                    motion_style: motion,
                    reference_assets: uploadedReferenceAssetId ? [uploadedReferenceAssetId] : []
                })
            });"""

new_exec_fetch = """            const brandName = document.getElementById('studioBrandInput')?.value?.trim() || '';
            const industry = document.getElementById('studioIndustrySelect')?.value || '';
            const features = document.getElementById('studioFeaturesInput')?.value?.trim() || '';
            const audience = document.getElementById('studioAudienceSelect')?.value || '';
            const ctaText = document.getElementById('studioCtaInput')?.value?.trim() || '';
            const cameraDynamics = document.getElementById('studioCameraSelect')?.value || 'macro_push';
            const lightingMood = document.getElementById('studioLightingSelect')?.value || 'studio_clean';
            const bgmGenre = document.getElementById('studioBgmSelect')?.value || 'tech_ambient';

            const res = await fetch('/api/studio/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    brand_name: brandName,
                    industry: industry,
                    features: features,
                    target_audience: audience,
                    cta_text: ctaText,
                    camera_dynamics: cameraDynamics,
                    lighting_mood: lightingMood,
                    bgm_genre: bgmGenre,
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
                    style: style,
                    aspect_ratio: aspect,
                    audio_voice: voice,
                    motion_style: motion,
                    reference_assets: uploadedReferenceAssetId ? [uploadedReferenceAssetId] : []
                })
            });"""

# Normalize CRLF
html_norm = html.replace("\r\n", "\n")

assert old_presets_btn.replace("\r\n", "\n") in html_norm, "old_presets_btn not found!"
html_norm = html_norm.replace(old_presets_btn.replace("\r\n", "\n"), new_presets_btn.replace("\r\n", "\n"), 1)

assert old_ref_vault_end.replace("\r\n", "\n") in html_norm, "old_ref_vault_end not found!"
html_norm = html_norm.replace(old_ref_vault_end.replace("\r\n", "\n"), new_ref_vault_end.replace("\r\n", "\n"), 1)

assert old_secondary_params.replace("\r\n", "\n") in html_norm, "old_secondary_params not found!"
html_norm = html_norm.replace(old_secondary_params.replace("\r\n", "\n"), new_secondary_params.replace("\r\n", "\n"), 1)

assert old_presets_marker in html_norm, "old_presets_marker not found!"
html_norm = html_norm.replace(old_presets_marker, new_presets_marker, 1)

assert old_load_preset.replace("\r\n", "\n") in html_norm, "old_load_preset not found!"
html_norm = html_norm.replace(old_load_preset.replace("\r\n", "\n"), new_load_preset.replace("\r\n", "\n"), 1)

assert old_exec_fetch.replace("\r\n", "\n") in html_norm, "old_exec_fetch not found!"
html_norm = html_norm.replace(old_exec_fetch.replace("\r\n", "\n"), new_exec_fetch.replace("\r\n", "\n"), 1)

with open("web_ec2/templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_norm)

print("Successfully updated web_ec2/templates/index.html with full Pro parameters suite!")
