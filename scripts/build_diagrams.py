#!/usr/bin/env python3
"""Generate light-themed concept diagrams for the landing notebook.

Writes one SVG + one PNG per diagram into notebooks/unsloth/assets/.
PNG is the version referenced by the notebook because it renders reliably in
both JupyterLab and GitHub's notebook viewer; the SVG is kept as the editable
source. Pure-Python (cairosvg) rasterization, no system tools required.

Style: light background, rounded cards, a small AMD-red / slate accent palette,
sans-serif. No em dashes anywhere (repo style rule).
"""
import os

import cairosvg

ASSETS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "notebooks",
    "unsloth",
    "assets",
)
os.makedirs(ASSETS, exist_ok=True)

# Palette
BG = "#ffffff"
INK = "#1e293b"        # slate-800 text
MUTED = "#64748b"      # slate-500 subtext
CARD = "#f8fafc"       # slate-50 card fill
BORDER = "#cbd5e1"     # slate-300 card stroke
ACCENT = "#ed1c24"     # AMD red
ACCENT_SOFT = "#fde8e8"
BLUE = "#2563eb"
BLUE_SOFT = "#e0ecff"
GREEN = "#059669"
GREEN_SOFT = "#d1fae5"
VIOLET = "#7c3aed"
VIOLET_SOFT = "#ede9fe"
AMBER = "#d97706"
AMBER_SOFT = "#fef3c7"

FONT = ("font-family='Segoe UI, Helvetica, Arial, sans-serif'")


def header_defs():
    """Shared SVG defs: a soft drop shadow and an arrowhead marker."""
    return (
        "<defs>"
        "<filter id='sh' x='-20%' y='-20%' width='140%' height='140%'>"
        "<feDropShadow dx='0' dy='1.5' stdDeviation='2' flood-color='#0f172a' flood-opacity='0.12'/>"
        "</filter>"
        f"<marker id='arrow' markerWidth='10' markerHeight='10' refX='7' refY='3' orient='auto' markerUnits='strokeWidth'>"
        f"<path d='M0,0 L7,3 L0,6 Z' fill='{MUTED}'/>"
        "</marker>"
        f"<marker id='arrowr' markerWidth='10' markerHeight='10' refX='7' refY='3' orient='auto' markerUnits='strokeWidth'>"
        f"<path d='M0,0 L7,3 L0,6 Z' fill='{ACCENT}'/>"
        "</marker>"
        "</defs>"
    )


def card(x, y, w, h, fill=CARD, stroke=BORDER, rx=12, sw=1.5):
    return (
        f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{rx}' "
        f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}' filter='url(#sh)'/>"
    )


def text(x, y, s, size: float = 15, fill=INK, weight="400", anchor="middle"):
    return (
        f"<text x='{x}' y='{y}' font-size='{size}' fill='{fill}' "
        f"font-weight='{weight}' text-anchor='{anchor}' {FONT}>{s}</text>"
    )


def svg(w, h, body):
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
        f"viewBox='0 0 {w} {h}'>"
        f"<rect width='{w}' height='{h}' fill='{BG}'/>"
        f"{header_defs()}{body}</svg>"
    )


def save(name, markup):
    svg_path = os.path.join(ASSETS, name + ".svg")
    png_path = os.path.join(ASSETS, name + ".png")
    with open(svg_path, "w") as f:
        f.write(markup)
    # Scale=2 for crisp rendering on high-DPI displays.
    cairosvg.svg2png(bytestring=markup.encode("utf-8"), write_to=png_path, scale=2)
    print("wrote", os.path.basename(svg_path), "and", os.path.basename(png_path))


# ------------------------------------------------------------------ 1. overview
def diagram_overview():
    W, H = 860, 260
    b = []
    b.append(text(W / 2, 36, "What fine-tuning does", 20, INK, "700"))
    # three cards + two arrows
    cw, ch, cy = 220, 130, 74
    x1, x2, x3 = 24, 320, 616
    # base model
    b.append(card(x1, cy, cw, ch, BLUE_SOFT, BLUE))
    b.append(text(x1 + cw / 2, cy + 40, "Pre-trained", 17, BLUE, "700"))
    b.append(text(x1 + cw / 2, cy + 64, "base model", 17, BLUE, "700"))
    b.append(text(x1 + cw / 2, cy + 96, "a generalist from", 13, MUTED))
    b.append(text(x1 + cw / 2, cy + 114, "the HF Hub", 13, MUTED))
    # your data (accent)
    b.append(card(x2, cy, cw, ch, ACCENT_SOFT, ACCENT))
    b.append(text(x2 + cw / 2, cy + 40, "+ your data", 17, ACCENT, "700"))
    b.append(text(x2 + cw / 2, cy + 70, "a few hundred to", 13, MUTED))
    b.append(text(x2 + cw / 2, cy + 88, "a few thousand", 13, MUTED))
    b.append(text(x2 + cw / 2, cy + 106, "clean examples", 13, MUTED))
    # fine-tuned model
    b.append(card(x3, cy, cw, ch, GREEN_SOFT, GREEN))
    b.append(text(x3 + cw / 2, cy + 40, "Fine-tuned", 17, GREEN, "700"))
    b.append(text(x3 + cw / 2, cy + 64, "model", 17, GREEN, "700"))
    b.append(text(x3 + cw / 2, cy + 96, "adapted to your", 13, MUTED))
    b.append(text(x3 + cw / 2, cy + 114, "task, tone, format", 13, MUTED))
    # arrows
    ay = cy + ch / 2
    b.append(f"<line x1='{x1+cw+10}' y1='{ay}' x2='{x2-12}' y2='{ay}' stroke='{MUTED}' stroke-width='2.5' marker-end='url(#arrow)'/>")
    b.append(f"<line x1='{x2+cw+10}' y1='{ay}' x2='{x3-12}' y2='{ay}' stroke='{MUTED}' stroke-width='2.5' marker-end='url(#arrow)'/>")
    b.append(text(W / 2, H - 14, "Same skill, now specialized. Cheaper and more reliable than a giant prompt.", 13, MUTED))
    save("01-finetuning-overview", svg(W, H, "".join(b)))


# ------------------------------------------------------------------ 2. SFT vs GRPO
def diagram_families():
    W, H = 860, 340
    b = []
    b.append(text(W / 2, 34, "Two families of fine-tuning", 20, INK, "700"))
    cw, ch, cy = 388, 250, 60
    x1, x2 = 24, 448
    # SFT
    b.append(card(x1, cy, cw, ch, BLUE_SOFT, BLUE))
    b.append(text(x1 + cw / 2, cy + 34, "1. Supervised Fine-Tuning (SFT)", 17, BLUE, "700"))
    b.append(text(x1 + cw / 2, cy + 58, "Show the model the right answers", 13, MUTED))
    # mini rows
    ry = cy + 86
    for label, val in [("instruction", "\"Translate to French\""), ("input", "\"Good morning\""), ("output", "\"Bonjour\"")]:
        b.append(f"<rect x='{x1+28}' y='{ry-16}' width='{cw-56}' height='26' rx='6' fill='#ffffff' stroke='{BORDER}' stroke-width='1'/>")
        b.append(text(x1 + 44, ry + 2, label, 12, BLUE, "700", "start"))
        b.append(text(x1 + cw - 44, ry + 2, val, 12, INK, "400", "end"))
        ry += 34
    b.append(text(x1 + cw / 2, cy + ch - 40, "Model learns to imitate the gold output.", 12, MUTED))
    b.append(text(x1 + cw / 2, cy + ch - 20, "The workhorse. Start here.", 13, BLUE, "700"))
    # GRPO
    b.append(card(x2, cy, cw, ch, VIOLET_SOFT, VIOLET))
    b.append(text(x2 + cw / 2, cy + 34, "2. GRPO (reinforcement)", 17, VIOLET, "700"))
    b.append(text(x2 + cw / 2, cy + 58, "Score answers, reward the best", 13, MUTED))
    # prompt -> N candidates -> reward
    px = x2 + 28
    b.append(f"<rect x='{px}' y='{cy+82}' width='86' height='30' rx='6' fill='#ffffff' stroke='{BORDER}'/>")
    b.append(text(px + 43, cy + 101, "prompt", 12, INK))
    for i, yy in enumerate([cy + 78, cy + 108, cy + 138]):
        b.append(f"<rect x='{px+140}' y='{yy}' width='88' height='24' rx='6' fill='#ffffff' stroke='{BORDER}'/>")
        b.append(text(px + 184, yy + 16, f"answer {i+1}", 11, MUTED))
        b.append(f"<line x1='{px+86}' y1='{cy+97}' x2='{px+138}' y2='{yy+12}' stroke='{MUTED}' stroke-width='1.5' marker-end='url(#arrow)'/>")
    b.append(f"<rect x='{px+250}' y='{cy+96}' width='74' height='30' rx='6' fill='{VIOLET_SOFT}' stroke='{VIOLET}'/>")
    b.append(text(px + 287, cy + 115, "reward", 12, VIOLET, "700"))
    for yy in [cy + 78, cy + 108, cy + 138]:
        b.append(f"<line x1='{px+228}' y1='{yy+12}' x2='{px+248}' y2='{cy+111}' stroke='{MUTED}' stroke-width='1.2' marker-end='url(#arrow)'/>")
    b.append(text(x2 + cw / 2, cy + ch - 40, "Push the model toward higher reward.", 12, MUTED))
    b.append(text(x2 + cw / 2, cy + ch - 20, "Great for reasoning. Use after SFT.", 13, VIOLET, "700"))
    save("02-sft-vs-grpo", svg(W, H, "".join(b)))


# ------------------------------------------------------------------ 3. LoRA/QLoRA memory
def diagram_memory():
    W, H = 860, 330
    b = []
    b.append(text(W / 2, 34, "Full vs LoRA vs QLoRA: the memory trick", 20, INK, "700"))
    cw, ch, cy = 260, 232, 62
    xs = [24, 300, 576]
    titles = ["Full fine-tune", "LoRA", "QLoRA"]
    accents = [(MUTED, "#eef2f6"), (BLUE, BLUE_SOFT), (GREEN, GREEN_SOFT)]
    subs = ["Update every weight", "Freeze base, train tiny adapters", "4-bit base + LoRA adapters"]
    for i in range(3):
        x = xs[i]
        acc, soft = accents[i]
        b.append(card(x, cy, cw, ch, soft, acc))
        b.append(text(x + cw / 2, cy + 32, titles[i], 17, acc, "700"))
        b.append(text(x + cw / 2, cy + 54, subs[i], 11.5, MUTED))
        # weight block visual
        bx, by, bw = x + 40, cy + 76, cw - 80
        if i == 0:
            b.append(f"<rect x='{bx}' y='{by}' width='{bw}' height='90' rx='8' fill='{ACCENT_SOFT}' stroke='{ACCENT}' stroke-width='1.5'/>")
            b.append(text(x + cw / 2, by + 42, "ALL weights", 13, ACCENT, "700"))
            b.append(text(x + cw / 2, by + 62, "trainable", 12, ACCENT))
            b.append(text(x + cw / 2, cy + ch - 42, "Memory: very high", 12, INK, "700"))
            b.append(text(x + cw / 2, cy + ch - 22, "Needs big GPUs", 11.5, MUTED))
        elif i == 1:
            b.append(f"<rect x='{bx}' y='{by}' width='{bw}' height='90' rx='8' fill='#eef2f6' stroke='{BORDER}' stroke-width='1.5'/>")
            b.append(text(x + cw / 2, by + 34, "base weights", 12, MUTED))
            b.append(text(x + cw / 2, by + 52, "FROZEN", 12, MUTED, "700"))
            b.append(f"<rect x='{bx+bw-58}' y='{by+58}' width='46' height='24' rx='5' fill='{BLUE_SOFT}' stroke='{BLUE}'/>")
            b.append(text(bx + bw - 35, by + 74, "LoRA", 10.5, BLUE, "700"))
            b.append(text(x + cw / 2, cy + ch - 42, "Memory: medium", 12, INK, "700"))
            b.append(text(x + cw / 2, cy + ch - 22, "~1 to 2% trainable", 11.5, MUTED))
        else:
            b.append(f"<rect x='{bx}' y='{by}' width='{bw}' height='90' rx='8' fill='#eef2f6' stroke='{BORDER}' stroke-width='1.5' stroke-dasharray='4 3'/>")
            b.append(text(x + cw / 2, by + 34, "base weights", 12, MUTED))
            b.append(text(x + cw / 2, by + 52, "4-bit + FROZEN", 11.5, GREEN, "700"))
            b.append(f"<rect x='{bx+bw-58}' y='{by+58}' width='46' height='24' rx='5' fill='{GREEN_SOFT}' stroke='{GREEN}'/>")
            b.append(text(bx + bw - 35, by + 74, "LoRA", 10.5, GREEN, "700"))
            b.append(text(x + cw / 2, cy + ch - 42, "Memory: low", 12, INK, "700"))
            b.append(text(x + cw / 2, cy + ch - 22, "Single-GPU friendly", 11.5, MUTED))
    b.append(text(W / 2, H - 12, "Qwen3-4B QLoRA on a Radeon Pro W7900 used only ~5.6 GB of VRAM.", 13, ACCENT, "700"))
    save("03-full-lora-qlora", svg(W, H, "".join(b)))


# ------------------------------------------------------------------ 4. Studio loop
def diagram_loop():
    W, H = 860, 240
    b = []
    b.append(text(W / 2, 34, "The fine-tuning loop in Unsloth Studio", 20, INK, "700"))
    steps = [
        ("1", "Pick model", "start small"),
        ("2", "Pick data", "HF or upload"),
        ("3", "SFT / QLoRA", "set a few knobs"),
        ("4", "Train", "watch loss drop"),
        ("5", "Compare", "chat vs base"),
    ]
    n = len(steps)
    cw, gap = 140, 22
    total = n * cw + (n - 1) * gap
    x0 = (W - total) / 2
    cy, ch = 78, 110
    for i, (num, title, sub) in enumerate(steps):
        x = x0 + i * (cw + gap)
        acc = ACCENT if i in (3,) else BLUE
        soft = ACCENT_SOFT if i in (3,) else BLUE_SOFT
        b.append(card(x, cy, cw, ch, soft, acc))
        b.append(f"<circle cx='{x+cw/2}' cy='{cy+30}' r='16' fill='{acc}'/>")
        b.append(text(x + cw / 2, cy + 35, num, 15, "#ffffff", "700"))
        b.append(text(x + cw / 2, cy + 66, title, 14, INK, "700"))
        b.append(text(x + cw / 2, cy + 88, sub, 11.5, MUTED))
        if i < n - 1:
            ax = x + cw + 3
            b.append(f"<line x1='{ax}' y1='{cy+ch/2}' x2='{ax+gap-6}' y2='{cy+ch/2}' stroke='{MUTED}' stroke-width='2.5' marker-end='url(#arrow)'/>")
    b.append(text(W / 2, H - 16, "Under the hood this is the same SFT / LoRA / QLoRA, just point-and-click.", 13, MUTED))
    save("04-studio-loop", svg(W, H, "".join(b)))


# ------------------------------------------------------------------ 5. launch flow
def diagram_launch():
    W, H = 860, 250
    b = []
    b.append(text(W / 2, 34, "Launching Studio: two moves", 20, INK, "700"))
    cw, ch, cy = 250, 140, 70
    x1, x2, x3 = 24, 305, 586
    # terminal
    b.append(card(x1, cy, cw, ch, "#0f172a", "#0f172a"))
    b.append(text(x1 + cw / 2, cy + 30, "1. In a terminal", 14, "#e2e8f0", "700"))
    b.append(f"<rect x='{x1+18}' y='{cy+46}' width='{cw-36}' height='40' rx='6' fill='#020617' stroke='#334155'/>")
    b.append(f"<text x='{x1+30}' y='{cy+70}' font-size='11.5' fill='#4ade80' font-family='Consolas, monospace' text-anchor='start'>unsloth studio</text>")
    b.append(f"<text x='{x1+30}' y='{cy+84}' font-size='11.5' fill='#4ade80' font-family='Consolas, monospace' text-anchor='start'>  -H 0.0.0.0 -p 8888</text>")
    b.append(text(x1 + cw / 2, cy + ch - 14, "File > New > Terminal", 11.5, "#94a3b8"))
    # cloudflare link
    b.append(card(x2, cy, cw, ch, AMBER_SOFT, AMBER))
    b.append(text(x2 + cw / 2, cy + 30, "2. Copy the secure link", 14, AMBER, "700"))
    b.append(f"<rect x='{x2+18}' y='{cy+50}' width='{cw-36}' height='34' rx='6' fill='#ffffff' stroke='{AMBER}'/>")
    b.append(f"<text x='{x2+cw/2}' y='{cy+71}' font-size='11' fill='{INK}' font-family='Consolas, monospace' text-anchor='middle'>https://....trycloudflare.com</text>")
    b.append(text(x2 + cw / 2, cy + ch - 26, "\"Use the secure link via", 11.5, MUTED))
    b.append(text(x2 + cw / 2, cy + ch - 12, "Cloudflare instead\"", 11.5, MUTED))
    # browser
    b.append(card(x3, cy, cw, ch, GREEN_SOFT, GREEN))
    b.append(text(x3 + cw / 2, cy + 30, "3. Open in your browser", 14, GREEN, "700"))
    b.append(f"<rect x='{x3+30}' y='{cy+46}' width='{cw-60}' height='60' rx='6' fill='#ffffff' stroke='{GREEN}'/>")
    b.append(f"<rect x='{x3+30}' y='{cy+46}' width='{cw-60}' height='14' rx='6' fill='{GREEN_SOFT}'/>")
    b.append(f"<circle cx='{x3+40}' cy='{cy+53}' r='2.5' fill='{GREEN}'/>")
    b.append(text(x3 + cw / 2, cy + 88, "Unsloth Studio", 12.5, GREEN, "700"))
    b.append(text(x3 + cw / 2, cy + ch - 12, "log in, then train", 11.5, MUTED))
    # arrows
    ay = cy + ch / 2
    b.append(f"<line x1='{x1+cw+4}' y1='{ay}' x2='{x2-6}' y2='{ay}' stroke='{MUTED}' stroke-width='2.5' marker-end='url(#arrow)'/>")
    b.append(f"<line x1='{x2+cw+4}' y1='{ay}' x2='{x3-6}' y2='{ay}' stroke='{MUTED}' stroke-width='2.5' marker-end='url(#arrow)'/>")
    b.append(text(W / 2, H - 12, "Prefer the Cloudflare link over the raw 0.0.0.0:8888 address.", 13, MUTED))
    save("05-launch-flow", svg(W, H, "".join(b)))


if __name__ == "__main__":
    diagram_overview()
    diagram_families()
    diagram_memory()
    diagram_loop()
    diagram_launch()
    print("done ->", ASSETS)
