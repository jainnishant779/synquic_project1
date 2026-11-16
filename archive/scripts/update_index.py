from pathlib import Path

index_path = Path("web_ec2/templates/index.html")
content = index_path.read_text(encoding="utf-8")

# 1. Preset button
button_target = '<button onclick="loadStudioPreset(\'parkfnb\')"'
button_new = '''<button onclick="loadStudioPreset('homingo')" class="px-3 py-1 rounded-lg bg-indigo-950/70 hover:bg-indigo-900/90 text-xs text-indigo-200 border border-indigo-500/60 transition flex items-center gap-1.5 font-bold shadow-md shadow-indigo-500/20">
                                🛠️ Homingo Home Services ★
                            </button>
                            <button onclick="loadStudioPreset('parkfnb')"'''
content = content.replace(button_target, button_new, 1)

# 2. Industry option
industry_target = '<option value="" selected>Auto-Detect from Brief & Anchor</option>'
industry_new = '''<option value="" selected>Auto-Detect from Brief & Anchor</option>
                                    <option value="home_services">🛠️ Home Services, Repairs & On-Demand Apps</option>'''
content = content.replace(industry_target, industry_new, 1)

# 3. PRESETS dict
presets_target = 'const PRESETS = {'
presets_new = '''const PRESETS = {
            homingo: "make ad for homingo app -an home service provider app: Verified background-checked professionals for emergency plumbing, electrical repairs, and deep cleaning, arriving in 30 minutes with transparent pricing.",'''
content = content.replace(presets_target, presets_new, 1)

# 4. loadStudioPreset function
load_target = 'if (key === \'parkfnb\') {'
load_new = '''if (key === 'homingo') {
                    if (document.getElementById('studioBrandInput')) document.getElementById('studioBrandInput').value = 'Homingo';
                    if (document.getElementById('studioIndustrySelect')) document.getElementById('studioIndustrySelect').value = 'home_services';
                    if (document.getElementById('studioFeaturesInput')) document.getElementById('studioFeaturesInput').value = 'Verified Experts in 30 Min, Emergency Plumbing & Repairs, Transparent Pricing';
                    if (document.getElementById('studioCtaInput')) document.getElementById('studioCtaInput').value = 'Download Homingo Today';
                    if (document.getElementById('studioCameraSelect')) document.getElementById('studioCameraSelect').value = 'macro_push';
                    if (document.getElementById('studioLightingSelect')) document.getElementById('studioLightingSelect').value = 'daylight';
                    if (document.getElementById('studioBgmSelect')) document.getElementById('studioBgmSelect').value = 'energetic';
                    if (document.getElementById('studioStyleSelect')) document.getElementById('studioStyleSelect').value = 'Modern Architectural';
                } else if (key === 'parkfnb') {'''
content = content.replace(load_target, load_new, 1)

index_path.write_text(content, encoding="utf-8")
print("Updated web_ec2/templates/index.html successfully.")
