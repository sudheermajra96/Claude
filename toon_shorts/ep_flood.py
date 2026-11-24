"""Turn around, don't drown: a flooded underpass in the rain. Houston, Texas.

World: +Z = north (travel). The road dips under a highway overpass: road height y(z) = -D * (0.5 + 0.5 cos(pi z / HL))
for |z| < HL, water surface at Y_W -> water where the road is below it (|z| < ~14 m, max depth 1.2 m / 4 ft).
Cross street at z = -26 (our escape route, turning right / east). Walls of the underpass at x = +-5.5.
Facts used (US National Weather Service): 6 in of moving water can knock an adult down, 12 in can carry away most
cars, 2 ft can carry away SUVs and trucks; you cannot see the depth or whether the road under the water is gone.
Parts of a car below the water line are covered by a translucent water layer (screen-space hull of the part below
the water, minus the hull of the part above it), so the car looks half submerged.
"""
import math
import random

import cairo
import numpy as np

from mkit import *
import truckkit
from truckkit import draw_car_round
from peoplekit import *
import citykit
import engine

DUR = 35.0
D, HL, Y_W = 1.5, 20.0, -0.3
Z_CROSS = -26.0
T_R0 = 17.2
C_WATER = hexc('#7d6a4e')
C_WATER_L = hexc('#a08c6a')


def road_y(z):
    return -D * (0.5 + 0.5 * math.cos(math.pi * z / HL)) if abs(z) < HL else 0.0


Z_EDGE = HL / math.pi * math.acos(2 * (-Y_W / D) - 1)          # water edge |z|


def depth_at(z):
    return max(0.0, Y_W - road_y(z))


# ------------------------------------------------------------------ car drawn on a slope / floating, with water layer
def make_L(yoff, pitch):
    def Lp(x, z, h):
        ch, sh = math.cos(h), math.sin(h)
        return lambda lx, ly, lz: (x + lx * ch + lz * sh, ly + yoff + lz * pitch, z - lx * sh + lz * ch)
    return Lp


def hull(pts):
    pts = sorted(set((round(p[0], 2), round(p[1], 2)) for p in pts))
    if len(pts) < 3:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def box_pts(Lf, y0, y1, wx=0.96, lz=2.26):
    return [Lf(sx * wx, y, sz * lz) for sx in (-1, 1) for sz in (-1, 1) for y in (y0, y1)]


def car_in_water(ctx, view, x, z, h, col, t, yoff, pitch, occ=None, blink=None, brake=0.0):
    old = truckkit.L
    truckkit.L = make_L(yoff, pitch)
    try:
        draw_car_round(ctx, view, x, z, h, col, t, blink, brake, occ=occ)
    finally:
        truckkit.L = old
    if view.ortho:
        return
    Lf = make_L(yoff, pitch)(x, z, h)
    # local water height (approx, at the car's centre)
    yl = Y_W - yoff
    if yl <= 0.02:
        return
    yl = min(yl, 1.5)
    below = [view.pt(p) for p in box_pts(Lf, -0.05, yl)]
    above = [view.pt(p) for p in box_pts(Lf, yl, 1.45, 0.94, 2.2)] if yl < 1.45 else []
    if not all(below) or (above and not all(above)):
        return
    hb = hull(below)
    ctx.save()
    poly(ctx, hb)
    ctx.clip()
    if above:
        ha = hull(above)
        ctx.rectangle(-100, -100, SW + 200, SH + 200)
        poly(ctx, ha)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.clip()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    setc(ctx, C_WATER, 0.86)
    ctx.paint()
    ctx.restore()
    # waterline ripple ring around the car
    ring = [view.pt(Lf(1.15 * math.cos(a), yl + 0.01, 2.5 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 28)]
    if all(ring):
        poly(ctx, ring)
        setc(ctx, C_WATER_L, 0.8)
        ctx.set_line_width(max(1.5, (view.scale(Lf(0, yl, 0)) or 10) * 0.04))
        ctx.stroke()


class FCar:
    """Car with a pose function (x, z, h), a height offset and pitch from the road profile, optional floating."""

    def __init__(self, posef, col, occ=None, float_from=None, blink=None, brake=None, haz=False):
        self.posef, self.col, self.occ, self.float_from = posef, col, occ, float_from
        self.blink = blink or (lambda t: None)
        self.brake = brake or (lambda t: 0.0)
        self.haz = haz

    def pose(self, t):
        return self.posef(t)

    def speed(self, t):
        a, b = self.pose(t - 0.05), self.pose(t + 0.05)
        return math.hypot(b[0] - a[0], b[1] - a[1]) / 0.1

    def steer(self, t):
        return 0.0

    def visible(self, t):
        return True

    def yoff_pitch(self, t):
        x, z, h = self.pose(t)
        y = road_y(z)
        pitch = (road_y(z + 1.0) - road_y(z - 1.0)) / 2.0 * math.cos(h)
        if self.float_from is not None and t > self.float_from:
            u = t - self.float_from
            fy = Y_W - 0.55 + 0.04 * math.sin(u * 2.5)
            k = smooth(u / 1.5)
            return y + (max(y, fy) - y) * k, pitch * (1 - k) + 0.04 * math.sin(u * 1.7) * k
        return y, pitch

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        yoff, pitch = self.yoff_pitch(t)
        b = self.blink(t)
        if self.haz:
            b = 'L' if (t * 1.25) % 1 < 0.5 else None

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, b, self.occ is not None)
                return
            car_in_water(ctx, view, x, z, h, self.col, t, yoff, pitch, self.occ(t) if self.occ else None, b, self.brake(t))
            if self.haz and (t * 1.25) % 1 < 0.5:
                Lf = make_L(yoff, pitch)(x, z, h)
                for P in (Lf(-0.85, 0.7, 2.2), Lf(0.85, 0.7, 2.2), Lf(-0.85, 0.7, -2.2), Lf(0.85, 0.7, -2.2)):
                    p = view.pt(P)
                    if p and view.to_cam(P)[2] > 0:
                        glow(ctx, p[0], p[1], min((view.scale(P) or 10) * 0.8, 120), AMBER, 0.9)
            spl = splash_amt(self, t)
            if spl > 0:
                splash(ctx, view, self, t, spl)
        return [((x, 0.8 + yoff, z), fn)]


def splash_amt(car, t):
    x, z, h = car.pose(t)
    d = depth_at(z)
    v = car.speed(t)
    if d < 0.03 or v < 0.8:
        return 0.0
    return min(1.0, v / 8.0) * min(1.0, d / 0.4)


def splash(ctx, view, car, t, amt):
    x, z, h = car.pose(t)
    Lf = L(x, z, h)
    rnd = random.Random(int(t * 30))
    for side in (-1, 1):
        for k in range(10):
            u = rnd.random()
            P = Lf(side * (1.0 + u * 1.6 * amt), Y_W + 0.2 + rnd.random() * 1.1 * amt * (1 - u), 1.9 + rnd.uniform(-0.4, 0.6))
            p, s = view.pt(P), view.scale(P)
            if p and s:
                ellipse(ctx, p[0], p[1], 0.14 * s, 0.1 * s)
                setc(ctx, (0.92, 0.95, 1.0), 0.75)
                ctx.fill()


# ------------------------------------------------------------------ hero paths
LOOK = Key([(0, 0.0), (99, 0.0)])


def hero_occ_fn(expr_fn):
    def occ(t):
        def fn(ctx, view, Lf, h):
            person3d(ctx, view, Lf, -0.38, 0.05, 'hero', 0.0, expr_fn(t))
        return fn
    return occ


# part 1: drives in, floats, drifts with the current (+x) and turns
_trW = Track(1.75, Key([(0, 11.0), (7.4, 11.0), (8.6, 6.5), (9.4, 5.5), (10.6, 2.0), (11.3, 0.6), (12.0, 0.0), (99, 0.0)], 'lin'),
             9.4, -Z_EDGE, '#e23b3b')
T_FLOAT = 11.0


def pose_w(t):
    x, z, h = _trW.pose(t)
    if t > T_FLOAT:
        u = t - T_FLOAT
        drift = 2.4 * smooth(u / 4.0)
        return 1.75 + drift, z, 0.55 * smooth(u / 4.0)
    return x, z, h


HERO_W = FCar(pose_w, '#e23b3b', hero_occ_fn(lambda t: 'calm' if t < 9.6 else 'shock'), float_from=T_FLOAT,
              brake=lambda t: 1.0 if 7.4 < t < 9.0 else 0.0)

# part 2: approaches, stops before the water, signals right, turns onto the cross street (east)
R_TURN = 6.0
Z_STOPR = Z_CROSS - 1.75 - R_TURN
PATH_R = Path([('L', (1.75, -140), (1.75, Z_STOPR)), ('A', (1.75 + R_TURN, Z_STOPR), R_TURN, 180, 90),
               ('L', (1.75 + R_TURN, Z_CROSS - 1.75), (300, Z_CROSS - 1.75))])
T_STOPR, T_GO = 20.6, 23.4
_spdR = Key([(0, 11.0), (18.6, 11.0), (T_STOPR, 0.0), (T_GO, 0.0), (T_GO + 1.4, 5.0), (T_GO + 3.0, 5.5), (T_GO + 5.0, 11.0), (99, 11.0)], 'lin')
_movR = OnPath(PATH_R, _spdR, T_STOPR, PATH_R.s_near(1.75, Z_STOPR - 2.2), '#e23b3b')
HERO_R = FCar(_movR.pose, '#e23b3b', hero_occ_fn(lambda t: 'focus'),
              blink=blink_side([(T_STOPR - 0.6, T_GO + 2.4)], 'R'), brake=lambda t: 1.0 if 18.6 < t < T_GO else 0.0)
STALLED = FCar(lambda t: (-1.9, 3.0, math.pi + 0.25), '#c9c9d6', None, float_from=-10, haz=True)


class DeckCar:
    """Car driving across the overpass (along x) on the deck at y = DECK_Y."""

    def __init__(self, x0, v, zl, col):
        self.x0, self.v, self.zl, self.col = x0, v, zl, col

    def visible(self, t):
        return True

    def pose(self, t):
        return self.x0 + self.v * t, self.zl, math.pi / 2 if self.v > 0 else -math.pi / 2

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        if abs(x) > 140 or view.ortho:
            return []
        return [((x, DECK_Y + 0.8, z), lambda: car_in_water(ctx, view, x, z, h, self.col, t, DECK_Y, 0.0))]


DECK_Y = 5.3
DECK = [DeckCar(-120 + 37 * i, 16.0, -1.8, c) for i, c in enumerate(['#3a7bd5', '#f2a541', '#1c1c22', '#c9c9d6', '#37b26c', '#7a4fd0', '#f4f4f6'])]
DECK += [DeckCar(140 - 41 * i, -15.0, 1.8, c) for i, c in enumerate(['#e05d5d', '#2f6f73', '#d8c3a0', '#3a7bd5', '#f4f4f6', '#1c1c22'])]


# ------------------------------------------------------------------ Houston street in the rain
def houston_sky(ctx, view):
    if view.ortho:
        return
    towers(ctx, view, 1100, -260, 220, 20, 90, 300, seed=5, base='#7d8896', haze='#b9c2cc')


class FloodStreet:
    sky = ('#6f7d8c', '#b9c2cc')

    def __init__(self):
        self.ground_col = hexc('#7f9a6c')
        r = random.Random(14)
        self.blds = []
        for sx in (-1, 1):
            z = -320.0
            while z < 400:
                w = r.uniform(16, 26)
                if not (-34 < z + w and z < -18) and not (-26 < z and z < 26) and not (-26 < z + w and z + w < 26):
                    x0 = sx * 11.0
                    self.blds.append((min(x0, x0 + sx * r.uniform(12, 20)), max(x0, x0 + sx * r.uniform(12, 20)), z, z + w,
                                      r.uniform(8, 22), r.choice(['#b7a28a', '#a9b8c6', '#c9b9a6', '#8f9aa8', '#9fb3a0', '#c98b6b'])))
                z += w + r.uniform(3, 8)

    def skyline(self, ctx, view):
        houston_sky(ctx, view)

    def strip(self, ctx, view, x0, x1, z0, z1, col, dy=0.0, step=1.0):
        zs = np.arange(z0, z1 + 0.001, step)
        for a, b in zip(zs, zs[1:]):
            fill_poly(ctx, view, [(x0, road_y(a) + dy, a), (x1, road_y(a) + dy, a), (x1, road_y(b) + dy, b), (x0, road_y(b) + dy, b)], col)

    def ground(self, ctx, view, t):
        # sidewalks + road outside the dip; the dip itself in strips
        gquad(ctx, view, -11, 11, -600, -HL, C_WALK)
        gquad(ctx, view, -11, 11, HL, 600, C_WALK)
        gquad(ctx, view, -600, 600, Z_CROSS - 3.5 - 2, Z_CROSS + 3.5 + 2, C_WALK)
        gquad(ctx, view, -5.5, 5.5, -600, -HL, C_ASPH)
        gquad(ctx, view, -5.5, 5.5, HL, 600, C_ASPH)
        gquad(ctx, view, -600, 600, Z_CROSS - 3.5, Z_CROSS + 3.5, C_ASPH)
        self.strip(ctx, view, -5.5, 5.5, -HL, HL, C_ASPH, 0.0, 1.0 if not view.ortho else 4.0)
        for sx in (-1, 1):
            gquad(ctx, view, *sorted((sx * 3.45, sx * 3.6)), -600, Z_CROSS - 3.5, C_LINE, 0.01)
            gquad(ctx, view, *sorted((sx * 3.45, sx * 3.6)), Z_CROSS + 3.5, -HL, C_LINE, 0.01)
        for z0, z1 in ((-600, Z_CROSS - 3.5), (Z_CROSS + 3.5, -HL), (HL, 600)):
            gquad(ctx, view, -0.2, -0.07, z0, z1, C_YEL, 0.01)
            gquad(ctx, view, 0.07, 0.2, z0, z1, C_YEL, 0.01)
        self.strip(ctx, view, -0.2, -0.07, -HL, -Z_EDGE, C_YEL, 0.01, 1.0)
        self.strip(ctx, view, 0.07, 0.2, -HL, -Z_EDGE, C_YEL, 0.01, 1.0)
        gquad(ctx, view, 0.2, 3.5, Z_CROSS - 3.5 - 0.5, Z_CROSS - 3.5, C_LINE, 0.012)
        # water surface + rain rings
        zs = np.linspace(-Z_EDGE, Z_EDGE, 15)
        for a, b in zip(zs, zs[1:]):
            if not view.ortho and view.to_cam((0, Y_W, (a + b) / 2))[2] < -8 and view.to_cam((0, Y_W, a))[2] < 0 and view.to_cam((0, Y_W, b))[2] < 0:
                continue
            fill_poly(ctx, view, [(-5.5, Y_W, a), (5.5, Y_W, a), (5.5, Y_W, b), (-5.5, Y_W, b)], C_WATER)
        rnd = random.Random(3)
        for k in range(40 if not view.ortho else 0):
            ph = (t * 1.3 + rnd.random()) % 1
            wx, wz = rnd.uniform(-5.2, 5.2), rnd.uniform(-Z_EDGE + 0.5, Z_EDGE - 0.5)
            pts = [view.pt((wx + 0.5 * ph * math.cos(a), Y_W + 0.005, wz + 0.5 * ph * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 12)]
            if all(pts):
                poly(ctx, pts)
                setc(ctx, C_WATER_L, 0.7 * (1 - ph))
                ctx.set_line_width(2)
                ctx.stroke()
        for k in range(6):
            zz = -Z_EDGE + 2 + k * 4.0
            a, b = view.pt((-5.0, Y_W + 0.005, zz)), view.pt((5.0, Y_W + 0.005, zz + 0.6 * math.sin(t + k)))
            if a and b and not view.ortho:
                ctx.move_to(*a)
                ctx.line_to(*b)
                setc(ctx, C_WATER_L, 0.5)
                ctx.set_line_width(2)
                ctx.stroke()

        # underpass walls (drawn after the water so they bound it) (concrete) from the road up to street level + 1 m
        if not view.ortho:
            for sx in (-1, 1):
                zs = np.arange(-HL, HL + 0.01, 2.0)
                for a, b in zip(zs, zs[1:]):
                    fill_poly(ctx, view, [(sx * 5.5, road_y(a), a), (sx * 5.5, road_y(b), b), (sx * 5.5, 1.0, b), (sx * 5.5, 1.0, a)],
                              hexc('#a7a39a'))

    def objects(self, ctx, view, t):
        out = []
        for b in self.blds:
            out.append((((b[0] + b[1]) / 2, b[4] / 2, (b[2] + b[3]) / 2), lambda b=b: building(ctx, view, *b, win='#3b5872')))
        out.append(((0.0, DECK_Y - 0.5, -4.5), lambda: overpass(ctx, view)))
        out.append(((6.3, 1.0, -10.0), lambda: gauge(ctx, view, 6.0, -10.0)))
        out.append(((6.5, 1.5, -44.0), lambda: water_sign(ctx, view, 6.5, -44.0)))
        for z in np.arange(-300, 400, 30):
            if abs(z) > HL + 2 and abs(z - Z_CROSS) > 6:
                for sx in (-1, 1):
                    out.append(((sx * 7.5, 4, z), lambda z=z, sx=sx: lamp_post(ctx, view, sx * 7.5, z, sx)))
        return out


def overpass(ctx, view):
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    Lf = lambda a, b, c: (a, b, c)
    conc = hexc('#b9b4aa')
    lbox(ctx, view, Lf, 0.0, -200, 200, DECK_Y - 1.3, DECK_Y, -4.5, 4.5,
         {'front': mix(conc, (0, 0, 0), 0.25), 'back': mix(conc, (0, 0, 0), 0.15), 'left': conc, 'right': conc, 'top': hexc('#5b5f6c')}, 3)
    if not view.ortho:
        for zz in (-4.5, 4.5):
            fill_poly(ctx, view, [(-200, DECK_Y, zz), (200, DECK_Y, zz), (200, DECK_Y + 0.9, zz), (-200, DECK_Y + 0.9, zz)], conc, OUTL, 2)
        c, s = view.pt((0, DECK_Y - 0.65, -4.52)), view.scale((0, DECK_Y - 0.65, -4.52))
        if c and s and s > 3:
            text_center(ctx, 'I-45', c[0], c[1] + 0.25 * s, 0.7 * s, (1, 1, 1))


def gauge(ctx, view, x, z):
    """Flood depth gauge in feet, standing at the road edge (its zero is the road surface there)."""
    y0 = road_y(z)
    if view.ortho:
        return
    ft = 0.3048
    b, tp, s = view.pt((x, y0, z)), view.pt((x, y0 + 6 * ft, z)), view.scale((x, y0 + 3 * ft, z))
    if not b or not tp or not s:
        return
    w = 0.25 * s
    ctx.rectangle(b[0] - w / 2, tp[1], w, b[1] - tp[1])
    fill_stroke(ctx, (1, 1, 1), OUTL, max(1, s / 60))
    for k in range(1, 6):
        p = view.pt((x, y0 + k * ft, z))
        if p:
            ctx.move_to(p[0] - w / 2, p[1])
            ctx.line_to(p[0] + w / 2, p[1])
            setc(ctx, OUTL)
            ctx.set_line_width(max(1, s / 40))
            ctx.stroke()
            if s > 12:
                text_center(ctx, str(k), p[0] + w * 1.2, p[1] + 0.05 * s, 0.18 * s, (1, 1, 1))
    p = view.pt((x, y0 + 6 * ft, z))
    rrect(ctx, p[0] - w * 0.7, p[1] - w * 0.9, w * 1.4, w * 0.9, w * 0.2)
    fill_stroke(ctx, hexc('#d62828'), OUTL, max(1, s / 60))
    # the part of the gauge under the water, tinted
    wy = view.pt((x, Y_W, z))
    if wy and Y_W > y0:
        ctx.rectangle(b[0] - w, wy[1], 2 * w, b[1] - wy[1] + 2)
        setc(ctx, C_WATER, 0.8)
        ctx.fill()


def water_sign(ctx, view, x, z):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 2.2, z)), view.scale((x, 2.2, z))
    if not b or not tp or not s:
        return
    ctx.move_to(*b)
    ctx.line_to(*tp)
    setc(ctx, hexc('#6a6f7c'))
    ctx.set_line_width(max(2, 0.08 * s))
    ctx.stroke()
    ctx.save()
    ctx.translate(tp[0], tp[1] - 0.55 * s)
    ctx.rotate(math.pi / 4)
    rrect(ctx, -0.55 * s, -0.55 * s, 1.1 * s, 1.1 * s, 0.08 * s)
    fill_stroke(ctx, hexc('#f2c230'), OUTL, max(1, s / 40))
    ctx.restore()
    if s > 10:
        text_center(ctx, 'HIGH', tp[0], tp[1] - 0.62 * s, 0.22 * s, OUTL)
        text_center(ctx, 'WATER', tp[0], tp[1] - 0.36 * s, 0.22 * s, OUTL)


world = SegWorld(DUR, [hook_seg(0, 3.0, 9.0, HERO_W, [STALLED] + DECK, []),
                       (3.0, T_R0, HERO_W, [STALLED] + DECK, []),
                       (T_R0, 99, HERO_R, [STALLED] + DECK, [])], FloodStreet(), 'mph')
world.police_flash = lambda t: 0.0


# ------------------------------------------------------------------ rain + cameras
def rain(ctx, t, amt=1.0, wash=0.16):
    setc(ctx, (0.45, 0.5, 0.58), wash)
    ctx.paint()
    rnd = random.Random(7)
    for k in range(int(170 * amt)):
        x0, y0, sp = rnd.uniform(-100, SW + 100), rnd.uniform(0, SH), rnd.uniform(1400, 2200)
        y = (y0 + t * sp) % (SH + 120) - 60
        x = x0 - (y - y0) * 0.12
        ctx.move_to(x, y)
        ctx.line_to(x - 7, y + 42)
        setc(ctx, (0.88, 0.92, 1.0), 0.45)
        ctx.set_line_width(2)
        ctx.stroke()


def car_cam(w, t, mode):
    e = w.ego(t)
    x, z, h = e.pose(t)
    yo = e.yoff_pitch(t)[0] if hasattr(e, 'yoff_pitch') else 0.0
    yo = max(yo, Y_W - 0.6) if depth_at(z) > 0 else yo
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    if mode == 'chase':
        return TCam((x - fx * 10.5, 3.6 + yo * 0.6, z - fz * 10.5), h, 0.16, 1000, cy=520)
    if mode == 'high':
        return TCam((x - fx * 14, 10.0, z - fz * 14), h, 0.44, 1000, cy=470)
    if mode == 'inside':
        return TCam((x - rx * 0.38 - fx * 0.2, 1.18 + yo, z - rz * 0.38 - fz * 0.2), h, 0.04, 1000, cy=470)
    raise ValueError(mode)


def fl_cam(ctx, w, t, lt, kw):
    tf = min(t, kw['freeze']) if 'freeze' in kw else t
    if kw['cam'] == 'fixed':
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000))
    else:
        view = car_cam(w, tf, kw['cam'])
    draw_scene(ctx, view, w, tf, ego=kw['cam'] != 'inside')
    if kw['cam'] == 'inside':
        drops_and_wipers(ctx, t)
        citykit.cockpit(ctx, w, tf)
    rain(ctx, t, 1.0 if kw['cam'] != 'inside' else 0.4, 0.14)
    if 'freeze' in kw and t >= kw['freeze']:
        u = t - kw['freeze']
        setc(ctx, (1, 1, 1), max(0, 0.8 - u * 3))
        ctx.paint()
        setc(ctx, (0.6, 0, 0), 0.22)
        ctx.paint()
    if kw.get('hud', kw['cam'] in ('chase', 'inside')):
        hud(ctx, w, tf)
    if kw.get('meter'):
        depth_meter(ctx, w, tf)


def drops_and_wipers(ctx, t):
    rnd = random.Random(11)
    wp = (t * 0.9) % 1
    ang = math.pi * (0.5 - 0.5 * math.cos(2 * math.pi * wp))       # 0..pi..0
    for k in range(70):
        x, y = rnd.uniform(250, 1700), rnd.uniform(40, 800)
        age = (t * 0.7 + rnd.random()) % 1
        ellipse(ctx, x, y, 7 + 5 * age, 9 + 6 * age)
        setc(ctx, (0.85, 0.92, 1.0), 0.35 * (1 - age * 0.5))
        ctx.fill()
    for px in (620, 1260):
        a = -math.pi + ang
        ctx.move_to(px, 820)
        ctx.line_to(px + math.cos(a) * 620, 820 + math.sin(a) * 620)
        setc(ctx, hexc('#15151c'))
        ctx.set_line_width(14)
        ctx.stroke()


def depth_meter(ctx, w, t):
    x, z, h = w.ego(t).pose(t)
    d = depth_at(z)
    inches = d / 0.0254
    rrect(ctx, 1460, 40, 420, 150, 34)
    setc(ctx, (0, 0, 0), 0.6)
    ctx.fill()
    text_center(ctx, 'WATER DEPTH', 1670, 90, 36, (0.9, 0.9, 0.95))
    col = hexc('#22c35e') if inches < 4 else (hexc('#ffd23f') if inches < 10 else hexc('#ff4b4b'))
    text_center(ctx, f'{int(round(inches))} in', 1670, 165, 66, col)


def flood_win(ctx, w, t, lt, kw):
    """Hero through his window with brown water rising up the door."""
    WIN = [(240, 770), (1730, 770), (1730, 190), (600, 150)]
    path = lambda: (ctx.move_to(*WIN[0]), [ctx.line_to(*p) for p in WIN[1:]], ctx.close_path())
    rise = kw.get('rise', (0.0, 0.0))
    lvl = 1080 - (rise[0] + (rise[1] - rise[0]) * smooth(lt / max(0.1, kw.get('rdur', 2.5))))
    ctx.save()
    path()
    ctx.clip()
    setc(ctx, hexc('#2c2d38'))
    ctx.paint()
    g = cairo.LinearGradient(0, 200, 0, 560)
    g.add_color_stop_rgb(0, *hexc('#6f7d8c'))
    g.add_color_stop_rgb(1, *hexc('#b9c2cc'))
    ctx.set_source(g)
    ctx.rectangle(560, 200, 1200, 360)
    ctx.fill()
    ctx.rectangle(560, 400, 1200, 160)
    setc(ctx, hexc('#a7a39a'))
    ctx.fill()
    ctx.rectangle(0, 120, SW, 80)
    setc(ctx, hexc('#4a4b58'))
    ctx.fill()
    ctx.move_to(200, 560)
    ctx.curve_to(400, 520, 560, 560, 620, 800)
    ctx.line_to(200, 800)
    ctx.close_path()
    fill_stroke(ctx, hexc('#1f2029'), OUTL, 5)
    rrect(ctx, 1080, 300, 300, 700, 90)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 5)
    rrect(ctx, 1110, 250, 230, 150, 60)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 5)
    head2d(ctx, 900, 480, 175, 'hero', kw.get('expr', 'shock'), kw.get('turn', -0.5), t)
    # rain on the glass
    rnd = random.Random(5)
    for k in range(40):
        x, y = rnd.uniform(250, 1720), rnd.uniform(160, 760)
        yy = y + (t * 60 * rnd.uniform(0.5, 1.5)) % 120
        ellipse(ctx, x, yy, 6, 9)
        setc(ctx, (0.85, 0.92, 1.0), 0.4)
        ctx.fill()
    setc(ctx, (0.75, 0.88, 1.0), 0.1)
    ctx.paint()
    ctx.restore()
    body = hexc('#e23b3b')
    ctx.rectangle(-40, -40, SW + 80, SH + 80)
    path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    setc(ctx, body)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.rectangle(-40, -40, SW + 80, 130)
    setc(ctx, mix(body, (0, 0, 0), 0.15))
    ctx.fill()
    path()
    setc(ctx, hexc('#15151c'))
    ctx.set_line_width(22)
    ctx.stroke()
    # the flood water outside, up the door
    ctx.move_to(-40, lvl)
    for k in range(0, SW + 80, 40):
        ctx.line_to(k, lvl + 10 * math.sin(k / 60 + t * 4))
    ctx.line_to(SW + 40, SH + 40)
    ctx.line_to(-40, SH + 40)
    ctx.close_path()
    setc(ctx, C_WATER, 0.92)
    ctx.fill()
    rain(ctx, t, 0.6, 0.08)


def cross_section(ctx, w, t, lt, kw):
    """Side cut of the flooded dip: what you cannot see, and how little water it takes."""
    g = cairo.LinearGradient(0, 0, 0, SH)
    g.add_color_stop_rgb(0, *hexc('#6f7d8c'))
    g.add_color_stop_rgb(1, *hexc('#b9c2cc'))
    ctx.set_source(g)
    ctx.paint()
    X = lambda z: 960 + z * 38
    Y = lambda y: 300 - y * 130
    # ground body
    pts = [(X(z), Y(road_y(z) if abs(z - 4) > 2.2 else road_y(z) - 0.9 * math.cos((z - 4) / 2.2 * math.pi / 2))) for z in np.arange(-26, 26.1, 0.5)]
    ctx.move_to(-10, Y(0))
    for p in pts:
        ctx.line_to(*p)
    ctx.line_to(SW + 10, Y(0))
    ctx.line_to(SW + 10, SH + 10)
    ctx.line_to(-10, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, hexc('#5c4a36'), OUTL, 5)
    # road line on top
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    setc(ctx, C_ASPH)
    ctx.set_line_width(12)
    ctx.stroke()
    # water
    ctx.move_to(X(-Z_EDGE), Y(Y_W))
    for z in np.arange(-Z_EDGE, Z_EDGE + 0.01, 0.5):
        yy = road_y(z) if abs(z - 4) > 2.2 else road_y(z) - 0.9 * math.cos((z - 4) / 2.2 * math.pi / 2)
        ctx.line_to(X(z), Y(min(yy, Y_W)))
    ctx.line_to(X(Z_EDGE), Y(Y_W))
    ctx.close_path()
    setc(ctx, hexc('#6f9fb8'), 0.85)
    ctx.fill()
    ctx.move_to(X(-Z_EDGE), Y(Y_W))
    ctx.line_to(X(Z_EDGE), Y(Y_W))
    setc(ctx, C_WATER_L)
    ctx.set_line_width(5)
    ctx.stroke()
    if lt > 0.6:
        a = smooth((lt - 0.6) / 0.3)
        ctx.save()
        ctx.translate(X(4), Y(-1.9) + 40)
        label(ctx, 0, 70, 'Road washed away?', '#e0393e', 40)
        ctx.restore()
        ctx.arc(X(4), Y(-1.9), 70, 0, 2 * math.pi)
        setc(ctx, hexc('#ff4b4b'), a)
        ctx.set_line_width(6)
        ctx.stroke()
    # little car at the edge
    cx, cy = X(-Z_EDGE - 4.5), Y(road_y(-Z_EDGE - 4.5))
    rrect(ctx, cx - 70, cy - 46, 140, 34, 10)
    fill_stroke(ctx, hexc('#e23b3b'), OUTL, 4)
    poly(ctx, [(cx - 40, cy - 46), (cx - 22, cy - 72), (cx + 26, cy - 72), (cx + 44, cy - 46)])
    fill_stroke(ctx, hexc('#2a3448'), OUTL, 4)
    for wx in (-42, 42):
        ellipse(ctx, cx + wx, cy - 10, 16, 16)
        fill_stroke(ctx, hexc('#1d1d24'), OUTL, 3)
    text_center(ctx, "You can't see the depth, or what's under it", 1010, 95, 56, (1, 1, 1))
    # the depth ladder (NWS)
    rows = [('6 in', 'can knock you off your feet', 0.15), ('12 in', 'can float most cars', 0.30), ('2 ft', 'can sweep away SUVs and trucks', 0.61)]
    for i, (a_, b_, dm) in enumerate(rows):
        if lt < 0.9 + i * 0.6:
            continue
        al = smooth((lt - 0.9 - i * 0.6) / 0.25)
        y = 740 + i * 112
        rrect(ctx, 200, y - 50, 1520, 100, 30)
        setc(ctx, (0, 0, 0), 0.6 * al)
        ctx.fill()
        text_center(ctx, a_, 360, y + 22, 64, hexc('#ffd23f'), a=al)
        text_center(ctx, b_, 1080, y + 18, 54, (1, 1, 1), a=al)


def caught_card(ctx, w, t, lt, kw):
    """Bonus: if water rises around your car."""
    setc(ctx, hexc('#1f2b38'))
    ctx.paint()
    text_center(ctx, 'If water rises around your car:', 960, 170, 70, (1, 1, 1))
    items = [('SEATBELT', 'off'), ('WINDOW', 'down'), ('GET OUT', 'to higher ground')]
    for i, (a_, b_) in enumerate(items):
        if lt < 0.3 + i * 0.55:
            continue
        al = smooth((lt - 0.3 - i * 0.55) / 0.25)
        cx = 360 + i * 600
        sc = 0.85 + 0.15 * al
        ctx.save()
        ctx.translate(cx, 560)
        ctx.scale(sc, sc)
        rrect(ctx, -250, -230, 500, 460, 50)
        setc(ctx, hexc('#22a356'), al)
        ctx.fill()
        ellipse(ctx, 0, -90, 90, 90)
        setc(ctx, (1, 1, 1), al)
        ctx.fill()
        text_center(ctx, str(i + 1), 0, -60, 100, hexc('#22a356'), a=al)
        text_center(ctx, a_, 0, 90, 64, (1, 1, 1), a=al)
        text_center(ctx, b_, 0, 170, 44, (0.9, 1, 0.92), a=al)
        ctx.restore()
    if lt > 2.0:
        text_center(ctx, 'Then call 911', 960, 950, 60, hexc('#ffd23f'), a=smooth((lt - 2.0) / 0.3))


engine.SCENES.update(fl_cam=fl_cam, flood_win=flood_win, cross_section=cross_section, caught_card=caught_card)

HOOK = dict(cam='fixed', pos=(4.6, 0.6, -2.0), target=(1.0, 0.0, -14.0), f=950)
SIDE = dict(cam='fixed', pos=(-4.6, 0.9, -4.5), target=(1.8, -0.4, -12.0), f=900, meter=True)
WIDE_W = dict(cam='fixed', pos=(-3.6, 2.0, -0.5), target=(3.0, -0.5, -9.0), f=850, freeze=15.3)
TURN = dict(cam='fixed', pos=(-6.0, 7.5, -48.0), target=(4.0, 0.0, -28.0), f=900)
END = dict(cam='fixed', pos=(4.0, 2.4, -32.0), target=(0.0, -0.2, -2.0), f=900)
defs = [
    (3.0, 'fl_cam', dict(HOOK)),
    (6.0, 'fl_cam', dict(cam='chase')),
    (8.5, 'fl_cam', dict(cam='inside')),
    (11.0, 'fl_cam', dict(SIDE)),
    (13.5, 'flood_win', dict(expr='shock', rise=(150, 420), rdur=2.5)),
    (16.0, 'fl_cam', dict(WIDE_W)),
    (T_R0, 'rewind_seq', dict()),
    (19.7, 'fl_cam', dict(cam='inside')),
    (23.0, 'cross_section', dict()),
    (26.0, 'fl_cam', dict(TURN)),
    (28.5, 'fl_cam', dict(cam='chase')),
    (31.5, 'caught_card', dict()),
    (DUR, 'fl_cam', dict(END)),
]
shots = build_shots(defs)
shots[6].kw.update(srcs=list(reversed(shots[1:6])), dur=shots[6].dur)
video = Video(['Flooded road ahead.', 'Would you drive through?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('How deep is it?', 300, 130, hexc('#ffd23f'), 0.2, True)),
    (3.0, 6.0, location_tag('Houston, Texas')),
    (3.2, 6.0, caption('Heavy rain. Underpass ahead.')),
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, E[2], caption('"It\'s just a puddle..."')),
    (S[3] + 0.2, E[3], caption('Deeper... and deeper')),
    (S[4] + 0.2, E[4], caption('12 in of moving water can float a car')),
    (S[5] + 0.2, E[5], caption('Floating. No brakes. No steering.')),
    (S[5] + 1.8, E[5], x_mark),
    (S[11], E[11], badge('BONUS', '#7a4fd0')),
    (S[12] + 0.2, E[12], end_card("Turn around. Don't drown.", 'Would YOU have driven through? Comment!')),
]
for n, (i, txt) in enumerate(((7, 'Stop BEFORE the water'), (8, "You can't see the depth or the road"), (9, 'Turn around. Take another route.'),
                              (10, 'Higher roads. Arrive late, arrive alive.')), 1):
    video.overlays += [(S[i], E[i], step_badge(min(n, 3))) if i != 10 else (S[i], E[i], badge('RIGHT', '#22a356')),
                       (S[i] + 0.15, E[i], caption(txt) if i != 8 else (lambda ctx, lt, d: None))]


# ------------------------------------------------------------------ sound
def rain_bed(d):
    n = int(d * SR)
    s = bp(noise(n), 1500, 7000) * 0.35 + lp(noise(n), 500) * 0.25
    rnd = np.random.default_rng(4)
    for i in rnd.integers(0, n - 400, int(d * 60)):
        s[i:i + 300] += np.exp(-np.arange(300) / 40) * rnd.uniform(0.1, 0.4) * np.sign(rnd.standard_normal())
    return s


def thunder(d=3.0):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return lp(noise(n), 120) * (np.exp(-tt / 1.2) * (1 - np.exp(-tt / 0.08))) * 2.5


def wiper(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    ph = (tt * 0.9) % 1
    return bp(noise(n), 400, 2500) * np.exp(-((ph - 0.25) % 0.5) / 0.05) * 0.3


def gurgle(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    rnd = np.random.default_rng(2)
    for i in rnd.integers(0, n - 4000, int(d * 14)):
        f = rnd.uniform(200, 700)
        k = np.arange(3000) / SR
        out[i:i + 3000] += np.sin(2 * np.pi * f * (1 + 4 * k) * k) * np.exp(-k / 0.03) * 0.3
    return lp(out + lp(noise(n), 300) * 0.4, 1800)


def sound():
    m = Mixer(video.dur)
    m.add(rain_bed(video.dur), 0, 0.28)
    hook_sfx(m)
    m.add(thunder(3.0), 0.3, 0.9)
    m.add(ambience(world, 13.0, inside=0.9), 3.0, 0.12)
    m.add(wiper(E[2] - S[2]), S[2], 0.6)
    m.add(gurgle(5.0), 9.2, 0.6)
    m.add(whoosh(1.2, 0.3), 9.2, 0.6)
    m.add(heartbeat(4, 130), S[4] + 0.1, 0.8)
    m.add(gurgle(4.0), S[4], 0.7)
    m.add(sad_violin(), 15.3, 0.85)
    m.add(impact(), 15.3, 0.4)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(ambience(world, video.dur - T_R0, inside=0.9)[:int((E[7] - T_R0) * SR)], T_R0, 0.12)
    m.add(wiper(E[7] - S[7]), S[7], 0.6)
    m.add(brake_squeal(1.0), 19.4, 0.3)
    m.add(thunder(3.0), S[8] + 0.2, 0.6)
    for i in (7, 8, 9):
        m.add(pop(), S[i] + 0.15, 0.6)
    m.add(click(), T_STOPR - 0.6, 0.7)
    indicator(m, T_STOPR - 0.6, T_GO + 2.4, 0.4, 0.2)
    m.add(ambience(world, 12.0, inside=0.9)[:int((E[10] - S[9]) * SR)], S[9], 0.12)
    for i in range(3):
        m.add(pop(), S[11] + 0.3 + i * 0.55, 0.7)
    m.add(chime(), S[11] + 2.0, 0.6)
    m.add(success_jingle(), S[12] + 0.3, 0.8)
    return m.out(video.dur)


def verify():
    print('water edge |z| =', round(Z_EDGE, 2), '| max depth', round(Y_W + D, 2), 'm =', round((Y_W + D) / 0.3048, 1), 'ft',
          '| gauge depth', round(depth_at(-10) / 0.0254), 'in')
    print('part 1: enters water at t =', round(next(t for t in np.arange(3, 16, 0.01) if depth_at(pose_w(t)[1]) > 0), 2),
          '| depth when it floats', round(depth_at(pose_w(T_FLOAT)[1]) / 0.0254), 'in', '| final pose', [round(v, 2) for v in pose_w(15.3)])
    x, z, h = pose_w(15.3)
    print('   float drift keeps clear of wall (x + 2.3 < 5.5):', round(x + 2.3 * abs(math.sin(h)) + 0.92 * abs(math.cos(h)), 2),
          '| clear of the stalled car:', round(math.hypot(x - (-1.9), z - 3.0), 2), 'm')
    print('part 2: stops at z', round(HERO_R.pose(T_GO)[1] + 2.2, 2), '(front) | water edge at', round(-Z_EDGE, 2),
          '| stop line', Z_CROSS - 4.0, '| turn ends heading', round(math.degrees(HERO_R.pose(T_GO + 4.5)[2])))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        run(video, sound, 'flood.mp4')
