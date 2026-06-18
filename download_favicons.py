"""在 PythonAnywhere 服务器上运行此脚本下载所有 favicon"""
import os, urllib.request, ssl

domains = [
    "huaban.com", "zcool.com.cn", "pinterest.com", "unsplash.com",
    "pixabay.com", "pexels.com", "remove.bg", "zuotang.com",
    "koukoutu.com", "maoken.com", "ziyouziti.com", "fonts.google.com",
    "edu.zcool.com.cn", "uisdc.com", "colorhunt.co", "coolors.co",
    "zhongguose.com", "canva.cn", "chuangkit.com", "51yuansu.com",
    "58pic.com", "588ku.com", "midjourney.com", "stablediffusionweb.com",
    "aliyun.com", "yige.baidu.com", "eagle.cool", "pullywood.com",
    "ublockorigin.com",
]

out = os.path.join(os.path.dirname(__file__), "static", "images", "favicons")
os.makedirs(out, exist_ok=True)
ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

for d in set(domains):
    fname = os.path.join(out, d + ".png")
    for url in [
        f"https://www.google.com/s2/favicons?domain={d}&sz=64",
        f"https://api.iowen.cn/favicon/{d}.png",
    ]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, context=ctx, timeout=15).read()
            if len(data) > 100:
                with open(fname, "wb") as f: f.write(data)
                print(f"OK  {d} ({len(data)} bytes)")
                break
        except: continue
    else:
        print(f"FAIL {d}")

print("Done!")
