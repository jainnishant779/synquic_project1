import urllib.request

url = "http://13.205.82.99/"
html = urllib.request.urlopen(url).read().decode("utf-8")
print("<select id=\"studioVoiceSelect\" in HTML:", '<select id="studioVoiceSelect"' in html)
print("<select id=\"studioMotionSelect\" in HTML:", '<select id="studioMotionSelect"' in html)
print("<select id=\"studioModelSelect\" in HTML:", '<select id="studioModelSelect"' in html)
