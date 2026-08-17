#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXPORT FOR ART CAM 2018
=======================
ART CAM 2018 reads DXF best as an old-style AutoCAD **R12 (AC1009)** file that
contains only simple primitives. This exporter writes the same timber-lattice
design as:
    * POLYLINE (closed 2D polylines)  -> all triangle outlines + stock square
    * CIRCLE                          -> frame ring (Ø300 / Ø280) + field Ø280
    * LINE                            -> pyramid guide edges (PYR_GUIDES layer)
    * POINT                           -> pyramid apexes
    * TEXT (plain ASCII, LEFT)        -> legend notes
It intentionally emits NO: LWPOLYLINE, DIMENSION, MTEXT, HATCH, SPLINE
(those are the entities that make ART CAM choke or import garbage).

Output: timber_lattice_ART_CAM_R12.dxf  (1 unit = 1 mm)
"""
import math
import os
from ezdxf import new as new_doc

from generate_dxf import (S, R_OUT, R_IN, STOCK, D_YEL, A_YEL, inradius,
                          T, centroid, tri_inset,
                          build_cells, stretch_outer_to_circle)

OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "timber_lattice_ART_CAM_R12.dxf")

# ACI colors (same as main file)
ACI_FRAME = 7
ACI_RED   = 1
ACI_YEL   = 2
ACI_BLU   = 5
ACI_GUIDE = 8
ACI_NOTE  = 6
ACI_STOCK = 9


def main():
    cells = build_cells(S, R_IN)
    cells = stretch_outer_to_circle(cells, R_IN)
    cells.sort(key=lambda c: (c['ring'], c['d']))

    doc = new_doc('R12')
    doc.header['$LUNITS'] = 2        # decimal, inches or mm per import choice
    doc.header['$LUPREC'] = 2
    doc.header['$MEASUREMENT'] = 1   # metric

    dashed_ok = False
    try:
        doc.linetypes.add('DASHED', pattern=[0.4, -0.25, 0.0, -0.25],
                          description='Dashed __ __ __')
        dashed_ok = True
    except Exception:
        pass

    layers = {
        'FRAME_RING':         (ACI_FRAME, 'CONTINUOUS'),
        'TRI_RED_D5_FLAT':    (ACI_RED,   'CONTINUOUS'),
        'TRI_YEL_D15_PYR':    (ACI_YEL,   'CONTINUOUS'),
        'TRI_BLU_D45_REVPYR': (ACI_BLU,   'CONTINUOUS'),
        'PYR_GUIDES':         (ACI_GUIDE, 'DASHED' if dashed_ok else 'CONTINUOUS'),
        'FIELD':              (ACI_RED,   'CONTINUOUS'),
        'NOTES':              (ACI_NOTE,  'CONTINUOUS'),
        'STOCK_LIMIT':        (ACI_STOCK, 'DASHED' if dashed_ok else 'CONTINUOUS'),
        'CENTERLINES':        (ACI_GUIDE, 'DASHED' if dashed_ok else 'CONTINUOUS'),
    }
    for name, (color, lt) in layers.items():
        doc.layers.add(name, color=color)
        try:
            doc.layers.get(name).dxf.linetype = lt
        except Exception:
            pass

    msp = doc.modelspace()

    def poly(points, layer):
        msp.add_polyline2d([(p[0], p[1]) for p in points], format='xy',
                           close=True, dxfattribs={'layer': layer})

    # ---- stock square (reference only) ----
    s2 = STOCK / 2.0
    poly([(-s2, -s2), (s2, -s2), (s2, s2), (-s2, s2)], 'STOCK_LIMIT')

    # ---- frame ring + field pocket boundary ----
    msp.add_circle((0, 0), R_OUT, dxfattribs={'layer': 'FRAME_RING'})
    msp.add_circle((0, 0), R_IN,  dxfattribs={'layer': 'FRAME_RING'})
    msp.add_circle((0, 0), R_IN,  dxfattribs={'layer': 'FIELD'})

    # ---- triangles by zone ----
    for cell in cells:
        if cell['ring'] == 0:
            poly(cell['poly'], 'TRI_RED_D5_FLAT')
        elif cell['ring'] == 1:
            poly(cell['poly'], 'TRI_YEL_D15_PYR')
            d_inset = D_YEL * math.tan(T(A_YEL))
            base = tri_inset(cell['poly'], d_inset)
            poly(base, 'PYR_GUIDES')
            c = centroid(cell['poly'])
            for b in base:
                msp.add_line(b, c, dxfattribs={'layer': 'PYR_GUIDES'})
            msp.add_point(c, dxfattribs={'layer': 'PYR_GUIDES'})
        else:
            poly(cell['poly'], 'TRI_BLU_D45_REVPYR')
            c = centroid(cell['poly'])
            for p in cell['poly']:
                msp.add_line(p, c, dxfattribs={'layer': 'PYR_GUIDES'})
            msp.add_point(c, dxfattribs={'layer': 'PYR_GUIDES'})

    # ---- center lines ----
    msp.add_line((-R_OUT - 15, 0), (R_OUT + 15, 0),
                 dxfattribs={'layer': 'CENTERLINES'})
    msp.add_line((0, -R_OUT - 15), (0, R_OUT + 15),
                 dxfattribs={'layer': 'CENTERLINES'})

    # ---- notes (plain ASCII text only — ART CAM friendly) ----
    n_red = sum(1 for c in cells if c['ring'] == 0)
    n_yel = sum(1 for c in cells if c['ring'] == 1)
    n_blu = sum(1 for c in cells if c['ring'] == 2)
    a_blu = math.degrees(math.atan(inradius(S) / 45.0))
    apex_yel = D_YEL + inradius(S) / math.tan(T(A_YEL))

    def note(s, x, y, h=4.0):
        t = msp.add_text(s, dxfattribs={'layer': 'NOTES', 'height': h})
        t.set_placement((x, y))
        return t

    tx, ty = -R_OUT - 75, R_OUT + 30
    note('TIMBER LATTICE - CNC PANEL - ALL DIMENSIONS mm', tx, ty, 5.0)
    note('UNITS: 1 unit = 1 mm (select mm at ART CAM import)', tx, ty - 10, 4.0)
    note('COLOURS = DEPTHS:', tx, ty - 18, 4.5)
    note('RED    = flat pocket D=5mm  (base level, whole interior)', tx, ty - 25, 4.0)
    note('YELLOW = pocket D=15mm + pyramid wall 30deg (apex %.1fmm)' % apex_yel,
         tx, ty - 32, 4.0)
    note('BLUE   = inverted pyramid apex D=45mm  (wall %.1fdeg)' % a_blu,
         tx, ty - 39, 4.0)
    note('FRAME  = ring width 10mm (OUTER D300 / INNER D280), +5mm', tx, ty - 46, 4.0)
    note('STOCK  = 300x300, blank thickness >= 50mm', tx, ty - 53, 4.0)
    note('TRIANGLES %d  = %d red + %d yellow + %d blue'
         % (len(cells), n_red, n_yel, n_blu), tx, ty - 60, 4.0)
    note('DASHED PYR_GUIDES = pyramid edges/apex. DO NOT machine.', tx, ty - 67, 3.5)
    note('Generated for ART CAM 2018 (DXF R12/AC1009)', tx, ty - 74, 3.5)

    doc.saveas(OUT_FILE)
    print('ART CAM R12 DXF written:', OUT_FILE)
    print('  triangles: %d red / %d yellow / %d blue' % (n_red, n_yel, n_blu))
    print('  BLUE wall %.1f deg | YELLOW apex %.1f mm' % (a_blu, apex_yel))


if __name__ == '__main__':
    main()
