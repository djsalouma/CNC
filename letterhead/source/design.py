# -*- coding: utf-8 -*-
"""
Goya Ten  -  letterhead design tokens (brand, palette, geometry, fonts).

Arabic typesetting itself lives in typeset.py (HarfBuzz + python-bidi).
"""
import os
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ----------------------------------------------------------------------------
# Brand content
# ----------------------------------------------------------------------------
BRAND_EN       = "GOYA TEN"
BRAND_AR       = "جويا تن"
ADDR_EN        = "105 Street, Maadi, Cairo, Egypt"
ADDR_AR        = "شارع 105، المعادي، القاهرة، مصر"
WEB_PLACEHOLDER = ""          # keep empty unless the client supplies it

# ----------------------------------------------------------------------------
# Palette
# ----------------------------------------------------------------------------
NAVY       = HexColor("#0E2A47")
NAVY_SOFT  = HexColor("#1B4066")
GOLD       = HexColor("#C0A062")
GOLD_DARK  = HexColor("#A98A4B")
GRAY       = HexColor("#6E7681")
RULE_LIGHT = HexColor("#D9DEE5")
WHITE      = HexColor("#FFFFFF")

# ----------------------------------------------------------------------------
# Geometry (A4)
# ----------------------------------------------------------------------------
MM = 2.8346456692913385           # 1 mm in points
PW, PH = 595.276, 841.89          # A4 portrait


def Y(mm_from_top: float) -> float:
    """Convert a distance measured from the top edge into a PDF y coordinate."""
    return PH - mm_from_top * MM


MARGIN_X   = 20 * MM                      # 20 mm left / right
CONTENT_W  = PW - 2 * MARGIN_X
RIGHT_EDGE = PW - MARGIN_X

# ----------------------------------------------------------------------------
# Fonts
# ----------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
#: fonts shipped next to this file (see fonts/), otherwise the Google Fonts clone
FDIR = os.path.join(_HERE, "fonts") if os.path.isdir(os.path.join(_HERE, "fonts")) \
    else "/home/user/work/gfonts/ofl"
FONT_FILES = {
    "GT-Sans":       f"{FDIR}/Carlito-Regular.ttf",
    "GT-Sans-Bold":  f"{FDIR}/Carlito-Bold.ttf",
    "GT-Ar":         f"{FDIR}/IBMPlexSansArabic-Regular.ttf",
    "GT-Ar-Med":     f"{FDIR}/IBMPlexSansArabic-Medium.ttf",
    "GT-Ar-Semi":    f"{FDIR}/IBMPlexSansArabic-SemiBold.ttf",
    "GT-Ar-Bold":    f"{FDIR}/IBMPlexSansArabic-Bold.ttf",
    # standalone wordmark face (all caps, tight, heavy)
    "GT-Mark":       f"{FDIR}/Lato-Black.ttf",
}
_REGISTERED = False


def register_fonts():
    global _REGISTERED
    if _REGISTERED:
        return
    for name, path in FONT_FILES.items():
        assert os.path.exists(path), path
        pdfmetrics.registerFont(TTFont(name, path))
    _REGISTERED = True
