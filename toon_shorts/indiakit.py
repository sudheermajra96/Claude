"""Indian street vehicles + scenery in the 2D+3D house style: auto rickshaw, motorbike with rider, city bus,
small hatchback, cow; colourful shops with signboards, overhead wires, food carts."""
import math
import random

import cairo
import numpy as np

from mkit import *
from truckkit import wheel3, solid

# type: (length, width)
DIMS = {'auto': (2.7, 1.35), 'bike': (2.0, 0.8), 'car': (3.8, 1.7), 'bus': (11.0, 2.5), 'cow': (2.2, 0.9)}


def auto3(ctx, view, x, z, h, t, body='#1c1c22', roof='#f2c230', driver=True):
    """Auto rickshaw: 3 round wheels, black body, yellow canvas roof. Origin = centre."""
    Lf = L(x, z, h)
    d = view.depth((x, 1, z))
    lw = max(1.2, min(3.5, 50 / max(d, 1)))
    if view.ortho:
        fill_poly(ctx, view, [Lf(-0.68, 0, -1.35), Lf(0.68, 0, -1.35), Lf(0.55, 0, 0.9), Lf(0.25, 0, 1.35), Lf(-0.25, 0, 1.35), Lf(-0.55, 0, 0.9)],
                  hexc(roof), OUTL, 3)
        return
    for c in (Lf(0.0, 0.3, 1.0), Lf(-0.62, 0.3, -0.95), Lf(0.62, 0.3, -0.95)):
        wheel3(ctx, view, c, h, 0.3, 0.16)
    b, r = hexc(body), hexc(roof)
    # lower tub (wider at the back) and nose
    solid(ctx, view, Lf, [(-0.68, 0.3, -1.35), (0.68, 0.3, -1.35), (0.55, 0.3, 0.6), (-0.55, 0.3, 0.6)],
          [(-0.68, 0.85, -1.35), (0.68, 0.85, -1.35), (0.55, 0.85, 0.6), (-0.55, 0.85, 0.6)],
          {'back': b, 'front': b, 'left': mix(b, (1, 1, 1), 0.08), 'right': mix(b, (1, 1, 1), 0.08), 'top': hexc('#2a2a33')}, lw)
    solid(ctx, view, Lf, [(-0.55, 0.45, 0.6), (0.55, 0.45, 0.6), (0.22, 0.45, 1.35), (-0.22, 0.45, 1.35)],
          [(-0.5, 1.05, 0.6), (0.5, 1.05, 0.6), (0.18, 0.9, 1.3), (-0.18, 0.9, 1.3)],
          {'back': b, 'front': hexc(roof), 'left': b, 'right': b, 'top': b}, lw)
    # headlight
    p = view.pt(Lf(0, 0.85, 1.33))
    s = view.scale(Lf(0, 0.85, 1.33))
    if p and s:
        ellipse(ctx, p[0], p[1], 0.09 * s, 0.07 * s)
        setc(ctx, hexc('#fff6d8'))
        ctx.fill()
    # posts
    for px, pz in ((-0.62, -1.3), (0.62, -1.3), (-0.5, 0.55), (0.5, 0.55)):
        a, c = view.pt(Lf(px, 0.85, pz)), view.pt(Lf(px * 0.95, 1.75, pz))
        if a and c:
            ctx.move_to(*a)
            ctx.line_to(*c)
            setc(ctx, OUTL)
            ctx.set_line_width(max(1.5, (view.scale(Lf(px, 1.2, pz)) or 10) * 0.05))
            ctx.stroke()
    # driver (head + shoulders) visible under the roof
    if driver:
        c = Lf(0.0, 1.35, 0.2)
        p, s = view.pt(c), view.scale(c)
        if p and s:
            rrect(ctx, p[0] - 0.22 * s, p[1] - 0.02 * s, 0.44 * s, 0.4 * s, 0.1 * s)
            fill_stroke(ctx, hexc('#e9e3d3'), OUTL, max(1, lw * 0.6))
            ellipse(ctx, p[0], p[1] - 0.18 * s, 0.14 * s, 0.16 * s)
            fill_stroke(ctx, hexc('#9c6a4a'), OUTL, max(1, lw * 0.6))
            ctx.arc(p[0], p[1] - 0.22 * s, 0.145 * s, math.pi, 2 * math.pi)
            setc(ctx, hexc('#1d1613'))
            ctx.fill()
    # canvas roof (rounded top) + windshield
    solid(ctx, view, Lf, [(-0.66, 1.72, -1.4), (0.66, 1.72, -1.4), (0.56, 1.72, 0.62), (-0.56, 1.72, 0.62)],
          [(-0.6, 1.92, -1.3), (0.6, 1.92, -1.3), (0.5, 1.88, 0.55), (-0.5, 1.88, 0.55)],
          {'back': r, 'front': r, 'left': mix(r, (0, 0, 0), 0.1), 'right': mix(r, (0, 0, 0), 0.1), 'top': r}, lw)
    fill_poly(ctx, view, [Lf(-0.5, 1.05, 0.6), Lf(0.5, 1.05, 0.6), Lf(0.52, 1.7, 0.58), Lf(-0.52, 1.7, 0.58)], hexc('#9cc6e0'), OUTL, lw * 0.6, 0.55)


def rider(ctx, view, Lf, top, helmet, skin='#9c6a4a', seat_z=-0.15):
    hip = Lf(0, 1.0, seat_z)
    sh = Lf(0, 1.55, seat_z + 0.15)
    hd = Lf(0, 1.78, seat_z + 0.2)
    p, s = view.pt(sh), view.scale(sh)
    q = view.pt(hip)
    if not p or not s or not q:
        return
    rrect(ctx, p[0] - 0.21 * s, p[1] - 0.05 * s, 0.42 * s, (q[1] - p[1]) + 0.1 * s, 0.1 * s)
    fill_stroke(ctx, hexc(top), OUTL, max(1, s / 50))
    hp = view.pt(hd)
    if hp:
        ellipse(ctx, hp[0], hp[1], 0.15 * s, 0.16 * s)
        fill_stroke(ctx, hexc(helmet) if helmet else hexc(skin), OUTL, max(1, s / 50))
        if not helmet:
            ctx.arc(hp[0], hp[1] - 0.04 * s, 0.15 * s, math.pi, 2 * math.pi)
            setc(ctx, hexc('#1d1613'))
            ctx.fill()


def bike3(ctx, view, x, z, h, t, col='#e0393e', top='#3a7bd5', helmet='#f4f4f6', pillion=None):
    Lf = L(x, z, h)
    if view.ortho:
        fill_poly(ctx, view, [Lf(-0.35, 0, -1.0), Lf(0.35, 0, -1.0), Lf(0.35, 0, 1.0), Lf(-0.35, 0, 1.0)], hexc(col), OUTL, 2)
        return
    d = view.depth((x, 1, z))
    lw = max(1.2, min(3.5, 45 / max(d, 1)))
    for wz in (-0.68, 0.68):
        wheel3(ctx, view, Lf(0, 0.32, wz), h, 0.32, 0.1)
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    lbox(ctx, view, Lf, h, -0.16, 0.16, 0.45, 0.85, -0.55, 0.55, allc(hexc(col)), lw)
    lbox(ctx, view, Lf, h, -0.17, 0.17, 0.85, 0.98, -0.6, 0.15, allc(hexc('#1c1c22')), lw)
    lbox(ctx, view, Lf, h, -0.36, 0.36, 1.05, 1.1, 0.5, 0.56, allc(hexc('#3a3d48')), lw)
    if pillion:
        rider(ctx, view, Lf, pillion, None, seat_z=-0.55)
    rider(ctx, view, Lf, top, helmet, seat_z=-0.05)
    p = view.pt(Lf(0, 0.95, 0.62))
    s = view.scale(Lf(0, 0.95, 0.62))
    if p and s:
        ellipse(ctx, p[0], p[1], 0.08 * s, 0.07 * s)
        setc(ctx, hexc('#fff6d8'))
        ctx.fill()


def bus3(ctx, view, x, z, h, t):
    Lf = L(x, z, h)
    if view.ortho:
        fill_poly(ctx, view, [Lf(-1.25, 0, -5.5), Lf(1.25, 0, -5.5), Lf(1.25, 0, 5.5), Lf(-1.25, 0, 5.5)], hexc('#c8312f'), OUTL, 3)
        return
    d = view.depth((x, 1.5, z))
    lw = max(1.4, min(4, 70 / max(d, 1)))
    for wz in (-3.6, 3.6):
        for wx in (-1.05, 1.05):
            wheel3(ctx, view, Lf(wx, 0.5, wz), h, 0.5, 0.35)
    red, cream = hexc('#c8312f'), hexc('#f2e6c4')
    vis = lbox(ctx, view, Lf, h, -1.25, 1.25, 0.4, 3.1, -5.5, 5.5,
               {'front': red, 'back': red, 'left': mix(red, (0, 0, 0), 0.12), 'right': mix(red, (0, 0, 0), 0.05), 'top': hexc('#e8e1d0')}, lw)
    for face, dx in (('left', -1.26), ('right', 1.26)):
        if face in vis:
            face_rect(ctx, view, Lf, face, -5.2, 5.2, 1.9, 2.8, dx, cream)
            for k in range(8):
                face_rect(ctx, view, Lf, face, -5.0 + k * 1.28, -4.0 + k * 1.28, 1.98, 2.72, dx * 1.002, hexc('#2d3f55'))
    if 'back' in vis:
        face_rect(ctx, view, Lf, 'back', -1.0, 1.0, 1.9, 2.8, -5.51, hexc('#2d3f55'))
        for sx in (-1, 1):
            face_rect(ctx, view, Lf, 'back', sx * 1.0 - 0.15, sx * 1.0 + 0.15, 0.7, 1.0, -5.52, hexc('#b01818'))
    if 'front' in vis:
        face_rect(ctx, view, Lf, 'front', -1.1, 1.1, 1.6, 2.8, 5.51, hexc('#2d3f55'))
        face_rect(ctx, view, Lf, 'front', -1.0, 1.0, 2.85, 3.05, 5.52, hexc('#ffb21e'))


def cow3(ctx, view, x, z, h, t):
    Lf = L(x, z, h)
    if view.ortho:
        fill_poly(ctx, view, [Lf(-0.4, 0, -1.0), Lf(0.4, 0, -1.0), Lf(0.4, 0, 1.0), Lf(-0.4, 0, 1.0)], hexc('#f4f2ec'), OUTL, 2)
        return
    d = view.depth((x, 1, z))
    lw = max(1.2, min(3.5, 45 / max(d, 1)))
    white = hexc('#f4f2ec')
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    for lx in (-0.25, 0.25):
        for lz in (-0.7, 0.6):
            lbox(ctx, view, Lf, h, lx - 0.07, lx + 0.07, 0, 0.75, lz - 0.07, lz + 0.07, allc(mix(white, (0, 0, 0), 0.1)), lw)
    lbox(ctx, view, Lf, h, -0.4, 0.4, 0.7, 1.35, -0.9, 0.85, {'front': white, 'back': white, 'left': mix(white, (0, 0, 0), 0.06),
                                                           'right': mix(white, (0, 0, 0), 0.03), 'top': white}, lw)
    lbox(ctx, view, Lf, h, -0.22, 0.22, 1.35, 1.6, 0.35, 0.75, {'front': white, 'back': white, 'left': mix(white, (0, 0, 0), 0.08),
                                                             'right': mix(white, (0, 0, 0), 0.04), 'top': white}, lw)   # zebu hump
    sw = math.sin(t * 2.0) * 0.15
    lbox(ctx, view, Lf, h, -0.18 + sw, 0.18 + sw, 1.05, 1.55, 0.85, 1.35, allc(white), lw)
    for sx in (-1, 1):
        a, c = view.pt(Lf(sx * 0.12 + sw, 1.55, 1.1)), view.pt(Lf(sx * 0.28 + sw, 1.8, 1.05))
        if a and c:
            ctx.move_to(*a)
            ctx.line_to(*c)
            setc(ctx, hexc('#8a6a4a'))
            ctx.set_line_width(max(2, (view.scale(Lf(0, 1.6, 1.1)) or 10) * 0.06))
            ctx.stroke()
    a, c = view.pt(Lf(0, 1.3, -0.9)), view.pt(Lf(0.05, 0.75, -1.05))
    if a and c:
        ctx.move_to(*a)
        ctx.line_to(*c)
        setc(ctx, OUTL)
        ctx.set_line_width(2)
        ctx.stroke()


DRAW = {'auto': lambda ctx, v, a, x, z, h, t: auto3(ctx, v, x, z, h, t, a.body, a.roof),
        'bike': lambda ctx, v, a, x, z, h, t: bike3(ctx, v, x, z, h, t, a.col, a.top, a.helmet, a.pillion),
        'car': lambda ctx, v, a, x, z, h, t: draw_car_round(ctx, v, x, z, h, a.col, t),
        'bus': lambda ctx, v, a, x, z, h, t: bus3(ctx, v, x, z, h, t),
        'cow': lambda ctx, v, a, x, z, h, t: cow3(ctx, v, x, z, h, t)}


class IV:
    """Indian traffic agent: kind, x key, speed, anchored z."""

    def __init__(self, kind, x, speed, t_anchor, z_anchor, col='#3a7bd5', heading=0.0, **kw):
        self.kind = kind
        self.tr = Track(x, speed, t_anchor, z_anchor, col, t0=kw.get('t0', -3), t1=kw.get('t1', 36))
        self.col, self.h0 = col, heading
        self.body, self.roof = kw.get('body', '#1c1c22'), kw.get('roof', '#f2c230')
        self.top, self.helmet, self.pillion = kw.get('top', '#3a7bd5'), kw.get('helmet', '#f4f4f6'), kw.get('pillion')
        self.brake = lambda t: 0.0
        self.blink = lambda t: None

    def pose(self, t):
        x, z, h = self.tr.pose(t)
        return x, z, h + self.h0

    def speed(self, t):
        return self.tr.speed(t)

    def steer(self, t):
        return self.tr.steer(t)

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        return [((x, 1.0, z), lambda: DRAW[self.kind](ctx, view, self, x, z, h, t))]


# ------------------------------------------------------------------ scenery
SHOP_COLS = ['#f2a541', '#e05d5d', '#56b38a', '#3a7bd5', '#f4d35e', '#ee964b', '#c77dff', '#2ec4b6', '#ff6b9d']
SIGNS = ['CHAI', 'MOBILE', 'SWEETS', 'PHARMACY', 'TAILOR', 'JUICE', 'VADA PAV', 'BOOKS', 'SAREES', 'HOTEL']
SIGN_COLS = ['#d62828', '#1f7a43', '#2b5fb3', '#f2c230', '#7a4fd0', '#e8590c']


def shop_signs(ctx, view, bld, idx):
    x0, x1, z0, z1, h, col = bld
    fx = x0 if x0 > 0 else x1
    if (view.pos[0] - fx) * (-1 if x0 > 0 else 1) <= 0 or view.ortho:
        return
    Lf = lambda a, b, c: (a, b, c)
    face = 'left' if x0 > 0 else 'right'
    d = fx - 0.06 if x0 > 0 else fx + 0.06
    nseg = max(1, int((z1 - z0) / 6))
    for k in range(nseg):
        a = z0 + (z1 - z0) * k / nseg + 0.4
        b = z0 + (z1 - z0) * (k + 1) / nseg - 0.4
        sc = hexc(SIGN_COLS[(idx + k) % len(SIGN_COLS)])
        face_rect(ctx, view, Lf, face, a, b, 3.0, 4.1, d, sc)
        face_rect(ctx, view, Lf, face, a + 0.2, b - 0.2, 0.0, 2.6, d, hexc('#3a3d48'))
        face_rect(ctx, view, Lf, face, a + 0.4, b - 0.4, 0.3, 2.4, d - (0.01 if x0 > 0 else -0.01), hexc('#f2e6c4'))
        c = ((d, 3.55, (a + b) / 2))
        p, s = view.pt(c), view.scale(c)
        if p and s and s > 9:
            pa, pb = view.pt((d, 3.55, a)), view.pt((d, 3.55, b))
            if pa and pb:
                ang = math.atan2(pb[1] - pa[1], pb[0] - pa[0])
                if abs(ang) > math.pi / 2:
                    ang += math.pi
                ctx.save()
                ctx.translate(*p)
                ctx.rotate(ang)
                ctx.scale(1, 1)
                txt = SIGNS[(idx * 3 + k) % len(SIGNS)]
                w = abs(pb[0] - pa[0]) + abs(pb[1] - pa[1])
                size = min(s * 0.62, w / max(4, len(txt)) * 1.4)
                text_center(ctx, txt, 0, size * 0.35, size, (1, 1, 1))
                ctx.restore()


def wires(ctx, view, ez):
    if view.ortho:
        return
    poles = [z for z in np.arange(-400, 900, 26) if ez - 40 < z < ez + 160]
    for sx in (-1, 1):
        for z in poles:
            b, tp, s = view.pt((sx * 12.6, 0, z)), view.pt((sx * 12.6, 8.0, z)), view.scale((sx * 12.6, 0, z))
            if b and tp and s:
                ctx.rectangle(b[0] - 0.08 * s, tp[1], 0.16 * s, b[1] - tp[1])
                fill_stroke(ctx, hexc('#6a6f7c'), OUTL, max(1, s / 60))
        for za, zb in zip(poles, poles[1:]):
            for k, y in enumerate((7.8, 7.3, 6.9)):
                pts = [view.pt((sx * 12.6, y - 0.6 * math.sin(math.pi * u), za + (zb - za) * u)) for u in np.linspace(0, 1, 8)]
                if all(pts):
                    ctx.move_to(*pts[0])
                    for q in pts[1:]:
                        ctx.line_to(*q)
                    setc(ctx, hexc('#2a2a33'))
                    ctx.set_line_width(1.5)
                    ctx.stroke()
    for z in poles[::2]:
        pts = [view.pt((-12.6 + 25.2 * u, 7.4 - 1.2 * math.sin(math.pi * u), z)) for u in np.linspace(0, 1, 12)]
        if all(pts):
            ctx.move_to(*pts[0])
            for q in pts[1:]:
                ctx.line_to(*q)
            setc(ctx, hexc('#2a2a33'))
            ctx.set_line_width(1.5)
            ctx.stroke()


def food_cart(ctx, view, x, z, col):
    if view.ortho:
        return
    Lf = lambda a, b, c: (a, b, c)
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    lbox(ctx, view, Lf, 0.0, x - 0.6, x + 0.6, 0.4, 1.0, z - 0.9, z + 0.9, allc(hexc('#c98b4a')), 2)
    for wz in (-0.5, 0.5):
        wheel3(ctx, view, (x - 0.62, 0.3, z + wz), 0.0, 0.3, 0.08)
    b, tp, s = view.pt((x, 1.0, z)), view.pt((x, 2.4, z)), view.scale((x, 2.4, z))
    if b and tp and s:
        ctx.move_to(*b)
        ctx.line_to(*tp)
        setc(ctx, OUTL)
        ctx.set_line_width(max(1, s * 0.04))
        ctx.stroke()
        ctx.move_to(tp[0] - 1.2 * s, tp[1] + 0.3 * s)
        ctx.curve_to(tp[0] - 0.6 * s, tp[1] - 0.4 * s, tp[0] + 0.6 * s, tp[1] - 0.4 * s, tp[0] + 1.2 * s, tp[1] + 0.3 * s)
        ctx.close_path()
        fill_stroke(ctx, hexc(col), OUTL, max(1, s / 50))


def mumbai_sky(ctx, view):
    if view.ortho:
        return
    towers(ctx, view, 1500, -500, 500, 30, 60, 210, seed=19, base='#a8a39a', haze='#f2e6d6')
    far_line(ctx, view, 2200, lambda x: 40 + 25 * math.sin(x / 160), col='#b9b09a')
