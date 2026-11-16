from pathlib import Path

index_path = Path("web_ec2/templates/index.html")
content = index_path.read_text(encoding="utf-8")

# 1. Update features input placeholder
old_ph = 'placeholder="e.g. 0.6s Rapid Lift, RFID, Radar Sensor"'
new_ph = 'placeholder="e.g. High-Speed Rapid Lift, RFID, Radar Sensor"'
if old_ph in content:
    content = content.replace(old_ph, new_ph)
    print("Updated features input placeholder.")

# 2. Update PRESETS.parkfnb prompt text
old_pfnb_preset = 'MAKE AD FOR PARKFNB BARRIER: 15-second 4-stage commercial. Scene 1: Crowded parking bottleneck with vehicle looking for space. Scene 2: High-tech smart ANPR camera detects vehicle and recognizes license plate. Scene 3: Brushless boom barrier elevates rapidly in 0.6 seconds for authorized access. Scene 4: Mobile parking slot booking app and ParkFnB brand reveal.'
new_pfnb_preset = 'MAKE AD FOR PARKFNB BARRIER: 15-second 4-stage commercial. Scene 1: Crowded parking bottleneck with vehicle looking for space. Scene 2: High-tech smart ANPR camera detects vehicle and recognizes license plate. Scene 3: High-speed brushless boom barrier elevates rapidly for authorized access. Scene 4: Mobile parking slot booking app and ParkFnB brand reveal.'
if old_pfnb_preset in content:
    content = content.replace(old_pfnb_preset, new_pfnb_preset)
    print("Updated ParkFnB preset prompt text.")

# 3. Update loadStudioPreset('parkfnb') features value
old_pfnb_feat = "document.getElementById('studioFeaturesInput').value = 'ANPR Plate Recognition, 0.6s Rapid Lift, Mobile Slot Booking App';"
new_pfnb_feat = "document.getElementById('studioFeaturesInput').value = 'ANPR Plate Recognition, High-Speed Rapid Lift, Mobile Slot Booking App';"
if old_pfnb_feat in content:
    content = content.replace(old_pfnb_feat, new_pfnb_feat)
    print("Updated ParkFnB preset features value.")

index_path.write_text(content, encoding="utf-8")
print("Done writing web_ec2/templates/index.html!")
