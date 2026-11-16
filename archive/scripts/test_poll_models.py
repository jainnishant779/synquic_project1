import urllib.request
for m in ['turbo', 'flux', 'flux-realism', 'any-dark']:
    url = f'https://image.pollinations.ai/prompt/cat?model={m}&nologo=true'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(m, 'SUCCESS:', len(r.read()))
    except Exception as e:
        print(m, 'FAILED:', e)
