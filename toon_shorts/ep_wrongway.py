"""A wrong-way driver coming at you: freeze vs act. Highway 400 near Barrie, Ontario, in winter.

World: +Z = south (our travel). Our carriageway: left/passing lane x = 1.75, right lane x = 5.25, paved shoulder
7.0..10.0 with snowbanks; wide snowy median at x < -1.5, opposite carriageway at x -22..-29.
The wrong-way car drives in OUR left lane toward us (wrong-way drivers usually end up in the left lane, which is
"their" right lane - NTSB). Two cars at 100 km/h close at ~55 m every second.
Part 1 (wrong): he freezes and stays in the left lane (freeze 35 m before). Part 2 (right): slow down, move RIGHT,
let it pass, pull onto the shoulder and call 911 with the location and direction.
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

DUR = 37.0
V = 27.8
T_R0 = 16.7
T_FREEZE = 15.0
T_MEET_W = T_FREEZE + 35.0 / (2 * V)
T_PASS = 23.0
C_SNOW = hexc('#eef3f8')


class WCar(Track):
    def __init__(self, x, speed, ta, za, col, occ=None, blink=None, brake=None, haz_from=None, rev=False):
        super().__init__(x, speed, ta, za, col, blink=blink, brake=brake, t0=-3, t1=45)
        self.occ, self.haz_from, self.rev = occ, haz_from, rev

    def pose(self, t):
        x, z, h = super().pose(t)
        if self.rev:
            return x, self.z(t), math.pi
        return x, z, h

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        b = ('L' if (t * 1.25) % 1 < 0.5 else None) if (self.haz_from is not None and t >= self.haz_from) else self.blink(t)

        def fn():
            if view.ortho:
                draw_car_top_g(ctx, view, x, z, h, self.col, t, b, self.occ is not None)
                return
            draw_car_round(ctx, view, x, z, h, self.col, t, b, self.brake(t), occ=self.occ(t) if self.occ else None)
            if self.rev:                        # its headlights, facing us
                Lf = L(x, z, h)
                for sx in (-0.62, 0.62):
                    P = Lf(sx, 0.68, 2.24)
                    p, s = view.pt(P), view.scale(P)
                    if p and s and view.to_cam(P)[2] > 0:
                        glow(ctx, p[0], p[1], min(1.3 * s + 30, 320), (1.0, 0.97, 0.85), 0.95)
        return [((x, 0.8, z), fn)]


class Rev(WCar):
    """Travels -z: z(t) = z_meet + v (t_meet - t)."""

    def __init__(self, x, v, t_meet, z_meet, col, occ=None):
        super().__init__(x, const(0.0), 0.0, 0.0, col, occ)
        self.v, self.tm, self.zm = v, t_meet, z_meet
        self.rev = True

    def z(self, t):
        return self.zm + self.v * (self.tm - t)

    def pose(self, t):
        return self.x0, self.z(t), math.pi

    @property
    def x0(self):
        return 1.75

    def speed(self, t):
        return self.v


def occ_for(expr):
    def occ(t):
        def fn(ctx, view, Lf, h):
            person3d(ctx, view, Lf, -0.38, 0.05, 'hero', 0.0, expr(t))
        return fn
    return occ


# ---- part 1
HERO_W = WCar(1.75, const(V), 0.0, 0.0, '#e23b3b', occ_for(lambda t: 'calm' if t < 8.5 else 'shock'))
WW_W = Rev(1.75, V, T_MEET_W, HERO_W.z(T_MEET_W), '#1c1c22')
TRAF_W = [WCar(5.25, const(25.0), 0.0, 60.0 + 70 * i, c) for i, c in enumerate(['#3a7bd5', '#37b26c', '#c9c9d6'])]

# ---- part 2
SPD_R = Key([(0, V), (18.6, V), (20.6, 16.5), (24.4, 16.5), (27.4, 0.0), (99, 0.0)], 'lin')
X_R = Key([(0, 1.75), (19.2, 1.75), (20.8, 5.25), (24.6, 5.25), (26.6, 8.6), (99, 8.6)])
HERO_R = WCar(X_R, SPD_R, T_R0, 0.0, '#e23b3b', occ_for(lambda t: 'focus' if t < 27.4 else 'calm'),
              blink=blink_side([(18.9, 21.0), (24.2, 26.8)], 'R'), brake=lambda t: 1.0 if 18.6 < t < 20.6 or 24.4 < t < 28 else 0.0,
              haz_from=27.6)
WW_R = Rev(1.75, V, T_PASS, HERO_R.z(T_PASS), '#1c1c22')
TRAF_R = [WCar(5.25, const(16.5), T_R0, HERO_R.z(T_R0) + 95.0, '#3a7bd5', haz_from=21.0), WCar(5.25, const(16.0), T_R0, HERO_R.z(T_R0) - 60.0, '#37b26c')]


# ------------------------------------------------------------------ winter highway
def snow_tree(ctx, view, x, z, s):
    conifer(ctx, view, x, z, s)
    if view.ortho:
        return
    for k, (y, w) in enumerate(((3.9, 1.0), (2.6, 1.5), (1.4, 2.0))):
        p, sc = view.pt((x, y * s * 1.2, z)), view.scale((x, y * s * 1.2, z))
        if p and sc:
            ellipse(ctx, p[0], p[1], w * s * sc * 0.65, 0.22 * s * sc)
            setc(ctx, C_SNOW)
            ctx.fill()


class Winter:
    sky = ('#8fa6bf', '#dfe8f0')

    def __init__(self):
        self.ground_col = C_SNOW
        r = random.Random(9)
        self.trees = [(r.uniform(14, 70), z + r.uniform(-4, 4), r.uniform(1.0, 1.7)) for z in np.arange(-300, 1600, 9)]
        self.trees += [(-r.uniform(32, 80), z + r.uniform(-4, 4), r.uniform(1.0, 1.7)) for z in np.arange(-300, 1600, 11)]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        far_line(ctx, view, 2500, lambda x: 30 + 12 * math.sin(x / 260), col='#9fb0a8')

    def ground(self, ctx, view, t):
        ez = view.pos[2] if not view.ortho else view.zc
        zlo, zhi = ez - 250, ez + 1600
        gquad(ctx, view, -0.8, 10.0, zlo, zhi, hexc('#8d8f96'))
        gquad(ctx, view, 0.0, 7.0, zlo, zhi, C_ASPH)
        gquad(ctx, view, -29.0, -21.0, zlo, zhi, C_ASPH)
        for xl in (3.5, -25.0):
            for k in range(int(zlo // 12), int(zhi // 12) + 1):
                gquad(ctx, view, xl - 0.07, xl + 0.07, k * 12, k * 12 + 4, C_LINE, 0.01)
        gquad(ctx, view, 0.05, 0.2, zlo, zhi, C_YEL, 0.01)
        gquad(ctx, view, 6.85, 7.0, zlo, zhi, C_LINE, 0.01)
        # slush along the edges + snowbanks
        gquad(ctx, view, 9.4, 10.0, zlo, zhi, hexc('#c9d2db'), 0.005)
        gquad(ctx, view, -0.8, -0.4, zlo, zhi, hexc('#c9d2db'), 0.005)
        if not view.ortho:
            for xb, w in ((10.6, 1.2), (-2.0, 1.0)):
                fill_poly(ctx, view, [(xb - w, 0, zlo), (xb - w, 0, zhi), (xb, 0.7, zhi), (xb, 0.7, zlo)], hexc('#dfe7ef'))
                fill_poly(ctx, view, [(xb, 0.7, zlo), (xb, 0.7, zhi), (xb + w, 0, zhi), (xb + w, 0, zlo)], hexc('#f4f8fb'))

    def objects(self, ctx, view, t):
        out = []
        ez = view.pos[2] if not view.ortho else view.zc
        for x, z, s in self.trees:
            if ez - 60 < z < ez + 700:
                out.append(((x, 2.5, z), lambda x=x, z=z, s=s: snow_tree(ctx, view, x, z, s * (0.5 if view.ortho else 1.0))))
        for zs in (180.0, 640.0):
            out.append(((12.0, 3, zs), lambda zs=zs: hwy_sign(ctx, view, 12.0, zs)))
        return out


def hwy_sign(ctx, view, x, z):
    if view.ortho:
        return
    a, b = view.pt((x, 0, z)), view.pt((x, 2.4, z))
    if not a or not b:
        return
    ctx.move_to(*a)
    ctx.line_to(*b)
    setc(ctx, hexc('#6a6f7c'))
    ctx.set_line_width(max(2, (view.scale((x, 1, z)) or 10) * 0.1))
    ctx.stroke()
    if fill_poly(ctx, view, [(x - 1.3, 2.4, z), (x + 1.3, 2.4, z), (x + 1.3, 4.6, z), (x - 1.3, 4.6, z)], hexc('#1f6f43'), (1, 1, 1), 3):
        c, s = view.pt((x, 3.5, z)), view.scale((x, 3.5, z))
        if c and s and s > 5:
            text_center(ctx, '400', c[0], c[1] - 0.1 * s, 0.8 * s, (1, 1, 1))
            text_center(ctx, 'SOUTH', c[0], c[1] + 0.65 * s, 0.38 * s, (1, 1, 1))


world = SegWorld(DUR, [hook_seg(0, 3.0, 12.0, HERO_W, [WW_W] + TRAF_W, []),
                       (3.0, T_R0, HERO_W, [WW_W] + TRAF_W, []),
                       (T_R0, 99, HERO_R, [WW_R] + TRAF_R, [])], Winter(), 'kmh')
world.police_flash = lambda t: 0.0


def snowfall(ctx, t, n=120):
    rnd = random.Random(2)
    for k in range(n):
        x0, y0, sp, r = rnd.uniform(0, SW), rnd.uniform(0, SH), rnd.uniform(60, 160), rnd.uniform(2, 6)
        y = (y0 + t * sp) % SH
        x = (x0 + 30 * math.sin(t + k)) % SW
        ellipse(ctx, x, y, r, r)
        setc(ctx, (1, 1, 1), 0.85)
        ctx.fill()


def w_cam(ctx, w, t, lt, kw):
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
        view = TCam((x, 3.4, z - 10.5), 0.0, 0.14, 1000, cy=520)
    elif m == 'high':
        view = TCam((4.0, 14.0, z - 20), 0.0, 0.45, 950, cy=440)
    elif m == 'inside':
        view = TCam((x - 0.38, 1.18, z - 0.2), h, 0.03, 1000, cy=470)
    draw_scene(ctx, view, w, tf, ego=m != 'inside')
    if m == 'inside':
        citykit.cockpit(ctx, w, tf)
    snowfall(ctx, t, 70 if m == 'inside' else 120)
    if 'freeze' in kw and t >= kw['freeze']:
        u = t - kw['freeze']
        setc(ctx, (1, 1, 1), max(0, 0.8 - u * 3))
        ctx.paint()
        setc(ctx, (0.6, 0, 0), 0.22)
        ctx.paint()
    if kw.get('hud', m in ('chase', 'inside')):
        hud(ctx, w, tf)
    if kw.get('gap'):
        ww = WW_W if tf < T_R0 else WW_R
        d = ww.z(tf) - e.pose(tf)[1] - 4.4
        if d > 0:
            rrect(ctx, 1400, 40, 480, 160, 34)
            setc(ctx, (0, 0, 0), 0.6)
            ctx.fill()
            text_center(ctx, 'DISTANCE', 1640, 92, 36, (0.9, 0.9, 0.95))
            text_center(ctx, f'{int(d)} m', 1640, 172, 70, hexc('#ff4b4b') if d < 150 else hexc('#ffd23f'))


def win_face(ctx, w, t, lt, kw):
    WIN = [(240, 770), (1730, 770), (1730, 190), (600, 150)]
    path = lambda: (ctx.move_to(*WIN[0]), [ctx.line_to(*p) for p in WIN[1:]], ctx.close_path())
    ctx.save()
    path()
    ctx.clip()
    setc(ctx, hexc('#2c2d38'))
    ctx.paint()
    g = cairo.LinearGradient(0, 200, 0, 560)
    g.add_color_stop_rgb(0, *hexc('#8fa6bf'))
    g.add_color_stop_rgb(1, *hexc('#dfe8f0'))
    ctx.set_source(g)
    ctx.rectangle(560, 200, 1200, 360)
    ctx.fill()
    ctx.rectangle(560, 430, 1200, 140)
    setc(ctx, C_SNOW)
    ctx.fill()
    off = (t * 700) % 260
    for k in range(-1, 7):
        poly(ctx, [(600 + k * 260 + off, 300), (560 + k * 260 + off, 440), (640 + k * 260 + off, 440)])
        fill_stroke(ctx, hexc('#2f6b45'), OUTL, 3)
    ctx.rectangle(0, 120, SW, 80)
    setc(ctx, hexc('#4a4b58'))
    ctx.fill()
    rrect(ctx, 1080, 300, 300, 700, 90)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 5)
    rrect(ctx, 1110, 250, 230, 150, 60)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 5)
    head2d(ctx, 900, 480, 175, 'hero', kw.get('expr', 'shock'), kw.get('turn', -0.6), t)
    a = 0.25 + 0.25 * math.sin(t * 12)
    glow(ctx, 380, 380, 320, (1.0, 0.97, 0.85), a)       # oncoming headlights through the windshield side
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
    snowfall(ctx, t, 50)


def call_card(ctx, w, t, lt, kw):
    setc(ctx, hexc('#1f2b38'))
    ctx.paint()
    rrect(ctx, 120, 90, 620, 900, 70)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, 8)
    rrect(ctx, 150, 140, 560, 800, 40)
    setc(ctx, hexc('#14325a'))
    ctx.fill()
    text_center(ctx, 'Calling', 430, 300, 56, (0.8, 0.9, 1.0))
    text_center(ctx, '911', 430, 440, 140, (1, 1, 1))
    for k in range(3):
        a = (lt * 2 - k * 0.3) % 1
        ctx.arc(430, 650, 60 + a * 110, 0, 2 * math.pi)
        setc(ctx, (0.5, 0.8, 1.0), 1 - a)
        ctx.set_line_width(5)
        ctx.stroke()
    ellipse(ctx, 430, 650, 56, 56)
    setc(ctx, hexc('#22c35e'))
    ctx.fill()
    text_center(ctx, 'Tell them:', 1300, 200, 64, (1, 1, 1))
    rows = ['Wrong-way driver', 'Highway 400, near Barrie', 'Going NORTH in the southbound lanes', 'Left lane, black car']
    for i, r_ in enumerate(rows):
        if lt < 0.4 + i * 0.5:
            continue
        a = smooth((lt - 0.4 - i * 0.5) / 0.25)
        rrect(ctx, 830, 280 + i * 150, 950, 110, 36)
        setc(ctx, hexc('#22a356'), 0.9 * a)
        ctx.fill()
        text_center(ctx, r_, 1305, 350 + i * 150, 48, (1, 1, 1), a=a)


def why_right(ctx, w, t, lt, kw):
    """Why move RIGHT: wrong-way drivers usually drive in the left lane (their 'right' lane)."""
    setc(ctx, C_SNOW)
    ctx.paint()
    view = HTop(3.5, 0.0, 45.0, 960, 520)
    gquad(ctx, view, -0.8, 10.0, -60, 60, hexc('#8d8f96'))
    gquad(ctx, view, 0.0, 7.0, -60, 60, C_ASPH)
    for k in range(-6, 6):
        gquad(ctx, view, 3.43, 3.57, k * 12, k * 12 + 4, C_LINE)
    gquad(ctx, view, 0.05, 0.2, -60, 60, C_YEL)
    u = smooth(lt / 1.6)
    draw_car_top_g(ctx, view, 1.75, 16 - 20 * u, math.pi, '#1c1c22', t)
    a, b = view.pt((1.75, 0, 40)), view.pt((1.75, 0, 40 - 70 * u))
    arrow_path(ctx, [a, b], hexc('#ff4b4b'), 12, 0.9, (22, 14), 30)
    draw_car_top_g(ctx, view, 5.25, -16 + 8 * u, 0.0, '#e23b3b', t, None, True)
    p = view.pt((1.75, 0, 10))
    label(ctx, 960, p[1] - 80, 'Wrong-way drivers usually use THIS lane', '#e0393e', 46)
    q = view.pt((5.25, 0, -18))
    label(ctx, 960, q[1] + 120, 'You: keep RIGHT', '#22a356', 50)


engine.SCENES.update(w_cam=w_cam, win_face=win_face, call_card=call_card, why_right=why_right)

HOOK = dict(cam='chase', gap=True)
LOW_W = dict(cam='rel', off=(3.2, 1.2, -6.0), look=(0.0, 1.0, 40.0), f=1000, freeze=T_FREEZE, gap=True, hud=False)
PASS_R = dict(cam='fixed', pos=(8.8, 1.6, 0.0), target=(3.0, 0.9, 0.0), f=900, hud=False)
defs = [
    (3.0, 'w_cam', dict(HOOK)),
    (6.0, 'w_cam', dict(cam='chase')),
    (8.5, 'w_cam', dict(cam='inside', gap=True)),
    (11.0, 'w_cam', dict(cam='high', hud=False, gap=True)),
    (13.0, 'win_face', dict(expr='shock', turn=-0.6)),
    (15.5, 'w_cam', dict(LOW_W)),
    (T_R0, 'rewind_seq', dict()),
    (19.2, 'w_cam', dict(cam='inside', gap=True)),
    (22.2, 'w_cam', dict(cam='high', hud=False, gap=True)),
    (24.7, 'w_cam', dict(PASS_R)),
    (27.7, 'w_cam', dict(cam='high', hud=False)),
    (30.7, 'call_card', dict()),
    (33.5, 'why_right', dict()),
    (DUR, 'w_cam', dict(cam='chase', hud=False)),
]
shots = build_shots(defs)
shots[6].kw.update(srcs=list(reversed(shots[1:6])), dur=shots[6].dur)
z_pass = HERO_R.z(T_PASS)
shots[9].kw.update(pos=(9.8, 1.7, z_pass + 24.0), target=(3.0, 0.9, z_pass + 2.0))
video = Video(['A car is coming at you.', 'In YOUR lane. What do you do?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('It is coming the WRONG way!', 300, 100, hexc('#ffd23f'), 0.2, True)),
    (3.0, 6.0, location_tag('Highway 400 near Barrie, Ontario')),
    (3.2, 6.0, caption('Left lane, 100 km/h')),
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, E[2], caption('Headlights... in YOUR lane?')),
    (S[3] + 0.2, E[3], caption('Closing at about 55 m every second')),
    (S[4] + 0.2, E[4], caption('He freezes and stays in the left lane')),
    (S[5] + 0.2, E[5], caption('No time left to react')),
    (S[5] + 1.0, E[5], x_mark),
    (S[9], E[9], badge('RIGHT', '#22a356')),
    (S[9] + 0.2, E[9], caption('It passes by in the left lane')),
    (S[12], E[12], badge('WHY RIGHT?', '#3a3d48')),
    (S[13] + 0.2, E[13], end_card('Slow down. Move RIGHT. Call 911.', 'Ever seen a wrong-way driver? Comment!')),
]
for n, (i, txt) in enumerate(((7, 'Slow down. Ease off and brake.'), (8, 'Move RIGHT, away from it'), (10, 'Pull over safely. Call 911.')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]


# ------------------------------------------------------------------ sound
def snow_wind(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return lp(noise(n), 600) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * tt) ** 2)


def sound():
    m = Mixer(video.dur)
    m.add(snow_wind(video.dur), 0, 0.2)
    hook_sfx(m)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.13)
    m.add(horn(1.2), 1.4, 0.8)
    m.add(heartbeat(4, 130), S[2] + 0.4, 0.7)
    m.add(horn(0.5), 12.2, 0.8)
    m.add(horn(0.5), 12.9, 0.8)
    m.add(riser(2.2), 12.9, 0.6)
    m.add(impact(), T_FREEZE, 0.45)
    m.add(sad_violin(), T_FREEZE + 0.05, 0.85)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(brake_squeal(1.2), 18.7, 0.3)
    m.add(click(), 18.9, 0.7)
    indicator(m, 18.9, 21.0, 0.4, 0.2)
    m.add(horn(0.4), 19.6, 0.6)
    m.add(car_pass(1.8, 0.5, 110), T_PASS - 0.9, 1.0, np.linspace(0.7, -0.7, int(1.8 * SR)))
    m.add(whoosh(1.0, 0.45), T_PASS - 0.5, 0.7)
    indicator(m, 24.2, 26.8, 0.4, 0.2)
    indicator(m, 27.6, 30.7, 0.35, 0.0)
    for i in (7, 8, 10):
        m.add(pop(), S[i] + 0.15, 0.6)
    for k in range(3):
        m.add(beep_tone(), S[11] + 0.2 + k * 0.25, 0.5)
    m.add(chime(), S[12] + 0.5, 0.6)
    m.add(success_jingle(), S[13] + 0.3, 0.8)
    return m.out(video.dur)


def beep_tone():
    tt = np.arange(int(0.15 * SR)) / SR
    return np.sin(2 * np.pi * 1209 * tt) * 0.3 + np.sin(2 * np.pi * 697 * tt) * 0.3


def verify():
    print('wrong: gap at freeze', round(WW_W.z(T_FREEZE) - HERO_W.z(T_FREEZE) - 4.4, 1), 'm | gap when first seen (t=6):',
          round(WW_W.z(6) - HERO_W.z(6), 0), 'm')
    t_in = next(t for t in np.arange(T_R0, 30, 0.01) if X_R(t) - 0.92 > 1.75 + 0.92 + 0.3)
    print('right: hero fully in right lane at t =', round(t_in, 2), '| ww car passes at', T_PASS,
          '| gap then', round(WW_R.z(t_in) - HERO_R.z(t_in), 1), 'm')
    print('   lateral clearance when passing', round(X_R(T_PASS) - 1.75 - 1.84, 2), 'm | stops on shoulder x', X_R(30))
    worst = 99
    for t in np.arange(T_R0, DUR, 0.05):
        for c in TRAF_R:
            x, z, h = HERO_R.pose(t)
            if abs(c.pose(t)[0] - x) < 1.95:
                worst = min(worst, abs(c.z(t) - z) - 4.4)
    print('   min gap to right-lane cars', round(worst, 2))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        run(video, sound, 'wrongway.mp4')
