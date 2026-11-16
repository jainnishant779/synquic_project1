import urllib.request
import json

url = "http://13.205.82.99/static/media/projects/proj_44b4c733/manifest.json"
req = urllib.request.urlopen(url)
data = json.loads(req.read().decode("utf-8"))
print(json.dumps(data, indent=2))
