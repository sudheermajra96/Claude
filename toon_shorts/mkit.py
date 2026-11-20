"""Toolkit for the 'driver mistakes' series (zipper-video style: hook, round tyres, improved cars, multi-angle).

  Track        car on a straight road: x(t) key, speed key, anchored z; heading from motion
  OnPath       car following a Path with a lateral offset key (curves, turns)
  Shift        time-shifted copy of an agent (for the hook flash-forward)
  SegWorld     CityWorld with per-segment pedestrians
  Street       straight road builder (lanes, median, sidewalks, optional cross street, signals/signs)
  scenery      city rows, village houses + church, farms (fields, barns, silos), conifer forest, desert
  scenes       m_cam (chase/close/high/inside/fixed), m_top (north-up), m_htop (travel to the right),
               m_mirror (L/R outside mirror), plus c_shoulder / dash2 / face_day from earlier kits
"""
import math
import random

import cairo
import numpy as np

from citykit import *
from truckkit import draw_car_round, tractor_det, trailer_det
import citykit
import toronto

engine.DAY = True
citykit.draw_car_g = draw_car_round
COLS = ['#3a7bd5', '#f4f4f6', '#37b26c', '#f2a541', '#7a4fd0', '#c9c9d6', '#2f6f73', '#e05d5d', '#1c1c22', '#d8c3a0']


def blink_side(intervals, side):
    b = blinking(intervals, 0.8)
    return lambda t: side if b(t) > 0.5 else None


# ------------------------------------------------------------------ agents
class Track:
    def __init__(self, x, speed, t_anchor, z_anchor, col, blink=None, brake=None, t0=-40, t1=120):
        self.xk = x if callable(x) else const(x)
        self.sk = speed if callable(speed) else const(speed)
        self.col = col
        self.blink = blink or (lambda t: None)
        self.brake = brake or (lambda t: 1.0 if self.sk(t + 0.25) < self.sk(t) - 0.15 or (self.sk(t) < 0.05) else 0.0)
        self.g = np.arange(t0, t1, 1 / 120)
        v = np.array([max(0.0, self.sk(t)) for t in self.g])
        zz = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 / 120)])
        self.zv = zz - float(np.interp(t_anchor, self.g, zz)) + z_anchor

    def z(self, t):
        return float(np.interp(t, self.g, self.zv))

    def pose(self, t):
        x, z = self.xk(t), self.z(t)
        dx = self.xk(t + 0.15) - self.xk(t - 0.15)
        dz = self.z(t + 0.15) - self.z(t - 0.15)
        h = math.atan2(dx, dz) if abs(dz) > 0.02 else 0.0
        return x, z, h

    def speed(self, t):
        return max(0.0, self.sk(t))

    def steer(self, t):
        return clamp((self.pose(t + 0.3)[2] - self.pose(t - 0.3)[2]) * 3.0, -1.6, 1.6)

    def visible(self, t):
        return True


class OnPath(Mover):
    """Mover with a lateral offset (metres to the right of the path)."""

    def __init__(self, path, speed, t_anchor, s_anchor, col, offset=None, **kw):
        super().__init__(path, speed, t_anchor, s_anchor, col, t0=-40, t1=120, **kw)
        self.off = offset or const(0.0)
        if 'brake' not in kw:
            self.brake = lambda t: 1.0 if self.speed_k(t + 0.25) < self.speed_k(t) - 0.15 else 0.0

    def pose(self, t):
        s = self.s(t)
        x, z = self.path.pos(s)
        h = self.path.heading(s)
        o = self.off(t)
        x, z = x + math.cos(h) * o, z - math.sin(h) * o
        do = (self.off(t + 0.15) - self.off(t - 0.15)) / 0.3
        v = max(self.speed(t), 0.5)
        return x, z, h + math.atan2(do, v)


class Shift:
    def __init__(self, a, dt):
        self.a, self.dt = a, dt
        self.col = a.col

    def pose(self, t):
        return self.a.pose(t + self.dt)

    def speed(self, t):
        return self.a.speed(t + self.dt)

    def steer(self, t):
        return self.a.steer(t + self.dt)

    def blink(self, t):
        return self.a.blink(t + self.dt)

    def brake(self, t):
        return self.a.brake(t + self.dt)

    def visible(self, t):
        return True

    def __getattr__(self, k):
        if k == 'items' and hasattr(self.a, 'items'):
            return lambda ctx, view, t: self.a.items(ctx, view, t + self.dt)
        raise AttributeError(k)


class ShiftPed:
    def __init__(self, p, dt):
        self.p, self.dt = p, dt

    def x(self, t):
        return self.p.x(t + self.dt)

    def z(self, t):
        return self.p.z(t + self.dt)

    def draw(self, ctx, view, t):
        self.p.draw(ctx, view, t + self.dt)


class SegWorld(CityWorld):
    def __init__(self, dur, segs, city, units, peds=None):
        """segs: [(t0, t1, ego, others, peds)]"""
        super().__init__(dur, [s[:4] for s in segs], [], city, units)
        self.pseg = segs

    def peds_at(self, t):
        for s in self.pseg:
            if s[0] <= t < s[1]:
                return s[4]
        return self.pseg[-1][4]


def hook_seg(t0, t1, dt, ego, others, peds=()):
    """Flash-forward segment: shows the world at time t + dt."""
    return (t0, t1, Shift(ego, dt), [Shift(o, dt) for o in others], [ShiftPed(p, dt) for p in peds])


def min_gap(agents, t0, t1, step=0.05, lat=2.0):
    """Smallest bumper gap between any two cars that overlap laterally (approximate, axis aligned)."""
    worst = (99.0, None)
    for t in np.arange(t0, t1, step):
        P = [(a.pose(t), a) for a in agents]
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                (x1, z1, h1), a1 = P[i]
                (x2, z2, h2), a2 = P[j]
                if abs(x1 - x2) < lat:
                    g = abs(z1 - z2) - 4.4
                    if g < worst[0]:
                        worst = (g, (round(t, 2), getattr(a1, 'col', ''), getattr(a2, 'col', '')))
    return worst


# ------------------------------------------------------------------ scenery pieces
def gable_house(ctx, view, x0, x1, z0, z1, h, col, roof, ridge='z', frame='#ffffff'):
    building(ctx, view, x0, x1, z0, z1, h, col, win='#3b5872', roof=hexc(roof), floors=2.9, frame=frame)
    if view.ortho:
        return
    rh = 2.6
    if ridge == 'x':
        zm = (z0 + z1) / 2
        slopes = [[(x0, h, z0), (x1, h, z0), (x1, h + rh, zm), (x0, h + rh, zm)], [(x0, h, z1), (x1, h, z1), (x1, h + rh, zm), (x0, h + rh, zm)]]
        gables = [([(x0, h, z0), (x0, h, z1), (x0, h + rh, zm)], -math.pi / 2), ([(x1, h, z0), (x1, h, z1), (x1, h + rh, zm)], math.pi / 2)]
    else:
        xm = (x0 + x1) / 2
        slopes = [[(x0, h, z0), (x0, h, z1), (xm, h + rh, z1), (xm, h + rh, z0)], [(x1, h, z0), (x1, h, z1), (xm, h + rh, z1), (xm, h + rh, z0)]]
        gables = [([(x0, h, z0), (x1, h, z0), (xm, h + rh, z0)], math.pi), ([(x0, h, z1), (x1, h, z1), (xm, h + rh, z1)], 0.0)]
    for pts, fh in gables:
        c = (sum(p[0] for p in pts) / 3, sum(p[2] for p in pts) / 3)
        if front_facing(view, c[0], c[1], fh):
            fill_poly(ctx, view, pts, hexc(col), OUTL, 2)
    for pts in sorted(slopes, key=lambda q: -view.depth((sum(p[0] for p in q) / 4, h + 1, sum(p[2] for p in q) / 4))):
        fill_poly(ctx, view, pts, hexc(roof), OUTL, 2)


def church(ctx, view, x0, x1, z0, z1):
    gable_house(ctx, view, x0, x1, z0, z1, 7.0, '#f6f4ee', '#4a4f5c', 'x' if (x1 - x0) > (z1 - z0) else 'z')
    if view.ortho:
        return
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    tw = 1.6
    building(ctx, view, cx - tw, cx + tw, cz - tw, cz + tw, 14.0, '#f6f4ee', win='#2d3f55', floors=4.5)
    base = [(cx - tw, 14, cz - tw), (cx + tw, 14, cz - tw), (cx + tw, 14, cz + tw), (cx - tw, 14, cz + tw)]
    apex = (cx, 22.5, cz)
    faces = []
    for i in range(4):
        q = [base[i], base[(i + 1) % 4], apex]
        faces.append((view.depth(((q[0][0] + q[1][0]) / 2, 16, (q[0][2] + q[1][2]) / 2)), q))
    for _, q in sorted(faces, key=lambda f: -f[0]):
        fill_poly(ctx, view, q, hexc('#e9e6de'), OUTL, 2)


def barn(ctx, view, x0, x1, z0, z1):
    gable_house(ctx, view, x0, x1, z0, z1, 5.0, '#b3322b', '#4a4f5c', 'x' if (x1 - x0) > (z1 - z0) else 'z', frame='#ffffff')


def silo(ctx, view, x, z, h=13, r=2.2, col='#c9ccd6'):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], r * view.s, r * view.s)
        fill_stroke(ctx, hexc(col), OUTL, 2)
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, h, z)), view.scale((x, 0, z))
    if not b or not tp or not s:
        return
    w = r * s
    ctx.rectangle(b[0] - w, tp[1], 2 * w, b[1] - tp[1])
    fill_stroke(ctx, hexc(col), OUTL, max(1, s / 40))
    for k in range(1, 6):
        yy = b[1] - (b[1] - tp[1]) * k / 6
        ctx.move_to(b[0] - w, yy)
        ctx.line_to(b[0] + w, yy)
    setc(ctx, mix(hexc(col), (0, 0, 0), 0.25))
    ctx.set_line_width(max(1, s / 60))
    ctx.stroke()
    ctx.new_sub_path()
    ctx.arc(tp[0], tp[1], w, math.pi, 2 * math.pi)
    ctx.close_path()
    fill_stroke(ctx, hexc('#8a8f9c'), OUTL, max(1, s / 40))


def hay_bale(ctx, view, x, z):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 0.8 * view.s, 0.8 * view.s)
        fill_stroke(ctx, hexc('#e6c46a'), OUTL, 1.5)
        return
    b, s = view.pt((x, 0.75, z)), view.scale((x, 0.75, z))
    if b and s and s > 1:
        ellipse(ctx, b[0], b[1], 0.8 * s, 0.75 * s)
        fill_stroke(ctx, hexc('#e6c46a'), OUTL, max(1, s / 50))
        ellipse(ctx, b[0], b[1], 0.35 * s, 0.33 * s)
        setc(ctx, hexc('#c9a24a'))
        ctx.set_line_width(max(1, s / 60))
        ctx.stroke()


def fence(ctx, view, x, z0, z1, step=3.0):
    if view.ortho:
        return
    for z in np.arange(z0, z1, step):
        a, b = view.pt((x, 0, z)), view.pt((x, 1.1, z))
        if a and b:
            ctx.move_to(*a)
            ctx.line_to(*b)
    a, b = view.pt((x, 0.9, z0)), view.pt((x, 0.9, z1))
    if a and b:
        ctx.move_to(*a)
        ctx.line_to(*b)
    a, b = view.pt((x, 0.5, z0)), view.pt((x, 0.5, z1))
    if a and b:
        ctx.move_to(*a)
        ctx.line_to(*b)
    setc(ctx, hexc('#8a6a4a'))
    ctx.set_line_width(3)
    ctx.stroke()


def palm(ctx, view, x, z, s=1.0):
    if view.ortho:
        p = view.pt((x, 0, z))
        for k in range(6):
            a = k / 6 * 2 * math.pi
            ctx.move_to(*p)
            ctx.line_to(p[0] + math.cos(a) * 2.5 * view.s, p[1] + math.sin(a) * 2.5 * view.s)
        setc(ctx, hexc('#3f9a4c'))
        ctx.set_line_width(max(2, 0.5 * view.s))
        ctx.stroke()
        return
    b, tp, sc = view.pt((x, 0, z)), view.pt((x, 10 * s, z)), view.scale((x, 0, z))
    if not b or not tp or not sc:
        return
    ctx.move_to(*b)
    ctx.curve_to(b[0] + 0.6 * sc, b[1] - 4 * sc, tp[0] - 0.3 * sc, tp[1] + 3 * sc, *tp)
    setc(ctx, OUTL)
    ctx.set_line_width(max(2, 0.45 * sc))
    ctx.stroke()
    ctx.move_to(*b)
    ctx.curve_to(b[0] + 0.6 * sc, b[1] - 4 * sc, tp[0] - 0.3 * sc, tp[1] + 3 * sc, *tp)
    setc(ctx, hexc('#8a6a4a'))
    ctx.set_line_width(max(1, 0.3 * sc))
    ctx.stroke()
    for k in range(7):
        a = math.pi + k / 6 * math.pi
        ex, ey = tp[0] + math.cos(a) * 3.2 * s * sc, tp[1] + math.sin(a) * 1.2 * s * sc + 1.5 * s * sc
        ctx.move_to(*tp)
        ctx.curve_to(tp[0] + math.cos(a) * 1.5 * s * sc, tp[1] - 0.8 * s * sc, ex, ey - sc * 0.6 * s, ex, ey)
        setc(ctx, hexc('#2f8a45'))
        ctx.set_line_width(max(2, 0.35 * sc * s))
        ctx.stroke()


def lamp_post(ctx, view, x, z, side=1):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 8.5, z)), view.scale((x, 0, z))
    if not b or not tp or not s or s < 1.2:
        return
    ctx.rectangle(b[0] - 0.09 * s, tp[1], 0.18 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#6a6f7c'), OUTL, max(1, s / 60))
    a = view.pt((x - side * 1.6, 8.5, z))
    if a:
        ctx.move_to(*tp)
        ctx.line_to(*a)
        setc(ctx, hexc('#6a6f7c'))
        ctx.set_line_width(max(2, 0.14 * s))
        ctx.stroke()


def far_line(ctx, view, z, fn, x0=-2400, x1=2400, step=60, col='#7fa47a'):
    if view.ortho:
        return
    pts = [view.pt((x, fn(x), z)) for x in range(x0, x1 + 1, step)]
    base = view.pt((0, 0, z))
    if not base or not all(pts):
        return
    ctx.move_to(pts[0][0] - 2000, base[1] + 4)
    for q in pts:
        ctx.line_to(*q)
    ctx.line_to(pts[-1][0] + 2000, base[1] + 4)
    ctx.close_path()
    setc(ctx, hexc(col))
    ctx.fill()


def towers(ctx, view, z, x0, x1, n, hmin, hmax, seed=1, base='#8aa0b5', haze='#d4e8f6', w=(20, 40)):
    if view.ortho:
        return
    r = random.Random(seed)
    for i in range(n):
        X = x0 + (x1 - x0) * i / max(1, n - 1) + r.uniform(-8, 8)
        H = r.uniform(hmin, hmax)
        b, tp, s = view.pt((X, 0, z + r.uniform(-60, 60))), None, None
        Z = z + r.uniform(-60, 60)
        b, tp, s = view.pt((X, 0, Z)), view.pt((X, H, Z)), view.scale((X, 0, Z))
        if b and tp:
            ww = r.uniform(*w) * s
            ctx.rectangle(b[0] - ww / 2, tp[1], ww, b[1] - tp[1])
            setc(ctx, mix(hexc(base), hexc(haze), r.uniform(0.25, 0.5)))
            ctx.fill()


# ------------------------------------------------------------------ straight street
class Street:
    """Straight N-S road along Z. lanes per direction n; northbound lanes at x = (i + 0.5) * 3.5.
    median: 'yellow' | 'barrier'. cross: z of an E-W cross street (or None) with half width cw.
    kind: 'city' | 'village' | 'farm' | 'forest' | 'desert' | 'freeway'"""

    def __init__(self, kind, n=1, median='yellow', cross=None, cw=7.0, sidewalk=True, seed=1, palette=None,
                 sky=('#5fb4f2', '#dcf1ff'), ground='#86c46a', skyline=None, extras=None, hmin=8, hmax=30,
                 setback=4.0, crosswalks=True, stop_line=True, northbound_stop=True):
        self.kind, self.n, self.median, self.cross, self.cw = kind, n, median, cross, cw
        self.sidewalk, self.sky, self.ground_col = sidewalk, sky, hexc(ground)
        self.skyline_fn, self.extras = skyline, extras or (lambda ctx, view, t: [])
        self.crosswalks, self.stop_line = crosswalks, stop_line
        self.R = n * 3.5
        self.W = self.R + (2.0 if sidewalk else 1.2)
        r = random.Random(seed)
        pal = palette or ['#c9b9a6', '#a9b8c6', '#d8cfc0', '#8f9aa8', '#b7a28a', '#9fb3a0']
        self.items = []
        x_in = self.W + setback
        for sx in (-1, 1):
            z = -400.0
            while z < 500:
                if cross is not None and cross - cw - 6 < z + 30 and z < cross + cw + 6:
                    z = cross + cw + 6
                    continue
                if kind == 'city' or kind == 'freeway':
                    w = r.uniform(14, 26)
                    x0 = sx * (x_in + (0 if kind == 'city' else 8))
                    x1 = x0 + sx * r.uniform(12, 22)
                    self.items.append(('bld', (min(x0, x1), max(x0, x1), z, z + w, r.uniform(hmin, hmax), r.choice(pal))))
                    z += w + r.uniform(2, 8)
                elif kind == 'village':
                    w = r.uniform(9, 12)
                    x0 = sx * (x_in + 4)
                    x1 = x0 + sx * r.uniform(8, 11)
                    self.items.append(('house', (min(x0, x1), max(x0, x1), z, z + w, r.uniform(5.2, 6.4), r.choice(pal),
                                                 r.choice(['#4a4f5c', '#6b3f32', '#38485a', '#2f4a3a']))))
                    z += w + r.uniform(6, 12)
                else:
                    z += 40
            for z in np.arange(-400, 500, 11 if kind in ('city', 'village') else 7):
                if cross is not None and abs(z - cross) < cw + 4:
                    continue
                if kind in ('city', 'village'):
                    self.items.append(('tree', (sx * (self.R + 1.2 + (1.0 if sidewalk else 0)), z + r.uniform(-1, 1), 0.9 + r.uniform(0, 0.3))))
                elif kind == 'forest':
                    for _ in range(2):
                        self.items.append(('conifer', (sx * (self.W + 3 + r.uniform(0, 30)), z + r.uniform(-3, 3), 0.9 + r.uniform(0, 0.6))))
                elif kind == 'farm' and r.random() < 0.25:
                    self.items.append(('tree', (sx * (self.W + 2 + r.uniform(0, 4)), z, 1.0 + r.uniform(0, 0.4))))
                elif kind == 'desert' and r.random() < 0.18:
                    self.items.append(('shrub', (sx * (self.W + 3 + r.uniform(0, 40)), z)))
            if kind in ('city', 'freeway', 'village'):
                for z in np.arange(-400, 500, 32):
                    if cross is None or abs(z - cross) > cw + 3:
                        self.items.append(('lamp', (sx * (self.W - 0.3), z, sx)))

    def skyline(self, ctx, view):
        if self.skyline_fn:
            self.skyline_fn(ctx, view)

    def ground(self, ctx, view, t):
        R, W, c = self.R, self.W, self.cross
        if self.kind == 'farm':
            for k in range(-12, 14):
                for sx in (-1, 1):
                    gquad(ctx, view, *sorted((sx * (W + 1), sx * 260)), k * 40, k * 40 + 38,
                          hexc(['#b7c96a', '#86c46a', '#c9b06a', '#9fcf7a'][(k + (sx > 0)) % 4]))
        if self.kind == 'desert':
            gquad(ctx, view, -600, 600, -600, 900, hexc('#d9c08f'))
        gquad(ctx, view, -W, W, -500, 600, C_WALK if self.sidewalk else hexc('#9a958c'))
        gquad(ctx, view, -R - (0.0 if self.sidewalk else 1.0), R + (0.0 if self.sidewalk else 1.0), -500, 600, C_ASPH)
        if c is not None:
            fill_poly(ctx, view, [(-600, 0, c - self.cw - 2), (600, 0, c - self.cw - 2), (600, 0, c + self.cw + 2), (-600, 0, c + self.cw + 2)], C_WALK)
            fill_poly(ctx, view, [(-600, 0, c - self.cw), (600, 0, c - self.cw), (600, 0, c + self.cw), (-600, 0, c + self.cw)], C_ASPH)
        segs = [(-500, 600)] if c is None else [(-500, c - self.cw - (4.5 if self.crosswalks else 0)), (c + self.cw + (4.5 if self.crosswalks else 0), 600)]
        for a, b in segs:
            if self.median == 'yellow':
                gquad(ctx, view, -0.2, -0.07, a, b, C_YEL, 0.01)
                gquad(ctx, view, 0.07, 0.2, a, b, C_YEL, 0.01)
            else:
                gquad(ctx, view, -0.5, 0.5, a, b, hexc('#c9c4ba'), 0.01)
            for i in range(1, self.n):
                for sx in (-1, 1):
                    xl = sx * i * 3.5
                    for k in range(int(a // 12), int(b // 12) + 1):
                        z0, z1 = max(a, k * 12.0), min(b, k * 12.0 + 4)
                        if z1 > z0:
                            gquad(ctx, view, xl - 0.07, xl + 0.07, z0, z1, C_LINE, 0.01)
            for sx in (-1, 1):
                gquad(ctx, view, *sorted((sx * (R - 0.15), sx * R)), a, b, C_LINE, 0.01)
        if c is not None:
            if self.crosswalks:
                for zz in (c - self.cw - 4.0, c + self.cw + 0.8):
                    zebra(ctx, view, -R, R, zz, zz + 3.2, 'x')
            if self.stop_line:
                zs = c - self.cw - (4.6 if self.crosswalks else 1.0)
                gquad(ctx, view, 0.2, R, zs - 0.5, zs, C_LINE, 0.012)
            for sx in (-1, 1):
                fill_poly(ctx, view, [(-600, 0.01, c + sx * 0.07), (-R - 4.5, 0.01, c + sx * 0.07), (-R - 4.5, 0.01, c + sx * 0.2), (-600, 0.01, c + sx * 0.2)], C_YEL)
                fill_poly(ctx, view, [(R + 4.5, 0.01, c + sx * 0.07), (600, 0.01, c + sx * 0.07), (600, 0.01, c + sx * 0.2), (R + 4.5, 0.01, c + sx * 0.2)], C_YEL)
        if self.median == 'barrier' and not view.ortho:
            fill_poly(ctx, view, [(-0.35, 0, -500), (-0.35, 0, 600), (-0.35, 0.85, 600), (-0.35, 0.85, -500)], hexc('#c9c4ba'), OUTL, 2)
            fill_poly(ctx, view, [(0.35, 0, -500), (0.35, 0, 600), (0.35, 0.85, 600), (0.35, 0.85, -500)], hexc('#c9c4ba'), OUTL, 2)

    def objects(self, ctx, view, t):
        out = []
        for kind, a in self.items:
            if kind == 'bld':
                out.append((((a[0] + a[1]) / 2, a[4] / 2, (a[2] + a[3]) / 2), lambda a=a: building(ctx, view, *a, win='#3b5872')))
            elif kind == 'house':
                out.append((((a[0] + a[1]) / 2, 3, (a[2] + a[3]) / 2), lambda a=a: gable_house(ctx, view, *a)))
            elif kind == 'tree':
                out.append(((a[0], 1.5, a[1]), lambda a=a: tree3(ctx, view, a[0], a[1], a[2] * (0.45 if view.ortho else 1.0), int(abs(a[1])) % 3)))
            elif kind == 'conifer':
                out.append(((a[0], 2.5, a[1]), lambda a=a: conifer(ctx, view, a[0], a[1], a[2] * (0.5 if view.ortho else 1.2))))
            elif kind == 'lamp':
                out.append(((a[0], 4, a[1]), lambda a=a: lamp_post(ctx, view, a[0], a[1], a[2])))
            elif kind == 'shrub':
                out.append(((a[0], 0.5, a[1]), lambda a=a: shrub(ctx, view, a[0], a[1])))
        out += self.extras(ctx, view, t)
        return out


def shrub(ctx, view, x, z):
    if view.ortho:
        return
    b, s = view.pt((x, 0.4, z)), view.scale((x, 0.4, z))
    if b and s and s > 0.8:
        ellipse(ctx, b[0], b[1], 0.9 * s, 0.5 * s)
        fill_stroke(ctx, hexc('#8a9a5a'), OUTL, max(1, s / 60))


# ------------------------------------------------------------------ scenes
def ego_cam(w, t, mode, yaw=0.0):
    e = w.ego(t)
    x, z, h = e.pose(t)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    if mode == 'chase':
        return TCam((x - fx * 10.5, 3.6, z - fz * 10.5), h, 0.16, 1000, cy=520)
    if mode == 'chase_low':
        return TCam((x - fx * 7.5 - rx * 1.5, 1.9, z - fz * 7.5 - rz * 1.5), h + 0.08, 0.06, 1000)
    if mode == 'high':
        return TCam((x - fx * 14, 10.0, z - fz * 14), h, 0.44, 1000, cy=470)
    if mode == 'close_l':
        return TCam((x - fx * 5.6 - rx * 1.3, 1.7, z - fz * 5.6 - rz * 1.3), h + 0.13, 0.08, 1000)
    if mode == 'close_r':
        return TCam((x - fx * 5.6 + rx * 1.3, 1.7, z - fz * 5.6 + rz * 1.3), h - 0.13, 0.08, 1000)
    if mode == 'front':
        return look_at((x + fx * 9 + rx * 2.5, 1.6, z + fz * 9 + rz * 2.5), (x, 0.9, z), 950)
    if mode == 'side_l':
        return look_at((x - rx * 7 + fx * 1.0, 2.0, z - rz * 7 + fz * 1.0), (x + fx * 1.5, 0.9, z + fz * 1.5), 950)
    if mode == 'outer':
        return look_at((x + rx * 7.0 + fx * 8.0, 2.6, z + rz * 7.0 + fz * 8.0), (x + rx * 1.8, 0.7, z + rz * 1.8), 900)
    if mode == 'inside':
        return TCam((x - rx * 0.38 - fx * 0.2, 1.18, z - rz * 0.38 - fz * 0.2), h + yaw, 0.03, 1000, cy=470)
    raise ValueError(mode)


def m_cam(ctx, w, t, lt, kw):
    if kw['cam'] == 'fixed':
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000))
    elif kw['cam'] == 'follow':
        x, z, h = w.ego(t).pose(t)
        px, py, pz = kw['off']
        tx, ty, tz = kw.get('look', (0, 0.9, 0))
        view = look_at((x + px, py, z + pz), (x + tx, ty, z + tz), kw.get('f', 1000))
    else:
        view = ego_cam(w, t, kw['cam'], key_or(kw, 'yaw', lt, 0.0))
    draw_scene(ctx, view, w, t, overlay=(lambda c, v: kw['under'](c, v, t, lt)) if kw.get('under') else None)
    if kw['cam'] == 'inside':
        if abs(key_or(kw, 'yaw', lt, 0.0)) < 0.3:
            citykit.cockpit(ctx, w, t)
        else:
            side_window(ctx)
    if kw.get('hud', True) and kw['cam'] != 'fixed':
        hud(ctx, w, t)
    if kw.get('post'):
        kw['post'](ctx, view, t, lt)


def side_window(ctx):
    setc(ctx, hexc('#2a2a36'))
    ctx.rectangle(-10, -10, SW + 20, 50)
    ctx.fill()
    ctx.rectangle(-10, 860, SW + 20, 240)
    setc(ctx, hexc('#c23535'))
    ctx.fill()
    ctx.rectangle(-10, 850, SW + 20, 20)
    setc(ctx, OUTL)
    ctx.fill()


class NTop:
    """North-up map view (travel = up)."""
    ortho = True

    def __init__(self, xc, zc, s, ox=960, oy=540):
        self.xc, self.zc, self.s, self.ox, self.oy = xc, zc, s, ox, oy
        self.pos = (0, 1000, 0)

    def pt(self, P):
        return (self.ox + (P[0] - self.xc) * self.s, self.oy - (P[2] - self.zc) * self.s)

    def poly(self, pts):
        return [self.pt(p) for p in pts]

    def depth(self, P):
        return 0.0

    def scale(self, P):
        return self.s


class HTop(NTop):
    """Travel = right; the right side of the road is at the bottom."""
    hrot = math.pi / 2

    def pt(self, P):
        return (self.ox + (P[2] - self.zc) * self.s, self.oy + (P[0] - self.xc) * self.s)


def m_top(ctx, w, t, lt, kw):
    ex, ez = w.ego_xz(t)
    cls = HTop if kw.get('horizontal', True) else NTop
    xc = kw.get('xc', ex if not kw.get('horizontal', True) else 0.0)
    zc = ez + kw.get('ahead', 0.0) if kw.get('follow', True) else kw['zc']
    view = cls(xc, zc, kw.get('scale', 22.0))
    draw_scene(ctx, view, w, t, overlay=(lambda c, v: kw['under'](c, v, t, lt)) if kw.get('under') else None)
    if kw.get('post'):
        kw['post'](ctx, view, t, lt)


def m_mirror(ctx, w, t, lt, kw):
    """Outside mirror close-up (side 'L' or 'R'), same layout as the approved Toronto mirror shot."""
    side = kw.get('side', 'L')
    sg = -1 if side == 'L' else 1
    x, z, h = w.ego(t).pose(t)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    draw_scene(ctx, TCam((x + sg * rx * 0.4, 1.2, z + sg * rz * 0.4), h + sg * 0.75, 0.05, 700), w, t, ego=False)
    setc(ctx, (0.05, 0.08, 0.15), 0.25)
    ctx.paint()
    mx, my, rot = 930, 520, -0.06
    body = hexc(w.ego(t).col)

    def flip():
        if side == 'R':
            ctx.translate(SW, 0)
            ctx.scale(-1, 1)
    ctx.save()
    flip()
    poly(ctx, [(1700, -10), (SW + 10, -10), (SW + 10, SH + 10), (1450, SH + 10), (1640, 600)])
    fill_stroke(ctx, mix(body, (0, 0, 0), 0.15), OUTL, 6)
    poly(ctx, [(1640, 600), (1450, SH + 10), (1380, SH + 10), (1590, 560)])
    fill_stroke(ctx, hexc('#2a2a36'), OUTL, 4)
    ctx.translate(mx, my)
    ctx.rotate(rot)
    rrect(ctx, -560, -330, 1120, 660, 300)
    fill_stroke(ctx, body, OUTL, 7)
    rrect(ctx, -520, -290, 1040, 580, 260)
    fill_stroke(ctx, hexc('#0b1424'), OUTL, 5)
    ctx.restore()
    ctx.save()
    ctx.save()
    flip()
    ctx.translate(mx, my)
    ctx.rotate(rot)
    rrect(ctx, -500, -270, 1000, 540, 240)
    ctx.restore()
    ctx.clip()
    mcx = mx + 120 if side == 'L' else SW - (mx + 120)
    mcam = TCam((x + sg * rx * 1.05 + fx * 0.6, 1.05, z + sg * rz * 1.05 + fz * 0.6), h + math.pi - sg * kw.get('aim', 0.02), 0.04,
                kw.get('mf', 1400),
                cx=mcx, cy=my - 40, mirror=True)
    draw_scene(ctx, mcam, w, t, ego=False)
    ctx.save()
    flip()
    poly(ctx, [(mx + 330, my - 40), (mx + 520, my - 90), (mx + 520, my + 300), (mx + 260, my + 300)])
    fill_stroke(ctx, body, OUTL, 5)
    ctx.restore()
    g = cairo.LinearGradient(0, my - 270, SW, my + 270)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.1)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    b = w.ego(t).blink(t)
    if b == side:
        bx = (mx - 430) if side == 'L' else SW - (mx - 430)
        rrect(ctx, bx - 70, my + 232, 140, 36, 18)
        setc(ctx, AMBER)
        ctx.fill()
        glow(ctx, bx, my + 250, 200, AMBER, 0.7)
    if kw.get('post'):
        kw['post'](ctx, None, t, lt)


engine.SCENES.update(m_cam=m_cam, m_top=m_top, m_mirror=m_mirror)


# ------------------------------------------------------------------ overlays & series template
def big_text(text, y, size, col=(1, 1, 1), delay=0.0, pulse=False):
    def fn(ctx, lt, d):
        u = lt - delay
        if u < 0:
            return
        sc = (1 + 0.35 * (1 - smooth(u / 0.25))) * (1 + (0.04 * math.sin(lt * 9) if pulse else 0))
        ctx.save()
        ctx.translate(960, y)
        ctx.scale(sc, sc)
        outlined_text(ctx, text, 0, 0, size, col, lw=size * 0.2)
        ctx.restore()
    return fn


def mistake_title(n, text):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.2)
        sc = 1 + 0.3 * (1 - smooth(lt / 0.25))
        ctx.save()
        ctx.translate(960, 300)
        ctx.scale(sc, sc)
        label(ctx, 0, -95, f'MISTAKE #{n}', '#e0393e', 64)
        outlined_text(ctx, text, 0, 40, 92, (1, 1, 1), lw=18)
        ctx.restore()
    return fn


def x_mark(ctx, lt, d):
    a = smooth(lt / 0.15)
    sc = 1 + 0.6 * (1 - a)
    ctx.save()
    ctx.translate(1700, 240)
    ctx.scale(sc, sc)
    ellipse(ctx, 0, 0, 95, 95)
    fill_stroke(ctx, hexc('#e0393e'), (1, 1, 1), 8)
    ctx.move_to(-40, -40)
    ctx.line_to(40, 40)
    ctx.move_to(40, -40)
    ctx.line_to(-40, 40)
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(18)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.restore()


def check_mark(ctx, lt, d):
    a = smooth(lt / 0.15)
    sc = 1 + 0.6 * (1 - a)
    ctx.save()
    ctx.translate(1700, 240)
    ctx.scale(sc, sc)
    ellipse(ctx, 0, 0, 95, 95)
    fill_stroke(ctx, hexc('#22a356'), (1, 1, 1), 8)
    ctx.move_to(-42, 2)
    ctx.line_to(-12, 34)
    ctx.line_to(44, -32)
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(18)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.restore()


def end_card(line1, line2):
    def fn(ctx, lt, d):
        label(ctx, 960, 200, line1, '#22a356', 62)
        if lt > 1.0:
            b = smooth((lt - 1.0) / 0.3)
            ctx.save()
            ctx.translate(960, 320)
            ctx.scale(0.8 + 0.2 * b, 0.8 + 0.2 * b)
            label(ctx, 0, 0, line2, '#e0393e', 50)
            ctx.restore()
    return fn


def build_shots(defs):
    shots, prev = [], 0.0
    for end, kind, kw in defs:
        shots.append(Shot(end - prev, kind, **kw))
        prev = end
    return shots


def caption(text):
    return caption_in_scene(text)


def gap_meter(fn, title='GAP', unit='s', good=2.0, ok=1.2, x=960, y=960):
    def ov(ctx, lt, d):
        v = fn(lt)
        if v is None:
            return
        rrect(ctx, x - 230, y - 80, 460, 150, 34)
        setc(ctx, (0, 0, 0), 0.65)
        ctx.fill()
        col = hexc('#22c35e') if v >= good else (hexc('#ffd23f') if v >= ok else hexc('#ff4b4b'))
        text_center(ctx, title, x, y - 28, 36, (0.85, 0.85, 0.9))
        text_center(ctx, f'{v:.1f} {unit}', x, y + 45, 72, col)
    return ov


# ------------------------------------------------------------------ sound helpers
def series_sound_base(m, w, dur, amb=0.22, eng=0.1):
    m.add(city_ambience(dur), 0, amb)
    m.add(ambience(w, dur, inside=0.9), 0, eng)


def hook_sfx(m, t0=0.0):
    m.add(heartbeat(3, 120), t0 + 0.1, 1.2)
    m.add(riser(2.6), t0 + 0.2, 0.7)


def sting_bad(m, t):
    m.add(impact(), t, 0.5)
    m.add(sad_trombone(), t + 0.3, 0.55)


def sting_good(m, t):
    m.add(chime(), t, 0.7)
