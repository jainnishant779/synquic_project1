with open('web_ec2/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the secondary parameters HTML
old_secondary = """                        <!-- Secondary Parameters: Duration, Resolution, Quality Preset, Aspect Ratio -->
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
                        </div>"""

new_secondary = """                        <!-- Secondary Parameters: Duration, Style, Resolution, Quality Preset, Aspect Ratio -->
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

# Normalize CRLF for matching
normalized_content = content.replace('\r\n', '\n')
normalized_old = old_secondary.replace('\r\n', '\n')
normalized_new = new_secondary.replace('\r\n', '\n')

assert normalized_old in normalized_content, "old_secondary not found!"
normalized_content = normalized_content.replace(normalized_old, normalized_new, 1)

# 2. Update executeGenerateVideo to use safe optional chaining and the actual style
old_js = """        async function executeGenerateVideo() {
            const prompt = document.getElementById('studioPromptInput').value.trim();
            if (!prompt) {
                alert("Please enter a creative brief or select a preset.");
                return;
            }

            const model = document.getElementById('studioModelSelect').value;
            const duration = parseInt(document.getElementById('studioDurationSelect').value, 10);
            const style = document.getElementById('studioStyleSelect').value;
            const aspect = document.getElementById('studioAspectSelect').value;
            const btn = document.getElementById('btnGenerateVideo');"""

new_js = """        async function executeGenerateVideo() {
            const prompt = document.getElementById('studioPromptInput')?.value?.trim() || '';
            if (!prompt) {
                alert("Please enter a creative brief or select a preset.");
                return;
            }

            const model = document.getElementById('studioModelSelect')?.value || 'nvidia/nemotron-3.5-lightning-30b-a3b';
            const duration = parseInt(document.getElementById('studioDurationSelect')?.value || '15', 10);
            const style = document.getElementById('studioStyleSelect')?.value || 'Luxury Minimalist';
            const aspect = document.getElementById('studioAspectSelect')?.value || '16:9';
            const btn = document.getElementById('btnGenerateVideo');"""

normalized_old_js = old_js.replace('\r\n', '\n')
normalized_new_js = new_js.replace('\r\n', '\n')

assert normalized_old_js in normalized_content, "old_js not found!"
normalized_content = normalized_content.replace(normalized_old_js, normalized_new_js, 1)

# Also fix the payload style: 'Luxury Minimalist' -> style: style
old_payload_style = "style: 'Luxury Minimalist',"
new_payload_style = "style: style,"
assert old_payload_style in normalized_content, "old_payload_style not found!"
normalized_content = normalized_content.replace(old_payload_style, new_payload_style, 1)

with open('web_ec2/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(normalized_content)

print("Successfully patched index.html with studioStyleSelect and robust JS guards!")
