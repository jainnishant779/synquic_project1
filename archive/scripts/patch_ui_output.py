from pathlib import Path

index_path = Path("d:/research_synquic/web_ec2/templates/index.html")
html = index_path.read_text(encoding="utf-8")

# 1. Add output items in Production QC & Rating Panel
old_qc_box = """                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Faststart Web Optimized</span>
                                    <span class="text-emerald-400 font-mono">Yes (moov atom indexed)</span>
                                </div>"""

new_qc_box = """                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Faststart Web Optimized</span>
                                    <span class="text-emerald-400 font-mono">Yes (moov atom indexed)</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Audio Voice Engine</span>
                                    <span class="text-purple-300 font-mono text-[11px]" id="outVoiceEngine">en-US-ChristopherNeural</span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Visual Motion Engine</span>
                                    <span class="text-cyan-300 font-mono text-[11px]" id="outMotionEngine">kenburns_cinematic</span>
                                </div>"""

if old_qc_box in html:
    html = html.replace(old_qc_box, new_qc_box, 1)
    print("Added voice & motion engine display to index.html")
else:
    old_crlf = old_qc_box.replace("\n", "\r\n")
    new_crlf = new_qc_box.replace("\n", "\r\n")
    if old_crlf in html:
        html = html.replace(old_crlf, new_crlf, 1)
        print("Added voice & motion engine display (CRLF) to index.html")
    else:
        print("Could not find old_qc_box")

# 2. Add assignment in renderStudioResult
old_render = """            document.getElementById('outCost').innerText = `$${data.cost_est_usd} USD`;"""
new_render = """            document.getElementById('outCost').innerText = `$${data.cost_est_usd} USD`;
            if (document.getElementById('outVoiceEngine')) document.getElementById('outVoiceEngine').innerText = data.audio_voice || 'Default';
            if (document.getElementById('outMotionEngine')) document.getElementById('outMotionEngine').innerText = data.motion_style || 'kenburns_cinematic';"""

if old_render in html:
    html = html.replace(old_render, new_render, 1)
    print("Added JS assignments in renderStudioResult")
else:
    old_render_crlf = old_render.replace("\n", "\r\n")
    new_render_crlf = new_render.replace("\n", "\r\n")
    if old_render_crlf in html:
        html = html.replace(old_render_crlf, new_render_crlf, 1)
        print("Added JS assignments (CRLF) in renderStudioResult")
    else:
        print("Could not find old_render")

index_path.write_text(html, encoding="utf-8")
print("Saved updated index.html")
