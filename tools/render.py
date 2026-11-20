"""Render a folder of 5 slide HTML files (*.dc.html) into PNGs and one PDF.
Usage: python3 tools/render.py <slides_dir> <out_pdf>
Needs: npm install (fonts), google-chrome, Pillow.
"""
import re, subprocess, sys, glob, os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = f"{ROOT}/node_modules/@fontsource"
ff = ""
for w in (500,600,700,800): ff += f"@font-face{{font-family:'Nunito';font-weight:{w};src:url('file://{F}/nunito/files/nunito-latin-{w}-normal.woff2')}}\n"
for w in (400,500): ff += f"@font-face{{font-family:'DM Mono';font-weight:{w};src:url('file://{F}/dm-mono/files/dm-mono-latin-{w}-normal.woff2')}}\n"
MAP = {"1c65ab73d616db9c10d870fb45162ab9":"csharp.png","21edb6e8c9da3bad373b775199ae43f1":"netviolet.png","a45dcb880c0ad2edaf859b44d8fac2dd":"photo.png"}
LOGOS = ('<img src="/_blob/1c65ab73d616db9c10d870fb45162ab9" alt="" aria-hidden="true" style="position: absolute; z-index: -1; width: 334px; height: 328px; left: 739px; top: -9px; transform: rotate(-11deg) scaleY(1.07); opacity: 0.1; filter: brightness(1.4) drop-shadow(0 0 16px rgba(150,120,255,0.4))">'
 '<img src="/_blob/21edb6e8c9da3bad373b775199ae43f1" alt="" aria-hidden="true" style="position: absolute; z-index: -1; width: 431px; height: 430px; left: -61px; top: 1016px; transform: rotate(-21deg); opacity: 0.1; filter: brightness(1.2) drop-shadow(0 0 16px rgba(150,120,255,0.4)); border-radius: 267px">')
def render(src, out_png):
    h = open(src).read()
    h = h.replace("margin-left:-19px;margin-top:-2px", "margin-left:-22px;margin-top:-2px")
    tag = "font-family:'Nunito',sans-serif;overflow:hidden\">"
    if "isolation:isolate" not in h:
        h = h.replace(tag, "font-family:'Nunito',sans-serif;overflow:hidden;position:relative;isolation:isolate\">" + LOGOS, 1)
    body = h[h.index("<x-dc>")+6:h.index("</x-dc>")]
    body = re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S)
    for k, v in MAP.items(): body = body.replace(f"/_blob/{k}", f"file://{ROOT}/assets/{v}")
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{ff} body{{margin:0}}</style></head><body>{body}</body></html>"
    tmp = out_png.replace(".png", ".html"); open(tmp, "w").write(html)
    subprocess.run(["google-chrome","--headless=new","--no-sandbox","--disable-gpu","--allow-file-access-from-files","--hide-scrollbars","--force-device-scale-factor=2","--window-size=1080,1350",f"--screenshot={out_png}",f"file://{tmp}"], capture_output=True, timeout=180)
if __name__ == "__main__":
    d, out_pdf = sys.argv[1], sys.argv[2]
    build = os.path.join(os.path.dirname(os.path.abspath(out_pdf)), "build"); os.makedirs(build, exist_ok=True)
    pngs = []
    for s in sorted(glob.glob(f"{d}/*.dc.html")):
        p = f"{build}/{os.path.basename(s).split('.')[0]}.png"; render(s, p); pngs.append(p)
    ims = [Image.open(p).convert("RGB") for p in pngs]
    ims[0].save(out_pdf, save_all=True, append_images=ims[1:], resolution=200, quality=95, subsampling=0)
    print("wrote", out_pdf, len(ims), "pages")
