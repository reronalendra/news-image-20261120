#!/usr/bin/env python3
"""Render the 20 November 2026 world-news front page as a 1024x1024 PNG.

Everything is drawn with Pillow primitives and the DejaVu fonts that ship
with the system, so the output is fully deterministic: same input, same
bytes, every run. Run:  python3 build_image.py [out.png]
"""

import math
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024


def _find_font(bold):
    """Locate a DejaVu font across OS font dirs; fail loudly if absent."""
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for cand in (
        f"/usr/share/fonts/truetype/dejavu/{name}",
        f"/usr/share/fonts/dejavu/{name}",
        f"/usr/local/share/fonts/{name}",
        f"/opt/homebrew/share/fonts/{name}",
        f"/System/Library/Fonts/Supplemental/{name}",
        f"C:/Windows/Fonts/{name}",
    ):
        if Path(cand).is_file():
            return cand
    raise RuntimeError(f"DejaVu font not found: {name}")


BOLD = _find_font(True)
REG = _find_font(False)

PAPER = (247, 243, 234)      # warm newsprint
INK = (16, 28, 46)           # near-black navy
NAVY = (16, 35, 63)          # masthead band
RED = (178, 34, 34)          # accent / hero bar
GOLD = (197, 146, 44)
CARD = (255, 255, 255)
LINE = (203, 196, 182)
MUTED = (84, 92, 104)
TEAL = (15, 110, 110)
GREEN = (34, 120, 60)
ORANGE = (196, 90, 20)
PURPLE = (96, 62, 140)


@lru_cache(maxsize=None)
def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, lines, fnt, fill, leading):
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += leading
    return y


def tag(draw, x, y, label, color):
    f = font(BOLD, 17)
    w = int(draw.textlength(label, font=f)) + 18
    draw.rounded_rectangle([x, y, x + w, y + 26], radius=4, fill=color)
    draw.text((x + 9, y + 4), label, font=f, fill=(255, 255, 255))
    return w


# ---- little flat icons, drawn with plain shapes ---------------------------

def icon_bridge(d, x, y, s, col):
    # a bridge deck with two arches, plus a burst above it
    d.line([(x, y + s * 0.62), (x + s, y + s * 0.62)], fill=col, width=5)
    d.arc([x + s * 0.06, y + s * 0.30, x + s * 0.48, y + s * 0.95],
          180, 360, fill=col, width=5)
    d.arc([x + s * 0.52, y + s * 0.30, x + s * 0.94, y + s * 0.95],
          180, 360, fill=col, width=5)
    # two suspension towers between deck and arches
    for px in (0.27, 0.73):
        d.line([(x + s * px, y + s * 0.30), (x + s * px, y + s * 0.62)],
               fill=col, width=4)
    cx, cy = x + s * 0.5, y + s * 0.22
    for ang in range(0, 360, 45):
        r1, r2 = s * 0.08, s * 0.18
        a = math.radians(ang)
        d.line([(cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                (cx + r2 * math.cos(a), cy + r2 * math.sin(a))],
               fill=(214, 48, 49), width=4)


def icon_chart(d, x, y, s, col):
    pts = [(x, y + s * 0.25), (x + s * 0.28, y + s * 0.42),
           (x + s * 0.52, y + s * 0.34), (x + s * 0.80, y + s * 0.72)]
    d.line(pts, fill=col, width=6, joint="curve")
    ex, ey = x + s * 0.80, y + s * 0.72
    d.polygon([(ex, ey + s * 0.14), (ex - s * 0.16, ey - s * 0.06),
               (ex + s * 0.02, ey - s * 0.16)], fill=col)


def icon_cyclone(d, x, y, s, col):
    for i, r in enumerate([s * 0.46, s * 0.34, s * 0.22]):
        d.arc([x + s / 2 - r, y + s / 2 - r, x + s / 2 + r, y + s / 2 + r],
              200 + i * 55, 200 + i * 55 + 250, fill=col, width=6)
    d.ellipse([x + s * 0.44, y + s * 0.44, x + s * 0.56, y + s * 0.56],
              fill=col)


def icon_quake(d, x, y, s, col):
    # sharp seismograph wave inside a frame
    d.rectangle([x + s * 0.04, y + s * 0.04, x + s * 0.96, y + s * 0.96],
                outline=col, width=4)
    d.line([(x + s * 0.10, y + s * 0.60), (x + s * 0.26, y + s * 0.60),
            (x + s * 0.33, y + s * 0.34), (x + s * 0.42, y + s * 0.82),
            (x + s * 0.52, y + s * 0.46), (x + s * 0.62, y + s * 0.68),
            (x + s * 0.90, y + s * 0.60)], fill=col, width=5,
           joint="curve")


def icon_podium(d, x, y, s, col):
    d.rectangle([x + s * 0.30, y + s * 0.45, x + s * 0.70, y + s * 0.92],
                fill=col)
    d.rectangle([x + s * 0.22, y + s * 0.36, x + s * 0.78, y + s * 0.48],
                fill=col)
    d.line([(x + s * 0.50, y + s * 0.36), (x + s * 0.50, y + s * 0.06)],
           fill=col, width=4)
    d.polygon([(x + s * 0.50, y + s * 0.06), (x + s * 0.86, y + s * 0.14),
               (x + s * 0.50, y + s * 0.24)], fill=(178, 34, 34))


def icon_tanker(d, x, y, s, col):
    d.polygon([(x, y + s * 0.55), (x + s, y + s * 0.55),
               (x + s * 0.88, y + s * 0.88), (x + s * 0.12, y + s * 0.88)],
              fill=col)
    d.rectangle([x + s * 0.58, y + s * 0.34, x + s * 0.82, y + s * 0.55],
                fill=col)
    d.polygon([(x + s * 0.30, y + s * 0.42), (x + s * 0.40, y + s * 0.18),
               (x + s * 0.48, y + s * 0.42)], fill=(230, 126, 34))
    d.polygon([(x + s * 0.14, y + s * 0.48), (x + s * 0.22, y + s * 0.30),
               (x + s * 0.30, y + s * 0.48)], fill=(230, 126, 34))


def icon_globe(d, x, y, s, col):
    d.ellipse([x, y, x + s, y + s], outline=col, width=6)
    d.ellipse([x + s * 0.32, y, x + s * 0.68, y + s], outline=col, width=4)
    d.line([(x, y + s * 0.50), (x + s, y + s * 0.50)], fill=col, width=4)
    # latitude curves kept inside the globe outline
    d.arc([x + s * 0.14, y + s * 0.14, x + s * 0.86, y + s * 0.86],
          200, 340, fill=col, width=4)
    d.arc([x + s * 0.14, y + s * 0.14, x + s * 0.86, y + s * 0.86],
          20, 160, fill=col, width=4)


CARDS = [
    dict(tag="UKRAINE  ·  WAR", color=RED, icon=icon_bridge,
         head="Russia's biggest strike of the month hits Kyiv — missiles land in Poland",
         body="More than 400 drones and 110 missiles overnight; three Kyiv bridges hit, "
              "at least 8 killed. Two Russian missiles and a drone came down in Poland."),
    dict(tag="MARKETS  ·  ECONOMY", color=NAVY, icon=icon_chart,
         head="AI sell-off drags Wall Street into correction",
         body="S&P 500 -3.7%; Nasdaq -5.3%. Nvidia -14%; Anthropic -8.5%. "
              "S&P, Dow in correction."),
    dict(tag="INDIA  ·  WEATHER", color=TEAL, icon=icon_cyclone,
         head="Cyclone Akvan makes landfall in Odisha",
         body="Winds of 70–80 km/h near Gopalpur; over 300,000 evacuated. "
              "Heavy rain, but no deaths reported."),
    dict(tag="PERU  ·  EARTHQUAKE", color=ORANGE, icon=icon_quake,
         head="Magnitude 6.7 quake shakes the Andes",
         body="Epicentre in Junín, felt in Lima as residents rushed outdoors. "
              "No casualties reported."),
    dict(tag="USA  ·  POLITICS", color=PURPLE, icon=icon_podium,
         head="Trump defends Putin ties, accuses Iran of stalling",
         body="After the Shenzhen summit, Trump said Putin wants peace and "
              "accused Iran of stalling."),
    dict(tag="HORMUZ  ·  ENERGY", color=(120, 60, 20), icon=icon_tanker,
         head="Tanker struck by projectile, catches fire",
         body="Hit 8 nautical miles north of Khasab, Oman. No casualties. "
              "Iran says the tanker struck a mine."),
    dict(tag="CLIMATE  ·  COP31", color=GREEN, icon=icon_globe,
         head="COP31 endgame: no deal, fossil fuels dropped",
         body="Talks in Antalya run past the Friday deadline. The draft deal "
              "drops every mention of fossil fuels."),
]

ALSO = [
    ("MYANMAR", "Myanmar calls the ICJ genocide ruling \u201cunfair\u201d"),
    ("SAUDI ARABIA", "Saudi defences intercept Houthi missile aimed at the south"),
    ("ESTONIA", "Land border with Russia to shut for six months from 1 Dec"),
]


def draw_card(d, x, y, w, h, card, hero=False):
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=CARD,
                        outline=LINE, width=1)
    pad = 18
    if hero:
        d.rounded_rectangle([x, y, x + 10, y + h], radius=5, fill=RED)
        tx = x + pad + 8
    else:
        tx = x + pad
    tag(d, tx, y + 14, card["tag"], card["color"])
    icon_size = 84 if hero else 58
    ix = x + w - icon_size - 16
    iy = y + 12
    card["icon"](d, ix, iy, icon_size, card["color"])
    head_f = font(BOLD, 30 if hero else 22)
    body_f = font(REG, 21 if hero else 17)
    max_head = w - (pad + 8 if hero else pad) - icon_size - 28
    head_lines = wrap(d, card["head"], head_f, max_head)
    hy = y + 48 if hero else y + 46
    hy = text_block(d, tx, hy, head_lines, head_f, INK, 36 if hero else 26)
    body_lines = wrap(d, card["body"], body_f, w - 2 * pad - (8 if hero else 0))
    body_end = text_block(d, tx, hy + (6 if hero else 4), body_lines, body_f,
                          (58, 64, 76), 26 if hero else 21)
    assert body_end <= y + h - 8, (
        f"card overflow: {card['tag']} text ends at y={body_end}, "
        f"card bottom is y={y + h}")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead ------------------------------------------------------
    d.rectangle([0, 0, W, 132], fill=NAVY)
    d.rectangle([0, 132, W, 138], fill=GOLD)
    d.text((28, 16), "THE WORLD IN ONE IMAGE", font=font(BOLD, 19),
           fill=(212, 175, 105))
    d.text((28, 42), "FRIDAY, 20 NOVEMBER 2026", font=font(BOLD, 46),
           fill=(255, 255, 255))
    d.text((28, 100), "Seven stories that defined the day — from Kyiv to Lima",
           font=font(REG, 20), fill=(196, 208, 224))

    # ---- hero card -----------------------------------------------------
    draw_card(d, 28, 152, W - 56, 190, CARDS[0], hero=True)

    # ---- six-card grid -------------------------------------------------
    gx, gy = 28, 354
    cw, ch, gap = (W - 56 - 16) // 2, 164, 16
    for i, card in enumerate(CARDS[1:]):
        cx = gx + (i % 2) * (cw + gap)
        cy = gy + (i // 2) * (ch + 10)
        draw_card(d, cx, cy, cw, ch, card)

    # ---- also today ----------------------------------------------------
    ay = gy + 3 * ch + 2 * 10 + 14
    d.rounded_rectangle([28, ay, W - 28, ay + 104], radius=10, fill=NAVY)
    d.text((46, ay + 10), "ALSO TODAY", font=font(BOLD, 18),
           fill=(212, 175, 105))
    col_w = (W - 56 - 36) // 3
    for i, (label, text) in enumerate(ALSO):
        ax = 46 + i * col_w
        d.text((ax, ay + 36), label, font=font(BOLD, 16),
               fill=(212, 175, 105))
        lines = wrap(d, text, font(REG, 16), col_w - 16)
        assert len(lines) <= 2, (
            f"ALSO overflow: {label} wraps to {len(lines)} lines")
        text_block(d, ax, ay + 58, lines, font(REG, 16),
                   (220, 226, 234), 20)

    # ---- footer --------------------------------------------------------
    d.text((28, H - 26),
           "Sources: Reuters, AP, BBC, ISW, USGS, Barron's, India Meteorological Dept, UKMTO  ·  All events of 20 November 2026",
           font=font(REG, 15), fill=MUTED)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG", optimize=True)


if __name__ == "__main__":
    main()
