"""Breakdown on the highway at night: where to stop, how to get out, where to wait. Highway 401 near Kingston, Ontario.

World: +Z = east (travel). Three eastbound lanes x = 1.75 / 5.25 / 8.75, paved shoulder 10.5..13.5, steel guardrail at
x = 14.2, grass slope beyond. Concrete median barrier at x = -0.4, westbound lanes at x < -1.
Night: the scene is drawn, darkened, then a light pass adds headlight beams, tail lights, hazards and reflectors.
Part 1 (wrong): engine dies, he brakes to a stop IN the middle lane, steps out of the driver door into traffic and
stands behind his car. Part 2 (right): hazards on at once, use the momentum to coast onto the shoulder, get out on
the PASSENGER side, climb behind the guardrail and wait upstream of the car, call for help. If it is not safe to get
out: stay buckled in with hazards on and call 911.
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
import euro

DUR = 37.0
V = 27.8                                  # 100 km/h
T_FAIL_W, T_FAIL_R = 7.0, 18.0
T_R0 = 17.2
T_FREEZE = 15.5
NIGHT = (0.03, 0.05, 0.16)


# ------------------------------------------------------------------ cars
class NCar(Track):
    def __init__(self, x, speed, ta, za, col, occ=None, haz_from=None, door=None, door_side=-1, blink=None, xfun=None,
                 kind='car', brake=None):
        super().__init__(x, speed, ta, za, col, blink=blink, brake=brake, t0=-3, t1=45)
        self.occ, self.haz_from, self.door, self.door_side, self.xfun, self.kind = occ, haz_from, door, door_side, xfun, kind
        self.lights_on = True

    def pose(self, t):
        x, z, h = super().pose(t)
        if self.xfun:
            nx = self.xfun(z)
            dz = 0.3
            h = math.atan2(self.xfun(z + dz) - self.xfun(z - dz), 2 * dz) if self.speed(t) > 1 else 0.0
            return nx, z, h
        return x, z, h

    def haz(self, t):
        return self.haz_from is not None and t >= self.haz_from

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        b = ('L' if (t * 1.25) % 1 < 0.5 else None) if self.haz(t) else self.blink(t)
        if self.kind == 'semi':
            if view.ortho:
                return [((x, 1, z), lambda: fill_poly(ctx, view, [(x - 1.3, 0, z - 17), (x + 1.3, 0, z - 17), (x + 1.3, 0, z + 5),
                                                                   (x - 1.3, 0, z + 5)], hexc('#d9d9de'), OUTL, 3))]
            br = self.brake(t) > 0.5
            return [((x, 1.5, z + 2.5), lambda: tractor_det(ctx, view, x, z, h, '#3a3d48', False, None, br)),
                    ((x, 2.0, z - 7.2), lambda: trailer_det(ctx, view, x, z, h, False, False, br, '#d9d9de', '#2f6f9f', 'EASTLINE'))]

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, b, self.occ is not None)
                return
            occ = self.occ(t) if self.occ else None
            draw_car_round(ctx, view, x, z, h, self.col, t, b, self.brake(t), occ=occ)
        out = [((x, 0.8, z), fn)]
        a = self.door(t) if self.door else 0.0
        if a > 0.02 and not view.ortho:
            Lf = L(x, z, h)
            sd = self.door_side
            ex, ez = sd * (0.92 + math.sin(a) * 1.15), 0.95 - math.cos(a) * 1.15
            lower = [Lf(sd * 0.92, 0.35, 0.95), Lf(ex, 0.35, ez), Lf(ex, 0.85, ez), Lf(sd * 0.92, 0.85, 0.95)]
            upper = [Lf(sd * 0.92, 0.85, 0.95), Lf(ex, 0.85, ez), Lf(ex - sd * 0.05, 1.32, ez + 0.2), Lf(sd * 0.86, 1.36, 0.75)]

            def door_fn():
                fill_poly(ctx, view, lower, mix(hexc(self.col), (0, 0, 0), 0.18), OUTL, 2)
                fill_poly(ctx, view, upper, hexc('#3b4658'), OUTL, 2, 0.85)
            out.append((Lf((ex + sd * 0.92) / 2, 0.8, (ez + 0.95) / 2), door_fn))
        return out


def hero_occ(until, expr):
    def occ(t):
        if t >= until:
            return None

        def fn(ctx, view, Lf, h):
            person3d(ctx, view, Lf, -0.38, 0.05, 'hero', 0.0, expr(t))
        return fn
    return occ


# ---- part 1
SPD_W = Key([(0, V), (T_FAIL_W, V), (7.8, 26.0), (10.4, 0.0), (99, 0.0)], 'lin')
T_EXIT_W = 11.6
HERO_W = NCar(5.25, SPD_W, T_FAIL_W, 0.0, '#e23b3b', hero_occ(T_EXIT_W, lambda t: 'calm' if t < T_FAIL_W else 'worried'),
              door=Key([(0, 0), (T_EXIT_W - 0.4, 0), (T_EXIT_W, 1.0), (13.0, 1.0), (13.4, 0.0), (99, 0)]), door_side=-1)
ZW = HERO_W.z(12.0)
SWERVE = lambda z: 5.25 + (1.75 - 5.25) * smooth((z - (ZW - 45)) / 25.0) * (1 - smooth((z - (ZW + 25)) / 30.0))
CAR1 = NCar(5.25, const(30.0), 12.9, ZW, '#c9c9d6', xfun=SWERVE)
SEMI = NCar(5.25, Key([(0, 25.0), (14.2, 25.0), (16.0, 14.0), (99, 14.0)], 'lin'), T_FREEZE, ZW - 40.0, '#3a3d48', kind='semi',
            brake=lambda t: 1.0 if t > 14.2 else 0.0)
TRAF_W = [NCar(1.75, const(31.0), 9.0, ZW - 70 + 60 * i, c) for i, c in enumerate(['#3a7bd5', '#f2a541', '#37b26c'])]
TRAF_W += [NCar(8.75, const(27.0), 9.0, ZW - 20 + 55 * i, c) for i, c in enumerate(['#7a4fd0', '#1c1c22', '#f4f4f6'])]
PATH_W_T = [T_EXIT_W, T_EXIT_W + 0.5, 12.9, 99]
HERO_PED_W = Ped(lambda t: float(np.interp(t, PATH_W_T, [5.25 - 1.45, 3.9, 5.0, 5.0])),
                 lambda t: float(np.interp(t, PATH_W_T, [ZW + 0.4, ZW - 0.5, ZW - 3.6, ZW - 3.6])),
                 top='#d0912c', pants='#2b3a63', skin='#e9b98f', hair='#3a2316')

# ---- part 2
SPD_R = Key([(0, V), (T_FAIL_R, V), (19.0, 25.5), (21.5, 13.0), (23.0, 0.0), (99, 0.0)], 'lin')
X_R = Key([(0, 5.25), (19.2, 5.25), (20.4, 8.75), (21.2, 8.75), (22.6, 12.0), (99, 12.0)])
T_EXIT_R = 24.0
HERO_R = NCar(X_R, SPD_R, T_FAIL_R, 0.0, '#e23b3b', hero_occ(T_EXIT_R, lambda t: 'focus' if t < 26 else 'relieved'),
              haz_from=T_FAIL_R + 0.5, door=Key([(0, 0), (T_EXIT_R - 0.6, 0), (T_EXIT_R - 0.1, 1.0), (24.9, 1.0), (25.3, 0.0), (99, 0)]),
              door_side=1)
ZR = HERO_R.z(25.0)
MOVE_OVER = lambda z: 8.75 + (5.25 - 8.75) * smooth((z - (ZR - 70)) / 25.0) * (1 - smooth((z - (ZR + 15)) / 25.0))
TRAF_R = [NCar(8.75, const(26.5), 25.5 + 2.6 * i, ZR, c, xfun=MOVE_OVER) for i, c in enumerate(['#7a4fd0', '#f4f4f6', '#37b26c', '#3a7bd5'])]
TRAF_R += [NCar(1.75, const(31.0), 20.0, ZR - 80 + 70 * i, c) for i, c in enumerate(['#f2a541', '#1c1c22', '#c9c9d6'])]
PATH_R_T = [T_EXIT_R + 0.2, T_EXIT_R + 0.7, T_EXIT_R + 1.6, T_EXIT_R + 2.4, T_EXIT_R + 5.6, 99]
HERO_PED_R = Ped(lambda t: float(np.interp(t, PATH_R_T, [12.0 + 1.45, 13.7, 14.0, 15.4, 16.2, 16.2])),
                 lambda t: float(np.interp(t, PATH_R_T, [ZR + 0.3, ZR - 0.2, ZR - 0.8, ZR - 1.4, ZR - 13.0, ZR - 13.0])),
                 top='#d0912c', pants='#2b3a63', skin='#e9b98f', hair='#3a2316')


class TimedPed:
    def __init__(self, p, t0):
        self.p, self.t0 = p, t0

    def x(self, t):
        return self.p.x(t)

    def z(self, t):
        return self.p.z(t)

    def draw(self, ctx, view, t):
        if t >= self.t0:
            self.p.draw(ctx, view, t)
            if not view.ortho and getattr(self, 'phone', None) and t >= self.phone:
                P = (self.p.x(t) + 0.15, 1.55, self.p.z(t))
                pp, s = view.pt(P), view.scale(P)
                if pp and s:
                    glow(ctx, pp[0], pp[1], min(0.5 * s, 50), (0.7, 0.85, 1.0), 0.9)


PW = TimedPed(HERO_PED_W, T_EXIT_W)
PW.phone = 13.0
PR = TimedPed(HERO_PED_R, T_EXIT_R + 0.2)
PR.phone = T_EXIT_R + 5.6


# ------------------------------------------------------------------ the 401 at night
C_GRASS_N = hexc('#2f4a33')


class Night401:
    sky = ('#050a1e', '#1d2a52')

    def __init__(self):
        self.ground_col = C_GRASS_N
        r = random.Random(4)
        self.trees = [(r.uniform(20, 60), z + r.uniform(-4, 4), r.uniform(1.0, 1.6)) for z in np.arange(-300, 1500, 11)]
        self.trees += [(-r.uniform(22, 60), z + r.uniform(-4, 4), r.uniform(1.0, 1.6)) for z in np.arange(-300, 1500, 13)]
        self.stars = [(r.uniform(0, SW), r.uniform(0, 1), r.uniform(1, 2.6)) for _ in range(90)]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        hy = view.horizon()
        for x, f, r in self.stars:
            ellipse(ctx, x, hy - 40 - f * 600, r, r)
            setc(ctx, (1, 1, 1), 0.8)
            ctx.fill()
        ellipse(ctx, 1500, hy - 430, 55, 55)
        setc(ctx, hexc('#f4f2e2'))
        ctx.fill()
        glow(ctx, 1500, hy - 430, 180, hexc('#c9d6ff'), 0.4)
        far_line(ctx, view, 2500, lambda x: 25 + 10 * math.sin(x / 300), col='#0f1a2a')

    def ground(self, ctx, view, t):
        ez = view.pos[2] if not view.ortho else view.zc
        zlo, zhi = ez - 200, ez + 1500
        gquad(ctx, view, -13.0, 13.5, zlo, zhi, hexc('#4a4d58'))
        gquad(ctx, view, -11.5, -1.0, zlo, zhi, C_ASPH)
        gquad(ctx, view, 0.0, 10.5, zlo, zhi, C_ASPH)
        for xl in (3.5, 7.0, -4.5, -8.0):
            for k in range(int(zlo // 12), int(zhi // 12) + 1):
                gquad(ctx, view, xl - 0.07, xl + 0.07, k * 12, k * 12 + 4, C_LINE, 0.01)
        gquad(ctx, view, 10.35, 10.5, zlo, zhi, C_LINE, 0.01)
        gquad(ctx, view, 0.0, 0.15, zlo, zhi, C_YEL, 0.01)
        if not view.ortho:
            for x0, x1, y0, y1 in ((-0.4, -0.4, 0.0, 0.9),):
                fill_poly(ctx, view, [(-0.4, 0, zlo), (-0.4, 0, zhi), (-0.4, 0.9, zhi), (-0.4, 0.9, zlo)], hexc('#8d8a84'), OUTL, 1)
            # guardrail: posts + rail
            fill_poly(ctx, view, [(14.2, 0.55, zlo), (14.2, 0.55, zhi), (14.2, 0.8, zhi), (14.2, 0.8, zlo)], hexc('#b9bcc4'), OUTL, 1)
            for k in range(int(max(zlo, ez - 40) // 4), int(min(zhi, ez + 160) // 4)):
                a, b = view.pt((14.2, 0, k * 4.0)), view.pt((14.2, 0.6, k * 4.0))
                if a and b:
                    ctx.move_to(*a)
                    ctx.line_to(*b)
                    setc(ctx, hexc('#7a7f8c'))
                    ctx.set_line_width(max(1, (view.scale((14.2, 0.3, k * 4.0)) or 4) * 0.12))
                    ctx.stroke()
        else:
            gquad(ctx, view, 14.1, 14.3, zlo, zhi, hexc('#b9bcc4'))

    def objects(self, ctx, view, t):
        out = []
        ez = view.pos[2] if not view.ortho else view.zc
        for x, z, s in self.trees:
            if ez - 60 < z < ez + 600:
                out.append(((x, 2.5, z), lambda x=x, z=z, s=s: conifer(ctx, view, x, z, s * (0.5 if view.ortho else 1.0))))
        return out


world = SegWorld(DUR, [hook_seg(0, 3.0, 12.5, HERO_W, [CAR1, SEMI] + TRAF_W, [PW]),
                       (3.0, T_R0, HERO_W, [CAR1, SEMI] + TRAF_W, [PW]),
                       (T_R0, 99, HERO_R, TRAF_R, [PR])], Night401(), 'kmh')
world.police_flash = lambda t: 0.0


# ------------------------------------------------------------------ night light pass
def all_cars(w, t):
    out = [w.ego(t)] + list(w.others(t))
    return out


def light_pass(ctx, view, w, t):
    if view.ortho:
        return
    # darken
    setc(ctx, NIGHT, 0.55)
    ctx.paint()
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    for a in all_cars(w, t):
        if not hasattr(a, 'pose'):
            continue
        x, z, h = a.pose(t)
        d = view.depth((x, 0.8, z))
        if d < 1.5 or d > 400:
            continue
        Lf = L(x, z, h)
        semi = getattr(a, 'kind', getattr(getattr(a, 'a', None), 'kind', 'car')) == 'semi'
        fz = 3.0 if semi else 2.25
        # headlight beam on the road
        beam = [Lf(-0.9, 0.02, fz), Lf(0.9, 0.02, fz), Lf(3.5, 0.02, fz + 32), Lf(-3.5, 0.02, fz + 32)]
        pts = view.poly(beam) if not (a is HERO_R and t > 23.2) else None
        if pts:
            p0 = view.pt(Lf(0, 0.02, fz))
            p1 = view.pt(Lf(0, 0.02, fz + 30))
            if p0 and p1:
                g = cairo.LinearGradient(p0[0], p0[1], p1[0], p1[1])
                g.add_color_stop_rgba(0, 1.0, 0.95, 0.7, 0.42)
                g.add_color_stop_rgba(1, 1.0, 0.95, 0.7, 0.0)
                poly(ctx, pts)
                ctx.set_source(g)
                ctx.fill()
        if a is HERO_R and t > 23.2:
            beam_off = True
        else:
            beam_off = False
        vx, vz = view.pos[0] - x, view.pos[2] - z
        facing = (math.sin(h) * vx + math.cos(h) * vz)
        for sx in (-0.62, 0.62):
            if facing > 0 and not beam_off:
                P = Lf(sx, 0.68 if not semi else 1.1, fz + 0.02)
                p, s = view.pt(P), view.scale(P)
                if p and s:
                    glow(ctx, p[0], p[1], min(1.6 * s, 420), (1.0, 0.95, 0.8), 0.9)
            else:
                P = Lf(sx, 0.68 if not semi else 1.0, -2.22 if not semi else -15.0)
                p, s = view.pt(P), view.scale(P)
                if p and s:
                    br = a.brake(t) > 0.5 if hasattr(a, 'brake') else False
                    glow(ctx, p[0], p[1], min((0.9 if br else 0.5) * s, 220), (1.0, 0.1, 0.1), 0.9 if br else 0.6)
        if getattr(a, 'haz', None) and a.haz(t) and (t * 1.25) % 1 < 0.5:
            for P in (Lf(-0.85, 0.68, 2.22), Lf(0.85, 0.68, 2.22), Lf(-0.85, 0.68, -2.22), Lf(0.85, 0.68, -2.22)):
                p, s = view.pt(P), view.scale(P)
                if p and s and view.to_cam(P)[2] > 0:
                    glow(ctx, p[0], p[1], min(1.2 * s, 260), AMBER, 0.9)
    # guardrail reflectors + lane marking sparkle near the camera
    ez = view.pos[2]
    for k in range(int((ez - 10) // 8), int((ez + 200) // 8)):
        P = (14.15, 0.7, k * 8.0)
        p, s = view.pt(P), view.scale(P)
        if p and s:
            glow(ctx, p[0], p[1], min(0.25 * s + 4, 30), (1.0, 0.8, 0.3), 0.6)
    ctx.restore()


def n_cam(ctx, w, t, lt, kw):
    tf = min(t, kw['freeze']) if 'freeze' in kw else t
    e = w.ego(tf)
    x, z, h = e.pose(tf)
    m = kw['cam']
    if m == 'fixed':
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000))
    elif m == 'rel':
        ox, oy, oz = kw['off']
        tx, ty, tz = kw['look']
        view = look_at((x + ox, oy, z + oz), (x + tx, ty, z + tz), kw.get('f', 950))
    elif m == 'chase':
        view = TCam((x, 3.6, z - 10.5), 0.0, 0.16, 1000, cy=520)
    elif m == 'high':
        view = TCam((7.0, 13.0, z - 18), 0.0, 0.5, 1000, cy=470)
    draw_scene(ctx, view, w, tf)
    light_pass(ctx, view, w, tf)
    if 'freeze' in kw and t >= kw['freeze']:
        u = t - kw['freeze']
        setc(ctx, (1, 1, 1), max(0, 0.8 - u * 3))
        ctx.paint()
        setc(ctx, (0.6, 0, 0), 0.22)
        ctx.paint()
    if kw.get('hud', m == 'chase'):
        hud(ctx, w, tf)
    if kw.get('post'):
        kw['post'](ctx, view, tf, lt)


def dash_n(ctx, w, t, lt, kw):
    """Night dashboard: engine + battery lights, the speedo dropping, the hazard button."""
    setc(ctx, hexc('#0c0e16'))
    ctx.paint()
    rrect(ctx, 200, 160, 1520, 760, 120)
    fill_stroke(ctx, hexc('#11131c'), hexc('#2a2c3a'), 8)
    cx, cy, r = 640, 540, 300
    ellipse(ctx, cx, cy, r, r)
    fill_stroke(ctx, hexc('#07080c'), hexc('#3a3d58'), 8)
    v = w.speed(t) * 3.6
    for k in range(0, 161, 20):
        a = math.pi * (0.75 + 1.5 * k / 160)
        ctx.move_to(cx + math.cos(a) * (r - 30), cy + math.sin(a) * (r - 30))
        ctx.line_to(cx + math.cos(a) * (r - 70), cy + math.sin(a) * (r - 70))
        setc(ctx, (0.6, 0.85, 1.0))
        ctx.set_line_width(6)
        ctx.stroke()
    a = math.pi * (0.75 + 1.5 * clamp(v / 160))
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(a) * (r - 60), cy + math.sin(a) * (r - 60))
    setc(ctx, hexc('#ff6a3d'))
    ctx.set_line_width(12)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    text_center(ctx, f'{int(round(v))} km/h', cx, cy + 190, 56, (0.8, 0.9, 1.0))
    t_fail = kw['t_fail']
    on = t >= t_fail and (t * 2.2) % 1 < 0.7
    for k, (lbl, col) in enumerate((('ENGINE', '#ffb21e'), ('BATTERY', '#ff3030'))):
        bx, by = 1120 + k * 250, 330
        rrect(ctx, bx - 100, by - 70, 200, 140, 24)
        fill_stroke(ctx, hexc(col) if on else hexc('#2a2c3a'), OUTL, 4)
        text_center(ctx, lbl, bx, by + 18, 40, (0.1, 0.1, 0.1) if on else (0.4, 0.4, 0.45))
        if on:
            glow(ctx, bx, by, 220, hexc(col), 0.35)
    # hazard button
    pressed = kw.get('hazard') is not None and lt >= kw['hazard']
    hb = pressed and (t * 1.25) % 1 < 0.5
    bx, by = 1245, 680
    rrect(ctx, bx - 140, by - 110, 280, 220, 40)
    fill_stroke(ctx, hexc('#ff3030') if hb else hexc('#3a1a1a'), OUTL, 6)
    poly(ctx, [(bx, by - 70), (bx + 80, by + 60), (bx - 80, by + 60)])
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(14)
    ctx.stroke()
    if hb:
        glow(ctx, bx, by, 300, hexc('#ff3030'), 0.45)
    if lt > 0.6 and t >= t_fail:
        label(ctx, 1250, 150, 'Engine losing power...', '#3a3d48', 50)


def phone_card(ctx, w, t, lt, kw):
    setc(ctx, hexc('#070b1a'))
    ctx.paint()
    rrect(ctx, 660, 60, 600, 960, 70)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, 8)
    rrect(ctx, 690, 110, 540, 860, 40)
    setc(ctx, hexc('#14325a'))
    ctx.fill()
    text_center(ctx, 'Calling...', 960, 250, 56, (0.8, 0.9, 1.0))
    text_center(ctx, 'Roadside', 960, 380, 76, (1, 1, 1))
    text_center(ctx, 'Assistance', 960, 470, 76, (1, 1, 1))
    for k in range(3):
        a = (lt * 2 - k * 0.3) % 1
        ctx.arc(960, 640, 60 + a * 120, 0, 2 * math.pi)
        setc(ctx, (0.5, 0.8, 1.0), 1 - a)
        ctx.set_line_width(5)
        ctx.stroke()
    ellipse(ctx, 960, 640, 56, 56)
    setc(ctx, hexc('#22c35e'))
    ctx.fill()
    text_center(ctx, 'Danger? Call 911', 960, 880, 52, hexc('#ffd23f'))
    if lt > 1.0:
        label(ctx, 330, 300, "Can't get out safely?", '#e0393e', 44)
        label(ctx, 330, 380, 'Stay buckled in,', '#3a3d48', 40)
        label(ctx, 330, 450, 'hazards ON,', '#3a3d48', 40)
        label(ctx, 330, 520, 'call 911.', '#3a3d48', 40)


def zones_top(ctx, w, t, lt, kw):
    view = HTop(6.5, ZR - 4.0, 34.0)
    draw_scene(ctx, view, w, t)
    a = smooth(lt / 0.4)
    # danger: in the lanes, beside and right behind the car
    for (x0, x1, z0, z1, col) in ((0.0, 10.5, ZR - 25, ZR + 25, '#ff4b4b'), (10.5, 14.2, ZR - 12, ZR - 2.3, '#ff4b4b')):
        pts = view.poly([(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)])
        poly(ctx, pts)
        setc(ctx, hexc(col), 0.25 * a)
        ctx.fill()
    pts = view.poly([(14.4, 0, ZR - 22), (19.0, 0, ZR - 22), (19.0, 0, ZR - 6), (14.4, 0, ZR - 6)])
    poly(ctx, pts)
    setc(ctx, hexc('#22c35e'), 0.35 * a)
    ctx.fill()
    p = view.pt((16.5, 0, ZR - 14))
    label(ctx, p[0], p[1] + 70, 'SAFE: behind the guardrail', '#22a356', 38)
    q = view.pt((12.3, 0, ZR - 8))
    label(ctx, q[0] - 80, q[1] - 20, 'Not behind your car', '#e0393e', 36)
    r_ = view.pt((5.0, 0, ZR + 6))
    label(ctx, r_[0], r_[1], 'Traffic', '#e0393e', 36)


engine.SCENES.update(n_cam=n_cam, dash_n=dash_n, phone_card=phone_card, zones_top=zones_top)

HOOK = dict(cam='fixed', pos=(8.6, 2.0, ZW + 7.0), target=(4.2, 0.9, ZW - 30.0), f=950)
SIDE_W = dict(cam='fixed', pos=(-3.0, 1.8, ZW + 9.0), target=(4.5, 1.0, ZW - 2.0), f=900)
BEHIND_W = dict(cam='fixed', pos=(12.5, 3.2, ZW + 3.0), target=(4.5, 0.8, ZW - 16.0), f=900, freeze=T_FREEZE)
EXIT_R = dict(cam='fixed', pos=(17.0, 2.2, ZR + 9.0), target=(12.0, 1.0, ZR - 1.0), f=900)
WAIT_R = dict(cam='fixed', pos=(19.8, 2.2, ZR - 22.0), target=(12.5, 1.0, ZR - 6.0), f=900)
defs = [
    (3.0, 'n_cam', dict(HOOK)),
    (6.0, 'n_cam', dict(cam='chase')),
    (8.5, 'dash_n', dict(t_fail=T_FAIL_W)),
    (11.0, 'n_cam', dict(cam='high')),
    (13.5, 'n_cam', dict(SIDE_W)),
    (16.0, 'n_cam', dict(BEHIND_W)),
    (T_R0, 'rewind_seq', dict()),
    (19.7, 'dash_n', dict(t_fail=T_FAIL_R, hazard=1.2)),
    (22.7, 'n_cam', dict(cam='high')),
    (25.2, 'n_cam', dict(EXIT_R)),
    (28.2, 'n_cam', dict(WAIT_R)),
    (31.0, 'zones_top', dict()),
    (33.5, 'phone_card', dict()),
    (DUR, 'n_cam', dict(WAIT_R)),
]
shots = build_shots(defs)
shots[6].kw.update(srcs=list(reversed(shots[1:6])), dur=shots[6].dur)
video = Video(['Your car dies on the highway.', 'At night. What now?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Stalled in the dark...', 300, 120, hexc('#ffd23f'), 0.2, True)),
    (3.0, 6.0, location_tag('Highway 401 near Kingston, Ontario')),
    (3.2, 6.0, caption('Night drive at 100 km/h')),
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, E[2], caption('Warning lights... the engine dies')),
    (S[3] + 0.2, E[3], caption('He stops right IN the middle lane')),
    (S[4] + 0.2, E[4], caption('...and steps out into traffic!')),
    (S[5] + 0.2, E[5], caption('Behind the car: the worst spot')),
    (S[5] + 1.8, E[5], x_mark),
    (S[11], E[11], badge('WHERE TO WAIT', '#22a356')),
    (S[12], E[12], badge('CALL FOR HELP', '#22a356')),
    (S[13] + 0.2, E[13], end_card('Hazards. Shoulder. Passenger side. Guardrail.', 'Did you know the passenger-side rule? Comment!')),
]
for n, (i, txt) in enumerate(((7, 'Hazards ON right away'), (8, 'Use the momentum: get onto the shoulder'),
                              (9, 'Get out on the PASSENGER side'), (10, 'Wait behind the guardrail, away from the car')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]


# ------------------------------------------------------------------ sound
def sputter(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    f = 45 * np.maximum(0.2, 1 - tt / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    gate = (np.sin(2 * np.pi * 5 * tt + 3 * np.sin(2 * np.pi * 1.3 * tt)) > -0.2).astype(float)
    return lp(sum(np.sin(k * ph) / k for k in range(1, 6)), 500) * gate * 0.5 * np.maximum(0, 1 - tt / d)


def air_horn(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    s = sum(sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, 8)) for f in (220, 277, 330))
    return bp(np.tanh(s * 0.5), 150, 3000) * env_adsr(n, 0.04, 0.1) * 0.45


def ring(d):
    out = np.zeros(int(d * SR) + SR)
    k = 0
    while k * 2.0 < d:
        tt = np.arange(int(1.0 * SR)) / SR
        place(out, (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * 0.15, k * 2.0)
        k += 1
    return out[:int(d * SR)]


def sound():
    m = Mixer(video.dur)
    m.add(lp(noise(int(video.dur * SR)), 250), 0, 0.18)
    hook_sfx(m)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.12)
    m.add(air_horn(1.6), 0.8, 0.8)
    m.add(car_pass(1.4, 0.5, 100), 1.4, 0.7, np.linspace(-0.5, 0.5, int(1.4 * SR)))
    m.add(sputter(2.5), T_FAIL_W, 0.7)
    m.add(tick(True), T_FAIL_W + 0.2, 0.6)
    m.add(screech(1.6, 1100), 8.4, 0.35)
    m.add(click(), T_EXIT_W - 0.4, 0.8)
    m.add(horn(1.0), 12.4, 0.9, -0.4)
    m.add(car_pass(1.6, 0.5, 100), 12.1, 1.0, np.linspace(-0.8, 0.8, int(1.6 * SR)))
    m.add(heartbeat(3, 130), 13.6, 0.7)
    m.add(air_horn(1.6), 14.0, 0.9)
    m.add(brake_squeal(1.4), 14.2, 0.6)
    m.add(sad_violin(), T_FREEZE + 0.05, 0.8)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(sputter(2.5), T_FAIL_R, 0.7)
    m.add(click(), S[7] + 1.2, 0.8)
    indicator(m, S[7] + 1.2, 33.5, 0.38, 0.1)
    m.add(click(), T_EXIT_R - 0.6, 0.8)
    m.add(thud(), 25.3, 0.4)
    t = T_EXIT_R + 0.3
    while t < T_EXIT_R + 5.6:
        m.add(footsteps(0.1, 100), t, 0.25)
        t += 0.42
    for i in range(4):
        m.add(car_pass(1.6, 0.5, 100), 25.7 + 2.6 * i, 0.5, np.linspace(-0.6, 0.6, int(1.6 * SR)))
    for i in (7, 8, 9, 10):
        m.add(pop(), S[i] + 0.15, 0.6)
    m.add(ring(2.4), S[12] + 0.1, 0.7)
    m.add(chime(), S[11] + 0.5, 0.6)
    m.add(success_jingle(), S[13] + 0.3, 0.8)
    return m.out(video.dur)


def verify():
    print('wrong: stops in the middle lane at z', round(ZW, 1))
    gap = min(abs(CAR1.pose(t)[0] - HERO_PED_W.x(t)) - 0.92 - 0.25 for t in np.arange(T_EXIT_W, 14, 0.02) if abs(CAR1.pose(t)[1] - HERO_PED_W.z(t)) < 2.6)
    print('   swerving car vs the man standing in lane 1 (closest lateral m):', round(gap, 2))
    print('   semi gap at freeze:', round(ZW - 2.2 - (SEMI.z(T_FREEZE) + 5.0), 1), 'm (man behind the car at z', round(ZW - 3.6, 1), ')')
    worst = 99
    for t in np.arange(T_FAIL_W, T_FREEZE, 0.05):
        for c in TRAF_W:
            for o in [HERO_W, CAR1, SEMI]:
                if abs(c.pose(t)[0] - o.pose(t)[0]) < 1.9:
                    worst = min(worst, abs(c.z(t) - o.pose(t)[1]) - 4.4)
    print('   traffic min gap (lane sharing):', round(worst, 2))
    print('right: stops on shoulder x', X_R(24), 'z', round(ZR, 1), '| car edge', round(X_R(24) + 0.92, 2), 'guardrail 14.2')
    worst = 99
    for t in np.arange(T_R0, DUR, 0.05):
        P = [HERO_R] + TRAF_R
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                a, b = P[i].pose(t), P[j].pose(t)
                if abs(a[0] - b[0]) < 1.95:
                    worst = min(worst, abs(a[1] - b[1]) - 4.4)
    print('   min gap right part:', round(worst, 2), '| moved-over cars pass the parked car at x', round(MOVE_OVER(ZR), 2))
    print('   man waits at', round(HERO_PED_R.x(32), 1), round(HERO_PED_R.z(32) - ZR, 1), '(behind the guardrail, upstream)')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        run(video, sound, 'breakdown.mp4')
