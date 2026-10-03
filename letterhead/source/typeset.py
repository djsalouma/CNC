# -*- coding: utf-8 -*-
"""
Arabic/Latin typesetting for ReportLab.

HarfBuzz does the contextual shaping, python-bidi resolves the visual order and
the glyphs are emitted as vector outlines, so the PDF is print-perfect and does
not depend on the viewer having the font installed.
A hidden (invisible) text layer keeps the file searchable / copy-pasteable.
"""
import unicodedata
from functools import lru_cache

import uharfbuzz as hb
from fontTools.ttLib import TTFont as FTFont
from fontTools.pens.basePen import BasePen

from bidi.algorithm import get_empty_storage, get_embedding_levels, \
    explicit_embed_and_overrides, resolve_weak_types, resolve_neutral_types, \
    resolve_implicit_levels

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLTTFont


# ---------------------------------------------------------------------------
# font cache
# ---------------------------------------------------------------------------
@lru_cache(maxsize=None)
def _hb_font(path):
    blob = hb.Blob.from_file_path(path)
    face = hb.Face(blob)
    font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    return font, face.upem


@lru_cache(maxsize=None)
def _ft_font(path):
    f = FTFont(path, lazy=True)
    return f, f.getGlyphSet(), f.getGlyphOrder()


# ---------------------------------------------------------------------------
# bidi -> runs (logical order, with embedding levels)
# ---------------------------------------------------------------------------
_AR_RANGES = (
    (0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
)


def _is_arabic(ch):
    o = ord(ch)
    return any(a <= o <= b for a, b in _AR_RANGES)


def bidi_runs(text, base_dir="R"):
    """Return [(run_text, level, is_rtl), ...] in logical order."""
    storage = get_empty_storage()
    base_level = 1 if base_dir == "R" else 0
    storage["base_level"] = base_level
    storage["base_dir"] = base_dir
    get_embedding_levels(text, storage, False, False)
    explicit_embed_and_overrides(storage, False)
    resolve_weak_types(storage, False)
    resolve_neutral_types(storage, False)
    resolve_implicit_levels(storage, False)

    runs, cur, cur_level = [], [], None
    for ch in storage["chars"]:
        lvl = ch["level"]
        if cur_level is None or lvl == cur_level:
            cur.append(ch["ch"])
            cur_level = lvl
        else:
            runs.append(("".join(cur), cur_level, cur_level % 2 == 1))
            cur, cur_level = [ch["ch"]], lvl
    if cur:
        runs.append(("".join(cur), cur_level, cur_level % 2 == 1))
    return runs, base_level


def visual_runs(text, base_dir="R"):
    """Runs ordered the way they are painted (left to right).

    Adjacent runs that share a direction are merged first: for RTL runs the
    painted result is identical (reversing a concatenation == concatenating the
    reversed parts) and it keeps whole Arabic phrases in logical order, which
    makes the PDF text layer searchable and copy-pasteable.
    """
    runs, base_level = bidi_runs(text, base_dir)
    merged = []
    for run_text, level, is_rtl in runs:
        if merged and merged[-1][2] == is_rtl:
            t, lv, _, txt = merged[-1][0], merged[-1][1], merged[-1][2], merged[-1][0]
            merged[-1] = (merged[-1][0] + run_text, merged[-1][1], merged[-1][2])
        else:
            merged.append((run_text, level, is_rtl))
    if base_level == 1:
        merged = merged[::-1]
    return merged


# ---------------------------------------------------------------------------
# shaping
# ---------------------------------------------------------------------------
def shape_run(text, font_path, size, rtl):
    """-> [(glyph_name, x_advance, y_advance, x_offset, y_offset, cluster)]"""
    if not text:
        return []
    hbfont, upem = _hb_font(font_path)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.direction = "rtl" if rtl else "ltr"
    script = "Arab" if any(_is_arabic(c) for c in text) else "Latn"
    buf.script = script
    buf.language = "ar" if script == "Arab" else "en"
    hb.shape(hbfont, buf, {"kern": True, "liga": True, "calt": True})

    _, gs, _ = _ft_font(font_path)
    out = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((info.codepoint, pos.x_advance, pos.y_advance,
                    pos.x_offset, pos.y_offset, info.cluster))
    return out, upem


# ---------------------------------------------------------------------------
# outline pen: font units -> page points
# ---------------------------------------------------------------------------
class _GlyphPen(BasePen):
    def __init__(self, glyphSet, path, scale, ox, oy):
        super().__init__(glyphSet)
        self.path, self.s, self.ox, self.oy = path, scale, ox, oy

    def _pt(self, p):
        return self.ox + p[0] * self.s, self.oy + p[1] * self.s

    def _moveTo(self, pt):
        self.path.moveTo(*self._pt(pt))

    def _lineTo(self, pt):
        self.path.lineTo(*self._pt(pt))

    def _curveToOne(self, p1, p2, p3):
        a, b, cc = self._pt(p1), self._pt(p2), self._pt(p3)
        self.path.curveTo(a[0], a[1], b[0], b[1], cc[0], cc[1])

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        c1 = (p0[0] + 2.0 / 3.0 * (p1[0] - p0[0]), p0[1] + 2.0 / 3.0 * (p1[1] - p0[1]))
        c2 = (p2[0] + 2.0 / 3.0 * (p1[0] - p2[0]), p2[1] + 2.0 / 3.0 * (p1[1] - p2[1]))
        self._curveToOne(c1, c2, p2)

    def _closePath(self):
        self.path.close()

    def _endPath(self):
        self.path.close()


def _measure(text, font_path, size, base_dir="R", tracking=0.0):
    """-> (runs, line_width)  runs = [(text, start_x, shaped, scale, is_rtl)]."""
    runs, total = [], 0.0
    for run_text, level, is_rtl in visual_runs(text, base_dir):
        shaped, upem = shape_run(run_text, font_path, size, is_rtl)
        s = size / upem
        if not shaped:
            shaped, s = [], 1.0
        w = sum(g[1] for g in shaped) * s + tracking * len(shaped)
        runs.append((run_text, total, shaped, s, is_rtl))
        total += w
    line_w = max(0.0, total - (tracking if tracking else 0.0))
    return runs, line_w


def layout_runs(text, font_path, size, base_dir="R", tracking=0.0):
    """-> ([(run_text, x, width, is_rtl), ...], line_width)"""
    runs, line_w = _measure(text, font_path, size, base_dir, tracking)
    out = []
    for i, (run_text, rx, shaped, s, is_rtl) in enumerate(runs):
        nxt = runs[i + 1][1] if i + 1 < len(runs) else line_w
        out.append((run_text, rx, nxt - rx, is_rtl))
    return out, line_w


def layout(text, font_path, size, base_dir="R"):
    """All glyphs of a line, positioned relative to the line origin."""
    runs, count = [], 0
    for run_text, level, is_rtl in visual_runs(text, base_dir):
        shaped, upem = shape_run(run_text, font_path, size, is_rtl)
        s = size / upem
        runs.append((shaped, s))
    return runs


def text_width(text, font_path, size, base_dir="R", tracking=0.0):
    return _measure(text, font_path, size, base_dir, tracking)[1]


def draw_text(c, text, x, y, font_path, size, color, align="left",
              base_dir="R", tracking=0.0, hidden=True):
    """Paint shaped text as vector outlines (+ an invisible searchable layer).

    Returns the advance width of the line.
    """
    if not text:
        return 0.0
    runs, width = _measure(text, font_path, size, base_dir, tracking)
    if align == "right":
        x -= width
    elif align == "center":
        x -= width / 2.0

    _, gs, order = _ft_font(font_path)

    # ---- visible, outlined glyphs -----------------------------------------
    c.saveState()
    c.setFillColor(color)
    path = c.beginPath()
    for run_text, rx, shaped, s, is_rtl in runs:
        cx = x + rx
        for i, (gid, xa, ya, xo, yo, _cl) in enumerate(shaped):
            gname = order[gid] if 0 <= gid < len(order) else None
            if gname:
                try:
                    g = gs[gname]
                except KeyError:
                    g = None
                if g is not None:
                    g.draw(_GlyphPen(gs, path, s, cx + xo * s, y + yo * s))
            cx += xa * s + tracking
    c.drawPath(path, stroke=0, fill=1, fillMode=1)      # non-zero winding
    c.restoreState()

    # ---- invisible text layer (search / copy-paste) ------------------------
    if hidden:
        name = _rl_font_name(font_path)
        c.saveState()
        c.setFont(name, size)
        for run_text, rx, shaped, s, is_rtl in runs:
            if not run_text:
                continue
            t = c.beginText(x + rx, y)
            t.setTextRenderMode(3)
            if tracking:
                t.setCharSpace(tracking)
            t.textOut(run_text)
            c.drawText(t)
        c.restoreState()
    return width


@lru_cache(maxsize=None)
def _rl_font_name(font_path):
    """Register a parallel ReportLab font (used only for the invisible layer)."""
    name = "INV-" + str(abs(hash(font_path)) % 10 ** 8)
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(RLTTFont(name, font_path))
    return name
