import sys
from pathlib import Path

index_path = Path("d:/research_synquic/web_ec2/templates/index.html")
content = index_path.read_text(encoding="utf-8")

# 1. Add preset button
button_html = '''                            <button onclick="loadStudioPreset('realestate')" class="px-3 py-1 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 text-xs text-emerald-200 border border-emerald-800/60 transition flex items-center gap-1.5 font-semibold">
                                🏢 Property Broker App
                            </button>
'''

if "loadStudioPreset('realestate')" not in content:
    target_btn = '<button onclick="loadStudioPreset(\'instagram\')"'
    if target_btn in content:
        content = content.replace(target_btn, button_html + "                            " + target_btn, 1)
        print("Added Property Broker App button to index.html")
    else:
        print("Could not find target button in index.html")
else:
    print("Property Broker App button already present")

# 2. Add to PRESETS dictionary
preset_entry = '''            realestate: "MAKE AD FOR PROPERTY BROKER APP: Modern architectural real estate commercial for PrimeEstate property broker app, sunlit luxury glass villa with pool, broker handing keys to homebuyer, high-rise penthouse skyline view, verified listings.",\n'''

if "realestate:" not in content:
    target_dict = 'const PRESETS = {\n'
    if target_dict in content:
        content = content.replace(target_dict, target_dict + preset_entry, 1)
        print("Added realestate to PRESETS in index.html")
    else:
        print("Could not find PRESETS dict in index.html")
else:
    print("realestate already in PRESETS")

index_path.write_text(content, encoding="utf-8")
print("Saved updated index.html successfully!")
