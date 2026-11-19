"""European (Amsterdam-style) city street in the multi-angle 2D house style: canal houses, canal + boats,
red bike lanes, tram tracks, cars, a parked delivery van, pedestrians, zebra crossing, and our hero on a bike.

World: +Z = direction of travel, +X = right, Y up. Cross-section (X):
  right facades 9.5 | sidewalk 6.5..9.5 | bike lane 4.5..6.3 | car lane 1.2..4.4 | tram -1.2..1.2 |
  car lane -4.4..-1.2 | bike lane -6.3..-4.5 | sidewalk -9.5..-6.5 | canal -24..-9.5 | far facades -24
"""
import math
import random

import cairo
import numpy as np

from toronto import *       # TCam, TopView, fill_poly, gquad, lbox, L, draw_car3, draw_car_top, tree3, kit/engine
import toronto
import life

BIKE_X = 5.4
C_PAVE = hexc('#c9c2b4')
C_ROAD = hexc('#55585f')
C_BIKE = hexc('#b5524a')
C_TRAM = hexc('#8e8a84')
C_CANAL = hexc('#3f7f9e')
C_HELMET = hexc('#5bc0eb')
C_PACK = hexc('#2f6f73')
BRICK = ['#8a4b38', '#a35d43', '#6e3b2e', '#d8c3a0', '#7d7f86', '#b88a5a', '#9c4f3f', '#e0d6c2', '#5f6a7a']
ZV0, ZV1 = 84.0, 89.6          # delivery van in the bike lane
ZC0, ZC1 = 115.5, 119.5        # zebra crossing


# ------------------------------------------------------------- canal houses
def _houses(side, x, seed):
    r = random.Random(seed)
    out = []
    z = -60.0
    while z < 420:
        w = r.uniform(5.0, 7.0)
        h = r.uniform(10.5, 16.0)
        out.append(dict(x=x, z0=z, z1=z + w, h=h, col=hexc(r.choice(BRICK)), gable=r.choice(['step', 'bell', 'neck', 'flat']),
                        floors=int(h // 3.2), side=side))
        z += w
    return out


HOUSES_R = _houses(1, 9.5, 11)
HOUSES_FAR = _houses(-1, -24.0, 22)


def facade(ctx, view, hs):
    x, z0, z1, h, col = hs['x'], hs['z0'], hs['z1'], hs['h'], hs['col']
    if view.ortho:
        depth_x = x + 9 * hs['side']
        fill_poly(ctx, view, [(x, 0, z0), (depth_x, 0, z0), (depth_x, 0, z1), (x, 0, z1)],
                  mix(col, (0.3, 0.3, 0.3), 0.35), OUTL, 2)
        return
    if not fill_poly(ctx, view, [(x, 0, z0), (x, 0, z1), (x, h, z1), (x, h, z0)], col, OUTL, 2):
        return
    zm, w = (z0 + z1) / 2, z1 - z0
    g = hs['gable']
    if g == 'step':
        pts = [(x, h, z0 + 0.3), (x, h + 1.0, z0 + 0.3), (x, h + 1.0, z0 + w * 0.25), (x, h + 2.0, z0 + w * 0.25),
               (x, h + 2.0, z0 + w * 0.4), (x, h + 3.0, z0 + w * 0.4), (x, h + 3.0, z1 - w * 0.4), (x, h + 2.0, z1 - w * 0.4),
               (x, h + 2.0, z1 - w * 0.25), (x, h + 1.0, z1 - w * 0.25), (x, h + 1.0, z1 - 0.3), (x, h, z1 - 0.3)]
    elif g == 'bell':
        pts = [(x, h, z0 + 0.4), (x, h + 1.2, z0 + w * 0.2), (x, h + 2.6, z0 + w * 0.32), (x, h + 3.2, zm),
               (x, h + 2.6, z1 - w * 0.32), (x, h + 1.2, z1 - w * 0.2), (x, h, z1 - 0.4)]
    elif g == 'neck':
        pts = [(x, h, z0 + 0.3), (x, h + 0.8, z0 + w * 0.28), (x, h + 3.0, z0 + w * 0.32), (x, h + 3.4, zm),
               (x, h + 3.0, z1 - w * 0.32), (x, h + 0.8, z1 - w * 0.28), (x, h, z1 - 0.3)]
    else:
        pts = [(x, h, z0), (x, h + 0.6, z0), (x, h + 0.6, z1), (x, h, z1)]
    fill_poly(ctx, view, pts, col, OUTL, 2)
    fill_poly(ctx, view, [(x, h - 0.05, z0), (x, h - 0.05, z1), (x, h + 0.15, z1), (x, h + 0.15, z0)], (0.95, 0.95, 0.92))
    off = -0.03 * hs['side']
    frame, glass = (0.97, 0.97, 0.95), hexc('#2d3f55')
    for f in range(1, hs['floors']):
        y0 = f * 3.2 + 0.7
        for c in range(3):
            a = z0 + w * (0.12 + c * 0.29)
            fill_poly(ctx, view, [(x + off, y0, a), (x + off, y0, a + w * 0.18), (x + off, y0 + 1.9, a + w * 0.18), (x + off, y0 + 1.9, a)], frame)
            fill_poly(ctx, view, [(x + off * 2, y0 + 0.15, a + 0.12), (x + off * 2, y0 + 0.15, a + w * 0.18 - 0.12),
                                  (x + off * 2, y0 + 1.75, a + w * 0.18 - 0.12), (x + off * 2, y0 + 1.75, a + 0.12)], glass)
    fill_poly(ctx, view, [(x + off, 0, z0 + 0.5), (x + off, 0, z0 + 1.6), (x + off, 2.4, z0 + 1.6), (x + off, 2.4, z0 + 0.5)], hexc('#2f3e4f'))
    fill_poly(ctx, view, [(x + off, 0.6, z0 + 2.1), (x + off, 0.6, z1 - 0.4), (x + off, 2.5, z1 - 0.4), (x + off, 2.5, z0 + 2.1)], hexc('#9cc6e0'))


# ------------------------------------------------------------- people & bikes
def ped_bb(ctx, view, x, z, t, top='#e05d5d', pants='#2b3a63', skin='#e8b48f', hair='#3a2316', kid=False,
           walking=True, wave=0.0):
    if view.ortho:
        p = view.pt((x, 0, z))
        r = (0.22 if not kid else 0.17) * view.s
        ellipse(ctx, p[0], p[1], r, r)
        fill_stroke(ctx, hexc(top), OUTL, 3)
        ellipse(ctx, p[0], p[1], r * 0.55, r * 0.55)
        fill_stroke(ctx, hexc(hair), OUTL, 2)
        return
    base = view.pt((x, 0, z))
    s = view.scale((x, 0, z))
    if not base or not s:
        return
    H_ = 1.2 if kid else 1.72
    bx, by = base
    ph = t * 2 * math.pi * 1.6 if walking else 0
    lw = max(1.5, min(4, s / 40))
    leg = H_ * 0.45 * s
    hip = (bx, by - leg)
    for k in (-1, 1):
        fx = bx + k * math.sin(ph) * leg * 0.35
        for col, wdt in ((OUTL, H_ * 0.11 * s + lw), (hexc(pants), H_ * 0.11 * s)):
            ctx.move_to(*hip)
            ctx.line_to(fx, by)
            setc(ctx, col)
            ctx.set_line_width(wdt)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()
    bw, bh = H_ * 0.26 * s, H_ * 0.36 * s
    rrect(ctx, bx - bw / 2, hip[1] - bh, bw, bh + bw * 0.1, bw * 0.35)
    fill_stroke(ctx, hexc(top), OUTL, lw)
    shy = hip[1] - bh * 0.9
    for k in (-1, 1):
        if k > 0 and wave > 0:
            ex_, ey_ = bx + bw * 0.9, shy - bh * 0.6 - math.sin(t * 12) * bw * 0.25
        else:
            ex_, ey_ = bx + k * bw * 0.55 - k * math.sin(ph) * bw * 0.3, hip[1] - bh * 0.1
        for col, wdt in ((OUTL, H_ * 0.07 * s + lw), (hexc(top), H_ * 0.07 * s)):
            ctx.move_to(bx + k * bw * 0.45, shy)
            ctx.line_to(ex_, ey_)
            setc(ctx, col)
            ctx.set_line_width(wdt)
            ctx.stroke()
        ellipse(ctx, ex_, ey_, H_ * 0.035 * s, H_ * 0.035 * s)
        fill_stroke(ctx, hexc(skin), OUTL, lw * 0.6)
    hr = H_ * 0.11 * s
    hx, hy = bx, hip[1] - bh - hr * 0.9
    ellipse(ctx, hx, hy, hr, hr * 1.08)
    fill_stroke(ctx, hexc(skin), OUTL, lw)
    ctx.arc(hx, hy - hr * 0.15, hr * 1.02, math.pi, 2 * math.pi)
    ctx.close_path()
    setc(ctx, hexc(hair))
    ctx.fill()
    for k in (-1, 1):
        ellipse(ctx, hx + k * hr * 0.38, hy + hr * 0.15, hr * 0.1, hr * 0.12)
        setc(ctx, OUTL)
        ctx.fill()
    ctx.arc(hx, hy + hr * 0.35, hr * 0.3, 0.2 * math.pi, 0.8 * math.pi)
    setc(ctx, OUTL)
    ctx.set_line_width(max(1, lw * 0.6))
    ctx.stroke()


def rider_back(ctx, view, x, z, t, arm='bars', pedal=True, brake=0.0):
    """Our hero on a bike, seen from behind. arm: 'bars' | 'left' | 'right'."""
    if view.ortho:
        p = view.pt((x, 0, z))
        s = view.s
        ctx.save()
        ctx.translate(*p)
        rrect(ctx, -0.95 * s, -0.08 * s, 1.9 * s, 0.16 * s, 0.08 * s)
        setc(ctx, OUTL)
        ctx.fill()
        ellipse(ctx, -0.1 * s, 0, 0.32 * s, 0.24 * s)
        fill_stroke(ctx, JACKET, OUTL, 3)
        if arm in ('left', 'right'):
            sgn = -1 if arm == 'left' else 1
            ctx.move_to(-0.05 * s, sgn * 0.2 * s)
            ctx.line_to(-0.05 * s, sgn * 0.9 * s)
            setc(ctx, JACKET)
            ctx.set_line_width(0.14 * s)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()
        ellipse(ctx, 0.0, 0, 0.14 * s, 0.14 * s)
        fill_stroke(ctx, C_HELMET, OUTL, 2)
        ctx.restore()
        return
    base = view.pt((x, 0, z))
    s = view.scale((x, 0, z))
    if not base or not s:
        return
    bx, by = base
    lw = max(1.5, min(5, s / 45))
    U = lambda dx, dy: (bx + dx * s, by - dy * s)
    # wheel (rear, seen edge-on) + mudguard + rear light
    rrect(ctx, *U(-0.035, 0.68), 0.07 * s, 0.68 * s, 0.035 * s)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, lw)
    ctx.move_to(*U(0, 0.36))
    ctx.line_to(*U(0, 0.98))
    setc(ctx, hexc('#2a6f97'))
    ctx.set_line_width(0.05 * s)
    ctx.stroke()
    rrect(ctx, *U(-0.16, 0.74), 0.32 * s, 0.06 * s, 0.02 * s)
    fill_stroke(ctx, hexc('#2a2a33'), OUTL, lw * 0.6)
    lx, ly = U(0, 0.66)
    ellipse(ctx, lx, ly, 0.04 * s, 0.03 * s)
    setc(ctx, RED)
    ctx.fill()
    glow(ctx, lx, ly, min(0.25 * s, 120), RED, 0.5 + 0.4 * brake)
    # legs pedalling
    ph = t * 2 * math.pi * 1.1 if pedal else 0.6
    for k in (-1, 1):
        hip = U(k * 0.11, 1.0)
        fy = 0.32 + 0.14 * math.sin(ph + (0 if k < 0 else math.pi))
        foot = U(k * 0.17, fy)
        knee = U(k * 0.2, (1.0 + fy) / 2 + 0.12)
        for col, wdt in ((OUTL, 0.12 * s + lw), (life.PANTS, 0.12 * s)):
            ctx.move_to(*hip)
            ctx.line_to(*knee)
            ctx.line_to(*foot)
            setc(ctx, col)
            ctx.set_line_width(wdt)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke()
        ellipse(ctx, foot[0], foot[1], 0.07 * s, 0.045 * s)
        fill_stroke(ctx, life.SHOE, OUTL, lw * 0.6)
    ellipse(ctx, *U(0, 0.99), 0.1 * s, 0.04 * s)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, lw * 0.6)
    # handlebar ends
    for k in (-1, 1):
        rrect(ctx, *U(k * 0.33 - 0.04, 1.1), 0.08 * s, 0.05 * s, 0.02 * s)
        setc(ctx, hexc('#1c1c22'))
        ctx.fill()
    # torso + backpack
    ctx.move_to(*U(-0.2, 1.0))
    ctx.curve_to(*U(-0.24, 1.3), *U(-0.24, 1.5), *U(0, 1.56))
    ctx.curve_to(*U(0.24, 1.5), *U(0.24, 1.3), *U(0.2, 1.0))
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, lw)
    # arms
    for k in (-1, 1):
        sh = U(k * 0.2, 1.48)
        side = 'left' if k < 0 else 'right'
        if arm == side:
            hand = U(k * 0.95, 1.44)
            elbow = U(k * 0.58, 1.46)
        else:
            hand = U(k * 0.33, 1.13)
            elbow = U(k * 0.3, 1.3)
        for col, wdt in ((OUTL, 0.1 * s + lw), (JACKET, 0.1 * s)):
            ctx.move_to(*sh)
            ctx.line_to(*elbow)
            ctx.line_to(*hand)
            setc(ctx, col)
            ctx.set_line_width(wdt)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.stroke()
        if arm == side:
            rrect(ctx, hand[0] - (0.02 if k > 0 else 0.13) * s, hand[1] - 0.05 * s, 0.15 * s, 0.09 * s, 0.03 * s)
            fill_stroke(ctx, SKIN, OUTL, lw * 0.6)
        else:
            ellipse(ctx, hand[0], hand[1], 0.045 * s, 0.045 * s)
            fill_stroke(ctx, SKIN, OUTL, lw * 0.6)
    rrect(ctx, *U(-0.15, 1.46), 0.3 * s, 0.36 * s, 0.06 * s)
    fill_stroke(ctx, C_PACK, OUTL, lw)
    # head: curls under a helmet
    hx, hy = U(0, 1.72)
    for dx in (-0.1, 0, 0.1):
        ellipse(ctx, hx + dx * s, hy + 0.06 * s, 0.06 * s, 0.05 * s)
        fill_stroke(ctx, HAIR, OUTL, lw * 0.5)
    for k in (-1, 1):
        ellipse(ctx, hx + k * 0.115 * s, hy + 0.02 * s, 0.025 * s, 0.035 * s)
        fill_stroke(ctx, SKIN, OUTL, lw * 0.5)
    ctx.arc(hx, hy, 0.135 * s, math.pi, 2 * math.pi)
    ctx.close_path()
    fill_stroke(ctx, C_HELMET, OUTL, lw)
    for dx in (-0.06, 0, 0.06):
        rrect(ctx, hx + dx * s - 0.012 * s, hy - 0.11 * s, 0.024 * s, 0.07 * s, 0.01 * s)
        setc(ctx, hexc('#2a6f97'))
        ctx.fill()


def parked_bike(ctx, view, x, z, col='#2a6f97'):
    if view.ortho:
        return
    b = view.pt((x, 0, z))
    s = view.scale((x, 0, z))
    if not b or not s:
        return
    lw = max(1, s / 60)
    for dz in (-0.5, 0.5):
        c = view.pt((x, 0.34, z + dz))
        if c:
            ellipse(ctx, c[0], c[1], 0.06 * s, 0.34 * s)
            setc(ctx, OUTL)
            ctx.set_line_width(lw * 1.5)
            ctx.stroke()
    a, c = view.pt((x, 0.8, z - 0.3)), view.pt((x, 0.85, z + 0.4))
    if a and c:
        ctx.move_to(*a)
        ctx.line_to(*c)
        setc(ctx, hexc(col))
        ctx.set_line_width(lw * 2.5)
        ctx.stroke()


def tram(ctx, view, x, z, h, t):
    Lf = L(x, z, h)
    white, blue = hexc('#f4f4f6'), hexc('#2b5fb3')
    if view.ortho:
        fill_poly(ctx, view, [Lf(-1.2, 0, -12), Lf(1.2, 0, -12), Lf(1.2, 0, 12), Lf(-1.2, 0, 12)], white, OUTL, 3)
        fill_poly(ctx, view, [Lf(-0.5, 0, -11), Lf(0.5, 0, -11), Lf(0.5, 0, 11), Lf(-0.5, 0, 11)], hexc('#c9ccd6'))
        return
    vis = lbox(ctx, view, Lf, h, -1.2, 1.2, 0.35, 3.3, -12, 12,
               {'front': white, 'back': white, 'left': white, 'right': white, 'top': hexc('#c9ccd6')}, 3)
    for face in vis:
        if face in ('left', 'right'):
            d = 1.21 if face == 'right' else -1.21
            face_rect(ctx, view, Lf, face, -11.5, 11.5, 0.6, 1.0, d, blue)
            for i in range(9):
                face_rect(ctx, view, Lf, face, -11 + i * 2.5, -9.4 + i * 2.5, 1.5, 2.7, d, hexc('#2d3f55'))
        if face == 'front':
            face_rect(ctx, view, Lf, 'front', -1.0, 1.0, 1.6, 2.9, 12.01, hexc('#2d3f55'))
            face_rect(ctx, view, Lf, 'front', -1.2, 1.2, 0.6, 1.0, 12.01, blue)
            for k in (-0.8, 0.8):
                face_rect(ctx, view, Lf, 'front', k - 0.15, k + 0.15, 1.15, 1.35, 12.02, hexc('#fff6d8'))
    a, b = view.pt(Lf(0, 3.3, 0)), view.pt(Lf(0, 4.3, -2))
    if a and b:
        ctx.move_to(*a)
        ctx.line_to(*b)
        setc(ctx, OUTL)
        ctx.set_line_width(3)
        ctx.stroke()


def van(ctx, view, t):
    x, z = BIKE_X, (ZV0 + ZV1) / 2
    Lf = L(x, z, 0.0)
    white = hexc('#f2f2f4')
    haz = (t * 1.6) % 1 < 0.5
    if view.ortho:
        fill_poly(ctx, view, [Lf(-1.0, 0, -2.8), Lf(1.0, 0, -2.8), Lf(1.0, 0, 2.8), Lf(-1.0, 0, 2.8)], white, OUTL, 4)
        fill_poly(ctx, view, [Lf(-0.9, 0, 1.6), Lf(0.9, 0, 1.6), Lf(0.9, 0, 2.5), Lf(-0.9, 0, 2.5)], hexc('#2d3f55'))
        if haz:
            for px in (-0.9, 0.9):
                for pz in (-2.7, 2.7):
                    q = view.pt(Lf(px, 0, pz))
                    glow(ctx, q[0], q[1], 1.2 * view.s, AMBER, 0.8)
        return
    for wx in (-0.9, 0.9):
        for wz in (-1.9, 1.9):
            lbox(ctx, view, Lf, 0.0, wx - 0.15, wx + 0.15, 0, 0.7, wz - 0.35, wz + 0.35,
                 {k: hexc('#1c1c22') for k in ('front', 'back', 'left', 'right', 'top')}, 2)
    vis = lbox(ctx, view, Lf, 0.0, -1.0, 1.0, 0.35, 2.7, -2.8, 2.8,
               {'front': white, 'back': white, 'left': mix(white, (0, 0, 0), 0.08), 'right': mix(white, (0, 0, 0), 0.08),
                'top': white}, 3)
    if 'back' in vis:
        face_rect(ctx, view, Lf, 'back', -0.01, 0.01, 0.45, 2.6, -2.81, OUTL)
        face_rect(ctx, view, Lf, 'back', -1.0, 1.0, 1.25, 1.45, -2.81, hexc('#f28c28'))
        for k in (-0.88, 0.88):
            face_rect(ctx, view, Lf, 'back', k - 0.1, k + 0.1, 0.55, 0.85, -2.82,
                      AMBER if haz else hexc('#7a4a00'), AMBER if haz else None, 1.2)
    if 'left' in vis:
        face_rect(ctx, view, Lf, 'left', -2.5, 1.0, 1.25, 1.45, -1.01, hexc('#f28c28'))
        face_rect(ctx, view, Lf, 'left', 1.4, 2.6, 1.5, 2.3, -1.01, hexc('#2d3f55'))


def bike_symbol(ctx, view, x, z):
    for dz in (-0.45, 0.45):
        pts = [(x + 0.28 * math.sin(a), 0.02, z + dz + 0.28 * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 12)]
        sp = view.poly(pts)
        if sp:
            poly(ctx, sp)
            setc(ctx, (1, 1, 1), 0.9)
            ctx.set_line_width(3)
            ctx.stroke()
    a, b = view.pt((x, 0.02, z - 0.45)), view.pt((x, 0.02, z + 0.45))
    if a and b:
        ctx.move_to(*a)
        ctx.line_to(*b)
        setc(ctx, (1, 1, 1), 0.9)
        ctx.set_line_width(4)
        ctx.stroke()


# ------------------------------------------------------------- world
class BikeWorld:
    def __init__(self, dur, speed, lat, arm, cars, peds, crossers, oncoming, trams):
        self.dur, self.speed, self.lat, self.arm_fn = dur, speed, lat, arm
        self.cars_, self.peds, self.crossers, self.oncoming, self.trams = cars, peds, crossers, oncoming, trams
        self._g = np.arange(0, dur + 2, 1 / 120)
        v = np.array([speed(t) for t in self._g])
        self._z = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 / 120)])
        self.headlights = const(0)
        self.blink_left = lambda t: 0.0
        self.blink_right = lambda t: 0.0
        self.ego_brake = const(0)
        self.shake = const(0)

    def ego_z(self, t):
        return float(np.interp(t, self._g, self._z))

    def ego_xz(self, t):
        return BIKE_X + self.lat(t), self.ego_z(t)

    def heading(self, t):
        x0, z0 = self.ego_xz(t - 0.15)
        x1, z1 = self.ego_xz(t + 0.15)
        if math.hypot(x1 - x0, z1 - z0) < 0.05:
            return 0.0
        return math.atan2(x1 - x0, z1 - z0)

    def steer(self, t):
        return 0.0

    def arm(self, t):
        return self.arm_fn(t)


def draw_city(ctx, view, w, t, ego=True, top_overlay=None):
    ez = w.ego_z(t)
    zlo, zhi = ez - 120, ez + 420
    if view.ortho:
        setc(ctx, C_PAVE)
        ctx.paint()
    else:
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 700, 0, hy)
        g.add_color_stop_rgb(0, *hexc('#6fb8ee'))
        g.add_color_stop_rgb(1, *hexc('#dcefff'))
        ctx.set_source(g)
        ctx.rectangle(-50, -50, SW + 100, hy + 52)
        ctx.fill()
        for cx0, cy0, sc0 in ((300, 140, 1.0), (1000, 90, 0.8), (1650, 170, 1.1)):
            for dx, dy, r in ((0, 0, 60), (60, -25, 70), (130, 0, 55), (60, 15, 60)):
                ellipse(ctx, cx0 + dx * sc0, hy - 560 + cy0 + dy * sc0, r * sc0, r * sc0 * 0.8)
            setc(ctx, (1, 1, 1), 0.9)
            ctx.fill()
        setc(ctx, C_PAVE)
        ctx.rectangle(-50, hy, SW + 100, SH + 100 - hy)
        ctx.fill()
    # canal + far houses
    gquad(ctx, view, -24.0, -9.5, zlo, zhi, C_CANAL)
    if not view.ortho:
        for hs in sorted(HOUSES_FAR, key=lambda h: -h['z0']):
            if hs['z1'] > zlo and hs['z0'] < zhi:
                facade(ctx, view, hs)
    gquad(ctx, view, -9.7, -9.5, zlo, zhi, hexc('#7d6f63'))
    # street surfaces
    gquad(ctx, view, -6.5, 6.5, zlo, zhi, C_ROAD)
    gquad(ctx, view, 4.5, 6.3, zlo, zhi, C_BIKE)
    gquad(ctx, view, -6.3, -4.5, zlo, zhi, C_BIKE)
    gquad(ctx, view, -1.2, 1.2, zlo, zhi, C_TRAM)
    for rx in (-0.95, -0.25, 0.25, 0.95):
        gquad(ctx, view, rx - 0.04, rx + 0.04, zlo, zhi, hexc('#c7c9cf'), 0.01)
    gquad(ctx, view, 6.3, 6.5, zlo, zhi, hexc('#9a958c'))
    gquad(ctx, view, -6.5, -6.3, zlo, zhi, hexc('#9a958c'))
    for xx in (4.4, -4.4):
        gquad(ctx, view, xx - 0.07, xx + 0.07, zlo, zhi, C_LINE, 0.01)
    for k in range(int(zlo // 30), int(zhi // 30) + 1):
        if not (ZC0 - 6 < k * 30 < ZC1 + 4) and not (ZV0 - 3 < k * 30 < ZV1 + 3):
            bike_symbol(ctx, view, BIKE_X, k * 30.0) if not view.ortho else None
    # zebra
    for i in range(14):
        x0 = -6.4 + i * 0.95
        gquad(ctx, view, x0, x0 + 0.5, ZC0, ZC1, (0.98, 0.98, 0.98), 0.012)
    if top_overlay:
        top_overlay(ctx, view)
    items = []
    if not view.ortho:
        for hs in HOUSES_R:
            if hs['z1'] > zlo and hs['z0'] < zhi:
                items.append(((hs['x'], 6, (hs['z0'] + hs['z1']) / 2), lambda hs=hs: facade(ctx, view, hs)))
    else:
        for hs in HOUSES_R + HOUSES_FAR:
            if hs['z1'] > zlo and hs['z0'] < zhi:
                items.append(((hs['x'], 0, hs['z0']), lambda hs=hs: facade(ctx, view, hs)))
    for k in range(int(zlo // 13), int(zhi // 13) + 1):
        zz = k * 13.0 + 4
        if ZC0 - 3 < zz < ZC1 + 3:
            continue
        for xx in (7.7, -8.0):
            items.append(((xx, 1.5, zz), lambda xx=xx, zz=zz: tree3(ctx, view, xx, zz, 1.3 if not view.ortho else 0.8, int(zz) % 3)))
        items.append(((8.9, 0.5, zz + 5), lambda zz=zz: parked_bike(ctx, view, 8.9, zz + 5, '#2a6f97' if int(zz) % 2 else '#c0392b')))
    # tram wire poles
    if not view.ortho:
        for k in range(int(zlo // 30), int(zhi // 30) + 1):
            zz = k * 30.0
            for xx in (-6.8, 6.8):
                items.append(((xx, 3, zz), lambda xx=xx, zz=zz: pole(ctx, view, xx, zz)))
    items.append(((BIKE_X, 1.3, (ZV0 + ZV1) / 2), lambda: van(ctx, view, t)))
    for c in w.cars_:
        x, z = c['x'], ez + c['rel'](t)
        if zlo < z < zhi:
            items.append(((x, 0.8, z), lambda x=x, z=z, col=c['col']: (draw_car_top(ctx, view, x, z, 0.0, col, t) if view.ortho
                                                                       else draw_car3(ctx, view, x, z, 0.0, col, t))))
    for c in w.oncoming:
        x, z = c['x'], c['z0'] - c['v'] * t
        if zlo < z < zhi:
            items.append(((x, 0.8, z), lambda x=x, z=z, col=c['col']: (draw_car_top(ctx, view, x, z, math.pi, col, t) if view.ortho
                                                                       else draw_car3(ctx, view, x, z, math.pi, col, t))))
    for tr in w.trams:
        z = tr['z0'] - tr['v'] * t
        if zlo - 15 < z < zhi:
            items.append(((tr['x'], 1.5, z), lambda z=z, x=tr['x']: tram(ctx, view, x, z, math.pi, t)))
    for p in w.peds:
        z = p['z0'] + p['v'] * t
        items.append(((p['x'], 0.9, z), lambda p=p, z=z: ped_bb(ctx, view, p['x'], z, t, p['top'], p.get('pants', '#2b3a63'),
                                                                p.get('skin', '#e8b48f'), p.get('hair', '#3a2316'))))
    for p in w.crossers:
        x = p['x'](t)
        items.append(((x, 0.9, p['z']), lambda p=p, x=x: ped_bb(ctx, view, x, p['z'], t, p['top'], p.get('pants', '#2b3a63'),
                                                                p.get('skin', '#e8b48f'), p.get('hair', '#3a2316'), p.get('kid', False),
                                                                p['walking'](t), p.get('wave', lambda t: 0)(t))))
    if ego:
        ex, ezz = w.ego_xz(t)
        items.append(((ex, 1.0, ezz), lambda: rider_back(ctx, view, ex, ezz, t, w.arm(t), w.speed(t) > 0.3)))
    if view.ortho:
        for _, fn in items:
            fn()
    else:
        for _, fn in sorted(items, key=lambda it: -view.depth(it[0])):
            fn()
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 30, 0, hy + 140)
        g.add_color_stop_rgba(0, 0.86, 0.94, 1, 0.0)
        g.add_color_stop_rgba(0.25, 0.86, 0.94, 1, 0.4)
        g.add_color_stop_rgba(1, 0.86, 0.94, 1, 0.0)
        ctx.set_source(g)
        ctx.rectangle(-50, hy - 30, SW + 100, 170)
        ctx.fill()


def pole(ctx, view, x, z):
    b, tp = view.pt((x, 0, z)), view.pt((x, 6.2, z))
    s = view.scale((x, 0, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.08 * s, tp[1], 0.16 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#4a4e5c'), OUTL, max(1, s / 60))
    c = view.pt((0, 6.0, z))
    if c:
        ctx.move_to(*tp)
        ctx.line_to(*c)
        setc(ctx, hexc('#3a3d48'))
        ctx.set_line_width(max(1, s / 80))
        ctx.stroke()
