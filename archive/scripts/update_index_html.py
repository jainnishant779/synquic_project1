# Update web_ec2/templates/index.html with presets, unmute overlay, and audio player handling
with open("web_ec2/templates/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update presets buttons in HTML
old_preset_buttons = '''                        <div class="flex flex-wrap gap-2">
                            <button onclick="loadStudioPreset('auraglow')" class="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition flex items-center gap-1.5">
                                🌿 AuraGlow Botanical Serum
                            </button>
                            <button onclick="loadStudioPreset('terrastride')" class="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition flex items-center gap-1.5">
                                👟 TerraStride Eco-Runner
                            </button>
                            <button onclick="loadStudioPreset('northwind')" class="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition flex items-center gap-1.5">
                                ☕ Northwind Pour-Over Kettle
                            </button>
                            <button onclick="loadStudioPreset('cyberpunk')" class="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition flex items-center gap-1.5">
                                ⚡ Apex Cyberpunk Energy Drink
                            </button>
                        </div>'''

new_preset_buttons = '''                        <div class="flex flex-wrap gap-2">
                            <button onclick="loadStudioPreset('coke')" class="px-3 py-1 rounded-lg bg-red-950/60 hover:bg-red-900/80 text-xs text-red-200 border border-red-800/60 transition flex items-center gap-1.5 font-semibold">
                                🥤 Coca-Cola
                            </button>
                            <button onclick="loadStudioPreset('burger')" class="px-3 py-1 rounded-lg bg-amber-950/60 hover:bg-amber-900/80 text-xs text-amber-200 border border-amber-800/60 transition flex items-center gap-1.5 font-semibold">
                                🍔 Gourmet Burger
                            </button>
                            <button onclick="loadStudioPreset('car')" class="px-3 py-1 rounded-lg bg-blue-950/60 hover:bg-blue-900/80 text-xs text-blue-200 border border-blue-800/60 transition flex items-center gap-1.5 font-semibold">
                                🏎️ Sports Car
                            </button>
                            <button onclick="loadStudioPreset('watch')" class="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition flex items-center gap-1.5 font-semibold">
                                ⌚ Luxury Watch
                            </button>
                            <button onclick="loadStudioPreset('coffee')" class="px-3 py-1 rounded-lg bg-amber-900/40 hover:bg-amber-800/60 text-xs text-amber-200 border border-amber-700/60 transition flex items-center gap-1.5 font-semibold">
                                ☕ Artisan Coffee
                            </button>
                            <button onclick="loadStudioPreset('perfume')" class="px-3 py-1 rounded-lg bg-purple-950/60 hover:bg-purple-900/80 text-xs text-purple-200 border border-purple-800/60 transition flex items-center gap-1.5 font-semibold">
                                ✨ Haute Perfume
                            </button>
                            <button onclick="loadStudioPreset('headphones')" class="px-3 py-1 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/80 text-xs text-cyan-200 border border-cyan-800/60 transition flex items-center gap-1.5 font-semibold">
                                🎧 ANC Headphones
                            </button>
                            <button onclick="loadStudioPreset('terrastride')" class="px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition flex items-center gap-1.5 font-semibold">
                                👟 Sneaker
                            </button>
                            <button onclick="loadStudioPreset('auraglow')" class="px-3 py-1 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 text-xs text-emerald-200 border border-emerald-800/60 transition flex items-center gap-1.5 font-semibold">
                                🌿 Skincare Serum
                            </button>
                        </div>'''

if old_preset_buttons in html:
    html = html.replace(old_preset_buttons, new_preset_buttons)
    print("Replaced preset buttons in HTML")
else:
    print("Warning: old_preset_buttons not found")

# 2. Update Video Player Container with Play/Unmute Overlay
old_player = '''                            <div class="relative rounded-xl overflow-hidden bg-black aspect-video flex items-center justify-center">
                                <video id="studioMainVideoPlayer" controls autoplay playsinline loop class="w-full h-full object-contain">
                                    <source id="studioMainVideoSource" src="" type="video/mp4">
                                    Your browser does not support HTML5 video streaming.
                                </video>
                            </div>'''

new_player = '''                            <div class="relative rounded-xl overflow-hidden bg-black aspect-video flex items-center justify-center">
                                <video id="studioMainVideoPlayer" controls playsinline loop class="w-full h-full object-contain">
                                    <source id="studioMainVideoSource" src="" type="video/mp4">
                                    Your browser does not support HTML5 video streaming.
                                </video>
                                <!-- Interactive Play / Unmute Audio Overlay -->
                                <div id="videoUnmuteOverlay" onclick="unmuteAndPlay()" class="absolute inset-0 bg-slate-950/70 backdrop-blur-[2px] flex flex-col items-center justify-center cursor-pointer group hover:bg-slate-950/50 transition z-20">
                                    <div class="w-16 h-16 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-2xl shadow-2xl group-hover:scale-110 transition shadow-emerald-500/50">
                                        <i class="fa-solid fa-play ml-1"></i>
                                    </div>
                                    <span class="mt-4 px-4 py-1.5 rounded-full bg-slate-900/90 text-emerald-300 text-xs font-bold border border-emerald-500/40 shadow-lg flex items-center gap-2">
                                        <i class="fa-solid fa-volume-high text-emerald-400"></i> Click to Play Commercial with Studio Audio & Music
                                    </span>
                                </div>
                            </div>'''

if old_player in html:
    html = html.replace(old_player, new_player)
    print("Replaced player container in HTML")
else:
    print("Warning: old_player not found")

# 3. Update Tech specs text
old_tech = '768x448 @ 24fps | H.264 Baseline | AAC 48kHz'
new_tech = '768x448 @ 24fps | H.264 Faststart | Stereo 48kHz AAC (Voice + BGM Mixed) | Kinetic Typography'
if old_tech in html:
    html = html.replace(old_tech, new_tech)
    print("Replaced tech specs text")

# 4. Update PRESETS JS object and add unmuteAndPlay function
old_js_presets = '''        // Commercial Brief Presets
        const PRESETS = {
            auraglow: "Luxury commercial for AuraGlow Botanical Face Serum: amber glass bottle on Italian marble, golden morning window rays, rich golden hour bokeh, macro droplet reveal, 100% organic botanical hydration aesthetic.",
            terrastride: "High-energy urban commercial for TerraStride Eco-Runner sneaker: sneaker lands firmly on rain-slick city pavement, water droplets spray outward in slow motion 120fps, neon blue and amber street reflections, dynamic tracking shot.",
            northwind: "Artisanal morning commercial for Northwind Pour-Over Kettle: matte forest green kettle with carved walnut handle, steam rising from gooseneck spout into sunlit kitchen, smooth water stream pouring into ceramic dripper, quiet luxury.",
            cyberpunk: "Hyper-kinetic commercial for Apex Cyberpunk Energy Drink: ice-cold frosted can opening with explosive carbonation mist, neon laser reflections, rapid whip pan cameras, futuristic Tokyo night city aesthetic."
        };'''

new_js_presets = '''        // Commercial Brief Presets
        const PRESETS = {
            coke: "Make commercial for Coca-Cola: ultra-macro 4K frost and condensation beads on crimson contour bottle, ice cubes splashing, sparkling carbonated fizz pour, taste the feeling.",
            burger: "Mouthwatering gourmet burger commercial: flame-seared Angus beef patty sizzling on blazing iron grill, melted aged cheddar dripping, golden toasted brioche bun, appetizing macro.",
            car: "Kinetic night commercial for Apex AeroGT sports car: twin-turbo engine roar, gleaming LED headlights carving through midnight highway, neon light trails, speed and aerodynamic luxury.",
            watch: "High-end luxury commercial for Aethelgard mechanical chronograph: brushed titanium bezel, sapphire crystal reflections, microscopic ticking gears, dark moody executive aesthetic.",
            coffee: "Artisanal single-origin pour-over coffee commercial: aromatic steam rising from fresh crema espresso, dark roast beans, morning sunlight in wooden cafe, quiet craft.",
            perfume: "Haute perfumerie commercial for Maison Élixir: sculpted crystal flacon on silk satin, golden hour amber light, fine atomized mist cloud, luxurious sensual presence.",
            headphones: "Futuristic audio commercial for SonicWave Pro ANC headphones: matte obsidian earcups, cyan neon rim lighting, titanium acoustic driver bass vibration, immersive silence.",
            auraglow: "Luxury commercial for AuraGlow Botanical Face Serum: amber glass bottle on Italian marble, golden morning window rays, rich golden hour bokeh, macro droplet reveal, 100% organic botanical hydration aesthetic.",
            terrastride: "High-energy urban commercial for TerraStride Eco-Runner sneaker: sneaker lands firmly on rain-slick city pavement, water droplets spray outward in slow motion 120fps, neon blue and amber street reflections, dynamic tracking shot.",
            northwind: "Artisanal morning commercial for Northwind Pour-Over Kettle: matte forest green kettle with carved walnut handle, steam rising from gooseneck spout into sunlit kitchen, smooth water stream pouring into ceramic dripper, quiet luxury."
        };

        function unmuteAndPlay() {
            const player = document.getElementById('studioMainVideoPlayer');
            player.muted = false;
            player.volume = 1.0;
            player.play();
            const overlay = document.getElementById('videoUnmuteOverlay');
            if (overlay) overlay.classList.add('hidden');
        }'''

if old_js_presets in html:
    html = html.replace(old_js_presets, new_js_presets)
    print("Replaced JS presets and added unmuteAndPlay")
else:
    print("Warning: old_js_presets not found")

# 5. Show overlay on video load
old_load = '''            // Video player
            const player = document.getElementById('studioMainVideoPlayer');
            const source = document.getElementById('studioMainVideoSource');
            source.src = data.video_url + "?t=" + Date.now();
            player.load();
            player.play().catch(e => console.log("Autoplay caught:", e));'''

new_load = '''            // Video player
            const player = document.getElementById('studioMainVideoPlayer');
            const source = document.getElementById('studioMainVideoSource');
            source.src = data.video_url + "?t=" + Date.now();
            player.load();
            const overlay = document.getElementById('videoUnmuteOverlay');
            if (overlay) overlay.classList.remove('hidden');
            player.play().catch(e => {
                console.log("Autoplay caught:", e);
                if (overlay) overlay.classList.remove('hidden');
            });'''

if old_load in html:
    html = html.replace(old_load, new_load)
    print("Replaced player load logic")
else:
    print("Warning: old_load not found")

with open("web_ec2/templates/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved updated web_ec2/templates/index.html!")
