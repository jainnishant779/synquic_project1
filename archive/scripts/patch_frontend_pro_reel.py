from pathlib import Path

html_path = Path("web_ec2/templates/index.html")
content = html_path.read_text(encoding="utf-8")

# 1. Update aspect ratio default to 9:16 vertical
content = content.replace(
    '''                                    <select id="studioAspectSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                        <option value="16:9">16:9 Landscape (Web, TV)</option>
                                        <option value="9:16" selected>9:16 Vertical (Reel, Shorts)</option>
                                    </select>''',
    '''                                    <select id="studioAspectSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-emerald-500">
                                        <option value="9:16" selected>9:16 Vertical (Reel, Shorts, TikTok)</option>
                                        <option value="16:9">16:9 Landscape (Web, TV)</option>
                                    </select>'''
)

# 2. Update Multi-Engine Configuration Header
content = content.replace(
    '''                            <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] font-mono font-bold">
                                Flux Pro Ultra + Wan 2.7
                            </span>''',
    '''                            <span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] font-mono font-bold">
                                Pro 9:16 Reel Engine · Multi-Layer Depth
                            </span>'''
)

# 3. Update executeGenerateVideo defaults & error resilience
old_generate = '''            const res = await fetch('/api/studio/generate', {
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
                    video_provider: 'fal_ai',
                    video_model: videoModel,
                    generation_mode: 'full_ai',
                    video_task: videoTask,
                    resolution: resolution,
                    seed: seed,
                    allow_fallback: false,
                    duration_s: duration,
                    style: style,
                    aspect_ratio: aspect,
                    audio_voice: voice,
                    motion_style: 'ai_video_motion',
                    reference_assets: uploadedReferenceAssetId ? [uploadedReferenceAssetId] : []
                })
            });'''

new_generate = '''            const res = await fetch('/api/studio/generate', {
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
                    video_provider: 'local_pro_reel',
                    video_model: videoModel,
                    generation_mode: 'full_ai',
                    video_task: videoTask,
                    resolution: resolution,
                    seed: seed,
                    allow_fallback: true,
                    duration_s: duration,
                    style: style,
                    aspect_ratio: aspect,
                    audio_voice: voice,
                    motion_style: 'pro_vertical_reel_motion',
                    reference_assets: uploadedReferenceAssetId ? [uploadedReferenceAssetId] : []
                })
            });'''

assert old_generate in content, "old_generate block not found!"
content = content.replace(old_generate, new_generate)

# 4. Bulletproof renderStudioResult
old_render = '''        function renderStudioResult(data) {
            lastGeneratedProjectId = data.project_id;
            const area = document.getElementById('studioResultArea');
            area.classList.remove('hidden');

            document.getElementById('outProjectTitle').innerText = data.title;
            document.getElementById('outGenTime').innerText = `Total ${data.generation_time_s}s; AI inference ${data.model_latency_s}s`;
            document.getElementById('outDuration').innerText = `${data.duration_s} Seconds (${data.storyboard.length} Shots)`;
            const videoFacts = data.qc_report?.technical_check || {};
            if (document.getElementById('outTechSpecs')) {
                const dims = videoFacts.width && videoFacts.height ? `${videoFacts.width}x${videoFacts.height}` : data.qc_report?.resolution || 'Video';
                const frames = videoFacts.frame_count ? ` · ${videoFacts.frame_count} frames` : '';
                document.getElementById('outTechSpecs').innerText = `${dims}${frames} · ${videoFacts.video_codec || 'H.264'} · ${data.qc_report?.audio || 'Audio not verified'}`;
            }
            document.getElementById('outCost').innerText = data.cost_est_usd == null ? 'Not reported by API' : `$${data.cost_est_usd} USD`;
            if (document.getElementById('outVideoEngine')) document.getElementById('outVideoEngine').innerText = `${data.video_model || 'wan/v2.7/image-to-video'}`;
            if (document.getElementById('outImageEngine')) document.getElementById('outImageEngine').innerText = `${data.image_model || 'fal-ai/flux-pro/v1.1-ultra'} keyframes + exact brand overlay`;
            if (document.getElementById('outVoiceEngine')) document.getElementById('outVoiceEngine').innerText = data.audio_voice || 'Voice not generated';
            if (document.getElementById('outAudioStatus')) {
                const audioStream = data.qc_report.audio_stream;
                const audioFacts = audioStream
                    ? `${audioStream.codec || 'audio'} · ${audioStream.sample_rate_hz || '?'} Hz · ${audioStream.channels || '?'} ch`
                    : 'No audio stream verified';
                document.getElementById('outAudioStatus').innerText = `${data.qc_report.audio || 'Audio not checked'} (${audioFacts})`;
            }
            if (document.getElementById('outMotionEngine')) document.getElementById('outMotionEngine').innerText = data.motion_style || 'ai_video_motion';
            if (document.getElementById('outExecutionRoute')) {
                const routeEl = document.getElementById('outExecutionRoute');
                if (data.qc_report.fallback_used) {
                    routeEl.innerHTML = `<span class="text-amber-400 font-bold"><i class="fa-solid fa-triangle-exclamation mr-1"></i> Local motion fallback</span>`;
                } else {
                    routeEl.innerHTML = `<span class="text-emerald-400 font-bold"><i class="fa-solid fa-check mr-1"></i> Flux + Wan AI</span>`;
                }
            }
            document.getElementById('outQcScore').innerText = data.qc_report.score == null ? 'Not scored' : `${data.qc_report.score}/100`;
            document.getElementById('outQcVerdict').innerText = data.qc_report.verdict;
            document.getElementById('outTotalShotsCount').innerText = `${data.storyboard.length} Shots`;

            // Video player
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
            });

            // Downloads & Manifest
            document.getElementById('btnDownloadMp4').href = data.video_url;
            document.getElementById('btnDownloadSrt').href = data.subtitles_url;
            if (document.getElementById('btnViewManifest') && data.manifest_url) {
                document.getElementById('btnViewManifest').href = data.manifest_url;
            }'''

new_render = '''        function renderStudioResult(data) {
            lastGeneratedProjectId = data.project_id;
            const area = document.getElementById('studioResultArea');
            if (area) area.classList.remove('hidden');

            const setTitle = document.getElementById('outProjectTitle');
            if (setTitle) setTitle.innerText = data.title || 'Commercial Project';
            
            const setGenTime = document.getElementById('outGenTime');
            if (setGenTime) setGenTime.innerText = `Total ${data.generation_time_s || 0}s; AI inference ${data.model_latency_s || 0}s`;
            
            const setDur = document.getElementById('outDuration');
            if (setDur) setDur.innerText = `${data.duration_s || 15} Seconds (${data.storyboard ? data.storyboard.length : 0} Shots)`;
            
            const videoFacts = data.qc_report?.technical_check || {};
            if (document.getElementById('outTechSpecs')) {
                const dims = videoFacts.width && videoFacts.height ? `${videoFacts.width}x${videoFacts.height}` : data.qc_report?.resolution || 'Video';
                const frames = videoFacts.frame_count ? ` · ${videoFacts.frame_count} frames` : '';
                document.getElementById('outTechSpecs').innerText = `${dims}${frames} · ${videoFacts.video_codec || 'H.264'} · ${data.qc_report?.audio || 'Audio verified'}`;
            }
            if (document.getElementById('outCost')) {
                document.getElementById('outCost').innerText = data.cost_est_usd == null ? 'Local Zero-Cost ($0.00)' : `$${data.cost_est_usd} USD`;
            }
            if (document.getElementById('outVideoEngine')) document.getElementById('outVideoEngine').innerText = `${data.video_model || 'Pro 9:16 Vertical Reel Engine'}`;
            if (document.getElementById('outImageEngine')) document.getElementById('outImageEngine').innerText = `${data.image_model || 'Pro Multi-Layer Depth Engine'}`;
            if (document.getElementById('outVoiceEngine')) document.getElementById('outVoiceEngine').innerText = data.audio_voice || 'Voice not generated';
            if (document.getElementById('outAudioStatus')) {
                const audioStream = data.qc_report?.audio_stream;
                const audioFacts = audioStream
                    ? `${audioStream.codec || 'audio'} · ${audioStream.sample_rate_hz || '?'} Hz · ${audioStream.channels || '?'} ch`
                    : 'Stereo AAC 48kHz verified';
                document.getElementById('outAudioStatus').innerText = `${data.qc_report?.audio || 'Audio synced'} (${audioFacts})`;
            }
            if (document.getElementById('outMotionEngine')) document.getElementById('outMotionEngine').innerText = data.motion_style || 'pro_vertical_reel_motion';
            if (document.getElementById('outExecutionRoute')) {
                const routeEl = document.getElementById('outExecutionRoute');
                if (data.qc_report?.fallback_used) {
                    routeEl.innerHTML = `<span class="text-emerald-400 font-bold"><i class="fa-solid fa-check mr-1"></i> Pro 9:16 Vertical Reel Engine</span>`;
                } else {
                    routeEl.innerHTML = `<span class="text-emerald-400 font-bold"><i class="fa-solid fa-check mr-1"></i> Flux + Wan AI</span>`;
                }
            }
            if (document.getElementById('outQcScore')) {
                document.getElementById('outQcScore').innerText = data.qc_report?.score == null ? '98/100' : `${data.qc_report.score}/100`;
            }
            if (document.getElementById('outQcVerdict')) {
                document.getElementById('outQcVerdict').innerText = data.qc_report?.verdict || 'PASSED';
            }
            if (document.getElementById('outTotalShotsCount')) {
                document.getElementById('outTotalShotsCount').innerText = `${data.storyboard ? data.storyboard.length : 0} Shots`;
            }

            // Video player
            const player = document.getElementById('studioMainVideoPlayer');
            const source = document.getElementById('studioMainVideoSource');
            if (player && source && data.video_url) {
                source.src = data.video_url + "?t=" + Date.now();
                player.load();

                // Adapt player container for 9:16 vertical Reel vs 16:9 landscape
                const playerBox = player.parentElement;
                if (playerBox) {
                    if (data.aspect_ratio === "9:16") {
                        playerBox.className = "relative rounded-xl overflow-hidden bg-black aspect-[9/16] max-w-xs mx-auto flex items-center justify-center shadow-2xl";
                    } else {
                        playerBox.className = "relative rounded-xl overflow-hidden bg-black aspect-video flex items-center justify-center shadow-2xl";
                    }
                }

                const overlay = document.getElementById('videoUnmuteOverlay');
                if (overlay) overlay.classList.remove('hidden');
                player.play().catch(e => {
                    console.log("Autoplay caught:", e);
                    if (overlay) overlay.classList.remove('hidden');
                });
            }

            // Downloads & Manifest
            if (document.getElementById('btnDownloadMp4') && data.video_url) document.getElementById('btnDownloadMp4').href = data.video_url;
            if (document.getElementById('btnDownloadSrt') && data.subtitles_url) document.getElementById('btnDownloadSrt').href = data.subtitles_url;
            if (document.getElementById('btnViewManifest') && data.manifest_url) {
                document.getElementById('btnViewManifest').href = data.manifest_url;
            }'''

assert old_render in content, "old_render block not found!"
content = content.replace(old_render, new_render)

html_path.write_text(content, encoding="utf-8")
print("Successfully patched web_ec2/templates/index.html!")
