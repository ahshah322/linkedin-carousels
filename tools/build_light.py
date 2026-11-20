"""Light-theme carousel builder (design from Ali's Logging reference PDF).
1080x1350 (4:5) slides: tag pill, two-line headline, illustration top-right, tinted cards,
dark code blocks, navy Save / Repost / Follow bar on every slide.

Usage: python3 tools/build_light.py react/specs/es6-fundamentals.json react/es6-fundamentals.pdf
Needs: npm install (fonts), google-chrome, Pillow.
Spec: see react/specs/es6-fundamentals.json (slides -> blocks).
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
PHOTO = f"file://{ROOT}/assets/photo.png"
E = html.escape

NAVY, BLUE, INK, MUTED = "#0A1B4F", "#1E40E8", "#14214F", "#3A4670"
THEMES = {  # tint bg, border, text colour, solid pill colour (white text on pill passes contrast)
    "blue": ("#EEF3FF", "#CFDCFF", "#1B3FE0", "#1E40E8"),
    "green": ("#EAF7EF", "#C6E8D3", "#1B6E40", "#1F7A47"),
    "orange": ("#FFF3E2", "#F8D6A0", "#B85008", "#C2570A"),
    "purple": ("#F1EEFC", "#D8D0F6", "#5338BC", "#5B3FC4"),
    "red": ("#FDEDED", "#F5C6C6", "#B3232A", "#C0272D"),
}

ICON = {  # stroke icons, 24x24
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "bookmark": '<path d="M6 3h12v18l-6-4.5L6 21V3z"/>',
    "repost": '<path d="M17 2l4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4M21 13v2a3 3 0 0 1-3 3H3"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-6.5 8-6.5s8 2.5 8 6.5"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9L12 3z"/>',
    "code": '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "filter": '<path d="M3 4h18l-7 8v6l-4 2v-8L3 4z"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "box": '<path d="M12 3l9 4.5v9L12 21l-9-4.5v-9L12 3z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9"/>',
    "zap": '<path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 9.5"/>',
    "x": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    "layers": '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
    "copy": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M4 16V6a2 2 0 0 1 2-2h10"/>',
    "braces": '<path d="M8 4c-2 0-3 1-3 3v2c0 1.5-1 3-2 3 1 0 2 1.5 2 3v2c0 2 1 3 3 3M16 4c2 0 3 1 3 3v2c0 1.5 1 3 2 3-1 0-2 1.5-2 3v2c0 2-1 3-3 3"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "wave": '<path d="M3 12c2-6 4-6 6 0s4 6 6 0 4-6 6 0"/>',
}


def ic(name, size=30, color="currentColor", sw=2.2):
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>'


def rich(t):
    """**bold** -> blue bold; `code` -> mono chip."""
    t = E(t)
    t = re.sub(r"\*\*(.+?)\*\*", rf'<b style="color:{BLUE}">\1</b>', t)
    t = re.sub(r"`(.+?)`", r"<code style=\"font:500 0.88em 'DM Mono',monospace;background:#E3EAFF;color:#1B3FE0;padding:1px 8px;border-radius:8px\">\1</code>", t)
    return t


# ---------- code highlighting (dark block) ----------
KW = r"\b(function|return|const|let|var|import|from|export|default|if|else|new|true|false|null|async|await|try|catch|throw|class|of|in)\b"
def hl(line):
    pat = re.compile(r"(//.*$)|(\"[^\"]*\"|'[^']*'|`[^`]*`)|(</?[A-Z][\w.]*|</?[a-z][\w]*(?=[\s/>]))|(\b\d+\b)|(\b[A-Za-z_$][\w$]*(?=\())|" + KW)
    out, pos = "", 0
    for m in pat.finditer(line):
        out += E(line[pos:m.start()])
        t = E(m.group(0))
        if m.group(1): c = "#7FC79A"
        elif m.group(2): c = "#FFAE70"
        elif m.group(3): c = "#8FB5FF"
        elif m.group(4): c = "#FFAE70"
        elif m.group(5): c = "#6FE0F5"
        else: c = "#D29BFF"
        out += f'<span style="color:{c}">{t}</span>'
        pos = m.end()
    return out + E(line[pos:])


def code(lines, size=23):
    rows = "".join(f'<div style="white-space:pre">{hl(l) if l.strip() else "&nbsp;"}</div>' for l in lines)
    return (f'<div style="background:#0E1B3D;border-radius:18px;padding:16px 22px;font:500 {size}px/1.5 \'DM Mono\',monospace;color:#F1F5FF;'
            f'box-shadow:0 10px 22px rgba(10,27,79,0.22);overflow:hidden">{rows}</div>')


# ---------- illustrations (viewBox 420x340) ----------
def dots():
    return "".join(f'<circle cx="{330 + c * 16}" cy="{14 + r * 16}" r="2.2" fill="#B9C9F7"/>' for r in range(6) for c in range(5))

def badge(txt, cx=345, cy=262, r=46):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{BLUE}"/><text x="{cx}" y="{cy + 13}" text-anchor="middle" font-family="DM Mono,monospace" font-weight="500" font-size="{38 if len(txt) < 3 else 30}" fill="#fff">{txt}</text>'

def lines(x, y, rows, w=170, gap=20, cols=("#1E40E8", "#1F7A47", "#C2570A", "#5B3FC4")):
    out = ""
    for i in range(rows):
        out += f'<rect x="{x + (i % 3) * 14}" y="{y + i * gap}" width="{w - (i * 23) % 70}" height="9" rx="4.5" fill="{cols[i % 4]}" opacity="0.85"/>'
    return out

def laptop(screen, dark=False):
    bg = "#0E1B3D" if dark else "#fff"
    return (f'<circle cx="215" cy="175" r="150" fill="#E6EDFE"/>{dots()}'
            f'<rect x="70" y="52" width="280" height="190" rx="12" fill="#12296A"/><rect x="80" y="62" width="260" height="168" rx="5" fill="{bg}"/>{screen}'
            f'<rect x="38" y="242" width="344" height="16" rx="8" fill="#1B3A8A"/><rect x="160" y="242" width="100" height="7" rx="3.5" fill="#0A1B4F" opacity="0.5"/>')

def illus(kind, glyph="{ }"):
    if kind == "clipboard":
        body = ('<circle cx="215" cy="180" r="140" fill="#E6EDFE"/>' + dots() +
                '<rect x="110" y="48" width="200" height="250" rx="16" fill="#fff" stroke="#12296A" stroke-width="9"/><rect x="165" y="26" width="90" height="38" rx="12" fill="#12296A"/>'
                '<circle cx="150" cy="112" r="14" fill="#1E40E8"/><rect x="178" y="100" width="100" height="10" rx="5" fill="#9DB4F5"/><rect x="178" y="118" width="70" height="10" rx="5" fill="#C9D6FA"/>'
                + "".join(f'<circle cx="146" cy="{160 + i * 38}" r="6" fill="#1E40E8"/><rect x="166" y="{155 + i * 38}" width="{120 - i * 12}" height="10" rx="5" fill="#B7C8F8"/>' for i in range(3)) + badge(glyph, 300, 268, 52))
    elif kind == "laptop_code":
        body = laptop('<rect x="96" y="76" width="70" height="9" rx="4.5" fill="#9DB4F5"/>' + lines(96, 100, 6) + '<rect x="96" y="230" width="0" height="0"/>') + badge(glyph)
    elif kind == "laptop_dark":
        body = laptop(lines(96, 80, 7, 190, 20), dark=True) + '<circle cx="94" cy="72" r="3" fill="#FF5F57"/><circle cx="106" cy="72" r="3" fill="#FEBC2E"/><circle cx="118" cy="72" r="3" fill="#28C840"/>' + badge(glyph)
    elif kind == "laptop_list":
        rows = "".join(f'<circle cx="104" cy="{92 + i * 34}" r="8" fill="{c}"/><rect x="124" y="{87 + i * 34}" width="{150 - i * 14}" height="10" rx="5" fill="#C9D6FA"/>' for i, c in enumerate(["#1F7A47", "#1E40E8", "#C2570A", "#5B3FC4"]))
        body = laptop(rows) + badge(glyph)
    elif kind == "laptop_async":
        body = laptop('<circle cx="150" cy="130" r="34" fill="none" stroke="#C9D6FA" stroke-width="9"/><path d="M150 96a34 34 0 0 1 34 34" fill="none" stroke="#1E40E8" stroke-width="9" stroke-linecap="round"/>'
                      '<rect x="206" y="108" width="100" height="10" rx="5" fill="#9DB4F5"/><rect x="206" y="130" width="70" height="10" rx="5" fill="#C9D6FA"/><rect x="96" y="190" width="220" height="10" rx="5" fill="#C9D6FA"/>') + badge(glyph)
    else:  # flow
        body = ('<circle cx="215" cy="175" r="140" fill="#E6EDFE"/>' + dots() +
                '<rect x="40" y="120" width="130" height="100" rx="14" fill="#fff" stroke="#12296A" stroke-width="7"/><rect x="58" y="146" width="70" height="9" rx="4.5" fill="#9DB4F5"/><rect x="58" y="166" width="50" height="9" rx="4.5" fill="#C9D6FA"/>'
                '<path d="M180 170h50" stroke="#12296A" stroke-width="7" stroke-linecap="round"/><path d="M218 156l16 14-16 14" fill="none" stroke="#12296A" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
                '<circle cx="320" cy="170" r="62" fill="#1F7A47"/><path d="M292 172l20 20 40-44" fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>')
    return f'<svg viewBox="0 0 420 340" width="330" height="267" aria-hidden="true">{body}</svg>'


# ---------- building blocks ----------
def hexagon(glyph):
    return (f'<svg width="74" height="82" viewBox="0 0 74 82" aria-hidden="true"><path d="M37 3l31 17.5v41L37 79 6 61.5v-41L37 3z" fill="{BLUE}" stroke="#12296A" stroke-width="3"/>'
            f'<text x="37" y="50" text-anchor="middle" font-family="Nunito,sans-serif" font-weight="800" font-size="{26 if len(glyph) < 3 else 20}" fill="#fff">{E(glyph)}</text></svg>')

def top(tag, glyph):
    return (f'<div style="display:flex;align-items:center;height:76px"><div style="position:relative;z-index:2">{hexagon(glyph)}</div>'
            f'<div style="margin-left:-14px;padding:0 30px 0 32px;height:58px;display:flex;align-items:center;background:#EEF3FF;border:2px solid #BFD0FF;border-radius:999px;'
            f"font:700 30px/1 'Nunito',sans-serif;color:{NAVY}\">{E(tag)}</div></div>")

def headline(l1, l2, size, ill, sub):
    return (f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-top:4px;position:relative">'
            f'<div style="padding-top:8px;flex:1;min-width:0;max-width:700px;position:relative;z-index:2"><h1 style="margin:0;font:800 {size}px/1.04 \'Nunito\',sans-serif;color:{NAVY};letter-spacing:-0.01em">{E(l1)}<br><span style="color:{BLUE}">{E(l2)}</span></h1>'
            f'<div style="width:96px;height:6px;border-radius:3px;background:{BLUE};margin:16px 0 14px"></div>'
            f'<p style="margin:0;font:600 29px/1.3 \'Nunito\',sans-serif;color:{INK};max-width:700px">{rich(sub)}</p></div>'
            f'<div style="position:absolute;right:-10px;top:-6px;z-index:1">{ill}</div></div>')

def callout(b):
    return (f'<div style="display:flex;align-items:center;gap:22px;background:#EEF3FF;border:2px solid #D2DEFF;border-radius:22px;padding:20px 26px">'
            f'<div style="color:{NAVY};flex:none">{ic(b.get("icon", "bulb"), 44, NAVY, 2)}</div>'
            f"<div style=\"font:600 31px/1.3 'Nunito',sans-serif;color:{INK}\">{rich(b['text'])}</div></div>")

def heading(b):
    return f"<div style=\"font:800 36px/1.1 'Nunito',sans-serif;color:{THEMES[b.get('color', 'blue')][2]};margin-top:6px\">{E(b['text'])}</div>"

def cards(b):
    cols = b.get("cols", 4)
    items = b["items"]
    rows = [items[i:i + cols] for i in range(0, len(items), cols)]
    out = '<div style="display:flex;flex-direction:column;gap:16px;flex:1">'
    for r in rows:
        out += f'<div style="display:grid;grid-template-columns:repeat({len(r)},minmax(0,1fr));gap:16px;flex:1">'
        for it in r:
            bg, bd, fg, solid = THEMES[it["color"]]
            out += (f'<div style="background:{bg};border:2px solid {bd};border-radius:24px;padding:20px 18px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:10px;justify-content:flex-start;padding-top:26px">'
                    f'<div style="width:62px;height:62px;border-radius:18px;background:#fff;box-shadow:0 6px 14px rgba(10,27,79,0.12);display:flex;align-items:center;justify-content:center;color:{fg}">{ic(it["icon"], 34, fg, 2.2)}</div>'
                    f"<div style=\"font:800 29px/1.15 'Nunito',sans-serif;color:{fg}\">{E(it['title'])}</div>"
                    f"<div style=\"font:600 25px/1.3 'Nunito',sans-serif;color:{MUTED}\">{E(it['text'])}</div></div>")
        out += "</div>"
    return out + "</div>"

def sections(b):
    out = '<div style="display:flex;flex-direction:column;gap:14px;flex:1">'
    for s in b["items"]:
        bg, bd, fg, solid = THEMES[s["color"]]
        extra = f'<div style="margin-top:10px;font:700 25px/1.3 \'Nunito\',sans-serif;color:{fg}">{rich(s["result"])}</div>' if s.get("result") else ""
        out += (f'<div style="display:grid;grid-template-columns:250px minmax(0,1fr);gap:20px;align-items:center;background:{bg};border:2px solid {bd};border-radius:26px;padding:16px 18px;flex:1">'
                f'<div style="display:flex;flex-direction:column;gap:10px;align-items:flex-start"><span style="background:{solid};color:#fff;font:800 25px/1 \'Nunito\',sans-serif;padding:12px 16px;border-radius:12px;white-space:nowrap">{E(s["title"])}</span>'
                f"<div style=\"font:600 24px/1.28 'Nunito',sans-serif;color:{INK}\">{rich(s['text'])}</div></div>"
                f'<div>{code(s["code"], s.get("size", 23))}{extra}</div></div>')
    return out + "</div>"

def flow(b):
    parts = []
    for i, it in enumerate(b["items"]):
        bg, bd, fg, solid = THEMES[it["color"]]
        parts.append(f'<div style="flex:1;background:{bg};border:2px solid {bd};border-radius:22px;padding:16px 14px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:8px">'
                     f'<div style="color:{fg}">{ic(it["icon"], 38, fg)}</div><div style="font:800 28px/1.1 \'Nunito\',sans-serif;color:{fg}">{E(it["title"])}</div>'
                     f'<div style="font:600 24px/1.25 \'Nunito\',sans-serif;color:{MUTED}">{E(it["text"])}</div></div>')
        if i < len(b["items"]) - 1:
            sep = b["seps"][i]
            parts.append(f'<div style="flex:none;color:{NAVY};display:flex;align-items:center;font:800 26px/1 \'Nunito\',sans-serif">{ic("arrow", 38, NAVY, 2.6) if sep == "arrow" else E(sep)}</div>')
    return f'<div style="display:flex;align-items:stretch;gap:12px">{"".join(parts)}</div>'

def takeaway(b):
    chips = ""
    if b.get("chips"):
        chips = '<div style="display:flex;align-items:center;gap:10px;flex:none">' + f'<span style="color:{NAVY}">{ic("arrow", 26, NAVY, 2.6)}</span>'.join(
            f'<span style="background:#fff;border:2px solid #BFD0FF;border-radius:12px;padding:10px 16px;font:700 25px/1 \'Nunito\',sans-serif;color:{BLUE}">{E(c)}</span>' for c in b["chips"]) + "</div>"
    return (f'<div style="display:flex;align-items:center;gap:22px;background:#EEF3FF;border:2px solid #D2DEFF;border-radius:22px;padding:14px 24px">'
            f'<div style="width:56px;height:56px;border-radius:50%;background:{BLUE};display:flex;align-items:center;justify-content:center;flex:none">{ic(b.get("icon", "bulb"), 32, "#fff", 2.2)}</div>'
            f"<div style=\"font:600 27px/1.3 'Nunito',sans-serif;color:{INK};flex:1\"><b style=\"color:{BLUE}\">{E(b.get('label', 'Key Point:'))}</b> {rich(b['text'])}</div>{chips}</div>")

def profile(b):
    return (f'<div style="display:flex;align-items:center;gap:26px;background:#fff;border:2px solid #D2DEFF;border-radius:26px;padding:14px 24px;box-shadow:0 10px 24px rgba(10,27,79,0.10)">'
            f'<div style="width:112px;height:112px;border-radius:50%;overflow:hidden;flex:none;border:4px solid {BLUE};box-sizing:border-box;background:#000"><img src="{PHOTO}" alt="" style="display:block;width:168px;height:auto;max-width:none;margin-left:-36px;margin-top:-3px"></div>'
            f"<div style=\"display:flex;flex-direction:column;gap:6px\"><span style=\"font:800 36px/1.1 'Nunito',sans-serif;color:{NAVY}\">Ali Husnain Shah</span>"
            f"<span style=\"font:700 26px/1.25 'Nunito',sans-serif;color:{MUTED}\">Senior Full Stack .NET Developer | AI Automation</span>"
            f"<span style=\"font:800 28px/1.2 'Nunito',sans-serif;color:{BLUE}\">LinkedIn @ahshah322 &nbsp;·&nbsp; GitHub @ahshah322</span></div></div>")

def bar():
    def item(icn, t, s):
        return (f'<div style="display:flex;align-items:center;gap:18px;flex:1;justify-content:center"><div style="width:78px;height:78px;border-radius:50%;background:{BLUE};display:flex;align-items:center;justify-content:center;flex:none">{ic(icn, 38, "#fff", 2.3)}</div>'
                f"<div><div style=\"font:800 29px/1.1 'Nunito',sans-serif;color:#fff\">{t}</div><div style=\"font:600 25px/1.2 'Nunito',sans-serif;color:#C9D6FF;margin-top:4px\">{s}</div></div></div>")
    sep = '<div style="width:2px;height:80px;background:rgba(255,255,255,0.22);flex:none"></div>'
    return (f'<div style="height:140px;background:{NAVY};display:flex;align-items:center;padding:0 24px;flex:none">'
            + item("bookmark", "Save this post", "for later") + sep + item("repost", "Repost to help", "your network") + sep + item("user", "Follow for more", "quality content") + "</div>")

BLOCKS = {"callout": callout, "heading": heading, "cards": cards, "sections": sections, "flow": flow, "takeaway": takeaway, "profile": profile}

def slide(spec, s):
    ill = illus(s.get("illus", "laptop_code"), s.get("glyph", spec.get("glyph", "{ }")))
    main = "".join(BLOCKS[b["type"]](b) for b in s["blocks"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS} body{{margin:0}}</style></head><body>
<div style="width:1080px;height:1350px;display:flex;flex-direction:column;background:linear-gradient(180deg,#FFFFFF 0%,#F6F9FF 100%);font-family:'Nunito',sans-serif;overflow:hidden;position:relative">
<div style="flex:1;min-height:0;padding:40px 60px 20px;display:flex;flex-direction:column;gap:16px">
{top(spec['tag'], spec['hex'])}
{headline(s['title'][0], s['title'][1], s.get('hsize', 88), ill, s['sub'])}
{main}
</div>{bar()}</div></body></html>"""

def shot(h, png):
    tmp = png.replace(".png", ".html")
    open(tmp, "w").write(h)
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--window-size=1080,1350", f"--screenshot={png}", f"file://{tmp}"], capture_output=True, timeout=180)

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    out_pdf = sys.argv[2]
    build = os.path.join(os.path.dirname(os.path.abspath(out_pdf)), "build-" + os.path.basename(out_pdf)[:-4])
    os.makedirs(build, exist_ok=True)
    pngs = []
    for i, s in enumerate(spec["slides"], 1):
        png = f"{build}/slide{i}.png"
        shot(slide(spec, s), png)
        pngs.append(png)
    ims = [Image.open(p).convert("RGB") for p in pngs]
    ims[0].save(out_pdf, save_all=True, append_images=ims[1:], resolution=200, quality=95, subsampling=0)
    print("wrote", out_pdf, len(ims), "pages")
