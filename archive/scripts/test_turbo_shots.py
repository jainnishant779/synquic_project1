import urllib.request, urllib.parse, time

shots = [
    "Frustrated homeowner looking at sudden leaking kitchen faucet pipe under sink water leaking emergency repair commercial photography portrait",
    "Modern smartphone displaying sleek Homingo home services mobile app interface booking confirmed verified technician assigned glowing UI portrait",
    "Friendly certified home service technician in clean uniform with modern toolkit repairing faucet with precision in bright modern home",
    "Pristine sparkling modern living room and kitchen relaxed smiling homeowner holding phone peaceful clean luxury home five-star badge"
]

for idx, p in enumerate(shots, 1):
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=576&height=1024&model=turbo&nologo=true"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"Shot {idx} turbo SUCCESS: {len(r.read())} bytes in {time.time()-t0:.2f}s")
    except Exception as e:
        print(f"Shot {idx} turbo FAILED: {e}")
