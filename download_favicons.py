"""Download final missing favicons"""
import os
import urllib.request
import ssl

domains_missing = ['zuotang.com', 'pan.baidu.com']

output_dir = os.path.join('static', 'images', 'favicons')

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

for domain in domains_missing:
    out_path = os.path.join(output_dir, f'{domain}.png')
    if os.path.exists(out_path):
        print(f'[EXISTS] {domain}')
        continue

    urls = [
        f'https://{domain}/favicon.ico',
        f'https://www.{domain}/favicon.ico',
        f'http://{domain}/favicon.ico',
        f'http://www.{domain}/favicon.ico',
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=12) as resp:
                data = resp.read()
            if len(data) > 100:
                with open(out_path, 'wb') as f:
                    f.write(data)
                print(f'[OK] {domain} ({len(data)} bytes)')
                break
        except Exception as e:
            print(f'[ERR] {url}: {e}')
    else:
        print(f'[MISS] {domain}')
print('Done!')
