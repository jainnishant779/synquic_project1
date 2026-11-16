with open("web_ec2/templates/index.html", "r", encoding="utf-8") as f:
    s = f.read()

s = s.replace('\r\n', '\n')

old_code = '''            // Video player
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

new_code = '''            // Video player
            const player = document.getElementById('studioMainVideoPlayer');
            const source = document.getElementById('studioMainVideoSource');
            source.src = data.video_url + "?t=" + Date.now();
            player.load();

            // Adapt player container for 9:16 vertical Reel vs 16:9 landscape
            const playerBox = player.parentElement;
            if (data.aspect_ratio === "9:16") {
                playerBox.className = "relative rounded-xl overflow-hidden bg-black aspect-[9/16] max-w-xs mx-auto flex items-center justify-center shadow-2xl";
            } else {
                playerBox.className = "relative rounded-xl overflow-hidden bg-black aspect-video flex items-center justify-center shadow-2xl";
            }

            const overlay = document.getElementById('videoUnmuteOverlay');
            if (overlay) overlay.classList.remove('hidden');
            player.play().catch(e => {
                console.log("Autoplay caught:", e);
                if (overlay) overlay.classList.remove('hidden');
            });'''

s = s.replace(old_code, new_code)

# Add instagram button to presets in HTML
old_btn = '''                            <button onclick="loadStudioPreset('coke')" class="px-3 py-1 rounded-lg bg-red-950/60 hover:bg-red-900/80 text-xs text-red-200 border border-red-800/60 transition flex items-center gap-1.5 font-semibold">
                                🥤 Coca-Cola
                            </button>'''

new_btn = '''                            <button onclick="loadStudioPreset('instagram')" class="px-3 py-1 rounded-lg bg-pink-950/60 hover:bg-pink-900/80 text-xs text-pink-200 border border-pink-800/60 transition flex items-center gap-1.5 font-semibold">
                                📸 Instagram Reel
                            </button>
                            <button onclick="loadStudioPreset('coke')" class="px-3 py-1 rounded-lg bg-red-950/60 hover:bg-red-900/80 text-xs text-red-200 border border-red-800/60 transition flex items-center gap-1.5 font-semibold">
                                🥤 Coca-Cola
                            </button>'''

s = s.replace(old_btn, new_btn)

# Add instagram preset in JS
old_js = '''            coke: "Make commercial for Coca-Cola: ultra-macro 4K frost and condensation beads on crimson contour bottle, ice cubes splashing, sparkling carbonated fizz pour, taste the feeling.",'''

new_js = '''            instagram: "MAKE AD FOR INSTAGRAM: High-energy 9:16 vertical viral Instagram reel commercial for creator social growth studio, neon ring light, smartphone UI, fast cuts, trending audio.",
            coke: "Make commercial for Coca-Cola: ultra-macro 4K frost and condensation beads on crimson contour bottle, ice cubes splashing, sparkling carbonated fizz pour, taste the feeling.",'''

s = s.replace(old_js, new_js)

with open("web_ec2/templates/index.html", "w", encoding="utf-8") as f:
    f.write(s)

print("Updated web_ec2/templates/index.html with vertical reel player and instagram preset!")
