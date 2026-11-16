with open("web_ec2/templates/index.html", "r", encoding="utf-8") as f:
    text = f.read()

target = '<option value="instagram">📱 Tech, SaaS & Mobile Apps</option>'
replacement = """<option value="home_services">🛠️ Home Services, Repairs & On-Demand Apps</option>
                                    <option value="tech_saas">📱 Mobile Apps, SaaS & Tech Platforms</option>
                                    <option value="instagram">🎬 Social Media & Content Creators</option>"""

# Also ensure we remove any duplicate home_services option if present
if target in text:
    text = text.replace(target, replacement, 1)
    print("Patched index.html industry options!")

# Check if unescaped template literal exists in static markup
if "${escapeHtml(data.scene_traces[idx].keyframe_url)}" in text:
    print("Found keyframe_url template string in index.html (this is in JS template, which is normal)")

with open("web_ec2/templates/index.html", "w", encoding="utf-8") as f:
    f.write(text)
