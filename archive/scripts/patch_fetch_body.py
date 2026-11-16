from pathlib import Path

HTML = Path("d:/research_synquic/web_ec2/templates/index.html")
html = HTML.read_text(encoding="utf-8")

# Find and patch fetch body
old = (
    "                    body: JSON.stringify({\n"
    "                        prompt: prompt,\n"
    "                        director_model: model,\n"
    "                        duration_s: duration,\n"
    "                        style: style,\n"
    "                        aspect_ratio: aspect\n"
    "                    })"
)
new = (
    "                    body: JSON.stringify({\n"
    "                        prompt: prompt,\n"
    "                        director_model: model,\n"
    "                        duration_s: duration,\n"
    "                        style: style,\n"
    "                        aspect_ratio: aspect,\n"
    "                        audio_voice: document.getElementById('studioVoiceSelect').value,\n"
    "                        motion_style: document.getElementById('studioMotionSelect').value\n"
    "                    })"
)

if old in html:
    html = html.replace(old, new, 1)
    print("OK: patched fetch body (LF)")
else:
    # try CRLF
    old_crlf = old.replace("\n", "\r\n")
    new_crlf = new.replace("\n", "\r\n")
    if old_crlf in html:
        html = html.replace(old_crlf, new_crlf, 1)
        print("OK: patched fetch body (CRLF)")
    else:
        # manual inspect
        idx = html.find("body: JSON.stringify")
        snippet = html[idx: idx + 300]
        print("SNIPPET:", repr(snippet))
        raise RuntimeError("Not found!")

HTML.write_text(html, encoding="utf-8")
print("Saved index.html")
