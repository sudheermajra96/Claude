"""Funny distracted-driving short: he stares at the smiling lady in the next car and bumps the curb.
Miami Beach, Florida. US: drive on the right, driver sits on the LEFT.

World: +Z = travel (north), +X = right. Two northbound lanes: lady's car x = 1.75 (left lane), our car x = 5.25
(right lane). Curb face at x = 7.0, then the sidewalk, palms, sand and the Atlantic on the right; art deco hotels left.
Occupants are drawn ONLY inside the window glass (clipped in truckkit.draw_car_round(occ=...)), and the close-ups are
drawn through a window opening that clips everything inside it, so no head or hand can stick out of a car.
"""
import math
import random

import cairo
import numpy as np

from mkit import *
from truckkit import draw_car_round
from life2 import boing, sparkle
import citykit
import engine
from peoplekit import *

DUR = 29.0
T_HIT = 19.25
SPD = 11.2                                   # 25 mph
X_EGO = Key([(0, 5.25), (9.5, 5.25), (10.5, 5.27), (12.0, 5.33), (T_HIT, 6.08), (T_HIT + 0.3, 5.9), (21.0, 5.93), (40, 5.93)], 'lin')
S_EGO = Key([(0, SPD), (T_HIT, SPD), (T_HIT + 0.25, 4.0), (21.0, 0.0), (40, 0.0)], 'lin')
CURB = 7.0
LOOK_START, LOOK_END = 6.2, T_HIT + 0.05

# head yaw (radians, + = turns LEFT)
LOOK_HERO = Key([(0, 0.0), (6.0, 0.0), (6.4, 1.15), (T_HIT, 1.15), (T_HIT + 0.15, 0.0), (40, 0.0)])
LOOK_LADY = Key([(0, 0.0), (6.6, 0.0), (7.0, -0.95), (9.0, -0.95), (9.4, 0.0), (T_HIT + 0.2, 0.0), (T_HIT + 0.5, -0.9), (40, -0.9)])
LOOK_HUSB = Key([(0, 0.0), (15.8, 0.0), (16.2, -0.75), (18.2, -0.75), (18.5, 0.0), (T_HIT + 0.3, 0.0), (T_HIT + 0.6, -0.5), (40, -0.5)])


def hero_expr(t):
    if t < 6.3:
        return 'calm'
    if t < T_HIT:
        return 'dreamy'
    return 'shock'


def lady_expr(t):
    if 6.7 < t < 9.3:
        return 'smile'
    if t > T_HIT + 0.3:
        return 'laugh'
    return 'calm'


def husb_expr(t):
    if 15.9 < t < 18.4:
        return 'annoyed'
    if t > T_HIT + 0.4:
        return 'smug'
    return 'calm'


def occ_hero(t):
    def fn(ctx, view, Lf, h):
        person3d(ctx, view, Lf, -0.38, 0.05, 'hero', LOOK_HERO(t), hero_expr(t))
    return fn


def occ_couple(t):
    def fn(ctx, view, Lf, h):
        ppl = [(-0.38, 'husb', LOOK_HUSB(t), husb_expr(t)), (0.38, 'lady', LOOK_LADY(t), lady_expr(t))]
        ppl.sort(key=lambda q: -view.depth(Lf(q[0], 1.14, 0.05)))
        for sx, who, lk, ex in ppl:
            person3d(ctx, view, Lf, sx, 0.05, who, lk, ex)
    return fn


class Car(Track):
    """Track car drawn with occupants; bounce(t) = body hop in metres (bump)."""

    def __init__(self, x, speed, col, occ, bounce=None):
        super().__init__(x, speed, 0.0, 0.0, col, t0=-3, t1=40)
        self.occ, self.bounce = occ, bounce or (lambda t: 0.0)

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, None, self is EGO)
                return
            hop = self.bounce(t)
            ctx.save()
            if hop:
                sc = view.scale((x, 0.8, z)) or 0
                ctx.translate(0, -hop * sc)
            draw_car_round(ctx, view, x, z, h, self.col, t, None, self.brake(t), occ=self.occ(t))
            ctx.restore()
        return [((x, 0.8, z), fn)]


def ego_bounce(t):
    u = t - T_HIT
    if 0 <= u < 0.6:
        return 0.13 * math.exp(-u / 0.15) * abs(math.sin(u * 22))
    return 0.0


EGO = Car(X_EGO, S_EGO, '#e23b3b', occ_hero, ego_bounce)
LADY = Car(const(1.75), const(SPD), '#f4f4f6', occ_couple)


class Rev:
    def __init__(self, x, v, z0, col):
        self.x, self.v, self.z0, self.col = x, v, z0, col

    def pose(self, t):
        return self.x, self.z0 - self.v * t, math.pi

    def speed(self, t):
        return self.v

    def steer(self, t):
        return 0.0

    def blink(self, t):
        return None

    def brake(self, t):
        return 0.0

    def visible(self, t):
        return True


ONC = [Rev(-1.75 if i % 2 else -5.25, 12.0, 60 + i * 55, c) for i, c in
       enumerate(['#3a7bd5', '#f2a541', '#c9c9d6', '#37b26c', '#1c1c22', '#7a4fd0', '#2f6f73', '#56b38a', '#e05d5d', '#d8c3a0'])]


# ------------------------------------------------------------------ hubcap (pops off at the bump and rolls away)
def wheel_fr(t):
    x, z, h = EGO.pose(t)
    Lf = L(x, z, h)
    return Lf(0.95, 0.34, 1.38)


HUB0 = wheel_fr(T_HIT)


def hub_state(t):
    """(x, y, z, dir, rolling)"""
    u = t - T_HIT - 0.05
    if u < 0:
        return None
    vz0, vx0 = 7.0, 1.5
    T_STOP = 2.6
    uu = min(u, T_STOP)
    z = HUB0[2] + vz0 * uu - vz0 / (2 * T_STOP) * uu * uu
    x = HUB0[0] + vx0 * uu - vx0 / (2 * T_STOP) * uu * uu
    hop = max(0.0, 0.35 * math.sin(math.pi * min(u, 0.45) / 0.45)) if u < 0.45 else 0.0
    rolling = u < T_STOP + 0.4
    return x, 0.21 + hop, z, math.atan2(vx0, vz0), rolling, u


class Hubcap:
    def items(self, ctx, view, t):
        st = hub_state(t)
        if not st or t > 26:
            return []
        x, y, z, d, rolling, u = st

        def fn():
            if view.ortho:
                p = view.pt((x, 0, z))
                ellipse(ctx, p[0], p[1], 0.22 * view.s, 0.22 * view.s)
                fill_stroke(ctx, RIM_C, OUTL, 2)
                return
            r = 0.21
            dx, dz = math.sin(d), math.cos(d)
            wob = 0.0 if u < 2.6 else min(1.0, (u - 2.6) / 0.4)
            if wob < 1.0:
                tilt = 0.25 * wob * math.sin(u * 30)
                nx, nz = math.cos(d), -math.sin(d)
                pts = [view.pt((x + dx * r * math.cos(a) + nx * r * math.sin(a) * tilt, y + r * math.sin(a), z + dz * r * math.cos(a) + nz * r * math.sin(a) * tilt))
                       for a in np.linspace(0, 2 * math.pi, 24)]
            else:
                pts = [view.pt((x + r * math.cos(a), 0.03, z + r * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 24)]
            if all(pts):
                poly(ctx, pts)
                fill_stroke(ctx, RIM_C, OUTL, 2)
                c = view.pt((x, y if wob < 1 else 0.03, z))
                s = view.scale((x, y, z)) or 10
                ang = -u * 30 if u < 2.6 else 0
                for k in range(5):
                    a = ang + k * 2 * math.pi / 5
                    ctx.move_to(*c)
                    ctx.line_to(c[0] + math.cos(a) * 0.12 * s * (1 if wob < 1 else 1), c[1] + math.sin(a) * 0.12 * s)
                setc(ctx, hexc('#8a8f9c'))
                ctx.set_line_width(max(1, s * 0.02))
                ctx.stroke()
        return [((x, 0.3, z), fn)]


RIM_C = hexc('#d4d8e0')
HUB = Hubcap()
for _a in (HUB,):
    _a.visible = lambda t: True
    _a.pose = lambda t: (0, 0, 0)
    _a.col = '#ccc'


# ------------------------------------------------------------------ Miami Beach street
def miami_sky(ctx, view):
    if view.ortho:
        return
    towers(ctx, view, 1400, -600, -60, 18, 40, 120, seed=8, base='#9fb3c8', haze='#e6f2fb')


class MiamiStreet(Street):
    def __init__(self):
        super().__init__('city', n=2, median='yellow', sidewalk=True, seed=17, hmin=10, hmax=18, setback=1.0,
                         sky=('#3fa7f0', '#e6f6ff'), ground='#8fd07a', skyline=miami_sky,
                         palette=['#f7c8d0', '#a8e0d8', '#f9e3a1', '#c9b8f0', '#f4efe6', '#ffcfa8', '#b8e0f7'])
        self.items = [it for it in self.items if (it[0] == 'bld' and it[1][0] < 0)]
        r = random.Random(3)
        for z in np.arange(-300, 600, 12):
            self.items.append(('palm', (-(self.R + 1.3), z + r.uniform(-1, 1), 0.9 + r.uniform(0, 0.25))))
        for z in np.arange(-300, 600, 9):
            self.items.append(('palm', (self.W + 2.5 + r.uniform(0, 3), z + r.uniform(-2, 2), 0.95 + r.uniform(0, 0.3))))

    def ground(self, ctx, view, t):
        gquad(ctx, view, self.W + 6, 2000, -600, 900, hexc('#f1dfae'))
        gquad(ctx, view, self.W + 38, 2000, -600, 900, hexc('#2fa7c9'))
        if not view.ortho:
            for k in range(14):
                gquad(ctx, view, self.W + 38, 2000, -600 + k * 3, -600 + k * 3 + 0.4, hexc('#2fa7c9'))
        super().ground(ctx, view, t)
        # curb faces (right curb is where he hits)
        if not view.ortho:
            for sx in (-1, 1):
                fill_poly(ctx, view, [(sx * CURB, 0, -500), (sx * CURB, 0, 600), (sx * CURB, 0.16, 600), (sx * CURB, 0.16, -500)],
                          hexc('#e6e1d6'), OUTL, 1.5)
        else:
            gquad(ctx, view, CURB - 0.05, CURB + 0.2, -500, 600, hexc('#e6e1d6'))

    def objects(self, ctx, view, t):
        out = []
        for kind, a in self.items:
            if kind == 'bld':
                out.append((((a[0] + a[1]) / 2, a[4] / 2, (a[2] + a[3]) / 2), lambda a=a: building(ctx, view, *a, win='#3b5872')))
            elif kind == 'palm':
                out.append(((a[0], 4, a[1]), lambda a=a: palm(ctx, view, a[0], a[1], a[2])))
        return out


world = SegWorld(DUR, [hook_seg(0, 3.0, 16.6, EGO, [LADY, HUB] + ONC), (3.0, 99, EGO, [LADY, HUB] + ONC, [])],
                 MiamiStreet(), 'mph')
world.peds_at = lambda t: []


# ------------------------------------------------------------------ 2D close-ups (everything inside a window opening is clipped to it)
def scenery_strip(ctx, x0, x1, y0, y1, t, direction, kind):
    """Scrolling world seen through a car window (direction +1 = scenery moves right)."""
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgb(0, *hexc('#3fa7f0'))
    g.add_color_stop_rgb(1, *hexc('#d9f1ff'))
    ctx.set_source(g)
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.fill()
    hz = y0 + (y1 - y0) * 0.7
    if kind == 'beach':
        ctx.rectangle(x0, hz - 20, x1 - x0, 30)
        setc(ctx, hexc('#2fa7c9'))
        ctx.fill()
        ctx.rectangle(x0, hz + 10, x1 - x0, y1 - hz)
        setc(ctx, hexc('#f1dfae'))
        ctx.fill()
        span = 520
        off = (t * 420 * direction) % span
        for k in range(-1, int((x1 - x0) / span) + 3):
            px = x0 + k * span + off
            ctx.move_to(px, y1)
            ctx.curve_to(px + 20, hz - 60, px - 10, hz - 180, px + 15, y0 + 60)
            setc(ctx, hexc('#8a6a4a'))
            ctx.set_line_width(16)
            ctx.stroke()
            for j in range(7):
                a = math.pi + j / 6 * math.pi
                ctx.move_to(px + 15, y0 + 60)
                ctx.curve_to(px + 15 + math.cos(a) * 70, y0 + 30, px + 15 + math.cos(a) * 150, y0 + 60 + math.sin(a) * 30, px + 15 + math.cos(a) * 160, y0 + 110)
                setc(ctx, hexc('#2f8a45'))
                ctx.set_line_width(14)
                ctx.stroke()
    else:
        cols = ['#f7c8d0', '#a8e0d8', '#f9e3a1', '#c9b8f0', '#ffcfa8', '#b8e0f7']
        span = 330
        off = (t * 380 * direction) % (span * len(cols))
        for k in range(-len(cols), int((x1 - x0) / span) + len(cols) + 2):
            px = x0 + k * span + off
            hgt = 160 + 90 * ((k * 7) % 3)
            ctx.rectangle(px, hz - hgt, span - 20, hgt + 200)
            fill_stroke(ctx, hexc(cols[k % len(cols)]), OUTL, 3)
            for wy in range(int(hz - hgt + 30), int(hz), 60):
                for wx in range(int(px + 25), int(px + span - 60), 70):
                    ctx.rectangle(wx, wy, 38, 30)
                    setc(ctx, hexc('#3b5872'))
                    ctx.fill()
        ctx.rectangle(x0, hz, x1 - x0, y1 - hz)
        setc(ctx, C_WALK)
        ctx.fill()


def opening_path(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


HERO_WIN = [(240, 770), (1730, 770), (1730, 190), (600, 150)]        # his driver window (front = screen LEFT)


def win_hero(ctx, w, t, lt, kw):
    """Seen from the lady's car: our hero through his window (closed glass)."""
    shake = kw.get('shake', 0.0) * max(0.0, 1 - lt / 1.0)
    jx, jy = math.sin(lt * 70) * 18 * shake, math.cos(lt * 63) * 12 * shake
    ctx.save()
    ctx.translate(jx, jy)
    setc(ctx, hexc('#f1dfae'))
    ctx.paint()
    ctx.save()
    opening_path(ctx, HERO_WIN)
    ctx.clip()
    setc(ctx, hexc('#2c2d38'))
    ctx.paint()
    scenery_strip(ctx, 560, 1760, 200, 560, t, 1, 'beach')          # through his far (right) window
    ctx.rectangle(0, 120, SW, 80)
    setc(ctx, hexc('#4a4b58'))
    ctx.fill()
    # dashboard + wheel rim at the front (screen left)
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
    # seat behind him (rear = screen right)
    rrect(ctx, 1080, 300, 300, 700, 90)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 5)
    rrect(ctx, 1110, 250, 230, 150, 60)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 5)
    turn = kw['turn'](lt) if callable(kw.get('turn')) else kw.get('turn', 0.0)
    expr = kw['expr'](t) if callable(kw.get('expr')) else kw.get('expr', 'calm')
    head2d(ctx, 900, 480, 175, 'hero', expr, turn, t, kw.get('tilt', 0.0) * (1 if shake else 0.3))
    if expr == 'dreamy':
        for i in range(4):
            ph = (t * 0.45 + i / 4) % 1
            heart(ctx, 1080 + i * 40 + 40 * math.sin(ph * 6 + i), 420 - ph * 260, 22 + 16 * ph, hexc('#ff2d55'), math.sin(math.pi * ph))
    # closed window glass: tint + reflection streaks
    setc(ctx, (0.75, 0.88, 1.0), 0.1)
    ctx.paint()
    for x0, wd in ((760, 70), (880, 26), (1420, 50)):
        poly(ctx, [(x0, 140), (x0 + wd, 140), (x0 + wd - 260, 790), (x0 - 260, 790)])
        setc(ctx, (1, 1, 1), 0.12)
        ctx.fill()
    ctx.restore()
    # car body around the opening
    body = hexc('#e23b3b')
    ctx.rectangle(-40, -40, SW + 80, SH + 80)
    opening_path(ctx, HERO_WIN)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    setc(ctx, body)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.rectangle(-40, -40, SW + 80, 130)
    setc(ctx, mix(body, (0, 0, 0), 0.15))
    ctx.fill()
    opening_path(ctx, HERO_WIN)
    setc(ctx, hexc('#15151c'))
    ctx.set_line_width(22)
    ctx.stroke()
    ctx.move_to(-40, 950)
    ctx.line_to(SW + 40, 930)
    setc(ctx, mix(body, (0, 0, 0), 0.3))
    ctx.set_line_width(6)
    ctx.stroke()
    rrect(ctx, 1450, 850, 170, 40, 18)
    fill_stroke(ctx, mix(body, (0, 0, 0), 0.25), OUTL, 4)
    ctx.restore()


LADY_WIN = [(520, 700), (1590, 700), (1290, 340), (520, 340)]     # her front passenger window (front = screen RIGHT), OPEN


def win_pov(ctx, w, t, lt, kw):
    """Hero's view out of his window: the lady in the next car, her husband driving."""
    sky_x0 = -40
    scenery_strip(ctx, -40, SW + 40, -40, 520, t, -1, 'city')
    # her car body (white) with the open front window
    body = hexc('#f4f4f6')
    ctx.move_to(-40, 300)
    ctx.line_to(1300, 300)
    ctx.curve_to(1500, 330, 1700, 560, 1960, 600)
    ctx.line_to(1960, 1120)
    ctx.line_to(-40, 1120)
    ctx.close_path()
    fill_stroke(ctx, body, OUTL, 5)
    ctx.save()
    opening_path(ctx, LADY_WIN)
    ctx.clip()
    setc(ctx, hexc('#2c2d38'))
    ctx.paint()
    scenery_strip(ctx, 520, 1600, 360, 600, t, -1, 'city')         # through her far window
    ctx.rectangle(0, 330, SW, 40)
    setc(ctx, hexc('#4a4b58'))
    ctx.fill()
    hl = LOOK_HUSB(t)
    lean = clamp(-hl / 0.75)
    head2d(ctx, 1050 + 90 * lean, 520 - 10 * lean, 92, 'husb', husb_expr(t), 0.85 - 0.9 * lean, t)
    ll = LOOK_LADY(t)
    turn_l = 0.85 - 1.05 * clamp(-ll / 0.95) if ll <= 0 else 0.85
    head2d(ctx, 790, 540, 128, 'lady', lady_expr(t), turn_l, t)
    ctx.restore()
    opening_path(ctx, LADY_WIN)
    setc(ctx, hexc('#15151c'))
    ctx.set_line_width(14)
    ctx.stroke()
    # rear door window (closed, tinted) + B-pillar
    poly(ctx, [(60, 700), (470, 700), (470, 340), (120, 340)])
    fill_stroke(ctx, hexc('#5a6b82'), hexc('#15151c'), 12)
    poly(ctx, [(200, 690), (260, 690), (380, 350), (320, 350)])
    setc(ctx, (1, 1, 1), 0.18)
    ctx.fill()
    ctx.rectangle(470, 330, 50, 380)
    setc(ctx, hexc('#15151c'))
    ctx.fill()
    ctx.move_to(-40, 860)
    ctx.line_to(1960, 850)
    setc(ctx, mix(body, (0, 0, 0), 0.2))
    ctx.set_line_width(5)
    ctx.stroke()
    rrect(ctx, 1180, 780, 150, 36, 16)
    fill_stroke(ctx, mix(body, (0, 0, 0), 0.12), OUTL, 4)
    # wheels of her car peeking at the bottom
    for wx in (330, 1560):
        ellipse(ctx, wx, 1110, 190, 150)
        fill_stroke(ctx, hexc('#1d1d24'), OUTL, 5)
        ellipse(ctx, wx, 1110, 110, 85)
        fill_stroke(ctx, RIM_C, OUTL, 4)
    # our own window frame (dark trim) + door top + A-pillar on the right
    ctx.rectangle(-40, -40, SW + 80, SH + 80)
    ctx.move_to(-40, 30)
    ctx.line_to(1480, 30)
    ctx.line_to(1880, 760)
    ctx.line_to(1880, 900)
    ctx.line_to(-40, 900)
    ctx.close_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    setc(ctx, hexc('#2a2a36'))
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.rectangle(-40, 900, SW + 80, 200)
    setc(ctx, hexc('#c23535'))
    ctx.fill()
    ctx.rectangle(-40, 890, SW + 80, 22)
    setc(ctx, OUTL)
    ctx.fill()


engine.SCENES.update(win_hero=win_hero, win_pov=win_pov)


# ------------------------------------------------------------------ 3D shot extras: bump effects, hearts, top-view paths
def bonk_fx(ctx, view, t):
    u = t - T_HIT
    if view is None or view.ortho or not (0 <= u < 1.4):
        return
    c = wheel_fr(T_HIT)
    p, s = view.pt((c[0] + 0.1, 0.25, c[2])), view.scale((c[0], 0.25, c[2]))
    if not p or not s:
        return
    rnd = random.Random(4)
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        d = (0.4 + 1.4 * u) * s * rnd.uniform(0.6, 1.2)
        ellipse(ctx, p[0] + math.cos(a) * d * 0.8, p[1] - abs(math.sin(a)) * d * 0.5, 0.25 * s * (1 + u), 0.18 * s * (1 + u))
        setc(ctx, hexc('#e8dfcc'), max(0, 0.7 - u * 0.5))
        ctx.fill()
    if u < 0.6:
        sz = clamp(s * 0.9, 70, 150) * (1 + 0.3 * (1 - smooth(u / 0.12)))
        n = 12
        pts = []
        for k in range(2 * n):
            ang = k * math.pi / n
            rr = (1.0 if k % 2 == 0 else 0.65) * sz
            pts.append((p[0] + math.cos(ang) * rr * 1.5, p[1] - sz * 1.2 + math.sin(ang) * rr))
        poly(ctx, pts)
        fill_stroke(ctx, hexc('#ffd23f'), OUTL, 5)
        text_center(ctx, 'BONK!', p[0], p[1] - sz * 1.2 + sz * 0.22, sz * 0.62, OUTL)


def hero_hearts(ctx, view, t):
    if not (LOOK_START + 0.3 < t < T_HIT) or view is None or view.ortho:
        return
    x, z, h = EGO.pose(t)
    for i in range(3):
        ph = (t * 0.5 + i / 3) % 1
        P = (x - 0.6 - ph * 0.8, 1.8 + ph * 1.6, z + 0.1)
        p, s = view.pt(P), view.scale(P)
        if p and s:
            heart(ctx, p[0], p[1], clamp(0.18 * s, 8, 40), hexc('#ff2d55'), math.sin(math.pi * ph))


def fx_post(ctx, view, t, lt):
    hero_hearts(ctx, view, t)
    bonk_fx(ctx, view, t)


def top_post(ctx, view, t, lt):
    pts = [view.pt((X_EGO(u), 0, EGO.z(u))) for u in np.arange(max(9.0, t - 6), min(t, T_HIT) + 0.01, 0.05)]
    if len(pts) > 2:
        arrow_path(ctx, pts, hexc('#e0393e'), 9, 0.9, None, 0)
    fut = [view.pt((X_EGO(u), 0, EGO.z(u))) for u in np.arange(t, T_HIT + 0.01, 0.05)]
    if len(fut) > 2:
        arrow_path(ctx, fut, hexc('#ffd23f'), 7, 0.9, (18, 14), 28)
    ex, ez = world.ego_xz(t)
    a = view.pt((CURB, 0, ez + 14))
    label(ctx, a[0], a[1] + 75, 'CURB', '#e0393e', 40)
    b = view.pt((ex, 0, ez))
    label(ctx, b[0] - 260, b[1] + 75, 'Still staring...', '#7a4fd0', 38)


# ------------------------------------------------------------------ shots
HOOK_CAM = dict(cam='fixed', pos=(9.6, 1.4, 223.0), target=(4.6, 0.9, 210.0), f=1050, hud=False)
FRONT = dict(cam='follow', off=(2.0, 1.7, 8.5), look=(-1.6, 1.0, 0), f=1000, hud=False)
WIDE_END = dict(cam='fixed', pos=(10.2, 2.0, 212.5), target=(5.6, 0.6, 223.5), f=950, hud=False)
defs = [
    (3.0, 'm_cam', dict(HOOK_CAM, post=fx_post)),
    (6.0, 'm_cam', dict(cam='chase', post=fx_post)),
    (8.6, 'win_pov', dict()),
    (11.2, 'win_hero', dict(expr='dreamy', turn=0.0)),
    (13.8, 'm_cam', dict(FRONT, post=fx_post)),
    (16.0, 'm_top', dict(horizontal=True, xc=3.5, ahead=8.0, scale=40.0, post=top_post)),
    (18.2, 'win_pov', dict()),
    (20.6, 'm_cam', dict(cam='close_r', post=fx_post)),
    (22.6, 'win_hero', dict(expr='shock', turn=-0.7, shake=1.0, tilt=0.12)),
    (25.0, 'm_cam', dict(WIDE_END, post=fx_post)),
    (DUR, 'm_cam', dict(WIDE_END, post=fx_post)),
]
shots = build_shots(defs)
video = Video(['Eyes on the ROAD...', 'not the next car'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]


def eyes_off_meter(ctx, lt, d):
    t = S[1] + lt
    if t < LOOK_START:
        return
    v = min(t, LOOK_END) - LOOK_START
    rrect(ctx, 1420, 40, 460, 140, 34)
    setc(ctx, (0, 0, 0), 0.6)
    ctx.fill()
    text_center(ctx, 'EYES OFF ROAD', 1650, 90, 36, (0.9, 0.9, 0.95))
    text_center(ctx, f'{v:.1f} s', 1650, 160, 62, hexc('#ff4b4b') if v > 2 else hexc('#ffd23f'))


BLIND_FT = int(round(SPD * (LOOK_END - LOOK_START) * 3.281 / 10) * 10)
video.overlays = [
    (0.0, 3.0, big_text('Why did he hit the curb?', 300, 120, hexc('#ffd23f'), 0.2, True)),
    (3.0, 6.0, location_tag('Miami Beach, Florida')),
    (3.2, 6.0, caption('Just a normal drive...')),
    (S[1], S[9], eyes_off_meter),
    (S[2] + 0.8, E[2], caption('Oh... hello!')),
    (S[3] + 0.2, E[3], caption('Eyes on her... not the road')),
    (S[4] + 0.2, E[4], caption('The car slowly drifts right')),
    (S[6] + 0.2, E[6], caption('Her husband noticed...')),
    (S[8] + 0.2, E[8], caption('...but nobody told the curb')),
    (S[9] + 0.2, E[9], caption('...and his hubcap rolled away')),
    (S[10], E[10], end_card('Eyes on the ROAD. Always.', 'Ever been this distracted? Be honest!')),
    (S[10] + 0.3, E[10], big_text(f'13 s not looking = {BLIND_FT} ft driven blind', 980, 60, (1, 1, 1))),
]


# ------------------------------------------------------------------ sound
def harp(d=1.0):
    out = np.zeros(int(d * SR) + SR)
    for i, n in enumerate((72, 76, 79, 83, 84, 88, 91, 95)):
        tt = np.arange(int(0.8 * SR)) / SR
        s = sum(np.sin(2 * np.pi * midi(n) * k * tt) / k ** 2 for k in (1, 2, 3)) * np.exp(-tt / 0.35)
        place(out, s * 0.18, i * 0.07)
    return out[:int(d * SR)]


def scrape(d=0.5):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return (bp(noise(n), 900, 4500) * 0.6 + np.sin(2 * np.pi * 1800 * tt) * 0.1) * np.exp(-tt / 0.18)


def clank():
    n = int(0.8 * SR)
    tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt / dd) for f, dd in ((1310, 0.25), (2170, 0.18), (3420, 0.1), (870, 0.3)))
    return s * 0.25


def roll_ring(d=3.0):
    n = int(d * SR)
    tt = np.arange(n) / SR
    rate = 9 * np.maximum(0.15, 1 - tt / d)
    ph = np.cumsum(rate) / SR
    tick = (np.sin(2 * np.pi * ph) > 0.97).astype(float)
    body = bp(noise(n), 1500, 5000) * 0.15 * (1 - tt / d)
    wob = np.sin(2 * np.pi * 1100 * tt) * 0.12 * np.exp(-((tt - (d - 0.5)) ** 2) / 0.05)
    return lp(tick, 3000) * 0.5 + body + wob


def giggle(d=1.2, f0=300):
    out = np.zeros(int(d * SR) + SR)
    tt, k = 0.0, 0
    while tt < d:
        n = int(0.09 * SR)
        x = np.arange(n) / SR
        f = f0 * (1.15 if k % 2 else 1.0) * (1 + 0.1 * np.sin(2 * np.pi * 7 * x))
        s = sum(np.sin(2 * np.pi * np.cumsum(f * h) / SR) / h for h in (1, 2, 3))
        s = bp(s, 300, 2500) + bp(noise(n), 1500, 4000) * 0.3
        place(out, s * np.sin(np.pi * x / 0.09) * 0.35, tt)
        tt += 0.14 + 0.02 * (k % 3)
        k += 1
    return out[:int(d * SR)]


def throat_clear():
    out = np.zeros(int(0.8 * SR))
    for o, f in ((0.0, 140), (0.25, 120)):
        n = int(0.22 * SR)
        x = np.arange(n) / SR
        s = bp(noise(n), 200, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * f * x)) * np.sin(np.pi * x / 0.22)
        place(out, s * 0.9, o)
    return out


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur, 1.0), 0, 0.2)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.12)
    hook_sfx(m)
    # hook shows the bump at 0 + (T_HIT - 16.6)
    th = T_HIT - 16.6
    m.add(scrape(0.5), th, 0.8)
    m.add(thud(), th, 1.0)
    m.add(clank(), th + 0.1, 0.5)
    m.add(boing(), S[2] + 0.4, 0.0)
    m.add(harp(1.2), S[2] + 0.5, 0.8)                 # he sees her
    m.add(sparkle(), S[2] + 1.1, 0.5)                 # her polite smile
    m.add(harp(1.2), S[3] + 0.1, 0.6)
    for i in range(4):
        m.add(pop(), S[3] + 0.4 + i * 0.5, 0.35)
    m.add(throat_clear(), S[6] + 0.3, 0.9)            # husband
    m.add(heartbeat(2, 120), S[7] + 0.1, 0.6)
    m.add(scrape(0.6), T_HIT, 0.9)
    m.add(thud(), T_HIT, 1.2)
    m.add(impact(), T_HIT, 0.5)
    m.add(clank(), T_HIT + 0.08, 0.7)
    m.add(roll_ring(2.9), T_HIT + 0.2, 0.7)
    m.add(boing(), T_HIT + 0.3, 0.5)
    m.add(giggle(1.4), T_HIT + 0.7, 0.55, -0.4)
    m.add(sad_trombone(), S[8] + 0.6, 0.55)
    m.add(clank(), T_HIT + 2.9, 0.4)                  # hubcap falls flat
    m.add(car_pass(2.0, 0.4, 85), S[9] + 0.2, 0.35, np.linspace(-0.3, 0.7, int(2.0 * SR)))
    m.add(success_jingle(), S[10] + 0.2, 0.8)
    m.add(pop(), S[10] + 1.0, 0.8)
    return m.out(video.dur)


def verify():
    print('lateral gap between cars (m):', round(5.25 - 1.75 - 1.84, 2))
    xs = [(t, X_EGO(t) + 0.92) for t in np.arange(0, T_HIT + 0.01, 0.05)]
    print('ego tyre face reaches curb at t =', next(round(t, 2) for t, xr in xs if xr >= CURB - 0.005), '(T_HIT', T_HIT, ')',
          'max tyre x', round(max(X_EGO(t) + 0.92 for t in np.arange(0, 29, 0.01)), 3))
    print('ego z at hit', round(EGO.z(T_HIT), 1), 'lady z', round(LADY.z(T_HIT), 1), 'ego stops at z', round(EGO.z(25), 1))
    print('hubcap rest', [round(v, 2) for v in hub_state(24)[:3]])
    print('eyes off road (s):', round(LOOK_END - LOOK_START, 2), 'ft blind', BLIND_FT)
    for t in (3, 10, 18, 25):
        print('t', t, 'cam close_r ok')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        run(video, sound, 'curb.mp4')
