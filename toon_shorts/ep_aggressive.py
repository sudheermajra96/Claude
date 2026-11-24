"""Aggressive driver on the highway (cinematic, SQUARE 1:1). I-85 into Atlanta, Georgia, at golden hour.

World: +Z = travel (into Atlanta). Four lanes x = 1.75 / 5.25 / 8.75 / 12.25 (lane 1 = left/fast lane), right
shoulder 14.0 .. 17.5, concrete median barrier at x = -0.6, opposite carriageway x -2 .. -16.
Traffic cruises at V = 29 m/s (65 mph). The aggressive driver (A, charcoal coupe) does up to 100 mph: weaves
through traffic, tailgates our hero with flashing high beams + horn, our hero stays calm, signals and moves
right, A blasts past, cuts off a semi (truck brakes hard), then nearly rear-ends slowing traffic (slow motion),
police pull him over. Hero passes him a minute later: time saved = 0.
Every vehicle pair is checked for gaps in verify().
"""
import math
import random

import cairo
import numpy as np

from mkit import *
from truckkit import draw_car_round, tractor_det, trailer_det
from peoplekit import *
import citykit
import engine
from sqkit import *
import cinekit
from cinekit import shadow, shake, heli, look, sun_flare, warm_haze, speed_streaks, grade, whip

V = 29.0
LANES = [1.75, 5.25, 8.75, 12.25]
SHOULDER = 15.6
T_TAIL0, T_TAIL1 = 9.4, 13.4
T_SIG, T_LC0, T_LC1 = 11.4, 12.8, 14.2
T_CUT0, T_CUT1 = 17.25, 17.95
T_SLAM = 20.2
SM0, SM1, SMK = 19.6, 22.6, 0.4           # slow motion (video time) and its speed


# ------------------------------------------------------------------ time map (slow motion)
def wt(vt):
    if vt < SM0:
        return vt
    if vt < SM1:
        return SM0 + (vt - SM0) * SMK
    return vt - (SM1 - SM0) * (1 - SMK)


def vt_of(w):
    if w < SM0:
        return w
    if w < SM0 + (SM1 - SM0) * SMK:
        return SM0 + (w - SM0) / SMK
    return w + (SM1 - SM0) * (1 - SMK)


# ------------------------------------------------------------------ vehicles
class Veh(Track):
    def __init__(self, x, speed, ta, za, col, kind='car', occ=None, flash=None, police=None, brake=None):
        super().__init__(x, speed, ta, za, col, brake=brake, t0=-3, t1=60)
        self.kind, self.occ, self.flash, self.police = kind, occ, flash, police
        self.ext = (-15.5, 5.6, 1.3, 4.0) if kind == 'semi' else (-2.25, 2.25, 0.95, 1.45)

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        if not view.ortho:
            d = view.depth((x, 1, z))
            if d < -25 or d > 650:
                return []
        if self.kind == 'semi':
            br = self.brake(t) > 0.5
            return [((x + math.sin(h) * 2.5, 1.5, z + math.cos(h) * 2.5), lambda: tractor_det(ctx, view, x, z, h, '#2f6f9f', False, None, br)),
                    ((x - math.sin(h) * 7.2, 2.0, z - math.cos(h) * 7.2),
                     lambda: trailer_det(ctx, view, x, z, h, False, False, br, '#f4f4f6', '#e0393e', 'PEACH STATE'))]

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, self.blink(t), self.occ is not None)
                return
            draw_car_round(ctx, view, x, z, h, self.col, t, self.blink(t), self.brake(t), occ=self.occ(t) if self.occ else None)
            Lf = L(x, z, h)
            if self.flash and self.flash(t):
                for sx in (-0.62, 0.62):
                    P = Lf(sx, 0.68, 2.26)
                    p, s = view.pt(P), view.scale(P)
                    if p and s and view.to_cam(P)[2] > 0 and (math.sin(h) * (view.pos[0] - x) + math.cos(h) * (view.pos[2] - z)) > 0:
                        glow(ctx, p[0], p[1], min(1.2 * s + 30, 200), (1.0, 0.97, 0.85), 0.9)
            if self.police and self.police(t):
                on = (t * 2.6) % 1 < 0.5
                for sx, col in ((-0.3, (1.0, 0.15, 0.15)), (0.3, (0.2, 0.35, 1.0))):
                    P = Lf(sx, 1.62, -0.3)
                    p, s = view.pt(P), view.scale(P)
                    lit_ = on if sx < 0 else not on
                    if p and s:
                        rrect(ctx, p[0] - 0.14 * s, p[1] - 0.05 * s, 0.28 * s, 0.1 * s, 0.03 * s)
                        fill_stroke(ctx, col if lit_ else mix(col, (0, 0, 0), 0.6), OUTL, 1)
                        if lit_:
                            glow(ctx, p[0], p[1], min(0.8 * s + 10, 120), col, 0.8)
        return [((x, 0.8, z), fn)]


class Rev:
    """Opposite carriageway (travels -z)."""

    def __init__(self, x, z0, col, v=28.0):
        self.x, self.z0, self.col, self.v = x, z0, col, v
        self.kind = 'car'
        self.ext = (-2.25, 2.25, 0.95, 1.45)

    def pose(self, t):
        return self.x, self.z0 - self.v * t, math.pi

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        if not view.ortho:
            d = view.depth((x, 1, z))
            if d < -25 or d > 500:
                return []
        return [((x, 0.8, z), lambda: draw_car_round(ctx, view, x, z, h, self.col, t) if not view.ortho
                 else draw_car_top_g(ctx, view, x, z, h, self.col, t))]


def hero_occ(t):
    def fn(ctx, view, Lf, h):
        e = 'calm' if t < T_TAIL0 + 0.6 else ('worried' if t < T_LC1 else 'calm')
        person3d(ctx, view, Lf, -0.38, 0.05, 'hero', 0.0, e)
    return fn


def a_occ(t):
    def fn(ctx, view, Lf, h):
        person3d(ctx, view, Lf, -0.38, 0.05, 'husb', 0.0, 'shock' if T_SLAM < t < T_SLAM + 3 else 'annoyed')
    return fn


# hero: lane 2, then signals and moves to lane 3; slows when the truck ahead brakes
HERO = Veh(Key([(0, LANES[1]), (T_LC0, LANES[1]), (T_LC1, LANES[2]), (99, LANES[2])]),
           Key([(0, V), (14.4, V), (15.4, V - 4.0), (18.1, V - 4.0), (19.3, V - 10.0), (20.8, V - 10.0), (23.4, V), (99, V)], 'lin'),
           0.0, 0.0, '#e23b3b', occ=hero_occ)
HS = HERO.sk
HERO.blink = blink_side([(T_SIG, T_LC1 + 0.3)], 'R')

# aggressive driver
A_X = Key([(0, LANES[2]), (3.9, LANES[2]), (4.7, LANES[3]), (6.2, LANES[3]), (7.6, LANES[1]), (T_CUT0, LANES[1]), (T_CUT1, LANES[2]),
           (18.8, LANES[2]), (19.5, LANES[3]), (22.8, LANES[3]), (24.6, SHOULDER), (99, SHOULDER)])
A_S = Key([(0, 38.0), (8.6, 38.0), (9.4, V), (13.4, V), (14.6, 47.0), (T_SLAM, 47.0), (T_SLAM + 1.6, 19.0), (22.8, 19.0),
           (25.2, 0.0), (99, 0.0)], 'lin')
AGG = Veh(A_X, A_S, 3.0, 29.0 * 3 - 62.0, '#30333d', occ=a_occ,
          flash=lambda t: T_TAIL0 + 0.2 < t < T_TAIL1 and (t * 4.0) % 1 < 0.5)

# the semi in lane 3 ahead of the hero; brakes hard when cut off
SEMI = Veh(LANES[2], Key([(0, V), (18.0, V), (19.2, V - 9.0), (20.0, V - 9.0), (22.2, V), (99, V)], 'lin'), 0.0, 40.0, '#2f6f9f', kind='semi')

# police: comes up from far behind in lane 4 (defined by its distance behind A), lights on, follows A to the shoulder
class Police(Veh):
    G = Key([(0, 420.0), (18.6, 140.0), (20.8, 34.0), (22.8, 16.0), (25.2, 11.4), (99, 11.4)])

    def z(self, t):
        return AGG.z(t) - self.G(t)


POL = Police(Key([(0, LANES[3]), (23.4, LANES[3]), (25.2, SHOULDER), (99, SHOULDER)]), const(V), 0.0, 0.0, '#f4f4f6',
             police=lambda t: t > 20.6)

# traffic (all relative to the hero at t = 0: z = r)
COLS = ['#3a7bd5', '#f2a541', '#c9c9d6', '#37b26c', '#f4f4f6', '#7a4fd0', '#2f6f73', '#d8c3a0', '#e05d5d', '#1c1c22']
TRAF = []


def car(lane, r, col, speed=None):
    v = Veh(LANES[lane], speed or const(V), 0.0, r, col)
    TRAF.append(v)
    return v


WAVE2_ = Key([(0, V), (19.6, V), (21.2, V - 9.0), (23.6, V - 9.0), (25.8, V), (99, V)], 'lin')
C1 = car(2, -40.0, COLS[0], HS)
C2 = Veh(Key([(0, LANES[3]), (11.0, LANES[3]), (12.4, LANES[2]), (99, LANES[2])]), HS, 0.0, -20.0, COLS[1])
TRAF.append(C2)
car(0, -30.0, COLS[2])
car(0, 25.0, COLS[3])
car(1, 100.0, COLS[4], WAVE2_)
car(2, 120.0, COLS[5], Key([(0, V), (19.6, V), (21.2, V - 9.0), (23.6, V - 9.0), (25.8, V), (99, V)], 'lin'))
car(1, -60.0, COLS[6])
# lane 4 traffic that slows down ahead (the brake-light wave)
WAVE = Key([(0, V), (19.3, V), (20.8, V - 11.0), (23.4, V - 11.0), (25.6, V), (99, V)], 'lin')


def _wave_gap(off):
    c = Veh(LANES[3], WAVE, 0.0, 124.0 + off, '#000')
    g = 99.0
    for t in np.arange(19.4, 25.0, 0.02):
        x, z, h = AGG.pose(t)
        if abs(x - LANES[3]) < 2.2:
            g = min(g, (c.z(t) - 2.25) - (z + 2.25))
    return g


WAVE_OFF = min(np.arange(-30, 30, 0.1), key=lambda o: abs(_wave_gap(o) - 1.8) if _wave_gap(o) > 0 else 99)
C5 = car(3, 124.0 + WAVE_OFF, COLS[7], WAVE)
car(3, 136.0 + WAVE_OFF, COLS[8], WAVE)
car(3, 148.0 + WAVE_OFF, COLS[9], WAVE)
WAVE2 = Key([(0, V), (19.6, V), (21.2, V - 9.0), (23.6, V - 9.0), (25.8, V), (99, V)], 'lin')
car(2, 150.0, COLS[0], WAVE2)
car(1, 138.0, COLS[1], WAVE2)
car(0, 128.0, COLS[2], WAVE2)
for i in range(6):
    car(i % 4, 230.0 + 26 * i, COLS[(i + 3) % 10])
ONC = [Rev(-5.0 if i % 2 else -11.0, -200 + 47 * i, COLS[(i * 3) % 10]) for i in range(40)]
ALL = [HERO, AGG, SEMI, POL] + TRAF


# ------------------------------------------------------------------ skid smoke + marks
def rear_wheels(t):
    x, z, h = AGG.pose(t)
    Lf = L(x, z, h)
    return Lf(-0.8, 0.2, -1.38), Lf(0.8, 0.2, -1.38)


T_SK0, T_SK1 = T_SLAM, T_SLAM + 1.6


class Smoke:
    col = '#ccc'

    def visible(self, t):
        return True

    def pose(self, t):
        return 0, 0, 0

    def items(self, ctx, view, t):
        if view.ortho or t < T_SK0:
            return []
        out = []
        for s in np.arange(T_SK0, min(t, T_SK1), 0.06):
            age = t - s
            if age > 2.5:
                continue
            for k, P in enumerate(rear_wheels(s)):
                r = 0.4 + age * 1.3
                Q = (P[0] + (k - 0.5) * age * 0.8, 0.3 + age * 0.9, P[2] + age * 3.0)

                def fn(Q=Q, r=r, age=age):
                    p, sc = view.pt(Q), view.scale(Q)
                    if p and sc:
                        ellipse(ctx, p[0], p[1], r * sc, r * sc * 0.8)
                        setc(ctx, (0.92, 0.9, 0.88), max(0, 0.55 - age * 0.22))
                        ctx.fill()
                out.append((Q, fn))
        return out


def skid_marks(ctx, view, t):
    if view.ortho or t < T_SK0:
        return
    ts = np.arange(T_SK0, min(t, T_SK1), 0.04)
    if len(ts) < 2:
        return
    for k in range(2):
        pts = [view.pt((rear_wheels(s)[k][0], 0.012, rear_wheels(s)[k][2])) for s in ts]
        pts = [p for p in pts if p]
        if len(pts) > 1:
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            setc(ctx, (0.1, 0.1, 0.12), 0.7)
            sc = view.scale(rear_wheels(ts[-1])[k]) or 10
            ctx.set_line_width(max(2, 0.22 * sc))
            ctx.stroke()


# ------------------------------------------------------------------ the highway at golden hour
C_GRASS_G = hexc('#9aa85a')


def light_pole(ctx, view, x, z):
    a, b = view.pt((x, 0, z)), view.pt((x, 12.0, z))
    if not a or not b:
        return
    s = view.scale((x, 6, z)) or 5
    ctx.move_to(*a)
    ctx.line_to(*b)
    setc(ctx, hexc('#8d8f96'))
    ctx.set_line_width(max(1.5, 0.22 * s))
    ctx.stroke()
    for sx in (-1, 1):
        c = view.pt((x + sx * 2.6, 12.3, z))
        if c:
            ctx.move_to(*b)
            ctx.line_to(*c)
            ctx.set_line_width(max(1.2, 0.14 * s))
            ctx.stroke()
            ellipse(ctx, c[0], c[1], max(2, 0.4 * s), max(1, 0.15 * s))
            setc(ctx, hexc('#55585f'))
            ctx.fill()


def gantry(ctx, view, z):
    for px in (-1.2, 17.8):
        a, b = view.pt((px, 0, z)), view.pt((px, 7.4, z))
        if a and b:
            ctx.move_to(*a)
            ctx.line_to(*b)
            setc(ctx, hexc('#7a7f8c'))
            ctx.set_line_width(max(2, 0.3 * (view.scale((px, 3, z)) or 5)))
            ctx.stroke()
    fill_poly(ctx, view, [(-1.2, 7.0, z), (17.8, 7.0, z), (17.8, 7.5, z), (-1.2, 7.5, z)], hexc('#7a7f8c'))
    for x0, x1, t1, t2 in ((1.0, 8.0, 'I-85 SOUTH', 'Downtown Atlanta'), (9.5, 16.5, 'EXIT 248', 'Freedom Pkwy')):
        if fill_poly(ctx, view, [(x0, 4.6, z), (x1, 4.6, z), (x1, 7.0, z), (x0, 7.0, z)], hexc('#1f6f43'), (1, 1, 1), 2):
            c, s = view.pt(((x0 + x1) / 2, 5.8, z)), view.scale(((x0 + x1) / 2, 5.8, z))
            if c and s and s > 4:
                text_center(ctx, t1, c[0], c[1] - 0.15 * s, 0.75 * s, (1, 1, 1))
                text_center(ctx, t2, c[0], c[1] + 0.75 * s, 0.6 * s, (1, 1, 1))


def atl_skyline(ctx, view):
    """Downtown Atlanta far ahead: tall towers in warm haze, a spire tower (BoA-plaza like) and a cylinder."""
    if view.ortho:
        return
    haze = hexc('#ffc89a')
    rnd = random.Random(17)
    Z = 2600.0
    for k in range(22):
        X = -380 + k * 38 + rnd.uniform(-10, 10)
        hgt = rnd.uniform(60, 190) * (1.3 if abs(X - 40) < 120 else 0.8)
        w = rnd.uniform(24, 40)
        b, tp, s = view.pt((X, 0, Z + rnd.uniform(-60, 60))), view.pt((X, hgt, Z)), view.scale((X, 0, Z))
        if b and tp and s:
            ctx.rectangle(b[0] - w * s / 2, tp[1], w * s, b[1] - tp[1])
            setc(ctx, mix(hexc('#7d6f86'), haze, 0.35 + 0.25 * rnd.random()))
            ctx.fill()
    X = 60.0
    b, s = view.pt((X, 0, Z - 40)), view.scale((X, 0, Z - 40))
    if b and s:
        col = mix(hexc('#6d6378'), haze, 0.3)
        ctx.rectangle(b[0] - 16 * s, b[1] - 250 * s, 32 * s, 250 * s)
        setc(ctx, col)
        ctx.fill()
        poly(ctx, [(b[0] - 16 * s, b[1] - 250 * s), (b[0] + 16 * s, b[1] - 250 * s), (b[0], b[1] - 290 * s)])
        ctx.fill()
        ctx.rectangle(b[0] - 1.5 * s, b[1] - 320 * s, 3 * s, 32 * s)
        setc(ctx, mix(hexc('#e8c070'), haze, 0.2))
        ctx.fill()
    X = -120.0
    b, s = view.pt((X, 0, Z - 20)), view.scale((X, 0, Z - 20))
    if b and s:
        rrect(ctx, b[0] - 14 * s, b[1] - 220 * s, 28 * s, 220 * s, 12 * s)
        setc(ctx, mix(hexc('#5f6f80'), haze, 0.3))
        ctx.fill()


class I85:
    sky = ('#3b6fb6', '#ffc791')

    def __init__(self):
        self.ground_col = C_GRASS_G
        r = random.Random(3)
        self.trees = [(r.uniform(24, 70), z + r.uniform(-4, 4), r.uniform(1.0, 1.5)) for z in np.arange(-400, 3000, 10)]
        self.trees += [(-r.uniform(22, 60), z + r.uniform(-4, 4), r.uniform(1.0, 1.5)) for z in np.arange(-400, 3000, 12)]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        far_line(ctx, view, 2400, lambda x: 22 + 9 * math.sin(x / 220), col='#7d8a5a')
        atl_skyline(ctx, view)

    def ground(self, ctx, view, t):
        ez = view.pos[2] if not view.ortho else view.zc
        zlo, zhi = ez - 300, ez + 2400
        gquad(ctx, view, -17.0, 18.5, zlo, zhi, hexc('#8d8f96'))
        gquad(ctx, view, -0.2, 14.0, zlo, zhi, hexc('#4f525d'))
        gquad(ctx, view, -16.0, -2.0, zlo, zhi, hexc('#4f525d'))
        for xl in (3.5, 7.0, 10.5, -5.5, -9.0, -12.5):
            for k in range(int(zlo // 12), int(min(zhi, ez + 900) // 12) + 1):
                gquad(ctx, view, xl - 0.08, xl + 0.08, k * 12, k * 12 + 4, (0.93, 0.93, 0.9), 0.01)
        gquad(ctx, view, 0.0, 0.15, zlo, zhi, C_YEL, 0.01)
        gquad(ctx, view, 13.85, 14.0, zlo, zhi, (0.93, 0.93, 0.9), 0.01)
        # subtle wheel-track darkening in every lane
        if not view.ortho:
            for xl in LANES:
                for d in (-0.8, 0.8):
                    gquad(ctx, view, xl + d - 0.3, xl + d + 0.3, zlo, min(zhi, ez + 600), hexc('#484b55'), 0.004)
            # median barrier (jersey)
            fill_poly(ctx, view, [(-0.6, 0, zlo), (-0.6, 0, zhi), (-0.45, 0.85, zhi), (-0.45, 0.85, zlo)], hexc('#c9c4ba'), OUTL, 1)
            fill_poly(ctx, view, [(-0.45, 0.85, zlo), (-0.45, 0.85, zhi), (-0.75, 0.85, zhi), (-0.75, 0.85, zlo)], hexc('#e2ddd2'))
            fill_poly(ctx, view, [(-0.9, 0, zlo), (-0.9, 0, zhi), (-0.75, 0.85, zhi), (-0.75, 0.85, zlo)], hexc('#b3ada2'), OUTL, 1)
        skid_marks(ctx, view, t)
        # vehicle shadows
        for a in [HERO, AGG, SEMI, POL] + TRAF + ONC:
            x, z, h = a.pose(t)
            if not view.ortho:
                d = view.depth((x, 1, z))
                if d < -25 or d > 500:
                    continue
            lo, hi, hw, hg = a.ext
            shadow(ctx, view, x, z, h, lo, hi, hw, hg)

    def objects(self, ctx, view, t):
        out = []
        ez = view.pos[2] if not view.ortho else view.zc
        for x, z, s in self.trees:
            if ez - 80 < z < ez + 900:
                out.append(((x, 2, z), lambda x=x, z=z, s=s: tree3(ctx, view, x, z, s * (0.45 if view.ortho else 1.0), int(abs(z)) % 3)))
        if not view.ortho:
            for k in range(int((ez - 60) // 70), int((ez + 900) // 70) + 1):
                z = k * 70.0
                out.append(((-0.7, 6, z), lambda z=z: light_pole(ctx, view, -0.7, z)))
            for zg in (640.0, 1500.0):
                if ez - 40 < zg < ez + 1600:
                    out.append(((8.0, 6, zg), lambda zg=zg: gantry(ctx, view, zg)))
        return out


class HWorld(SegWorld):
    pass


world = HWorld(60.0, [(0, 99, HERO, [AGG, SEMI, POL, Smoke()] + TRAF + ONC, [])], I85(), 'mph')
world.police_flash = lambda t: 0.0


# ------------------------------------------------------------------ cinematic scenes (square canvas 1920 x 1920)
CANVAS = 1920
FMUL = 1.4                 # longer lenses on the square canvas (less fish-eye, more cinematic)


def finish(ctx, view, t, lt, kw, streak=0.0):
    warm_haze(ctx, view, CANVAS)
    sun_flare(ctx, view, CANVAS, CANVAS, kw.get('flare', 1.0))
    speed_streaks(ctx, t, streak, CANVAS, CANVAS)
    grade(ctx, t, CANVAS, CANVAS)


def pos_of(a, t):
    return a.pose(t)


def cine(ctx, w, t, lt, kw):
    tf = t + kw.get('dt', 0.0)
    m = kw['cam']
    streak = 0.0
    if m == 'heli':                         # helicopter orbit around a target agent
        a = kw['target']
        x, z, h = a.pose(tf)
        view = heli((x + kw.get('ox', 0), 1.0, z + kw.get('oz', 0)), lt, kw['R'], kw['H'], kw['a0'], kw['w'], kw.get('f', 1000))
    elif m == 'track':                      # camera car alongside the target (low, shaky)
        a = kw['target']
        x, z, h = a.pose(tf)
        ox, oy, oz = kw['off']
        lag = kw.get('lag', 0.0)
        sh = kw.get('shake', 0.08)
        pos = (x + ox + shake(tf, sh, 1.6, 4), oy + shake(tf, sh * 0.7, 2.1, 5), z + oz - lag * lt)
        tx, ty, tz = kw.get('look', (0, 0.9, 0))
        view = look(pos, (x + tx, ty, z + tz), kw.get('f', 800))
        streak = kw.get('streak', 0.0)
    elif m == 'tele':                       # long lens from far ahead / behind
        a = kw['target']
        x, z, h = a.pose(tf)
        ox, oy, oz = kw['off']
        view = look((ox + shake(tf, 0.15, 0.5, 6), oy, z + oz), (x + kw.get('tx', 0), 1.2, z + kw.get('tz', 0)), kw.get('f', 2600))
    elif m == 'fixed':
        view = look(kw['pos'], kw['target_pt'], kw.get('f', 1000))
    elif m == 'crane':                      # rising + pushing in, aimed at a target
        a = kw['target']
        x, z, h = a.pose(tf)
        u = smooth(lt / kw['dur_'])
        y = kw['y0'] + (kw['y1'] - kw['y0']) * u
        ox, oz = kw['ox'], kw['oz0'] + (kw['oz1'] - kw['oz0']) * u
        view = look((x + ox, y, z + oz), (x + kw.get('tx', 0), 1.0, z + kw.get('tz', 0)), kw.get('f', 950))
    view = TCam(view.pos, view.yaw, view.pitch, view.f * FMUL, view.cx, view.cy)
    if kw.get('jolt'):
        t0, amp = kw['jolt']
        u = tf - t0
        if 0 <= u < 1.2:
            k = amp * (1 - u / 1.2)
            view = TCam((view.pos[0] + k * math.sin(tf * 70), view.pos[1] + k * 0.6 * math.cos(tf * 61), view.pos[2]),
                        view.yaw + k * 0.01 * math.sin(tf * 53), view.pitch, view.f, view.cx, view.cy)
    draw_scene(ctx, view, w, tf)
    finish(ctx, view, tf, lt, kw, streak)
    if kw.get('hud'):
        sq_hud(ctx, w, tf)
    if kw.get('post'):
        kw['post'](ctx, view, tf, lt)


def interior_mirror(ctx, w, t, lt, kw):
    """Driver's view: road ahead + rear-view mirror full of the tailgater's flashing high beams."""
    x, z, h = HERO.pose(t)
    view = TCam((x - 0.38, 1.18, z - 0.2), h, 0.04, 900, cx=960, cy=1060)
    draw_scene(ctx, view, w, t, ego=False)
    warm_haze(ctx, view, CANVAS)
    sun_flare(ctx, view, CANVAS, CANVAS, 0.8)
    # cabin: roof, A-pillars, dashboard, wheel
    setc(ctx, hexc('#25262f'))
    ctx.rectangle(-10, -10, CANVAS + 20, 240)
    ctx.fill()
    poly(ctx, [(-10, 220), (260, 220), (90, 1560), (-10, 1560)])
    ctx.fill()
    poly(ctx, [(CANVAS + 10, 220), (CANVAS - 260, 220), (CANVAS - 90, 1560), (CANVAS + 10, 1560)])
    ctx.fill()
    ctx.move_to(-10, 1540)
    ctx.curve_to(600, 1460, 1320, 1460, CANVAS + 10, 1540)
    ctx.line_to(CANVAS + 10, CANVAS + 10)
    ctx.line_to(-10, CANVAS + 10)
    ctx.close_path()
    g = cairo.LinearGradient(0, 1460, 0, 1920)
    g.add_color_stop_rgb(0, *hexc('#3a3b48'))
    g.add_color_stop_rgb(1, *hexc('#1c1c24'))
    ctx.set_source(g)
    ctx.fill()
    ctx.save()
    ctx.translate(960, 1990)
    ctx.rotate(HERO.steer(t) * 0.5)
    ellipse(ctx, 0, 0, 560, 430)
    ellipse(ctx, 0, 0, 490, 365)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#15151c'), OUTL, 5)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for s in (-1, 1):
        ellipse(ctx, s * 520, -170, 90, 66, s * 0.5)
        fill_stroke(ctx, SKIN, OUTL, 5)
    ctx.restore()
    # rear-view mirror
    ctx.move_to(960, 220)
    ctx.line_to(960, 300)
    setc(ctx, hexc('#25262f'))
    ctx.set_line_width(30)
    ctx.stroke()
    rrect(ctx, 470, 290, 980, 340, 70)
    fill_stroke(ctx, hexc('#25262f'), OUTL, 6)
    ctx.save()
    rrect(ctx, 500, 318, 920, 284, 50)
    ctx.clip()
    mc = TCam((x, 1.3, z - 0.6), h + math.pi, 0.03, 820, cx=960, cy=470, mirror=True)
    draw_scene(ctx, mc, w, t, ego=False)
    g = cairo.LinearGradient(500, 318, 1420, 602)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.14)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    if AGG.flash(t):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ADD)
        glow(ctx, 960, 460, 420, (1.0, 0.97, 0.85), 0.25)
        ctx.restore()
    grade(ctx, t, CANVAS, CANVAS, 0.8)
    if kw.get('blink') and HERO.blink(t) == 'R':
        glow(ctx, 1140, 1600, 70, hexc('#2bff6a'), 0.6)
        poly(ctx, [(1170, 1600), (1130, 1572), (1130, 1588), (1100, 1588), (1100, 1612), (1130, 1612), (1130, 1628)])
        setc(ctx, hexc('#2bff6a'))
        ctx.fill()


def dash_face(ctx, w, t, lt, kw):
    """Dashboard camera looking back at the hero; the tailgater fills the rear window with high beams."""
    x, z, h = HERO.pose(t)
    setc(ctx, hexc('#1e1f27'))
    ctx.paint()
    RW = (330, 360, 1260, 560)
    ctx.save()
    rrect(ctx, *RW, 120)
    ctx.clip()
    view = TCam((x, 1.3, z - 1.4), h + math.pi, 0.02, 760, cx=960, cy=700)
    draw_scene(ctx, view, w, t, ego=False)
    warm_haze(ctx, view, CANVAS)
    if AGG.flash(t):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ADD)
        glow(ctx, 960, 700, 500, (1.0, 0.97, 0.85), 0.3)
        ctx.restore()
    ctx.restore()
    rrect(ctx, *RW, 120)
    setc(ctx, OUTL)
    ctx.set_line_width(10)
    ctx.stroke()
    # headrests of the back seat + the driver's seat
    for cx in (560, 1360):
        rrect(ctx, cx - 140, 830, 280, 170, 60)
        fill_stroke(ctx, hexc('#3d3d50'), OUTL, 5)
    rrect(ctx, 520, 960, 880, 1100, 200)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 6)
    rrect(ctx, 700, 860, 520, 240, 90)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 6)
    e = kw['expr'](lt) if callable(kw.get('expr')) else kw.get('expr', 'worried')
    head2d(ctx, 960, 1180, 260, 'hero', e, kw.get('turn', 0.0), t)
    poly(ctx, [(1250, 1420), (1330, 1450), (760, 1930), (660, 1930)])
    fill_stroke(ctx, hexc('#2a2a33'), OUTL, 5)
    if AGG.flash(t):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ADD)
        glow(ctx, 960, 880, 500, (1.0, 0.97, 0.85), 0.15)
        ctx.restore()
    grade(ctx, t, CANVAS, CANVAS, 0.7, grain=0.04)


engine.SCENES.update(cine=cine, interior_mirror=interior_mirror, dash_face=dash_face)


# ------------------------------------------------------------------ shots
def build(defs):
    shots, prev = [], 0.0
    for end, kind, kw in defs:
        kw = dict(kw)
        kw['dur_'] = end - prev
        s = Shot(end - prev, kind, **kw)
        s.start = prev
        shots.append(s)
        prev = end
    return shots


DUR = 37.0
z_stopA = AGG.z(30)
defs = [
    (3.0, 'cine', dict(cam='track', target=AGG, off=(-3.4, 0.9, 9.0), look=(0, 0.9, -3.0), f=760, dt=14.4, shake=0.12, streak=0.8)),
    (6.0, 'cine', dict(cam='heli', target=AGG, R=34.0, H=17.0, a0=-2.5, w=0.18, f=1050, oz=6.0)),
    (8.6, 'cine', dict(cam='track', target=AGG, off=(-1.9, 0.6, 7.0), look=(0, 0.9, -2.0), f=720, shake=0.1, streak=0.9)),
    (11.0, 'dash_face', dict(expr=lambda lt: 'annoyed' if lt < 0.6 else 'worried')),
    (13.5, 'interior_mirror', dict(blink=True)),
    (16.4, 'cine', dict(cam='tele', target=HERO, off=(3.0, 7.0, -110.0), tz=6.0, f=2200)),
    (19.6, 'cine', dict(cam='track', target=SEMI, off=(6.6, 1.3, 17.0), look=(-3.0, 1.4, 2.0), f=820, shake=0.05, jolt=(18.0, 0.5))),
    (22.6, 'cine', dict(cam='heli', target=AGG, R=19.0, H=8.0, a0=0.75, w=0.08, f=950, oz=5.0)),
    (26.0, 'cine', dict(cam='crane', target=POL, ox=-5.0, oz0=-14.0, oz1=-6.0, y0=1.2, y1=9.0, tx=0.0, tz=13.0, f=900)),
    (29.6, 'cine', dict(cam='fixed', pos=(18.0, 1.3, z_stopA + 9.0), target_pt=(12.5, 0.9, z_stopA - 9.0), f=760, dt=2.2)),
    (33.2, 'cine', dict(cam='heli', target=HERO, R=120.0, H=60.0, a0=-2.2, w=0.10, f=1100, oz=40.0)),
    (DUR, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-30.0, oz1=-40.0, y0=2.0, y1=26.0, tx=0.0, tz=200.0, f=1000)),
]
shots = build(defs)


class CineVideo(SquareVideo):
    def frame(self, ctx, t):
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        n = len(self.caption)
        y0 = SQ_Y - 40 - (n - 1) * 70
        for i, line in enumerate(self.caption):
            text_center(ctx, line, W / 2, y0 + i * 70, 56)
        s = self.shot_at(t)
        ctx.save()
        ctx.rectangle(0, SQ_Y, W, SQ_PX)
        ctx.clip()
        ctx.translate(0, SQ_Y)
        k = SQ_PX / SQ
        ctx.scale(k, k)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        lt = t - s.start
        engine.SCENES[s.kind](ctx, self.world, wt(t), lt if s.kind != 'cine' or s.kw.get('cam') != 'heli' else lt, s.kw)
        whip(ctx, lt, s.dur, CANVAS, CANVAS, 0.12)
        for t0, t1, fn in self.overlays:
            if t0 <= t < t1:
                fn(ctx, t - t0, t1 - t0)
        ctx.restore()


video = CineVideo(['Aggressive driver behind you?', "Here's what to do"], world, shots)
video.dur = DUR
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]


def counter(ctx, lt, d):
    a = smooth(lt / 0.3)
    rrect(ctx, 460, 140, 1000, 220, 50)
    setc(ctx, (0, 0, 0), 0.65 * a)
    ctx.fill()
    text_center(ctx, 'Time saved:', 960, 225, 66, (1, 1, 1), a=a)
    text_center(ctx, '0 seconds', 960, 320, 86, hexc('#ff4b4b'), a=a)


def slowmo_tag(ctx, lt, d):
    a = smooth(lt / 0.2) * smooth((d - lt) / 0.2)
    rrect(ctx, 1500, 70, 360, 90, 45)
    setc(ctx, (0, 0, 0), 0.55 * a)
    ctx.fill()
    ellipse(ctx, 1550, 115, 16, 16)
    setc(ctx, hexc('#ff4b4b'), a if (lt * 2) % 1 < 0.6 else 0.2 * a)
    ctx.fill()
    text_center(ctx, 'SLOW-MO', 1700, 133, 46, (1, 1, 1), a=a)


video.overlays = [
    (0.0, 3.0, big_text('100 mph in rush hour?!', 300, 120, hexc('#ffd23f'), 0.2, True)),
    (3.0, 6.0, location_tag('I-85, Atlanta, Georgia')),
    (3.2, 6.0, sq_caption('Rush hour. Everyone at 65 mph.')),
    (S[2] + 0.2, E[2], sq_caption('...except him. Weaving at 100 mph.')),
    (S[3] + 0.2, E[3], sq_caption('Now he is on YOUR bumper. Flashing. Honking.', 70)),
    (S[4], E[4], step_badge(1)),
    (S[4] + 0.15, E[4], sq_caption("Stay calm. Don't brake-check. Don't react.", 72)),
    (S[5], E[5], step_badge(2)),
    (S[5] + 0.15, E[5], sq_caption('Signal, move over, let him pass')),
    (S[6], E[6], step_badge(3)),
    (S[6] + 0.15, E[6], sq_caption('He cuts off a truck. You: keep your distance.', 70)),
    (S[7], E[7], slowmo_tag),
    (S[7] + 0.2, E[7], sq_caption('...and nearly rear-ends slowing traffic', 76)),
    (S[8] + 0.2, E[8], sq_caption('Police saw everything')),
    (S[9], E[9], counter),
    (S[9] + 0.3, E[9], sq_caption('You drive past him. Calm. On time.')),
    (S[10], E[10], badge('AGGRESSIVE DRIVING', '#e0393e')),
    (S[10] + 0.2, E[10], sq_caption('Tailgating, weaving, cutting off = crashes + tickets', 64)),
    (S[11] + 0.2, E[11], end_card("Don't engage. Move over. Let them go.", 'Ever been tailgated like this? Comment!')),
]


# ------------------------------------------------------------------ sound
def v8(d, rev_fn):
    n = int(d * SR)
    tt = np.arange(n) / SR
    grid = np.arange(0, d + 1, 0.02)
    rv = np.interp(tt, grid, [rev_fn(g) for g in grid])
    f = 28 + rv * 34
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(np.sin(k * ph + 0.4 * k) / k ** 0.7 for k in range(1, 12))
    rasp = bp(noise(n), 400, 2500) * (0.5 + 0.5 * np.sin(ph * 0.5)) ** 6
    return lp(np.tanh(s * 1.6), 2200) * 0.45 + rasp * 0.3


def braam(d=2.0, f0=55):
    n = int(d * SR)
    tt = np.arange(n) / SR
    s = sum(np.sign(np.sin(2 * np.pi * f * tt)) * 0.3 + np.sin(2 * np.pi * f * tt) for f in (f0, f0 * 1.5, f0 * 2.0))
    s = lp(s, 500 + 1500 * np.exp(-tt / 0.4))
    return s * env_adsr(n, 0.02, 0.8) * 0.4


def air_horn(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    s = sum(sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, 8)) for f in (220, 277, 330))
    return bp(np.tanh(s * 0.5), 150, 3000) * env_adsr(n, 0.04, 0.1) * 0.45


def abs_chatter(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return bp(noise(n), 300, 1800) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * tt))) * 0.6


def slow(sig, k):
    """Pitch-down / stretch a signal by 1/k (for slow motion)."""
    n = int(len(sig) / k)
    return np.interp(np.arange(n) * k, np.arange(len(sig)), sig)


def wind(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return lp(noise(n), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.2 * tt) ** 2)


def sound():
    m = Mixer(DUR)
    m.add(wind(DUR), 0, 0.22)
    m.add(lp(noise(int(DUR * SR)), 220), 0, 0.35)                  # highway roar
    # hook: A cutting off the truck (world 14..17)
    m.add(braam(2.2, 49), 0.05, 0.9)
    m.add(v8(3.0, lambda u: 0.8 + 0.2 * math.sin(u * 3)), 0, 0.5)
    m.add(car_pass(1.2, 0.5, 120), 1.4, 0.7, np.linspace(-0.6, 0.6, int(1.2 * SR)))
    # A's engine through the video (louder in his shots)
    m.add(v8(T_TAIL0 - 3.0, lambda u: 0.85 + 0.15 * math.sin(u * 2.3)), 3.0, 0.5)
    for k, tt in enumerate((4.2, 6.6, 7.4)):
        m.add(car_pass(1.2, 0.5, 110), tt, 0.6, np.linspace(-0.7 + 1.4 * (k % 2), 0.7 - 1.4 * (k % 2), int(1.2 * SR)))
    # tailgating: horn + engine revs
    for tt in (S[3] + 0.4, S[3] + 1.2, S[3] + 1.5, S[4] + 0.6, S[4] + 1.7):
        m.add(horn(0.45), tt, 0.7, 0.0)
    m.add(heartbeat(4, 125), S[3] + 0.2, 0.6)
    m.add(click(), T_SIG, 0.7)
    indicator(m, T_SIG, T_LC1 + 0.3, 0.45, 0.2)
    m.add(v8(2.0, lambda u: 0.6 + 0.4 * min(1, u / 0.8)), 13.4, 0.8)
    m.add(car_pass(1.6, 0.5, 120), 14.4, 1.0, np.linspace(-0.8, 0.8, int(1.6 * SR)))
    # cut-off
    m.add(air_horn(1.8), 17.5, 1.0)
    m.add(brake_squeal(1.6), 17.6, 0.7)
    m.add(v8(2.0, lambda u: 1.0), T_CUT0, 0.5)
    # slow-motion near miss (video time; sounds stretched)
    v_slam = vt_of(T_SLAM)
    m.add(braam(2.5, 41), SM0, 0.6)
    m.add(slow(screech(1.6, 1050), SMK), v_slam, 0.9)
    m.add(slow(abs_chatter(1.6), SMK), v_slam, 0.5)
    m.add(slow(heartbeat(3, 120), SMK), SM0 + 0.1, 0.8)
    # police
    m.add(siren_whoop(2), vt_of(20.8), 0.6) if 'siren_whoop' in globals() else None
    m.add(chime(), S[9] + 0.4, 0.4)
    m.add(sad_trombone(), S[9] + 0.6, 0.55)
    m.add(car_pass(1.4, 0.5, 95), S[9] + 1.6, 0.6, np.linspace(-0.6, 0.6, int(1.4 * SR)))
    for i in (4, 5, 6):
        m.add(pop(), S[i] + 0.15, 0.6)
    m.add(whoosh(0.5, 0.4), S[10] - 0.1, 0.5)
    m.add(success_jingle(), S[11] + 0.3, 0.8)
    return m.out(DUR)


# ------------------------------------------------------------------ checks
def verify():
    worst = {}
    agents = [('HERO', HERO), ('AGG', AGG), ('SEMI', SEMI), ('POL', POL)] + [(f'C{i}', c) for i, c in enumerate(TRAF)]
    for t in np.arange(0.0, 32.0, 0.02):
        P = [(n, a.pose(t), a.ext) for n, a in agents]
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                (ni, (x1, z1, h1), e1), (nj, (x2, z2, h2), e2) = P[i], P[j]
                hw1 = e1[2] + abs(math.sin(h1)) * 2.0
                hw2 = e2[2] + abs(math.sin(h2)) * 2.0
                if abs(x1 - x2) >= hw1 + hw2 + 0.15:
                    continue
                if z1 > z2:
                    g = (z1 + e1[0]) - (z2 + e2[1])
                else:
                    g = (z2 + e2[0]) - (z1 + e1[1])
                key = (ni, nj)
                if key not in worst or g < worst[key][0]:
                    worst[key] = (round(g, 2), round(t, 2), round(abs(x1 - x2), 2))
    for k, v in sorted(worst.items(), key=lambda kv: kv[1][0])[:14]:
        print(k, v)
    print('A max speed mph', round(max(A_S(t) for t in np.arange(0, 30, 0.1)) * 2.237), '| A stops on shoulder at z', round(AGG.z(30), 1),
          '| police stop z', round(POL.z(30), 1), 'gap', round(AGG.z(30) - 2.25 - POL.z(30) - 2.25, 1))


if __name__ == '__main__':
    import sys
    square_mode()
    cinekit.enable_lighting()
    from street import siren_whoop
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'check':
        check_sheet(video, sys.argv[1])
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        out = sys.argv[1] if len(sys.argv) > 1 else 'aggressive.mp4'
        video.render(out, sound(), out + '_work')
