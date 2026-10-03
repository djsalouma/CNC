# -*- coding: utf-8 -*-
"""Generate every Goya Ten stationery asset from one design source."""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, HexColor

import pymupdf
from PIL import Image
import PIL.ImageChops as C

from design import (PW, PH, MM, Y, MARGIN_X, RIGHT_EDGE, CONTENT_W, FONT_FILES,
                    NAVY, GOLD, RULE_LIGHT, GRAY, WHITE, BRAND_EN, BRAND_AR,
                    ADDR_EN, ADDR_AR)
import stationery as st
from stationery import (draw_header, draw_footer, lockup, lockup_width,
                        monogram, T, HEADER_H, FOOTER_H, FOOTER_TOP, BODY_TOP,
                        BODY_BOTTOM, TEL, MAIL, WEB)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = _ROOT                       # .../letterhead
LOGO = f"{OUT}/logo"
TMP = os.path.join(_ROOT, "source", "_build")
W = 210.0
DPI = 300


# ---------------------------------------------------------------------------
def render(c, path):
    c.showPage()
    c.save()
    return path


def to_png(pdf_path, png_path, dpi=DPI, trim=False, keep_alpha=True, page=0, pad=0.0):
    d = pymupdf.open(pdf_path)
    d[page].get_pixmap(dpi=dpi, alpha=keep_alpha).save(png_path)
    if trim:
        im = Image.open(png_path).convert("RGBA")
        b = im.getbbox()
        if b:
            im = im.crop(b)
        if pad:                      # breathing space around a trimmed logo
            px = int(round(pad * max(im.size)))
            canvas_ = Image.new("RGBA", (im.width + 2 * px, im.height + 2 * px), (0, 0, 0, 0))
            canvas_.paste(im, (px, px))
            im = canvas_
        if keep_alpha:
            im.save(png_path)
        else:
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            flat = Image.alpha_composite(bg, im).convert("RGB")
            b2 = C.difference(flat, Image.new("RGB", flat.size, (255, 255, 255))).getbbox()
            if b2:
                flat = flat.crop(b2)
            flat.save(png_path)
    d.close()
    return png_path


# ---------------------------------------------------------------------------
# 1. the A4 letterhead (vector PDF)
# ---------------------------------------------------------------------------
def build_letterhead(path, style="corporate", pages=1, guide=False):
    c = canvas.Canvas(path, pagesize=(PW, PH))
    c.setTitle("Goya Ten - Official Letterhead A4")
    c.setAuthor("Goya Ten")
    c.setSubject("ترويسة شركة جويا تن الرسمية - Goya Ten official letterhead")
    c.setKeywords("Goya Ten, GoyaTen, جويا تن, letterhead, Maadi, Cairo, Egypt")
    for p in range(pages):
        if p:
            c.showPage()
        draw_header(c, style)
        draw_footer(c, style)
        if guide:
            body_guides(c)
    return render(c, path)


def body_guides(c):
    c.saveState()
    c.setStrokeColor(Color(0.80, 0.85, 0.90, alpha=0.85))
    c.setLineWidth(0.3)
    c.setDash(1.8, 2.6)
    y = Y(BODY_TOP)
    while y > Y(BODY_BOTTOM) - 0.01:
        c.line(MARGIN_X, y, RIGHT_EDGE, y)
        y -= 10 * MM
    c.setStrokeColor(Color(0.90, 0.55, 0.55, alpha=0.9))
    c.line(MARGIN_X, Y(BODY_TOP), RIGHT_EDGE, Y(BODY_TOP))
    c.line(MARGIN_X, Y(BODY_BOTTOM), RIGHT_EDGE, Y(BODY_BOTTOM))
    c.setStrokeColor(Color(0.55, 0.72, 0.90, alpha=0.8))
    c.setDash(3, 3)
    for x in (MARGIN_X, RIGHT_EDGE):
        c.line(x, 0, x, PH)
    c.restoreState()


# ---------------------------------------------------------------------------
# 2. sample, filled-in letter (shows the letterhead in use)
# ---------------------------------------------------------------------------
SAMPLE_BODY_AR = [
    "السيد الأستاذ / .................................................",
    "الموقر",
    "",
    "تحية طيبة وبعد،،",
    "",
    "يسعدنا أن نتقدم إليكم بعرضنا المرفق، ونؤكد لسيادتكم حرص شركة جويا تن",
    "على تقديم أفضل الخدمات والمنتجات بأعلى معايير الجودة وفي التوقيتات المتفق عليها.",
    "",
    "وفي انتظار ردكم الكريم، تفضلوا بقبول فائق الاحترام والتقدير.",
    "",
    "",
    "المدير التنفيذي",
    "جويا تن",
]
SAMPLE_BODY_EN = [
    "Dear Sir / Madam,",
    "",
    "Thank you for your interest in Goya Ten. Please find enclosed our latest offer;",
    "we remain at your disposal for any further information or clarification.",
    "",
    "Yours faithfully,",
    "Goya Ten",
]


def build_sample_letter(path):
    c = canvas.Canvas(path, pagesize=(PW, PH))
    c.setTitle("Goya Ten - Sample Letter")
    c.setAuthor("Goya Ten")
    draw_header(c)
    draw_footer(c)

    y = BODY_TOP
    # date / reference line, right aligned (Arabic business style)
    T(c, "التاريخ: ................................", RIGHT_EDGE, Y(y), st.AR, 10.5, GRAY, "right", "R")
    T(c, "Date: ........................", MARGIN_X, Y(y), st.SANS, 10.0, GRAY, "left", "L")
    y += 9

    T(c, "السيد الأستاذ / .................................................",
      RIGHT_EDGE, Y(y), st.AR_M, 12, NAVY, "right", "R")
    y += 8
    T(c, "تحية طيبة وبعد،،", RIGHT_EDGE, Y(y), st.AR, 11, HexColor("#333333"), "right", "R")
    y += 11

    ar_lines = [
        "يسعدنا أن نتقدم إلى سيادتكم بخدمات شركة جويا تن، ونؤكد حرصنا على تقديم",
        "أفضل الحلول والمنتجات بأعلى معايير الجودة وفي التوقيتات المتفق عليها.",
        "",
        "ونحن في انتظار ردكم الكريم، تفضلوا بقبول فائق الاحترام والتقدير.",
    ]
    for line in ar_lines:
        if line:
            T(c, line, RIGHT_EDGE, Y(y), st.AR, 11, HexColor("#333333"), "right", "R")
        y += 7.2

    y += 6
    for line in SAMPLE_BODY_EN:
        if line:
            T(c, line, MARGIN_X, Y(y), st.SANS, 10.5, HexColor("#333333"), "left", "L", 0.1)
        y += 5.6

    y += 8
    T(c, "المدير التنفيذي", RIGHT_EDGE, Y(y), st.AR_M, 11, NAVY, "right", "R")
    y += 6.5
    T(c, "جويا تن", RIGHT_EDGE, Y(y), st.AR_B, 13, NAVY, "right", "R")
    y += 12
    T(c, "Managing Director  -  Goya Ten", MARGIN_X, Y(y), st.SANS_B, 10.5, NAVY, "left", "L", 0.1)
    return render(c, path)


# ---------------------------------------------------------------------------
# 3. header / footer strips for the Word template (full bleed, transparent)
# ---------------------------------------------------------------------------
def build_strips():
    hp = f"{TMP}/word_header.pdf"
    c = canvas.Canvas(hp)
    c.setPageSize((W * MM, HEADER_H * MM))
    c.translate(0, -(297.0 - HEADER_H) * MM)
    draw_header(c)
    render(c, hp)

    fp = f"{TMP}/word_footer.pdf"
    c = canvas.Canvas(fp)
    c.setPageSize((W * MM, FOOTER_H * MM))
    draw_footer(c)
    render(c, fp)

    h = to_png(hp, f"{TMP}/word_header.png", dpi=600)
    f = to_png(fp, f"{TMP}/word_footer.png", dpi=600)
    return h, f


# ---------------------------------------------------------------------------
# 4. stand-alone logo files
# ---------------------------------------------------------------------------
def build_logos():
    made = []

    h = 22 * MM
    w = lockup_width(h) + 6 * MM
    pdf = f"{TMP}/_logo_h.pdf"
    c = canvas.Canvas(pdf)
    c.setPageSize((w, h + 6 * MM))
    lockup(c, 3 * MM, 3 * MM, h, tile=True)
    render(c, pdf)
    made.append(to_png(pdf, f"{LOGO}/Goya_Ten_Logo_Horizontal.png", dpi=600,
                       trim=True, keep_alpha=False, pad=0.02))
    made.append(to_png(pdf, f"{LOGO}/Goya_Ten_Logo_Horizontal_Transparent.png", dpi=600,
                       trim=True, pad=0.02))
    shutil.copy(pdf, f"{LOGO}/Goya_Ten_Logo_Horizontal.pdf")

    s = 24 * MM
    pdf = f"{TMP}/_logo_m.pdf"
    c = canvas.Canvas(pdf)
    c.setPageSize((s + 4 * MM, s + 4 * MM))
    monogram(c, 2 * MM, 2 * MM, s, tile=True)
    render(c, pdf)
    made.append(to_png(pdf, f"{LOGO}/Goya_Ten_Monogram.png", dpi=600, trim=True,
                       keep_alpha=False, pad=0.03))
    made.append(to_png(pdf, f"{LOGO}/Goya_Ten_Monogram_Transparent.png", dpi=600,
                       trim=True, pad=0.03))
    shutil.copy(pdf, f"{LOGO}/Goya_Ten_Monogram.pdf")

    # white version - for dark backgrounds
    pdf = f"{TMP}/_logo_w.pdf"
    c = canvas.Canvas(pdf)
    c.setPageSize((s + 4 * MM, s + 4 * MM))
    monogram(c, 2 * MM, 2 * MM, s, tile=False, bar=WHITE, letters=WHITE)
    render(c, pdf)
    made.append(to_png(pdf, f"{LOGO}/Goya_Ten_Monogram_White.png", dpi=600, trim=True,
                       pad=0.03))
    shutil.copy(pdf, f"{LOGO}/Goya_Ten_Monogram_White.pdf")
    return made


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    for d in (OUT, LOGO, TMP):
        os.makedirs(d, exist_ok=True)

    corp = build_letterhead(f"{OUT}/Goya_Ten_Letterhead_A4_Corporate.pdf", "corporate", pages=2)
    mini = build_letterhead(f"{OUT}/Goya_Ten_Letterhead_A4_Minimal.pdf", "minimal", pages=2)
    build_letterhead(f"{TMP}/guide.pdf", "corporate", guide=True)
    sample = build_sample_letter(f"{OUT}/Goya_Ten_Letterhead_Sample_Letter.pdf")

    for pdf, name in [(corp, "Goya_Ten_Letterhead_A4_Corporate"),
                      (mini, "Goya_Ten_Letterhead_A4_Minimal")]:
        to_png(pdf, f"{OUT}/{name}.png", dpi=300, keep_alpha=False)



    # margin guide (printable area) for whoever types the letters
    to_png(f"{TMP}/guide.pdf", f"{OUT}/Goya_Ten_Letterhead_Margins_Guide.png",
           dpi=300, keep_alpha=False)

    print(build_strips())
    print(build_logos())
    print("assets done")
