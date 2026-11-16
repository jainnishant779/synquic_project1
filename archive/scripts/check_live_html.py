import urllib.request

url = "http://13.205.82.99/"
html = urllib.request.urlopen(url).read().decode("utf-8")
print("studioVoiceSelect in live HTML:", "studioVoiceSelect" in html)
print("studioMotionSelect in live HTML:", "studioMotionSelect" in html)
print("studioModelSelect in live HTML:", "studioModelSelect" in html)
if "studioVoiceSelect" in html:
    idx = html.find("studioVoiceSelect")
    print(html[idx-50:idx+150])
else:
    idx = html.find("studioModelSelect")
    print(html[idx-50:idx+200])
