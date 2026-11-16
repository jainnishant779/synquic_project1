import urllib.request, urllib.parse

p = "Modern smartphone displaying sleek Homingo home services mobile app interface 1-tap booking confirmed verified technician assigned glowing UI"
url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=576&height=1024&nologo=true"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print("Success! Size:", len(r.read()))
except Exception as e:
    print("Failed:", e)
