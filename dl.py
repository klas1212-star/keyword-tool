import os, urllib.request, ssl
domain = 'yezisheji.com'
out_path = os.path.join('static', 'images', 'favicons', f'{domain}.png')
os.makedirs(os.path.dirname(out_path), exist_ok=True)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
for url in [f'https://{domain}/favicon.ico', f'http://{domain}/favicon.ico']:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, context=ctx, timeout=10)
        d = r.read()
        if len(d) > 100:
            open(out_path,'wb').write(d); print(f'OK {len(d)}b'); break
    except Exception as e: print(f'{url}: {e}')
else: print('MISS')
