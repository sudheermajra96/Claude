"""Funny lesson: don't drive on the sidewalk to skip a traffic jam. Philadelphia, Pennsylvania. SQUARE (1:1) scene.

World: +Z = north (travel). Our lane x 0..3.5 (centre 1.75), oncoming lane x -3.5..0. Right sidewalk x 3.5..7.2,
brick rowhouses from x 7.6 (stoops in front). Cross street (and the red light causing the jam) at z 140..150.
The impatient driver bumps up onto the sidewalk (x 5.3) to skip the queue: people jump aside, trash cans fly,
a police officer waits at the corner -> ticket (PA Vehicle Code 3703, driving upon sidewalk). Then the light turns
green and every car he skipped drives past him: time saved = 0 s. Lesson + the right way (wait your turn).
"""
import math
import random

import cairo
import numpy as np

from mkit import *
from truckkit import draw_car_round
from peoplekit import *
import citykit
import engine
import euro
import street
from street import officer, ticket_paper, paper_rustle, paper_rip, siren_whoop
from life2 import boing
from sqkit import *

DUR = 32.0
T_GREEN = 19.4
Z_STOPLINE = 44.0
SIDE_X = 5.3
T_R0 = 99.0


# ------------------------------------------------------------------ jam
def jam_speed(i):
    t0 = T_GREEN + 0.45 * i
    return Key([(0, 0.0), (t0, 0.0), (t0 + 2.8, 9.0), (99, 9.0)], 'lin')


N_JAM = 9
JAM_Z = [41.5 - 6.8 * i for i in range(7)] + [-16.0, -22.8]     # front car first; two more behind the hero
JAM_COLS = ['#3a7bd5', '#f2a541', '#c9c9d6', '#37b26c', '#1c1c22', '#7a4fd0', '#f4f4f6', '#2f6f73', '#d8c3a0']
JAM = [Track(1.75, jam_speed(i), 0.0, z, JAM_COLS[i % len(JAM_COLS)]) for i, z in enumerate(JAM_Z)]

# ------------------------------------------------------------------ hero (the impatient one)
SPD = Key([(0, 0.0), (8.5, 0.0), (9.0, 3.6), (9.9, 4.2), (10.6, 10.0), (12.9, 10.0), (13.2, 6.0), (13.8, 6.0), (15.0, 0.0), (99, 0.0)], 'lin')
HERO_TR = Track(0.0, SPD, 0.0, -9.0, '#e23b3b')


def hero_x(t):
    z = HERO_TR.z(t)
    u = clamp((z - (-9.0)) / 5.0)                 # lateral move happens over the first 5 m of travel
    return 1.75 + (SIDE_X - 1.75) * smooth(u)


Z_CANS = 31.0
T_CAN = next(t for t in np.arange(8.5, 20, 0.005) if HERO_TR.z(t) + 2.25 > Z_CANS - 0.2)


def hero_pose(t):
    x, z = hero_x(t), HERO_TR.z(t)
    dx = hero_x(t + 0.1) - hero_x(t - 0.1)
    dz = HERO_TR.z(t + 0.1) - HERO_TR.z(t - 0.1)
    h = math.atan2(dx, dz) if dz > 0.02 else 0.0
    return x, z, h


def bump(t):
    """Curb hop when the wheels climb the curb + the can crash jolt."""
    out = 0.0
    for tc in (9.05, 9.35):
        u = t - tc
        if 0 <= u < 0.35:
            out += 0.12 * math.sin(math.pi * u / 0.35)
    u = t - T_CAN
    if 0 <= u < 0.4:
        out += 0.06 * math.sin(math.pi * u / 0.4)
    return out


def hero_expr(t):
    if t < 6.8:
        return 'annoyed'
    if t < 11.0:
        return 'smug'
    if t < 15.6:
        return 'shock'
    return 'worried'


class Hero:
    col = '#e23b3b'

    def pose(self, t):
        return hero_pose(t)

    def speed(self, t):
        return SPD(t)

    def steer(self, t):
        return clamp((hero_pose(t + 0.2)[2] - hero_pose(t - 0.2)[2]) * 3, -1.6, 1.6)

    def blink(self, t):
        return None

    def brake(self, t):
        return 1.0 if 14.2 < t < 99 else 0.0

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        x, z, h = hero_pose(t)
        hop = bump(t)

        def occ(ctx, view, Lf, h_):
            person3d(ctx, view, Lf, -0.38, 0.05, 'hero', 0.0, hero_expr(t))

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, None, True)
                return
            ctx.save()
            if hop:
                ctx.translate(0, -hop * (view.scale((x, 0.8, z)) or 0))
            draw_car_round(ctx, view, x, z, h, self.col, t, None, self.brake(t), occ=occ)
            ctx.restore()
        return [((x, 0.8, z), fn)]


HERO = Hero()


def t_when(zz):
    return next(t for t in np.arange(8.5, 20, 0.005) if HERO_TR.z(t) + 2.3 > zz)


# ------------------------------------------------------------------ pedestrians that jump aside
class YLift:
    def __init__(self, v, dy):
        self.v, self.dy, self.ortho = v, dy, v.ortho
        self.pos = (v.pos[0], v.pos[1] - dy, v.pos[2])
        if v.ortho:
            self.s = v.s

    def pt(self, P):
        return self.v.pt((P[0], P[1] + self.dy, P[2]))

    def scale(self, P):
        return self.v.scale((P[0], P[1] + self.dy, P[2]))

    def depth(self, P):
        return self.v.depth((P[0], P[1] + self.dy, P[2]))


class JumpPed:
    def __init__(self, x0, z0, vz, x1, t_jump, top, pants='#2b3a63', hair='#3a2316', skin='#e8b48f', kid=False, wave=None,
                 items=None):
        self.x0, self.z0, self.vz, self.x1, self.tj = x0, z0, vz, x1, t_jump
        self.p = Ped(self.x, self.z, top=top, pants=pants, hair=hair, skin=skin, kid=kid, wave=wave)
        self.items_kind = items

    def x(self, t):
        if self.tj is None or t < self.tj:
            return self.x0
        return self.x0 + (self.x1 - self.x0) * smooth((t - self.tj) / 0.45)

    def z(self, t):
        tt = t if self.tj is None else min(t, self.tj)
        return self.z0 + self.vz * tt

    def hop(self, t):
        if self.tj is None:
            return 0.0
        u = t - self.tj
        return 0.55 * math.sin(math.pi * u / 0.45) if 0 <= u < 0.45 else 0.0

    def draw(self, ctx, view, t):
        h = self.hop(t)
        self.p.draw(ctx, YLift(view, h) if (h and not view.ortho) else view, t)
        if self.items_kind and self.tj is not None and t > self.tj and not view.ortho:
            self.flying(ctx, view, t)

    def flying(self, ctx, view, t):
        u = t - self.tj
        rnd = random.Random(hash(self.items_kind) % 1000)
        n = 6 if self.items_kind == 'groceries' else 5
        for k in range(n):
            vx, vy, vz = rnd.uniform(-1.5, 1.0), rnd.uniform(3.0, 5.0), rnd.uniform(-1.0, 1.5)
            tt = min(u, 2 * vy / 9.8)
            P = (self.x0 + vx * tt, max(0.05, 1.2 + vy * tt - 4.9 * tt * tt), self.z(self.tj) + vz * tt)
            p, s = view.pt(P), view.scale(P)
            if not p or not s:
                continue
            if self.items_kind == 'groceries':
                col = ['#e0393e', '#f2c230', '#56b38a', '#e0393e', '#c98b4a', '#f2a541'][k]
                ellipse(ctx, p[0], p[1], 0.1 * s, 0.1 * s)
                fill_stroke(ctx, hexc(col), OUTL, max(1, s * 0.015))
            else:
                ellipse(ctx, p[0], p[1], 0.07 * s, 0.05 * s)
                setc(ctx, hexc('#6b4a2f'), 0.9)
                ctx.fill()


LADY = JumpPed(SIDE_X + 0.3, 6.0, 0.9, 7.05, None, '#ff6b9d', hair='#5a2a1e', skin='#e8b48f', items='groceries')
MAN = JumpPed(SIDE_X - 0.5, 34.0, -1.2, 3.75, None, '#56b38a', hair='#1d1613', skin='#9c6a4a', items='coffee')
KID = JumpPed(SIDE_X + 0.6, 52.0, -2.4, 7.1, None, '#f2c230', pants='#3a7bd5', kid=True)
OFFICER = JumpPed(SIDE_X, 39.6, 0.0, SIDE_X, None, '#1f3a6b', pants='#16294d', hair='#16294d', skin='#c98d63',
                  wave=lambda t: 1.0 if t > 13.0 else 0.0)


def solve_jump(p, lead):
    """Jump `lead` seconds before the car's front reaches the person."""
    for t in np.arange(8.5, 20, 0.01):
        if HERO_TR.z(t) + 2.3 > p.z0 + p.vz * t - 1.0:
            return t - lead
    return None


for p_, lead in ((LADY, 0.75), (MAN, 0.65), (KID, 0.85)):
    p_.tj = solve_jump(p_, lead)
WALKERS = [Ped(const(-5.4), Key([(0, z), (40, z + v * 40)], 'lin'), top=c, skin=sk, hair='#1d1613')
           for z, v, c, sk in ((10, 1.2, '#7a4fd0', '#c08a62'), (60, -1.3, '#e05d5d', '#e8b48f'), (120, 1.0, '#3a7bd5', '#9c6a4a'))]
PEDS = [LADY, MAN, KID, OFFICER] + WALKERS


# ------------------------------------------------------------------ trash cans that fly
_rc = random.Random(5)
CANS = [dict(x=x, z=Z_CANS + dz, col=c, vz=_rc.uniform(5, 8), vx=_rc.uniform(-0.8, 2.2), vy=_rc.uniform(2.5, 4.0), spin=_rc.uniform(-9, 9))
        for x, dz, c in ((4.7, 0.0, '#3a5f8a'), (5.5, 0.3, '#3a7a45'), (6.3, -0.2, '#3a5f8a'))]


class Cans:
    col = '#ccc'

    def visible(self, t):
        return True

    def pose(self, t):
        return 0, 0, 0

    def items(self, ctx, view, t):
        out = []
        for c in CANS:
            u = t - T_CAN
            if u < 0:
                x, y, z, ang = c['x'], 0.0, c['z'], 0.0
            else:
                tf = 2 * c['vy'] / 9.8
                tt = min(u, tf)
                x = c['x'] + c['vx'] * tt
                z = c['z'] + c['vz'] * tt + (c['vz'] * 0.25 * min(u - tf, 1.0) if u > tf else 0)
                y = max(0.0, c['vy'] * tt - 4.9 * tt * tt)
                ang = c['spin'] * tt + (math.pi / 2 if u > tf else 0)

            def fn(c=c, x=x, y=y, z=z, ang=ang):
                if view.ortho:
                    p = view.pt((x, 0, z))
                    ellipse(ctx, p[0], p[1], 0.35 * view.s, 0.35 * view.s)
                    fill_stroke(ctx, hexc(c['col']), OUTL, 2)
                    return
                p, s = view.pt((x, y + 0.5, z)), view.scale((x, y + 0.5, z))
                if not p or not s:
                    return
                ctx.save()
                ctx.translate(*p)
                ctx.rotate(ang)
                rrect(ctx, -0.32 * s, -0.5 * s, 0.64 * s, 1.0 * s, 0.08 * s)
                fill_stroke(ctx, hexc(c['col']), OUTL, max(1, s * 0.02))
                for k in range(3):
                    ctx.move_to(-0.32 * s, (-0.3 + 0.3 * k) * s)
                    ctx.line_to(0.32 * s, (-0.3 + 0.3 * k) * s)
                setc(ctx, mix(hexc(c['col']), (0, 0, 0), 0.3))
                ctx.set_line_width(max(1, s * 0.015))
                ctx.stroke()
                ellipse(ctx, 0, -0.52 * s, 0.36 * s, 0.1 * s)
                fill_stroke(ctx, mix(hexc(c['col']), (1, 1, 1), 0.2), OUTL, max(1, s * 0.02))
                ctx.restore()
            out.append(((x, y + 0.5, z), fn))
        # garbage bits
        u = t - T_CAN
        if 0 <= u < 3 and not view.ortho:
            rnd = random.Random(3)
            for k in range(14):
                vx, vy, vz = rnd.uniform(-1.5, 2.5), rnd.uniform(2, 5), rnd.uniform(3, 9)
                tt = min(u, 2 * vy / 9.8)
                P = (5.4 + vx * tt, max(0.03, 0.8 + vy * tt - 4.9 * tt * tt), Z_CANS + vz * tt)

                def bit(P=P, k=k):
                    p, s = view.pt(P), view.scale(P)
                    if p and s:
                        ctx.rectangle(p[0] - 0.08 * s, p[1] - 0.05 * s, 0.16 * s, 0.1 * s)
                        fill_stroke(ctx, hexc(['#f4f4f6', '#c98b4a', '#9fb3a0', '#e0393e'][k % 4]), OUTL, max(1, s * 0.01))
                out.append((P, bit))
        return out


# ------------------------------------------------------------------ Philadelphia rowhouse street
BRICK = ['#a35d43', '#8a4b38', '#9c4f3f', '#b56f52', '#7d3f30', '#c98b6b']


class Philly:
    sky = ('#5fb4f2', '#e2f3ff')

    def __init__(self):
        self.ground_col = hexc('#8aa760')
        r = random.Random(21)
        self.rows = []
        for sx in (-1, 1):
            z = -200.0
            while z < 400:
                if 38 < z + 7 and z < 59:
                    z = 59.0
                    continue
                self.rows.append((sx, z, z + 6.5, r.uniform(9, 11.5), r.choice(BRICK)))
                z += 6.5
        self.trees = [(sx * 3.95, z) for sx in (-1, 1) for z in np.arange(-150, 400, 19.0) + 4.0 if not 40 < z < 62 and not (sx > 0 and -32 < z < 12)]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        towers(ctx, view, 1500, -300, 300, 18, 80, 260, seed=33, base='#8f9aa8')

    def ground(self, ctx, view, t):
        gquad(ctx, view, -7.6, 7.6, -600, 900, C_WALK)
        gquad(ctx, view, -600, 600, 46.9, 58.4, C_WALK)
        gquad(ctx, view, -3.5, 3.5, -600, 900, C_ASPH)
        gquad(ctx, view, -600, 600, 47.5, 57.5, C_ASPH)
        gquad(ctx, view, -0.18, -0.06, -600, 44, C_YEL, 0.01)
        gquad(ctx, view, 0.06, 0.18, -600, 44, C_YEL, 0.01)
        gquad(ctx, view, -0.18, -0.06, 57.5, 900, C_YEL, 0.01)
        gquad(ctx, view, 0.06, 0.18, 57.5, 900, C_YEL, 0.01)
        gquad(ctx, view, 0.2, 3.5, Z_STOPLINE, Z_STOPLINE + 0.5, C_LINE, 0.012)
        zebra(ctx, view, -3.5, 3.5, 44.6, 46.8, 'x')
        if not view.ortho:
            for sx in (-1, 1):
                fill_poly(ctx, view, [(sx * 3.5, 0, -600), (sx * 3.5, 0, 900), (sx * 3.5, 0.15, 900), (sx * 3.5, 0.15, -600)], hexc('#d9d3c6'), OUTL, 1)
            # sidewalk slab joints
            ez = view.pos[2]
            for k in range(int((ez - 20) // 1.8), int((ez + 120) // 1.8)):
                gquad(ctx, view, 3.6, 7.2, k * 1.8, k * 1.8 + 0.05, hexc('#b9b2a5'), 0.005)

    def objects(self, ctx, view, t):
        out = []
        ez = view.pos[2] if not view.ortho else view.zc
        for sx, z0, z1, h, col in self.rows:
            if ez - 60 < z0 < ez + 500:
                x0 = sx * 7.6
                x1 = sx * 18.0
                out.append(((sx * 12, h / 2, (z0 + z1) / 2), lambda a=(min(x0, x1), max(x0, x1), z0, z1, h, col): rowhouse(ctx, view, *a)))
        for x, z in self.trees:
            if ez - 60 < z < ez + 500:
                out.append(((x, 1.5, z), lambda x=x, z=z: tree3(ctx, view, x, z, 0.85 if not view.ortho else 0.4, int(abs(z)) % 3)))
        state = 'green' if t >= T_GREEN else 'red'
        out.append(((3.9, 3.5, 47.2), lambda: (pole(ctx, view, 3.9, 47.2), signal_head(ctx, view, 3.9, 3.6, 47.2, math.pi, state))))
        out.append(((4.0, 0.4, 20.0), lambda: hydrant(ctx, view, 4.0, 20.0)))
        return out


def pole(ctx, view, x, z):
    if view.ortho:
        return
    a, b = view.pt((x, 0, z)), view.pt((x, 3.0, z))
    if a and b:
        ctx.move_to(*a)
        ctx.line_to(*b)
        setc(ctx, hexc('#3a3d48'))
        ctx.set_line_width(max(2, (view.scale((x, 1, z)) or 10) * 0.12))
        ctx.stroke()


def hydrant(ctx, view, x, z):
    if view.ortho:
        return
    p, s = view.pt((x, 0.4, z)), view.scale((x, 0.4, z))
    if p and s:
        rrect(ctx, p[0] - 0.15 * s, p[1] - 0.35 * s, 0.3 * s, 0.7 * s, 0.08 * s)
        fill_stroke(ctx, hexc('#e0393e'), OUTL, max(1, s * 0.02))
        ellipse(ctx, p[0], p[1] - 0.38 * s, 0.17 * s, 0.1 * s)
        fill_stroke(ctx, hexc('#e0393e'), OUTL, max(1, s * 0.02))


def rowhouse(ctx, view, x0, x1, z0, z1, h, col):
    Lf = lambda a, b, c: (a, b, c)
    c = hexc(col)
    vis = lbox(ctx, view, Lf, 0.0, x0, x1, 0, h, z0, z1,
               {'front': c, 'back': c, 'left': mix(c, (0, 0, 0), 0.1), 'right': mix(c, (0, 0, 0), 0.04), 'top': mix(c, (0, 0, 0), 0.25)}, 2)
    if view.ortho:
        return
    face = 'left' if x0 > 0 else 'right'
    if face in vis:
        dx = x0 - 0.02 if x0 > 0 else x1 + 0.02
        for fl in range(2):
            for k in range(2):
                face_rect(ctx, view, Lf, face, z0 + 0.8 + k * 3.0, z0 + 2.4 + k * 3.0, 4.0 + fl * 3.0, 5.8 + fl * 3.0, dx, hexc('#2d3f55'))
        face_rect(ctx, view, Lf, face, z0 + 4.4, z0 + 5.6, 0.4, 2.6, dx, hexc('#5b3a26'))
        face_rect(ctx, view, Lf, face, z0 + 0.8, z0 + 2.6, 1.0, 2.6, dx, hexc('#2d3f55'))
        face_rect(ctx, view, Lf, face, z0 + 0.2, z1 - 0.2, h - 0.6, h - 0.3, dx, hexc('#f4efe6'))
        # stoop (marble steps) in front of the door
        sx = 1 if x0 > 0 else -1
        allc = lambda cc: {k: cc for k in ('front', 'back', 'left', 'right', 'top')}
        xs = (x0 - 0.5, x0) if x0 > 0 else (x1, x1 + 0.5)
        lbox(ctx, view, Lf, 0.0, xs[0], xs[1], 0, 0.4, z0 + 4.2, z0 + 5.8, allc(hexc('#e9e6df')), 1.5)


world = SegWorld(DUR, [hook_seg(0, 3.0, LADY.tj - 1.2, HERO, JAM + [Cans()], PEDS),
                       (3.0, 99, HERO, JAM + [Cans()], PEDS)], Philly(), 'mph')
world.police_flash = lambda t: 0.0


# ------------------------------------------------------------------ scenes (square canvas)
def s_cam(ctx, w, t, lt, kw):
    tf = t + kw.get('dt', 0.0)
    x, z, h = hero_pose(tf)
    m = kw['cam']
    if m == 'fixed':
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000), cy=SQ_CY)
    elif m == 'chase':
        view = TCam((x * 0.8 + 0.4, 6.8, z - 11.0), 0.0, 0.34, 1000, cy=SQ_CY)
    elif m == 'high':
        view = TCam((2.0, 15.0, z - 16.0), 0.0, 0.55, 1000, cy=SQ_CY - 80)
    elif m == 'ahead':
        view = look_at((6.6, 1.3, z + kw.get('ahead', 14.0)), (4.6, 1.1, z), kw.get('f', 950), cy=SQ_CY)
    draw_scene(ctx, view, w, tf)
    if m == 'chase' and kw.get('hud', True):
        sq_hud(ctx, w, tf)
    if kw.get('post'):
        kw['post'](ctx, view, tf, lt)


def window_face(ctx, w, t, lt, kw):
    """Hero through his window (seen from the sidewalk side): impatient, then the 'idea', or calm (right way)."""
    setc(ctx, hexc('#e23b3b'))
    ctx.paint()
    ctx.save()
    ctx.translate(0, 420)
    WIN = [(240, 770), (1730, 770), (1730, 190), (600, 150)]
    path = lambda: (ctx.move_to(*WIN[0]), [ctx.line_to(*p) for p in WIN[1:]], ctx.close_path())
    ctx.save()
    path()
    ctx.clip()
    setc(ctx, hexc('#2c2d38'))
    ctx.paint()
    g = cairo.LinearGradient(0, 200, 0, 560)
    g.add_color_stop_rgb(0, *hexc('#5fb4f2'))
    g.add_color_stop_rgb(1, *hexc('#e2f3ff'))
    ctx.set_source(g)
    ctx.rectangle(560, 200, 1200, 360)
    ctx.fill()
    for k in range(6):
        ctx.rectangle(560 + k * 220, 280 - 40 * (k % 2), 200, 300)
        fill_stroke(ctx, hexc(BRICK[k % 6]), OUTL, 3)
    ctx.rectangle(0, 120, SW, 80)
    setc(ctx, hexc('#4a4b58'))
    ctx.fill()
    rrect(ctx, 1080, 300, 300, 700, 90)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 5)
    rrect(ctx, 1110, 250, 230, 150, 60)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 5)
    expr = kw['expr'](lt) if callable(kw.get('expr')) else kw.get('expr', 'annoyed')
    head2d(ctx, 900, 480, 175, 'hero', expr, kw.get('turn', 0.0), t)
    setc(ctx, (0.75, 0.88, 1.0), 0.08)
    ctx.paint()
    ctx.restore()
    body = hexc('#e23b3b')
    ctx.rectangle(-40, -500, SW + 80, SH + 1000)
    path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    setc(ctx, body)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    path()
    setc(ctx, hexc('#15151c'))
    ctx.set_line_width(22)
    ctx.stroke()
    rrect(ctx, 1450, 850, 170, 40, 18)
    fill_stroke(ctx, mix(body, (0, 0, 0), 0.25), OUTL, 4)
    if kw.get('idea') is not None and lt > kw['idea']:
        a = smooth((lt - kw['idea']) / 0.2)
        bx, by = 900, 60 - 30 * a
        glow(ctx, bx, by, 220, hexc('#ffe14d'), 0.8 * a)
        ellipse(ctx, bx, by, 70 * a, 80 * a)
        fill_stroke(ctx, hexc('#ffe14d'), OUTL, 5)
        rrect(ctx, bx - 32 * a, by + 70 * a, 64 * a, 40 * a, 8)
        fill_stroke(ctx, hexc('#9fa6b2'), OUTL, 4)
    if kw.get('clock'):
        cx, cy, r = 1500, -230, 150
        ellipse(ctx, cx, cy, r, r)
        fill_stroke(ctx, (1, 1, 1), OUTL, 8)
        a = t * 3
        ctx.move_to(cx, cy)
        ctx.line_to(cx + math.sin(a) * r * 0.8, cy - math.cos(a) * r * 0.8)
        ctx.move_to(cx, cy)
        ctx.line_to(cx + math.sin(a / 12) * r * 0.5, cy - math.cos(a / 12) * r * 0.5)
        setc(ctx, OUTL)
        ctx.set_line_width(10)
        ctx.stroke()
        label(ctx, cx, cy + r + 80, kw['clock'], '#e0393e', 50)
    ctx.restore()


def ticket_scene(ctx, w, t, lt, kw):
    """Officer at the window: writes it up, then the ticket close-up."""
    g = cairo.LinearGradient(0, 0, 0, SH)
    g.add_color_stop_rgb(0, *hexc('#5fb4f2'))
    g.add_color_stop_rgb(0.35, *hexc('#e2f3ff'))
    ctx.set_source(g)
    ctx.paint()
    for k in range(5):
        ctx.rectangle(-60 + k * 420, 250 - 60 * (k % 2), 400, 1200)
        fill_stroke(ctx, hexc(BRICK[k % 6]), OUTL, 4)
        for j in range(3):
            ctx.rectangle(-10 + k * 420, 380 + j * 260 - 60 * (k % 2), 120, 160)
            ctx.rectangle(160 + k * 420, 380 + j * 260 - 60 * (k % 2), 120, 160)
        setc(ctx, hexc('#2d3f55'))
        ctx.fill()
    ctx.rectangle(0, 1300, SW, 700)
    setc(ctx, C_WALK)
    ctx.fill()
    officer(ctx, 760 + math.sin(t * 1.3) * 6, 1180, 1.55, t, 'write', lt, 'flat')
    if lt > 1.2:
        u = smooth((lt - 1.2) / 0.35)
        ticket_paper(ctx, 1340, 980, 0.9 + 0.35 * u, -0.06, lt - 1.2, 0.8)
    # our car's window frame at the bottom
    ctx.rectangle(-10, 1640, SW + 20, 300)
    setc(ctx, hexc('#c23b3b'))
    ctx.fill()
    ctx.rectangle(-10, 1620, SW + 20, 30)
    setc(ctx, hexc('#1b1b24'))
    ctx.fill()


def top_lesson(ctx, w, t, lt, kw):
    view = HTop(1.5, 18.0, 30.0, 960, 960)
    draw_scene(ctx, view, w, t)
    a = smooth(lt / 0.4)
    pts = view.poly([(3.5, 0, -12), (7.2, 0, -12), (7.2, 0, 44), (3.5, 0, 44)])
    poly(ctx, pts)
    setc(ctx, hexc('#ff4b4b'), 0.3 * a)
    ctx.fill()
    p = view.pt((5.3, 0, 18))
    label(ctx, p[0], p[1] + 150, 'SIDEWALK = for PEOPLE', '#e0393e', 56)
    q = view.pt((1.75, 0, 18))
    label(ctx, q[0], q[1] - 120, 'Cars wait here', '#22a356', 52)
    # little people icons on the sidewalk: walker, wheelchair, stroller, kid


engine.SCENES.update(s_cam=s_cam, window_face=window_face, ticket_scene=ticket_scene, top_lesson=top_lesson)
street.TICKET_TEXT = 'Drove on the SIDEWALK'

Z_LADY = LADY.z(LADY.tj)
HOOK = dict(cam='fixed', pos=(6.4, 3.2, Z_LADY + 14.0), target=(4.6, 0.9, Z_LADY - 6.0), f=900)
AHEAD = dict(cam='fixed', pos=(6.7, 1.4, 37.0), target=(4.8, 1.0, 12.0), f=950)
SIDE = dict(cam='fixed', pos=(6.6, 2.3, 42.5), target=(5.0, 0.9, 30.0), f=900)
CORNER = dict(cam='fixed', pos=(-1.5, 4.2, 18.0), target=(4.0, 1.0, 40.0), f=950)
defs = [
    (3.0, 's_cam', HOOK),
    (6.0, 's_cam', dict(cam='chase')),
    (8.4, 'window_face', dict(expr=lambda lt: 'annoyed' if lt < 1.0 else 'smug', idea=1.0, clock='LATE!')),
    (11.0, 's_cam', dict(cam='chase')),
    (13.4, 's_cam', AHEAD),
    (15.6, 's_cam', SIDE),
    (18.8, 'ticket_scene', dict()),
    (22.4, 's_cam', CORNER),
    (25.4, 'top_lesson', dict()),
    (28.4, 'window_face', dict(expr='whistle', turn=-0.3)),
    (DUR, 's_cam', dict(cam='high')),
]
shots = build_shots(defs)
video = SquareVideo(["He's late. Traffic is jammed.", 'So he takes a "shortcut"...'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]


def saved_counter(ctx, lt, d):
    a = smooth(lt / 0.3)
    rrect(ctx, 460, 120, 1000, 200, 50)
    setc(ctx, (0, 0, 0), 0.65 * a)
    ctx.fill()
    text_center(ctx, 'Time saved:', 960, 200, 64, (1, 1, 1), a=a)
    sc = 1 + 0.2 * math.sin(lt * 8) * (1 if lt > 0.6 else 0)
    ctx.save()
    ctx.translate(960, 290)
    ctx.scale(sc, sc)
    text_center(ctx, '0 seconds', 0, 0, 84, hexc('#ff4b4b'), a=a)
    ctx.restore()


video.overlays = [
    (0.0, 3.0, big_text('Shortcut?!', 260, 160, hexc('#ffd23f'), 0.2, True)),
    (3.0, 6.0, location_tag('Philadelphia, Pennsylvania')),
    (3.2, 6.0, sq_caption('Stuck in traffic... and late')),
    (S[2] + 1.1, E[2], sq_caption('Then he gets an "idea"...')),
    (S[3] + 0.3, E[3], sq_caption('Up onto the SIDEWALK!')),
    (S[4] + 0.2, E[4], sq_caption('People jump out of the way!')),
    (S[5] + 0.2, E[5], sq_caption("CRASH! ...and guess who's waiting")),
    (S[6] + 0.2, E[6], sq_caption('PA Vehicle Code 3703: driving on a sidewalk', 66)),
    (S[7], E[7], saved_counter),
    (S[7] + 0.6, E[7], sq_caption('The light turns green... everyone passes him')),
    (S[8], E[8], badge('LESSON', '#e0393e')),
    (S[8] + 0.2, E[8], sq_caption('Kids, wheelchairs, strollers. Never drive there.', 70)),
    (S[9], E[9], badge('RIGHT WAY', '#22a356')),
    (S[9] + 0.2, E[9], sq_caption('Wait your turn. Late is better than sorry.', 74)),
    (S[10] + 0.2, E[10], end_card('The sidewalk is for PEOPLE.', 'Ever seen someone do this? Comment!')),
]


# ------------------------------------------------------------------ sound
def police_whistle(d=0.9):
    tt = np.arange(int(d * SR)) / SR
    f = 2900 * (1 + 0.04 * np.sign(np.sin(2 * np.pi * 28 * tt)))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_adsr(len(tt), 0.01, 0.08) * 0.35


def clatter(d=1.4):
    out = np.zeros(int(d * SR) + SR)
    rnd = np.random.default_rng(1)
    for k in range(9):
        tt = np.arange(int(0.4 * SR)) / SR
        f = rnd.uniform(500, 1600)
        s = (np.sin(2 * np.pi * f * tt) + 0.6 * np.sin(2 * np.pi * f * 2.7 * tt)) * np.exp(-tt / 0.08) + bp(noise(len(tt)), 1000, 5000) * np.exp(-tt / 0.03)
        place(out, s * 0.35, rnd.uniform(0, d * 0.7))
    return out[:int(d * SR)]


def tick_tock(d):
    out = np.zeros(int(d * SR) + SR)
    k = 0
    while k * 0.5 < d:
        tt = np.arange(int(0.05 * SR)) / SR
        place(out, np.sin(2 * np.pi * (1800 if k % 2 else 1300) * tt) * np.exp(-tt / 0.01) * 0.4, k * 0.5)
        k += 1
    return out[:int(d * SR)]


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur, 1.0), 0, 0.22)
    m.add(engine_idle(video.dur), 0, 0.12)
    hook_sfx(m)
    m.add(whoosh(0.8, 0.4), 1.6, 0.7)
    m.add(clatter(0.8), 2.2, 0.6)
    for k, tt in enumerate((3.6, 4.4, 5.5, 7.0)):
        m.add(horn(0.4 + 0.2 * (k % 2)), tt, 0.35, 0.4 - 0.25 * k)
    m.add(tick_tock(2.4), S[2], 0.6)
    m.add(bell(midi(88), 0.7), S[2] + 1.0, 0.8)
    m.add(boing(), 9.25, 0.8)
    m.add(boing(), 9.55, 0.6)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.12)
    for p_ in (LADY, MAN, KID):
        m.add(whoosh(0.6, 0.3), p_.tj, 0.6)
    m.add(thud(), LADY.tj + 0.9, 0.5)
    m.add(clatter(1.6), T_CAN, 1.0)
    m.add(impact(), T_CAN, 0.5)
    m.add(police_whistle(1.0), 13.6, 0.9)
    m.add(brake_squeal(1.2), 14.3, 0.4)
    m.add(siren_whoop(2), 15.7, 0.5)
    m.add(paper_rustle(1.2), S[6] + 0.3, 0.8)
    m.add(paper_rip(), S[6] + 2.6, 0.8)
    for k in range(6):
        m.add(horn(0.18), T_GREEN + 1.0 + k * 0.45, 0.35, 0.5 - 0.15 * k)
    m.add(car_pass(1.6, 0.5, 95), T_GREEN + 1.2, 0.5, np.linspace(-0.5, 0.5, int(1.6 * SR)))
    m.add(sad_trombone(), S[7] + 1.3, 0.6)
    m.add(chime(), S[9] + 0.3, 0.6)
    m.add(success_jingle(), S[10] + 0.3, 0.8)
    return m.out(video.dur)


def verify():
    worst = 99
    for t in np.arange(8.0, 16.0, 0.01):
        x, z, h = hero_pose(t)
        for c in JAM:
            cx, cz, _ = c.pose(t)
            lat = abs(cx - x) - 1.84 - 0.12
            lon = abs(cz - z) - 4.4
            if lat < 0 and lon < worst:
                worst = lon
    print('hero vs jam cars (min bumper gap while lanes overlap):', round(worst, 2))
    print('hero on sidewalk x =', round(hero_x(11), 2), '| clearance to jam cars', round(hero_x(11) - 0.92 - (1.75 + 0.92), 2),
          '| to house fronts', round(7.6 - 0.5 - (hero_x(11) + 0.92), 2), '(stoops)')
    for nm, p_ in (('lady', LADY), ('man', MAN), ('kid', KID)):
        tp = next(t for t in np.arange(8.5, 20, 0.01) if HERO_TR.z(t) + 2.3 > p_.z(t) - 0.3)
        print(f'   {nm}: jumps at {p_.tj:.2f}, car reaches at {tp:.2f}, lateral clearance then', round(abs(p_.x(tp) - hero_x(tp)) - 0.92 - 0.3, 2))
    print('cans hit at', round(T_CAN, 2), '| hero stops at z', round(HERO_TR.z(20), 1), 'front', round(HERO_TR.z(20) + 2.2, 1),
          '| officer at', OFFICER.z0, '->', round(OFFICER.z0 - HERO_TR.z(20) - 2.2, 1), 'm')
    print('jam cars passing the stopped hero at x 1.75: lateral clearance', round(hero_x(20) - 0.92 - (1.75 + 0.92), 2))


if __name__ == '__main__':
    import sys
    square_mode()
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'check':
        check_sheet(video, sys.argv[1])
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        video.render(sys.argv[1] if len(sys.argv) > 1 else 'sidewalk.mp4', sound(), (sys.argv[1] if len(sys.argv) > 1 else 'sw') + '_work')
