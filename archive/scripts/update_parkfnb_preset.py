from pathlib import Path

index_path = Path("web_ec2/templates/index.html")
content = index_path.read_text(encoding="utf-8")

old_p = 'parkfnb: "MAKE AD FOR PARKFNB BARRIER: High-tech commercial for ParkFnB Intelligent Automated Boom Barrier, sleek illuminated LED barrier arm at modern corporate headquarters, 0.6 second high-speed RFID vehicle clearance, anti-crash radar protection, seamless multi-lane access.",'
new_p = 'parkfnb: "MAKE AD FOR PARKFNB BARRIER: 15-second 4-stage commercial. Scene 1: Crowded parking bottleneck with vehicle looking for space. Scene 2: High-tech smart ANPR camera detects vehicle and recognizes license plate. Scene 3: Brushless boom barrier elevates rapidly in 0.6 seconds for authorized access. Scene 4: Mobile parking slot booking app and ParkFnB brand reveal.",'
content = content.replace(old_p, new_p)

old_feat = "document.getElementById('studioFeaturesInput').value = '0.6s Rapid Lift, RFID Access, Anti-Crash Radar Sensor';"
new_feat = "document.getElementById('studioFeaturesInput').value = 'ANPR Plate Recognition, 0.6s Rapid Lift, Mobile Slot Booking App';"
content = content.replace(old_feat, new_feat)

old_cta = "document.getElementById('studioCtaInput').value = 'Install ParkFnB Barrier Today';"
new_cta = "document.getElementById('studioCtaInput').value = 'Upgrade to ParkFnB Smart Parking';"
content = content.replace(old_cta, new_cta)

index_path.write_text(content, encoding="utf-8")
print("Updated ParkFnB preset.")
