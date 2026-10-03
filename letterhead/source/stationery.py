# -*- coding: utf-8 -*-
"""
Goya Ten  -  shared stationery drawing routines.

Everything is drawn in *page coordinates* measured from the top edge of an A4
sheet (via design.Y()), so the very same code produces
  * the A4 letterhead PDF,
  * the header / footer images that are embedded in the Word template,
  * the stand-alone logo files.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

import typeset as ts
from design import (BRAND_EN, BRAND_AR, ADDR_EN, ADDR_AR, NAVY, GOLD, GRAY,
                    RULE_LIGHT, WHITE, MM, PW, PH, Y, MARGIN_X, CONTENT_W,
                    RIGHT_EDGE, FONT_FILES)

SANS, SANS_B = FONT_FILES["GT-Sans"], FONT_FILES["GT-Sans-Bold"]
MARK = FONT_FILES["GT-Mark"]
AR, AR_M, AR_B = FONT_FILES["GT-Ar"], FONT_FILES["GT-Ar-Med"], FONT_FILES["GT-Ar-Bold"]
SOFT = HexColor("#C9D3DE")

# --- editable contact details (placeholders) --------------------------------
TEL = "01067668961"
MAIL = "info@goyaten.com"
WEB = "www.goyaten.com"

# --- page geometry, mm from the top edge ------------------------------------
HEADER_H = 46.0          # header block height (strips + logo + rule)
BODY_TOP = 50.0          # first text line
BODY_BOTTOM = 262.0      # last text line
FOOTER_H = 30.5          # from FOOTER_TOP down to the paper edge
FOOTER_TOP = 297.0 - FOOTER_H


def T(c, text, x, y, font, size, color, align="left", base="L", track=0.0, hidden=True):
    return ts.draw_text(c, text, x, y, font, size, color, align=align,
                        base_dir=base, tracking=track, hidden=hidden)


# ---------------------------------------------------------------------------
# logo
# ---------------------------------------------------------------------------
def monogram(c, x, y, size, tile=True, bar=GOLD, letters=None):
    """Square 'GT' monogram. (x, y) = bottom-left corner, size = side in pt."""
    r = size * 0.17
    bar_w, bar_h = size * 0.50, size * 0.050
    if tile:
        c.setFillColor(NAVY)
        c.roundRect(x, y, size, size, r, stroke=0, fill=1)

    fs = size * 0.545
    cap_top = y + size * 0.735
    col = letters or (WHITE if tile else NAVY)
    T(c, "GT", x + size / 2, cap_top - fs * 0.735, MARK, fs, col,
      align="center", base="L", track=-fs * 0.02)

    c.setFillColor(bar)
    yb = y + size * 0.20 if tile else y + size * 0.055
    c.rect(x + (size - bar_w) / 2, yb, bar_w, bar_h, stroke=0, fill=1)


def lockup(c, x, y_bottom, h, tile=True, tagline="Cairo  •  Egypt"):
    """Monogram + English wordmark. Returns the drawn width."""
    monogram(c, x, y_bottom, h, tile=tile)
    wx = x + h + h * 0.32
    fs = h * 0.575
    w1 = T(c, BRAND_EN, wx, y_bottom + h * 0.47, MARK, fs, NAVY, "left", "L", fs * 0.06)
    sub = h * 0.145
    w2 = T(c, tagline, wx + fs * 0.05, y_bottom + h * 0.16, SANS_B, sub, GRAY,
           "left", "L", sub * 0.30)
    return wx + max(w1, w2) - x


def lockup_width(h, tagline="Cairo  •  Egypt"):
    fs = h * 0.575
    w1 = ts.text_width(BRAND_EN, MARK, fs, "L", fs * 0.06)
    sub = h * 0.145
    w2 = ts.text_width(tagline, SANS_B, sub, "L", sub * 0.30)
    return h + h * 0.32 + max(w1, w2)


# ---------------------------------------------------------------------------
# header / footer
# ---------------------------------------------------------------------------
def draw_header(c, style="corporate"):
    """Navy strips + logo lock-up + Arabic block + gold rule."""
    if style == "corporate":
        c.setFillColor(NAVY)
        c.rect(0, Y(3.6), PW, 3.6 * MM, stroke=0, fill=1)
        c.setFillColor(GOLD)
        c.rect(0, Y(4.9), PW, 1.3 * MM, stroke=0, fill=1)
    else:
        c.setFillColor(GOLD)
        c.rect(0, Y(1.4), PW, 1.4 * MM, stroke=0, fill=1)

    tile = style == "corporate"
    lockup(c, MARGIN_X, Y(34 if tile else 32.5), 21 * MM if tile else 19 * MM, tile=tile)

    T(c, BRAND_AR, RIGHT_EDGE, Y(25.3), AR_B, 25 if tile else 22, NAVY, "right", "R")
    T(c, ADDR_AR, RIGHT_EDGE, Y(32.2), AR, 10.4 if tile else 10.0, GRAY, "right", "R")

    if tile:
        c.setFillColor(GOLD)
        c.rect(MARGIN_X, Y(44.0), CONTENT_W, 1.1 * MM, stroke=0, fill=1)
        c.setFillColor(RULE_LIGHT)
        c.rect(MARGIN_X, Y(45.0), CONTENT_W, 0.3 * MM, stroke=0, fill=1)
    else:
        c.setFillColor(GOLD)
        c.rect(MARGIN_X, Y(41.5), CONTENT_W, 0.9 * MM, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.rect(MARGIN_X, Y(42.6), CONTENT_W, 0.32 * MM, stroke=0, fill=1)


def draw_footer(c, style="corporate"):
    if style == "corporate":
        c.setFillColor(RULE_LIGHT)
        c.rect(MARGIN_X, Y(266.5), CONTENT_W, 0.3 * MM, stroke=0, fill=1)
        T(c, f"هاتف / Tel: {TEL}     •     البريد الإلكتروني / Email: {MAIL}",
          PW / 2, Y(271.8), AR_M, 8.8, GRAY, "center", "R")
        T(c, f"Web: {WEB}", PW / 2, Y(276.6), SANS, 8.4, GRAY, "center", "L", 0.2)

        c.setFillColor(GOLD)
        c.rect(0, 11.9 * MM, PW, 1.3 * MM, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.rect(0, 0, PW, 10.6 * MM, stroke=0, fill=1)
        T(c, ADDR_EN, MARGIN_X, 4.4 * MM, SANS, 8.2, SOFT, "left", "L", 0.15)
        T(c, BRAND_EN, PW / 2, 4.4 * MM, MARK, 9.6, WHITE, "center", "L", 2.4)
        T(c, ADDR_AR, RIGHT_EDGE, 4.4 * MM, AR, 8.6, SOFT, "right", "R")
    else:
        c.setFillColor(NAVY)
        c.rect(MARGIN_X, Y(272.0), CONTENT_W, 0.32 * MM, stroke=0, fill=1)
        T(c, ADDR_AR, PW / 2, Y(277.6), AR, 8.8, GRAY, "center", "R")
        T(c, ADDR_EN, PW / 2, Y(282.6), SANS, 8.6, GRAY, "center", "L", 0.2)
        T(c, f"هاتف / Tel: {TEL}     •     البريد الإلكتروني / Email: {MAIL}     •     {WEB}",
          PW / 2, Y(288.4), AR_M, 8.4, GRAY, "center", "R")
        c.setFillColor(GOLD)
        c.rect(0, 0, PW, 1.4 * MM, stroke=0, fill=1)
