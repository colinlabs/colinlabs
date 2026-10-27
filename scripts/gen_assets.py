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

SKILLS = [
    ("kubernetes", "kubernetes", "platforms · day-2 ops", "Running"),
    ("ci-cd", "drone", "pipeline-as-code", "Running"),
    ("observability", "prometheus", "metrics · logs · alerts", "Running"),
    ("service-mesh", "consul", "discovery · config", "Running"),
    ("ai-agents", "claude", "LLM · MCP · AIOps", "Building"),
    ("go-tooling", "go", "operators · CLIs", "Building"),
]
STATUS = {"Running": "#3fb950", "Building": "#e3b341"}


def hero():
    w, h = 880, 320
    px, py, pw = 468, 40, 372
    row_h = 31
    ph = 48 + row_h * len(SKILLS) + 14
    running = sum(1 for s in SKILLS if s[3] == "Running")

    drift_a = "" if STATIC else (
        '<animate attributeName="cx" values="18%;30%;18%" dur="14s" repeatCount="indefinite"/>'
        '<animate attributeName="cy" values="10%;30%;10%" dur="14s" repeatCount="indefinite"/>')
    drift_b = "" if STATIC else (
        '<animate attributeName="cx" values="88%;72%;88%" dur="17s" repeatCount="indefinite"/>'
        '<animate attributeName="cy" values="95%;70%;95%" dur="17s" repeatCount="indefinite"/>')

    rows = []
    for i, (name, slug, focus, status) in enumerate(SKILLS):
        y = py + 48 + i * row_h
        color = STATUS[status]
        chip_w = 76
        chip_x = px + pw - 16 - chip_w
        rows.append(
            enter(0.75 + i * 0.1, dx=14, dy=0, dur=0.6)
            + (f'<line x1="{px + 16}" y1="{y}" x2="{px + pw - 16}" y2="{y}" stroke="#21262d"/>' if i else "")
            + draw_icon(slug, px + 18, y + 8, 15)
            + f'<text x="{px + 44}" y="{y + 20}" font-family="{MONO}" font-size="12.5" fill="#e6edf3">{name}</text>'
            + f'<text x="{px + 160}" y="{y + 20}" font-family="{SANS}" font-size="11.5" fill="#8b949e">{escape(focus)}</text>'
            + f'<rect x="{chip_x}" y="{y + 7}" width="{chip_w}" height="18" rx="9" fill="{color}" fill-opacity="0.14" stroke="{color}" stroke-opacity="0.35"/>'
            + pulse(chip_x + 11, y + 16, color, 1.4 + i * 0.37)
            + f'<circle cx="{chip_x + 11}" cy="{y + 16}" r="3" fill="{color}"/>'
            + f'<text x="{chip_x + 20}" y="{y + 20}" font-family="{SANS}" font-size="11" font-weight="600" fill="{color}">{status}</text>'
            + "</g>"
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">
<title id="t">Colin Lee — DevOps expert from China. Kubernetes, CI/CD, observability, service mesh, AI agents and Go tooling.</title>
<defs>
<clipPath id="card"><rect width="{w}" height="{h}" rx="18"/></clipPath>
<radialGradient id="glowA" cx="18%" cy="10%" r="55%">{drift_a}<stop offset="0" stop-color="#1f6feb" stop-opacity="0.42"/><stop offset="1" stop-color="#1f6feb" stop-opacity="0"/></radialGradient>
<radialGradient id="glowB" cx="88%" cy="95%" r="55%">{drift_b}<stop offset="0" stop-color="#a371f7" stop-opacity="0.34"/><stop offset="1" stop-color="#a371f7" stop-opacity="0"/></radialGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#79c0ff" stop-opacity="0.55"/><stop offset="0.5" stop-color="#30363d" stop-opacity="0.6"/><stop offset="1" stop-color="#d2a8ff" stop-opacity="0.55"/></linearGradient>
<linearGradient id="title" x1="44" y1="0" x2="330" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#79c0ff"/><stop offset="1" stop-color="#d2a8ff"/></linearGradient>
<linearGradient id="name" x1="0" y1="140" x2="0" y2="190" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#c9d1d9"/></linearGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.9" fill="#ffffff" fill-opacity="0.07"/></pattern>
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

{enter(0.45, dx=0, dy=16, dur=0.8)}
<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="14" fill="#0d1117" fill-opacity="0.82" stroke="#30363d"/>
<circle cx="{px + 20}" cy="{py + 22}" r="4" fill="#ff5f56"/><circle cx="{px + 34}" cy="{py + 22}" r="4" fill="#ffbd2e"/><circle cx="{px + 48}" cy="{py + 22}" r="4" fill="#27c93f"/>
<text x="{px + 66}" y="{py + 26}" font-family="{MONO}" font-size="11.5" fill="#8b949e">kubectl get skills -n colin</text>
<text x="{px + pw - 16}" y="{py + 26}" text-anchor="end" font-family="{SANS}" font-size="11" font-weight="600" fill="#3fb950">{running}/{len(SKILLS)} ready</text>
<line x1="{px}" y1="{py + 40}" x2="{px + pw}" y2="{py + 40}" stroke="#30363d"/>
</g>
{chr(10).join(rows)}
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
