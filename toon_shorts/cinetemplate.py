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
                 trailer=('#f4f4f6', '#e0393e', 'PEACH STATE'), cab='#2f6f9f', t0=-3, t1=80, damage=None, mark=None):
        super().__init__(x, speed, ta, za, col, brake=brake, blink=blink, t0=t0, t1=t1)
        self.kind, self.occ, self.flash, self.police, self.trailer, self.cab = kind, occ, flash, police, trailer, cab
        self.damage = damage or []           # [('front' | 'back', world t of impact)]
        self.mark = mark                     # fn(t) -> bool: red arrow + ground glow on the problem driver
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

        mk = self.mark and self.mark(t)

        def fn():
            if view.ortho:
                if mk:
                    p = view.pt((x, 0, z))
                    ellipse(ctx, p[0], p[1], 3.2 * view.s, 3.2 * view.s)
                    setc(ctx, hexc('#ff2d2d'))
                    ctx.set_line_width(5)
                    ctx.stroke()
                draw_car_top_g(ctx, view, x, z, h, self.col, t, self.blink(t), self.occ is not None)
                return
            if mk:
                mark_ring(ctx, view, x, z, h, t)
            draw_car_round(ctx, view, x, z, h, self.col, t, self.blink(t), self.brake(t), occ=self.occ(t) if self.occ else None)
            Lf = L(x, z, h)
            if self.flash and self.flash(t):
                for sx in (-0.62, 0.62):
                    P = Lf(sx, 0.68, 2.26)
                    p, s = view.pt(P), view.scale(P)
                    if p and s and view.to_cam(P)[2] > 0 and (math.sin(h) * (view.pos[0] - x) + math.cos(h) * (view.pos[2] - z)) > 0:
                        glow(ctx, p[0], p[1], min(1.2 * s + 30, 200), (1.0, 0.97, 0.85), 0.9)
            if self.damage:
                for face, t_d in self.damage:
                    if t >= t_d:
                        crumple(ctx, view, Lf, x, z, h, face)
            if mk:
                mark_arrow(ctx, view, x, z, t)
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


def mark_ring(ctx, view, x, z, h, t):
    """Pulsing red glow on the ground under a car."""
    pts = [view.pt((x + 1.7 * math.cos(a) * math.cos(h) + 3.1 * math.sin(a) * math.sin(h), 0.02,
                    z - 1.7 * math.cos(a) * math.sin(h) + 3.1 * math.sin(a) * math.cos(h))) for a in np.linspace(0, 2 * math.pi, 28)]
    if not all(pts):
        return
    k = 0.5 + 0.5 * math.sin(t * 6.0)
    poly(ctx, pts)
    setc(ctx, hexc('#ff2d2d'), 0.28 + 0.2 * k)
    ctx.fill_preserve()
    setc(ctx, hexc('#ff2d2d'), 0.9)
    ctx.set_line_width(max(2.0, (view.scale((x, 0, z)) or 10) * 0.08))
    ctx.stroke()


def mark_arrow(ctx, view, x, z, t):
    """Bouncing red arrow pointing down at a car (never smaller than ~70 px so it reads from far away)."""
    bob = 0.25 * math.sin(t * 5.0)
    P = (x, 2.9 + bob, z)
    p, s = view.pt(P), view.scale(P)
    if not p or not s or view.to_cam(P)[2] <= 0.5:
        return
    L_ = max(min(1.5 * s, 260.0), 70.0)
    w = L_ * 0.62
    cx, cy = p[0], p[1] - L_ * 0.15
    glow(ctx, cx, cy - L_ * 0.5, L_ * 0.9, hexc('#ff2d2d'), 0.25)
    poly(ctx, [(cx - w * 0.28, cy - L_), (cx + w * 0.28, cy - L_), (cx + w * 0.28, cy - L_ * 0.42), (cx + w * 0.55, cy - L_ * 0.42),
               (cx, cy), (cx - w * 0.55, cy - L_ * 0.42), (cx - w * 0.28, cy - L_ * 0.42)])
    fill_stroke(ctx, hexc('#ff2d2d'), (1, 1, 1), max(3.0, L_ * 0.05))


def crumple(ctx, view, Lf, x, z, h, face):
    """Crushed bumper: jagged dark dent + crack lines on the front or back face (only when that face is seen)."""
    sz = 1 if face == 'front' else -1
    if (math.sin(h) * (view.pos[0] - x) + math.cos(h) * (view.pos[2] - z)) * sz <= 0:
        return
    zf = sz * 2.27
    rnd = random.Random(7 if sz > 0 else 9)
    top = [Lf(-0.82 + 1.64 * i / 8, 0.95 + rnd.uniform(-0.12, 0.1), zf) for i in range(9)]
    bot = [Lf(0.82 - 1.64 * i / 8, 0.28 + rnd.uniform(-0.05, 0.08), zf) for i in range(9)]
    pts = [view.pt(P) for P in top + bot]
    if not all(pts):
        return
    poly(ctx, pts)
    setc(ctx, hexc('#3a3b44'), 0.85)
    ctx.fill_preserve()
    setc(ctx, OUTL)
    ctx.set_line_width(2)
    ctx.stroke()
    for k in range(4):
        a, b = view.pt(Lf(-0.6 + k * 0.4, 0.9, zf)), view.pt(Lf(-0.5 + k * 0.38, 0.4, zf))
        if a and b:
            ctx.move_to(*a)
            ctx.line_to(*b)
            setc(ctx, (0.85, 0.85, 0.9), 0.7)
            ctx.set_line_width(2)
            ctx.stroke()


class CrashFX:
    """Impact flash, flying debris and rising steam at a world point. point_fn(t) -> (x, y, z)."""

    def __init__(self, t_imp, point_fn, steam=6.0):
        self.ti, self.pf, self.steam = t_imp, point_fn, steam
        r = random.Random(3)
        self.bits = [(r.uniform(-4, 4), r.uniform(2, 6), r.uniform(-3, 5), r.choice(['#2b2b33', '#c9c9d6', '#ff9b3a', '#e23b3b'])) for _ in range(26)]
        self.col, self.ext = '#000', (0, 0, 0, 0)

    def visible(self, t):
        return True

    def pose(self, t):
        x, y, z = self.pf(self.ti)
        return x, z, 0.0

    def items(self, ctx, view, t):
        u = t - self.ti
        if view.ortho or u < 0:
            return []
        X, Y, Z = self.pf(self.ti)
        out = []
        if u < 0.35:
            def flash():
                p, s = view.pt((X, Y, Z)), view.scale((X, Y, Z))
                if p and s:
                    glow(ctx, p[0], p[1], min(4.0 * s * (1 - u / 0.35) + 40, 700), (1.0, 0.95, 0.8), 0.9)
            out.append(((X, Y, Z - 0.1), flash))
        if u < 1.6:
            for vx, vy, vz, col in self.bits:
                P = (X + vx * u, max(0.05, Y + vy * u - 4.9 * u * u), Z + vz * u)

                def bit(P=P, col=col):
                    p, s = view.pt(P), view.scale(P)
                    if p and s:
                        rrect(ctx, p[0] - 0.09 * s, p[1] - 0.05 * s, 0.18 * s, 0.1 * s, 0.03 * s)
                        fill_stroke(ctx, hexc(col), OUTL, 1)
                out.append((P, bit))
        for k in range(int(min(u, self.steam) / 0.25)):
            age = u - k * 0.25
            if age > 3.0:
                continue
            P = (X + 0.4 * math.sin(k * 1.7), Y + 0.3 + age * 1.1, Z - 0.6 + 0.3 * age)

            def puff(P=P, age=age):
                p, s = view.pt(P), view.scale(P)
                if p and s:
                    ellipse(ctx, p[0], p[1], (0.35 + age * 0.5) * s, (0.3 + age * 0.4) * s)
                    setc(ctx, (0.93, 0.93, 0.95), max(0.0, 0.5 - age * 0.16))
                    ctx.fill()
            out.append((P, puff))
        return out


def follow_sim(lead_v, gap0, react, decel, t_brake, t0=-3.0, t1=60.0, dt=1 / 240, bounce=1.0, post_decel=None):
    """Lead (speed key) + follower starting gap0 m (bumper) behind at the lead's speed; follower brakes `react` s after
    t_brake at `decel`. Inelastic rear-end impact (equal masses) with a small bounce. Returns (lead_z(t), foll_z(t),
    t_impact, closing speed m/s, lead_v_after(t), foll_v_after(t))."""
    ts = np.arange(t0, t1, dt)
    zl, zf, vl_, vf_ = [0.0], [-(4.5 + gap0)], [lead_v(t0)], [lead_v(t0)]
    hit, vrel = None, 0.0
    vl, vf = lead_v(t0), lead_v(t0)
    pd = post_decel or decel
    for t in ts[1:]:
        if hit is None:
            vl = max(0.0, lead_v(t))
            vf = vf if t < t_brake + react else max(0.0, vf - decel * dt)
            if t < t_brake + react:
                vf = lead_v(t) if t < t_brake else vf
        else:
            vl, vf = max(0.0, vl - pd * dt), max(0.0, vf - pd * dt)
        zl.append(zl[-1] + vl * dt)
        zf.append(zf[-1] + vf * dt)
        if hit is None and zl[-1] - zf[-1] <= 4.5:
            hit, vrel = t, vf - vl
            vc = (vl + vf) / 2
            vl, vf = vc + bounce, vc - bounce
            zf[-1] = zl[-1] - 4.5
        vl_.append(vl)
        vf_.append(vf)
    zl, zf = np.array(zl), np.array(zf)
    return (lambda t: float(np.interp(t, ts, zl)), lambda t: float(np.interp(t, ts, zf)), hit, vrel,
            lambda t: float(np.interp(t, ts, vl_)), lambda t: float(np.interp(t, ts, vf_)))


def chain_sim(lead_v, gaps, reacts, decel, t_brake, t0=-3.0, t1=60.0, dt=1 / 240, L=4.5, bounce=0.5):
    """Lead + N followers in one lane (bumper gaps `gaps`, reaction times `reacts`, all brake at `decel` after seeing the
    car ahead brake). Inelastic rear-end impacts with a small bounce, cars never overlap. Returns
    ([z_fn], [v_fn], [impact times per follower or None])."""
    n = len(gaps) + 1
    ts = np.arange(t0, t1, dt)
    z = [0.0]
    for g in gaps:
        z.append(z[-1] - L - g)
    z = np.array(z)
    v = np.full(n, lead_v(t0))
    braking_at = [t_brake] + [None] * (n - 1)
    hits = [None] * n
    Z, VV = [z.copy()], [v.copy()]
    for t in ts[1:]:
        for i in range(n):
            if i == 0:
                v[0] = max(0.0, lead_v(t)) if hits[1] is None else max(0.0, v[0] - decel * dt)
                continue
            if braking_at[i] is None and braking_at[i - 1] is not None and t >= braking_at[i - 1] + reacts[i - 1]:
                braking_at[i] = t
            if braking_at[i] is not None:
                v[i] = max(0.0, v[i] - decel * dt)
            else:
                v[i] = v[i - 1] if t < t_brake else v[i]
        z = z + v * dt
        for i in range(1, n):
            if z[i - 1] - z[i] < L:
                z[i] = z[i - 1] - L
                if v[i] > v[i - 1] + 0.05:
                    if hits[i] is None:
                        hits[i] = t
                    vc = (v[i] + v[i - 1]) / 2
                    v[i - 1], v[i] = vc + bounce, max(0.0, vc - bounce)
                    if braking_at[i - 1] is None:
                        braking_at[i - 1] = t
        Z.append(z.copy())
        VV.append(v.copy())
    Z, VV = np.array(Z), np.array(VV)
    zf = [(lambda t, i=i: float(np.interp(t, ts, Z[:, i]))) for i in range(n)]
    vf = [(lambda t, i=i: float(np.interp(t, ts, VV[:, i]))) for i in range(n)]
    return zf, vf, hits[1:]


class SimCar(Veh):
    """Veh driven by a z(t) function (from follow_sim) instead of a speed key."""

    def __init__(self, x, zfn, vfn, col, **kw):
        super().__init__(x, const(V), 0.0, 0.0, col, **kw)
        self.zfn, self.vfn = zfn, vfn
        if 'brake' not in kw:
            self.brake = lambda t: 1.0 if self.vfn(t + 0.1) < self.vfn(t) - 0.02 or self.vfn(t) < 0.05 else 0.0

    def z(self, t):
        return self.zfn(t)

    def speed(self, t):
        return self.vfn(t)


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


def cn_tower(ctx, view, X, Z, haze='#ffc89a', H=553.0):
    """CN Tower landmark (far backdrop): tapering shaft, pod with the observation ring, upper pod and antenna."""
    if view.ortho:
        return
    col = mix(hexc('#b9b4b8'), hexc(haze), 0.35)
    dark = mix(hexc('#77727c'), hexc(haze), 0.35)

    def P(x, y):
        return view.pt((X + x, y, Z))
    pts = [P(-14, 0), P(14, 0), P(4, 330), P(-4, 330)]
    if not all(pts):
        return
    poly(ctx, pts)
    setc(ctx, col)
    ctx.fill()
    for y0, y1, w in ((330, 352, 26), (352, 362, 20)):
        q = [P(-w / 2, y0), P(w / 2, y0), P(w / 2 - 3, y1), P(-w / 2 + 3, y1)]
        if all(q):
            poly(ctx, q)
            setc(ctx, dark if y0 == 330 else col)
            ctx.fill()
    q = [P(-3, 362), P(3, 362), P(2.5, 446), P(-2.5, 446)]
    if all(q):
        poly(ctx, q)
        setc(ctx, col)
        ctx.fill()
    q = [P(-6, 446), P(6, 446), P(6, 456), P(-6, 456)]
    if all(q):
        poly(ctx, q)
        setc(ctx, dark)
        ctx.fill()
    a_, b_ = P(0, 456), P(0, H)
    if a_ and b_:
        ctx.move_to(*a_)
        ctx.line_to(*b_)
        setc(ctx, col)
        ctx.set_line_width(max(1.0, (view.scale((X, 400, Z)) or 0.1) * 2.2))
        ctx.stroke()


def toronto_far(Z=2600.0, xc=-120.0):
    """Backdrop for Highway(far=...): downtown Toronto towers + the CN Tower."""
    def far(ctx, view):
        city_skyline(ctx, view, Z=Z, xc=xc, n=24, seed=21, base='#6c7a92', hmin=60, hmax=210)
        cn_tower(ctx, view, xc + 140.0, Z - 30.0)
    return far


def city_401(gantry_z=(500.0, 1400.0)):
    """Highway 401 (Toronto, Ontario) dressing for Highway(...)."""
    return Highway(sky=('#3a6db5', '#ffd3a0'), grass='#8fae5f', hills='#7e9a63', far=toronto_far(), roadside='trees', seed=40,
                   gantries=[(gantry_z[0], [(1.0, 8.0, '401 EXPRESS', 'Kingston'), (9.5, 16.5, 'EXIT 369', 'Yonge St')]),
                             (gantry_z[1], [(1.0, 8.0, '401 EAST', 'Pickering'), (9.5, 16.5, 'EXIT 375', 'Bayview Ave')])])


def city_dallas(gz=(420.0, 1300.0)):
    """I-35E into Dallas, Texas (downtown skyline ahead)."""
    def far(ctx, view):
        city_skyline(ctx, view, Z=1600.0, xc=40.0, n=26, seed=11, base='#6f7690', hmin=70, hmax=230)
    return Highway(sky=('#3d6fb4', '#ffcf9a'), far=far, seed=2,
                   gantries=[(gz[0], [(1.0, 8.0, 'I-35E SOUTH', 'Downtown Dallas'), (9.5, 16.5, 'EXIT 429', 'Main St')]),
                             (gz[1], [(1.0, 8.0, 'I-35E SOUTH', 'Waco'), (9.5, 16.5, 'EXIT 428', 'Commerce St')])])


def city_golden(gz=(400.0, 1300.0)):
    """I-70 at Golden, Colorado (Rockies ahead, pine trees)."""
    def far(ctx, view):
        mountains(ctx, view, Z=view.pos[2] + 3400 if not view.ortho else 3400, col='#6c7895', hmax=620, seed=8)
    return Highway(sky=('#3d6fb4', '#ffcf9a'), grass='#a9a565', hills='#8a8a5a', far=far, roadside='pines', seed=7,
                   gantries=[(gz[0], [(1.0, 8.0, 'I-70 WEST', 'Mountain Resorts'), (9.5, 16.5, 'EXIT 263', 'Golden')]),
                             (gz[1], [(1.0, 8.0, 'I-70 WEST', 'Idaho Springs'), (9.5, 16.5, 'EXIT 260', 'C-470')])])


def cone(ctx, view, x, z):
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 0.75, z)), view.scale((x, 0, z))
    if not b or not tp or not s or s < 0.6:
        return
    w = 0.38 * s
    lw = max(1, min(3, s / 30))
    rrect(ctx, b[0] - w * 0.75, b[1] - 0.05 * s, w * 1.5, 0.1 * s, 0.02 * s)
    fill_stroke(ctx, hexc('#222222'), OUTL, lw)
    poly(ctx, [(b[0] - w / 2, b[1]), (b[0] + w / 2, b[1]), (tp[0] + w * 0.1, tp[1]), (tp[0] - w * 0.1, tp[1])])
    fill_stroke(ctx, hexc('#ff7a1a'), OUTL, lw)
    y1 = b[1] + (tp[1] - b[1]) * 0.45
    y2 = b[1] + (tp[1] - b[1]) * 0.65
    poly(ctx, [(b[0] - w * 0.36, y1), (b[0] + w * 0.36, y1), (b[0] + w * 0.27, y2), (b[0] - w * 0.27, y2)])
    setc(ctx, (1, 1, 1))
    ctx.fill()


class WorkZone:
    """Right lane (x 10.5..14) closed from z_t on: cone taper over `taper` m, cone line after, flashing arrow board,
    orange warning signs before. Add it to the world's agents."""

    def __init__(self, z_t, taper=60.0, length=400.0, signs=(250.0, 120.0)):
        self.zt, self.taper, self.len, self.signs = z_t, taper, length, signs
        self.col, self.ext = '#ff7a1a', (0, 0, 0, 0)
        pts = [(14.0 - 3.4 * k / 10, z_t - taper + taper * k / 10) for k in range(11)]
        pts += [(10.6, z_t + 8.0 * k) for k in range(1, int(length / 8))]
        self.cones = pts

    def visible(self, t):
        return True

    def pose(self, t):
        return 12.0, self.zt, 0.0

    def items(self, ctx, view, t):
        out = []
        if view.ortho:
            def top():
                for x, z in self.cones:
                    p = view.pt((x, 0, z))
                    ellipse(ctx, p[0], p[1], 0.35 * view.s, 0.35 * view.s)
                    setc(ctx, hexc('#ff7a1a'))
                    ctx.fill()
            return [((12.0, 0.0, self.zt), top)]
        ez = view.pos[2]
        for x, z in self.cones:
            if ez - 30 < z < ez + 500:
                out.append(((x, 0.4, z), lambda x=x, z=z: cone(ctx, view, x, z)))
        out.append(((12.25, 1.5, self.zt + 6.0), lambda: self.board(ctx, view, t)))
        for d in self.signs:
            out.append(((16.0, 2.0, self.zt - d), lambda d=d: self.sign(ctx, view, self.zt - d)))
        return out

    def board(self, ctx, view, t):
        z = self.zt + 6.0
        if not fill_poly(ctx, view, [(10.9, 0.6, z), (13.6, 0.6, z), (13.6, 2.6, z), (10.9, 2.6, z)], hexc('#1b1b22'), OUTL, 2):
            return
        fill_poly(ctx, view, [(11.0, 0.0, z + 0.5), (13.5, 0.0, z + 0.5), (13.5, 0.6, z + 0.5), (11.0, 0.6, z + 0.5)], hexc('#ff7a1a'), OUTL, 1)
        on = (t * 1.6) % 1 < 0.6
        k = int(t * 4) % 4
        for i in range(5):
            if on and i <= k + 1:
                c = view.pt((13.2 - i * 0.5, 1.6, z - 0.05))
                s = view.scale((13.2 - i * 0.5, 1.6, z))
                if c and s:
                    glow(ctx, c[0], c[1], max(4, 0.35 * s), hexc('#ffd23f'), 0.9)
        tip = [view.pt(P) for P in ((11.2, 1.6, z - 0.06), (11.8, 2.1, z - 0.06), (11.8, 1.1, z - 0.06))]
        if on and all(tip):
            poly(ctx, tip)
            setc(ctx, hexc('#ffd23f'))
            ctx.fill()

    def sign(self, ctx, view, z):
        x = 16.2
        a, b = view.pt((x, 0, z)), view.pt((x, 2.0, z))
        if not a or not b:
            return
        ctx.move_to(*a)
        ctx.line_to(*b)
        setc(ctx, hexc('#7a7f8c'))
        ctx.set_line_width(max(1.5, 0.1 * (view.scale((x, 1, z)) or 5)))
        ctx.stroke()
        pts = [view.pt(P) for P in ((x, 2.0, z), (x + 1.0, 3.0, z), (x, 4.0, z), (x - 1.0, 3.0, z))]
        if all(pts):
            poly(ctx, pts)
            fill_stroke(ctx, hexc('#ff8c1a'), OUTL, 2)
            c, s = view.pt((x, 3.0, z)), view.scale((x, 3.0, z))
            if c and s and s > 6:
                text_center(ctx, 'RIGHT LANE', c[0], c[1] - 0.05 * s, 0.26 * s, OUTL)
                text_center(ctx, 'CLOSED', c[0], c[1] + 0.3 * s, 0.26 * s, OUTL)


def city_phoenix(gz=(500.0, 1400.0)):
    """I-10 through Phoenix, Arizona: desert (saguaro + rocks), red-brown mountains, small downtown skyline."""
    def far(ctx, view):
        Zb = (view.pos[2] if not view.ortho else 0.0)
        mountains(ctx, view, Z=Zb + 3000, col='#9a6a55', snow='#b07a60', haze='#ffc08a', seed=12, peaks=7, hmax=330)
        city_skyline(ctx, view, Z=Zb + 2200, xc=-150.0, n=10, seed=31, base='#7d6a72', haze='#ffc08a', hmin=50, hmax=140)
    return Highway(sky=('#3f74c0', '#ffd09a'), grass='#d9b98a', hills='#c69c74', far=far, roadside='cactus', asphalt='#55555e', seed=12,
                   gantries=[(gz[0], [(1.0, 8.0, 'I-10 EAST', 'Phoenix'), (9.5, 16.5, 'EXIT 143', '7th St')]),
                             (gz[1], [(1.0, 8.0, 'I-10 EAST', 'Tucson'), (9.5, 16.5, 'EXIT 144', '16th St')])])


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


# cockpit palette (glossy cartoon, dark navy-purple like the reference look)
CK_DARK, CK_MID, CK_HI, CK_RED = hexc('#1b1828'), hexc('#2a2640'), hexc('#4d4870'), hexc('#ff3b4e')
WHEEL_C = (560, 1580)           # steering wheel centre (left-hand drive: wheel left of the camera)
MIRROR_R = (650, 40, 620, 175)  # rear-view mirror rect (x, y, w, h)


def _dash_edge(ctx):
    ctx.move_to(-10, 1290)
    ctx.curve_to(400, 1262, 1520, 1262, CANVAS + 10, 1290)


def cabin(ctx, steer, mph=None, hands=True, sleeve=None):
    """Clean animated cockpit: thin roof, slanted A-pillars, glossy dash band with gauge hood, centre screen,
    vents, red accent lights and a full steering wheel on the left (turns with steer)."""
    # roof strip
    ctx.move_to(-10, -10)
    ctx.line_to(CANVAS + 10, -10)
    ctx.line_to(CANVAS + 10, 60)
    ctx.curve_to(1400, 22, 520, 22, -10, 60)
    ctx.close_path()
    setc(ctx, CK_DARK)
    ctx.fill()
    # A-pillars: slim diagonal wedges + door frame below them
    for sg in (-1, 1):
        def X(v):
            return v if sg < 0 else CANVAS - v
        poly(ctx, [(X(-10), 40), (X(90), 40), (X(420), 1300), (X(300), 1300), (X(-10), 260)])
        g = cairo.LinearGradient(X(0), 0, X(420), 0)
        g.add_color_stop_rgb(0, *CK_DARK)
        g.add_color_stop_rgb(1, *CK_MID)
        ctx.set_source(g)
        ctx.fill()
        ctx.move_to(X(90), 40)
        ctx.line_to(X(420), 1300)
        setc(ctx, CK_HI)
        ctx.set_line_width(5)
        ctx.stroke()
        poly(ctx, [(X(-10), 1000), (X(120), 1060), (X(300), 1300), (X(-10), 1300)])
        setc(ctx, CK_DARK)
        ctx.fill()
    # dashboard band
    _dash_edge(ctx)
    ctx.line_to(CANVAS + 10, CANVAS + 10)
    ctx.line_to(-10, CANVAS + 10)
    ctx.close_path()
    g = cairo.LinearGradient(0, 1260, 0, 1920)
    g.add_color_stop_rgb(0, *CK_MID)
    g.add_color_stop_rgb(0.18, *mix(CK_MID, CK_DARK, 0.5))
    g.add_color_stop_rgb(1, *mix(CK_DARK, (0, 0, 0), 0.3))
    ctx.set_source(g)
    ctx.fill()
    _dash_edge(ctx)
    setc(ctx, CK_HI)
    ctx.set_line_width(6)
    ctx.stroke()
    # lower dash panel line
    ctx.move_to(-10, 1440)
    ctx.curve_to(500, 1420, 1420, 1420, CANVAS + 10, 1440)
    setc(ctx, mix(CK_DARK, (0, 0, 0), 0.2))
    ctx.set_line_width(4)
    ctx.stroke()
    wx, wy = WHEEL_C
    # gauge hood behind the wheel
    ctx.move_to(wx - 300, 1300)
    ctx.curve_to(wx - 280, 1180, wx + 280, 1180, wx + 300, 1300)
    ctx.close_path()
    fill_stroke(ctx, CK_DARK, CK_HI, 4)
    for gx in (wx - 130, wx + 130):
        ellipse(ctx, gx, 1330, 92, 80)
        fill_stroke(ctx, hexc('#0f0d18'), CK_HI, 3)
        ctx.arc_negative(gx, 1330, 70, math.radians(200), math.radians(-20))
        setc(ctx, CK_RED, 0.8)
        ctx.set_line_width(5)
        ctx.stroke()
    if mph is not None:
        a_ = math.radians(200 - 220 * clamp(mph / 140.0, 0, 1))
        ctx.move_to(wx - 130, 1330)
        ctx.line_to(wx - 130 + math.cos(a_) * 64, 1330 - math.sin(a_) * 64)
        setc(ctx, (1, 1, 1))
        ctx.set_line_width(5)
        ctx.stroke()
    # centre screen with a map route
    rrect(ctx, 880, 1350, 330, 230, 26)
    fill_stroke(ctx, hexc('#0d1424'), CK_HI, 5)
    rrect(ctx, 900, 1368, 290, 194, 16)
    setc(ctx, hexc('#18284a'))
    ctx.fill()
    ctx.move_to(990, 1545)
    ctx.curve_to(1060, 1500, 990, 1450, 1080, 1400)
    ctx.curve_to(1110, 1385, 1120, 1390, 1140, 1380)
    setc(ctx, hexc('#4fa8ff'))
    ctx.set_line_width(7)
    ctx.stroke()
    glow(ctx, 1045, 1465, 160, hexc('#4fa8ff'), 0.12)
    # vents on the right
    for vx in (1360, 1600):
        rrect(ctx, vx - 100, 1360, 200, 110, 24)
        fill_stroke(ctx, hexc('#120f1c'), CK_HI, 4)
        for k in range(4):
            ctx.move_to(vx - 80, 1380 + k * 22)
            ctx.line_to(vx + 80, 1380 + k * 22)
        setc(ctx, CK_MID)
        ctx.set_line_width(6)
        ctx.stroke()
    # red accent knobs + strip
    for kx in (960, 1130):
        ellipse(ctx, kx, 1640, 30, 30)
        fill_stroke(ctx, CK_DARK, CK_RED, 6)
        glow(ctx, kx, 1640, 50, CK_RED, 0.25)
    for i in range(4):
        rrect(ctx, 930 + i * 64, 1720, 44, 14, 7)
        setc(ctx, CK_RED, 0.85)
        ctx.fill()
    # steering wheel (full, on the left)
    ctx.save()
    ctx.translate(wx, wy)
    ctx.rotate(steer * 0.5)
    ellipse(ctx, 0, 0, 330, 310)
    ellipse(ctx, 0, 0, 280, 262)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#14121e'), OUTL, 4)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.arc(0, 0, 305, math.radians(205), math.radians(335))
    setc(ctx, CK_HI)
    ctx.set_line_width(6)
    ctx.stroke()
    for ang in (180, 0, 90):                # spokes: left, right, bottom
        r_ = math.radians(ang)
        ctx.save()
        ctx.rotate(-r_ + math.pi / 2 if ang == 90 else 0)
        if ang == 90:
            poly(ctx, [(-50, 60), (50, 60), (36, 285), (-36, 285)])
        else:
            sx = -1 if ang == 180 else 1
            poly(ctx, [(sx * 60, -40), (sx * 285, -22), (sx * 285, 30), (sx * 60, 50)])
        fill_stroke(ctx, hexc('#1c1929'), OUTL, 3)
        ctx.restore()
    ellipse(ctx, 0, 0, 105, 95)
    fill_stroke(ctx, hexc('#221e33'), CK_HI, 4)
    ellipse(ctx, 0, -4, 34, 30)
    fill_stroke(ctx, hexc('#b8bccb'), OUTL, 3)
    for sx in (-1, 1):
        for k in range(2):
            ellipse(ctx, sx * (150 + k * 50), 5, 14, 14)
            setc(ctx, CK_RED)
            ctx.fill()
    ctx.restore()
    if hands:
        cabin_hands(ctx, steer, sleeve or JACKET)


def cabin_hands(ctx, steer, sleeve):
    """Two hands gripping the rim at 10 and 2 o'clock, forearms in sleeves coming up from the bottom edge."""
    wx, wy = WHEEL_C
    sh = mix(sleeve, (0, 0, 0), 0.25)
    for sg, deg in ((-1, -55), (1, 55)):
        r = math.radians(deg) + steer * 0.5
        hx, hy = wx + math.sin(r) * 318, wy - math.cos(r) * 298
        bx = wx + sg * 330
        # forearm (tapered) + cuff
        nx, ny = hy - (CANVAS + 40), -(hx - bx)
        n = math.hypot(nx, ny) or 1
        nx, ny = nx / n, ny / n
        poly(ctx, [(bx + nx * 95, CANVAS + 40 + ny * 95), (hx + nx * 52, hy + 40 + ny * 52),
                   (hx - nx * 52, hy + 40 - ny * 52), (bx - nx * 95, CANVAS + 40 - ny * 95)])
        fill_stroke(ctx, sleeve, OUTL, 5)
        ctx.move_to(bx - nx * 40, CANVAS + 40 - ny * 40)
        ctx.line_to(hx - nx * 20, hy + 70 - ny * 20)
        setc(ctx, sh)
        ctx.set_line_width(12)
        ctx.stroke()
        ctx.move_to(hx + nx * 56, hy + 58 + ny * 56)
        ctx.line_to(hx - nx * 56, hy + 58 - ny * 56)
        setc(ctx, sh)
        ctx.set_line_width(16)
        ctx.stroke()
        # fist wrapped over the rim
        ctx.save()
        ctx.translate(hx, hy)
        ctx.rotate(r)
        rrect(ctx, -54, -46, 108, 96, 38)
        fill_stroke(ctx, SKIN, OUTL, 5)
        for i in range(3):
            ctx.move_to(-28 + i * 28, -42)
            ctx.line_to(-28 + i * 28, -14)
        setc(ctx, SKIN_SH)
        ctx.set_line_width(4)
        ctx.stroke()
        ellipse(ctx, -sg * 40, 4, 22, 34, 0.3 * sg)          # thumb over the rim
        fill_stroke(ctx, SKIN, OUTL, 4)
        ctx.restore()


def interior_mirror(ctx, w, t, lt, kw):
    """Driver's view of EP.hero (or kw car): road ahead, cockpit, rear-view mirror at the top.
    kw: blink (indicator arrow), mirror (bool), mirror_glow(t)."""
    H = kw.get('car', EP.hero)
    t = t + kw.get('dt', 0.0)
    x, z, h = H.pose(t)
    view = TCam((x - 0.22, 1.2, z - 0.2), h, 0.03, kw.get('f', 820), cx=960, cy=880)
    draw_scene(ctx, view, w, t, ego=False)
    warm_haze(ctx, view, CANVAS)
    sun_flare(ctx, view, CANVAS, CANVAS, 0.8)
    cabin(ctx, H.steer(t), H.speed(t) * 2.237, kw.get('hands', True), kw.get('sleeve'))
    if kw.get('mirror', True):
        mx, my, mw, mh = MIRROR_R
        ctx.move_to(960, 0)
        ctx.line_to(960, my + 10)
        setc(ctx, CK_DARK)
        ctx.set_line_width(26)
        ctx.stroke()
        rrect(ctx, mx, my, mw, mh, 60)
        fill_stroke(ctx, CK_DARK, OUTL, 5)
        ctx.save()
        rrect(ctx, mx + 18, my + 16, mw - 36, mh - 32, 46)
        ctx.clip()
        mc = TCam((x, 1.3, z - 0.6), h + math.pi, 0.03, 560, cx=960, cy=my + mh * 0.55, mirror=True)
        draw_scene(ctx, mc, w, t, ego=False)
        g = cairo.LinearGradient(mx, my, mx + mw, my + mh)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.16)
        g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
        ctx.set_source(g)
        ctx.paint()
        ctx.restore()
        rrect(ctx, mx + 4, my + 4, mw - 8, mh - 8, 56)
        setc(ctx, CK_HI)
        ctx.set_line_width(4)
        ctx.stroke()
        if kw.get('mirror_glow') and kw['mirror_glow'](t):
            rrect(ctx, mx + 18, my + 16, mw - 36, mh - 32, 46)
            setc(ctx, hexc('#ffd23f'))
            ctx.set_line_width(10)
            ctx.stroke()
        if EP.glare(t):
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_ADD)
            glow(ctx, 960, my + mh / 2, 320, (1.0, 0.97, 0.85), 0.25)
            ctx.restore()
    grade(ctx, t, CANVAS, CANVAS, 0.8)
    b = H.blink(t)
    if kw.get('blink') and b in ('L', 'R'):
        s = 1 if b == 'R' else -1
        cx, cy = WHEEL_C[0] + s * 60, 1236
        glow(ctx, cx, cy, 60, hexc('#2bff6a'), 0.6)
        poly(ctx, [(cx + s * 30, cy), (cx - s * 10, cy - 28), (cx - s * 10, cy - 12), (cx - s * 40, cy - 12), (cx - s * 40, cy + 12),
                   (cx - s * 10, cy + 12), (cx - s * 10, cy + 28)])
        setc(ctx, hexc('#2bff6a'))
        ctx.fill()


def dash_face(ctx, w, t, lt, kw):
    """Dashboard camera looking back at the driver of EP.hero (or kw car). kw: who, expr (str or fn(lt)), turn."""
    H = kw.get('car', EP.hero)
    t = t + kw.get('dt', 0.0)
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


def rewind_fx(ctx, lt, d):
    """VHS rewind look: blue tint, scanlines, jitter bars, big REWIND label with double triangles."""
    setc(ctx, hexc('#2a3b8f'), 0.28)
    ctx.paint()
    for y in range(0, CANVAS, 8):
        ctx.rectangle(0, y, CANVAS, 3)
    setc(ctx, (0, 0, 0), 0.18)
    ctx.fill()
    r = random.Random(int(lt * 30))
    for _ in range(3):
        y = r.uniform(0, CANVAS)
        ctx.rectangle(0, y, CANVAS, r.uniform(6, 30))
        setc(ctx, (1, 1, 1), 0.12)
        ctx.fill()
    on = (lt * 2.5) % 1 < 0.7
    if on:
        for k in range(2):
            x0 = 120 + k * 70
            poly(ctx, [(x0, 160), (x0 - 60, 200), (x0, 240)])
            setc(ctx, (1, 1, 1))
            ctx.fill()
        ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(84)
        ctx.move_to(230, 230)
        setc(ctx, (1, 1, 1))
        ctx.show_text('REWIND')


def verdict(kind, text, size=100):
    """Big bottom banner: kind 'x' (red, cross) or 'ok' (green, tick). Text wraps to two lines."""
    col = hexc('#d62f3a') if kind == 'x' else hexc('#1f9d52')

    def fn(ctx, lt, d):
        a = smooth(lt / 0.25)
        sc = 0.85 + 0.15 * smooth(lt / 0.3)
        ctx.save()
        ctx.translate(960, 1700)
        ctx.scale(sc, sc)
        ctx.translate(-960, -1700)
        rrect(ctx, 30, 1480, 1860, 410, 60)
        setc(ctx, col, 0.94 * a)
        ctx.fill_preserve()
        setc(ctx, (1, 1, 1), a)
        ctx.set_line_width(8)
        ctx.stroke()
        ellipse(ctx, 185, 1685, 120, 120)
        setc(ctx, (1, 1, 1), a)
        ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(30)
        setc(ctx, col, a)
        if kind == 'x':
            ctx.move_to(135, 1635)
            ctx.line_to(235, 1735)
            ctx.move_to(235, 1635)
            ctx.line_to(135, 1735)
        else:
            ctx.move_to(125, 1690)
            ctx.line_to(170, 1737)
            ctx.line_to(250, 1633)
        ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(size)
        words, lines, cur = text.split(), [], ''
        for wd in words:
            tr = (cur + ' ' + wd).strip()
            if ctx.text_extents(tr).x_advance > 1500 and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = tr
        lines.append(cur)
        y0 = 1685 - (len(lines) - 1) * size * 0.58 + size * 0.35
        for i, ln in enumerate(lines):
            ctx.move_to(345, y0 + i * size * 1.16)
            setc(ctx, (1, 1, 1), a)
            ctx.show_text(ln)
        ctx.restore()
    return fn


# ------------------------------------------------------------------ 2D close-up scenes
def pedal_close(ctx, w, t, lt, kw):
    """Footwell close-up: gas + brake pedals, the shoe hits kw['act'] ('brake'|'gas') at kw['hit'] (local s)."""
    g = cairo.LinearGradient(0, 0, 0, CANVAS)
    g.add_color_stop_rgb(0, *hexc('#2b2838'))
    g.add_color_stop_rgb(1, *hexc('#14121c'))
    ctx.set_source(g)
    ctx.paint()
    rrect(ctx, -20, 1500, CANVAS + 40, 500, 40)
    setc(ctx, hexc('#1b1925'))
    ctx.fill()
    for i in range(14):
        ctx.move_to(i * 150, 1520)
        ctx.line_to(i * 150 - 80, 1920)
    setc(ctx, hexc('#25222f'))
    ctx.set_line_width(10)
    ctx.stroke()
    hit = kw.get('hit', 0.6)
    act = kw.get('act', 'brake')
    press = smooth((lt - hit + 0.15) / 0.15) if lt > hit - 0.15 else 0.0
    for name, x, wdt, hgt in (('brake', 720, 300, 260), ('gas', 1260, 170, 420)):
        pr = press if name == act else 0.0
        y = 1050 + pr * 70
        ctx.move_to(x, 300)
        ctx.line_to(x, y)
        setc(ctx, hexc('#3b3848'))
        ctx.set_line_width(40)
        ctx.stroke()
        rrect(ctx, x - wdt / 2, y, wdt, hgt * (1 - 0.1 * pr), 40)
        fill_stroke(ctx, hexc('#4a4658'), OUTL, 6)
        for k in range(4):
            ctx.move_to(x - wdt / 2 + 30, y + 40 + k * hgt / 5)
            ctx.line_to(x + wdt / 2 - 30, y + 40 + k * hgt / 5)
        setc(ctx, hexc('#2c2a36'))
        ctx.set_line_width(10)
        ctx.stroke()
    # leg + shoe coming from the top-left
    fx = (720 if act == 'brake' else 1260) - 40
    u = smooth(lt / max(0.2, hit - 0.15)) if lt < hit else 1.0
    sx, sy = 260 + (fx - 260) * u, 640 + (1010 + press * 60 - 640) * u
    poly(ctx, [(-40, -40), (380, -40), (sx + 130, sy - 120), (sx - 120, sy - 90)])
    fill_stroke(ctx, hexc('#3b4a6b'), OUTL, 8)
    ctx.save()
    ctx.translate(sx, sy)
    ctx.rotate(0.35)
    rrect(ctx, -150, -120, 360, 210, 90)
    fill_stroke(ctx, hexc('#7a4a2a'), OUTL, 8)
    rrect(ctx, -150, 60, 360, 40, 18)
    fill_stroke(ctx, hexc('#2a1a10'), OUTL, 6)
    ctx.restore()
    if lt > hit:
        k = 1 - smooth((lt - hit) / 0.5)
        for i in range(10):
            a_ = i * math.pi / 5
            ctx.move_to(fx + math.cos(a_) * 300, 1150 + math.sin(a_) * 300)
            ctx.line_to(fx + math.cos(a_) * (300 + 160 * k), 1150 + math.sin(a_) * (300 + 160 * k))
        setc(ctx, (1, 1, 1), 0.8 * k)
        ctx.set_line_width(14)
        ctx.stroke()
        word = kw.get('word', 'SLAM!' if act == 'brake' else 'FLOOR IT!')
        ctx.save()
        ctx.translate(1180 if act == 'brake' else 640, 520)
        ctx.rotate(-0.12)
        s_ = 1 + 0.4 * k
        ctx.scale(s_, s_)
        outlined_text(ctx, word, 0, 0, 150, hexc('#ffd23f'), lw=26)
        ctx.restore()
    grade(ctx, t, CANVAS, CANVAS, 0.6, grain=0.04)


def horn_close(ctx, w, t, lt, kw):
    """Steering-wheel close-up: a fist slams the horn pad, HONK burst."""
    g = cairo.RadialGradient(960, 960, 100, 960, 960, 1300)
    g.add_color_stop_rgb(0, *hexc('#3a3650'))
    g.add_color_stop_rgb(1, *hexc('#14121c'))
    ctx.set_source(g)
    ctx.paint()
    ellipse(ctx, 960, 1000, 900, 820)
    ellipse(ctx, 960, 1000, 760, 690)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#17151f'), OUTL, 8)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for ang in (180, 0):
        sx = -1 if ang == 180 else 1
        poly(ctx, [(960 + sx * 200, 900), (960 + sx * 780, 930), (960 + sx * 780, 1060), (960 + sx * 200, 1100)])
        fill_stroke(ctx, hexc('#1d1a29'), OUTL, 6)
    hits = kw.get('hits', (0.4, 1.0, 1.4))
    press = max([smooth(1 - abs(lt - h) / 0.12) for h in hits] + [0])
    ellipse(ctx, 960, 1000, 330 - 12 * press, 290 - 12 * press)
    fill_stroke(ctx, hexc('#262236'), hexc('#4d4870'), 8)
    ellipse(ctx, 960, 990, 70, 55)
    fill_stroke(ctx, hexc('#b8bccb'), OUTL, 5)
    fy = 1000 - 260 * (1 - press) - 40
    poly(ctx, [(1500, 1960), (1880, 1960), (1120, fy + 120), (900, fy + 60)])
    fill_stroke(ctx, kw.get('sleeve', JACKET), OUTL, 8)
    rrect(ctx, 760, fy - 150, 400, 300, 120)
    fill_stroke(ctx, SKIN, OUTL, 8)
    for i in range(3):
        ctx.move_to(820 + i * 90, fy - 140)
        ctx.line_to(820 + i * 90, fy - 50)
    setc(ctx, SKIN_SH)
    ctx.set_line_width(8)
    ctx.stroke()
    if press > 0.3:
        for i in range(12):
            a_ = i * math.pi / 6
            ctx.move_to(960 + math.cos(a_) * 520, 900 + math.sin(a_) * 420)
            ctx.line_to(960 + math.cos(a_) * 700, 900 + math.sin(a_) * 560)
        setc(ctx, hexc('#ffd23f'), press)
        ctx.set_line_width(16)
        ctx.stroke()
        ctx.save()
        ctx.translate(960, 330)
        ctx.scale(0.9 + 0.3 * press, 0.9 + 0.3 * press)
        outlined_text(ctx, kw.get('word', 'HONK!'), 0, 0, 190, hexc('#ffd23f'), lw=30)
        ctx.restore()
    grade(ctx, t, CANVAS, CANVAS, 0.6, grain=0.04)


engine.SCENES.update(pedal_close=pedal_close, horn_close=horn_close)


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
        w = s.kw.get('world', self.world)
        tw = EP.tm.wt(t)
        if s.kw.get('rewind'):                 # play world time backwards a -> b over the shot
            a, b = s.kw['rewind']
            u = lt / s.dur
            tw = a + (b - a) * (u * u * (3 - 2 * u))
        engine.SCENES[s.kind](ctx, w, tw, lt, s.kw)
        if s.kw.get('rewind'):
            rewind_fx(ctx, lt, s.dur)
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
    elif len(a) > 3 and a[2] == 'audio':            # remix only: new sound on an already rendered video
        import os
        import subprocess
        wav = a[1] + '.wav'
        engine.write_wav(wav, sound())
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a[3], '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                        '-c:a', 'aac', '-b:a', '256k', '-shortest', a[1]], check=True)
        os.remove(wav)
    elif len(a) > 2 and a[2] == 'still':
        for tt in a[3:]:
            video.render_still(float(tt), a[1].replace('.png', f'_{tt}.png'))
    else:
        out = a[1] if len(a) > 1 else default_out
        video.render(out, sound(), out + '_work')
