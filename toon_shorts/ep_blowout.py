"""Tire blowout at 70 mph: panic vs calm. I-15 near Las Vegas, Nevada, at sunset.

World: +Z = travel (north-east toward Las Vegas), +X = right. Our carriageway: left lane x = 1.75, right lane
x = 5.25, paved shoulder 7.0 .. 10.0 (rumble strip at 7.2). Wide desert median; the opposite carriageway at x < -16.
The FRONT-LEFT tyre blows: the car pulls to the left, the corner drops, rubber flaps.
Part 1 (wrong): slams the brakes + yanks the wheel -> spins, ends up sideways in the left lane, a truck closing in
(freeze before anything happens). Part 2 (right): grip the wheel, keep it straight, DON'T brake hard, ease off the
gas, let it slow down, then brake gently, signal and pull onto the shoulder, hazards on, wait away from traffic.
Prevention: under-inflated tyres overheat and fail - check the pressure monthly.
"""
import math
import random

import cairo
import numpy as np

from mkit import *
import truckkit
from truckkit import draw_car_round, tractor_det, trailer_det, wheel3
from peoplekit import *
import citykit
import engine
import euro

DUR = 38.0
V0 = 31.3                         # 70 mph
T_BW, T_BR = 8.0, 18.6            # blowout times (wrong / right)
T_R0 = 16.7
T_FREEZE = 14.6
SKY = ('#5a3f8c', '#ffb36b')


# ------------------------------------------------------------------ car with a dropped corner and shredded tyre
def make_L(yoff=0.0, pitch=0.0, roll=0.0):
    def Lp(x, z, h):
        ch, sh = math.cos(h), math.sin(h)
        return lambda lx, ly, lz: (x + lx * ch + lz * sh, ly + yoff + lz * pitch + lx * roll, z - lx * sh + lz * ch)
    return Lp


def shreds(ctx, view, Lf, t, amt, spin):
    """Rubber strips flapping off the front-left wheel + the rim almost on the road."""
    c = Lf(-0.86, 0.24, 1.38)
    p, s = view.pt(c), view.scale(c)
    if not p or not s:
        return
    for k in range(5):
        a = spin * t * 14 + k * 1.25
        L1 = (0.25 + 0.2 * (k % 2)) * amt
        q = view.pt(Lf(-0.92 - 0.05 * k, 0.24 + math.sin(a) * (0.3 + L1), 1.38 + math.cos(a) * (0.3 + L1)))
        if q:
            ctx.move_to(p[0] + math.cos(a) * 0.25 * s, p[1] - math.sin(a) * 0.25 * s)
            ctx.curve_to(p[0] + math.cos(a + 0.3) * 0.4 * s, p[1] - math.sin(a + 0.3) * 0.4 * s, q[0], q[1], q[0] + 0.05 * s, q[1])
            setc(ctx, hexc('#141418'))
            ctx.set_line_width(max(2, 0.08 * s))
            ctx.stroke()


class BCar:
    def __init__(self, posef, t_blow, occ=None, haz_from=None, blink=None, brake=None, sparks=False):
        self.posef, self.t_blow, self.occ, self.haz_from = posef, t_blow, occ, haz_from
        self.col = '#e23b3b'
        self.blink_f = blink or (lambda t: None)
        self.brake_f = brake or (lambda t: 0.0)
        self.sparks = sparks

    def pose(self, t):
        return self.posef(t)

    def speed(self, t):
        a, b = self.pose(t - 0.05), self.pose(t + 0.05)
        return math.hypot(b[0] - a[0], b[1] - a[1]) / 0.1

    def steer(self, t):
        return clamp((self.pose(t + 0.15)[2] - self.pose(t - 0.15)[2]) * 4.0, -1.6, 1.6)

    def blink(self, t):
        if self.haz_from is not None and t >= self.haz_from:
            return 'L' if (t * 1.25) % 1 < 0.5 else None
        return self.blink_f(t)

    def brake(self, t):
        return self.brake_f(t)

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        blown = t >= self.t_blow
        roll = -0.05 if blown else 0.0
        pitch = 0.025 if blown else 0.0
        yoff = -0.04 if blown else 0.0
        bl = self.blink(t)

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, bl, True)
                return
            old = truckkit.L
            truckkit.L = make_L(yoff, pitch, roll)
            try:
                draw_car_round(ctx, view, x, z, h, self.col, t, bl, self.brake(t), occ=self.occ(t) if self.occ else None)
            finally:
                truckkit.L = old
            if self.haz_from is not None and t >= self.haz_from and (t * 1.25) % 1 < 0.5:
                Lf = L(x, z, h)
                for P in (Lf(-0.85, 0.68, 2.2), Lf(0.85, 0.68, 2.2), Lf(-0.85, 0.68, -2.2), Lf(0.85, 0.68, -2.2)):
                    pp = view.pt(P)
                    if pp and view.to_cam(P)[2] > 0:
                        glow(ctx, pp[0], pp[1], min((view.scale(P) or 10) * 0.9, 140), AMBER, 0.9)
            if blown:
                Lf = make_L(yoff, pitch, roll)(x, z, h)
                sp = self.speed(t)
                shreds(ctx, view, Lf, t, min(1.0, sp / 15.0), 1.0 if sp > 1 else 0.0)
                if self.sparks and sp > 6:
                    c = Lf(-0.86, 0.02, 1.38)
                    pc, sc = view.pt(c), view.scale(c)
                    if pc and sc:
                        rnd = random.Random(int(t * 40))
                        for k in range(8):
                            a = rnd.uniform(math.pi * 0.9, math.pi * 1.3)
                            d = rnd.uniform(0.2, 0.9) * sc
                            ctx.move_to(*pc)
                            ctx.line_to(pc[0] + math.cos(a) * d, pc[1] + math.sin(a) * d * 0.4)
                            setc(ctx, hexc('#ffd23f'))
                            ctx.set_line_width(2)
                            ctx.stroke()
            if blown and t - self.t_blow < 0.5:
                bang(ctx, view, x, z, h, t - self.t_blow)
        return [((x, 0.8, z), fn)]


def bang(ctx, view, x, z, h, u):
    Lf = L(x, z, h)
    P = Lf(-1.3, 1.4, 1.6)
    p, s = view.pt(P), view.scale(P)
    if not p or not s:
        return
    sz = clamp(s * 0.9, 70, 160) * (1 + 0.35 * (1 - smooth(u / 0.1)))
    pts = []
    for k in range(24):
        a = k * math.pi / 12
        rr = (1.0 if k % 2 == 0 else 0.6) * sz
        pts.append((p[0] + math.cos(a) * rr * 1.5, p[1] + math.sin(a) * rr))
    poly(ctx, pts)
    fill_stroke(ctx, hexc('#ffd23f'), OUTL, 5)
    text_center(ctx, 'BANG!', p[0], p[1] + sz * 0.22, sz * 0.62, OUTL)


# ------------------------------------------------------------------ motion
_zW = Track(0.0, Key([(0, V0), (T_BW + 0.35, V0), (9.0, 26), (10.0, 18), (11.0, 10), (12.0, 4), (12.8, 0), (99, 0)], 'lin'), 3.0, 0.0, '#e23b3b')
X_W = Key([(0, 5.25), (T_BW, 5.25), (8.35, 5.0), (8.8, 5.6), (9.4, 4.6), (10.4, 2.6), (11.6, 1.6), (13.0, 1.4), (99, 1.4)])
H_W = Key([(0, 0.0), (T_BW, 0.0), (8.35, -0.08), (8.8, 0.3), (9.3, -0.5), (10.0, -1.5), (10.8, -2.3), (11.8, -2.75), (13.0, -2.85), (99, -2.85)])


def pose_w(t):
    return X_W(t), _zW.z(t), H_W(t)


EXPR_W = lambda t: 'calm' if t < T_BW else 'shock'
LOOK0 = lambda t: 0.0


def occ_for(expr):
    def occ(t):
        def fn(ctx, view, Lf, h):
            person3d(ctx, view, Lf, -0.38, 0.05, 'hero', 0.0, expr(t))
        return fn
    return occ


HERO_W = BCar(pose_w, T_BW, occ_for(EXPR_W), brake=lambda t: 1.0 if 8.4 < t < 12.9 else 0.0, sparks=True)
Z_REST = _zW.z(13.5)
TRUCK_W = Track(1.75, Key([(0, 27.0), (12.6, 27.0), (14.0, 18.0), (99, 18.0)], 'lin'), T_FREEZE, Z_REST - 34.0, '#2f6f9f')
OTHERS_W = [Track(1.75, const(33.0), 3.0, 60.0, '#c9c9d6'), Track(5.25, const(V0), 3.0, 90.0, '#3a7bd5')]

# part 2: keeps it straight, coasts down, gentle brake + shoulder
S_R = Key([(0, V0), (T_BR, V0), (T_BR + 0.5, V0 - 0.6), (27.0, 14.5), (28.6, 9.0), (30.4, 0.0), (99, 0.0)], 'lin')
_zR = Track(0.0, S_R, T_R0, 0.0, '#e23b3b')
X_R = Key([(0, 5.25), (T_BR, 5.25), (T_BR + 0.35, 5.08), (T_BR + 1.0, 5.2), (25.6, 5.25), (28.4, 8.4), (99, 8.4)])
H_EXTRA = Key([(0, 0.0), (T_BR, 0.0), (T_BR + 0.3, -0.035), (T_BR + 0.9, 0.01), (T_BR + 1.4, 0.0), (99, 0.0)])


def pose_r(t):
    x = X_R(t)
    z = _zR.z(t)
    dx = (X_R(t + 0.15) - X_R(t - 0.15)) / 0.3
    v = max(0.5, S_R(t))
    return x, z, math.atan2(dx, v) + H_EXTRA(t)


T_HAZ = 28.2
HERO_R = BCar(pose_r, T_BR, occ_for(lambda t: 'calm' if t < T_BR else ('focus' if t < 30.6 else 'relieved')), haz_from=T_HAZ,
              blink=blink_side([(25.0, T_HAZ)], 'R'), brake=lambda t: 1.0 if 27.0 < t < 30.6 else 0.0)
OTHERS_R = [Track(1.75, const(33.0), T_R0, 40.0 + 120 * i, c) for i, c in enumerate(['#c9c9d6', '#37b26c', '#f2a541'])]
OTHERS_R += [Track(1.75, const(32.0), T_R0, -60.0 - 90 * i, c) for i, c in enumerate(['#3a7bd5', '#1c1c22'])]
Z_STOP = _zR.z(31.0)
PED_T = [31.4, 32.4, 99]
WALK = Ped(lambda t: float(np.interp(t, PED_T, [8.4 + 1.1, 13.0, 13.0])), lambda t: float(np.interp(t, PED_T, [Z_STOP + 0.5, Z_STOP - 8.0, Z_STOP - 8.0])),
           top='#d0912c', pants='#2b3a63', skin='#e9b98f', hair='#3a2316')


class WalkHero:
    def x(self, t):
        return WALK.x(t)

    def z(self, t):
        return WALK.z(t)

    def draw(self, ctx, view, t):
        if t >= PED_T[0]:
            WALK.draw(ctx, view, t)


class Semi:
    def __init__(self, tr):
        self.tr = tr
        self.col = '#2f6f9f'

    def visible(self, t):
        return True

    def pose(self, t):
        return self.tr.pose(t)

    def items(self, ctx, view, t):
        x, z, h = self.tr.pose(t)
        if view.ortho:
            return [((x, 1, z), lambda: (fill_poly(ctx, view, [(x - 1.3, 0, z - 17), (x + 1.3, 0, z - 17), (x + 1.3, 0, z + 5), (x - 1.3, 0, z + 5)], hexc('#f4f4f6'), OUTL, 3)))]
        br = self.tr.sk(t + 0.2) < self.tr.sk(t) - 0.1
        return [((x, 1.5, z + 2.5), lambda: tractor_det(ctx, view, x, z, h, '#2f6f9f', False, None, br)),
                ((x, 2.0, z - 7.2), lambda: trailer_det(ctx, view, x, z, h, False, False, br, '#f4f4f6', '#e0393e', 'DESERT FREIGHT'))]


# ------------------------------------------------------------------ desert interstate
C_SAND = hexc('#d9a86c')


def joshua(ctx, view, x, z, s):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 0.8 * view.s, 0.8 * view.s)
        fill_stroke(ctx, hexc('#6f8f4a'), OUTL, 2)
        return
    b, sc = view.pt((x, 0, z)), view.scale((x, 0, z))
    if not b or not sc or sc < 0.6:
        return
    tp = (b[0], b[1] - 3.2 * s * sc)
    ctx.move_to(*b)
    ctx.line_to(*tp)
    setc(ctx, hexc('#7a5e3e'))
    ctx.set_line_width(max(2, 0.35 * s * sc))
    ctx.stroke()
    for k, (dx, dy) in enumerate(((-1.2, -1.0), (1.1, -1.3), (-0.6, -1.8), (0.7, -0.6))):
        e = (tp[0] + dx * s * sc, tp[1] + dy * s * sc)
        ctx.move_to(tp[0], tp[1] + 0.5 * s * sc)
        ctx.curve_to(tp[0] + dx * 0.4 * s * sc, tp[1], e[0], e[1] + 0.6 * s * sc, *e)
        setc(ctx, hexc('#7a5e3e'))
        ctx.set_line_width(max(2, 0.25 * s * sc))
        ctx.stroke()
        ellipse(ctx, e[0], e[1], 0.45 * s * sc, 0.38 * s * sc)
        fill_stroke(ctx, hexc('#6f8f4a'), OUTL, max(1, sc * 0.05))


def mesa(ctx, view, x, z, w, d, hgt, col):
    from truckkit import solid
    Lf = lambda a, b, c: (a, b, c)
    c = hexc(col)
    bot = [(x - w, 0, z - d), (x + w, 0, z - d), (x + w, 0, z + d), (x - w, 0, z + d)]
    top = [(x - w * 0.7, hgt, z - d * 0.7), (x + w * 0.7, hgt, z - d * 0.7), (x + w * 0.7, hgt, z + d * 0.7), (x - w * 0.7, hgt, z + d * 0.7)]
    haze = hexc('#f0b98a')
    k = clamp(math.hypot(view.pos[0] - x, view.pos[2] - z) / 2500) * 0.6
    cc = mix(c, haze, k)
    solid(ctx, view, Lf, bot, top, {'front': cc, 'back': cc, 'left': mix(cc, (0, 0, 0), 0.15), 'right': mix(cc, (0, 0, 0), 0.08),
                                    'top': mix(cc, (1, 1, 1), 0.1)}, 2)


def green_sign(ctx, view, x, z):
    if view.ortho:
        return
    for px in (x - 1.8, x + 1.8):
        a, b = view.pt((px, 0, z)), view.pt((px, 3.2, z))
        if a and b:
            ctx.move_to(*a)
            ctx.line_to(*b)
            setc(ctx, hexc('#6a6f7c'))
            ctx.set_line_width(max(2, (view.scale((px, 1, z)) or 10) * 0.12))
            ctx.stroke()
    if fill_poly(ctx, view, [(x - 2.6, 3.2, z), (x + 2.6, 3.2, z), (x + 2.6, 5.2, z), (x - 2.6, 5.2, z)], hexc('#1f6f43'), (1, 1, 1), 3):
        c, s = view.pt((x, 4.2, z)), view.scale((x, 4.2, z))
        if c and s and s > 5:
            text_center(ctx, 'Las Vegas  35', c[0], c[1] - 0.05 * s, 0.55 * s, (1, 1, 1))
            text_center(ctx, 'I-15 NORTH', c[0], c[1] + 0.6 * s, 0.38 * s, (1, 1, 1))


class Desert:
    sky = SKY

    def __init__(self):
        self.ground_col = C_SAND
        r = random.Random(8)
        self.items = []
        for z in np.arange(-400, 1400, 12):
            if r.random() < 0.55:
                self.items.append(('jt', (r.uniform(13, 60), z + r.uniform(-4, 4), r.uniform(0.8, 1.3))))
            if r.random() < 0.45:
                self.items.append(('jt', (-r.uniform(4, 14), z + r.uniform(-4, 4), r.uniform(0.8, 1.2))))
            if r.random() < 0.6:
                self.items.append(('shrub', (r.uniform(11, 80) * r.choice([-1, 1]), z + r.uniform(-5, 5))))
        self.mesas = [(380, 900, 160, 90, 75, '#b5523b'), (-420, 1300, 220, 120, 95, '#c0643f'), (600, 1700, 250, 140, 120, '#a8492f'),
                      (-150, 2200, 300, 150, 110, '#b85a3a')]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        hy = view.horizon()
        glow(ctx, 1250, hy - 60, 420, hexc('#ffd27a'), 0.8)
        ellipse(ctx, 1250, hy - 60, 70, 70)
        setc(ctx, hexc('#fff1c9'))
        ctx.fill()
        mountains(ctx, view, [(-2600, 0), (-1900, 260), (-1300, 120), (-700, 300), (-100, 160), (500, 340), (1200, 170), (1800, 300), (2600, 0)], 3400, snow=False)
        towers(ctx, view, 3000, -120, 160, 14, 60, 190, seed=3, base='#8a6f8f', haze='#f0b98a')
        for m in self.mesas:
            mesa(ctx, view, *m)

    def ground(self, ctx, view, t):
        ex, ez = view.pos[0], view.pos[2]
        zlo, zhi = (ez - 200, ez + 1500) if not view.ortho else (view.zc - 80, view.zc + 80)
        gquad(ctx, view, -0.8, 10.0, zlo, zhi, hexc('#8d8f96'))
        gquad(ctx, view, 0.0, 7.0, zlo, zhi, C_ASPH)
        gquad(ctx, view, -27.0, -16.0, zlo, zhi, C_ASPH)
        for k in range(int(zlo // 12), int(zhi // 12) + 1):
            gquad(ctx, view, 3.43, 3.57, k * 12, k * 12 + 4, C_LINE, 0.01)
            gquad(ctx, view, -21.57, -21.43, k * 12, k * 12 + 4, C_LINE, 0.01)
        gquad(ctx, view, 0.05, 0.2, zlo, zhi, C_YEL, 0.01)
        gquad(ctx, view, 6.85, 7.0, zlo, zhi, C_LINE, 0.01)
        if not view.ortho:
            for k in range(int(zlo // 1.2), int(min(zhi, ez + 120) // 1.2) + 1):
                gquad(ctx, view, 7.3, 7.7, k * 1.2, k * 1.2 + 0.35, hexc('#6f7380'), 0.012)

    def objects(self, ctx, view, t):
        out = []
        ez = view.pos[2] if not view.ortho else view.zc
        for kind, a in self.items:
            if not (ez - 60 < a[1] < ez + 700):
                continue
            if kind == 'jt':
                out.append(((a[0], 2, a[1]), lambda a=a: joshua(ctx, view, a[0], a[1], a[2])))
            else:
                out.append(((a[0], 0.4, a[1]), lambda a=a: shrub(ctx, view, a[0], a[1])))
        for zs in (120.0, 560.0):
            out.append(((3.5, 4, zs), lambda zs=zs: green_sign(ctx, view, 3.5, zs) if False else green_sign(ctx, view, 11.8, zs)))
        return out


world = SegWorld(DUR, [hook_seg(0, 3.0, T_BW - 1.7, HERO_W, [Semi(TRUCK_W)] + OTHERS_W, []),
                       (3.0, T_R0, HERO_W, [Semi(TRUCK_W)] + OTHERS_W, []),
                       (T_R0, 99, HERO_R, OTHERS_R, [WalkHero()])], Desert(), 'mph')
world.police_flash = lambda t: 0.0


# ------------------------------------------------------------------ scenes
def warm(ctx, a=0.08):
    setc(ctx, hexc('#ff9a5a'), a)
    ctx.paint()


def b_cam(ctx, w, t, lt, kw):
    tf = min(t, kw['freeze']) if 'freeze' in kw else t
    e = w.ego(tf)
    x, z, h = e.pose(tf)
    m = kw['cam']
    if m == 'fixed':
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000))
    elif m == 'rel':                      # camera offset relative to the car (car frame), looking at a car-frame point
        Lf = L(x, z, 0.0 if kw.get('world_aligned') else h)
        ox, oy, oz = kw['off']
        tx, ty, tz = kw['look']
        P, T_ = Lf(ox, oy, oz), Lf(tx, ty, tz)
        view = look_at(P, T_, kw.get('f', 950))
    elif m == 'chase':
        zz = z
        view = TCam((x - 0.0, 3.6, zz - 10.5), 0.0, 0.16, 1000, cy=520)
    elif m == 'high':
        view = TCam((3.5, 12.0, z - 16), 0.0, 0.5, 1000, cy=470)
    elif m == 'inside':
        fx, fz = math.sin(h), math.cos(h)
        rx, rz = math.cos(h), -math.sin(h)
        view = TCam((x - rx * 0.38 - fx * 0.2, 1.14, z - rz * 0.38 - fz * 0.2), h, 0.03, 1000, cy=470)
    shake = 0.0
    if 0 <= tf - e.t_blow < 0.6:
        shake = 1 - (tf - e.t_blow) / 0.6
    if shake and isinstance(view, TCam):
        view = TCam((view.pos[0] + 0.12 * shake * math.sin(t * 70), view.pos[1] + 0.08 * shake * math.cos(t * 61), view.pos[2]),
                    view.yaw, view.pitch, view.f, view.cx, view.cy)
    draw_scene(ctx, view, w, tf, ego=m != 'inside')
    if m == 'inside':
        citykit.cockpit(ctx, w, tf)
        if 0 <= tf - e.t_blow < 0.5:
            label(ctx, 960, 300, 'BANG!', '#e0393e', 90)
    warm(ctx)
    if 'freeze' in kw and t >= kw['freeze']:
        u = t - kw['freeze']
        setc(ctx, (1, 1, 1), max(0, 0.8 - u * 3))
        ctx.paint()
        setc(ctx, (0.6, 0, 0), 0.22)
        ctx.paint()
    if kw.get('hud', m in ('chase', 'inside', 'rel')):
        big_speed(ctx, w, tf, kw.get('bigspeed', False))
    if kw.get('post'):
        kw['post'](ctx, view, tf, lt)


def big_speed(ctx, w, t, big):
    v = w.speed(t) * 2.237
    if big:
        rrect(ctx, 1420, 40, 460, 190, 40)
        setc(ctx, (0, 0, 0), 0.6)
        ctx.fill()
        text_center(ctx, f'{int(round(v))}', 1590, 185, 130, hexc('#ffd23f'))
        text_center(ctx, 'mph', 1790, 185, 44, (0.9, 0.9, 0.95))
        return
    hud(ctx, w, t)


def tire_close(ctx, w, t, lt, kw):
    """Low camera beside the front-left wheel."""
    e = w.ego(t)
    x, z, h = e.pose(t)
    Lf = L(x, z, h)
    view = look_at(Lf(-2.4, 0.55, 3.4), Lf(-0.7, 0.35, 1.0), 900)
    draw_scene(ctx, view, w, t)
    warm(ctx, 0.06)
    hud(ctx, w, t)


class Strip:
    """Map strip: distance along the road to the right (5.4 px/m), lanes exaggerated across (52 px/m)."""
    ortho = True
    hrot = math.pi / 2

    def __init__(self, oy):
        self.oy, self.s, self.pos = oy, 13.0, (0, 1000, 0)
        self.xc, self.zc = 5.0, 0.0

    def pt(self, P):
        return (110 + P[2] * 5.4, self.oy + (P[0] - 5.0) * 34)

    def poly(self, pts):
        return [self.pt(p) for p in pts]

    def depth(self, P):
        return 0.0

    def scale(self, P):
        return self.s


def top_compare(ctx, w, t, lt, kw):
    """Map view, two strips: the panic path (spin) vs the calm path (straight, coast, shoulder)."""
    setc(ctx, C_SAND)
    ctx.paint()
    u = smooth(lt / 2.0)
    for oy, t0, t1, posef, zb, col, txt, lcol in ((330, T_BW - 0.6, 13.0, pose_w, _zW.z(T_BW), '#ff4b4b', 'PANIC: brake hard + yank = SPIN', '#e0393e'),
                                                   (790, T_BR - 0.6, 31.0, pose_r, _zR.z(T_BR), '#22c35e', 'CALM: straight, coast, then shoulder', '#22a356')):
        v = Strip(oy)
        gquad(ctx, v, -0.8, 10.0, -10, 340, hexc('#8d8f96'))
        gquad(ctx, v, 0.0, 7.0, -10, 340, C_ASPH)
        for k in range(-1, 30):
            gquad(ctx, v, 3.43, 3.57, k * 12, k * 12 + 4, C_LINE)
        gquad(ctx, v, 6.85, 7.0, -10, 340, C_LINE)
        ts = np.arange(t0, t0 + (t1 - t0) * u + 0.001, 0.05)
        pts = []
        for s_ in ts:
            x, z, h = posef(s_)
            pts.append(v.pt((x, 0, z - zb)))
        if len(pts) > 2:
            arrow_path(ctx, pts, hexc(col), 10, 1.0, None, 26)
        x, z, h = posef(ts[-1])
        draw_car_top_g(ctx, v, x, z - zb, h, '#e23b3b', t)
        b = v.pt((5.25, 0, 0))
        ellipse(ctx, b[0], b[1], 16, 16)
        fill_stroke(ctx, hexc('#ffd23f'), OUTL, 4)
        label(ctx, 600, oy - 215, txt, lcol, 46)
    b = Strip(330).pt((5.25, 0, 0))
    label(ctx, b[0] + 40, b[1] + 95, 'BANG', '#3a3d48', 30)


def pressure_card(ctx, w, t, lt, kw):
    g = cairo.LinearGradient(0, 0, 0, SH)
    g.add_color_stop_rgb(0, *hexc('#5a3f8c'))
    g.add_color_stop_rgb(1, *hexc('#ffb36b'))
    ctx.set_source(g)
    ctx.paint()
    # gauge
    cx, cy = 600, 560
    ellipse(ctx, cx, cy, 300, 300)
    fill_stroke(ctx, (1, 1, 1), OUTL, 10)
    for k in range(11):
        a = math.pi * (0.75 + 1.5 * k / 10)
        ctx.move_to(cx + math.cos(a) * 250, cy + math.sin(a) * 250)
        ctx.line_to(cx + math.cos(a) * 285, cy + math.sin(a) * 285)
        setc(ctx, OUTL)
        ctx.set_line_width(8)
        ctx.stroke()
    for lo, hi, col in ((0, 0.45, '#ff4b4b'), (0.45, 0.75, '#22c35e'), (0.75, 1.0, '#ffd23f')):
        ctx.arc(cx, cy, 220, math.pi * (0.75 + 1.5 * lo), math.pi * (0.75 + 1.5 * hi))
        setc(ctx, hexc(col))
        ctx.set_line_width(30)
        ctx.stroke()
    v = 0.3 + 0.32 * smooth((lt - 0.5) / 1.2)
    a = math.pi * (0.75 + 1.5 * v)
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(a) * 200, cy + math.sin(a) * 200)
    setc(ctx, OUTL)
    ctx.set_line_width(16)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ellipse(ctx, cx, cy, 30, 30)
    setc(ctx, OUTL)
    ctx.fill()
    text_center(ctx, 'PSI', cx, cy + 150, 60, OUTL)
    text_center(ctx, 'Low pressure', 1350, 360, 64, (1, 1, 1))
    text_center(ctx, '= hot tire = blowout risk', 1350, 450, 54, (1, 1, 1))
    if lt > 1.0:
        label(ctx, 1350, 620, 'Check pressure monthly', '#22a356', 56)
    if lt > 1.7:
        label(ctx, 1350, 760, "Use the number on the driver's door", '#3a3d48', 42)


engine.SCENES.update(b_cam=b_cam, tire_close=tire_close, top_compare=top_compare, pressure_card=pressure_card)

REAR_W = dict(cam='rel', off=(1.6, 1.4, 9.0), look=(0.0, 0.8, -14.0), f=900, world_aligned=True, freeze=T_FREEZE, hud=False)
WIDE_R = dict(cam='fixed', pos=(16.0, 2.4, 0.0), target=(8.0, 0.8, 0.0), f=950, hud=False)
defs = [
    (3.0, 'tire_close', dict()),
    (6.0, 'b_cam', dict(cam='chase')),
    (8.4, 'tire_close', dict()),
    (10.5, 'b_cam', dict(cam='inside')),
    (13.0, 'b_cam', dict(cam='high', hud=False)),
    (15.5, 'b_cam', dict(REAR_W)),
    (T_R0, 'rewind_seq', dict()),
    (19.2, 'b_cam', dict(cam='chase')),
    (21.7, 'b_cam', dict(cam='inside')),
    (24.7, 'b_cam', dict(cam='chase', bigspeed=True)),
    (27.7, 'b_cam', dict(cam='high', hud=False)),
    (30.7, 'top_compare', dict()),
    (33.5, 'b_cam', dict(cam='fixed', pos=(16.0, 2.2, Z_STOP + 14.0), target=(8.4, 0.9, Z_STOP - 2.0), f=900, hud=False)),
    (DUR, 'pressure_card', dict()),
]
shots = build_shots(defs)
shots[6].kw.update(srcs=list(reversed(shots[1:6])), dur=shots[6].dur)
video = Video(['BANG! Tire blowout at 70 mph.', 'What do you do?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Front tire blows at 70 mph...', 300, 100, hexc('#ffd23f'), 0.2, True)),
    (3.0, 6.0, location_tag('I-15 near Las Vegas, Nevada')),
    (3.2, 6.0, caption('Cruising at 70 mph...')),
    (S[2], E[5], badge('PANIC', '#e0393e')),
    (S[2] + 0.4, E[2], caption('BANG! The front tire blows')),
    (S[3] + 0.2, E[3], caption('He slams the brakes and yanks the wheel')),
    (S[4] + 0.2, E[4], caption('The car spins out of control')),
    (S[5] + 0.2, E[5], caption('...right in front of a truck')),
    (S[5] + 2.2, E[5], x_mark),
    (S[7], E[7], badge('CALM', '#22a356')),
    (S[7] + 0.2, E[7], caption('Same blowout. Now stay calm.')),
    (S[12] + 0.2, E[12], caption('Hazards on. Wait well away from traffic.')),
    (S[13], E[13], end_card('Grip. Ease off. Coast. Pull over.', 'Would YOU stay calm? Comment YES or NO')) if False else
    (S[13] + 2.4, E[13], lambda ctx, lt, d: label(ctx, 960, 980, 'Would YOU stay calm? Comment YES or NO', '#e0393e', 50)),
]
for n, (i, txt) in enumerate(((8, 'Grip the wheel. Keep it STRAIGHT.'), (9, "Don't brake hard. Ease OFF the gas."),
                              (10, 'Slow? Brake gently, signal, shoulder.')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]


# ------------------------------------------------------------------ sound
def flap(d, rate_fn):
    n = int(d * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    ph = 0.0
    k = 0
    for i in range(0, n, 64):
        ph += rate_fn(tt[i]) * 64 / SR
        if ph >= 1:
            ph -= 1
            m = min(n - i, int(0.03 * SR))
            out[i:i + m] += lp(noise(m), 900) * np.exp(-np.arange(m) / SR / 0.008) * 1.4
    return out


def pop_bang():
    n = int(0.7 * SR)
    tt = np.arange(n) / SR
    return (noise(n) * np.exp(-tt / 0.05) * 1.2 + lp(noise(n), 200) * np.exp(-tt / 0.2) * 2.0)


def sound():
    m = Mixer(video.dur)
    m.add(lp(noise(int(video.dur * SR)), 300), 0, 0.12)                  # desert wind
    hook_sfx(m)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.14)
    hb = 1.7                                                             # hook shows t = 6.3..9.3 -> blowout at 1.7
    m.add(pop_bang(), hb, 1.0)
    m.add(flap(1.3, lambda t: 9.0), hb + 0.05, 0.6)
    m.add(pop_bang(), T_BW, 1.0)
    m.add(flap(T_FREEZE - T_BW - 1.5, lambda t: max(1.5, 11 - t * 2.2)), T_BW + 0.05, 0.6)
    m.add(screech(3.6, 1050), 8.4, 0.75)
    m.add(heartbeat(4, 140), 10.6, 0.7)
    m.add(horn(1.6, [0.72] * 4), 13.2, 0.9)
    m.add(brake_squeal(1.4), 13.0, 0.5)
    m.add(sad_violin(), T_FREEZE + 0.1, 0.85)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(pop_bang(), T_BR, 1.0)
    m.add(flap(31.0 - T_BR, lambda t: max(0.0, 10.5 - t * 0.9)), T_BR + 0.05, 0.5)
    for i in (8, 9, 10):
        m.add(pop(), S[i] + 0.15, 0.6)
    m.add(click(), 25.0, 0.7)
    indicator(m, 25.0, T_HAZ, 0.4, 0.2)
    indicator(m, T_HAZ, 34.0, 0.35, 0.0)
    m.add(car_pass(2.0, 0.5, 100), 33.6, 0.4, np.linspace(-0.6, 0.6, int(2.0 * SR)))
    m.add(chime(), S[11] + 0.6, 0.6)
    m.add(success_jingle(), S[13] + 0.4, 0.8)
    return m.out(video.dur)


def verify():
    print('wrong: car rests at x', X_W(13.5), 'z', round(Z_REST, 1), 'heading', round(math.degrees(H_W(13.5))),
          '| truck gap at freeze', round(Z_REST - TRUCK_W.z(T_FREEZE) - 2.2 - 5.0, 1), 'm, truck speed', TRUCK_W.speed(T_FREEZE))
    print('   other cars ahead stay clear:', [round(o.z(t) - _zW.z(t), 1) for o in OTHERS_W for t in (8.0, 12.0)])
    print('right: speed at 27.0 =', round(S_R(27.0) * 2.237), 'mph; on shoulder x', X_R(29), '(shoulder 7.0..10.0, car half 0.92)',
          '| stops at', round(Z_STOP, 1))
    gaps = []
    for t in np.arange(T_R0, DUR, 0.05):
        x, z, h = pose_r(t)
        for o in OTHERS_R:
            if abs(o.pose(t)[0] - x) < 2.0:
                gaps.append(abs(o.z(t) - z) - 4.4)
    print('   min gap to cars sharing a lane:', round(min(gaps), 2) if gaps else 'none')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        run(video, sound, 'blowout.mp4')
