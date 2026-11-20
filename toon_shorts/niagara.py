"""QEW near Niagara Falls: highway EXIT world in the multi-angle 2D house style.

World: +Z = travel direction (toward Niagara Falls), +X = right. Lanes: left -3.6..0, right 0..3.6.
Exit: taper Z -70..0 (3.6 -> 7.2), exit (deceleration) lane 3.6..7.2 from Z 0 to E1, then the off-ramp
curves away to the right: x = 5.4 + K (z - E1)^2. Scenery: vineyards, Skylon Tower, hotels, falls mist.
"""
import math
import random

import cairo
import numpy as np

from toronto import *
import toronto

E1 = 155.0
K = 0.0035
TAPER0 = -70.0
GANTRY_Z = -260.0
C_SOIL = hexc('#b08a5e')
C_VINE = hexc('#4f9a3f')


def ramp_xn(z):
    return 5.4 + K * (z - E1) ** 2 if z > E1 else 5.4


RAMPN = [(ramp_xn(z), z) for z in np.arange(E1 - 2, E1 + 190, 1.0)]


class NWorld:
    def __init__(self, dur, speed, z0, lat, blink_right, traffic, oncoming):
        self.dur, self.speed, self.lat = dur, speed, lat
        self.blink_right = blink_right
        self.blink_left = lambda t: 0.0
        self.headlights = const(0)
        self.ego_brake = const(0)
        self.shake = const(0)
        self.traffic, self.oncoming = traffic, oncoming
        self._g = np.arange(0, dur + 2, 1 / 120)
        v = np.array([speed(t) for t in self._g])
        self._z = z0 + np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 / 120)])

    def blink_on(self, t):
        return self.blink_right(t) > 0.5

    def ego_z(self, t):
        return float(np.interp(t, self._g, self._z))

    def ego_xz(self, t):
        z = self.ego_z(t)
        return (ramp_xn(z) if z > E1 else -1.8 + self.lat(t)), z

    def heading(self, t):
        x0, z0 = self.ego_xz(t - 0.12)
        x1, z1 = self.ego_xz(t + 0.12)
        return math.atan2(x1 - x0, z1 - z0)

    def steer(self, t):
        return (self.heading(t + 0.15) - self.heading(t - 0.15)) / 0.3 * 0.35

    def dist(self, t):
        return self.ego_z(t)

    def camx(self, t):
        return self.ego_xz(t)[0]

    def cars(self, t):
        out = [(c['x'], c['z0'] + c['v'] * t, 0.0, c['col']) for c in self.traffic]
        out += [(c['x'], c['z0'] - 27 * t, math.pi, c['col']) for c in self.oncoming]
        return out


# ------------------------------------------------------------- cars with a right indicator
def draw_car_n(ctx, view, x, z, h, col, t, blink=False, lw=None):
    Lf = L(x, z, h)
    body = hexc(col)
    dark = mix(body, (0, 0, 0), 0.3)
    glass = hexc('#2a3448')
    d = view.depth((x, 0.8, z))
    lw = lw or max(1.5, min(4.5, 60 / max(d, 1)))
    for wx in (-0.86, 0.86):
        for wz in (-1.38, 1.38):
            lbox(ctx, view, Lf, h, wx - 0.15, wx + 0.15, 0, 0.62, wz - 0.33, wz + 0.33,
                 {k: hexc('#1c1c22') for k in ('front', 'back', 'left', 'right', 'top')}, lw)
    vis = lbox(ctx, view, Lf, h, -0.92, 0.92, 0.28, 0.88, -2.2, 2.2,
               {'front': body, 'back': body, 'left': dark, 'right': dark, 'top': body}, lw)
    lbox(ctx, view, Lf, h, -0.78, 0.78, 0.88, 1.42, -1.25, 0.95,
         {'front': glass, 'back': glass, 'left': glass, 'right': glass, 'top': body}, lw)
    on = bool(blink)
    amb, off = AMBER, hexc('#7a4a00')
    if 'back' in vis:
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'back', s * 0.62 - 0.2, s * 0.62 + 0.2, 0.62, 0.78, -2.21, hexc('#b01818'))
        face_rect(ctx, view, Lf, 'back', -0.25, 0.25, 0.42, 0.56, -2.21, hexc('#e8e8ee'))
        face_rect(ctx, view, Lf, 'back', 0.66, 0.9, 0.6, 0.8, -2.22, amb if on else off, amb if on else None, 1.6)
    if 'front' in vis:
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'front', s * 0.6 - 0.22, s * 0.6 + 0.22, 0.6, 0.76, 2.21, hexc('#fff6d8'))
        face_rect(ctx, view, Lf, 'front', 0.7, 0.9, 0.6, 0.76, 2.22, amb if on else off, amb if on else None, 1.2)
    if 'right' in vis:
        face_rect(ctx, view, Lf, 'right', 1.2, 1.5, 0.6, 0.72, 0.93, amb if on else off, amb if on else None, 1.0)


def draw_car_top_n(ctx, view, x, z, h, col, t, blink=False, ego=False):
    cx, cy = view.pt((x, 0, z))
    s = view.s
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(-h)
    Lr, Wr = 4.4 * s, 1.84 * s
    if ego:
        glow(ctx, 0, 0, 4.0 * s, hexc('#ffffff'), 0.5)
    rrect(ctx, -Lr / 2, -Wr / 2, Lr, Wr, Wr * 0.35)
    fill_stroke(ctx, hexc(col), OUTL, 3)
    poly(ctx, [(Lr * 0.12, -Wr * 0.4), (Lr * 0.3, -Wr * 0.34), (Lr * 0.3, Wr * 0.34), (Lr * 0.12, Wr * 0.4)])
    setc(ctx, hexc('#2a3448'))
    ctx.fill()
    if blink:
        for px in (Lr * 0.46, -Lr * 0.46):
            glow(ctx, px, Wr * 0.42, 1.8 * s, AMBER, 0.9)
            ellipse(ctx, px, Wr * 0.42, 0.35 * s, 0.35 * s)
            setc(ctx, AMBER)
            ctx.fill()
    ctx.restore()


# ------------------------------------------------------------- scenery
def vine_rows(ctx, view, x0, x1, z0, z1):
    gquad(ctx, view, x0, x1, z0, z1, C_SOIL)
    for x in np.arange(x0 + 0.8, x1, 2.6):
        gquad(ctx, view, x, x + 1.1, z0 + 1, z1 - 1, C_VINE, 0.02)


def skylon(ctx, view):
    """Niagara Falls skyline: Skylon Tower, hotel towers, mist from the falls (far ahead, right)."""
    if view.ortho:
        return
    haze = hexc('#c3dcee')
    rnd = random.Random(31)
    blds = []
    for i in range(16):
        X = 40 + i * 26 + rnd.uniform(-8, 8)
        if abs(X - 170) < 25:
            continue
        blds.append((X, E1 + 1500 + rnd.uniform(-80, 80), rnd.uniform(22, 38), rnd.uniform(45, 125)))
    for X, Z, w, hgt in sorted(blds, key=lambda b: -b[1]):
        b, tp, sc = view.pt((X, 0, Z)), view.pt((X, hgt, Z)), view.scale((X, 0, Z))
        if not b or not tp:
            continue
        ctx.rectangle(b[0] - w * sc / 2, tp[1], w * sc, b[1] - tp[1])
        setc(ctx, mix(hexc('#8aa3b8'), haze, 0.3 + 0.3 * rnd.random()))
        ctx.fill()
    # mist plume from the falls
    for i in range(9):
        X, Y = -40 + i * 9 + rnd.uniform(-5, 5), 25 + i * 9 + rnd.uniform(-4, 4)
        p, sc = view.pt((X, Y, E1 + 1400)), view.scale((X, Y, E1 + 1400))
        if p and sc:
            ellipse(ctx, p[0], p[1], 28 * sc, 18 * sc)
            setc(ctx, (1, 1, 1), 0.55)
            ctx.fill()
    X, Z = 170.0, E1 + 1350.0
    b, sc = view.pt((X, 0, Z)), view.scale((X, 0, Z))
    if not b or not sc:
        return
    bx, by = b
    Y = lambda m: by - m * sc
    col = mix(hexc('#7d8796'), haze, 0.2)
    ctx.rectangle(bx - 5 * sc, Y(150), 10 * sc, 150 * sc)
    setc(ctx, col)
    ctx.fill()
    poly(ctx, [(bx - 16 * sc, by), (bx + 16 * sc, by), (bx + 5 * sc, Y(20)), (bx - 5 * sc, Y(20))])
    ctx.fill()
    # yellow outside elevator
    ctx.rectangle(bx + 5 * sc, Y(95), 4 * sc, 6 * sc)
    setc(ctx, hexc('#f2c230'))
    ctx.fill()
    # pod: three stacked rings
    for y0, w in ((140, 22), (148, 26), (156, 20)):
        rrect(ctx, bx - w * sc, Y(y0 + 7), 2 * w * sc, 7 * sc, 3 * sc)
        setc(ctx, mix(hexc('#5d6878'), haze, 0.15))
        ctx.fill()
    ctx.rectangle(bx - 1 * sc, Y(175), 2 * sc, 12 * sc)
    setc(ctx, col)
    ctx.fill()


TREESN = []
_r = random.Random(5)
for zz in np.arange(-700, 1600, 13):
    TREESN.append((-15.5 - _r.uniform(0, 1.5), zz + _r.uniform(-3, 3), 0.9 + _r.uniform(0, 0.4)))
    for xr in (12.5 + _r.uniform(0, 2), ):
        if zz < E1 - 10 or abs(xr - ramp_xn(zz)) > 9:
            TREESN.append((xr, zz + _r.uniform(-3, 3), 0.9 + _r.uniform(0, 0.4)))
for zz in np.arange(E1 + 40, E1 + 190, 11):          # outside the ramp curve
    TREESN.append((ramp_xn(zz) + 8 + _r.uniform(0, 3), zz, 1.0 + _r.uniform(0, 0.4)))


def gantry_n(ctx, view):
    z = GANTRY_Z
    if view.ortho:
        gquad(ctx, view, -5.0, 9.0, z - 0.6, z + 0.6, hexc('#6a6f7c'))
        return
    for px in (-5.2, 9.0):
        fill_poly(ctx, view, [(px - 0.25, 0, z), (px + 0.25, 0, z), (px + 0.25, 7.8, z), (px - 0.25, 7.8, z)],
                  hexc('#8a8f9c'), OUTL, 2)
    fill_poly(ctx, view, [(-5.2, 7.4, z), (9.0, 7.4, z), (9.0, 7.8, z), (-5.2, 7.8, z)], hexc('#8a8f9c'), OUTL, 2)
    pts = [(-1.2, 4.2, z - 0.05), (7.6, 4.2, z - 0.05), (7.6, 8.4, z - 0.05), (-1.2, 8.4, z - 0.05)]
    sp = view.poly(pts)
    if not sp:
        return
    poly(ctx, sp)
    fill_stroke(ctx, hexc('#1f7a43'), (1, 1, 1), 3)
    c, s = view.pt((3.2, 6.3, z)), view.scale((3.2, 6.3, z))
    if c and s and s > 4:
        text_center(ctx, 'Niagara Falls', c[0], c[1] - 0.2 * s, 1.15 * s, (1, 1, 1))
        text_center(ctx, 'EXIT  300 m', c[0] - 0.7 * s, c[1] + 1.4 * s, 0.95 * s, (1, 1, 1))
        s = s * 1.5
        ax, ay = c[0] + 2.4 * s, c[1] + 0.75 * s
        ctx.move_to(ax - 0.35 * s, ay - 0.35 * s)
        ctx.line_to(ax + 0.25 * s, ay + 0.25 * s)
        setc(ctx, (1, 1, 1))
        ctx.set_line_width(0.14 * s)
        ctx.stroke()
        poly(ctx, [(ax + 0.38 * s, ay + 0.38 * s), (ax - 0.05 * s, ay + 0.3 * s), (ax + 0.3 * s, ay - 0.05 * s)])
        ctx.fill()


def post_sign(ctx, view, x, z, kind):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 2.4, z)), view.scale((x, 2.4, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.06 * s, tp[1], 0.12 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#8a8f9c'), OUTL, 2)
    if kind == 'exit':
        rrect(ctx, tp[0] - 0.8 * s, tp[1] - 0.75 * s, 1.6 * s, 0.75 * s, 0.08 * s)
        fill_stroke(ctx, hexc('#1f7a43'), (1, 1, 1), max(2, s / 25))
        if s > 10:
            text_center(ctx, 'EXIT', tp[0], tp[1] - 0.2 * s, 0.48 * s, (1, 1, 1))
        return
    # advisory: yellow diamond with right-curve arrow + yellow "50 km/h" tab
    r = 0.62 * s
    cx_, cy_ = tp[0], tp[1] - r - 0.5 * s
    rrect(ctx, cx_ - 0.6 * s, tp[1] - 0.48 * s, 1.2 * s, 0.46 * s, 0.05 * s)
    fill_stroke(ctx, hexc('#f2c230'), OUTL, max(2, s / 25))
    if s > 10:
        text_center(ctx, '50 km/h', cx_, tp[1] - 0.12 * s, 0.3 * s, OUTL)
    poly(ctx, [(cx_, cy_ - r), (cx_ + r, cy_), (cx_, cy_ + r), (cx_ - r, cy_)])
    fill_stroke(ctx, hexc('#f2c230'), OUTL, max(2, s / 25))
    ctx.move_to(cx_ - r * 0.15, cy_ + r * 0.55)
    ctx.curve_to(cx_ - r * 0.15, cy_ - r * 0.1, cx_, cy_ - r * 0.25, cx_ + r * 0.25, cy_ - r * 0.25)
    setc(ctx, OUTL)
    ctx.set_line_width(max(2, r * 0.13))
    ctx.stroke()
    poly(ctx, [(cx_ + r * 0.45, cy_ - r * 0.25), (cx_ + r * 0.2, cy_ - r * 0.45), (cx_ + r * 0.2, cy_ - r * 0.05)])
    ctx.fill()


# ------------------------------------------------------------- world render
def draw_world_n(ctx, view, w, t, ego=True, overlay=None):
    ez = w.ego_z(t)
    zlo, zhi = ez - 220, ez + 1000
    if view.ortho:
        setc(ctx, C_GRASS)
        ctx.paint()
    else:
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 700, 0, hy)
        g.add_color_stop_rgb(0, *hexc('#5fb4f2'))
        g.add_color_stop_rgb(1, *hexc('#d9f1ff'))
        ctx.set_source(g)
        ctx.rectangle(-50, -50, SW + 100, hy + 52)
        ctx.fill()
        for cx0, cy0, sc0 in ((240, 110, 1.0), (1020, 70, 0.8), (1620, 150, 1.1)):
            for dx, dy, r in ((0, 0, 60), (60, -25, 70), (130, 0, 55), (60, 15, 60)):
                ellipse(ctx, cx0 + dx * sc0, hy - 520 + cy0 + dy * sc0, r * sc0, r * sc0 * 0.8)
            setc(ctx, (1, 1, 1), 0.9)
            ctx.fill()
        setc(ctx, C_GRASS)
        ctx.rectangle(-50, hy, SW + 100, SH + 100 - hy)
        ctx.fill()
        skylon(ctx, view)
    # vineyards
    vine_rows(ctx, view, -60, -18, zlo, zhi)
    vine_rows(ctx, view, 16, 60, zlo, min(zhi, E1 + 10))
    if zhi > E1 + 150:
        vine_rows(ctx, view, 16, 60, E1 + 150, zhi)
    # opposite carriageway
    gquad(ctx, view, -13.2, -5.2, zlo, zhi, C_ASPH)
    for k in range(int(zlo // 12), int(zhi // 12) + 1):
        gquad(ctx, view, -8.9, -8.75, k * 12, k * 12 + 4, C_LINE, 0.01)
    # our carriageway + exit
    gquad(ctx, view, -4.5, 3.6, zlo, zhi, C_ASPH)
    gquad(ctx, view, 3.6, 4.6, zlo, TAPER0, C_SHOULDER)
    gquad(ctx, view, 3.6, 4.6, E1 + 20, zhi, C_SHOULDER)
    fill_poly(ctx, view, [(3.6, 0, TAPER0), (7.2, 0, 0), (3.6, 0, 0)], C_ASPH)
    gquad(ctx, view, 3.6, 7.2, 0, E1, C_ASPH)
    ribbon3(ctx, view, RAMPN, 4.4, C_ASPH)
    if overlay:
        overlay(ctx, view)
    # markings
    for k in range(int(zlo // 12), int(zhi // 12) + 1):
        gquad(ctx, view, -0.08, 0.08, k * 12, k * 12 + 4, C_LINE, 0.01)
    gquad(ctx, view, -3.75, -3.6, zlo, zhi, C_YEL, 0.01)
    gquad(ctx, view, 3.5, 3.7, zlo, TAPER0, C_LINE, 0.01)
    gquad(ctx, view, 3.5, 3.7, E1, zhi, C_LINE, 0.01)
    for k in range(int(TAPER0 // 4), int(E1 // 4)):
        gquad(ctx, view, 3.45, 3.75, k * 4, k * 4 + 2, C_LINE, 0.01)
    fill_poly(ctx, view, [(3.6, 0.01, TAPER0), (3.75, 0.01, TAPER0), (7.25, 0.01, 0), (7.1, 0.01, 0)], C_LINE)
    gquad(ctx, view, 7.1, 7.25, 0, E1, C_LINE, 0.01)
    ribbon3(ctx, view, RAMPN, 0.16, C_LINE, 0.01, -2.05)
    ribbon3(ctx, view, RAMPN, 0.16, C_LINE, 0.01, 2.05)
    # depth-sorted objects
    far, near = [], []
    for x, z, s in TREESN:
        if zlo < z < zhi:
            sz = s * (0.45 if view.ortho else 1.0)
            (far if x < -5 else near).append(((x, 1.5, z), lambda x=x, z=z, sz=sz: tree3(ctx, view, x, z, sz, int(abs(z)) % 3)))
    for x, z, h, col in w.cars(t):
        if zlo < z < zhi:
            fn = (lambda x=x, z=z, h=h, col=col: draw_car_top_n(ctx, view, x, z, h, col, t)) if view.ortho else \
                 (lambda x=x, z=z, h=h, col=col: draw_car_n(ctx, view, x, z, h, col, t))
            (far if x < -5 else near).append(((x, 0.8, z), fn))
    if ego:
        ex, ezz = w.ego_xz(t)
        h = w.heading(t)
        bl = w.blink_on(t)
        fn = (lambda: draw_car_top_n(ctx, view, ex, ezz, h, C_EGO, t, bl, True)) if view.ortho else \
             (lambda: draw_car_n(ctx, view, ex, ezz, h, C_EGO, t, bl))
        near.append(((ex, 0.8, ezz), fn))
    near.append(((2.0, 5.0, GANTRY_Z), lambda: gantry_n(ctx, view)))
    near.append(((5.0, 1.5, E1 + 30), lambda: post_sign(ctx, view, 5.0, E1 + 30, 'exit')))
    near.append(((ramp_xn(E1 + 22) + 3.2, 1.5, E1 + 22),
                 lambda: post_sign(ctx, view, ramp_xn(E1 + 22) + 3.2, E1 + 22, 'advisory')))
    key = (lambda it: 0) if view.ortho else (lambda it: -view.depth(it[0]))
    for it in sorted(far, key=key):
        it[1]()
    if view.ortho:
        gquad(ctx, view, -5.0, -4.6, zlo, zhi, C_WALL)
    else:
        fill_poly(ctx, view, [(-4.6, 0, zlo), (-4.6, 0, zhi), (-4.6, 1.0, zhi), (-4.6, 1.0, zlo)], mix(C_WALL, (0, 0, 0), 0.1))
        fill_poly(ctx, view, [(-5.0, 1.0, zlo), (-4.6, 1.0, zlo), (-4.6, 1.0, zhi), (-5.0, 1.0, zhi)], C_WALL)
    for it in sorted(near, key=key):
        it[1]()
    if not view.ortho:
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 30, 0, hy + 140)
        g.add_color_stop_rgba(0, 0.85, 0.95, 1, 0.0)
        g.add_color_stop_rgba(0.25, 0.85, 0.95, 1, 0.45)
        g.add_color_stop_rgba(1, 0.85, 0.95, 1, 0.0)
        ctx.set_source(g)
        ctx.rectangle(-50, hy - 30, SW + 100, 170)
        ctx.fill()


# ------------------------------------------------------------- cameras / scenes
def cam_n(w, t, mode):
    ex, ez = w.ego_xz(t)
    h = w.heading(t)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    if mode == 'chase':
        return TCam((ex - fx * 10.5, 3.6, ez - fz * 10.5), h, 0.16, 1000, cy=520)
    if mode == 'close_r':
        return TCam((ex - fx * 5.6 + rx * 1.3, 1.7, ez - fz * 5.6 + rz * 1.3), h - 0.13, 0.08, 1000)
    if mode == 'wide':
        return TCam((ex - fx * 18 - rx * 5, 8.0, ez - fz * 18 - rz * 5), h + 0.2, 0.2, 1000, cy=500)
    if mode == 'inside':
        return TCam((ex - rx * 0.38 - fx * 0.2, 1.18, ez - rz * 0.38 - fz * 0.2), h, 0.03, 1000, cy=470)
    raise ValueError(mode)


def n_chase(ctx, world, t, lt, kw):
    draw_world_n(ctx, cam_n(world, t, kw.get('cam', 'chase')), world, t)
    if kw.get('hud', True):
        hud_speed(ctx, world, t)


def n_inside(ctx, world, t, lt, kw):
    cam = cam_n(world, t, 'inside')
    draw_world_n(ctx, cam, world, t, ego=False)
    kit.cockpit_day_nomirror(ctx, world, t, cam)
    if world.blink_on(t):
        glow(ctx, 1050, 880, 70, hexc('#2bff6a'), 0.5)
        poly(ctx, [(1080, 880), (1040, 852), (1040, 868), (1010, 868), (1010, 892), (1040, 892), (1040, 908)])
        setc(ctx, hexc('#2bff6a'))
        ctx.fill()
    hud_speed(ctx, world, t)


def n_mirror(ctx, world, t, lt, kw):
    """RIGHT outside mirror close-up (layout of the approved left-mirror shot, mirrored)."""
    ex, ez = world.ego_xz(t)
    h = world.heading(t)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    draw_world_n(ctx, TCam((ex + rx * 0.5, 1.2, ez + rz * 0.5), h + 0.75, 0.05, 700), world, t, ego=False)
    setc(ctx, (0.05, 0.08, 0.15), 0.25)
    ctx.paint()
    mx, my, rot = 930, 520, -0.06

    def flipped(fn):
        ctx.save()
        ctx.translate(SW, 0)
        ctx.scale(-1, 1)
        fn()
        ctx.restore()

    def frame():
        poly(ctx, [(1700, -10), (SW + 10, -10), (SW + 10, SH + 10), (1450, SH + 10), (1640, 600)])
        fill_stroke(ctx, hexc('#b92f2f'), OUTL, 6)
        poly(ctx, [(1640, 600), (1450, SH + 10), (1380, SH + 10), (1590, 560)])
        fill_stroke(ctx, hexc('#2a2a36'), OUTL, 4)
        ctx.save()
        ctx.translate(mx, my)
        ctx.rotate(rot)
        rrect(ctx, -560, -330, 1120, 660, 300)
        fill_stroke(ctx, hexc('#c23535'), OUTL, 7)
        rrect(ctx, -520, -290, 1040, 580, 260)
        fill_stroke(ctx, hexc('#0b1424'), OUTL, 5)
        ctx.restore()
    flipped(frame)

    def glass_path():
        ctx.translate(mx, my)
        ctx.rotate(rot)
        rrect(ctx, -500, -270, 1000, 540, 240)
    ctx.save()
    flipped(glass_path)
    ctx.clip()
    mcam = TCam((ex + rx * 1.05 + fx * 0.6, 1.05, ez + rz * 1.05 + fz * 0.6), h + math.pi - 0.22, 0.04, 900,
                cx=SW - (mx + 120), cy=my - 40, mirror=True)
    draw_world_n(ctx, mcam, world, t, ego=False)

    def body():
        poly(ctx, [(mx + 330, my - 40), (mx + 520, my - 90), (mx + 520, my + 300), (mx + 260, my + 300)])
        fill_stroke(ctx, hexc(C_EGO), OUTL, 5)
    flipped(body)
    g = cairo.LinearGradient(SW - mx - 500, my - 270, SW - mx + 100, my + 270)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.12)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    if world.blink_on(t):
        bx, by = SW - (mx - 430), my + 250
        rrect(ctx, bx - 70, by - 18, 140, 36, 18)
        setc(ctx, AMBER)
        ctx.fill()
        glow(ctx, bx, by, 200, AMBER, 0.7)


def n_shoulder(ctx, world, t, lt, kw):
    """Over-the-RIGHT-shoulder look through the rear right window."""
    ex, ez = world.ego_xz(t)
    h = world.heading(t)
    rx, rz = math.cos(h), -math.sin(h)
    draw_world_n(ctx, TCam((ex - rx * 0.35, 1.2, ez - rz * 0.35), h + 2.2, 0.03, 800, cx=SW - 900), world, t, ego=False)
    ctx.save()
    ctx.translate(SW, 0)
    ctx.scale(-1, 1)
    setc(ctx, hexc('#2a2a36'))
    ctx.rectangle(-10, -10, SW + 20, 130)
    ctx.fill()
    poly(ctx, [(1560, -10), (1930, -10), (1930, SH + 10), (1700, SH + 10)])
    ctx.fill()
    poly(ctx, [(-10, -10), (140, -10), (60, 870), (-10, 870)])
    ctx.fill()
    ctx.rectangle(-10, 860, 1700, 240)
    setc(ctx, hexc('#b92f2f'))
    ctx.fill()
    ctx.rectangle(-10, 850, 1700, 18)
    setc(ctx, OUTL)
    ctx.fill()
    rrect(ctx, 1380, 330, 420, 800, 110)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 6)
    ctx.move_to(1250, SH + 10)
    ctx.curve_to(1300, 760, 1600, 700, 1930, 720)
    ctx.line_to(1930, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    ctx.restore()


def label(ctx, x, y, text, col, size=38):
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    w = ctx.text_extents(text).x_advance
    rrect(ctx, x - w / 2 - 18, y - size - 4, w + 36, size + 22, 14)
    fill_stroke(ctx, col, (1, 1, 1), 3)
    ctx.move_to(x - w / 2, y + 2)
    setc(ctx, (1, 1, 1))
    ctx.show_text(text)


def n_top(ctx, world, t, lt, kw):
    s, ox = kw.get('scale', 9.0), kw.get('ox', 170)
    view = TopView(world.ego_z(t), xc=kw.get('xc', 3.0), s=s, ox=ox)
    a = smooth(lt / 0.4)

    def zones(c, v):
        fill_poly(c, v, [(0.1, 0, 0), (3.5, 0, 0), (3.5, 0, E1), (0.1, 0, E1)], hexc('#e0393e'), None, 3, 0.35 * a)
        fill_poly(c, v, [(3.7, 0, 0), (7.2, 0, 0), (7.2, 0, E1), (3.7, 0, E1)], hexc('#22c35e'), None, 3, 0.45 * a)
    draw_world_n(ctx, view, world, t, overlay=zones)
    # planned path
    pts = [view.pt((world.ego_xz(tt)[0], 0, world.ego_xz(tt)[1])) for tt in np.arange(t, 24.5, 0.1)]
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.set_dash([16, 12], -t * 50)
    setc(ctx, (1, 1, 1), a)
    ctx.set_line_width(7)
    ctx.stroke()
    ctx.set_dash([])
    zl = min(max(world.ego_z(t) + 26, 14), E1 - 25)
    r = view.pt((1.8, 0, zl))
    g = view.pt((5.4, 0, zl))
    if a > 0.05:
        label(ctx, r[0], r[1] - 60, "Don't slow down here", hexc('#e0393e'), 48)
        label(ctx, g[0], g[1] + 110, 'Slow down HERE', hexc('#22a356'), 48)


engine.SCENES.update(n_chase=n_chase, n_inside=n_inside, n_mirror=n_mirror, n_shoulder=n_shoulder, n_top=n_top)
