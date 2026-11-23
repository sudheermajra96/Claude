"""Make way for the ambulance: one ambulance, two outcomes. Ottawa, Ontario.

World: +Z = north (travel), +X = right. Two northbound lanes: left x = 1.75 (our hero), right x = 5.25; two
southbound lanes at x = -1.75 / -5.25 (always busy, so the ambulance cannot borrow them). Curb at x = 7.0.
Part 1 (WRONG): nobody moves, the ambulance is stuck behind the hero, then he panics and stops IN the lane.
Part 2 (RIGHT): everyone signals, pulls RIGHT and stops (both directions); the ambulance uses the clear left lane,
the hero waits, does not follow it, and merges back. Hospital with an EMERGENCY entrance further up the road.
Every vehicle pair is checked for clearance (verify()) before rendering.
"""
import math
import random

import cairo
import numpy as np

from mkit import *
from truckkit import draw_car_round, wheel3, solid
from peoplekit import *
import citykit
import engine

DUR = 40.0
V = 12.0                     # traffic speed, m/s (43 km/h in a 50 zone)
T_W0, T_W1 = 3.0, 18.5       # wrong part (world segment)
T_RW = 19.7                  # right part starts (after the rewind)
HERO_X_L = 4.3               # where left-lane cars pull to (right side of their lane, into the gaps)
RIGHT_X = 5.95               # right-lane cars pull to the curb
AMB_X = 1.5


def blink_iv(iv):
    b = blinking(iv, 0.8)
    return lambda t: 'R' if b(t) > 0.5 else None


# ------------------------------------------------------------------ vehicles
class Car(Track):
    def __init__(self, x, speed, ta, za, col, occ=None, blink=None):
        super().__init__(x, speed, ta, za, col, blink=blink, t0=-3, t1=45)
        self.occ = occ

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, self.blink(t), self.occ is not None)
            else:
                draw_car_round(ctx, view, x, z, h, self.col, t, self.blink(t), self.brake(t),
                               occ=self.occ(t) if self.occ else None)
        return [((x, 0.8, z), fn)]


def amb3(ctx, view, x, z, h, t, lights=True):
    """Ambulance: cab + patient box, round tyres, red stripe, blue star of life, mirrored AMBULANCE on the front,
    small red/white flashing lights on the box corners."""
    Lf = L(x, z, h)
    white, red = hexc('#f7f7f9'), hexc('#d62828')
    if view.ortho:
        pts = [Lf(-1.2, 0, -3.3), Lf(1.2, 0, -3.3), Lf(1.2, 0, 3.3), Lf(-1.2, 0, 3.3)]
        fill_poly(ctx, view, pts, white, OUTL, 3)
        fill_poly(ctx, view, [Lf(-0.25, 0, -2.2), Lf(0.25, 0, -2.2), Lf(0.25, 0, -0.2), Lf(-0.25, 0, -0.2)], red)
        fill_poly(ctx, view, [Lf(-0.9, 0, -1.45), Lf(0.9, 0, -1.45), Lf(0.9, 0, -0.95), Lf(-0.9, 0, -0.95)], red)
        on = (t * 4) % 1 < 0.5
        if lights:
            p = view.pt(Lf(0, 0, 1.0))
            glow(ctx, p[0], p[1], 2.5 * view.s, (1, 0.15, 0.15) if on else (0.9, 0.9, 1.0), 0.8)
        return
    d = view.depth((x, 1.4, z))
    lw = max(1.4, min(4.0, 70 / max(d, 1)))
    for wz in (-2.0, 2.3):
        for sx in (-1, 1):
            wheel3(ctx, view, Lf(sx * 1.0, 0.42, wz), h, 0.42, 0.3)
    side = mix(white, (0, 0, 0), 0.08)
    # cab
    cb = [(-1.08, 0.4, 1.0), (1.08, 0.4, 1.0), (1.05, 0.4, 3.3), (-1.05, 0.4, 3.3)]
    ct = [(-1.08, 1.25, 1.0), (1.08, 1.25, 1.0), (1.02, 1.15, 3.1), (-1.02, 1.15, 3.1)]
    solid(ctx, view, Lf, cb, ct, {'front': white, 'back': white, 'left': side, 'right': side, 'top': white}, lw)
    gb = [(-1.05, 1.25, 1.0), (1.05, 1.25, 1.0), (1.0, 1.2, 2.45), (-1.0, 1.2, 2.45)]
    gt = [(-1.0, 2.25, 1.0), (1.0, 2.25, 1.0), (0.95, 2.2, 1.7), (-0.95, 2.2, 1.7)]
    glass = hexc('#2a3448')
    cv = solid(ctx, view, Lf, gb, gt, {'front': glass, 'back': white, 'left': glass, 'right': glass, 'top': white}, lw)
    # patient box
    vis = lbox(ctx, view, Lf, h, -1.2, 1.2, 0.45, 2.95, -3.3, 1.0,
               {'front': white, 'back': white, 'left': side, 'right': side, 'top': hexc('#e4e4ea')}, lw)
    for face, dx in (('left', -1.205), ('right', 1.205)):
        if face in vis:
            face_rect(ctx, view, Lf, face, -3.25, 0.95, 1.05, 1.35, dx, red)
            face_rect(ctx, view, Lf, face, -3.25, 0.95, 2.45, 2.6, dx, red)
            star_of_life(ctx, view, Lf(dx * 1.002, 1.9, -1.2), view.scale(Lf(dx, 1.9, -1.2)))
    if 'back' in vis:
        face_rect(ctx, view, Lf, 'back', -1.15, 1.15, 1.05, 1.35, -3.305, red)
        for sx in (-1, 1):
            face_rect(ctx, view, Lf, 'back', sx * 0.55 - 0.4, sx * 0.55 + 0.4, 1.6, 2.4, -3.31, hexc('#2d3f55'))
            face_rect(ctx, view, Lf, 'back', sx * 1.0 - 0.12, sx * 1.0 + 0.12, 0.6, 0.85, -3.31, hexc('#b01818'))
        star_of_life(ctx, view, Lf(0, 2.65, -3.32), view.scale(Lf(0, 2.65, -3.32)) * 0.45)
    if 'front' in vis:
        face_rect(ctx, view, Lf, 'front', -1.15, 1.15, 2.3, 2.9, 1.005, white)
        c, s = view.pt(Lf(0, 2.6, 1.01)), view.scale(Lf(0, 2.6, 1.01))
        if c and s and s > 8:
            ctx.save()
            ctx.translate(*c)
            ctx.scale(-1, 1)                     # mirrored so it reads right in a mirror
            text_center(ctx, 'AMBULANCE', 0, 0.14 * s, 0.38 * s, red)
            ctx.restore()
    if 'front' in cv or True:
        for sx in (-1, 1):
            face_rect(ctx, view, Lf, 'front', sx * 0.72 - 0.2, sx * 0.72 + 0.2, 0.72, 0.9, 3.31, hexc('#fff6d8'), WHITE_L, 0.4)
    # small flashing lights on the box corners and the cab roof
    if lights:
        ph = (t * 3.0) % 1
        for k, (lx, ly, lz) in enumerate(((-1.12, 2.98, 0.95), (1.12, 2.98, 0.95), (-1.12, 2.98, -3.25), (1.12, 2.98, -3.25),
                                          (-0.45, 2.3, 1.55), (0.45, 2.3, 1.55))):
            on = (ph < 0.5) == (k % 2 == 0)
            col = (1.0, 0.12, 0.12) if (k % 2 == 0) else (0.95, 0.95, 1.0)
            P = Lf(lx, ly, lz)
            p, s = view.pt(P), view.scale(P)
            if not p or not s:
                continue
            rrect(ctx, p[0] - 0.12 * s, p[1] - 0.07 * s, 0.24 * s, 0.14 * s, 0.04 * s)
            fill_stroke(ctx, col if on else mix(col, (0, 0, 0), 0.55), OUTL, max(1, lw * 0.5))
            if on:
                glow(ctx, p[0], p[1], min(0.9 * s, 160), col, 0.7)


def star_of_life(ctx, view, P, s):
    p = view.pt(P)
    if not p or not s or s < 4:
        return
    r = 0.42 * s
    ctx.save()
    ctx.translate(*p)
    for k in range(3):
        ctx.save()
        ctx.rotate(k * math.pi / 3)
        ctx.rectangle(-0.18 * r, -r, 0.36 * r, 2 * r)
        setc(ctx, hexc('#1f5fbf'))
        ctx.fill()
        ctx.restore()
    ctx.move_to(0, -0.7 * r)
    ctx.line_to(0, 0.7 * r)
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(max(1, 0.06 * r))
    ctx.stroke()
    ctx.restore()


class Amb(Track):
    def __init__(self, x, speed, ta, za):
        super().__init__(x, speed, ta, za, '#f7f7f9', t0=-3, t1=45)

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        return [((x, 1.4, z - 1.0), lambda: amb3(ctx, view, x, z, h, t))]


class Rev:
    """Southbound car (travels -z); optional pull-right (to more negative x) and stop."""

    def __init__(self, x, z0, col, t0=None, xr=None, ts=None):
        self.x0, self.z0, self.col = x, z0, col
        self.t0, self.xr, self.ts = t0, xr, ts       # stop: start time, pulled x, stop duration

    def zt(self, t):
        if self.t0 is None or t < self.t0:
            return self.z0 - V * t
        u = t - self.t0
        dec = 1.6
        if u < dec:
            return self.z0 - V * self.t0 - V * (u - u * u / (2 * dec))
        return self.z0 - V * self.t0 - V * dec / 2

    def pose(self, t):
        x = self.x0
        if self.t0 is not None and t > self.t0:
            x = self.x0 + (self.xr - self.x0) * smooth((t - self.t0) / 1.2)
        z = self.zt(t)
        dx = (self.xr - self.x0) * 0.6 if (self.t0 is not None and self.t0 < t < self.t0 + 1.2) else 0.0
        return x, z, math.pi + math.atan2(-dx, V) * 0.3

    def speed(self, t):
        return V

    def steer(self, t):
        return 0.0

    def blink(self, t):
        return None

    def brake(self, t):
        return 1.0 if (self.t0 is not None and t > self.t0) else 0.0

    def visible(self, t):
        return True


# ------------------------------------------------------------------ hero look + occupants
LOOK = Key([(0, 0), (12.7, 0), (12.9, 0.35), (13.5, 0.35), (13.7, 0), (19.9, 0), (20.1, 0.4), (21.0, 0.4), (21.2, 0),
            (29.6, 0), (29.8, 0.35), (30.4, 0.35), (30.6, 0), (99, 0)])


def hero_occ(t):
    def fn(ctx, view, Lf, h):
        person3d(ctx, view, Lf, -0.38, 0.05, 'hero', LOOK(t), 'shock' if 12.8 < t < 15.5 else 'calm')
    return fn


# ---------------- PART 1 (wrong): anchors z = 0 at T_W0 for the hero
HERO_W = Car(1.75, Key([(0, V), (13.0, V), (14.6, 0), (99, 0)], 'lin'), T_W0, 0.0, '#e23b3b', hero_occ)
AMB_W = Amb(AMB_X + 0.25, Key([(0, 20), (6.9, 20), (7.9, V), (13.25, V), (14.9, 0), (99, 0)], 'lin'), T_W0, -46.0)
TRAF_W = [Car(1.75, const(V), T_W0, 20.0 + 18 * i, c) for i, c in enumerate(['#3a7bd5', '#c9c9d6', '#37b26c'])]
TRAF_W = TRAF_W
TRAF_W += [Car(5.25, const(V), T_W0, -30 + 16 * i, c) for i, c in
           enumerate(['#f2a541', '#f4f4f6', '#7a4fd0', '#1c1c22', '#2f6f73', '#c9c9d6', '#e05d5d', '#3a7bd5', '#d8c3a0'])]
_OC = ['#3a7bd5', '#f2a541', '#c9c9d6', '#37b26c', '#1c1c22', '#7a4fd0', '#2f6f73', '#f4f4f6', '#e05d5d', '#d8c3a0']
ONC_W = [Rev(-1.75 if i % 2 else -5.25, -40 + i * 11 + (3 if i % 3 == 0 else 0), _OC[(i * 3) % 10]) for i in range(64)]

# ---------------- PART 2 (right): anchors z = 0 at T_RW for the hero
T_SIG, T_PULL, T_STOP = 20.6, 22.3, 24.1
AMB_SPD = Key([(0, 18), (23.6, 18), (24.6, 12), (27.6, 12), (29.0, 15), (31.2, 15), (33.4, 0), (99, 0)], 'lin')
_amb0 = Amb(const(AMB_X), AMB_SPD, T_RW, -40.0)
Z_STOP = V * (T_PULL - T_RW) + V * (T_STOP - T_PULL) / 2          # hero's stop z (anchor 0)
LEFT_AHEAD, RIGHT_OFFS = [16.0], [-24.0, -8.0, 8.0, 24.0]
_front = Z_STOP + max(LEFT_AHEAD + RIGHT_OFFS)
T_LAST = next(t for t in np.arange(T_RW, DUR, 0.01) if _amb0.z(t) - 3.3 > _front + 2.2 + 1.0)
T_GO = max(27.3, round(T_LAST + 0.8, 2))                           # everyone waits until it has passed
T_BACK = T_GO + 3.2
T_AMB_LANE = round(T_LAST + 0.6, 2)                                # ambulance returns right only past everybody
S_STOP = Key([(0, V), (T_PULL, V), (T_STOP, 0), (T_GO, 0), (T_GO + 2.6, V), (99, V)], 'lin')
HERO_R = Car(Key([(0, 1.75), (T_PULL, 1.75), (T_PULL + 1.3, HERO_X_L), (T_BACK, HERO_X_L), (T_BACK + 1.3, 1.75), (99, 1.75)]),
             S_STOP, T_RW, 0.0, '#e23b3b', hero_occ,
             blink=blink_iv([(T_SIG, T_PULL + 1.4), (T_BACK - 1.0, T_BACK + 1.2)]))
TRAF_R = [Car(Key([(0, 1.75), (T_PULL, 1.75), (T_PULL + 1.3, HERO_X_L), (T_BACK - 0.3, HERO_X_L), (T_BACK + 1.0, 1.75), (99, 1.75)]),
              S_STOP, T_RW, dz, c, blink=blink_iv([(T_SIG + 0.3, T_PULL + 1.4)])) for dz, c in zip(LEFT_AHEAD, ['#3a7bd5'])]
TRAF_R += [Car(Key([(0, 5.25), (T_PULL, 5.25), (T_PULL + 1.2, RIGHT_X), (99, RIGHT_X)]), S_STOP, T_RW, dz, c,
               blink=blink_iv([(T_SIG + 0.2, T_PULL + 1.3)]))
           for dz, c in zip(RIGHT_OFFS, ['#f2a541', '#f4f4f6', '#7a4fd0', '#1c1c22'])]
ONC_R = [Rev(o.x0, o.z0, o.col, t0=T_PULL + 0.4 + 0.02 * i, xr=(-2.45 if o.x0 > -3 else -5.95)) for i, o in enumerate(ONC_W)]
AMB_R = Amb(Key([(0, AMB_X), (T_AMB_LANE, AMB_X), (T_AMB_LANE + 1.6, 5.0), (31.9, 5.0), (33.4, 8.6), (99, 8.6)]), AMB_SPD, T_RW, -40.0)
HOSP_Z = AMB_R.z(33.4) + 0.0


# ------------------------------------------------------------------ Ottawa street + hospital
def ottawa_sky(ctx, view):
    if view.ortho:
        return
    towers(ctx, view, 1500, -500, 400, 22, 40, 120, seed=21, base='#9fb0c2', haze='#dceefa')
    X, Z = -60.0, 1350.0
    b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
    if not b or not s:
        return
    stone, copper = mix(hexc('#cdbf9c'), hexc('#dceefa'), 0.25), mix(hexc('#5fa38a'), hexc('#dceefa'), 0.25)
    # Centre Block + Peace Tower
    ctx.rectangle(b[0] - 70 * s, b[1] - 32 * s, 140 * s, 32 * s)
    setc(ctx, stone)
    ctx.fill()
    for k in range(-3, 4):
        if k == 0:
            continue
        cx = b[0] + k * 20 * s
        poly(ctx, [(cx - 8 * s, b[1] - 32 * s), (cx + 8 * s, b[1] - 32 * s), (cx, b[1] - 44 * s)])
        setc(ctx, copper)
        ctx.fill()
    ctx.rectangle(b[0] - 7 * s, b[1] - 82 * s, 14 * s, 82 * s)
    setc(ctx, stone)
    ctx.fill()
    ellipse(ctx, b[0], b[1] - 70 * s, 4 * s, 4 * s)
    setc(ctx, mix(hexc('#f4f2ec'), hexc('#dceefa'), 0.2))
    ctx.fill()
    poly(ctx, [(b[0] - 8 * s, b[1] - 82 * s), (b[0] + 8 * s, b[1] - 82 * s), (b[0], b[1] - 102 * s)])
    setc(ctx, copper)
    ctx.fill()


def hospital(ctx, view, z0):
    x0, x1, z1 = 13.0, 32.0, z0 + 40.0
    building(ctx, view, x0, x1, z0 - 10, z1, 16.0, '#e8e3da', win='#5b8fb3')
    if view.ortho:
        return
    # canopy over the emergency entrance + red sign + sliding doors
    Lf = lambda a, b, c: (a, b, c)
    face_rect(ctx, view, Lf, 'right', z0 + 4, z0 + 14, 0.0, 3.0, x0 - 0.02, hexc('#9cc6e0'))
    face_rect(ctx, view, Lf, 'right', z0 + 8.9, z0 + 9.1, 0.0, 3.0, x0 - 0.03, OUTL)
    face_rect(ctx, view, Lf, 'right', z0 + 3, z0 + 15, 4.0, 5.6, x0 - 0.03, hexc('#d62828'))
    c, s = view.pt((x0 - 0.05, 4.8, z0 + 9)), view.scale((x0 - 0.05, 4.8, z0 + 9))
    pa, pb = view.pt((x0 - 0.05, 4.8, z0 + 3.5)), view.pt((x0 - 0.05, 4.8, z0 + 14.5))
    if c and s and pa and pb and s > 3:
        ang = math.atan2(pb[1] - pa[1], pb[0] - pa[0])
        if abs(ang) > math.pi / 2:
            ang += math.pi
        w = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
        ctx.save()
        ctx.translate(*c)
        ctx.rotate(ang)
        ctx.scale(1, min(1.0, s * 1.4 / max(w / 7, 1)))
        text_center(ctx, 'EMERGENCY', 0, 0.45 * s, min(1.1 * s, w / 6.5), (1, 1, 1))
        ctx.restore()
    fill_poly(ctx, view, [(x0, 3.4, z0 + 2), (x0, 3.4, z0 + 16), (8.0, 3.4, z0 + 16), (8.0, 3.4, z0 + 2)], hexc('#d9d4ca'), OUTL, 2)
    for zz in (z0 + 2.3, z0 + 15.7):
        a, b = view.pt((8.3, 0, zz)), view.pt((8.3, 3.4, zz))
        if a and b:
            ctx.move_to(*a)
            ctx.line_to(*b)
            setc(ctx, OUTL)
            ctx.set_line_width(max(2, (view.scale((8.3, 1, zz)) or 10) * 0.15))
            ctx.stroke()


class OttawaStreet(Street):
    def __init__(self):
        super().__init__('city', n=2, median='yellow', sidewalk=True, seed=41, hmin=10, hmax=30, setback=1.0,
                         sky=('#5fb4f2', '#e2f3ff'), skyline=ottawa_sky,
                         palette=['#c9b9a6', '#a9b8c6', '#d8cfc0', '#8f9aa8', '#b7a28a', '#9fb3a0', '#c98b6b'])
        self.items = [it for it in self.items if not (it[0] == 'bld' and it[1][0] > 0 and HOSP_Z - 40 < it[1][3] and it[1][2] < HOSP_Z + 60)]

    def ground(self, ctx, view, t):
        super().ground(ctx, view, t)
        gquad(ctx, view, self.R, 13.0, HOSP_Z - 13, HOSP_Z + 8, C_ASPH, 0.005)      # ambulance bay driveway

    def objects(self, ctx, view, t):
        out = super().objects(ctx, view, t)
        out.append(((22.0, 8.0, HOSP_Z + 10), lambda: hospital(ctx, view, HOSP_Z - 9.0)))
        return out


DAUGHTER = Ped(const(12.2), const(HOSP_Z + 6.5), top='#7a4fd0', pants='#2b3a63', skin='#e8b48f', hair='#2a1a14')
world = SegWorld(DUR, [(0, T_W1 + 1.2, HERO_W, [AMB_W] + TRAF_W + ONC_W, [DAUGHTER]),
                       (T_W1 + 1.2, 99, HERO_R, [AMB_R] + TRAF_R + ONC_R, [DAUGHTER])], OttawaStreet(), 'kmh')


# ------------------------------------------------------------------ heart rate (story) + ECG
def hr_at(t):
    if t < T_W0:
        return 128.0
    if t < T_W1 + 1.2:
        return 128 + 18 * smooth((t - 9.0) / 4.0)
    return 124 - 26 * smooth((t - 26.0) / 4.0)


_g = np.arange(0, DUR + 1, 0.002)
_ph = np.cumsum([hr_at(t) / 60 * 0.002 for t in _g])
BEATS = [float(np.interp(k, _ph, _g)) for k in range(1, int(_ph[-1]))]


def ecg_val(t):
    """ECG-ish value at time t (0 baseline, 1 = R peak)."""
    i = np.searchsorted(BEATS, t) - 1
    if i < 0:
        return 0.0
    u = t - BEATS[i]
    v = 0.12 * math.exp(-((u - 0.0) / 0.03) ** 2) * 0       # (P wave folded into previous beat)
    v += 1.0 * math.exp(-((u - 0.06) / 0.012) ** 2) - 0.25 * math.exp(-((u - 0.085) / 0.012) ** 2)
    v += 0.25 * math.exp(-((u - 0.28) / 0.05) ** 2)
    v += 0.1 * math.exp(-((u + 0.12) / 0.03) ** 2)
    return v


def amb_in(ctx, w, t, lt, kw):
    """Inside the ambulance: grandpa on the stretcher (oxygen mask), the paramedic watching the monitor."""
    critical = kw.get('critical', True)
    sway = math.sin(t * 2.3) * 6
    ctx.save()
    ctx.translate(sway, math.sin(t * 3.1) * 3)
    setc(ctx, hexc('#eef1f4'))
    ctx.paint()
    # rear door windows (left) with the road behind and flashing light spill
    for wx in (40, 250):
        rrect(ctx, wx, 120, 170, 300, 20)
        ctx.save()
        ctx.clip_preserve()
        g = cairo.LinearGradient(0, 120, 0, 420)
        g.add_color_stop_rgb(0, *hexc('#7fbfee'))
        g.add_color_stop_rgb(1, *hexc('#dff1ff'))
        ctx.set_source(g)
        ctx.fill_preserve()
        poly(ctx, [(wx - 10, 430), (wx + 190, 430), (wx + 110, 300), (wx + 70, 300)])
        setc(ctx, C_ASPH)
        ctx.fill()
        ctx.restore()
        rrect(ctx, wx, 120, 170, 300, 20)
        setc(ctx, OUTL)
        ctx.set_line_width(6)
        ctx.stroke()
    # cabinets
    for k in range(4):
        rrect(ctx, 520 + k * 230, 40, 215, 170, 14)
        fill_stroke(ctx, hexc('#c9d3de'), OUTL, 4)
        rrect(ctx, 600 + k * 230, 170, 60, 14, 6)
        setc(ctx, hexc('#8a96a6'))
        ctx.fill()
    # monitor
    mx0, my0, mw, mh = 1420, 150, 440, 300
    rrect(ctx, mx0 - 16, my0 - 16, mw + 32, mh + 32, 24)
    fill_stroke(ctx, hexc('#3a3d48'), OUTL, 5)
    ctx.rectangle(mx0, my0, mw, mh)
    setc(ctx, hexc('#0b1410'))
    ctx.fill()
    hr = hr_at(t)
    col = hexc('#ff4b4b') if critical else hexc('#3cff7a')
    ctx.save()
    ctx.rectangle(mx0, my0, mw, mh)
    ctx.clip()
    span = 3.0
    pts = []
    for i in range(160):
        tt = t - span + span * i / 159
        pts.append((mx0 + 10 + (mw - 140) * i / 159, my0 + 190 - 120 * ecg_val(tt)))
    poly_open = pts
    ctx.move_to(*poly_open[0])
    for p in poly_open[1:]:
        ctx.line_to(*p)
    setc(ctx, col)
    ctx.set_line_width(5)
    ctx.stroke()
    glow(ctx, pts[-1][0], pts[-1][1], 30, col, 0.8)
    ctx.restore()
    text_center(ctx, 'HR', mx0 + mw - 65, my0 + 60, 32, col)
    text_center(ctx, f'{int(round(hr))}', mx0 + mw - 65, my0 + 140, 76, col)
    if critical and (t * 2) % 1 < 0.5:
        rrect(ctx, mx0 + 12, my0 + 12, 170, 50, 10)
        setc(ctx, hexc('#ff4b4b'))
        ctx.fill()
        text_center(ctx, 'ALARM', mx0 + 97, my0 + 50, 34, (1, 1, 1))
    # paramedic (behind the stretcher), looking at the monitor
    head2d(ctx, 1170, 430, 120, 'medic', kw.get('medic', 'worried'), 0.55, t)
    # stretcher + grandpa lying down (head on the left, face up), oxygen mask, blanket
    rrect(ctx, 330, 760, 1260, 60, 20)
    fill_stroke(ctx, hexc('#8a96a6'), OUTL, 5)
    for wx in (420, 1500):
        ctx.move_to(wx, 820)
        ctx.line_to(wx, 980)
        setc(ctx, OUTL)
        ctx.set_line_width(14)
        ctx.stroke()
        ellipse(ctx, wx, 1000, 34, 34)
        fill_stroke(ctx, hexc('#2a2a33'), OUTL, 4)
    rrect(ctx, 350, 660, 300, 110, 50)
    fill_stroke(ctx, (1, 1, 1), OUTL, 5)
    head2d(ctx, 560, 640, 120, 'grandpa', 'closed', 0.0, t, -math.pi / 2)
    ctx.save()                                  # oxygen mask over nose + mouth (rotated with the head)
    ctx.translate(560, 640)
    ctx.rotate(-math.pi / 2)
    ellipse(ctx, 0, 0.47 * 120, 0.26 * 120, 0.2 * 120)
    fill_stroke(ctx, hexc('#bfe8d0'), OUTL, 4, 0.75)
    ctx.restore()
    ctx.move_to(560 - 50, 640 - 30)
    ctx.curve_to(400, 520, 300, 470, 260, 440)
    setc(ctx, hexc('#9fd6bb'))
    ctx.set_line_width(9)
    ctx.stroke()
    breathe = 6 * math.sin(t * 2 * math.pi * 0.3)
    ctx.move_to(690, 770)
    ctx.curve_to(700, 620 - breathe, 900, 600 - breathe, 1200, 640)
    ctx.curve_to(1400, 660, 1580, 680, 1590, 770)
    ctx.close_path()
    fill_stroke(ctx, hexc('#6fa8dc'), OUTL, 5)
    # red light spill from the flashing lights outside
    a = 0.06 + 0.06 * (1 if (t * 3) % 1 < 0.5 else 0)
    setc(ctx, (1, 0.2, 0.2), a)
    ctx.paint()
    ctx.restore()


def hero_win(ctx, w, t, lt, kw):
    """Hero through his driver window (seen from the right lane): music on, whistling, no idea."""
    WIN = [(240, 770), (1730, 770), (1730, 190), (600, 150)]
    ctx.save()
    opening = lambda: (ctx.move_to(*WIN[0]), [ctx.line_to(*p) for p in WIN[1:]], ctx.close_path())
    opening()
    ctx.clip()
    setc(ctx, hexc('#2c2d38'))
    ctx.paint()
    g = cairo.LinearGradient(0, 200, 0, 560)
    g.add_color_stop_rgb(0, *hexc('#5fb4f2'))
    g.add_color_stop_rgb(1, *hexc('#e2f3ff'))
    ctx.set_source(g)
    ctx.rectangle(560, 200, 1200, 360)
    ctx.fill()
    off = (t * 380) % 330
    for k in range(-1, 6):
        px = 560 + k * 330 + off
        ctx.rectangle(px, 300 - 60 * (k % 2), 300, 400)
        fill_stroke(ctx, hexc(['#c9b9a6', '#a9b8c6', '#d8cfc0', '#9fb3a0'][k % 4]), OUTL, 3)
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
    head2d(ctx, 900, 480, 175, 'hero', 'whistle', -0.35, t)
    # glowing car stereo on the dash with a loud volume bar
    rrect(ctx, 260, 600, 220, 90, 14)
    fill_stroke(ctx, hexc('#111111'), OUTL, 4)
    vol = 0.85 + 0.15 * math.sin(t * 9)
    for k in range(10):
        if k / 10 < vol:
            ctx.rectangle(275 + k * 19, 670 - k * 5, 13, 10 + k * 5)
            setc(ctx, hexc('#3cff7a') if k < 7 else hexc('#ff4b4b'))
            ctx.fill()
    setc(ctx, (0.75, 0.88, 1.0), 0.1)
    ctx.paint()
    ctx.restore()
    body = hexc('#e23b3b')
    ctx.rectangle(-40, -40, SW + 80, SH + 80)
    opening()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    setc(ctx, body)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.rectangle(-40, -40, SW + 80, 130)
    setc(ctx, mix(body, (0, 0, 0), 0.15))
    ctx.fill()
    opening()
    setc(ctx, hexc('#15151c'))
    ctx.set_line_width(22)
    ctx.stroke()
    rrect(ctx, 1450, 850, 170, 40, 18)
    fill_stroke(ctx, mix(body, (0, 0, 0), 0.25), OUTL, 4)


def hosp_face(ctx, w, t, lt, kw):
    """The granddaughter waiting at the emergency entrance."""
    setc(ctx, hexc('#e8e3da'))
    ctx.paint()
    ctx.rectangle(0, 0, SW, 150)
    setc(ctx, hexc('#d62828'))
    ctx.fill()
    text_center(ctx, 'EMERGENCY', 960, 110, 92, (1, 1, 1))
    for k, x0 in enumerate((260, 980)):
        ctx.rectangle(x0, 220, 680, 860)
        fill_stroke(ctx, hexc('#9cc6e0'), OUTL, 6)
        ctx.rectangle(x0 + 40, 260, 600, 760)
        setc(ctx, hexc('#b8d8ec'))
        ctx.fill()
    ctx.rectangle(950, 220, 30, 860)
    setc(ctx, OUTL)
    ctx.fill()
    expr = kw.get('expr', 'worried')
    head2d(ctx, 960, 560, 200, 'daughter', expr, 0.0, t)
    if kw.get('tear'):
        ty = 600 + (lt * 60) % 120
        ctx.move_to(960 - 70, ty - 30)
        ctx.curve_to(960 - 50, ty, 960 - 50, ty + 20, 960 - 70, ty + 20)
        ctx.curve_to(960 - 90, ty + 20, 960 - 90, ty, 960 - 70, ty - 30)
        fill_stroke(ctx, hexc('#8fd6ff'), OUTL, 3)
    if kw.get('lights'):
        a = 0.12 if (t * 3) % 1 < 0.5 else 0.0
        setc(ctx, (1, 0.2, 0.2), a)
        ctx.paint()


engine.SCENES.update(amb_in=amb_in, hero_win=hero_win, hosp_face=hosp_face)


# ------------------------------------------------------------------ cameras
def amb_follow(ctx, w, t, lt, kw):
    a = AMB_W if t < T_W1 + 1.2 else AMB_R
    x, z, h = a.pose(t)
    off = kw.get('off', (0.0, 6.5, -16.0))
    view = look_at((x + off[0], off[1], z + off[2]), (x + kw.get('lx', 0.6), 1.2, z + kw.get('lz', 14.0)), kw.get('f', 1000))
    draw_scene(ctx, view, w, t)
    if kw.get('post'):
        kw['post'](ctx, view, t, lt)


def rear_mirror(ctx, w, t, lt, kw):
    """Driver's seat: road ahead + the rear-view mirror (hanging from the windshield) showing what is behind."""
    e = w.ego(t)
    x, z, h = e.pose(t)
    draw_scene(ctx, ego_cam(w, t, 'inside'), w, t, ego=False)
    citykit.cockpit(ctx, w, t)
    ctx.move_to(960, -10)
    ctx.line_to(960, 70)
    setc(ctx, hexc('#2a2a36'))
    ctx.set_line_width(26)
    ctx.stroke()
    rrect(ctx, 520, 60, 880, 330, 60)
    fill_stroke(ctx, hexc('#2a2a36'), OUTL, 6)
    ctx.save()
    rrect(ctx, 548, 86, 824, 278, 44)
    ctx.clip()
    mc = TCam((x, 1.3, z - 0.4), h + math.pi, 0.02, 880, cx=960, cy=225, mirror=True)
    draw_scene(ctx, mc, w, t, ego=False)
    g = cairo.LinearGradient(548, 86, 1372, 364)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.12)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    rrect(ctx, 548, 86, 824, 278, 44)
    setc(ctx, OUTL)
    ctx.set_line_width(5)
    ctx.stroke()
    hud(ctx, w, t)


engine.SCENES.update(amb_follow=amb_follow, rear_mirror=rear_mirror)

HOSP_CAM = dict(cam='fixed', pos=(1.5, 2.1, HOSP_Z - 13), target=(9.5, 1.6, HOSP_Z + 1), f=900, hud=False)
TOP = dict(horizontal=True, xc=0.0, ahead=6.0, scale=26.0)
defs = [
    (3.0, 'amb_in', dict(critical=True, medic='worried')),
    (5.5, 'amb_follow', dict()),
    (7.8, 'hero_win', dict()),
    (10.3, 'amb_follow', dict(off=(1.0, 11.0, -13.0), lx=0.3, lz=12.0, f=950)),
    (12.8, 'amb_in', dict(critical=True, medic='worried')),
    (13.9, 'rear_mirror', dict()),
    (16.0, 'm_cam', dict(cam='high')),
    (18.5, 'hosp_face', dict(expr='worried')),
    (19.7, 'rewind_seq', dict()),
    (22.2, 'rear_mirror', dict()),
    (25.2, 'm_cam', dict(cam='high')),
    (27.7, 'm_top', dict(TOP)),
    (30.2, 'amb_in', dict(critical=False, medic='calm')),
    (32.7, 'm_cam', dict(cam='chase')),
    (34.6, 'm_cam', dict(HOSP_CAM)),
    (36.4, 'hosp_face', dict(expr='relieved', tear=True, lights=True)),
    (DUR, 'm_cam', dict(HOSP_CAM)),
]
shots = build_shots(defs)
shots[8].kw.update(srcs=list(reversed(shots[1:8])), dur=shots[8].dur)
video = Video(['An ambulance is behind you.', 'Do you MOVE?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('A life is inside this ambulance', 975, 80, hexc('#ffd23f'), 0.2, True)),
    (3.0, 5.5, location_tag('Ottawa, Ontario')),
    (3.2, 5.5, caption('Siren behind you. What do you do?')),
    (S[2], E[6], badge('WHEN NOBODY MOVES', '#e0393e')),
    (S[2] + 0.2, E[2], caption('Music up... he hears nothing')),
    (S[3] + 0.2, E[3], caption('Stuck. Nowhere to go.')),
    (S[4] + 0.2, E[4], caption('Every second counts...')),
    (S[6] + 0.2, E[6], caption('Panic! He stops IN the lane')),
    (S[7] + 0.2, E[7], caption('Her grandpa is still on the way...')),
    (S[11], E[12], badge('WHEN EVERYONE MOVES', '#22a356')),
    (S[14], E[14], badge('WHEN EVERYONE MOVES', '#22a356')),
    (S[16] + 0.2, E[16], end_card('Move RIGHT. STOP. Let it pass.', 'Would YOU make way? Comment YES')),
]
for n, (i, txt) in enumerate(((9, 'Check mirrors. Signal right.'), (10, 'Pull RIGHT and STOP'),
                              (13, "Merge back. Don't follow it.")), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays += [
    (S[11] + 0.2, E[11], caption('Both directions pull over')),
    (S[12] + 0.2, E[12], caption('Minutes saved. Heart rate easing.')),
    (S[14] + 0.2, E[14], caption('Arrived. Right on time.')),
    (S[15] + 0.2, E[15], caption('Thank you for moving over')),
]


# ------------------------------------------------------------------ sound
def beep(f=1000, d=0.07):
    tt = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * f * tt) * env_adsr(len(tt), 0.004, 0.02) * 0.5


def alarm(d):
    tt = np.arange(int(d * SR)) / SR
    gate = ((tt * 2.5) % 1 < 0.35).astype(float)
    return np.sin(2 * np.pi * 880 * tt) * gate * 0.35


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur, 1.0), 0, 0.18)
    inside = [(S[0], E[0]), (S[4], E[4]), (S[12], E[12])]
    for b in BEATS:
        if any(a <= b < c for a, c in inside):
            m.add(beep(1000 if b < T_W1 + 1.2 else 880), b, 0.55)
        elif any(a <= b < c for a, c in ((S[7], E[7]), (S[15], E[15]))):
            pass
    m.add(alarm(E[4] - S[4] - 0.6), S[4] + 0.6, 0.35)
    # sirens (muffled inside the ambulance)
    m.add(lp(ambulance_siren(3.0), 900), 0, 0.5)
    m.add(ambulance_siren(E[7] - S[1]), S[1], 0.9)
    m.add(lp(ambulance_siren(E[4] - S[4]), 900), S[4], 0.1)
    m.add(heartbeat(3, 120), 0.1, 0.8)
    m.add(horn(0.6), S[3] + 1.2, 0.35, -0.2)
    m.add(screech(1.1, 1200), 13.0, 0.6)
    m.add(brake_squeal(1.0), 13.3, 0.5)
    m.add(sad_violin(), S[7] + 0.4, 0.9)
    m.add(rewind_sfx(1.2), S[8], 1.0)
    m.add(ambulance_siren(E[13] - S[9], [1.0] * 8 + [0.95] * 2), S[9], 0.9)
    m.add(click(), T_SIG, 0.7)
    indicator(m, T_SIG, T_PULL + 1.4, 0.45, 0.2)
    m.add(brake_squeal(1.0), T_STOP - 1.0, 0.25)
    m.add(car_pass(1.8, 0.5, 100), 25.6, 0.9, np.linspace(-0.6, 0.4, int(1.8 * SR)))
    for i in (9, 10, 13):
        m.add(pop(), S[i] + 0.15, 0.7)
    indicator(m, T_BACK - 1.0, T_BACK + 1.2, 0.4, -0.2)
    m.add(chime(), S[14] + 0.3, 0.7)
    m.add(success_jingle(), S[16] + 0.3, 0.8)
    return m.out(video.dur)


# ------------------------------------------------------------------ checks
def gaps(agents, t0, t1, w_of):
    worst = (99, None)
    for t in np.arange(t0, t1, 0.05):
        P = [(a.pose(t), w_of(a), i) for i, a in enumerate(agents)]
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                (x1, z1, _), (w1, l1), _ = P[i]
                (x2, z2, _), (w2, l2), _ = P[j]
                lat = abs(x1 - x2) - (w1 + w2) / 2
                lon = abs(z1 - z2) - (l1 + l2) / 2
                if lat < 0.25 and lon < worst[0]:
                    worst = (round(lon, 2), (round(t, 2), i, j, round(lat, 2)))
    return worst


def verify():
    dims = lambda a: (2.4, 6.6) if isinstance(a, Amb) else (1.84, 4.4)
    print('WRONG part: smallest bumper gap between lane-sharing vehicles:', gaps([HERO_W, AMB_W] + TRAF_W, T_W0, T_W1 + 1.2, dims))
    print('   ambulance-hero gap at 10, 14, 16 s:', [round(HERO_W.z(t) - AMB_W.z(t) - 5.5, 2) for t in (10, 14, 16)])
    print('RIGHT part:', gaps([HERO_R, AMB_R] + TRAF_R, T_RW, DUR, dims))
    print('   (hospital bay x 8.6; lanes end at x 7.0)')
    lat = min(min(abs(c.pose(t)[0] - AMB_R.pose(t)[0]) - (1.84 + 2.4) / 2 for c in [HERO_R] + TRAF_R
                  if abs(c.pose(t)[1] - AMB_R.pose(t)[1]) < 6) for t in np.arange(23.5, 30, 0.05)
              if any(abs(c.pose(t)[1] - AMB_R.pose(t)[1]) < 6 for c in [HERO_R] + TRAF_R))
    print('   ambulance lateral clearance passing the stopped cars (m):', round(lat, 2))
    print('   last car passed', T_LAST, 'everyone goes at', T_GO, 'hero merges back', T_BACK, 'amb lane change', T_AMB_LANE)
    print('   ambulance passes hero at t =', round(next(t for t in np.arange(T_RW, DUR, 0.02) if AMB_R.z(t) - 3.3 > HERO_R.z(t) + 2.2), 2),
          '| hero moves again at', T_GO, '| merges back', T_BACK)
    print('   gap hero -> ambulance when hero merges back (m):', round(AMB_R.z(T_BACK) - HERO_R.z(T_BACK), 1))
    print('   ambulance stops at hospital z', round(HOSP_Z, 1), 'x', AMB_R.pose(34)[0], '| right-lane cars pass it at x', RIGHT_X,
          'clearance', round(AMB_R.pose(34)[0] - 1.2 - RIGHT_X - 0.92, 2))
    onc = gaps(ONC_R, T_RW, DUR, lambda a: (1.84, 4.4))
    print('   oncoming (pull-over) min gap', onc)
    print('beats:', len(BEATS), 'HR wrong end', round(hr_at(12.8)), 'HR right end', round(hr_at(30)))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        run(video, sound, 'makeway.mp4')
