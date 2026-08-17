#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render 2D top view + 3D relief previews of the timber-lattice design."""
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle as MplCircle, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from generate_dxf import (S, R_OUT, R_IN, RING_H, D_RED, D_YEL, A_YEL, D_BLU,
                          inradius, centroid, tri_inset, PREVIEW2D, PREVIEW3D)

RED_C   = '#d62728'
YEL_C   = '#f7b731'
BLU_C   = '#2b6cb0'
FRM_C   = '#b0b0b0'
FIELD_C = '#f0c4c4'

def cell_poly(cell, r_circ):
    """cell polygon with ring-2 outer vertices stretched onto circle (mirror of generator)."""
    if cell['ring'] != 2:
        return cell['poly']
    out = []
    for p in cell['poly']:
        if math.hypot(p[0], p[1]) > r_circ - 1e-6:
            n = math.hypot(p[0], p[1])
            out.append((p[0] / n * r_circ, p[1] / n * r_circ))
        else:
            out.append(p)
    return out

def render_previews(cells, legend_info):
    r_circ = R_IN
    polys = {0: [], 1: [], 2: []}
    for c in cells:
        polys[c['ring']].append(cell_poly(c, r_circ))

    # ------------------------------------------------------------ 2D
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.add_patch(MplCircle((0, 0), R_OUT, fill=False, ec='black', lw=2.5))
    ax.add_patch(MplCircle((0, 0), R_IN,  fill=False, ec='black', lw=2.0))
    for poly in polys[2]:
        ax.add_patch(Polygon(poly, closed=True, facecolor=BLU_C, edgecolor='black', lw=0.6))
    for poly in polys[1]:
        ax.add_patch(Polygon(poly, closed=True, facecolor=YEL_C, edgecolor='black', lw=0.6))
    for poly in polys[0]:
        ax.add_patch(Polygon(poly, closed=True, facecolor=RED_C, edgecolor='black', lw=0.6))
    # frame annulus
    theta = [i / 100 * 2 * math.pi for i in range(101)]
    fx = [R_OUT * math.cos(t) for t in theta] + [R_IN * math.cos(t) for t in theta[::-1]]
    fy = [R_OUT * math.sin(t) for t in theta] + [R_IN * math.sin(t) for t in theta[::-1]]
    ax.add_patch(Polygon(list(zip(fx, fy)), closed=True, facecolor=FRM_C, edgecolor='none', zorder=1))
    ax.add_patch(MplCircle((0, 0), R_IN, fill=False, ec='black', lw=1.5, zorder=2))
    ax.add_patch(MplCircle((0, 0), R_OUT, fill=False, ec='black', lw=2.5, zorder=2))
    ax.set_xlim(-R_OUT - 30, R_OUT + 30)
    ax.set_ylim(-R_OUT - 30, R_OUT + 30)
    ax.set_aspect('equal')
    ax.set_title('TIMBER LATTICE — TOP VIEW (Ø300 panel)')
    handles = [Rectangle((0, 0), 1, 1, facecolor=RED_C, edgecolor='k'),
               Rectangle((0, 0), 1, 1, facecolor=YEL_C, edgecolor='k'),
               Rectangle((0, 0), 1, 1, facecolor=BLU_C, edgecolor='k'),
               Rectangle((0, 0), 1, 1, facecolor=FRM_C, edgecolor='k')]
    ax.legend(handles, ['RED  D=5mm flat', 'YELLOW  D=15mm + pyramid',
                        'BLUE  D=45mm rev-pyramid', 'FRAME ring +5mm'],
              loc='upper right', fontsize=9)
    fig.tight_layout()
    fig.savefig(PREVIEW2D, dpi=150)
    plt.close(fig)
    print('preview 2D:', PREVIEW2D)

    # ------------------------------------------------------------ 3D
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=32, azim=-60)

    def face(pts, color, alpha=1.0, ec='k', lw=0.5, zorder=3):
        ax.add_collection3d(Poly3DCollection([pts], facecolor=color,
                                             edgecolor=ec, linewidth=lw,
                                             alpha=alpha, zsort='average'))

    def quad(a, b, c_, d, color):
        face([a, b, c_, d], color)

    for poly in polys[2]:                       # BLUE inverted pyramid
        c = centroid(poly)
        apex = (c[0], c[1], -D_BLU)
        for i in range(3):
            p0, p1 = poly[i], poly[(i + 1) % 3]
            face([(p0[0], p0[1], 0), (p1[0], p1[1], 0), apex], BLU_C)
    for poly in polys[1]:                       # YELLOW pocket + pyramid
        c = centroid(poly)
        d_inset = D_YEL * math.tan(math.radians(A_YEL))
        base = tri_inset(poly, d_inset)
        apex = (c[0], c[1], -(D_YEL + inradius(S) / math.tan(math.radians(A_YEL))))
        # walls 0 -> -15
        for i in range(3):
            p0, p1 = poly[i], poly[(i + 1) % 3]
            face([(p0[0], p0[1], 0), (p1[0], p1[1], 0),
                  (p1[0], p1[1], -D_YEL), (p0[0], p0[1], -D_YEL)], YEL_C, 0.95)
        # floor -15 (visible rim)
        face([(p[0], p[1], -D_YEL) for p in poly], YEL_C, 0.95)
        # pyramid faces
        for i in range(3):
            b0, b1 = base[i], base[(i + 1) % 3]
            face([(b0[0], b0[1], -D_YEL), (b1[0], b1[1], -D_YEL), apex], YEL_C)
    for poly in polys[0]:                       # RED flat pockets
        face([(p[0], p[1], -D_RED) for p in poly], RED_C)
        for i in range(3):
            p0, p1 = poly[i], poly[(i + 1) % 3]
            face([(p0[0], p0[1], 0), (p1[0], p1[1], 0),
                  (p1[0], p1[1], -D_RED), (p0[0], p0[1], -D_RED)], RED_C, 0.9)

    # frame ring: outer wall, top, inner wall
    n = 96
    th = [i / n * 2 * math.pi for i in range(n + 1)]
    for i in range(n):
        t0, t1 = th[i], th[i + 1]
        o0 = (R_OUT * math.cos(t0), R_OUT * math.sin(t0))
        o1 = (R_OUT * math.cos(t1), R_OUT * math.sin(t1))
        i0 = (R_IN * math.cos(t0), R_IN * math.sin(t0))
        i1 = (R_IN * math.cos(t1), R_IN * math.sin(t1))
        face([(o0[0], o0[1], RING_H), (o1[0], o1[1], RING_H),
              (o1[0], o1[1], 0), (o0[0], o0[1], 0)], FRM_C, 0.97)
        face([(i0[0], i0[1], RING_H), (i1[0], i1[1], RING_H),
              (i1[0], i1[1], 0), (i0[0], i0[1], 0)], FRM_C, 0.97)
        face([(o0[0], o0[1], RING_H), (o1[0], o1[1], RING_H),
              (i1[0], i1[1], RING_H), (i0[0], i0[1], RING_H)], FRM_C, 0.97)

    # field gaps (between hexagon edges and inner circle) at RED level
    hex_pts = [(R_IN * math.cos(k * math.pi / 3 - math.pi / 2),
                R_IN * math.sin(k * math.pi / 3 - math.pi / 2)) for k in range(6)]
    # actually hexagon vertices of the tiling: at angles -90, -30, 30, 90, 150, 210
    for k in range(6):
        a0 = math.pi / 2 + k * math.pi / 3
        a1 = math.pi / 2 + (k + 1) * math.pi / 3
        p0 = hex_pts[k]
        p1 = hex_pts[(k + 1) % 6]
        arc = [(R_IN * math.cos(t), R_IN * math.sin(t))
               for t in [a0 + (a1 - a0) * j / 12 for j in range(13)]]
        poly = [p0] + arc + [p1]
        face([(p[0], p[1], -D_RED) for p in poly], FIELD_C, 0.95)
        for i in range(len(poly) - 1):
            q0, q1 = poly[i], poly[i + 1]
            face([(q0[0], q0[1], 0), (q1[0], q1[1], 0),
                  (q1[0], q1[1], -D_RED), (q0[0], q0[1], -D_RED)], FIELD_C, 0.9)

    ax.set_xlim(-R_OUT - 5, R_OUT + 5)
    ax.set_ylim(-R_OUT - 5, R_OUT + 5)
    ax.set_zlim(-D_BLU - 5, RING_H + 5)
    ax.set_box_aspect((1, 1, 0.85))
    ax.set_axis_off()
    ax.set_title('TIMBER LATTICE — 3D RELIEF VIEW\n'
                 'RED -5 | YELLOW -15+pyramid(apex %.0f) | BLUE -45 rev-pyramid | FRAME +5'
                 % (D_YEL + inradius(S) / math.tan(math.radians(A_YEL))))
    fig.tight_layout()
    fig.savefig(PREVIEW3D, dpi=150)
    plt.close(fig)
    print('preview 3D:', PREVIEW3D)
