"""Car stalled on the railway tracks: what to do. Prairie crossing near Moose Jaw, Saskatchewan.

World: road runs north (+Z); the railway runs east-west along X, rails at z = +-0.72. The train comes from the
EAST (+X) heading west. Our car stalls with its centre on the tracks (x = 1.75, z = 0).
Part 1 (wrong): he stays in the car trying to restart -> freeze before the train arrives (no crash shown).
Part 2 (right): get out NOW, move away from the tracks TOWARD the train at ~45 degrees (debris flies the way the
train travels), call the emergency number on the sign; the train hits the EMPTY car, the debris flies west.
Facts used: a freight train can need up to ~2 km to stop; Canadian crossings show an emergency phone number and a
crossing ID on a sign (number drawn here is a fictional 555 number).
"""
import math
import random

import cairo
import numpy as np

from mkit import *
from truckkit import draw_car_round, wheel3
from peoplekit import *
import citykit
import euro
import engine

DUR = 39.0
X_CAR = 1.75
T_STOP_W, T_STALL, T_LIGHTS_W = 5.3, 6.6, 8.6
T_W_END = 16.0                      # wrong part freezes here
T_HIT_W = 17.0                      # (never shown)
T_R0 = 17.2
T_LIGHTS_R = 15.0
T_DOOR, T_EXIT = 19.3, 19.7
T_HIT = 29.0
V_TR = 25.0                          # 90 km/h
RAIL = 0.72


# ------------------------------------------------------------------ train
def train_front_x(t, t_hit):
    """x of the locomotive nose (moving -x). Emergency braking after the hit."""
    if t < t_hit:
        return X_CAR + 0.92 + V_TR * (t_hit - t)
    u = t - t_hit
    return X_CAR + 0.92 - (V_TR * u - 0.6 * u * u)


NCARS = 9


def loco(ctx, view, xf, t, horn_on):
    h = -math.pi / 2
    xc = xf + 11.0
    Lf = L(xc, 0.0, h)               # local z = forward = -x
    d = view.depth((xc, 2, 0)) if not view.ortho else 1
    lw = max(1.4, min(4.5, 90 / max(d, 1)))
    body, stripe, dark = hexc('#22406e'), hexc('#f2c230'), hexc('#1c1c22')
    if view.ortho:
        fill_poly(ctx, view, [Lf(-1.55, 0, -11), Lf(1.55, 0, -11), Lf(1.55, 0, 11), Lf(-1.55, 0, 11)], body, OUTL, 3)
        fill_poly(ctx, view, [Lf(-1.55, 0, 6), Lf(1.55, 0, 6), Lf(1.55, 0, 11), Lf(-1.55, 0, 11)], stripe, OUTL, 2)
        return
    for wz in (-8.5, -6.8, -5.1, 5.1, 6.8, 8.5):
        for sx in (-1, 1):
            wheel3(ctx, view, Lf(sx * 0.72, 0.5, wz), h, 0.5, 0.2)
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    lbox(ctx, view, Lf, h, -1.5, 1.5, 0.95, 1.45, -11, 11, allc(dark), lw)                   # underframe
    lbox(ctx, view, Lf, h, -1.2, 1.2, 1.45, 4.3, -10.6, 5.2,
         {'front': body, 'back': body, 'left': mix(body, (0, 0, 0), 0.15), 'right': mix(body, (0, 0, 0), 0.08), 'top': mix(body, (1, 1, 1), 0.12)}, lw)
    vis = lbox(ctx, view, Lf, h, -1.5, 1.5, 1.45, 4.7, 5.2, 9.0,
               {'front': body, 'back': body, 'left': mix(body, (0, 0, 0), 0.15), 'right': mix(body, (0, 0, 0), 0.08), 'top': mix(body, (1, 1, 1), 0.12)}, lw)
    nv = lbox(ctx, view, Lf, h, -1.4, 1.4, 1.45, 3.0, 9.0, 11.0,
              {'front': stripe, 'back': body, 'left': mix(stripe, (0, 0, 0), 0.12), 'right': mix(stripe, (0, 0, 0), 0.06), 'top': body}, lw)
    for face, dx in (('left', -1.505), ('right', 1.505)):
        if face in vis:
            face_rect(ctx, view, Lf, face, 6.0, 8.6, 3.2, 4.2, dx, hexc('#9cc6e0'))
        face_rect(ctx, view, Lf, face, -10.5, 11.0, 1.5, 1.9, dx * 1.002, stripe) if face in vis else None
    if 'front' in vis:
        face_rect(ctx, view, Lf, 'front', -1.3, -0.15, 3.3, 4.3, 9.005, hexc('#9cc6e0'))
        face_rect(ctx, view, Lf, 'front', 0.15, 1.3, 3.3, 4.3, 9.005, hexc('#9cc6e0'))
    if 'front' in nv:
        for k in range(5):
            face_rect(ctx, view, Lf, 'front', -1.4 + k * 0.6, -1.1 + k * 0.6, 1.5, 3.0, 11.005, dark)
    # headlight + flashing ditch lights (they alternate while the horn sounds)
    for (lx, ly), on in (((0.0, 4.55), True), ((-1.1, 1.25), horn_on and (t * 2.4) % 1 < 0.5), ((1.1, 1.25), horn_on and (t * 2.4) % 1 >= 0.5)):
        P = Lf(lx, ly, 11.02 if ly < 2 else 9.02)
        p, s = view.pt(P), view.scale(P)
        if p and s and view.depth(P) > 0 and view.to_cam(P)[2] > 0:
            ellipse(ctx, p[0], p[1], 0.18 * s, 0.18 * s)
            setc(ctx, hexc('#fff6d8') if on else hexc('#7a7462'))
            ctx.fill()
            if on:
                glow(ctx, p[0], p[1], min(1.6 * s, 380), WHITE_L, 0.85)


def freight(ctx, view, xc, k):
    h = -math.pi / 2
    Lf = L(xc, 0.0, h)
    cols = ['#8a4b38', '#6b6f7c', '#b07a55', '#4f6f8f', '#7d3f30']
    col = hexc(cols[k % len(cols)])
    if view.ortho:
        fill_poly(ctx, view, [Lf(-1.5, 0, -8.6), Lf(1.5, 0, -8.6), Lf(1.5, 0, 8.6), Lf(-1.5, 0, 8.6)], col, OUTL, 3)
        return
    d = view.depth((xc, 2, 0))
    lw = max(1.2, min(4, 80 / max(d, 1)))
    for wz in (-6.5, -5.0, 5.0, 6.5):
        for sx in (-1, 1):
            wheel3(ctx, view, Lf(sx * 0.72, 0.45, wz), h, 0.45, 0.2)
    allc = lambda c: {kk: c for kk in ('front', 'back', 'left', 'right', 'top')}
    lbox(ctx, view, Lf, h, -1.4, 1.4, 0.9, 1.25, -8.6, 8.6, allc(hexc('#1c1c22')), lw)
    vis = lbox(ctx, view, Lf, h, -1.55, 1.55, 1.25, 4.1, -8.4, 8.4,
               {'front': col, 'back': col, 'left': mix(col, (0, 0, 0), 0.15), 'right': mix(col, (0, 0, 0), 0.07), 'top': mix(col, (1, 1, 1), 0.1)}, lw)
    for face, dx in (('left', -1.555), ('right', 1.555)):
        if face in vis:
            for j in range(6):
                face_rect(ctx, view, Lf, face, -7.8 + j * 2.7, -7.7 + j * 2.7, 1.35, 4.0, dx, mix(col, (0, 0, 0), 0.3))


class Train:
    def __init__(self, t_hit):
        self.t_hit = t_hit
        self.col = '#22406e'

    def pose(self, t):
        return train_front_x(t, self.t_hit), 0.0, -math.pi / 2

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        xf = train_front_x(t, self.t_hit)
        out = [((xf + 6.0, 2.2, 0.0), lambda: loco(ctx, view, xf, t, horn_on(t)))]
        for k in range(NCARS):
            xc = xf + 22.0 + 1.2 + k * 18.4 + 9.2
            if view.ortho or view.depth((xc, 2, 0)) < 400:
                out.append(((xc, 2.2, 0.0), lambda xc=xc, k=k: freight(ctx, view, xc, k)))
        return out


def horn_on(t):
    return any(a <= t < b for a, b in HORN_IV)


HORN_IV = [(0.4, 2.6), (12.0, 13.2), (13.5, 14.7), (14.9, 15.4), (15.6, 16.0),
           (23.0, 24.4), (24.7, 26.1), (26.3, 26.8), (27.0, 29.2)]


# ------------------------------------------------------------------ hero car (stall, door, impact)
def hit_pose(u):
    x = X_CAR - (27.0 * u - 3.2 * u * u) if u < 4.2 else X_CAR - (27.0 * 4.2 - 3.2 * 4.2 ** 2)
    uu = min(u, 2.2)
    z = 5.2 * uu - 1.1 * uu * uu
    h = 4.2 * (1 - math.exp(-u / 0.9))
    return x, z, h


class HeroCar(Track):
    def __init__(self, speed, ta, za, occ_until=99.0, t_hit=None, door=None):
        super().__init__(X_CAR, speed, ta, za, '#e23b3b', t0=-3, t1=45)
        self.occ_until, self.t_hit, self.door = occ_until, t_hit, door or (lambda t: 0.0)

    def pose(self, t):
        if self.t_hit is not None and t >= self.t_hit:
            u = t - self.t_hit
            x, z, h = hit_pose(u)
            return x, self.z(self.t_hit) + z, h
        return super().pose(t)

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        hop = 0.0
        if self.t_hit is not None and t >= self.t_hit:
            u = t - self.t_hit
            hop = max(0.0, 1.4 * math.sin(math.pi * min(u, 1.0)))

        def occ_fn(t=t):
            if t >= self.occ_until:
                return None

            def fn(ctx, view, Lf, h):
                person3d(ctx, view, Lf, -0.38, 0.05, 'hero', LOOK(t), 'shock' if t > T_LIGHTS_W else 'calm')
            return fn

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, None, True)
                return
            ctx.save()
            if hop:
                sc = view.scale((x, 0.8, z)) or 0
                ctx.translate(0, -hop * sc)
            draw_car_round(ctx, view, x, z, h, self.col, t, None, self.brake(t), occ=occ_fn())
            ctx.restore()
        out = [((x, 0.8, z), fn)]
        a = self.door(t)
        if a > 0.02 and not view.ortho:
            Lf = L(x, z, h)
            ex, ez = -0.92 - math.sin(a) * 1.15, 0.95 - math.cos(a) * 1.15
            lower = [Lf(-0.92, 0.35, 0.95), Lf(ex, 0.35, ez), Lf(ex, 0.85, ez), Lf(-0.92, 0.85, 0.95)]
            upper = [Lf(-0.92, 0.85, 0.95), Lf(ex, 0.85, ez), Lf(ex + 0.05, 1.32, ez + 0.2), Lf(-0.86, 1.36, 0.75)]

            def door_fn():
                fill_poly(ctx, view, lower, mix(hexc(self.col), (0, 0, 0), 0.18), OUTL, 2)
                fill_poly(ctx, view, upper, hexc('#3b4658'), OUTL, 2, 0.85)
            out.append((Lf(ex / 2 - 0.46, 0.8, (ez + 0.95) / 2), door_fn))
        return out


LOOK = Key([(0, 0.0), (8.8, 0.0), (9.1, -1.0), (10.0, -1.0), (10.3, 0.0), (99, 0.0)])

# ---- part 1: he follows the queue across, traffic ahead stops, he stops ON the tracks, it stalls
HERO_W = HeroCar(Key([(0, 13.0), (3.6, 13.0), (T_STOP_W, 0.0), (99, 0.0)], 'lin'), T_STOP_W + 0.5, 0.0)
QUEUE = [Track(1.75, Key([(0, 13.0), (3.3, 13.0), (T_STOP_W - 0.3, 0.0), (99, 0.0)], 'lin'), T_STOP_W + 0.5, 7.4, '#2f6f73'),
         Track(1.75, Key([(0, 13.0), (3.1, 13.0), (T_STOP_W - 0.5, 0.0), (99, 0.0)], 'lin'), T_STOP_W + 0.5, 14.0, '#c9c9d6'),
         Track(1.75, Key([(0, 13.0), (2.9, 13.0), (T_STOP_W - 0.7, 0.0), (99, 0.0)], 'lin'), T_STOP_W + 0.5, 20.6, '#f2a541')]
TRAIN_W = Train(T_HIT_W)

# ---- part 2: same stalled car; he gets out right away
HERO_R = HeroCar(const(0.0), T_R0, 0.0, occ_until=T_EXIT, t_hit=T_HIT,
                 door=Key([(0, 0.0), (T_DOOR, 0.0), (T_DOOR + 0.4, 1.05), (99, 1.05)]))
QUEUE_R = [Track(1.75, Key([(0, 0.0), (20.6 - 0.4 * i, 0.0), (24.0 - 0.4 * i, 12.0), (99, 12.0)], 'lin'), T_R0, q.z(T_STOP_W + 1), q.col)
           for i, q in enumerate(QUEUE)]       # traffic ahead clears and drives on
TRAIN_R = Train(T_HIT)

PATH_T = [T_EXIT, T_EXIT + 0.8, T_EXIT + 1.5, T_EXIT + 8.3, 99]
PATH_X = [X_CAR - 1.45, X_CAR - 1.45, X_CAR + 1.0, X_CAR + 17.0, X_CAR + 17.0]
PATH_Z = [0.3, 3.2, 3.9, 17.0, 17.0]


class HeroPed(Ped):
    def __init__(self):
        super().__init__(lambda t: float(np.interp(t, PATH_T, PATH_X)), lambda t: float(np.interp(t, PATH_T, PATH_Z)),
                         top='#d0912c', pants='#2b3a63', skin='#e9b98f', hair='#3a2316')

    def draw(self, ctx, view, t):
        if t < T_EXIT:
            return
        euro.ped_bb(ctx, view, self.x(t), self.z(t), t * 1.7, self.top, self.pants, self.skin, self.hair, False,
                    self.walking(t), 0.0)


HERO_PED = HeroPed()


# ------------------------------------------------------------------ debris after the hit (flies WEST, the way the train goes)
_r = random.Random(9)
DEBRIS = [dict(vx=-_r.uniform(14, 30), vy=_r.uniform(2, 7), vz=_r.uniform(-3, 7), s=_r.uniform(0.15, 0.45),
               col=_r.choice(['#e23b3b', '#e23b3b', '#2a3448', '#1c1c22', '#c9c9d6']), spin=_r.uniform(-9, 9)) for _ in range(18)]


class Debris:
    col = '#ccc'

    def visible(self, t):
        return True

    def pose(self, t):
        return 0, 0, 0

    def items(self, ctx, view, t):
        u = t - T_HIT
        if u < 0 or u > 6:
            return []
        out = []
        for d in DEBRIS:
            tt = min(u, 2 * d['vy'] / 9.8)
            x = X_CAR + d['vx'] * tt * (1 - tt * 0.15)
            y = 0.8 + d['vy'] * tt - 4.9 * tt * tt
            z = d['vz'] * tt
            if view.ortho:
                continue

            def fn(x=x, y=y, z=z, d=d):
                p, s = view.pt((x, max(0.05, y), z)), view.scale((x, y, z))
                if not p or not s:
                    return
                ctx.save()
                ctx.translate(*p)
                ctx.rotate(d['spin'] * min(u, tt + 0.01))
                ctx.rectangle(-d['s'] * s, -d['s'] * 0.6 * s, 2 * d['s'] * s, 1.2 * d['s'] * s)
                fill_stroke(ctx, hexc(d['col']), OUTL, max(1, s * 0.02))
                ctx.restore()
            out.append(((x, y, z), fn))
        return out


# ------------------------------------------------------------------ prairie + crossing
C_WHEAT = hexc('#e2c46a')
C_BALLAST = hexc('#9a958c')


def gate_angle(t):
    """0 = up (vertical), 1 = down (horizontal)."""
    t0 = T_LIGHTS_W + 1.0 if t < T_R0 - 0.01 else T_LIGHTS_R + 1.0
    return smooth((t - t0) / 2.0)


def lights_on(t):
    return t >= (T_LIGHTS_W if t < T_R0 - 0.01 else T_LIGHTS_R)


def crossing_mast(ctx, view, x, z, face_h, t, gate_dir):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 0.3 * view.s, 0.3 * view.s)
        fill_stroke(ctx, hexc('#c9c9d6'), OUTL, 2)
        a = gate_angle(t)
        if a > 0.5:
            q = view.pt((x + gate_dir * 4.4, 0, z))
            ctx.move_to(*p)
            ctx.line_to(*q)
            setc(ctx, hexc('#e0393e'))
            ctx.set_line_width(max(2, 0.18 * view.s))
            ctx.stroke()
        return
    b, tp = view.pt((x, 0, z)), view.pt((x, 4.4, z))
    s = view.scale((x, 2, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.08 * s, tp[1], 0.16 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#c9c9d6'), OUTL, max(1, s / 60))
    fx, fz = math.sin(face_h), math.cos(face_h)
    rx, rz = math.cos(face_h), -math.sin(face_h)
    # crossbuck
    c = (x + fx * 0.1, 4.0, z + fz * 0.1)
    for sg in (-1, 1):
        a = (c[0] - rx * 0.9, c[1] + sg * 0.55, c[2] - rz * 0.9)
        bb = (c[0] + rx * 0.9, c[1] - sg * 0.55, c[2] + rz * 0.9)
        pa, pb = view.pt(a), view.pt(bb)
        if pa and pb:
            for col, w_ in ((hexc('#d62828'), 0.32), ((1, 1, 1), 0.22)):
                ctx.move_to(*pa)
                ctx.line_to(*pb)
                setc(ctx, col)
                ctx.set_line_width(w_ * s)
                ctx.set_line_cap(cairo.LINE_CAP_BUTT)
                ctx.stroke()
    # light unit: black backplate with two red lights flashing alternately
    on = lights_on(t)
    ph = (t * 1.1) % 1
    pc = view.pt((x + fx * 0.15, 3.0, z + fz * 0.15))
    if pc:
        rrect(ctx, pc[0] - 0.75 * s, pc[1] - 0.28 * s, 1.5 * s, 0.56 * s, 0.25 * s)
        fill_stroke(ctx, hexc('#1c1c22'), OUTL, max(1, s / 60))
        for k, sg in enumerate((-1, 1)):
            q = view.pt((x + fx * 0.2 + rx * sg * 0.45, 3.0, z + fz * 0.2 + rz * sg * 0.45))
            if not q:
                continue
            lit = on and ((ph < 0.5) == (k == 0))
            ellipse(ctx, q[0], q[1], 0.2 * s, 0.2 * s)
            setc(ctx, hexc('#ff2a2a') if lit else hexc('#5a1414'))
            ctx.fill()
            if lit and view.to_cam((x + fx * 0.2, 3.0, z + fz * 0.2))[2] > 0 and fx * (view.pos[0] - x) + fz * (view.pos[2] - z) > 0:
                glow(ctx, q[0], q[1], min(1.4 * s, 260), (1, 0.15, 0.15), 0.8)
    # blue emergency sign under the lights
    ps = view.pt((x + fx * 0.12, 2.1, z + fz * 0.12))
    if ps and s > 6:
        ctx.rectangle(ps[0] - 0.3 * s, ps[1] - 0.2 * s, 0.6 * s, 0.4 * s)
        fill_stroke(ctx, hexc('#1f5fbf'), OUTL, max(1, s / 80))
    # gate arm (pivots down across the lane)
    a = gate_angle(t)
    piv = (x, 1.2, z)
    L_ = 4.4
    ang = (1 - a) * math.pi / 2
    end = (x + gate_dir * L_ * math.cos(ang), 1.2 + L_ * math.sin(ang), z)
    pa, pb = view.pt(piv), view.pt(end)
    if pa and pb:
        n = 8
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            qa = view.pt((piv[0] + (end[0] - piv[0]) * u0, piv[1] + (end[1] - piv[1]) * u0, z))
            qb = view.pt((piv[0] + (end[0] - piv[0]) * u1, piv[1] + (end[1] - piv[1]) * u1, z))
            if qa and qb:
                ctx.move_to(*qa)
                ctx.line_to(*qb)
                setc(ctx, OUTL)
                ctx.set_line_width(0.2 * s + 3)
                ctx.stroke()
                ctx.move_to(*qa)
                ctx.line_to(*qb)
                setc(ctx, hexc('#d62828') if i % 2 == 0 else (1, 1, 1))
                ctx.set_line_width(0.2 * s)
                ctx.stroke()


def grain_elevator(ctx, view, x, z):
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    Lf = lambda a, b, c: (a, b, c)
    red = hexc('#b3322b')
    lbox(ctx, view, Lf, 0.0, x - 4, x + 4, 0, 18, z - 5, z + 5,
         {'front': red, 'back': red, 'left': mix(red, (0, 0, 0), 0.15), 'right': mix(red, (0, 0, 0), 0.05), 'top': red}, 3)
    lbox(ctx, view, Lf, 0.0, x - 2, x + 2, 18, 24, z - 3, z + 3, allc(mix(red, (0, 0, 0), 0.1)), 3)
    lbox(ctx, view, Lf, 0.0, x + 4, x + 12, 0, 6, z - 3, z + 3, allc(mix(red, (1, 1, 1), 0.1)), 3)
    if not view.ortho:
        c, s = view.pt((x, 14, z - 5.02)), view.scale((x, 14, z - 5.02))
        if c and s and s > 1.2:
            text_center(ctx, 'PRAIRIE POOL', c[0], c[1] + 0.4 * s, 1.2 * s, (1, 1, 1))


def power_pole(ctx, view, x, z):
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 9, z)), view.scale((x, 0, z))
    if not b or not tp or not s or view.ortho:
        return
    ctx.move_to(*b)
    ctx.line_to(*tp)
    setc(ctx, hexc('#7a5a3a'))
    ctx.set_line_width(max(1.5, 0.25 * s))
    ctx.stroke()
    a, c = view.pt((x, 8.4, z - 1.2)), view.pt((x, 8.4, z + 1.2))
    if a and c:
        ctx.move_to(*a)
        ctx.line_to(*c)
        ctx.set_line_width(max(1.2, 0.15 * s))
        ctx.stroke()


class Prairie:
    sky = ('#3d9be0', '#e8f5ff')

    def __init__(self):
        self.ground_col = C_WHEAT
        r = random.Random(12)
        self.poles = [(-14.0 if False else x, -6.0) for x in np.arange(-400, 600, 45)]
        self.bales = [(r.uniform(14, 120) * r.choice([-1, 1]), r.uniform(-200, 300)) for _ in range(30)]
        self.bales = [(x, z) for x, z in self.bales if abs(z) > 12 and abs(x) > 12]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        far_line(ctx, view, 1600, lambda x: 6 + 3 * math.sin(x / 140), col='#c9b46a')
        # big prairie clouds
        hy = view.horizon()
        for cx0, cy0, sc0 in ((300, 260, 1.4), (1250, 200, 1.1), (1800, 300, 0.9)):
            for dx, dy, rr in ((0, 0, 60), (70, -30, 80), (150, 0, 60), (75, 18, 65)):
                ellipse(ctx, cx0 + dx * sc0, hy - cy0 + dy * sc0, rr * sc0, rr * sc0 * 0.7)
            setc(ctx, (1, 1, 1), 0.92)
            ctx.fill()

    def ground(self, ctx, view, t):
        for k in range(-10, 14):
            for sx in (-1, 1):
                gquad(ctx, view, *sorted((sx * 6.5, sx * 400)), k * 60 + 3, k * 60 + 60, hexc(['#e2c46a', '#d8b85a', '#c9b06a'][(k + (sx > 0)) % 3]))
        gquad(ctx, view, -600, 600, -2.6, 2.6, C_BALLAST)
        gquad(ctx, view, -6.5, 6.5, -600, 600, hexc('#b8ab8c'))
        gquad(ctx, view, -3.6, 3.6, -600, 600, C_ASPH)
        gquad(ctx, view, -0.2, -0.07, -600, -3, C_YEL, 0.01)
        gquad(ctx, view, 0.07, 0.2, -600, -3, C_YEL, 0.01)
        gquad(ctx, view, -0.2, -0.07, 3, 600, C_YEL, 0.01)
        gquad(ctx, view, 0.07, 0.2, 3, 600, C_YEL, 0.01)
        for sx in (-1, 1):
            gquad(ctx, view, *sorted((sx * 3.45, sx * 3.6)), -600, 600, C_LINE, 0.01)
        # crossing panels, ties, rails
        gquad(ctx, view, -4.5, 4.5, -1.6, 1.6, hexc('#6f6a62'), 0.005)
        ex = view.pos[0]
        lo, hi = (ex - 120, ex + 260) if not view.ortho else (view.xc - 80, view.xc + 80)
        if not view.ortho:
            for xx in np.arange(math.floor(lo), hi, 0.65):
                if abs(xx) < 4.5:
                    continue
                gquad(ctx, view, xx - 0.12, xx + 0.12, -1.3, 1.3, hexc('#6b4a2f'), 0.01)
        for zr in (-RAIL, RAIL):
            if view.ortho:
                gquad(ctx, view, lo, hi, zr - 0.06, zr + 0.06, hexc('#5a5d66'), 0.02)
            else:
                fill_poly(ctx, view, [(lo, 0.0, zr), (hi, 0.0, zr), (hi, 0.16, zr), (lo, 0.16, zr)], hexc('#7a7f8c'), OUTL, 1)
        # stop lines before the crossing
        gquad(ctx, view, 0.2, 3.5, -5.6, -5.2, C_LINE, 0.012)
        gquad(ctx, view, -3.5, -0.2, 5.2, 5.6, C_LINE, 0.012)
        for zz in (-12.0, 12.0):
            sx = 1 if zz < 0 else -1
            gquad(ctx, view, *sorted((sx * 0.4, sx * 3.2)), zz - 1.6, zz + 1.6, C_LINE, 0.012) if False else None

    def objects(self, ctx, view, t):
        out = [((5.0, 2, -4.5), lambda: crossing_mast(ctx, view, 5.0, -4.5, math.pi, t, -1)),
               ((-5.0, 2, 4.5), lambda: crossing_mast(ctx, view, -5.0, 4.5, 0.0, t, 1)),
               ((-70, 9, -18), lambda: grain_elevator(ctx, view, -70, -18))]
        for x, z in self.poles:
            out.append(((x, 4, z), lambda x=x, z=z: power_pole(ctx, view, x, z)))
        for x, z in self.bales:
            out.append(((x, 0.7, z), lambda x=x, z=z: hay_bale(ctx, view, x, z)))
        out.append(((60, 3, 140), lambda: silo(ctx, view, 60, 140)))
        out.append(((75, 3, 150), lambda: barn(ctx, view, 68, 82, 144, 156)))
        return out


world = SegWorld(DUR, [hook_seg(0, 3.0, 13.0, HERO_W, QUEUE + [TRAIN_W], []),
                       (3.0, T_R0, HERO_W, QUEUE + [TRAIN_W], []),
                       (T_R0, 99, HERO_R, QUEUE_R + [TRAIN_R, Debris()], [HERO_PED])], Prairie(), 'kmh')
world.police_flash = lambda t: 0.0


# ------------------------------------------------------------------ scenes
def rr_cam(ctx, w, t, lt, kw):
    tf = min(t, kw['freeze']) if 'freeze' in kw else t
    if kw['cam'] == 'fixed':
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000))
    elif kw['cam'] == 'ped':
        x, z = HERO_PED.x(tf), HERO_PED.z(tf)
        ox, oy, oz = kw['off']
        view = look_at((x + ox, oy, z + oz), (x + kw.get('lx', 0), 1.0, z + kw.get('lz', 0)), kw.get('f', 950))
    else:
        view = ego_cam(w, tf, kw['cam'])
    sh = kw.get('shake', 0.0)
    if sh and T_HIT <= t < T_HIT + 1.2:
        k = sh * (1 - (t - T_HIT) / 1.2)
        view = TCam((view.pos[0] + 0.3 * k * math.sin(t * 60), view.pos[1] + 0.2 * k * math.cos(t * 53), view.pos[2]), view.yaw, view.pitch, view.f) \
            if isinstance(view, TCam) else view
    draw_scene(ctx, view, w, tf)
    if 'freeze' in kw and t >= kw['freeze']:
        u = t - kw['freeze']
        setc(ctx, (1, 1, 1), max(0, 0.8 - u * 3))
        ctx.paint()
        setc(ctx, (0.6, 0, 0), 0.25)
        ctx.paint()
    if kw.get('hud'):
        hud(ctx, w, tf)
    if kw.get('post'):
        kw['post'](ctx, view, tf, lt)


def stall_win(ctx, w, t, lt, kw):
    """Our hero through his window (seen from the passenger side): turning the key, panicking / unbuckling."""
    WIN = [(240, 770), (1730, 770), (1730, 190), (600, 150)]
    shake = 6 if kw.get('crank') and (t * 9) % 1 < 0.5 else 0
    ctx.save()
    ctx.translate(math.sin(t * 50) * shake, 0)
    path = lambda: (ctx.move_to(*WIN[0]), [ctx.line_to(*p) for p in WIN[1:]], ctx.close_path())
    path()
    ctx.clip()
    setc(ctx, hexc('#2c2d38'))
    ctx.paint()
    g = cairo.LinearGradient(0, 200, 0, 560)
    g.add_color_stop_rgb(0, *hexc('#3d9be0'))
    g.add_color_stop_rgb(1, *hexc('#e8f5ff'))
    ctx.set_source(g)
    ctx.rectangle(560, 200, 1200, 360)
    ctx.fill()
    ctx.rectangle(560, 470, 1200, 120)
    setc(ctx, C_WHEAT)
    ctx.fill()
    if lights_on(t):
        on = (t * 1.1) % 1 < 0.5
        glow(ctx, 1500, 330, 160, (1, 0.15, 0.15), 0.6 if on else 0.15)
    ctx.rectangle(0, 120, SW, 80)
    setc(ctx, hexc('#4a4b58'))
    ctx.fill()
    ctx.move_to(200, 560)
    ctx.curve_to(400, 520, 560, 560, 620, 800)
    ctx.line_to(200, 800)
    ctx.close_path()
    fill_stroke(ctx, hexc('#1f2029'), OUTL, 5)
    ellipse(ctx, 520, 860, 70, 260, 0.15)
    ellipse(ctx, 520, 860, 38, 220, 0.15)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#15151c'), OUTL, 5)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    rrect(ctx, 1080, 300, 300, 700, 90)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 5)
    rrect(ctx, 1110, 250, 230, 150, 60)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 5)
    turn = kw.get('turn', -0.35)
    head2d(ctx, 900, 480, 175, 'hero', kw.get('expr', 'calm'), turn, t)
    # seatbelt across the chest (slides away when he unbuckles)
    ub = smooth((lt - kw['unbuckle']) / 0.5) if 'unbuckle' in kw else 0.0
    if ub < 1:
        ctx.save()
        ctx.translate(ub * 260, ub * 220)
        poly(ctx, [(1080, 640), (1140, 660), (760, 1000), (690, 980)])
        fill_stroke(ctx, hexc('#2a2a33'), OUTL, 4, 1 - ub)
        ctx.restore()
    if kw.get('sweat'):
        sx, sy = 1050, 360 + (lt * 50) % 70
        ctx.move_to(sx, sy - 40)
        ctx.curve_to(sx + 26, sy, sx + 26, sy + 26, sx, sy + 26)
        ctx.curve_to(sx - 26, sy + 26, sx - 26, sy, sx, sy - 40)
        fill_stroke(ctx, hexc('#8fd6ff'), OUTL, 4)
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
    rrect(ctx, 1450, 850, 170, 40, 18)
    fill_stroke(ctx, mix(body, (0, 0, 0), 0.25), OUTL, 4)
    if kw.get('crank'):
        if (t * 3) % 1 < 0.6:
            label(ctx, 960, 75, 'click... rrr... rrr...', '#3a3d48', 46)


def sign_close(ctx, w, t, lt, kw):
    """The blue emergency sign on the crossing mast (number is fictional)."""
    g = cairo.LinearGradient(0, 0, 0, SH)
    g.add_color_stop_rgb(0, *hexc('#3d9be0'))
    g.add_color_stop_rgb(0.62, *hexc('#e8f5ff'))
    g.add_color_stop_rgb(0.62, *C_WHEAT)
    g.add_color_stop_rgb(1, *hexc('#c9b06a'))
    ctx.set_source(g)
    ctx.paint()
    on = (t * 1.1) % 1 < 0.5
    glow(ctx, 300, 160, 260, (1, 0.15, 0.15), 0.35 if on else 0.1)
    ctx.rectangle(1500, -10, 90, SH + 20)
    fill_stroke(ctx, hexc('#c9c9d6'), OUTL, 6)
    sc = 1 + 0.04 * smooth(lt / 2.0)
    ctx.save()
    ctx.translate(960, 520)
    ctx.scale(sc, sc)
    rrect(ctx, -560, -300, 1120, 600, 30)
    fill_stroke(ctx, hexc('#1f5fbf'), (1, 1, 1), 12)
    text_center(ctx, 'EMERGENCY / URGENCE', 0, -190, 64, (1, 1, 1))
    text_center(ctx, 'Call 1-800-555-0199', 0, -40, 92, hexc('#ffd23f'))
    text_center(ctx, 'Crossing ID: 247.3 PRAIRIE SUB', 0, 90, 56, (1, 1, 1))
    text_center(ctx, 'Report a problem at this crossing', 0, 200, 44, (0.85, 0.9, 1.0))
    ctx.restore()
    if lt > 0.6:
        a = smooth((lt - 0.6) / 0.3)
        ctx.save()
        ctx.translate(960, 830)
        label(ctx, 0, 0, 'Tell them: car stuck, crossing ID', '#22a356', 48)
        ctx.restore()


def calm_face(ctx, w, t, lt, kw):
    g = cairo.LinearGradient(0, 0, 0, SH)
    g.add_color_stop_rgb(0, *hexc('#3d9be0'))
    g.add_color_stop_rgb(0.6, *hexc('#e8f5ff'))
    g.add_color_stop_rgb(0.6, *C_WHEAT)
    g.add_color_stop_rgb(1, *hexc('#c9b06a'))
    ctx.set_source(g)
    ctx.paint()
    # the empty, wrecked car far behind him + the train still rolling by
    for k in range(5):
        x = (-200 + k * 420 - lt * 600) % 2400 - 300
        rrect(ctx, x, 430, 400, 150, 10)
        fill_stroke(ctx, mix(hexc(['#8a4b38', '#6b6f7c', '#b07a55', '#4f6f8f', '#7d3f30'][k]), hexc('#e8f5ff'), 0.35), OUTL, 3)
    head2d(ctx, 960, 560, 210, 'hero', kw.get('expr', 'relieved'), 0.0, t)


engine.SCENES.update(rr_cam=rr_cam, stall_win=stall_win, sign_close=sign_close, calm_face=calm_face)


def top_post(ctx, view, t, lt):
    # train direction, the danger cone (debris flies WEST), and the safe 45-degree escape path (EAST + away)
    a, b = view.pt((60, 0, -4.5)), view.pt((25, 0, -4.5))
    arrow_path(ctx, [a, b], hexc('#ffffff'), 10, 0.95, None, 30)
    label(ctx, a[0] - 60, a[1] + 70, 'TRAIN', '#22406e', 38)
    c0 = view.pt((X_CAR, 0, 0))
    cone = [view.pt((X_CAR + 1, 0, 0)), view.pt((X_CAR - 70, 0, 18)), view.pt((X_CAR - 70, 0, -18))]
    poly(ctx, cone)
    setc(ctx, hexc('#ff4b4b'), 0.35)
    ctx.fill()
    label(ctx, view.pt((X_CAR - 40, 0, 0))[0], view.pt((X_CAR - 40, 0, 0))[1] - 40, 'DEBRIS ZONE', '#e0393e', 40)
    pts = [view.pt((x, 0, z)) for x, z in zip(PATH_X[:4], PATH_Z[:4])]
    arrow_path(ctx, pts, hexc('#22c35e'), 12, 1.0, None, 34)
    q = view.pt((PATH_X[3], 0, PATH_Z[3]))
    label(ctx, q[0], q[1] - 50, 'SAFE: toward the train, away from tracks', '#22a356', 36)


HOOK = dict(cam='fixed', pos=(-9.0, 1.5, -3.2), target=(40.0, 2.4, 0.4), f=1000)
SIDE = dict(cam='fixed', pos=(12.0, 1.7, -14.0), target=(1.0, 1.6, 0.0), f=950)
DRONE_W = dict(cam='fixed', pos=(-26.0, 22.0, -34.0), target=(14.0, 0.0, 2.0), f=900, freeze=T_W_END - 0.8)
RUN = dict(cam='fixed', pos=(23.0, 2.3, 11.0), target=(0.0, 1.0, 2.5), f=900)
IMPACT = dict(cam='fixed', pos=(26.0, 3.4, 27.0), target=(-8.0, 1.2, 1.0), f=950, shake=1.0)
END = dict(cam='fixed', pos=(-14.0, 6.0, -26.0), target=(2.0, 1.0, 2.0), f=900)
TOPV = dict(xc=12.0, zc=4.0, scale=13.0)


def m_top_fixed(ctx, w, t, lt, kw):
    view = NTop(kw['xc'], kw['zc'], kw['scale'])
    draw_scene(ctx, view, w, t)
    top_post(ctx, view, t, lt)


engine.SCENES.update(m_top_fixed=m_top_fixed)

defs = [
    (3.0, 'rr_cam', dict(HOOK)),
    (6.0, 'rr_cam', dict(cam='chase', hud=True)),
    (8.5, 'stall_win', dict(expr='worried', crank=True, turn=-0.35)),
    (11.0, 'rr_cam', dict(SIDE)),
    (13.5, 'stall_win', dict(expr='shock', crank=True, sweat=True, turn=-0.6)),
    (T_W_END, 'rr_cam', dict(DRONE_W)),
    (T_R0, 'rewind_seq', dict()),
    (19.7, 'stall_win', dict(expr='focus', unbuckle=0.6, turn=-0.2)),
    (23.0, 'rr_cam', dict(RUN)),
    (25.5, 'm_top_fixed', dict(TOPV)),
    (27.5, 'sign_close', dict()),
    (28.8, 'rr_cam', dict(IMPACT)),
    (31.0, 'rr_cam', dict(cam='fixed', pos=(-12.0, 3.0, 12.0), target=(4.0, 1.0, -1.0), f=900, shake=1.0)),
    (33.6, 'calm_face', dict(expr='relieved')),
    (DUR, 'rr_cam', dict(END)),
]
shots = build_shots(defs)
shots[6].kw.update(srcs=list(reversed(shots[1:6])), dur=shots[6].dur)
video = Video(['Your car stalls ON the tracks.', 'What do you do?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('A train is coming...', 930, 110, hexc('#ffd23f'), 0.2, True)),
    (3.0, 6.0, location_tag('Near Moose Jaw, Saskatchewan')),
    (3.2, 6.0, caption('Traffic stops... right on the tracks')),
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, E[2], caption('And the engine stalls')),
    (S[3] + 0.2, E[3], caption('Lights. Bells. Gates coming down.')),
    (S[4] + 0.2, E[4], caption('He stays inside, trying to restart...')),
    (S[5] + 0.2, E[5], caption('A train can need 2 km to stop')),
    (S[5] + 1.7, E[5], x_mark),
    (S[7], E[12], badge('RIGHT', '#22a356')),
    (S[11] + 0.2, E[11], caption('Safe distance. Train coming.')),
    (S[12] + 0.4, E[12], caption("Cars can be replaced. You can't.")),
    (S[13] + 0.2, E[13], caption('Safe. Then call 911 too.')),
    (S[14] + 0.2, E[14], end_card('Never stop ON the tracks.', 'Did you know to go TOWARD the train? Comment!')),
    (S[14] + 1.4, E[14], caption('Wait until there is room on the other side')),
]
for n, (i, txt) in enumerate(((7, 'Get OUT. Right now.'), (8, 'Move away, TOWARD the train (45 deg)'), (9, 'Debris flies the way the train goes'),
                              (10, 'Call the number on the sign')), 1):
    if i == 9:
        video.overlays += [(S[i] + 0.15, E[i], caption(txt))]
        continue
    video.overlays += [(S[i], E[i], step_badge(n if n < 3 else 3)), (S[i] + 0.15, E[i], caption(txt))]


# ------------------------------------------------------------------ sound
def crossing_bell(d, rate=2.2):
    out = np.zeros(int(d * SR) + SR)
    k = 0
    while k / rate < d:
        tt = np.arange(int(0.4 * SR)) / SR
        s = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt / dd) for f, dd in ((1250, 0.25), (2900, 0.12), (4300, 0.06)))
        place(out, s * 0.3, k / rate)
        k += 1
    return out[:int(d * SR)]


def train_horn(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    s = np.zeros(n)
    for f in (277, 330, 415, 554):
        ph = 2 * np.pi * f * tt
        s += sum(np.sin(k * ph) / k for k in range(1, 8))
    s = np.tanh(s * 0.6)
    return bp(s, 200, 3500) * env_adsr(n, 0.05, 0.12) * 0.4


def train_rumble(d, t_hit):
    n = int(d * SR)
    tt = np.arange(n) / SR
    dist = np.abs(np.array([train_front_x(t, t_hit) for t in tt[::400]]))
    dist = np.interp(tt, tt[::400], dist)
    g = 1.0 / (1 + (dist / 40) ** 2)
    clack = np.zeros(n)
    for k in range(int(d * 6)):
        i = int(k / 6 * SR)
        m_ = min(n - i, int(0.03 * SR))
        clack[i:i + m_] += np.exp(-np.arange(m_) / SR / 0.008)
    return (lp(noise(n), 160) * 0.9 + bp(noise(n), 300, 1200) * 0.3 + clack * 0.5) * g


def crank(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    s = bp(noise(n), 200, 1400) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 9 * tt)))
    return s * 0.5 * (((tt * 3) % 1) < 0.6)


def sound():
    m = Mixer(video.dur)
    m.add(lp(noise(int(video.dur * SR)), 400), 0, 0.08)                         # prairie wind
    hook_sfx(m)
    # hook (shows t = 13..16 of part 1)
    m.add(crossing_bell(3.0), 0, 0.35)
    m.add(train_horn(2.2), 0.4, 0.6)
    m.add(ambience(world, 6.0, inside=0.9)[:int(5.3 * SR)], 3.0, 0.12)
    m.add(brake_squeal(0.8), 4.4, 0.25)
    m.add(click(), 6.7, 0.7)
    m.add(crank(1.6), 6.9, 0.6)
    m.add(crossing_bell(T_W_END - T_LIGHTS_W), T_LIGHTS_W, 0.4)
    m.add(heartbeat(4, 130), 11.2, 0.8)
    m.add(crank(2.0), 11.3, 0.6)
    for a, b in HORN_IV:
        if 11 < a < T_W_END:
            m.add(train_horn(b - a), a, 0.8)
    m.add(train_rumble(T_W_END - 12.0, T_HIT_W - 12.0)[:int((T_W_END - 12.0) * SR)], 12.0, 0.8)
    m.add(impact(), T_W_END - 0.8, 0.5)
    m.add(sad_violin(), T_W_END - 0.6, 0.8)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    # part 2
    m.add(crossing_bell(T_HIT + 3 - T_R0), T_R0, 0.32)
    m.add(click(), S[7] + 0.6, 0.8)                                               # seatbelt
    m.add(thud(), T_DOOR, 0.4)
    t = T_EXIT + 0.2
    while t < T_EXIT + 8.2:
        m.add(footsteps(0.1, 100), t, 0.3)
        t += 0.3
    for i in (7, 8, 10):
        m.add(pop(), S[i] + 0.15, 0.6)
    for a, b in HORN_IV:
        if a > T_R0:
            m.add(train_horn(b - a), a, 0.8)
    m.add(train_rumble(DUR - 22.0, T_HIT - 22.0), 22.0, 0.9)
    m.add(impact(), T_HIT, 1.0)
    m.add(thud(), T_HIT, 1.0)
    m.add(bp(noise(int(1.2 * SR)), 1500, 6000) * np.exp(-np.arange(int(1.2 * SR)) / SR / 0.3) * 0.6, T_HIT + 0.05, 0.8)
    m.add(brake_squeal(4.0), T_HIT + 0.3, 0.5)
    m.add(chime(), S[13] + 0.4, 0.6)
    m.add(success_jingle(), S[14] + 0.3, 0.8)
    return m.out(video.dur)


def verify():
    print('part 1: hero stops at z', round(HERO_W.z(T_STOP_W + 1), 2), '(front', round(HERO_W.z(T_STOP_W + 1) + 2.2, 2),
          ') | car ahead rear at', round(QUEUE[0].z(T_STOP_W + 1) - 2.2, 2), '| gap', round(QUEUE[0].z(T_STOP_W + 1) - HERO_W.z(T_STOP_W + 1) - 4.4, 2))
    print('   train nose at freeze', round(train_front_x(T_W_END - 0.8, T_HIT_W) - X_CAR - 0.92, 1), 'm from the car')
    print('part 2: hero clear of tracks (z > 2.6) at t =', round(next(t for t in np.arange(T_EXIT, 40, 0.01) if HERO_PED.z(t) > 2.6), 2),
          '| train hits at', T_HIT)
    print('   hero position at hit', round(HERO_PED.x(T_HIT), 1), round(HERO_PED.z(T_HIT), 1), '| distance to impact',
          round(math.hypot(HERO_PED.x(T_HIT) - X_CAR, HERO_PED.z(T_HIT)), 1), 'm (debris flies -x)')
    worst = 99
    for t in np.arange(T_HIT, T_HIT + 6, 0.02):
        cx, cz, ch = HERO_R.pose(t)
        tx = train_front_x(t, T_HIT)
        if cx > tx - 0.5 and cx < tx + 200:
            worst = min(worst, cz - 1.55 - 1.0)
    print('   after hit: wreck clearance beside the passing train (m):', round(worst, 2), '| wreck stops at', [round(v, 1) for v in HERO_R.pose(T_HIT + 6)])
    print('   min distance debris -> hero:', round(min(math.hypot(X_CAR + d['vx'] * min(u, 2 * d['vy'] / 9.8) * (1 - min(u, 2 * d['vy'] / 9.8) * 0.15) - HERO_PED.x(T_HIT + u),
                                                                 d['vz'] * min(u, 2 * d['vy'] / 9.8) - HERO_PED.z(T_HIT + u)) for d in DEBRIS for u in np.arange(0, 6, 0.05)), 1))
    print('   path vs south-west gate arm: hero passes z=4.5 at x', round(float(np.interp(4.5, PATH_Z[2:4], PATH_X[2:4])), 2), '(arm ends at x -0.6)')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        run(video, sound, 'tracks.mp4')
