"""Zipper merge, the right way: Montreal expressway roadwork (right lane closed). Hook + myth-buster + 6 steps.
Traffic is generated so cars alternate L, R, L, R through the merge; positions are verified (no overlaps,
every car stays inside the cone taper) before rendering."""
import math
import random

import cairo
import numpy as np

from citykit import *
from truckkit import draw_car_round
import citykit

engine.DAY = True
citykit.draw_car_g = draw_car_round

LX, RX = -1.75, 1.75
TAPER0, TAPER1 = -40.0, 0.0              # right lane narrows from x=3.5 (z=-40) to x=0 (z=0)
ZM = -30.0                                # merge reference (where the zipper "teeth" interlock)
V = 5.0                                   # slow congested traffic, 18 km/h
HEAD = 1.5                                # seconds between cars passing the merge point
T_E = 24.0                                # ego's merge time
K_E = 11                                  # ego's index in the merge order (odd = right lane)
COLS = ['#3a7bd5', '#f4f4f6', '#37b26c', '#f2a541', '#7a4fd0', '#c9c9d6', '#2f6f73', '#e05d5d', '#1c1c22', '#d8c3a0']

P_L = Path([('L', (LX, -400), (LX, 400))])
P_R = Path([('L', (RX, -400), (RX, -46)), ('S', [(RX, -46), (RX, -42), (1.2, -36), (0.0, -31), (-1.2, -26), (LX, -22), (LX, -18)]),
            ('L', (LX, -18), (LX, 400))])


def s_at_z(path, z):
    i = int(np.argmin(np.abs(path.p[:, 1] - z)))
    return float(path.s[i])


def taper_x(z):
    if z <= TAPER0:
        return 3.5
    if z >= TAPER1:
        return 0.0
    return 3.5 * (TAPER1 - z) / (TAPER1 - TAPER0)


class ZCar(Mover):
    pass


def make_car(k):
    lane = 'R' if k % 2 else 'L'
    path = P_R if lane == 'R' else P_L
    tk = T_E + (k - K_E) * HEAD
    col = C_EGO if k == K_E else COLS[(k * 7) % len(COLS)]
    m = ZCar(path, const(V), tk, s_at_z(path, ZM), col, t0=-60, t1=110)
    m.lane, m.k, m.tk = lane, k, tk
    if lane == 'R':
        b = blinking([(-5, 80)], 0.8)
        m.blink = (lambda m=m, b=b: lambda t: 'L' if (-95 < m.pose(t)[1] < -24 and b(t + m.k * 0.13) > 0.5) else None)()
    return m


CARS = [make_car(k) for k in range(-12, 44)]
EGO = next(c for c in CARS if c.k == K_E)
OTHERS = [c for c in CARS if c.k != K_E]


def verify():
    worst_gap, worst_taper = 99.0, 99.0
    for t in np.arange(3.2, 34, 0.1):
        P = [(c.pose(t), c) for c in CARS]
        P = [(p, c) for p, c in P if -260 < p[1] < 120]
        for i in range(len(P)):
            (x1, z1, h1), c1 = P[i]
            if c1.lane == 'R' and z1 < -18:
                # right side of the car (front-right corner) must stay left of the taper line minus 0.2 m
                for lz in (2.2, -2.2):
                    cx = x1 + 0.92 * math.cos(h1) + lz * math.sin(h1)
                    cz = z1 - 0.92 * math.sin(h1) + lz * math.cos(h1)
                    worst_taper = min(worst_taper, taper_x(cz) - cx)
            for j in range(i + 1, len(P)):
                (x2, z2, h2), c2 = P[j]
                if abs(x1 - x2) < 2.1:
                    worst_gap = min(worst_gap, abs(z1 - z2) - 4.4)
    return worst_gap, worst_taper


# ------------------------------------------------------------- hook: two stubborn cars nose to nose
P_HB = Path([('L', (RX, -400), (RX, -46)), ('S', [(RX, -46), (RX, -40), (1.1, -34.5), (0.6, -32.5)])])
hook_r = Mover(P_HB, Key([(-5, 5), (0.6, 5), (1.4, 0), (9, 0)], 'lin'), 1.4, P_HB.length, '#f4f4f6',
               blink=lambda t: 'L' if (t * 1.25) % 1 < 0.5 else None)
hook_l = Mover(P_L, Key([(-5, 5), (0.6, 5), (1.4, 0), (9, 0)], 'lin'), 1.4, s_at_z(P_L, -31.6), '#3a7bd5')
hook_q = [Mover(P_L, Key([(-5, 5), (0.6, 5), (1.4, 0), (9, 0)], 'lin'), 1.4, s_at_z(P_L, -31.6 - 7 * i), COLS[i % 9]) for i in range(1, 9)] + \
         [Mover(P_R, Key([(-5, 5), (0.6, 5), (1.4, 0), (9, 0)], 'lin'), 1.4, s_at_z(P_R, -32.5 - 7 * i), COLS[(i + 4) % 9]) for i in range(1, 8)]


# ------------------------------------------------------------- Montreal expressway + work zone
def orange_diamond(ctx, view, x, z, kind, tab=None):
    def icon(ctx, cx, cy, r):
        ctx.set_line_width(max(2, r * 0.1))
        setc(ctx, OUTL)
        if kind == 'closed':
            ctx.move_to(cx - r * 0.3, cy + r * 0.55)
            ctx.line_to(cx - r * 0.3, cy - r * 0.55)
            ctx.move_to(cx + r * 0.3, cy + r * 0.55)
            ctx.line_to(cx + r * 0.3, cy)
            ctx.line_to(cx + r * 0.02, cy - r * 0.45)
            ctx.stroke()
        else:
            ctx.move_to(cx + r * 0.25, cy + r * 0.55)
            ctx.curve_to(cx + r * 0.25, cy, cx - r * 0.2, cy, cx - r * 0.2, cy - r * 0.3)
            ctx.stroke()
            poly(ctx, [(cx - r * 0.2, cy - r * 0.6), (cx - r * 0.42, cy - r * 0.25), (cx + 0.02 * r, cy - r * 0.25)])
            ctx.fill()
    diamond_sign(ctx, view, x, z, math.pi, icon, tab, col='#f28c28')


def travaux(ctx, view, x, z):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 2.4, z)), view.scale((x, 2.4, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.05 * s, tp[1], 0.1 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#9aa0aa'), OUTL, max(1, s / 40))
    if not front_facing(view, x, z, math.pi):
        return
    rrect(ctx, tp[0] - 0.85 * s, tp[1] - 0.95 * s, 1.7 * s, 0.95 * s, 0.08 * s)
    fill_stroke(ctx, hexc('#f28c28'), OUTL, max(1, s / 40))
    if s > 10:
        text_center(ctx, 'TRAVAUX', tp[0], tp[1] - 0.32 * s, 0.42 * s, OUTL)


def cone(ctx, view, x, z):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], max(2.5, 0.22 * view.s), max(2.5, 0.22 * view.s))
        fill_stroke(ctx, hexc('#f28c28'), OUTL, 1.5)
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 0.75, z)), view.scale((x, 0, z))
    if not b or not tp or not s or s < 2:
        return
    w = 0.22 * s
    poly(ctx, [(b[0] - w, b[1]), (b[0] + w, b[1]), (tp[0], tp[1])])
    fill_stroke(ctx, hexc('#f28c28'), OUTL, max(1, s / 60))
    yy = b[1] + (tp[1] - b[1]) * 0.45
    ctx.rectangle(b[0] - w * 0.55, yy - 0.06 * s, w * 1.1, 0.12 * s)
    setc(ctx, (1, 1, 1))
    ctx.fill()


def barrel(ctx, view, x, z):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], max(3, 0.3 * view.s), max(3, 0.3 * view.s))
        fill_stroke(ctx, hexc('#f28c28'), OUTL, 1.5)
        return
    b, s = view.pt((x, 0, z)), view.scale((x, 0, z))
    if not b or not s or s < 2:
        return
    w, h = 0.3 * s, 1.0 * s
    rrect(ctx, b[0] - w, b[1] - h, 2 * w, h, w * 0.3)
    fill_stroke(ctx, hexc('#f28c28'), OUTL, max(1, s / 60))
    for k in (0.3, 0.65):
        ctx.rectangle(b[0] - w, b[1] - h * k - 0.07 * s, 2 * w, 0.14 * s)
    setc(ctx, (1, 1, 1))
    ctx.fill()


def arrow_board(ctx, view, x, z, t):
    if view.ortho:
        p = view.pt((x, 0, z))
        rrect(ctx, p[0] - 0.9 * view.s, p[1] - 0.6 * view.s, 1.8 * view.s, 1.2 * view.s, 4)
        fill_stroke(ctx, hexc('#f28c28'), OUTL, 2)
        return
    Lf = lambda a, b, c: (a, b, c)
    lbox(ctx, view, Lf, 0.0, x - 0.9, x + 0.9, 0.3, 0.9, z, z + 2.4, {k: hexc('#f28c28') for k in ('front', 'back', 'left', 'right', 'top')}, 2)
    for wx in (-0.75, 0.75):
        pass
    fill_poly(ctx, view, [(x - 1.1, 1.3, z - 0.02), (x + 1.1, 1.3, z - 0.02), (x + 1.1, 2.7, z - 0.02), (x - 1.1, 2.7, z - 0.02)], hexc('#1c1c22'), OUTL, 2)
    on = (t * 1.5) % 1 < 0.6
    if on and front_facing(view, x, z, math.pi):
        pts = [view.pt((x + dx, y, z - 0.04)) for dx, y in ((0.9, 2.0), (-0.5, 2.0))]
        if all(pts):
            arrow_path(ctx, pts, hexc('#ffd23f'), max(3, view.scale((x, 2, z)) * 0.18), 1.0, head=max(8, view.scale((x, 2, z)) * 0.45))
            glow(ctx, pts[1][0], pts[1][1], view.scale((x, 2, z)) * 1.4, hexc('#ffd23f'), 0.5)


class Montreal:
    ground_col = hexc('#8fa37a')
    sky = ('#6aaee6', '#e0f1ff')

    def __init__(self):
        r = random.Random(17)
        self.blds = []
        for sx in (-1, 1):
            z = -320.0
            while z < 420:
                w = r.uniform(14, 26)
                x0 = sx * r.uniform(14, 22)
                x1 = x0 + sx * r.uniform(12, 22)
                self.blds.append((min(x0, x1), max(x0, x1), z, z + w, r.uniform(9, 30),
                                  r.choice(['#c9b9a6', '#a9b8c6', '#d8cfc0', '#8f9aa8', '#b7a28a', '#9fb3a0'])))
                z += w + r.uniform(3, 9)
        self.workers = [(2.2, 34.0), (1.4, 47.0), (2.6, 61.0)]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        p = [view.pt((x, 120 + 70 * math.exp(-((x + 380) / 260) ** 2), 1800)) for x in range(-1200, 1201, 60)]
        base = view.pt((0, 0, 1800))
        if base and all(p):
            ctx.move_to(p[0][0] - 1000, base[1] + 4)
            for q in p:
                ctx.line_to(*q)
            ctx.line_to(p[-1][0] + 1000, base[1] + 4)
            ctx.close_path()
            setc(ctx, hexc('#7fa47a'))
            ctx.fill()
        r = random.Random(4)
        for i in range(22):
            X = -260 + i * 30 + r.uniform(-6, 6)
            b, tp, s = view.pt((X, 0, 1500)), view.pt((X, r.uniform(50, 190), 1500)), view.scale((X, 0, 1500))
            if b and tp:
                ctx.rectangle(b[0] - 12 * s, tp[1], 24 * s, b[1] - tp[1])
                setc(ctx, mix(hexc('#8aa0b5'), hexc('#d4e8f6'), r.uniform(0.25, 0.5)))
                ctx.fill()
        # stadium with its leaning tower (east)
        X, Z = 520.0, 1250.0
        b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
        if b and s:
            ellipse(ctx, b[0], b[1] - 12 * s, 110 * s, 22 * s)
            setc(ctx, hexc('#e9edf2'))
            ctx.fill()
            poly(ctx, [(b[0] + 80 * s, b[1] - 10 * s), (b[0] + 100 * s, b[1] - 10 * s), (b[0] + 10 * s, b[1] - 170 * s), (b[0] - 6 * s, b[1] - 160 * s)])
            setc(ctx, hexc('#dfe4ea'))
            ctx.fill()
            poly(ctx, [(b[0] - 6 * s, b[1] - 160 * s), (b[0] + 10 * s, b[1] - 170 * s), (b[0] + 2 * s, b[1] - 182 * s), (b[0] - 14 * s, b[1] - 170 * s)])
            setc(ctx, hexc('#b9c2cc'))
            ctx.fill()

    def ground(self, ctx, view, t):
        gquad(ctx, view, -5.2, 5.2, -500, 500, C_ASPH)
        gquad(ctx, view, -3.65, -3.5, -500, 500, C_YEL, 0.01)
        gquad(ctx, view, 3.5, 3.65, -500, TAPER0, C_LINE, 0.01)
        for k in range(-60, 0):
            z0 = k * 9.0
            if z0 + 3 <= TAPER0:
                gquad(ctx, view, -0.08, 0.08, z0, z0 + 3, C_LINE, 0.01)
        fill_poly(ctx, view, [(3.5, 0.008, TAPER0), (3.5, 0.008, 500), (0.0, 0.008, 500), (0.0, 0.008, TAPER1)], hexc('#6b6f7c'))
        gquad(ctx, view, -0.08, 0.08, TAPER1, 500, C_LINE, 0.012)
        for sx in (-1, 1):
            fill_poly(ctx, view, [(sx * 5.2, 0, -500), (sx * 5.2, 0, 500), (sx * 5.2, 0.85, 500), (sx * 5.2, 0.85, -500)], hexc('#c9c4ba'), OUTL, 2) \
                if not view.ortho else gquad(ctx, view, *sorted((sx * 5.0, sx * 5.6)), -500, 500, hexc('#c9c4ba'))

    def objects(self, ctx, view, t):
        out = []
        for a in self.blds:
            out.append((((a[0] + a[1]) / 2, a[4] / 2, (a[2] + a[3]) / 2), lambda a=a: building(ctx, view, *a, win='#3b5872')))
        for z in np.arange(TAPER0, TAPER1 + 0.1, 4.0):
            out.append(((taper_x(z) + 0.1, 0.4, z), lambda z=z: cone(ctx, view, taper_x(z) + 0.15, z)))
        for z in np.arange(4, 200, 6):
            out.append(((0.35, 0.5, z), lambda z=z: barrel(ctx, view, 0.4, z)))
        out.append(((2.2, 1.5, -8.0), lambda: arrow_board(ctx, view, 2.2, -8.0, t)))
        for x, z in self.workers:
            out.append(((x, 0.9, z), lambda x=x, z=z: euro.ped_bb(ctx, view, x, z, t, '#f28c28', '#2b3a63', '#e8b48f', '#ffd23f', False, False)))
        out.append(((5.0, 1.5, -150), lambda: travaux(ctx, view, 5.0, -150)))
        out.append(((5.0, 1.5, -110), lambda: orange_diamond(ctx, view, 5.0, -110, 'closed', '300 m')))
        out.append(((5.0, 1.5, -62), lambda: orange_diamond(ctx, view, 5.0, -62, 'merge')))
        for z in np.arange(-480, 480, 40):
            out.append(((-5.6, 4, z), lambda z=z: lamp_post(ctx, view, -5.6, z)))
        return out


def lamp_post(ctx, view, x, z):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 9, z)), view.scale((x, 0, z))
    if not b or not tp or not s or s < 1.5:
        return
    ctx.rectangle(b[0] - 0.09 * s, tp[1], 0.18 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#7a7f8c'), OUTL, max(1, s / 60))
    a = view.pt((x + 1.8, 9, z))
    if a:
        ctx.move_to(*tp)
        ctx.line_to(*a)
        setc(ctx, hexc('#7a7f8c'))
        ctx.set_line_width(max(2, 0.14 * s))
        ctx.stroke()


city = Montreal()
SEG_HOOK = (0.0, 3.2, hook_r, [hook_l] + hook_q)
world = CityWorld(32.0, [SEG_HOOK, (3.2, 99, EGO, OTHERS)], [], city, 'kmh')


class HTop:
    """Horizontal map view: travel direction points RIGHT, the closed (right) lane is at the bottom."""
    ortho = True
    hrot = math.pi / 2

    def __init__(self, zc, s, ox=960, oy=540, xc=0.0):
        self.zc, self.s, self.ox, self.oy, self.xc = zc, s, ox, oy, xc
        self.pos = (0, 1000, 0)

    def pt(self, P):
        return (self.ox + (P[2] - self.zc) * self.s, self.oy + (P[0] - self.xc) * self.s)

    def poly(self, pts):
        return [self.pt(p) for p in pts]

    def depth(self, P):
        return 0.0

    def scale(self, P):
        return self.s


# ------------------------------------------------------------- myth-buster split screen
def split_compare(ctx, w, t, lt, kw):
    N = 20
    for half, mode in ((0, 'early'), (1, 'zip')):
        y0 = half * 540
        ctx.save()
        ctx.rectangle(0, y0, SW, 540)
        ctx.clip()
        view = HTop(-60.0, 12.5, ox=1000, oy=y0 + 330)
        setc(ctx, city.ground_col)
        ctx.paint()
        city.ground(ctx, view, t)
        for z in np.arange(TAPER0, TAPER1 + 0.1, 4.0):
            cone(ctx, view, taper_x(z) + 0.15, z)
        crawl = (lt * 2.2) % 7.0
        bl = 'L' if (lt * 1.25) % 1 < 0.5 else None
        if mode == 'early':
            for i in range(N):
                draw_car_top_g(ctx, view, LX, -6 - 7 * i + crawl, 0.0, COLS[i % 10], t)
            front, back = -6 + 2.2, -6 - 7 * (N - 1) - 2.2
        else:
            for i in range(N // 2):
                draw_car_top_g(ctx, view, LX, -6 - 7 * i + crawl, 0.0, COLS[i % 10], t)
                draw_car_top_g(ctx, view, RX, -9.5 - 7 * i + crawl, 0.0, COLS[(i + 5) % 10], t, bl)
            front, back = -6 + 2.2, -9.5 - 7 * (N // 2 - 1) - 2.2
        col = '#e0393e' if mode == 'early' else '#22a356'
        a = smooth((lt - 0.6) / 0.5)
        if a > 0:
            p0, p1 = view.pt((-7.2, 0, front)), view.pt((-7.2, 0, back))
            xb = p0[0] + (p1[0] - p0[0]) * a
            ctx.move_to(p0[0], p0[1])
            ctx.line_to(xb, p0[1])
            setc(ctx, hexc(col))
            ctx.set_line_width(12)
            ctx.stroke()
            for x in (p0[0], xb):
                ctx.move_to(x, p0[1] - 24)
                ctx.line_to(x, p0[1] + 24)
                ctx.stroke()
            if a > 0.95:
                label(ctx, (p0[0] + p1[0]) / 2, p0[1] - 30, f'{int(round(front - back))} m of cars', col, 50)
        ctx.restore()
        title = 'Merge EARLY: one long line' if mode == 'early' else 'ZIPPER: two lines, HALF as long'
        label(ctx, 430, y0 + 90, title, col, 46)
    ctx.rectangle(0, 535, SW, 10)
    setc(ctx, (1, 1, 1))
    ctx.fill()
    label(ctx, 1640, 1010, 'Same 20 cars', '#2f6f9f', 44)


engine.SCENES['split_compare'] = split_compare


def z_top(ctx, w, t, lt, kw):
    ez = EGO.pose(t)[1]
    view = HTop(ez + kw.get('ahead', 22.0), kw.get('scale', 24.0), oy=560, xc=0.5)
    nums = kw['nums'](t, lt) if kw.get('nums') else None
    draw_scene(ctx, view, w, t, nums=nums)
    if kw.get('post'):
        kw['post'](ctx, view, t, lt)


engine.SCENES['z_top'] = z_top


def zip_nums(t, lt):
    """Merge-order numbers for the cars around the merge point."""
    near = sorted([c for c in CARS if c.tk > t - 0.3 and c.tk < t + 9], key=lambda c: c.tk)
    out = {}
    for i, c in enumerate(near[:6]):
        if c.k == K_E:
            out['ego'] = i + 1
        else:
            out[OTHERS.index(c)] = i + 1
    return out


def top_both_post(ctx, view, t, lt):
    a = smooth((lt - 0.4) / 0.4)
    if a <= 0:
        return
    ex, ez, _ = EGO.pose(t)
    p = view.pt((RX + 4.6, 0, ez))
    label(ctx, p[0], p[1], 'Stay in your lane', '#22a356', 44)
    q = view.pt((-6.2, 0, ZM))
    q = (min(q[0], SW - 200), q[1])
    label(ctx, q[0], q[1], 'Merge point', '#2f6f9f', 44)
    ctx.move_to(q[0], q[1] + 20)
    ctx.line_to(q[0], view.pt((0, 0, ZM))[1])
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(5)
    ctx.set_dash([10, 8])
    ctx.stroke()
    ctx.set_dash([])


def zip_post(ctx, view, t, lt):
    q = view.pt((-6.2, 0, ZM))
    label(ctx, q[0], q[1], 'One from each lane', '#22a356', 44)


TOPC = dict(center=(0.0, -40.0), scale=13.0)
shots_def = [
    (3.2, 'c_cam', dict(cam='fixed', pos=(1.2, 1.5, -19.5), target=(0.4, 0.9, -33), f=1000, hud=False)),         # HOOK
    (9.2, 'split_compare', dict()),                                                                              # myth-buster
    (12.2, 'c_cam', dict(cam='chase')),                                                                          # 1 signs
    (15.2, 'z_top', dict(post=top_both_post, ahead=12.0)),                                 # 2 both lanes
    (18.0, 'c_cam', dict(cam='close_l', hud=False)),                                                             # 3 signal early
    (21.6, 'z_top', dict(nums=zip_nums, post=zip_post, ahead=-2.0 if False else 8.0)),                                                 # 4 take turns
    (25.0, 'c_cam', dict(cam='high')),                                                                           # 5 merge smoothly
    (28.4, 'c_cam', dict(cam='fixed', pos=(-2.5, 9.0, 18), target=(0.5, 0, -32), f=1000, hud=False)),           # 6 next car's turn
    (32.0, 'c_cam', dict(cam='fixed', pos=(-12, 22, -90), target=(0, 0, -20), f=1000, hud=False)),             # end
]
shots, prev = [], 0.0
for end, kind, kw in shots_def:
    shots.append(Shot(end - prev, kind, **kw))
    prev = end
video = Video(['ZIPPER MERGE:', 'the right way'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]


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


def end_card(ctx, lt, d):
    label(ctx, 960, 200, 'Use both lanes. Take turns. ZIP!', '#22a356', 62)
    if lt > 1.0:
        b = smooth((lt - 1.0) / 0.3)
        ctx.save()
        ctx.translate(960, 320)
        ctx.scale(0.8 + 0.2 * b, 0.8 + 0.2 * b)
        label(ctx, 0, 0, 'Do drivers zipper merge in your city? Comment!', '#e0393e', 50)
        ctx.restore()


steps = ['See the signs early', 'Traffic slow? Use BOTH lanes', 'Signal early', 'Take turns: one from each lane',
         'Match speed & merge smoothly', "Next car's turn: keep the zipper going"]
video.overlays = [
    (0.0, 3.2, big_text('Who goes first?', 290, 150, hexc('#ffd23f'), 0.4, True)),
    (0.3, 3.0, location_tag('Montreal, Quebec')),
    (5.6, 9.2, lambda ctx, lt, d: label(ctx, 960, 560, 'Merging early does NOT help traffic', '#2f6f9f', 50)),
    (S[8] + 0.2, E[8], end_card),
]
for n, txt in enumerate(steps, 1):
    video.overlays += [(S[n + 1], E[n + 1], step_badge(n)), (S[n + 1] + 0.15, E[n + 1], caption_in_scene(txt))]


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur), 0, 0.25)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.12)
    m.add(brake_squeal(0.8), 0.7, 0.25)
    m.add(horn(0.9), 1.5, 0.9, 0.2)
    m.add(horn(0.5, doppler=[0.85] * 4), 2.2, 0.8, -0.3)
    m.add(heartbeat(2, 120), 0.4, 0.8)
    m.add(whoosh(0.6, 0.4), 3.05, 0.7)
    m.add(sad_trombone(), 5.0, 0.6)
    m.add(pop(), 6.0, 0.8)
    m.add(chime(), 6.6, 0.7)
    m.add(click(), EGO.tk - 10.0, 1.2)
    indicator(m, EGO.tk - 10.0, EGO.tk + 2.0, 0.9, -0.2)
    m.add(click(), EGO.tk + 2.0, 1.0)
    for i in range(2, 8):
        m.add(pop(), S[i] + 0.15, 0.8)
    for k in range(6):
        m.add(bell(midi(79 + (k % 2) * 5), 0.4), S[5] + 0.6 + k * 0.45, 0.4)
    m.add(success_jingle(), S[8] + 0.2, 0.9)
    m.add(pop(), S[8] + 1.0, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        print('verify (min bumper gap m, min taper clearance m):', verify())
    else:
        run(video, sound, 'zipper.mp4')
