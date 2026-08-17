#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TIMBER LATTICE — CNC Panel Generator (DXF + previews)
=====================================================
Ø300mm round panel inside a 300x300mm stock.

Design (from the user's spec):
  * Circular frame ring  : outer Ø300, inner Ø280  -> ring width 10mm.
                           Ring is RAISED 5mm above the RED (base) level.
  * Triangular lattice mosaic inside the Ø280 circle (hexagonal tiling,
    hexagon inscribed in the circle, outer ring of triangles stretched
    onto the circle so the mosaic fills it completely).
  * 3 triangle "models", each on its own color layer:
       RED    : flat pocket, depth  5mm                       (field/base level)
       YELLOW : flat pocket 15mm + inscribed pyramid below,
                pyramid wall angle A_YEL from vertical.
       BLUE   : inverted (reverse) pyramid, apex depth 45mm,
                wall angle A_BLU auto = atan(cell inradius / 45) so the
                apex lands exactly at the triangle centroid.

All dimensions in mm. Everything is parametric — edit PARAMETERS below and
re-run. Outputs:
  * timber_lattice_300mm.dxf   (AutoCAD file, mm, colored layers + legend)
  * preview_2d.png             (top view)
  * preview_3d.png             (3D relief view)
"""
import math
import os
from ezdxf import new as new_doc
from ezdxf.enums import TextEntityAlignment
from ezdxf import zoom

# ----------------------------------------------------------------------
# PARAMETERS  (edit here, then re-run)
# ----------------------------------------------------------------------
S         = 140.0 / 3.0      # lattice triangle side; hexagon of 3 rings inscribed in Ø280
R_OUT     = 150.0            # frame ring outer radius  (Ø300)
R_IN      = 140.0            # frame ring inner radius  (Ø280)
RING_H    = 5.0              # frame ring height above the RED level
D_RED     = 5.0              # red triangles: flat pocket depth
D_YEL     = 15.0             # yellow triangles: flat pocket depth
A_YEL     = 30.0             # yellow pyramid wall angle from vertical (deg)
D_BLU     = 45.0             # blue triangles: inverted-pyramid apex depth
STOCK     = 300.0            # stock square size

OUT_DIR   = os.path.dirname(os.path.abspath(__file__))
DXF_FILE  = os.path.join(OUT_DIR, "timber_lattice_300mm.dxf")
PREVIEW2D = os.path.join(OUT_DIR, "preview_2d.png")
PREVIEW3D = os.path.join(OUT_DIR, "preview_3d.png")

# ACI colors
ACI_FRAME = 7       # white/black
ACI_RED   = 1
ACI_YEL   = 2
ACI_BLU   = 5
ACI_GUIDE = 8
ACI_DIM   = 3
ACI_NOTE  = 6
ACI_STOCK = 9

# ----------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------
SQ3  = math.sqrt(3.0)
def T(a):                     # deg -> rad
    return math.radians(a)

def vadd(a, b): return (a[0] + b[0], a[1] + b[1])
def vsub(a, b): return (a[0] - b[0], a[1] - b[1])
def vlen(a):   return math.hypot(a[0], a[1])
def vnorm(a):
    l = vlen(a)
    return (a[0] / l, a[1] / l) if l else (0.0, 0.0)
def vscale(a, k): return (a[0] * k, a[1] * k)
def vrot(a, deg):
    r = T(deg)
    c, s = math.cos(r), math.sin(r)
    return (a[0] * c - a[1] * s, a[0] * s + a[1] * c)

def inradius(side):
    """inradius of equilateral triangle"""
    return side * SQ3 / 6.0

def centroid(poly):
    n = len(poly)
    x = sum(p[0] for p in poly) / n
    y = sum(p[1] for p in poly) / n
    return (x, y)

def tri_inset(poly, d_inset):
    """inset an equilateral triangle about its centroid by distance d_inset"""
    c = centroid(poly)
    side = vlen(vsub(poly[0], poly[1]))
    k = 1.0 - d_inset / inradius(side)
    return [vadd(c, vscale(vsub(p, c), k)) for p in poly]

# ----------------------------------------------------------------------
# build the triangular-lattice mosaic
# ----------------------------------------------------------------------
def build_cells(side, r_hex):
    """hexagonal triangular tiling, 3 rings, hexagon circumradius = r_hex.
    Returns list of dicts {kind:'up'/'dn', poly:[3 pts], ring:int}"""
    X = (side, 0.0)
    Y = (side / 2.0, side * SQ3 / 2.0)
    def pt(i, j): return (i * X[0] + j * Y[0], i * X[1] + j * Y[1])

    cells = []
    for i in range(-6, 7):
        for j in range(-6, 7):
            for kind in ('up', 'dn'):
                if kind == 'up':
                    poly = [pt(i, j), pt(i + 1, j), pt(i, j + 1)]
                else:
                    poly = [pt(i + 1, j + 1), pt(i + 1, j), pt(i, j + 1)]
                c = centroid(poly)
                # hexagon inscribed in circle r_hex: |c| <= r_hex
                if vlen(c) <= r_hex + 1e-9:
                    d = vlen(c)
                    if d < side * 0.9:
                        ring = 0
                    elif d < side * 1.75:
                        ring = 1
                    else:
                        ring = 2
                    cells.append({'kind': kind, 'poly': poly, 'ring': ring, 'd': d})
    return cells

def stretch_outer_to_circle(cells, r_circ):
    """For ring-2 cells, project their outer vertices onto the Ø(2*r_circ) circle
    so the mosaic fills the circle instead of stopping at the hexagon."""
    for cell in cells:
        if cell['ring'] != 2:
            continue
        c = centroid(cell['poly'])
        outer = [p for p in cell['poly'] if vlen(vsub(p, c)) > 0.98 * max(vlen(vsub(q, c)) for q in cell['poly'])]
        # project outer vertices radially (from origin)
        newp = []
        for p in cell['poly']:
            if vlen(p) > r_circ - 1e-6:
                n = vnorm(p)
                newp.append((n[0] * r_circ, n[1] * r_circ))
            else:
                newp.append(p)
        cell['poly'] = newp
    return cells

# ----------------------------------------------------------------------
# DXF writer
# ----------------------------------------------------------------------
def make_dxf(cells, legend_info):
    doc = new_doc('R2010')
    doc.header['$INSUNITS'] = 4          # mm
    doc.header['$MEASUREMENT'] = 1       # metric
    msp = doc.modelspace()

    layers = {
        'FRAME_RING'        : (ACI_FRAME, 'CONTINUOUS'),
        'TRI_RED_D5_FLAT'   : (ACI_RED,   'CONTINUOUS'),
        'TRI_YEL_D15_PYR'   : (ACI_YEL,   'CONTINUOUS'),
        'TRI_BLU_D45_REVPYR': (ACI_BLU,   'CONTINUOUS'),
        'PYR_GUIDES'        : (ACI_GUIDE, 'DASHED'),
        'FIELD'             : (ACI_RED,   'CONTINUOUS'),
        'NOTES'             : (ACI_NOTE,  'CONTINUOUS'),
        'DIMENSIONS'        : (ACI_DIM,   'CONTINUOUS'),
        'STOCK_LIMIT'       : (ACI_STOCK, 'DASHED'),
        'CENTERLINES'       : (ACI_GUIDE, 'CENTER'),
    }
    for name, (color, lt) in layers.items():
        doc.layers.add(name, color=color)
        doc.layers.get(name).dxf.linetype = lt

    def add_poly(poly, layer):
        msp.add_lwpolyline([(p[0], p[1]) for p in poly],
                           format='xy', dxfattribs={'layer': layer, 'closed': True})

    # ---- stock square ----
    s2 = STOCK / 2.0
    msp.add_lwpolyline([(-s2, -s2), (s2, -s2), (s2, s2), (-s2, s2)],
                       format='xy', dxfattribs={'layer': 'STOCK_LIMIT', 'closed': True})

    # ---- frame ring: outer + inner circles ----
    msp.add_circle((0, 0), R_OUT, dxfattribs={'layer': 'FRAME_RING'})
    msp.add_circle((0, 0), R_IN,  dxfattribs={'layer': 'FRAME_RING'})

    # ---- field pocket boundary (whole interior at RED level, D=5) ----
    msp.add_circle((0, 0), R_IN,  dxfattribs={'layer': 'FIELD'})

    # ---- triangles per zone ----
    for cell in cells:
        if cell['ring'] == 0:
            add_poly(cell['poly'], 'TRI_RED_D5_FLAT')
        elif cell['ring'] == 1:
            add_poly(cell['poly'], 'TRI_YEL_D15_PYR')
            # pyramid base at -15 : inset by 15*tan(A_YEL)
            d_inset = D_YEL * math.tan(T(A_YEL))
            base = tri_inset(cell['poly'], d_inset)
            add_poly(base, 'PYR_GUIDES')
            c = centroid(cell['poly'])
            for b in base:
                msp.add_line(b, c, dxfattribs={'layer': 'PYR_GUIDES'})
            msp.add_circle(c, 1.5, dxfattribs={'layer': 'PYR_GUIDES'})
        else:
            add_poly(cell['poly'], 'TRI_BLU_D45_REVPYR')
            c = centroid(cell['poly'])
            for p in cell['poly']:
                msp.add_line(p, c, dxfattribs={'layer': 'PYR_GUIDES'})
            msp.add_circle(c, 1.5, dxfattribs={'layer': 'PYR_GUIDES'})

    # ---- dimensions ----
    dl = 'DIMENSIONS'
    msp.add_diameter_dim(center=(0, 0), radius=R_OUT, angle=45,
                         dxfattribs={'layer': dl}).set_text('Ø300')
    msp.add_diameter_dim(center=(0, 0), radius=R_IN, angle=30,
                         dxfattribs={'layer': dl}).set_text('Ø280')
    # ring width linear dim
    msp.add_linear_dim(base=(R_IN - 12, R_OUT - 6), p1=(R_IN, R_OUT - 6), p2=(R_OUT, R_OUT - 6),
                       angle=0, dxfattribs={'layer': dl}).set_text('RING 10')
    # ring height note with leader
    msp.add_line((R_IN - 6, R_OUT - 14), (R_IN - 6, R_OUT - 6),
                 dxfattribs={'layer': 'NOTES'})

    # ---- legend / notes ----
    def text(s, x, y, h=4.0, layer='NOTES', align=TextEntityAlignment.LEFT):
        t = msp.add_text(s, dxfattribs={'layer': layer, 'height': h})
        t.set_placement((x, y), align=align)
        return t

    tx, ty = -R_OUT - 40, R_OUT + 25
    text('TIMBER LATTICE - CNC PANEL  (mm)', tx, ty, 5.0)
    text('LEGEND / COLOURS = DEPTHS:', tx, ty - 10, 4.5)
    text('RED    = flat pocket  D=5mm   (base level)', tx, ty - 16, 4.0)
    text('        = whole interior inside Ø280 = FIELD (pocket to D=5)', tx, ty - 21, 3.5)
    text('YELLOW = pocket D=15mm + pyramid below', tx, ty - 27, 4.0)
    text('        (pyramid wall %.1f deg from vertical, apex ~D=%.1fmm)'
         % (A_YEL, D_YEL + inradius(S) / math.tan(T(A_YEL))), tx, ty - 32, 3.5)
    text('BLUE   = inverted pyramid, apex D=45mm', tx, ty - 38, 4.0)
    text('        (wall %.1f deg from vertical)' % legend_info['A_BLU'], tx, ty - 43, 3.5)
    text('FRAME  = ring width 10mm, raised 5mm above RED level', tx, ty - 49, 4.0)
    text('STOCK  = 300 x 300 (panel Ø300); blank >=50mm thick;', tx, ty - 55, 4.0)
    text('         recommend 320x320 blank for clamping', tx, ty - 60, 3.5)
    text('TRIANGLES: %d  (%d red / %d yellow / %d blue)'
         % (len(cells), legend_info['n_red'], legend_info['n_yel'], legend_info['n_blu']),
         tx, ty - 66, 4.0)
    text('GUIDES (dashed) = pyramid edges / apex. NOT machined.', tx, ty - 72, 3.5)

    # zone sample labels inside the mosaic
    text('RED D5', -34, -10, 3.5, 'TRI_RED_D5_FLAT', TextEntityAlignment.MIDDLE_CENTER)
    text('YEL D15', 0, 60, 3.5, 'TRI_YEL_D15_PYR', TextEntityAlignment.MIDDLE_CENTER)
    text('BLUE D45', 0, 118, 3.5, 'TRI_BLU_D45_REVPYR', TextEntityAlignment.MIDDLE_CENTER)

    # ---- center lines ----
    msp.add_line((-R_OUT - 15, 0), (R_OUT + 15, 0), dxfattribs={'layer': 'CENTERLINES'})
    msp.add_line((0, -R_OUT - 15), (0, R_OUT + 15), dxfattribs={'layer': 'CENTERLINES'})

    doc.saveas(DXF_FILE)
    return DXF_FILE

# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
def main():
    cells = build_cells(S, R_IN)
    cells = stretch_outer_to_circle(cells, R_IN)
    cells.sort(key=lambda c: (c['ring'], c['d']))

    n_red = sum(1 for c in cells if c['ring'] == 0)
    n_yel = sum(1 for c in cells if c['ring'] == 1)
    n_blu = sum(1 for c in cells if c['ring'] == 2)
    inr = inradius(S)
    a_blu = math.degrees(math.atan(inr / D_BLU))
    apex_yel = D_YEL + inr / math.tan(T(A_YEL))
    print('cells: %d total  (%d red / %d yellow / %d blue)' % (len(cells), n_red, n_yel, n_blu))
    print('cell side %.2f  inradius %.2f  circumradius %.2f' % (S, inr, S / SQ3))
    print('BLUE inverted pyramid: wall %.1f deg from vertical (V-bit ~ %.1f deg point)'
          % (a_blu, 2 * a_blu))
    print('YELLOW pyramid: wall %.1f deg from vertical, apex depth %.1f mm'
          % (A_YEL, apex_yel))
    print('max cell centroid radius %.1f  (inner circle %.0f)'
          % (max(c['d'] for c in cells), R_IN))

    legend_info = {'A_BLU': a_blu, 'n_red': n_red, 'n_yel': n_yel, 'n_blu': n_blu}
    path = make_dxf(cells, legend_info)
    print('DXF written:', path)

    # previews
    from previews import render_previews
    render_previews(cells, legend_info)

if __name__ == '__main__':
    main()
