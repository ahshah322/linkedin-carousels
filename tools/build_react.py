"""Build a React carousel (5 slides, 1080x1350) from a JSON spec and render it to PDF.
Usage: python3 tools/build_react.py react/specs/props-vs-state.json react/props-vs-state.pdf
Needs: npm install (fonts), google-chrome, Pillow.
Same layout pattern as the .NET carousels, with the React cyan accent (#61DAFB).
Rule: dark text on cyan, never white text on cyan.
"""
import html, json, os, re, subprocess, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = f"{ROOT}/node_modules/@fontsource"
FONTS = "".join(
    f"@font-face{{font-family:'Nunito';font-weight:{w};src:url('file://{F}/nunito/files/nunito-latin-{w}-normal.woff2')}}\n" for w in (500, 600, 700, 800)
) + "".join(
    f"@font-face{{font-family:'DM Mono';font-weight:{w};src:url('file://{F}/dm-mono/files/dm-mono-latin-{w}-normal.woff2')}}\n" for w in (400, 500)
)

CY, CY_D, CY_L = "#61DAFB", "#21A9D4", "#9BE9FF"   # React cyan, darker, lighter
INK = "#06131A"                                       # text colour used ON cyan
OR = "#FF4500"
CARD = "background:linear-gradient(165deg,#1B2733 0%,#0F1721 100%);border:1px solid rgba(255,255,255,0.15);box-shadow:0 2px 4px rgba(0,0,0,0.55),0 14px 28px rgba(0,0,0,0.5),0 34px 60px -8px rgba(0,0,0,0.7),inset 0 1px 0 rgba(255,255,255,0.20)"
GLOW = "text-shadow:0 10px 22px rgba(0,0,0,0.7),0 2px 4px rgba(0,0,0,0.6),0 0 38px rgba(97,218,251,0.40)"
PILL = f"display:inline-block;background:linear-gradient(180deg,{CY_L},{CY});color:{INK};box-shadow:0 12px 26px rgba(97,218,251,0.40),0 2px 4px rgba(0,0,0,0.55),inset 0 1px 0 rgba(255,255,255,0.6);font:800 28px/1 'Nunito',sans-serif;letter-spacing:0.08em;padding:14px 28px;border-radius:999px"
PILL_W = f"display:inline-block;background:linear-gradient(180deg,#FFFFFF,#D6EEF7);color:{INK};box-shadow:0 12px 26px rgba(214,238,247,0.25),0 2px 4px rgba(0,0,0,0.55),inset 0 1px 0 #fff;font:800 28px/1 'Nunito',sans-serif;letter-spacing:0.08em;padding:14px 28px;border-radius:999px"
BADGE = f"width:56px;height:56px;border-radius:50%;background:linear-gradient(180deg,{CY_L},{CY_D});box-shadow:0 10px 20px rgba(97,218,251,0.40),0 2px 4px rgba(0,0,0,0.55),inset 0 1px 0 rgba(255,255,255,0.6);color:{INK};font:800 30px/1 'Nunito',sans-serif;display:flex;align-items:center;justify-content:center;flex:none"

ATOM = lambda style: (f'<svg aria-hidden="true" viewBox="-11.5 -10.2 23 20.4" style="position:absolute;z-index:-1;{style}"><g fill="none" stroke="{CY}" stroke-width="1"><ellipse rx="10" ry="4.2"/><ellipse rx="10" ry="4.2" transform="rotate(60)"/><ellipse rx="10" ry="4.2" transform="rotate(120)"/></g><circle r="1.8" fill="{CY}"/></svg>')
LOGOS = (ATOM("width:380px;height:340px;left:720px;top:-20px;transform:rotate(-11deg);opacity:0.10;filter:drop-shadow(0 0 16px rgba(97,218,251,0.5))")
         + ATOM("width:470px;height:420px;left:-80px;top:1000px;transform:rotate(-21deg);opacity:0.10;filter:drop-shadow(0 0 16px rgba(97,218,251,0.5))"))

PHOTO = f"file://{ROOT}/assets/photo.png"
E = html.escape


def hl(line):
    """Tiny JS/JSX highlighter. Returns HTML for one code line."""
    kw = r"\b(function|return|const|let|var|import|from|export|default|if|else|new|true|false|null|async|await|useState|useEffect|useRef|useMemo|useCallback|useReducer|useContext|memo)\b"
    pat = re.compile(r"(//.*$)|(\"[^\"]*\"|'[^']*'|`[^`]*`)|(</?[A-Za-z][\w.]*)|" + kw)
    out, pos = "", 0
    for m in pat.finditer(line):
        out += E(line[pos:m.start()])
        t = m.group(0)
        if m.group(1): out += f'<span style="color:#9AAAB8">{E(t)}</span>'
        elif m.group(2): out += f'<span style="color:#FFC8A6">{E(t)}</span>'
        elif m.group(3): out += f'<span style="color:#E4F7FF">{E(t)}</span>'
        else: out += f'<span style="color:{CY}">{E(t)}</span>'
        pos = m.end()
    out += E(line[pos:])
    return out.replace(" ", "&nbsp;") if False else out


def code_block(lines):
    rows = "".join(f'<div style="white-space:pre">{hl(l) if l.strip() else "&nbsp;"}</div>' for l in lines)
    return (f'<div style="margin-top:26px"><div style="background:linear-gradient(180deg,#101A24 0%,#091017 100%);border:2px solid {CY};border-radius:32px;padding:30px 36px;'
            f"font:500 28px/1.45 'DM Mono',monospace;color:#EAF6FB;box-shadow:0 30px 46px -22px rgba(97,218,251,0.45),0 0 0 6px rgba(255,255,255,0.03),inset 0 1px 0 rgba(255,255,255,0.14)\">{rows}</div></div>")


def shell(tag, n, total, inner):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS} body{{margin:0}}</style></head><body>
<div style="width:1080px;height:1350px;box-sizing:border-box;padding:56px 72px;display:flex;flex-direction:column;position:relative;isolation:isolate;background:radial-gradient(900px 620px at 100% 0%, rgba(97,218,251,0.26), rgba(7,9,15,0) 62%), #07090F;color:#fff;font-family:'Nunito',sans-serif;overflow:hidden">
{LOGOS}
<div style="display:flex;justify-content:space-between;align-items:center;height:40px">
<div style="display:flex;align-items:center;gap:14px"><div style="width:14px;height:14px;border-radius:50%;background:{OR};box-shadow:0 0 12px {OR}"></div><span style="font:600 28px/1 'Nunito',sans-serif;letter-spacing:0.08em;color:#E3F6FF">{E(tag)}</span></div>
<span style="font:600 28px/1 'Nunito',sans-serif;color:#E3F6FF">{n} / {total}</span></div>
{inner}
</div></body></html>"""


def footer():
    return (f'<div style="display:flex;align-items:center;gap:18px;margin-top:auto;padding-top:18px;border-top:1px solid rgba(255,255,255,0.14)">'
            f'<div style="width:68px;height:68px;border-radius:50%;overflow:hidden;flex:none;border:3px solid {CY};box-sizing:border-box;background:#000;box-shadow:0 8px 16px rgba(0,0,0,0.6)"><img src="{PHOTO}" alt="" style="display:block;width:102px;height:auto;max-width:none;margin-left:-22px;margin-top:-2px"></div>'
            f'<div style="display:flex;flex-direction:column;gap:4px"><span style="font:800 30px/1.1 \'Nunito\',sans-serif;color:#fff">Ali Husnain Shah</span><span style="font:700 28px/1.1 \'Nunito\',sans-serif;color:#BFEFFF">@ahshah322</span></div>'
            f'<div style="margin-left:auto"><div style="width:48px;height:48px;border-radius:50%;background:linear-gradient(180deg,#FF6A33,#E03A00);box-shadow:0 10px 18px rgba(255,69,0,0.45),0 2px 4px rgba(0,0,0,0.55);display:flex;align-items:center;justify-content:center"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#08070E" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></div></div></div>')


def cover(s, tag, total):
    items = "".join(f'<div style="display:flex;align-items:center;gap:22px"><div style="{BADGE}">{i}</div><span style="font:500 32px/1.2 \'Nunito\',sans-serif;color:#fff">{E(t)}</span></div>' for i, t in enumerate(s["cover"]["items"], 1))
    a, b = s["cover"]["a"], s["cover"]["b"]
    big = lambda w, glow: f'<span style="font:800 172px/1.0 \'Nunito\',sans-serif;color:#fff;letter-spacing:0.02em;{glow}">{E(w)}</span>'
    inner = f"""<div style="margin-top:40px;display:flex;flex-direction:column;{CARD};border-radius:40px;padding:24px 40px 32px">
{big(a, GLOW)}<span style="font:700 68px/1.1 'Nunito',sans-serif;color:#FF6A33;margin:4px 0 6px 10px;text-shadow:0 4px 0 #8F2400,0 10px 14px rgba(0,0,0,0.6)">vs</span>{big(b, GLOW)}</div>
<p style="margin:34px 0 0 0;font:500 38px/1.3 'Nunito',sans-serif;color:#E3F6FF">{E(s['cover']['hook'])}</p>
<div style="position:relative;margin-top:34px"><div style="position:absolute;left:44px;right:44px;top:0;bottom:-26px;border-radius:30px;background:#0B121A;border:1px solid rgba(255,255,255,0.06);box-shadow:0 20px 30px rgba(0,0,0,0.6)"></div><div style="position:absolute;left:22px;right:22px;top:0;bottom:-13px;border-radius:30px;background:#111A24;border:1px solid rgba(255,255,255,0.08)"></div>
<div style="position:relative;{CARD};border-radius:30px;padding:30px 34px;display:flex;flex-direction:column;gap:18px">{items}</div></div>
{footer()}"""
    return shell(tag, 1, total, inner)


def concept(c, n, tag, total):
    dot = f'<span style="width:14px;height:14px;border-radius:50%;margin-top:11px;flex:none;background:linear-gradient(180deg,{CY_L},{CY_D});box-shadow:0 2px 0 #0A4A5E"></span>'
    pts = "".join(f'<div style="display:flex;gap:14px;align-items:flex-start">{dot}<span style="font:500 28px/1.3 \'Nunito\',sans-serif;color:#EAF6FB">{E(t)}</span></div>' for t in c["points"])
    inner = f"""<div style="margin-top:30px;display:flex;align-items:center;justify-content:space-between"><h1 style="margin:0;font:800 104px/1.05 'Nunito',sans-serif;color:#fff;{GLOW}">{E(c['title'])}</h1><div><span style="{PILL}">{E(c['pill'])}</span></div></div>
<p style="margin:10px 0 0 0;font:500 32px/1.3 'Nunito',sans-serif;color:#E3F6FF">{E(c['sub'])}</p>
{code_block(c['code'])}
<div style="margin-top:24px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:20px;align-items:stretch">
<div style="{CARD};border-radius:32px;padding:26px 28px;display:flex;flex-direction:column;gap:14px"><span style="font:700 28px/1.2 'Nunito',sans-serif;letter-spacing:0.1em;color:{CY_L}">HOW IT BEHAVES</span>{pts}</div>
<div style="{CARD};border-radius:32px;padding:26px 28px;display:flex;flex-direction:column;gap:10px"><span style="font:700 28px/1.2 'Nunito',sans-serif;letter-spacing:0.1em;color:{CY_L}">USE IT FOR</span><span style="font:500 28px/1.3 'Nunito',sans-serif;color:#fff">{E(c['use'])}</span>
<span style="margin-top:8px;font:700 28px/1.2 'Nunito',sans-serif;letter-spacing:0.1em;color:{OR}">WATCH OUT</span><span style="font:500 28px/1.3 'Nunito',sans-serif;color:#fff">{E(c['watch'])}</span></div></div>
{footer()}"""
    return shell(tag, n, total, inner)


def compare(s, n, tag, total):
    cmp_ = s["compare"]
    g = "display:grid;grid-template-columns:200px minmax(0,1fr) minmax(0,1fr);column-gap:12px;align-items:stretch"
    cell = lambda t, top, grad: f'<div style="background:linear-gradient(165deg,{grad} 0%,#0E151D 100%);border-radius:24px;padding:18px 20px;font:500 28px/1.3 \'Nunito\',sans-serif;color:#fff;border-top:4px solid {top};box-shadow:0 14px 20px -12px rgba(0,0,0,0.8),inset 0 1px 0 rgba(255,255,255,0.10)">{E(t)}</div>'
    rows = "".join(f'<div style="{g}"><div style="font:600 28px/1.3 \'Nunito\',sans-serif;color:#E3F6FF;padding:18px 0">{E(r[0])}</div>{cell(r[1], CY, "#1A2A38")}{cell(r[2], "#FFFFFF", "#25303B")}</div>' for r in cmp_["rows"])
    inner = f"""<h1 style="margin:30px 0 0 0;font:800 96px/1.05 'Nunito',sans-serif;color:#fff;{GLOW}">Side by side</h1>
<div style="{g};margin-top:26px"><div></div><div><span style="{PILL}">{E(cmp_['a'])}</span></div><div><span style="{PILL_W}">{E(cmp_['b'])}</span></div></div>
<div style="margin-top:22px;display:flex;flex-direction:column;gap:10px">{rows}</div>
<div style="margin-top:24px;{CARD};border-radius:32px;padding:24px 30px;display:flex;flex-direction:column;gap:8px"><span style="font:700 28px/1.2 'Nunito',sans-serif;letter-spacing:0.1em;color:{OR}">RULE OF THUMB</span><span style="font:500 30px/1.3 'Nunito',sans-serif;color:#fff">{E(cmp_['rule'])}</span></div>
{footer()}"""
    return shell(tag, n, total, inner)


ICONS = {
    "comment": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1.1-4.6A8 8 0 1 1 21 12z"/>',
    "save": '<path d="M6 3h12v18l-6-4.5L6 21V3z"/>',
    "repost": '<path d="M17 2l4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4M21 13v2a3 3 0 0 1-3 3H3"/>',
    "follow": '<circle cx="9" cy="8" r="4"/><path d="M1.5 21c0-3.6 3.2-6 7.5-6s7.5 2.4 7.5 6"/><path d="M19 7v6M16 10h6"/>',
}
LI = '<svg width="38" height="38" viewBox="3.5 3.5 17 17" fill="none"><path fill="#ffffff" d="M18.72 3.99997H5.37C5.19793 3.99191 5.02595 4.01786 4.86392 4.07635C4.70189 4.13484 4.55299 4.22471 4.42573 4.34081C4.29848 4.45692 4.19537 4.59699 4.12232 4.75299C4.04927 4.909 4.0077 5.07788 4 5.24997V18.63C4.01008 18.9901 4.15766 19.3328 4.41243 19.5875C4.6672 19.8423 5.00984 19.9899 5.37 20H18.72C19.0701 19.9844 19.4002 19.8322 19.6395 19.5761C19.8788 19.32 20.0082 18.9804 20 18.63V5.24997C20.0029 5.08247 19.9715 4.91616 19.9078 4.76122C19.8441 4.60629 19.7494 4.466 19.6295 4.34895C19.5097 4.23191 19.3672 4.14059 19.2108 4.08058C19.0544 4.02057 18.8874 3.99314 18.72 3.99997ZM9 17.34H6.67V10.21H9V17.34ZM7.89 9.12997C7.72741 9.13564 7.5654 9.10762 7.41416 9.04768C7.26291 8.98774 7.12569 8.89717 7.01113 8.78166C6.89656 8.66615 6.80711 8.5282 6.74841 8.37647C6.6897 8.22474 6.66301 8.06251 6.67 7.89997C6.66281 7.73567 6.69004 7.57169 6.74995 7.41854C6.80986 7.26538 6.90112 7.12644 7.01787 7.01063C7.13463 6.89481 7.2743 6.80468 7.42793 6.74602C7.58157 6.68735 7.74577 6.66145 7.91 6.66997C8.07259 6.66431 8.2346 6.69232 8.38584 6.75226C8.53709 6.8122 8.67431 6.90277 8.78887 7.01828C8.90344 7.13379 8.99289 7.27174 9.05159 7.42347C9.1103 7.5752 9.13699 7.73743 9.13 7.89997C9.13719 8.06427 9.10996 8.22825 9.05005 8.3814C8.99014 8.53456 8.89888 8.6735 8.78213 8.78931C8.66537 8.90513 8.5257 8.99526 8.37207 9.05392C8.21843 9.11259 8.05423 9.13849 7.89 9.12997ZM17.34 17.34H15V13.44C15 12.51 14.67 11.87 13.84 11.87C13.5822 11.8722 13.3313 11.9541 13.1219 12.1045C12.9124 12.2549 12.7546 12.4664 12.67 12.71C12.605 12.8926 12.5778 13.0865 12.59 13.28V17.34H10.29V10.21H12.59V11.21C12.7945 10.8343 13.0988 10.5225 13.4694 10.3089C13.84 10.0954 14.2624 9.98848 14.69 9.99997C16.2 9.99997 17.34 11 17.34 13.13V17.34Z"/></svg>'
GH = '<svg width="38" height="38" viewBox="0 0 16 16"><path fill="#ffffff" fill-rule="evenodd" clip-rule="evenodd" d="M7.976 0A7.977 7.977 0 0 0 0 7.976c0 3.522 2.3 6.507 5.431 7.584.392.049.538-.196.538-.392v-1.37c-2.201.49-2.69-1.076-2.69-1.076-.343-.93-.881-1.175-.881-1.175-.734-.489.048-.489.048-.489.783.049 1.224.832 1.224.832.734 1.223 1.859.88 2.3.685.048-.538.293-.88.489-1.076-1.762-.196-3.621-.881-3.621-3.964 0-.88.293-1.566.832-2.153-.05-.147-.343-.978.098-2.055 0 0 .685-.196 2.201.832.636-.196 1.322-.245 2.007-.245s1.37.098 2.006.245c1.517-1.027 2.202-.832 2.202-.832.44 1.077.146 1.908.097 2.104a3.16 3.16 0 0 1 .832 2.153c0 3.083-1.86 3.719-3.62 3.915.293.244.538.733.538 1.467v2.202c0 .196.146.44.538.392A7.984 7.984 0 0 0 16 7.976C15.951 3.572 12.38 0 7.976 0z"/></svg>'


def cta(s, n, tag, total):
    c = s["cta"]
    acts = "".join(
        f'<div style="{CARD};border-radius:30px;padding:14px 28px 14px 16px;display:flex;align-items:center;gap:22px"><div style="width:60px;height:60px;border-radius:50%;background:linear-gradient(180deg,{CY_L},{CY_D});box-shadow:0 10px 20px rgba(97,218,251,0.40),0 2px 4px rgba(0,0,0,0.55),inset 0 1px 0 rgba(255,255,255,0.6);display:flex;align-items:center;justify-content:center;flex:none"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{ICONS[i]}</svg></div><span style="font:700 34px/1.2 \'Nunito\',sans-serif;color:#fff">{E(t)}</span></div>'
        for i, t in c["actions"])
    h = E(c["headline"]).replace("{a}", f'<span style="color:#FF6A33;text-shadow:0 10px 22px rgba(0,0,0,0.7),0 2px 4px rgba(0,0,0,0.6),0 0 38px rgba(255,69,0,0.40)">').replace("{/a}", "</span>")
    inner = f"""<h1 style="margin:30px 0 0 0;font:800 96px/1.05 'Nunito',sans-serif;color:#fff;{GLOW}">{h}</h1>
<p style="margin:16px 0 0 0;font:600 36px/1.3 'Nunito',sans-serif;color:#E3F6FF">{E(c['question'])}</p>
<div style="margin-top:36px;display:flex;flex-direction:column;gap:18px">{acts}</div>
<div style="position:relative;margin-top:auto"><div style="position:absolute;left:36px;right:36px;top:0;bottom:-20px;border-radius:36px;background:#0B121A;border:1px solid rgba(255,255,255,0.06)"></div><div style="position:absolute;left:18px;right:18px;top:0;bottom:-10px;border-radius:36px;background:#111A24;border:1px solid rgba(255,255,255,0.08)"></div>
<div style="position:relative;{CARD};border-radius:36px;padding:30px 34px;display:flex;align-items:center;gap:30px">
<div style="width:170px;height:170px;border-radius:50%;overflow:hidden;flex:none;border:3px solid {CY};box-sizing:border-box;background:#000;box-shadow:0 8px 16px rgba(0,0,0,0.6)"><img src="{PHOTO}" alt="" style="display:block;width:255px;height:auto;max-width:none;margin-left:-55px;margin-top:-5px"></div>
<div style="display:flex;flex-direction:column;gap:12px"><span style="font:800 42px/1.1 'Nunito',sans-serif;color:#fff">Ali Husnain Shah</span><span style="font:600 28px/1.25 'Nunito',sans-serif;color:#E3F6FF">Senior Full Stack .NET Developer | AI Automation</span>
<div style="display:flex;align-items:center;gap:16px">{LI}<span style="font:700 30px/1.2 'Nunito',sans-serif;color:#fff">@ahshah322</span></div>
<div style="display:flex;align-items:center;gap:16px">{GH}<span style="font:700 30px/1.2 'Nunito',sans-serif;color:#fff">@ahshah322</span></div></div></div></div>"""
    return shell(tag, n, total, inner)


def shot(html_str, png):
    tmp = png.replace(".png", ".html")
    open(tmp, "w").write(html_str)
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--window-size=1080,1350", f"--screenshot={png}", f"file://{tmp}"], capture_output=True, timeout=180)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    out_pdf = sys.argv[2]
    build = os.path.join(os.path.dirname(os.path.abspath(out_pdf)), "build-" + os.path.basename(out_pdf)[:-4])
    os.makedirs(build, exist_ok=True)
    tag, total = spec["tag"], 5
    pages = [cover(spec, tag, total), concept(spec["a"], 2, tag, total), concept(spec["b"], 3, tag, total), compare(spec, 4, tag, total), cta(spec, 5, tag, total)]
    pngs = []
    for i, p in enumerate(pages, 1):
        png = f"{build}/slide{i}.png"
        shot(p, png)
        pngs.append(png)
    ims = [Image.open(p).convert("RGB") for p in pngs]
    ims[0].save(out_pdf, save_all=True, append_images=ims[1:], resolution=200, quality=95, subsampling=0)
    print("wrote", out_pdf, len(ims), "pages")
