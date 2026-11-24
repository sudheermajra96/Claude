"""Reusable template + camera library for the cinematic SQUARE (1:1) highway episodes (extracted from ep_aggressive.py).

A new episode only needs: the traffic plan (Veh / Rev agents), a Highway(...) world dressed for its city, a shot list
of camera presets, captions/overlays and a sound() mix.  Everything else lives here:

  EP              episode config: EP.hero (car for driver views), EP.glare(t) (high-beam glow), EP.shadows (agents),
                  EP.tm (TimeMap = slow motion), EP.extra_ground(ctx, view, t)
  TimeMap         slow-motion window(s): wt(video t) -> world t, vt(world t) -> video t
  Veh, Rev        car / semi (round tyres, occupants in the glass, high-beam flash, police lights, hazards 'B'),
                  opposite-carriageway car
  Trooper         standing police officer on the shoulder (2D billboard, writes a ticket / flinches / thumbs up)
  Highway         4-lane divided highway world: lanes, median barrier, light poles, overhead sign gantries,
                  tree or cactus rows, distant hills, mountains or a city skyline (all parameters)
  cameras         'cine' scene with cam = heli | track | tele | fixed | crane | top (+ jolt), 'interior_mirror'
                  (driver view + rear-view mirror), 'dash_face' (dashboard camera looking at the driver)
  overlays        counter_card, slowmo_tag, speed_tag, gap_tag (+ everything from mkit / toronto: big_text,
                  location_tag, step_badge, badge, sq_caption, end_card, x_mark, check_mark)
  sound           v8, braam, air_horn, abs_chatter, slow, wind, highway_bed
  checks          verify_gaps(agents), run(video, sound, verify)
World axes: +Z = travel, lanes x = 1.75 / 5.25 / 8.75 / 12.25 (lane 0 = left/fast), right shoulder 14.0 .. 17.5,
median barrier at x = -0.6, opposite carriageway x -2 .. -16.
"""
import math
import random
import sys
import types

import cairo
import numpy as np

from mkit import *
from truckkit import draw_car_round, tractor_det, trailer_det
from peoplekit import *
import citykit
import engine
import street
from sqkit import *
import cinekit
from cinekit import shadow, shake, heli, look, sun_flare, warm_haze, speed_streaks, grade, whip

V = 29.0
LANES = [1.75, 5.25, 8.75, 12.25]
SHOULDER = 15.6
CANVAS = 1920
FMUL = 1.4
COLS = ['#3a7bd5', '#f2a541', '#c9c9d6', '#37b26c', '#f4f4f6', '#7a4fd0', '#2f6f73', '#d8c3a0', '#e05d5d', '#1c1c22']


# ------------------------------------------------------------------ time map (slow motion)
class TimeMap:
    """segs: [(video t0, video t1, speed k)] in increasing order."""

    def __init__(self, segs=()):
        self.segs = list(segs)

    def wt(self, vt):
        w, prev = vt, 0.0
        lag = 0.0
        for a, b, k in self.segs:
            if vt < a:
                break
            if vt < b:
                return vt - lag - (vt - a) * (1 - k)
            lag += (b - a) * (1 - k)
        return vt - lag

    def vt(self, w):
        lo, hi = w - 1, w + 60
        for _ in range(60):
            m = (lo + hi) / 2
            if self.wt(m) < w:
                lo = m
            else:
                hi = m
        return (lo + hi) / 2


EP = types.SimpleNamespace(hero=None, glare=lambda t: False, shadows=[], tm=TimeMap(), extra_ground=None, unit='mph')


# ------------------------------------------------------------------ vehicles
class Veh(Track):
    def __init__(self, x, speed, ta, za, col, kind='car', occ=None, flash=None, police=None, brake=None, blink=None,
                 trailer=('#f4f4f6', '#e0393e', 'PEACH STATE'), cab='#2f6f9f', t0=-3, t1=80):
        super().__init__(x, speed, ta, za, col, brake=brake, blink=blink, t0=t0, t1=t1)
        self.kind, self.occ, self.flash, self.police, self.trailer, self.cab = kind, occ, flash, police, trailer, cab
        self.ext = (-15.5, 5.6, 1.3, 4.0) if kind == 'semi' else (-2.25, 2.25, 0.95, 1.45)

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        if not view.ortho:
            d = view.depth((x, 1, z))
            if d < -25 or d > 650:
                return []
        if self.kind == 'semi':
            br = self.brake(t) > 0.5
            tc, ts, tl = self.trailer
            return [((x + math.sin(h) * 2.5, 1.5, z + math.cos(h) * 2.5), lambda: tractor_det(ctx, view, x, z, h, self.cab, False, None, br)),
                    ((x - math.sin(h) * 7.2, 2.0, z - math.cos(h) * 7.2),
                     lambda: trailer_det(ctx, view, x, z, h, False, False, br, tc, ts, tl))]

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
                            glow(ctx, p[0], p[1], min(0.8 * s + 26, 120), col, 0.85)
        return [((x, 0.8, z), fn)]


class Rev:
    """Opposite carriageway car (travels -z)."""

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


def occ_of(who, expr_fn, seat=-0.38, look_fn=None):
    """Occupant callback for Veh(occ=...): expr_fn(t) -> expression."""
    def mk(t):
        def fn(ctx, view, Lf, h):
            person3d(ctx, view, Lf, seat, 0.05, who, look_fn(t) if look_fn else 0.0, expr_fn(t))
        return fn
    return mk


class Trooper:
    """Standing officer (2D billboard). pose_fn(t) -> ('write' | 'thumbs', local t); lean_fn(t) -> radians."""

    def __init__(self, x, z, pose_fn=None, lean_fn=None, expr_fn=None):
        self.x, self.zz = x, z
        self.pose_fn = pose_fn or (lambda t: ('write', t % 3))
        self.lean_fn = lean_fn or (lambda t: 0.0)
        self.expr_fn = expr_fn or (lambda t: 'flat')
        self.col = '#1f3a6b'
        self.ext = (-0.3, 0.3, 0.3, 1.9)

    def pose(self, t):
        return self.x, self.zz, 0.0

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        x, z = self.x, self.zz
        if view.ortho:
            def top():
                p = view.pt((x, 0, z))
                ellipse(ctx, p[0], p[1], 0.35 * view.s, 0.35 * view.s)
                fill_stroke(ctx, hexc('#1f3a6b'), (1, 1, 1), 3)
            return [((x, 1.0, z), top)]

        def draw():
            p, s = view.pt((x, 1.4, z)), view.scale((x, 1.4, z))
            g = view.pt((x, 0.0, z))
            if not (p and s and g and s > 2):
                return
            k = 0.115 * s / 100
            ctx.save()
            ctx.translate(g[0], g[1])
            ctx.rotate(self.lean_fn(t))
            ctx.translate(-g[0], -g[1])
            top_ = p[1] + 300 * k
            for dx in (-0.16, 0.16):
                lx = p[0] + dx * s
                ctx.rectangle(lx - 0.1 * s, top_, 0.2 * s, g[1] - top_ - 0.05 * s)
                fill_stroke(ctx, hexc('#16294d'), OUTL, max(1, s / 60))
                ellipse(ctx, lx + 0.04 * s, g[1] - 0.04 * s, 0.16 * s, 0.07 * s)
                fill_stroke(ctx, hexc('#111118'), OUTL, max(1, s / 60))
            pose, lt = self.pose_fn(t)
            street.officer(ctx, p[0], p[1], k, t, pose, lt, self.expr_fn(t))
            ctx.restore()
        return [((x, 1.0, z), draw)]


# ------------------------------------------------------------------ skid marks + smoke (generic: wheels_fn(t) -> 2 points)
class Smoke:
    col = '#ccc'

    def __init__(self, wheels_fn, t0, t1):
        self.wf, self.t0, self.t1 = wheels_fn, t0, t1

    def visible(self, t):
        return True

    def pose(self, t):
        return 0, 0, 0

    def items(self, ctx, view, t):
        if view.ortho or t < self.t0:
            return []
        out = []
        for s in np.arange(self.t0, min(t, self.t1), 0.06):
            age = t - s
            if age > 2.5:
                continue
            for k, P in enumerate(self.wf(s)):
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

    def marks(self, ctx, view, t):
        if view.ortho or t < self.t0:
            return
        ts = np.arange(self.t0, min(t, self.t1), 0.04)
        if len(ts) < 2:
            return
        for k in range(2):
            pts = [view.pt((self.wf(s)[k][0], 0.012, self.wf(s)[k][2])) for s in ts]
            pts = [p for p in pts if p]
            if len(pts) > 1:
                ctx.move_to(*pts[0])
                for p in pts[1:]:
                    ctx.line_to(*p)
                setc(ctx, (0.1, 0.1, 0.12), 0.7)
                sc = view.scale(self.wf(ts[-1])[k]) or 10
                ctx.set_line_width(max(2, 0.22 * sc))
                ctx.stroke()


def rear_wheels_of(a):
    def f(t):
        x, z, h = a.pose(t)
        Lf = L(x, z, h)
        return Lf(-0.8, 0.2, -1.38), Lf(0.8, 0.2, -1.38)
    return f


# ------------------------------------------------------------------ scenery
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


def gantry(ctx, view, z, signs):
    """signs: [(x0, x1, line1, line2)] green panels."""
    for px in (-1.2, 17.8):
        a, b = view.pt((px, 0, z)), view.pt((px, 7.4, z))
        if a and b:
            ctx.move_to(*a)
            ctx.line_to(*b)
            setc(ctx, hexc('#7a7f8c'))
            ctx.set_line_width(max(2, 0.3 * (view.scale((px, 3, z)) or 5)))
            ctx.stroke()
    fill_poly(ctx, view, [(-1.2, 7.0, z), (17.8, 7.0, z), (17.8, 7.5, z), (-1.2, 7.5, z)], hexc('#7a7f8c'))
    for x0, x1, t1, t2 in signs:
        if fill_poly(ctx, view, [(x0, 4.6, z), (x1, 4.6, z), (x1, 7.0, z), (x0, 7.0, z)], hexc('#1f6f43'), (1, 1, 1), 2):
            c, s = view.pt(((x0 + x1) / 2, 5.8, z)), view.scale(((x0 + x1) / 2, 5.8, z))
            if c and s and s > 4:
                text_center(ctx, t1, c[0], c[1] - 0.15 * s, 0.75 * s, (1, 1, 1))
                text_center(ctx, t2, c[0], c[1] + 0.75 * s, 0.6 * s, (1, 1, 1))


def mountains(ctx, view, Z=3200.0, col='#6f7f9a', snow='#f2efe9', haze='#ffc89a', seed=5, peaks=9, hmax=520.0, x0=-2600, x1=2600):
    """Jagged mountain range far ahead with snow caps (Rockies, Cascades...)."""
    if view.ortho:
        return
    rnd = random.Random(seed)
    xs = np.linspace(x0, x1, peaks * 2 + 1)
    hs = [rnd.uniform(0.35, 1.0) * hmax if i % 2 else rnd.uniform(0.1, 0.35) * hmax for i in range(len(xs))]
    for layer, (dz, fade) in enumerate(((600, 0.55), (0, 0.3))):
        pts = [view.pt((float(x), h * (0.8 if layer == 0 else 1.0), Z + dz)) for x, h in zip(xs, hs[::(1 if layer else -1)])]
        base = [view.pt((float(x1), 0, Z + dz)), view.pt((float(x0), 0, Z + dz))]
        if not all(pts) or not all(base):
            continue
        poly(ctx, pts + base)
        setc(ctx, mix(hexc(col), hexc(haze), fade))
        ctx.fill()
        if layer == 1:
            for i in range(1, len(pts) - 1, 2):
                a, p, b = pts[i - 1], pts[i], pts[i + 1]
                u = 0.28
                poly(ctx, [p, (p[0] + (b[0] - p[0]) * u, p[1] + (b[1] - p[1]) * u),
                           (p[0] + (b[0] - p[0]) * u * 0.5, p[1] + (b[1] - p[1]) * u * 0.8),
                           (p[0] + (a[0] - p[0]) * u * 0.6, p[1] + (a[1] - p[1]) * u * 1.1),
                           (p[0] + (a[0] - p[0]) * u, p[1] + (a[1] - p[1]) * u)])
                setc(ctx, mix(hexc(snow), hexc(haze), 0.2))
                ctx.fill()


def city_skyline(ctx, view, Z=2600.0, xc=0.0, n=22, seed=17, base='#7d6f86', haze='#ffc89a', hmin=60, hmax=190):
    if view.ortho:
        return
    rnd = random.Random(seed)
    for k in range(n):
        X = xc - n * 19 + k * 38 + rnd.uniform(-10, 10)
        hgt = rnd.uniform(hmin, hmax) * (1.3 if abs(X - xc) < 120 else 0.8)
        w = rnd.uniform(24, 40)
        b, tp, s = view.pt((X, 0, Z + rnd.uniform(-60, 60))), view.pt((X, hgt, Z)), view.scale((X, 0, Z))
        if b and tp and s:
            ctx.rectangle(b[0] - w * s / 2, tp[1], w * s, b[1] - tp[1])
            setc(ctx, mix(hexc(base), hexc(haze), 0.35 + 0.25 * rnd.random()))
            ctx.fill()


def cactus(ctx, view, x, z, s=1.0):
    """Saguaro (desert roadside)."""
    b, tp, sc = view.pt((x, 0, z)), view.pt((x, 4.2 * s, z)), view.scale((x, 0, z))
    if not b or not tp or not sc:
        return
    w = 0.55 * s * sc
    lw = max(1, min(4, sc / 30))
    col = hexc('#5f8f4e')
    rrect(ctx, b[0] - w / 2, tp[1], w, b[1] - tp[1], w / 2)
    fill_stroke(ctx, col, OUTL, lw)
    for sx, y0, y1 in ((-1, 1.6, 3.0), (1, 2.2, 3.5)):
        ya, yb = view.pt((x, y0 * s, z)), view.pt((x, y1 * s, z))
        if ya and yb:
            ax = b[0] + sx * 0.8 * s * sc
            rrect(ctx, min(b[0], ax) - w * 0.2, ya[1] - w * 0.2, abs(ax - b[0]) + w * 0.4, w * 0.45, w * 0.2)
            fill_stroke(ctx, col, OUTL, lw)
            rrect(ctx, ax - w * 0.22, yb[1], w * 0.45, ya[1] - yb[1] + w * 0.2, w * 0.22)
            fill_stroke(ctx, col, OUTL, lw)


def rock(ctx, view, x, z, s=1.0):
    p, sc = view.pt((x, 0.4 * s, z)), view.scale((x, 0, z))
    if p and sc:
        ellipse(ctx, p[0], p[1], 1.2 * s * sc, 0.6 * s * sc)
        fill_stroke(ctx, hexc('#b98a63'), OUTL, max(1, min(3, sc / 30)))


def conifer(ctx, view, x, z, s=1.0):
    b, sc = view.pt((x, 0, z)), view.scale((x, 0, z))
    if not b or not sc:
        return
    lw = max(1, min(4, sc / 30))
    for i, (y, w) in enumerate(((1.0, 2.0), (2.6, 1.6), (4.0, 1.1))):
        pa, pb = view.pt((x, y * s, z)), view.pt((x, (y + 2.6) * s, z))
        if pa and pb:
            poly(ctx, [(pa[0] - w * s * sc, pa[1]), (pa[0] + w * s * sc, pa[1]), pb])
            fill_stroke(ctx, hexc(['#2f6b45', '#3a7d50', '#2a5f3f'][i]), OUTL, lw)


class Highway:
    """4-lane divided highway. roadside: 'trees' | 'cactus' | 'pines'. far(ctx, view): distant backdrop."""

    def __init__(self, sky=('#3b6fb6', '#ffc791'), grass='#9aa85a', hills='#7d8a5a', far=None, gantries=(), roadside='trees',
                 asphalt='#4f525d', seed=3, poles=True):
        self.sky, self.ground_col, self.hills, self.far = sky, hexc(grass), hills, far
        self.gantries, self.roadside, self.asphalt, self.poles = list(gantries), roadside, asphalt, poles
        r = random.Random(seed)
        self.trees = [(r.uniform(24, 70), z + r.uniform(-4, 4), r.uniform(1.0, 1.5)) for z in np.arange(-400, 3000, 10)]
        self.trees += [(-r.uniform(22, 60), z + r.uniform(-4, 4), r.uniform(1.0, 1.5)) for z in np.arange(-400, 3000, 12)]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        if self.far:
            self.far(ctx, view)
        if self.hills:
            far_line(ctx, view, 2400, lambda x: 22 + 9 * math.sin(x / 220), col=self.hills)

    def ground(self, ctx, view, t):
        ez = view.pos[2] if not view.ortho else view.zc
        zlo, zhi = ez - 300, ez + 2400
        gquad(ctx, view, -17.0, 18.5, zlo, zhi, hexc('#8d8f96'))
        gquad(ctx, view, -0.2, 14.0, zlo, zhi, hexc(self.asphalt))
        gquad(ctx, view, -16.0, -2.0, zlo, zhi, hexc(self.asphalt))
        for xl in (3.5, 7.0, 10.5, -5.5, -9.0, -12.5):
            for k in range(int(zlo // 12), int(min(zhi, ez + 900) // 12) + 1):
                gquad(ctx, view, xl - 0.08, xl + 0.08, k * 12, k * 12 + 4, (0.93, 0.93, 0.9), 0.01)
        gquad(ctx, view, 0.0, 0.15, zlo, zhi, C_YEL, 0.01)
        gquad(ctx, view, 13.85, 14.0, zlo, zhi, (0.93, 0.93, 0.9), 0.01)
        if not view.ortho:
            for xl in LANES:
                for d in (-0.8, 0.8):
                    gquad(ctx, view, xl + d - 0.3, xl + d + 0.3, zlo, min(zhi, ez + 600), mix(hexc(self.asphalt), (0, 0, 0), 0.08), 0.004)
            fill_poly(ctx, view, [(-0.6, 0, zlo), (-0.6, 0, zhi), (-0.45, 0.85, zhi), (-0.45, 0.85, zlo)], hexc('#c9c4ba'), OUTL, 1)
            fill_poly(ctx, view, [(-0.45, 0.85, zlo), (-0.45, 0.85, zhi), (-0.75, 0.85, zhi), (-0.75, 0.85, zlo)], hexc('#e2ddd2'))
            fill_poly(ctx, view, [(-0.9, 0, zlo), (-0.9, 0, zhi), (-0.75, 0.85, zhi), (-0.75, 0.85, zlo)], hexc('#b3ada2'), OUTL, 1)
        if EP.extra_ground:
            EP.extra_ground(ctx, view, t)
        for a in EP.shadows:
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
                if self.roadside == 'cactus' and not view.ortho:
                    fn = (lambda x=x, z=z, s=s: cactus(ctx, view, x, z, s)) if int(abs(z)) % 3 else (lambda x=x, z=z, s=s: rock(ctx, view, x, z, s))
                elif self.roadside == 'pines' and not view.ortho:
                    fn = lambda x=x, z=z, s=s: conifer(ctx, view, x, z, s)
                else:
                    fn = lambda x=x, z=z, s=s: tree3(ctx, view, x, z, s * (0.45 if view.ortho else 1.0), int(abs(z)) % 3)
                out.append(((x, 2, z), fn))
        if not view.ortho:
            if self.poles:
                for k in range(int((ez - 60) // 70), int((ez + 900) // 70) + 1):
                    z = k * 70.0
                    out.append(((-0.7, 6, z), lambda z=z: light_pole(ctx, view, -0.7, z)))
            for zg, signs in self.gantries:
                if ez - 40 < zg < ez + 1600:
                    out.append(((8.0, 6, zg), lambda zg=zg, signs=signs: gantry(ctx, view, zg, signs)))
        return out


def make_world(city, hero, others, dur=60.0):
    w = SegWorld(dur, [(0, 99, hero, others, [])], city, EP.unit)
    w.police_flash = lambda t: 0.0
    return w


# ------------------------------------------------------------------ camera library
def finish(ctx, view, t, lt, kw, streak=0.0):
    warm_haze(ctx, view, CANVAS)
    sun_flare(ctx, view, CANVAS, CANVAS, kw.get('flare', 1.0))
    speed_streaks(ctx, t, streak, CANVAS, CANVAS)
    grade(ctx, t, CANVAS, CANVAS)


def cine(ctx, w, t, lt, kw):
    """cam = heli | track | tele | fixed | crane | top.  dt shifts world time (flash-forward hooks)."""
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
    elif m == 'tele':                       # long lens from far ahead / behind (ox, oy absolute; oz relative)
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
    elif m == 'top':                        # straight-down drone (lesson / map view), travel = up the frame
        x, z = kw['center'](tf) if callable(kw['center']) else kw['center']
        H_ = kw.get('H', 90.0)
        view = look((x, H_, z - H_ * 0.25), (x, 0.0, z), kw.get('f', 1000), cy=960)
    view = TCam(view.pos, view.yaw, view.pitch, view.f * FMUL, view.cx, view.cy)
    if kw.get('jolt'):
        t0, amp = kw['jolt']
        u = tf - t0
        if 0 <= u < 1.2:
            k = amp * (1 - u / 1.2)
            view = TCam((view.pos[0] + k * math.sin(tf * 70), view.pos[1] + k * 0.6 * math.cos(tf * 61), view.pos[2]),
                        view.yaw + k * 0.01 * math.sin(tf * 53), view.pitch, view.f, view.cx, view.cy)
    draw_scene(ctx, view, w, tf)
    if m != 'top':
        finish(ctx, view, tf, lt, kw, streak)
    else:
        grade(ctx, tf, CANVAS, CANVAS, 0.6)
    if kw.get('hud'):
        sq_hud(ctx, w, tf)
    if kw.get('post'):
        kw['post'](ctx, view, tf, lt)


def cabin(ctx, steer):
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
    ctx.rotate(steer * 0.5)
    ellipse(ctx, 0, 0, 560, 430)
    ellipse(ctx, 0, 0, 490, 365)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#15151c'), OUTL, 5)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for s in (-1, 1):
        ellipse(ctx, s * 520, -170, 90, 66, s * 0.5)
        fill_stroke(ctx, SKIN, OUTL, 5)
    ctx.restore()


def interior_mirror(ctx, w, t, lt, kw):
    """Driver's view of EP.hero (or kw car): road ahead + rear-view mirror. kw: blink (indicator arrow), mirror (bool)."""
    H = kw.get('car', EP.hero)
    x, z, h = H.pose(t)
    view = TCam((x - 0.38, 1.18, z - 0.2), h, 0.04, kw.get('f', 900), cx=960, cy=1060)
    draw_scene(ctx, view, w, t, ego=False)
    warm_haze(ctx, view, CANVAS)
    sun_flare(ctx, view, CANVAS, CANVAS, 0.8)
    cabin(ctx, H.steer(t))
    if kw.get('mirror', True):
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
        if kw.get('mirror_glow') and kw['mirror_glow'](t):
            rrect(ctx, 500, 318, 920, 284, 50)
            setc(ctx, hexc('#ffd23f'))
            ctx.set_line_width(10)
            ctx.stroke()
        if EP.glare(t):
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_ADD)
            glow(ctx, 960, 460, 420, (1.0, 0.97, 0.85), 0.25)
            ctx.restore()
    grade(ctx, t, CANVAS, CANVAS, 0.8)
    b = H.blink(t)
    if kw.get('blink') and b in ('L', 'R'):
        s = 1 if b == 'R' else -1
        cx = 960 + s * 180
        glow(ctx, cx, 1600, 70, hexc('#2bff6a'), 0.6)
        poly(ctx, [(cx + s * 30, 1600), (cx - s * 10, 1572), (cx - s * 10, 1588), (cx - s * 40, 1588), (cx - s * 40, 1612),
                   (cx - s * 10, 1612), (cx - s * 10, 1628)])
        setc(ctx, hexc('#2bff6a'))
        ctx.fill()


def dash_face(ctx, w, t, lt, kw):
    """Dashboard camera looking back at the driver of EP.hero (or kw car). kw: who, expr (str or fn(lt)), turn."""
    H = kw.get('car', EP.hero)
    x, z, h = H.pose(t)
    setc(ctx, hexc('#1e1f27'))
    ctx.paint()
    RW = (330, 360, 1260, 560)
    ctx.save()
    rrect(ctx, *RW, 120)
    ctx.clip()
    view = TCam((x, 1.3, z - 1.4), h + math.pi, 0.02, 760, cx=960, cy=700)
    draw_scene(ctx, view, w, t, ego=False)
    warm_haze(ctx, view, CANVAS)
    if EP.glare(t):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ADD)
        glow(ctx, 960, 700, 500, (1.0, 0.97, 0.85), 0.3)
        ctx.restore()
    ctx.restore()
    rrect(ctx, *RW, 120)
    setc(ctx, OUTL)
    ctx.set_line_width(10)
    ctx.stroke()
    for cx in (560, 1360):
        rrect(ctx, cx - 140, 830, 280, 170, 60)
        fill_stroke(ctx, hexc('#3d3d50'), OUTL, 5)
    rrect(ctx, 520, 960, 880, 1100, 200)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 6)
    rrect(ctx, 700, 860, 520, 240, 90)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 6)
    e = kw['expr'](lt) if callable(kw.get('expr')) else kw.get('expr', 'worried')
    turn = kw['turn'](lt) if callable(kw.get('turn')) else kw.get('turn', 0.0)
    head2d(ctx, 960, 1180, 260, kw.get('who', 'hero'), e, turn, t)
    poly(ctx, [(1250, 1420), (1330, 1450), (760, 1930), (660, 1930)])
    fill_stroke(ctx, hexc('#2a2a33'), OUTL, 5)
    grade(ctx, t, CANVAS, CANVAS, 0.7, grain=0.04)


engine.SCENES.update(cine=cine, interior_mirror=interior_mirror, dash_face=dash_face)


# ------------------------------------------------------------------ shots + video
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
        engine.SCENES[s.kind](ctx, self.world, EP.tm.wt(t), lt, s.kw)
        whip(ctx, lt, s.dur, CANVAS, CANVAS, 0.12)
        for t0, t1, fn in self.overlays:
            if t0 <= t < t1:
                fn(ctx, t - t0, t1 - t0)
        ctx.restore()


def make_video(title, world, defs, dur):
    shots = build(defs)
    v = CineVideo(title, world, shots)
    v.dur = dur
    v.S = [s.start for s in shots]
    v.E = [s.start + s.dur for s in shots]
    return v


# ------------------------------------------------------------------ overlays
def counter_card(title, value, col='#ff4b4b'):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.3)
        rrect(ctx, 460, 140, 1000, 220, 50)
        setc(ctx, (0, 0, 0), 0.65 * a)
        ctx.fill()
        text_center(ctx, title, 960, 225, 66, (1, 1, 1), a=a)
        text_center(ctx, value, 960, 320, 86, hexc(col), a=a)
    return fn


def slowmo_tag(ctx, lt, d):
    a = smooth(lt / 0.2) * smooth((d - lt) / 0.2)
    rrect(ctx, 1500, 70, 360, 90, 45)
    setc(ctx, (0, 0, 0), 0.55 * a)
    ctx.fill()
    ellipse(ctx, 1550, 115, 16, 16)
    setc(ctx, hexc('#ff4b4b'), a if (lt * 2) % 1 < 0.6 else 0.2 * a)
    ctx.fill()
    text_center(ctx, 'SLOW-MO', 1700, 133, 46, (1, 1, 1), a=a)


def value_tag(fn, title, unit, good, bad, x=1640, y=1560, fmt='{:.1f}', higher_is_good=True):
    """Live meter box. fn(lt) -> value or None. Green when good, red when bad, yellow between."""
    def ov(ctx, lt, d):
        v = fn(lt)
        if v is None:
            return
        a = smooth(lt / 0.2)
        rrect(ctx, x - 240, y - 95, 480, 180, 40)
        setc(ctx, (0, 0, 0), 0.62 * a)
        ctx.fill()
        ok = v >= good if higher_is_good else v <= good
        ko = v < bad if higher_is_good else v > bad
        col = hexc('#22c35e') if ok else (hexc('#ff4b4b') if ko else hexc('#ffd23f'))
        text_center(ctx, title, x, y - 38, 40, (0.85, 0.85, 0.9), a=a)
        text_center(ctx, fmt.format(v) + ' ' + unit, x, y + 50, 80, col, a=a)
    return ov


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
    k = np.exp(-tt / 0.4)
    s = lp(s, 2000) * k + lp(s, 500) * (1 - k)
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


def whoosh_by(d=1.2, f=110):
    """Close fast pass-by (stereo sweep)."""
    return car_pass(d, 0.5, f)


def highway_bed(m, dur, wind_amp=0.22, roar=0.35):
    m.add(wind(dur), 0, wind_amp)
    m.add(lp(noise(int(dur * SR)), 220), 0, roar)


def pans(d, a=-0.7, b=0.7):
    return np.linspace(a, b, int(d * SR))


# ------------------------------------------------------------------ checks + entry point
def verify_gaps(agents, t0=0.0, t1=32.0, top=14):
    """agents: [(name, agent with .pose/.ext)]. Prints the closest pairs: (gap m, world t, lateral distance)."""
    worst = {}
    for t in np.arange(t0, t1, 0.02):
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
    for k, v in sorted(worst.items(), key=lambda kv: kv[1][0])[:top]:
        print(k, v)
    return worst


def lateral_gap(a, b, t0, t1):
    """Smallest side-to-side clearance between a and b while they overlap along z: (gap m, world t)."""
    best = (99.0, None)
    for t in np.arange(t0, t1, 0.01):
        (x1, z1, _), (x2, z2, _) = a.pose(t), b.pose(t)
        e1, e2 = a.ext, b.ext
        if z1 + e1[0] < z2 + e2[1] and z2 + e2[0] < z1 + e1[1]:
            g = abs(x1 - x2) - e1[2] - e2[2]
            if g < best[0]:
                best = (round(g, 2), round(t, 2))
    return best


def run(video, sound, verify, default_out='episode.mp4'):
    square_mode()
    cinekit.enable_lighting()
    a = sys.argv
    if len(a) > 2 and a[2] == 'verify':
        verify()
    elif len(a) > 2 and a[2] == 'check':
        check_sheet(video, a[1])
    elif len(a) > 2 and a[2] == 'still':
        for tt in a[3:]:
            video.render_still(float(tt), a[1].replace('.png', f'_{tt}.png'))
    else:
        out = a[1] if len(a) > 1 else default_out
        video.render(out, sound(), out + '_work')
