from pathlib import Path

index_path = Path("web_ec2/templates/index.html")
content = index_path.read_text(encoding="utf-8")

# 1. Add QC checks container in HTML
target_qc_panel = '''                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Cost reported by API</span>
                                    <span class="text-white font-mono" id="outCost">Not reported</span>
                                </div>
                            </div>'''

replacement_qc_panel = '''                                <div class="flex items-center justify-between">
                                    <span class="text-slate-400">Cost reported by API</span>
                                    <span class="text-white font-mono" id="outCost">Not reported</span>
                                </div>
                            </div>

                            <div class="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-[11px] space-y-1.5" id="outQcChecksContainer">
                                <div class="font-bold text-slate-300 mb-1 flex items-center justify-between">
                                    <span><i class="fa-solid fa-list-check text-cyan-400 mr-1"></i> 7-Point Automated QC Audit</span>
                                    <span class="text-[9px] text-slate-400">Measured Engine Facts</span>
                                </div>
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[10px]" id="outQcChecksList">
                                    <div class="p-1 rounded border border-slate-800 text-slate-500">QC checks will populate upon generation</div>
                                </div>
                            </div>'''

content = content.replace(target_qc_panel, replacement_qc_panel, 1)

# 2. Update JavaScript to render the checks
target_js = '''            if (document.getElementById('outQcScore')) {
                document.getElementById('outQcScore').innerText = data.qc_report?.score == null ? '98/100' : `${data.qc_report.score}/100`;
            }
            if (document.getElementById('outQcVerdict')) {
                document.getElementById('outQcVerdict').innerText = data.qc_report?.verdict || 'PASSED';
            }'''

replacement_js = '''            if (document.getElementById('outQcScore')) {
                document.getElementById('outQcScore').innerText = data.qc_report?.score == null ? 'Not scored' : `${data.qc_report.score}/100`;
            }
            if (document.getElementById('outQcVerdict')) {
                document.getElementById('outQcVerdict').innerText = data.qc_report?.verdict || 'Visual review required';
            }
            if (data.qc_report?.checks) {
                const checks = data.qc_report.checks;
                const container = document.getElementById('outQcChecksList');
                if (container) {
                    const checkLabels = {
                        actual_video_generation: { label: "AI Video Provenance", passDesc: "Genuine AI Video", failDesc: "Motion Fallback" },
                        static_scene_detection: { label: "Static Scene Defect", passDesc: "No Freeze (Active)", failDesc: "Freeze Detected", invert: true },
                        duplicate_scene_detection: { label: "Duplicate Scenes", passDesc: "Unique Scenes", failDesc: "Duplicate Detected", invert: true },
                        visual_relevance: { label: "Visual Relevance", passDesc: "Domain Relevant", failDesc: "Irrelevant Stock" },
                        brand_consistency: { label: "Brand Integrity", passDesc: "Consistent", failDesc: "Inconsistent" },
                        text_quality: { label: "Typography Quality", passDesc: "Unique & Clean", failDesc: "Repetitive/Badges" },
                        storyboard_adherence: { label: "Storyboard Arc", passDesc: "4-Stage Narrative", failDesc: "Incomplete Arc" }
                    };
                    let html = '';
                    for (const [k, v] of Object.entries(checks)) {
                        const meta = checkLabels[k] || { label: k, passDesc: "Passed", failDesc: "Failed" };
                        const isGood = meta.invert ? !v : v;
                        const badgeColor = isGood ? 'text-emerald-400 bg-emerald-950/60 border-emerald-800/40' : 'text-amber-400 bg-amber-950/60 border-amber-800/40';
                        const icon = isGood ? 'fa-check' : (meta.invert ? 'fa-triangle-exclamation' : 'fa-xmark');
                        const statusTxt = isGood ? meta.passDesc : meta.failDesc;
                        html += `<div class="p-1 rounded border ${badgeColor} flex items-center justify-between">
                            <span class="truncate mr-1">${meta.label}</span>
                            <span class="font-mono font-bold"><i class="fa-solid ${icon} mr-0.5"></i> ${statusTxt}</span>
                        </div>`;
                    }
                    container.innerHTML = html;
                }
            }'''

content = content.replace(target_js, replacement_js, 1)

index_path.write_text(content, encoding="utf-8")
print("Updated web_ec2/templates/index.html with 7-point QC display.")
