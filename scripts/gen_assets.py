"""Generate the profile README SVGs: assets/hero.svg and assets/stack-{light,dark}.svg.

Icons come from https://simpleicons.org (CC0). Run: python3 scripts/gen_assets.py [--static]
--static drops all animation, for previewing the final frame with rsvg-convert.
"""

import re
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

STATIC = "--static" in sys.argv
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

SANS = "ui-sans-serif, -apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
EASE = 'calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1"'

_icon_cache = {}


def icon(slug):
    if slug not in _icon_cache:
        # The CDN answers 403 to urllib's default User-Agent.
        req = urllib.request.Request(f"https://cdn.simpleicons.org/{slug}", headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req) as resp:
            svg = resp.read().decode()
        path = re.search(r' d="([^"]+)"', svg).group(1)
        color = re.search(r'fill="(#[0-9a-fA-F]{6})"', svg).group(1)
        _icon_cache[slug] = (path, color)
    return _icon_cache[slug]


def luminance(hex_color):
    def channel(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(hex_color[i:i + 2]) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def icon_color(slug, dark):
    color = icon(slug)[1]
    if dark and luminance(color) < 0.1:
        return "#e6edf3"
    if not dark and luminance(color) > 0.6:
        return "#b08800"
    return color


def draw_icon(slug, x, y, size, dark=True):
    path = icon(slug)[0]
    return (f'<g transform="translate({x} {y}) scale({size / 24:.4f})">'
            f'<path d="{path}" fill="{icon_color(slug, dark)}"/></g>')


def enter(begin, dx=0, dy=12, dur=0.7):
    """Opening tag of a group that fades and slides into place."""
    if STATIC:
        return "<g>"
    return (f'<g opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="{dur}s" fill="freeze" {EASE}/>'
            f'<animateTransform attributeName="transform" type="translate" from="{dx} {dy}" to="0 0" '
            f'begin="{begin:.2f}s" dur="{dur}s" fill="freeze" {EASE}/>')


def pulse(cx, cy, color, begin):
    if STATIC:
        return ""
    return (f'<circle cx="{cx}" cy="{cy}" r="3" fill="none" stroke="{color}" stroke-width="1.5">'
            f'<animate attributeName="r" values="3;9" dur="2.2s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.7;0" dur="2.2s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
            f'</circle>')


# ---------------------------------------------------------------- hero

# Stages around the DevOps loop, in flow order: left lobe (dev) top → outer → bottom,
# then right lobe (ops) top → outer → bottom. Label side follows from the position.
STAGES = [
    ("Code", "git"), ("Build", "drone"), ("Package", "docker"),
    ("Deploy", "kubernetes"), ("Observe", "grafana"), ("Operate", "alibabacloud"),
]
LOOP = dict(cx=636,cy=165, w=130, a=36, d=92)


def loop_segments(cx, cy, w, a, d):
    """Figure-eight as four cubic Béziers: left lobe first, crossing smoothly at the center."""
    return [
        ((cx, cy), (cx - a, cy - d), (cx - w, cy - d), (cx - w, cy)),
        ((cx - w, cy), (cx - w, cy + d), (cx - a, cy + d), (cx, cy)),
        ((cx, cy), (cx + a, cy - d), (cx + w, cy - d), (cx + w, cy)),
        ((cx + w, cy), (cx + w, cy + d), (cx + a, cy + d), (cx, cy)),
    ]


def bezier(seg, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = seg
    u = 1 - t
    return (u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3,
            u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3)


def loop_path():
    segs = loop_segments(**LOOP)
    d = f"M{segs[0][0][0]} {segs[0][0][1]}" + "".join(
        f" C{s[1][0]} {s[1][1]} {s[2][0]} {s[2][1]} {s[3][0]} {s[3][1]}" for s in segs) + " Z"
    length = 0.0
    for s in segs:
        pts = [bezier(s, i / 200) for i in range(201)]
        length += sum(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 for (x1, y1), (x2, y2) in zip(pts, pts[1:]))
    # Stage anchors: lobe top (t=.5 of the rising segment), outer extreme, lobe bottom.
    anchors = []
    for rising, falling in ((segs[0], segs[1]), (segs[2], segs[3])):
        anchors += [(bezier(rising, 0.5), "top"), (rising[3], "side"), (bezier(falling, 0.5), "bottom")]
    return d, length, anchors


def stage_label(name, slug, x, y, where, begin):
    size, gap = 14, 6
    tw = size + gap + text_width(name, 12.5)
    if where == "top":
        lx, ly = x - tw / 2, y - 30
    elif where == "bottom":
        lx, ly = x - tw / 2, y + 16
    elif x < LOOP["cx"]:
        lx, ly = x - 14 - tw, y - 7
    else:
        lx, ly = x + 14, y - 7
    return (enter(begin, dy=6, dur=0.5)
            + draw_icon(slug, lx, ly, size)
            + f'<text x="{lx + size + gap:.1f}" y="{ly + 11.5:.1f}" font-family="{SANS}" font-size="12.5" '
              f'font-weight="600" fill="#e6edf3">{name}</text></g>')


def hero():
    w, h = 880, 320
    cx, cy, lw = LOOP["cx"], LOOP["cy"], LOOP["w"]
    d, length, anchors = loop_path()
    comet = 70
    lap = 5.5

    drift_a = "" if STATIC else (
        '<animate attributeName="cx" values="18%;30%;18%" dur="14s" repeatCount="indefinite"/>'
        '<animate attributeName="cy" values="10%;30%;10%" dur="14s" repeatCount="indefinite"/>')
    drift_b = "" if STATIC else (
        '<animate attributeName="cx" values="88%;72%;88%" dur="17s" repeatCount="indefinite"/>'
        '<animate attributeName="cy" values="95%;70%;95%" dur="17s" repeatCount="indefinite"/>')

    line = f'<path d="{d}" fill="none" stroke="url(#loopStroke)" stroke-width="2" stroke-opacity="0.7"'
    if STATIC:
        line += "/>"
        comet_anim = head_anim = ""
        comet_attrs = 'opacity="0"'
    else:
        line += (f' stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}">'
                 f'<animate attributeName="stroke-dashoffset" from="{length:.0f}" to="0" begin="0.5s" dur="1.4s" '
                 f'fill="freeze" {EASE}/></path>')
        comet_attrs = f'opacity="0" stroke-dasharray="{comet} {length - comet:.0f}"'
        # Dash spans [s - comet, s) while the head dot sits at s, so the dot leads the tail.
        comet_anim = (f'<set attributeName="opacity" to="1" begin="1.9s" fill="freeze"/>'
                      f'<animate attributeName="stroke-dashoffset" values="{length + comet:.0f};{comet}" '
                      f'begin="1.9s" dur="{lap}s" repeatCount="indefinite"/>')
        head_anim = (f'<set attributeName="opacity" to="1" begin="1.9s" fill="freeze"/>'
                     f'<animateMotion begin="1.9s" dur="{lap}s" repeatCount="indefinite"><mpath xlink:href="#loop"/></animateMotion>')

    markers = []
    labels = []
    for i, (((x, y), where), (name, slug)) in enumerate(zip(anchors, STAGES)):
        color = "#79c0ff" if x < cx else "#d2a8ff"
        markers.append(pulse(x, y, color, 2.0 + i * 0.6)
                       + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#0b0f17" stroke="{color}" stroke-width="1.5"/>'
                       + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" fill="{color}"/>')
        labels.append(stage_label(name, slug, x, y, where, 0.9 + i * 0.1))

    lobe_dx = lw * 0.56
    ai_glow = "" if STATIC else (
        '<animate attributeName="r" values="26;34;26" dur="3s" repeatCount="indefinite"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">
<title id="t">Colin Lee — DevOps expert from China. A DevOps loop: code, build, package, deploy, observe, operate, with AI at the center.</title>
<defs>
<clipPath id="card"><rect width="{w}" height="{h}" rx="18"/></clipPath>
<radialGradient id="glowA" cx="18%" cy="10%" r="55%">{drift_a}<stop offset="0" stop-color="#1f6feb" stop-opacity="0.42"/><stop offset="1" stop-color="#1f6feb" stop-opacity="0"/></radialGradient>
<radialGradient id="glowB" cx="88%" cy="95%" r="55%">{drift_b}<stop offset="0" stop-color="#a371f7" stop-opacity="0.34"/><stop offset="1" stop-color="#a371f7" stop-opacity="0"/></radialGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#79c0ff" stop-opacity="0.55"/><stop offset="0.5" stop-color="#30363d" stop-opacity="0.6"/><stop offset="1" stop-color="#d2a8ff" stop-opacity="0.55"/></linearGradient>
<linearGradient id="title" x1="44" y1="0" x2="330" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#79c0ff"/><stop offset="1" stop-color="#d2a8ff"/></linearGradient>
<linearGradient id="name" x1="0" y1="140" x2="0" y2="190" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#c9d1d9"/></linearGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.9" fill="#ffffff" fill-opacity="0.07"/></pattern>
<linearGradient id="loopStroke" x1="{cx - lw}" y1="0" x2="{cx + lw}" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#79c0ff"/><stop offset="1" stop-color="#d2a8ff"/></linearGradient>
<radialGradient id="aiGlow"><stop offset="0" stop-color="#d97757" stop-opacity="0.45"/><stop offset="1" stop-color="#d97757" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<path id="loop" d="{d}"/>
</defs>
<g clip-path="url(#card)">
<rect width="{w}" height="{h}" fill="#0b0f17"/>
<rect width="{w}" height="{h}" fill="url(#dots)"/>
<rect width="{w}" height="{h}" fill="url(#glowA)"/>
<rect width="{w}" height="{h}" fill="url(#glowB)"/>
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="17.5" fill="none" stroke="url(#edge)"/>

{enter(0.1)}
<rect x="44" y="58" width="226" height="26" rx="13" fill="#79c0ff" fill-opacity="0.1" stroke="#79c0ff" stroke-opacity="0.3"/>
{pulse(60, 71, "#3fb950", 0.8)}<circle cx="60" cy="71" r="3" fill="#3fb950"/>
<text x="72" y="75.5" font-family="{SANS}" font-size="11" font-weight="600" letter-spacing="1.6" fill="#79c0ff">DEVOPS · CLOUD NATIVE · AI</text>
</g>
{enter(0.22)}<text x="44" y="126" font-family="{SANS}" font-size="18" fill="#8b949e">Hi, I'm</text></g>
{enter(0.32)}<text x="42" y="182" font-family="{SANS}" font-size="54" font-weight="800" letter-spacing="-1.5" fill="url(#name)">Colin Lee</text></g>
{enter(0.44)}<text x="44" y="220" font-family="{SANS}" font-size="21" font-weight="600" fill="url(#title)">DevOps expert from China</text></g>
{enter(0.56)}<text x="44" y="258" font-family="{SANS}" font-size="14" fill="#8b949e">Automate the boring parts. Make deploys boring.</text></g>

{enter(0.3, dy=0, dur=1.0)}
<path d="{d}" fill="none" stroke="url(#loopStroke)" stroke-width="14" stroke-opacity="0.08" stroke-linejoin="round"/>
<text x="{cx - lobe_dx}" y="{cy + 4.5}" text-anchor="middle" font-family="{SANS}" font-size="12" font-weight="700" letter-spacing="3" fill="#79c0ff" fill-opacity="0.55">DEV</text>
<text x="{cx + lobe_dx}" y="{cy + 4.5}" text-anchor="middle" font-family="{SANS}" font-size="12" font-weight="700" letter-spacing="3" fill="#d2a8ff" fill-opacity="0.55">OPS</text>
</g>
{line}
<path d="{d}" fill="none" stroke="url(#loopStroke)" stroke-width="3" stroke-linecap="round" filter="url(#glow)" {comet_attrs}>{comet_anim}</path>
<circle r="3.5" fill="#ffffff" filter="url(#glow)" opacity="0">{head_anim}</circle>
{chr(10).join(markers)}
{chr(10).join(labels)}
{enter(1.5, dy=0, dur=0.6)}
<circle cx="{cx}" cy="{cy}" r="28" fill="url(#aiGlow)">{ai_glow}</circle>
<rect x="{cx - 28}" y="{cy - 13}" width="56" height="26" rx="13" fill="#0d1117" stroke="#d97757" stroke-opacity="0.6"/>
{draw_icon("claude", cx - 19, cy - 6.5, 13)}
<text x="{cx + 1}" y="{cy + 4.5}" font-family="{SANS}" font-size="12" font-weight="700" fill="#f0f6fc">AI</text>
</g>
</svg>
'''


# ---------------------------------------------------------------- stack

STACK = [
    ("Languages", [("go", "Go"), ("python", "Python"), ("gnubash", "Bash"), ("yaml", "YAML"), ("git", "Git")]),
    ("Cloud native", [("docker", "Docker"), ("kubernetes", "Kubernetes"), ("cncf", "CNCF"), ("consul", "Consul"),
                      ("drone", "Drone"), ("alibabacloud", "Alibaba Cloud")]),
    ("Observability", [("prometheus", "Prometheus"), ("grafana", "Grafana"), ("elastic", "Elastic"), ("fluentd", "Fluentd")]),
    ("AI", [("claude", "Claude"), ("modelcontextprotocol", "MCP"), ("ollama", "Ollama"),
            ("huggingface", "Hugging Face"), ("langchain", "LangChain")]),
]


def text_width(label, size=13):
    """Rough advance width for a 500-weight system sans; there is no font metrics at render time."""
    em = sum(0.68 if c.isupper() else 0.28 if c == " " else 0.55 for c in label)
    return em * size


def stack(dark):
    t = {
        "tile": "#161b22" if dark else "#f6f8fa",
        "border": "#30363d" if dark else "#d0d7de",
        "text": "#e6edf3" if dark else "#1f2328",
        "label": "#8b949e" if dark else "#656d76",
        "accent": "#d2a8ff" if dark else "#8250df",
    }
    w = 880
    label_w = 150
    tile_h, gap, row_gap = 40, 8, 14
    out = []
    y = 4
    n = 0
    for group, items in STACK:
        is_ai = group == "AI"
        out.append(
            f'<text x="4" y="{y + 25}" font-family="{SANS}" font-size="11" font-weight="700" letter-spacing="1.4" '
            f'fill="{t["accent"] if is_ai else t["label"]}">{escape(group.upper())}</text>')
        x = label_w
        for slug, label in items:
            tw = 43 + text_width(label) + 16
            border = t["accent"] if is_ai else t["border"]
            out.append(
                enter(0.05 + n * 0.04, dy=8, dur=0.5)
                + f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{tw:.0f}" height="{tile_h}" rx="10" fill="{t["tile"]}" '
                  f'stroke="{border}" stroke-opacity="{0.55 if is_ai else 1}"/>'
                + draw_icon(slug, x + 16, y + 11, 18, dark)
                + f'<text x="{x + 43}" y="{y + 25}" font-family="{SANS}" font-size="13" font-weight="500" fill="{t["text"]}">{escape(label)}</text>'
                + "</g>")
            x += tw + gap
            n += 1
        y += tile_h + row_gap
    h = y - row_gap + 6
    names = ", ".join(label for _, items in STACK for _, label in items)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">'
            f'<title id="t">Tech stack: {escape(names)}</title>\n' + "\n".join(out) + "\n</svg>\n")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    (OUT / "hero.svg").write_text(hero())
    (OUT / "stack-dark.svg").write_text(stack(dark=True))
    (OUT / "stack-light.svg").write_text(stack(dark=False))
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.svg"))))
