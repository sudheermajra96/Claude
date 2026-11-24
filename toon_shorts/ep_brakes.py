"""Brake failure on a steep hill: freeze vs act. Duluth, Minnesota (autumn, Lake Superior, the lift bridge).

World: +Z = downhill toward the lake. The avenue drops at a 12% grade: y(z) = -G z for z < Z_BOT, flat after.
Our lane x 0..3.5 (centre 1.75), a parking lane 3.5..6.0, curb at 6.0; uphill lane at x < 0.
Bottom: crosswalk + red light + Superior Street (cross traffic along X) at z ~ 140..160, then the waterfront.
All objects sit on the slope through YView, a view proxy that lifts everything by the road height at its z.
Steps used (standard driver-education advice): pump the brake pedal hard and fast, shift to a low gear (keep the
engine ON for power steering), apply the parking brake gradually, hazards + horn, steer to a safe spot.
Part 1 (wrong): he freezes on the dead pedal, the hill speeds him up toward a red light (freeze before).
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
import euro

DUR = 36.0
G = 0.12
Z_BOT = 140.0
Y_BOT = -G * Z_BOT
T_FW, T_R0, T_FR = 5.5, 16.0, 17.0
T_FREEZE = 14.3


def road_y(z):
    return -G * min(z, Z_BOT)


class YView:
    """View proxy: everything drawn through it is lifted by dy (sits on the slope)."""

    def __init__(self, v, dy):
        self.v, self.dy = v, dy
        self.ortho = v.ortho
        self.pos = (v.pos[0], v.pos[1] - dy, v.pos[2])
        if v.ortho:
            self.s, self.xc, self.zc = v.s, getattr(v, 'xc', 0), getattr(v, 'zc', 0)
            self.hrot = getattr(v, 'hrot', 0.0)

    def _p(self, P):
        return (P[0], P[1] + self.dy, P[2])

    def pt(self, P):
        return self.v.pt(self._p(P))

    def poly(self, pts):
        return self.v.poly([self._p(p) for p in pts])

    def depth(self, P):
        return self.v.depth(self._p(P))

    def scale(self, P):
        return self.v.scale(self._p(P))

    def to_cam(self, P):
        return self.v.to_cam(self._p(P))

    def horizon(self):
        return self.v.horizon()


def yv(view, z):
    return YView(view, road_y(z)) if not view.ortho else view


def make_L(pitch):
    def Lp(x, z, h):
        ch, sh = math.cos(h), math.sin(h)
        return lambda lx, ly, lz: (x + lx * ch + lz * sh, ly + lz * pitch * math.cos(h), z - lx * sh + lz * ch)
    return Lp


class HCar(Track):
    def __init__(self, x, speed, ta, za, col, occ=None, haz_from=None, blink=None, brake=None, horn=None):
        super().__init__(x, speed, ta, za, col, blink=blink, brake=brake, t0=-3, t1=45)
        self.occ, self.haz_from, self.horn = occ, haz_from, horn

    def blink_eff(self, t):
        if self.haz_from is not None and t >= self.haz_from:
            return 'L' if (t * 1.25) % 1 < 0.5 else None
        return self.blink(t)

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)

        def fn():
            v = yv(view, z)
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, self.blink_eff(t), self.occ is not None)
                return
            old = truckkit.L
            truckkit.L = make_L(-G if z < Z_BOT else 0.0)
            try:
                draw_car_round(ctx, v, x, z, h, self.col, t, self.blink_eff(t), self.brake(t), occ=self.occ(t) if self.occ else None)
            finally:
                truckkit.L = old
            if self.haz_from is not None and t >= self.haz_from and (t * 1.25) % 1 < 0.5:
                Lf = L(x, z, h)
                for P in (Lf(-0.85, 0.68 - 2.2 * G, 2.2), Lf(0.85, 0.68 - 2.2 * G, 2.2), Lf(-0.85, 0.68 + 2.2 * G, -2.2), Lf(0.85, 0.68 + 2.2 * G, -2.2)):
                    pp = v.pt(P)
                    if pp and v.to_cam(P)[2] > 0:
                        glow(ctx, pp[0], pp[1], min((v.scale(P) or 10) * 0.9, 140), AMBER, 0.9)
            if self.horn and self.horn(t):
                pp, sc = v.pt(L(x, z, h)(0, 2.2, 2.0)), v.scale(L(x, z, h)(0, 2.2, 2.0))
                if pp and sc:
                    label(ctx, pp[0], pp[1] - 20, 'HONK!', '#e0393e', clamp(sc * 0.5, 30, 70))
        return [((x, 0.8 + road_y(z), z), fn)]


def occ_for(expr):
    def occ(t):
        def fn(ctx, view, Lf, h):
            person3d(ctx, view, Lf, -0.38, 0.05, 'hero', 0.0, expr(t))
        return fn
    return occ


# ---- part 1: brakes fail at 5.5, he freezes; the 12% grade speeds him up
SPD_W = Key([(0, 11.0), (T_FW, 11.0), (T_FREEZE, 11.0 + 1.2 * (T_FREEZE - T_FW)), (99, 22.0)], 'lin')
HERO_W = HCar(1.75, SPD_W, T_FW, -30.0, '#e23b3b', occ_for(lambda t: 'calm' if t < T_FW else 'shock'))
# ---- part 2: pump (a little pressure back), low gear, parking brake slowly, steer to the curb, hazards + horn
SPD_R = Key([(0, 11.0), (T_FR, 11.0), (19.2, 12.1), (21.6, 9.7), (24.6, 1.9), (25.4, 0.0), (99, 0.0)], 'lin')
X_R = Key([(0, 1.75), (22.4, 1.75), (24.8, 4.55), (99, 4.55)])
HERO_R = HCar(X_R, SPD_R, T_FR, -30.0, '#e23b3b', occ_for(lambda t: 'calm' if t < T_FR else ('focus' if t < 25.6 else 'relieved')),
              haz_from=21.0, brake=lambda t: 1.0 if 21.6 < t < 99 else 0.0, horn=lambda t: 21.2 < t < 23.4 and (t * 3) % 1 < 0.6)
Z_STOP_R = HERO_R.z(30)

UPHILL = [HCar(-1.75, const(-0.0001), 0, 0, '#000')] if False else []
PARKED = [HCar(4.75, const(0.0), 0, z, c) for z, c in ((-70.0, '#c9c9d6'), (-55.0, '#37b26c'), (95.0, '#3a7bd5'), (108.0, '#f2a541'))]


class Up:
    """Uphill car (travels -z)."""

    def __init__(self, z0, v, col):
        self.z0, self.v, self.col = z0, v, col
        self.tr = HCar(-1.75, const(v), 0.0, 0.0, col)

    def visible(self, t):
        return True

    def pose(self, t):
        return -1.75, self.z0 - self.v * t, math.pi

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)

        def fn():
            v = yv(view, z)
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t)
                return
            old = truckkit.L
            truckkit.L = make_L(-G if z < Z_BOT else 0.0)
            try:
                draw_car_round(ctx, v, x, z, h, self.col, t)
            finally:
                truckkit.L = old
        return [((x, 0.8 + road_y(z), z), fn)]


UPS = [Up(150 + 70 * i, 8.0, c) for i, c in enumerate(['#7a4fd0', '#f4f4f6', '#2f6f73', '#d8c3a0', '#1c1c22'])]


class Cross:
    """Cross traffic on Superior Street (along X) at the bottom."""

    def __init__(self, x0, v, zl, col):
        self.x0, self.v, self.zl, self.col = x0, v, zl, col

    def visible(self, t):
        return True

    def pose(self, t):
        x = (self.x0 + self.v * t + 200) % 400 - 200
        return x, self.zl, math.pi / 2 if self.v > 0 else -math.pi / 2

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        return [((x, 0.8 + Y_BOT, z), lambda: draw_car_round(ctx, yv(view, z), x, z, h, self.col, t) if not view.ortho
                 else draw_car_top_g(ctx, view, x, z, h, self.col, t))]


CROSS = [Cross(-200 + 47 * i, 10.0, 151.75, c) for i, c in enumerate(['#3a7bd5', '#f2a541', '#c9c9d6', '#37b26c', '#e05d5d', '#1c1c22', '#7a4fd0', '#f4f4f6', '#2f6f73'])]
CROSS += [Cross(200 - 53 * i, -10.0, 155.25, c) for i, c in enumerate(['#d8c3a0', '#3a7bd5', '#e05d5d', '#f4f4f6', '#37b26c', '#1c1c22', '#f2a541', '#c9c9d6'])]


class SlopePed(Ped):
    def draw(self, ctx, view, t):
        Ped.draw(self, ctx, yv(view, self.z(t)), t)


def walker(x0, x1, t0, t1, z, top, hair='#3a2316', kid=False):
    return SlopePed(Key([(0, x0), (t0, x0), (t1, x1), (99, x1)], 'lin'), const(z), top=top, hair=hair, kid=kid)


PEDS = [walker(8.0, -8.0, 8.0, 19.0, 138.2, '#e05d5d'), walker(8.6, -7.4, 8.4, 19.4, 138.9, '#f2c230', kid=True),
        walker(-8.0, 8.0, 9.5, 20.5, 138.6, '#3a7bd5', '#6b4a2f'),
        walker(8.0, -8.0, 22.0, 33.0, 138.2, '#e05d5d'), walker(8.6, -7.4, 22.4, 33.4, 138.9, '#f2c230', kid=True)]


# ------------------------------------------------------------------ Duluth hillside + lake
AUTUMN = ['#e8742c', '#d9442b', '#f2b33d', '#b8572a', '#7d9a3a']


def autumn_tree(ctx, view, x, z, s, seed):
    v = yv(view, z)
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 2.0 * s * view.s, 2.0 * s * view.s)
        fill_stroke(ctx, hexc(AUTUMN[seed % 5]), OUTL, 2)
        return
    b, tp, sc = v.pt((x, 0, z)), v.pt((x, 3.4 * s, z)), v.scale((x, 0, z))
    if not b or not tp or not sc:
        return
    w = 0.35 * sc
    ctx.rectangle(b[0] - w / 2, tp[1], w, b[1] - tp[1])
    fill_stroke(ctx, hexc('#6b4a2f'), OUTL, max(1, min(4, sc / 30)))
    r = 2.0 * s * sc
    for i, (dx, dy) in enumerate(((-0.45, 0.1), (0.45, 0.15), (0, -0.4))):
        ellipse(ctx, tp[0] + dx * r, tp[1] + dy * r, r * 0.75, r * 0.7)
        fill_stroke(ctx, hexc(AUTUMN[(seed + i) % 5]), OUTL, max(1, min(4, sc / 30)))


def brick_bld(ctx, view, x0, x1, z0, z1, h, col):
    zc = (z0 + z1) / 2
    yb = road_y(z0 if z0 > 0 else z1) - 0.5
    Lf = lambda a, b, c: (a, b + yb, c)
    c = hexc(col)
    vis = lbox(ctx, view, Lf, 0.0, x0, x1, 0, h, z0, z1,
               {'front': c, 'back': c, 'left': mix(c, (0, 0, 0), 0.12), 'right': mix(c, (0, 0, 0), 0.05), 'top': mix(c, (0, 0, 0), 0.2)}, 2)
    if view.ortho:
        return
    face = 'left' if x0 > 0 else 'right'
    if face in vis:
        dx = x0 - 0.02 if x0 > 0 else x1 + 0.02
        for fl in range(int(h // 3.2)):
            for k in range(int((z1 - z0) // 3.0)):
                face_rect(ctx, view, Lf, face, z0 + 0.8 + k * 3.0, z0 + 2.2 + k * 3.0, 1.0 + fl * 3.2, 2.6 + fl * 3.2, dx, hexc('#2d3f55'))


class Hill:
    sky = ('#4f9ee0', '#e6f3ff')

    def __init__(self):
        self.ground_col = hexc('#8aa760')
        r = random.Random(6)
        self.trees, self.blds = [], []
        for z in np.arange(-260, Z_BOT - 8, 9):
            for sx in (-1, 1):
                self.trees.append((sx * (7.4 + r.uniform(0, 0.6)), z + r.uniform(-1, 1), r.uniform(0.9, 1.25), r.randrange(5)))
        for sx in (-1, 1):
            z = -260.0
            while z < Z_BOT - 20:
                w = r.uniform(12, 20)
                x0 = sx * 11.0
                x1 = sx * (11.0 + r.uniform(10, 16))
                self.blds.append((min(x0, x1), max(x0, x1), z, z + w, r.uniform(7, 14), r.choice(['#a35d43', '#8a4b38', '#b56f52', '#c9b9a6', '#9c4f3f'])))
                z += w + r.uniform(4, 10)

    def skyline(self, ctx, view):
        if view.ortho:
            return
        # Lake Superior to the horizon + the far shore + the aerial lift bridge
        far_line(ctx, view, 9000, lambda x: 60 + 30 * math.sin(x / 700), col='#7f9ab3')
        X, Z = -230.0, 520.0
        for dz in (0.0, 75.0):
            for k in range(2):
                pass
        b1, b2 = view.pt((X, Y_BOT, Z)), view.pt((X, Y_BOT, Z + 75))
        t1, t2 = view.pt((X, Y_BOT + 42, Z)), view.pt((X, Y_BOT + 42, Z + 75))
        s = view.scale((X, Y_BOT, Z))
        if b1 and b2 and t1 and t2 and s:
            col = hexc('#55606e')
            for b, tp in ((b1, t1), (b2, t2)):
                ctx.rectangle(tp[0] - 3 * s, tp[1], 6 * s, b[1] - tp[1])
                setc(ctx, col)
                ctx.fill()
            ctx.move_to(*t1)
            ctx.line_to(*t2)
            setc(ctx, col)
            ctx.set_line_width(max(2, 4 * s))
            ctx.stroke()
            m1, m2 = view.pt((X, Y_BOT + 30, Z)), view.pt((X, Y_BOT + 30, Z + 75))
            if m1 and m2:
                ctx.move_to(*m1)
                ctx.line_to(*m2)
                ctx.set_line_width(max(2, 3 * s))
                ctx.stroke()

    def ground(self, ctx, view, t):
        # lake (lower) beyond the waterfront
        gquad(ctx, view, -3000, 3000, 185, 9000, hexc('#3f7fb8'), Y_BOT - 1.0)
        gquad(ctx, view, -3000, 3000, 160, 185, hexc('#8aa760'), Y_BOT)
        # hillside + avenue on the slope (each section is planar)
        for x0, x1, col in ((-200, 200, hexc('#8aa760')), (-9.0, 9.0, C_WALK), (-6.0, 6.0, C_ASPH)):
            fill_poly(ctx, view, [(x0, road_y(-400), -400), (x1, road_y(-400), -400), (x1, Y_BOT, Z_BOT), (x0, Y_BOT, Z_BOT)], col)
        gquad(ctx, view, -200, 200, Z_BOT, 160.0, C_WALK, Y_BOT)
        gquad(ctx, view, -200, 200, 149.5, 157.5, C_ASPH, Y_BOT + 0.005)
        gquad(ctx, view, -6.0, 6.0, Z_BOT, 150.0, C_ASPH, Y_BOT + 0.004)
        # markings
        zlo = -400
        for zz in range(-400, int(Z_BOT) - 6, 12):
            a, b = zz, zz + 4
            fill_poly(ctx, view, [(-0.07, road_y(a) + 0.01, a), (0.07, road_y(a) + 0.01, a), (0.07, road_y(b) + 0.01, b), (-0.07, road_y(b) + 0.01, b)], C_YEL)
        for sx in (3.5,):
            fill_poly(ctx, view, [(sx - 0.07, road_y(zlo) + 0.01, zlo), (sx + 0.07, road_y(zlo) + 0.01, zlo), (sx + 0.07, Y_BOT + 0.01, Z_BOT - 6), (sx - 0.07, Y_BOT + 0.01, Z_BOT - 6)], C_LINE)
        if not view.ortho:
            zebra(ctx, YView(view, Y_BOT), -6.0, 6.0, 136.8, 140.0, 'x')
        else:
            zebra(ctx, view, -6.0, 6.0, 136.8, 140.0, 'x')
        fill_poly(ctx, view, [(0.2, Y_BOT + 0.012, 135.8), (6.0, Y_BOT + 0.012, 135.8), (6.0, Y_BOT + 0.012, 136.3), (0.2, Y_BOT + 0.012, 136.3)], C_LINE)

    def objects(self, ctx, view, t):
        out = []
        ez = view.pos[2] if not view.ortho else view.zc
        for x, z, s, sd in self.trees:
            if ez - 60 < z < ez + 500:
                out.append(((x, 1.5 + road_y(z), z), lambda x=x, z=z, s=s, sd=sd: autumn_tree(ctx, view, x, z, s * (0.45 if view.ortho else 1.0), sd)))
        for b in self.blds:
            if ez - 80 < b[2] < ez + 500:
                out.append((((b[0] + b[1]) / 2, b[4] / 2 + road_y(b[2]), (b[2] + b[3]) / 2), lambda b=b: brick_bld(ctx, view, *b)))
        out.append(((6.6, 3.0 + Y_BOT, 134.5), lambda: signal_head(ctx, YView(view, Y_BOT) if not view.ortho else view, 6.6, 3.4, 134.5, math.pi, 'red')))
        out.append(((-6.6, 3.0 + Y_BOT, 134.5), lambda: signal_head(ctx, YView(view, Y_BOT) if not view.ortho else view, -6.6, 3.4, 134.5, math.pi, 'red')))
        return out


world = SegWorld(DUR, [hook_seg(0, 3.0, 11.3, HERO_W, PARKED + UPS + CROSS, PEDS),
                       (3.0, T_R0, HERO_W, PARKED + UPS + CROSS, PEDS),
                       (T_R0, 99, HERO_R, PARKED + UPS + CROSS, PEDS)], Hill(), 'kmh')
world.police_flash = lambda t: 0.0


# ------------------------------------------------------------------ cameras + close-ups
def hb_cam(ctx, w, t, lt, kw):
    tf = min(t, kw['freeze']) if 'freeze' in kw else t
    e = w.ego(tf)
    x, z, h = e.pose(tf)
    m = kw['cam']
    if m == 'fixed':
        P, T_ = kw['pos'], kw['target']
        view = look_at((P[0], P[1] + road_y(P[2]), P[2]), (T_[0], T_[1] + road_y(T_[2]), T_[2]), kw.get('f', 1000))
    elif m == 'chase':
        view = TCam((x * 0.6 + 0.7, road_y(z - 10.5) + 3.4, z - 10.5), 0.0, 0.16 + math.atan(G) * 0.8, 1000, cy=500)
    elif m == 'high':
        view = TCam((3.0, road_y(z - 15) + 9.0, z - 15), 0.0, 0.42 + math.atan(G) * 0.5, 1000, cy=470)
    elif m == 'down':
        view = TCam((x * 0.5 + 0.9, road_y(z - 12) + 5.2, z - 12), 0.0, 0.33, 950, cy=430)
    elif m == 'side':
        view = look_at((-11.0, road_y(z + 3) + 2.6, z + 3.0), (x, road_y(z) + 0.9, z), 900)
    draw_scene(ctx, view, w, tf)
    if 'freeze' in kw and t >= kw['freeze']:
        u = t - kw['freeze']
        setc(ctx, (1, 1, 1), max(0, 0.8 - u * 3))
        ctx.paint()
        setc(ctx, (0.6, 0, 0), 0.22)
        ctx.paint()
    if kw.get('hud', m in ('chase',)):
        hud(ctx, w, tf)


def interior_bg(ctx):
    setc(ctx, hexc('#2a2b35'))
    ctx.paint()


def pedal_close(ctx, w, t, lt, kw):
    """Footwell: the brake pedal goes to the floor (fail) or is pumped hard and fast (pump)."""
    interior_bg(ctx)
    ctx.rectangle(0, 820, SW, 260)
    setc(ctx, hexc('#1c1c22'))
    ctx.fill()
    for k in range(9):
        ctx.rectangle(140 + k * 190, 840, 120, 220)
        setc(ctx, hexc('#24242c'))
        ctx.fill()
    mode = kw.get('mode', 'fail')
    if mode == 'fail':
        press = smooth(lt / 0.5)
        sink = smooth((lt - 0.5) / 0.6)
    else:
        press = 0.5 + 0.5 * math.sin(lt * 2 * math.pi * 2.6)
        sink = 0.75 * press
    # gas pedal (right)
    rrect(ctx, 1300, 380, 150, 330, 30)
    fill_stroke(ctx, hexc('#3a3d48'), OUTL, 6)
    # brake pedal (moves down / toward the floor)
    py = 330 + 330 * sink
    ctx.move_to(800, 0)
    ctx.line_to(820, py)
    setc(ctx, hexc('#3a3d48'))
    ctx.set_line_width(30)
    ctx.stroke()
    rrect(ctx, 650, py, 340, 190, 34)
    fill_stroke(ctx, hexc('#4a4d58'), OUTL, 6)
    for k in range(4):
        ctx.rectangle(690, py + 30 + k * 38, 260, 14)
        setc(ctx, hexc('#2a2b35'))
        ctx.fill()
    # the driver's shoe + trouser leg coming in from the top (attached, never floating)
    fy = py - 120 + 60 * (1 - press)
    ctx.move_to(560, -20)
    ctx.line_to(900, -20)
    ctx.line_to(980, fy + 40)
    ctx.line_to(640, fy + 60)
    ctx.close_path()
    fill_stroke(ctx, hexc('#2b3a63'), OUTL, 6)
    rrect(ctx, 600, fy + 20, 440, 170, 70)
    fill_stroke(ctx, hexc('#5b3a26'), OUTL, 6)
    if mode == 'fail' and lt > 0.9:
        label(ctx, 960, 200, 'Pedal to the floor... NOTHING!', '#e0393e', 64)
    if mode == 'pump':
        label(ctx, 1400, 220, 'PUMP! PUMP!', '#22a356', 64)


def dash_close(ctx, w, t, lt, kw):
    interior_bg(ctx)
    rrect(ctx, 260, 160, 1400, 760, 120)
    fill_stroke(ctx, hexc('#15151c'), OUTL, 8)
    cx, cy, r = 760, 560, 320
    ellipse(ctx, cx, cy, r, r)
    fill_stroke(ctx, hexc('#0b0b10'), hexc('#55566e'), 8)
    v = w.speed(t) * 3.6
    for k in range(0, 161, 20):
        a = math.pi * (0.75 + 1.5 * k / 160)
        ctx.move_to(cx + math.cos(a) * (r - 30), cy + math.sin(a) * (r - 30))
        ctx.line_to(cx + math.cos(a) * (r - 70), cy + math.sin(a) * (r - 70))
        setc(ctx, (1, 1, 1))
        ctx.set_line_width(6)
        ctx.stroke()
        text_center(ctx, str(k), cx + math.cos(a) * (r - 120), cy + math.sin(a) * (r - 120) + 14, 40, (0.85, 0.85, 0.9))
    a = math.pi * (0.75 + 1.5 * clamp(v / 160))
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(a) * (r - 60), cy + math.sin(a) * (r - 60))
    setc(ctx, hexc('#ff4b4b'))
    ctx.set_line_width(14)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    text_center(ctx, f'{int(round(v))} km/h', cx, cy + 200, 60, (1, 1, 1))
    on = (t * 2) % 1 < 0.6
    ellipse(ctx, 1320, 420, 120, 120)
    fill_stroke(ctx, hexc('#ff3030') if on else hexc('#5a1414'), OUTL, 6)
    text_center(ctx, '(!)', 1320, 450, 90, (1, 1, 1) if on else (0.6, 0.4, 0.4))
    text_center(ctx, 'BRAKE', 1320, 640, 70, hexc('#ff3030') if on else hexc('#7a3030'))
    if on:
        glow(ctx, 1320, 420, 260, hexc('#ff3030'), 0.4)


def shifter_close(ctx, w, t, lt, kw):
    """Centre console: the automatic shifter goes D -> 2 -> L (engine braking). Engine stays ON."""
    interior_bg(ctx)
    rrect(ctx, 520, 120, 880, 900, 80)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, 8)
    gates = ['P', 'R', 'N', 'D', '2', 'L']
    pos = 3 + 2 * smooth((lt - 0.4) / 1.4)
    for i, g in enumerate(gates):
        y = 240 + i * 120
        on = abs(pos - i) < 0.35
        text_center(ctx, g, 1180, y + 30, 80, hexc('#ffd23f') if on else (0.6, 0.6, 0.65))
    ctx.rectangle(940, 220, 60, 640)
    setc(ctx, hexc('#0b0b10'))
    ctx.fill()
    ky = 240 + pos * 120
    ctx.move_to(970, ky)
    ctx.line_to(970, ky - 10)
    rrect(ctx, 880, ky - 90, 180, 150, 60)
    fill_stroke(ctx, hexc('#3a3d48'), OUTL, 6)
    # hand on the knob, sleeve from the upper-left edge (attached)
    ctx.move_to(-20, ky - 420)
    ctx.line_to(220, ky - 520)
    ctx.line_to(930, ky - 60)
    ctx.line_to(850, ky + 50)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    rrect(ctx, 860, ky - 110, 220, 130, 60)
    fill_stroke(ctx, SKIN, OUTL, 6)
    for k in range(1, 4):
        ctx.move_to(860 + k * 52, ky - 104)
        ctx.line_to(860 + k * 52, ky - 60)
    setc(ctx, mix(SKIN, (0, 0, 0), 0.4))
    ctx.set_line_width(5)
    ctx.stroke()
    text_center(ctx, 'ENGINE ON', 320, 980, 50, hexc('#22c35e'))


def handbrake_close(ctx, w, t, lt, kw):
    """Parking brake lever pulled up SLOWLY (not yanked)."""
    interior_bg(ctx)
    ctx.rectangle(0, 700, SW, 400)
    setc(ctx, hexc('#1c1c22'))
    ctx.fill()
    ang = -0.15 - 0.5 * smooth((lt - 0.3) / 1.8)
    px, py = 620, 820
    ctx.save()
    ctx.translate(px, py)
    ctx.rotate(ang)
    rrect(ctx, 0, -50, 700, 100, 50)
    fill_stroke(ctx, hexc('#3a3d48'), OUTL, 6)
    rrect(ctx, 520, -62, 220, 124, 60)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, 6)
    rrect(ctx, 480, -90, 220, 150, 70)
    fill_stroke(ctx, SKIN, OUTL, 6)
    for k in range(1, 4):
        ctx.move_to(480 + k * 55, -86)
        ctx.line_to(480 + k * 55, -40)
    setc(ctx, mix(SKIN, (0, 0, 0), 0.4))
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.restore()
    hx = px + math.cos(ang) * 600 + 40
    hy = py + math.sin(ang) * 600
    ctx.move_to(hx + 60, hy - 30)
    ctx.line_to(SW + 40, hy - 260)
    ctx.line_to(SW + 40, hy + 120)
    ctx.line_to(hx + 80, hy + 70)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    label(ctx, 520, 240, 'Slowly... click, click, click', '#3a3d48', 54)


def face_win(ctx, w, t, lt, kw):
    """Hero through his window, downhill street and lake behind."""
    WIN = [(240, 770), (1730, 770), (1730, 190), (600, 150)]
    path = lambda: (ctx.move_to(*WIN[0]), [ctx.line_to(*p) for p in WIN[1:]], ctx.close_path())
    ctx.save()
    path()
    ctx.clip()
    setc(ctx, hexc('#2c2d38'))
    ctx.paint()
    g = cairo.LinearGradient(0, 200, 0, 560)
    g.add_color_stop_rgb(0, *hexc('#4f9ee0'))
    g.add_color_stop_rgb(1, *hexc('#e6f3ff'))
    ctx.set_source(g)
    ctx.rectangle(560, 200, 1200, 360)
    ctx.fill()
    ctx.rectangle(560, 420, 1200, 60)
    setc(ctx, hexc('#3f7fb8'))
    ctx.fill()
    off = (t * 500) % 300
    for k in range(-1, 6):
        ellipse(ctx, 600 + k * 300 + off, 500, 120, 90)
        fill_stroke(ctx, hexc(AUTUMN[k % 5]), OUTL, 3)
    ctx.rectangle(0, 120, SW, 80)
    setc(ctx, hexc('#4a4b58'))
    ctx.fill()
    rrect(ctx, 1080, 300, 300, 700, 90)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 5)
    rrect(ctx, 1110, 250, 230, 150, 60)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 5)
    head2d(ctx, 900, 480, 175, 'hero', kw.get('expr', 'shock'), kw.get('turn', -0.5), t)
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
    path()
    setc(ctx, hexc('#15151c'))
    ctx.set_line_width(22)
    ctx.stroke()


def signs_card(ctx, w, t, lt, kw):
    setc(ctx, hexc('#2b2f3a'))
    ctx.paint()
    text_center(ctx, 'Warning signs: get your brakes checked', 960, 150, 64, (1, 1, 1))
    items = [('Soft, spongy pedal', '#ffd23f'), ('Squealing or grinding', '#ffd23f'), ('BRAKE light on', '#ff4b4b'), ('Car pulls when braking', '#ffd23f')]
    for i, (txt, col) in enumerate(items):
        if lt < 0.3 + i * 0.45:
            continue
        a = smooth((lt - 0.3 - i * 0.45) / 0.25)
        y = 300 + i * 160
        rrect(ctx, 360, y - 60, 1200, 120, 40)
        setc(ctx, (1, 1, 1), 0.08 * a)
        ctx.fill()
        ellipse(ctx, 450, y, 34, 34)
        setc(ctx, hexc(col), a)
        ctx.fill()
        text_center(ctx, txt, 1000, y + 22, 62, (1, 1, 1), a=a)


engine.SCENES.update(hb_cam=hb_cam, pedal_close=pedal_close, dash_close=dash_close, shifter_close=shifter_close,
                     handbrake_close=handbrake_close, face_win=face_win, signs_card=signs_card)

HOOK = dict(cam='down')
FRONT_W = dict(cam='down', freeze=T_FREEZE)
SAFE = dict(cam='fixed', pos=(-2.5, 1.9, 31.0), target=(4.5, 0.6, 40.5), f=900)
END = dict(cam='fixed', pos=(-3.0, 4.5, -20.0), target=(2.0, 0.0, 60.0), f=950)
defs = [
    (3.0, 'hb_cam', dict(HOOK)),
    (5.5, 'hb_cam', dict(cam='chase')),
    (7.5, 'pedal_close', dict(mode='fail')),
    (9.5, 'dash_close', dict()),
    (12.0, 'face_win', dict(expr='shock', turn=-0.5)),
    (T_R0 - 1.2, 'hb_cam', dict(FRONT_W)),
    (T_R0, 'rewind_seq', dict()),
    (17.0, 'hb_cam', dict(cam='chase')),
    (19.2, 'pedal_close', dict(mode='pump')),
    (21.6, 'shifter_close', dict()),
    (24.0, 'handbrake_close', dict()),
    (27.0, 'hb_cam', dict(cam='high', hud=False)),
    (29.5, 'hb_cam', dict(SAFE)),
    (32.0, 'signs_card', dict()),
    (DUR, 'hb_cam', dict(END)),
]
shots = build_shots(defs)
shots[6].kw.update(srcs=list(reversed(shots[1:6])), dur=shots[6].dur)
video = Video(['Your brakes fail on a steep hill.', 'What do you do?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('No brakes. Steep hill.', 300, 120, hexc('#ffd23f'), 0.2, True)),
    (3.0, 5.5, location_tag('Duluth, Minnesota')),
    (3.2, 5.5, caption('A steep hill down to Lake Superior')),
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, E[2], caption('The pedal sinks to the floor!')),
    (S[3] + 0.2, E[3], caption('...and the hill keeps speeding him up')),
    (S[4] + 0.2, E[4], caption('He freezes. Just pressing the dead pedal.')),
    (S[5] + 0.2, E[5], caption('Straight toward a red light')),
    (S[5] + 1.0, E[5], x_mark),
    (S[7], E[7], badge('RIGHT', '#22a356')),
    (S[7] + 0.2, E[7], caption('Same failure. Act fast:')),
    (S[12], E[12], badge('RIGHT', '#22a356')),
    (S[12] + 0.2, E[12], caption('Stopped safely at the curb')),
    (S[14] + 0.2, E[14], end_card('Pump. Low gear. Parking brake. Steer safe.', 'Did you know these steps? Comment!')),
]
for n, (i, txt) in enumerate(((8, 'Pump the brakes hard and fast'), (9, 'Shift to a LOW gear (keep the engine on)'),
                              (10, 'Pull the parking brake SLOWLY'), (11, 'Hazards + horn. Steer to a safe spot.')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]


# ------------------------------------------------------------------ sound
def ratchet(d, rate=6.0):
    out = np.zeros(int(d * SR) + SR)
    k = 0
    while k / rate < d:
        tt = np.arange(int(0.05 * SR)) / SR
        place(out, bp(noise(len(tt)), 2000, 6000) * np.exp(-tt / 0.006) * 0.8, k / rate)
        k += 1
    return out[:int(d * SR)]


def pedal_thunk():
    tt = np.arange(int(0.25 * SR)) / SR
    return lp(noise(len(tt)), 400) * np.exp(-tt / 0.04) * 1.2


def engine_brake(d):
    tt = np.arange(int(d * SR)) / SR
    f = 60 + 30 * np.minimum(1, tt / 0.8)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return lp(sum(np.sin(k * ph) / k for k in range(1, 7)), 700) * 0.35 * env_adsr(len(tt), 0.1, 0.3)


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur, 1.0), 0, 0.16)
    hook_sfx(m)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.14)
    m.add(pedal_thunk(), S[2] + 0.5, 0.9)
    m.add(pedal_thunk(), S[2] + 1.0, 0.9)
    m.add(heartbeat(4, 140), S[4] + 0.1, 0.8)
    m.add(horn(0.8), S[5] + 0.3, 0.7, 0.3)
    m.add(horn(0.6), S[5] + 1.2, 0.6, -0.3)
    m.add(sad_violin(), T_FREEZE + 0.05, 0.85)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    for k in range(int((E[8] - S[8]) * 2.6)):
        m.add(pedal_thunk(), S[8] + 0.1 + k / 2.6, 0.7)
    m.add(click(), S[9] + 0.6, 0.8)
    m.add(click(), S[9] + 1.3, 0.8)
    m.add(engine_brake(3.0), S[9] + 0.7, 0.8)
    m.add(ratchet(1.8, 5.0), S[10] + 0.3, 0.6)
    for k in range(5):
        m.add(horn(0.25), S[11] + 0.2 + k * 0.4, 0.5)
    indicator(m, 21.0, 30.0, 0.35, 0.0)
    m.add(brake_squeal(1.2), 24.0, 0.3)
    for i in (8, 9, 10, 11):
        m.add(pop(), S[i] + 0.15, 0.6)
    m.add(chime(), S[12] + 0.4, 0.7)
    for i in range(4):
        m.add(pop(), S[13] + 0.3 + i * 0.45, 0.6)
    m.add(success_jingle(), S[14] + 0.3, 0.8)
    return m.out(video.dur)


def verify():
    zf = HERO_W.z(T_FREEZE)
    print('wrong: speed at freeze', round(SPD_W(T_FREEZE) * 3.6), 'km/h | front at z', round(zf + 2.2, 1), '| crosswalk starts 136.8 ->',
          round(136.8 - zf - 2.2, 1), 'm to go')
    print('   pedestrians on the crosswalk at freeze:', [round(p.x(T_FREEZE), 1) for p in PEDS[:3]])
    print('right: stops at z', round(Z_STOP_R, 1), 'x', X_R(30), '(curb 6.0, car edge', round(X_R(30) + 0.92, 2), ')',
          '| parked cars at z 95/108 and -70/-55 ->', round(95 - 2.2 - (Z_STOP_R + 2.2), 1), 'm clear ahead')
    for t in np.arange(T_FR, 30, 0.1):
        x, z, h = HERO_R.pose(t)
        for p_ in PARKED:
            if abs(p_.z(t) - z) < 4.6 and abs(p_.pose(t)[0] - x) < 1.95:
                print('   CONFLICT with parked car at', t)
    print('   distance from failure to stop', round(Z_STOP_R - (-30), 1), 'm')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        run(video, sound, 'brakes.mp4')
