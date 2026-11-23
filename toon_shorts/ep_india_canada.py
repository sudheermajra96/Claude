"""Split screen: an auto rickshaw in Mumbai traffic (top) vs a sedan on the Niagara Parkway, Ontario (bottom).

India keeps LEFT: our carriageway is x < 0 (lanes -10.5..-0.35), oncoming traffic on x > 0.
Canada keeps RIGHT: two-lane parkway, our lane x 0..3.6, the Niagara River on the left (west bank road).
Mumbai traffic is planned by rejection sampling: every vehicle is checked against the ego auto and all
other vehicles for the whole clip (lateral margin LATM, longitudinal margin LONM) before it is kept.
"""
import math
import random

import cairo
import numpy as np

from mkit import *
from indiakit import *
import indiakit
import niagara
import engine
import citykit

DUR = 31.0
LATM, LONM = 0.28, 0.9
DIMS['car'] = (4.4, 1.84)
SKIN = ['#9c6a4a', '#b07a55', '#8a5a3c', '#c08a62']

# ================================================================== MUMBAI (top panel)
EGO_X = Key([(0, -6.7), (4.9, -6.7), (5.9, -8.9), (7.8, -8.9), (8.8, -5.4), (10.6, -5.4), (11.6, -2.2), (13.2, -2.2),
             (14.2, -5.2), (16.2, -5.2), (17.2, -8.4), (19.4, -8.4), (20.4, -4.8), (22.4, -4.8), (23.4, -2.0),
             (25.4, -2.0), (26.4, -5.6), (28.4, -5.6), (29.4, -7.6), (40, -7.6)])
LANE_CHANGES = 10
EGO_S = Key([(0, 7.5), (4.4, 7.5), (5.4, 8.2), (7.5, 6.2), (9, 8.0), (12.8, 6.6), (14.5, 7.6), (17, 8.0), (19, 6.2),
             (21, 8.0), (25, 7.0), (27, 8.4), (31, 7.4), (40, 7.4)], 'lin')


class IVe(IV):
    """IV with ortho car + an ego highlight in the top view."""

    def __init__(self, *a, ego=False, **kw):
        super().__init__(*a, **kw)
        self.ego = ego

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        if culled(view, x, z):
            return []

        def fn():
            if view.ortho and self.ego:
                p = view.pt((x, 0, z))
                glow(ctx, p[0], p[1], 3.2 * view.s, hexc('#ffffff'), 0.5)
            if view.ortho and self.kind == 'car':
                draw_car_top_g(ctx, view, x, z, h, self.col, t)
            else:
                DRAW[self.kind](ctx, view, self, x, z, h, t)
        key = (x, 1.0, z)
        if self.kind == 'bus' and not view.ortho:
            key = (x, 1.5, z - 3.0)          # sort a long bus by its rear half (cameras are behind)
        return [(key, fn)]


def culled(view, x, z):
    if view.ortho:
        return abs(z - view.zc) > 45
    d = view.depth((x, 1.0, z))
    return d < 3.2 or d > 220


class Onc:
    """Oncoming vehicle on the other carriageway (travels -z)."""

    def __init__(self, kind, x, v, z0, **kw):
        self.a = IVe(kind, x, 0.0, 0.0, z0, **kw)
        self.x, self.v, self.z0, self.kind = x, v, z0, kind
        self.col = self.a.col

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

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        if culled(view, x, z):
            return []
        a = self.a

        def fn():
            if view.ortho and self.kind == 'car':
                draw_car_top_g(ctx, view, x, z, h, a.col, t)
            else:
                DRAW[self.kind](ctx, view, a, x, z, h, t)
        return [((x, 1.0, z), fn)]


ego_i = IVe('auto', EGO_X, EGO_S, 0.0, 0.0, roof='#f2c230', ego=True)
TG = np.arange(-0.5, 31.5, 0.05)


def arrays(a, kind):
    P = np.array([a.pose(t) for t in TG])
    l, w = DIMS[kind]
    h = P[:, 2]
    half_w = w / 2 + np.abs(np.sin(h)) * l / 2
    half_l = l / 2 + np.abs(np.sin(h)) * w / 2
    return P[:, 0], P[:, 1], half_w, half_l


EX, EZ, EHW, EHL = arrays(ego_i, 'auto')


def conflict(A, B, latm=LATM, lonm=LONM):
    xa, za, wa, la = A
    xb, zb, wb, lb = B
    lat = np.abs(xa - xb) - (wa + wb)
    lon = np.abs(za - zb) - (la + lb)
    return np.any((lat < latm) & (lon < lonm))


def occludes(B):
    """Vehicle sitting right behind the ego (would block the chase camera)."""
    xb, zb, wb, lb = B
    dz = EZ - zb
    return np.any((dz > 1.0) & (dz < 9.5) & (np.abs(EX - xb) < 1.3))


BIKE_COLS = ['#e0393e', '#1c1c22', '#3a7bd5', '#c9c9d6', '#7a4fd0', '#2f6f73', '#f2a541']
TOPS = ['#3a7bd5', '#f4f4f6', '#e05d5d', '#56b38a', '#f2c230', '#c77dff', '#ee964b', '#2b3a63']
CAR_COLS = ['#f4f4f6', '#c9c9d6', '#f4f4f6', '#e05d5d', '#3a7bd5', '#1c1c22', '#d8c3a0', '#f4f4f6']


def make(kind, x, v, ta, za, r):
    if kind == 'auto':
        roof = r.choice(['#f2c230', '#f2c230', '#f2c230', '#2f9a4a'])
        return IVe('auto', x, v, ta, za, roof=roof, body='#1c1c22' if roof == '#f2c230' else '#2f9a4a')
    if kind == 'bike':
        return IVe('bike', x, v, ta, za, col=r.choice(BIKE_COLS), top=r.choice(TOPS),
                   helmet=r.choice(['#f4f4f6', '#1c1c22', '#e0393e', '#3a7bd5', '#f2c230']),
                   pillion=r.choice([None, None, '#e05d5d', '#c77dff', '#56b38a']))
    if kind == 'bus':
        return IVe('bus', x, v, ta, za)
    return IVe('car', x, v, ta, za, col=r.choice(CAR_COLS))


bus0 = IVe('bus', -8.95, 4.5, 0.0, 5.85)
bike0 = IVe('bike', Key([(0, -5.27), (4.6, -5.27), (5.6, -4.2), (40, -4.2)]), Key([(0, 7.55), (4.0, 7.55), (5.5, 9.8), (40, 9.8)], 'lin'), 0.0, 0.4, col='#e0393e', top='#3a7bd5', helmet='#f4f4f6', pillion='#f2c230')
COW_Z = ego_i.tr.z(14.6)
cow0 = IVe('cow', -2.0, 0.0, 0.0, COW_Z, heading=0.35)
SCRIPTED = [(bus0, 'bus'), (bike0, 'bike'), (cow0, 'cow')]


def plan(seed=7, tries=22000, target=75):
    r = random.Random(seed)
    kept = [(ego_i, 'auto', (EX, EZ, EHW, EHL))]
    for a, k in SCRIPTED:
        A = arrays(a, k)
        assert not any(conflict(A, B[2]) for B in kept), k
        kept.append((a, k, A))
    n = 0
    while n < tries and len(kept) < target + 4:
        n += 1
        kind = r.choices(['bike', 'auto', 'car', 'bus'], [0.42, 0.27, 0.25, 0.06])[0]
        l, w = DIMS[kind]
        lo, hi = -10.35 + w / 2, -0.35 - w / 2 - 0.25
        x0 = r.uniform(lo, hi)
        v = {'bike': (6.5, 9.6), 'auto': (5.5, 8.0), 'car': (5.0, 8.2), 'bus': (4.0, 6.0)}[kind]
        v = r.uniform(*v)
        ta = r.uniform(0, 30)
        za = ego_i.tr.z(ta) + r.uniform(-28, 45)
        if kind == 'bike' and r.random() < 0.5:
            tc = r.uniform(1, 29)
            x1 = clamp(x0 + r.choice([-1, 1]) * r.uniform(1.5, 3.5), lo, hi)
            x = Key([(0, x0), (tc, x0), (tc + 1.0, x1), (40, x1)])
        else:
            x = x0
        a = make(kind, x, v, ta, za, r)
        A = arrays(a, kind)
        if occludes(A):
            continue
        if any(conflict(A, B[2]) for B in kept):
            continue
        kept.append((a, kind, A))
    return kept


KEPT = plan()
OTHERS_I = [a for a, k, A in KEPT[1:]]


def oncoming(seed=3):
    r = random.Random(seed)
    out = []
    for x, kinds, v in ((1.95, ['bus', 'car', 'car', 'auto'], 7.0), (3.7, ['bike'], 8.5), (5.3, ['car', 'auto'], 7.5),
                        (7.0, ['bike'], 9.0), (8.7, ['auto', 'car', 'auto'], 6.5)):
        z = 660.0
        while z > -30:
            k = r.choice(kinds)
            if k == 'bus' and r.random() < 0.6:
                k = 'car'
            l, w = DIMS[k]
            a = make(k, 0.0, 0.0, 0, 0, r)
            o = Onc(k, x, v, z, col=a.col, roof=a.roof, body=a.body, top=a.top, helmet=a.helmet, pillion=a.pillion)
            out.append(o)
            z -= l + r.uniform(5.0, 20.0)
    return out


ONC = oncoming()
PEDS_I = []
_r = random.Random(11)
for sx in (-1, 1):
    for k in range(26):
        v = _r.choice([-1, 1]) * _r.uniform(0.9, 1.5)
        z0 = _r.uniform(-60, 300)
        PEDS_I.append(Ped(const(sx * _r.choice([10.95, 11.25])), Key([(0, z0), (40, z0 + v * 40)], 'lin'),
                          top=_r.choice(TOPS + ['#d62828', '#ff6b9d', '#f4d35e']), pants=_r.choice(['#2b3a63', '#3a3d48', '#c8b48a', '#f4f4f6']),
                          skin=_r.choice(SKIN), hair='#1d1613'))
CARTS = [(sx * 11.9, z, c) for sx in (-1, 1) for z, c in zip(np.arange(-20 + 17 * (sx > 0), 320, 46),
                                                                    ['#e05d5d', '#2f9a4a', '#f2c230', '#3a7bd5', '#ee964b', '#c77dff', '#e05d5d', '#56b38a'])]


class MumbaiStreet(Street):
    def __init__(self):
        super().__init__('city', n=3, median='barrier', sidewalk=True, seed=23, hmin=9, hmax=24, setback=1.5,
                         sky=('#7fb8e6', '#f1e6d2'), ground='#b9a98c', skyline=mumbai_sky,
                         palette=['#e8a87c', '#f2d0a4', '#c38d9e', '#85c7b5', '#e3c567', '#d98c6a', '#b5d6e0', '#f4efe6'])
        self.items = [it for it in self.items if it[0] != 'lamp']

    def objects(self, ctx, view, t):
        out = super().objects(ctx, view, t)
        for i, (kind, a) in enumerate(self.items):
            if kind == 'bld':
                fx = a[0] if a[0] > 0 else a[1]
                out.append(((fx, 2.0, (a[2] + a[3]) / 2), lambda a=a, i=i: shop_signs(ctx, view, a, i)))
        for x, z, c in CARTS:
            out.append(((x, 1.0, z), lambda x=x, z=z, c=c: food_cart(ctx, view, x, z, c)))
        return out

    def ground(self, ctx, view, t):
        super().ground(ctx, view, t)
        # worn lane paint + curb stripes (black/yellow, typical of Mumbai kerbs)
        if not view.ortho:
            for sx in (-1, 1):
                for k in range(-20, 60):
                    z0 = k * 6.0
                    fill_poly(ctx, view, [(sx * 10.5, 0, z0), (sx * 10.5, 0, z0 + 3), (sx * 10.5, 0.18, z0 + 3), (sx * 10.5, 0.18, z0)],
                              hexc('#f2c230' if k % 2 else '#1c1c22'))


class IndiaWorld(SegWorld):
    def __init__(self):
        super().__init__(DUR, [(0, 99, ego_i, OTHERS_I + ONC, PEDS_I)], MumbaiStreet(), 'kmh')

    def objects_extra(self, ctx, view, t):
        return []


world_i = IndiaWorld()
_city_i = world_i.city
_orig_objects = _city_i.objects


def _objects_with_wires(ctx, view, t):
    out = _orig_objects(ctx, view, t)
    ez = world_i.ego_xz(t)[1]
    out.append(((0, 30, ez + 400), lambda: wires(ctx, view, ez)))
    return out


_city_i.objects = _objects_with_wires

# ------------------------------------------------------------------ horns (time, agent, kind)
EGO_HORNS = [0.3, 0.55, 4.9, 8.5, 11.3, 13.3, 13.55, 17.0, 20.2, 23.2, 26.2, 29.1]


def near_agents(t, rmax=22.0):
    ex, ez = EX[int((t + 0.5) / 0.05)], EZ[int((t + 0.5) / 0.05)]
    out = []
    for a in OTHERS_I:
        x, z, _ = a.pose(t)
        if a.kind != 'cow' and abs(z - ez) < rmax and 0 < z - ez + 4:
            out.append((abs(z - ez) + abs(x - ex), a))
    return [a for d, a in sorted(out, key=lambda q: q[0])]


def build_horns():
    r = random.Random(5)
    hs = [(t, ego_i) for t in EGO_HORNS]
    hs.append((6.0, bus0))                      # the bus answers the cut-in
    t = 1.4
    while t < 30.0:
        cand = near_agents(t)
        if cand:
            a = r.choice(cand[:5])
            if all(abs(t - u) > 0.35 for u, _ in hs):
                hs.append((t, a))
        t += r.uniform(0.9, 1.6)
    return sorted(hs, key=lambda h: h[0])


HORNS = build_horns()


def burst(ctx, x, y, text, size, col):
    n = 14
    pts = []
    for k in range(2 * n):
        ang = k * math.pi / n
        rr = (1.0 if k % 2 == 0 else 0.72) * size
        pts.append((x + math.cos(ang) * rr * 1.45, y + math.sin(ang) * rr * 0.95))
    poly(ctx, pts)
    fill_stroke(ctx, hexc(col), OUTL, max(2, size * 0.06))
    text_center(ctx, text, x, y + size * 0.2, size * 0.55, OUTL)


def horn_bubbles(ctx, view, t):
    for t0, a in HORNS:
        u = t - t0
        if not 0 <= u < 0.55:
            continue
        x, z, _ = a.pose(t)
        kind = getattr(a, 'kind', 'auto')
        txt, col = {'bus': ('HONK!', '#ff8a3d'), 'bike': ('PEEP!', '#ffe14d'), 'car': ('BEEP!', '#ffe14d'),
                    'auto': ('POM!', '#ff6b9d')}.get(kind, ('BEEP!', '#ffe14d'))
        if view is None:
            p, s = (960, 300), 160
        else:
            P = (x, 3.2 if kind != 'bus' else 4.2, z)
            if view.ortho:
                p, s = view.pt(P), 90
                p = (p[0], p[1] - 40)
            else:
                if view.depth(P) < 1.5:
                    continue
                p, s = view.pt(P), view.scale(P)
                if not p or not s:
                    continue
                s = clamp(s * 1.6, 46, 120)
        pop_k = 1 + 0.25 * (1 - smooth(u / 0.12))
        burst(ctx, p[0], p[1], txt, s * pop_k, col)


# ------------------------------------------------------------------ India cameras
def smooth_x(t, back=0.7):
    return sum(EGO_X(t - back * k / 6) for k in range(7)) / 7


def i_view(t, mode):
    x, z, h = ego_i.pose(t)
    sx = smooth_x(t)
    if mode == 'chase':
        return TCam((sx, 3.4, z - 9.0), 0.0, 0.15, 1000, cy=520)
    if mode == 'high':
        return TCam((sx + 1.0, 9.5, z - 13.5), -0.03, 0.42, 1000, cy=470)
    if mode == 'front':
        return look_at((sx + 2.2, 1.7, z + 8.5), (x, 1.1, z), 950)
    if mode == 'side':
        return look_at((-11.0, 2.4, z + 5.0), (x, 0.9, z + 1.0), 900)
    raise ValueError(mode)


def i_cam(ctx, w, t, lt, kw):
    view = i_view(t, kw['cam'])
    draw_scene(ctx, view, w, t)
    if 11.0 <= t < 14.6:
        p = view.pt((cow0.pose(t)[0], 1.0, COW_Z))
        s_ = view.scale((cow0.pose(t)[0], 1.0, COW_Z))
        if p and s_:
            ellipse(ctx, p[0], p[1], 2.2 * s_, 1.6 * s_)
            setc(ctx, hexc('#ffd23f'))
            ctx.set_line_width(5)
            ctx.stroke()
            label(ctx, p[0] + 2.4 * s_ + 20, p[1] - 2.0 * s_ - 30, 'COW!', '#e0393e', 40)
    horn_bubbles(ctx, view, t)
    hud(ctx, w, t)


def auto_front(ctx, t, steer):
    """Driver's view from inside the auto: canvas roof, posts, garland, handlebar with hands, dash."""
    roof = hexc('#f2c230')
    ctx.move_to(-10, -10)
    ctx.line_to(SW + 10, -10)
    ctx.line_to(SW + 10, 140)
    ctx.curve_to(1400, 196, 520, 196, -10, 140)
    ctx.close_path()
    fill_stroke(ctx, roof, OUTL, 6)
    ctx.move_to(-10, 110)
    ctx.curve_to(520, 160, 1400, 160, SW + 10, 110)
    setc(ctx, mix(roof, (0, 0, 0), 0.25))
    ctx.set_line_width(10)
    ctx.stroke()
    for k in range(23):                       # marigold garland
        u = k / 22
        x = 200 + u * 1520
        y = 196 + 46 * math.sin(math.pi * u) - 8 * (1 - math.sin(math.pi * u))
        ellipse(ctx, x, y, 17, 17)
        fill_stroke(ctx, hexc('#ff9f1c' if k % 2 else '#ffd23f'), OUTL, 2)
    for s in (-1, 1):
        x0 = 960 + s * 960
        poly(ctx, [(x0, 120), (x0 - s * 120, 125), (x0 - s * 260, SH + 10), (x0, SH + 10)])
        fill_stroke(ctx, hexc('#1c1c22'), OUTL, 4)
    ctx.move_to(-10, 860)
    ctx.curve_to(480, 800, 1440, 800, SW + 10, 860)
    ctx.line_to(SW + 10, SH + 10)
    ctx.line_to(-10, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, hexc('#1c1c22'), hexc('#3a3d48'), 6)
    ellipse(ctx, 960, 900, 70, 52)
    fill_stroke(ctx, hexc('#3a3d48'), OUTL, 4)
    ellipse(ctx, 960, 900, 52, 36)
    fill_stroke(ctx, hexc('#f4f2ec'), OUTL, 2)
    ctx.move_to(960, 905)
    ang = -2.4 + 1.4 * clamp(world_i.speed(t) / 10)
    ctx.line_to(960 + 40 * math.cos(ang), 905 + 30 * math.sin(ang))
    setc(ctx, hexc('#e0393e'))
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.save()
    ctx.translate(960, 985)
    ctx.rotate(clamp(steer, -1.6, 1.6) * 0.12)
    ctx.move_to(-520, -40)
    ctx.curve_to(-300, 10, 300, 10, 520, -40)
    setc(ctx, hexc('#4a4d58'))
    ctx.set_line_width(26)
    ctx.stroke()
    for s in (-1, 1):
        rrect(ctx, s * 560 - 80, -66, 160, 50, 22)
        fill_stroke(ctx, hexc('#1c1c22'), OUTL, 4)
        # khaki sleeve (driver's uniform) + fist wrapped round the grip
        poly(ctx, [(s * 560 - 62, -20), (s * 560 + 62, -20), (s * 700, 220), (s * 420, 220)])
        fill_stroke(ctx, hexc('#c8b48a'), OUTL, 5)
        rrect(ctx, s * 560 - 66, -92, 132, 96, 40)
        fill_stroke(ctx, hexc('#9c6a4a'), OUTL, 5)
        for k in range(1, 4):
            ctx.move_to(s * 560 - 66 + k * 33, -88)
            ctx.line_to(s * 560 - 66 + k * 33, -58)
        ctx.move_to(s * 560 - s * 66, -40)
        ctx.curve_to(s * 560 - s * 30, -60, s * 560 + s * 10, -54, s * 560 + s * 30, -36)
        setc(ctx, mix(hexc('#9c6a4a'), (0, 0, 0), 0.45))
        ctx.set_line_width(4)
        ctx.stroke()
    ctx.restore()


def auto_pov(ctx, w, t, lt, kw):
    x, z, h = ego_i.pose(t)
    view = TCam((x, 1.5, z + 0.35), h * 0.7, 0.05, 900, cy=500)
    draw_scene(ctx, view, w, t, ego=False)
    horn_bubbles(ctx, view, t)
    auto_front(ctx, t, ego_i.steer(t))
    for t0, a in HORNS:
        if a is ego_i and 0 <= t - t0 < 0.5:
            burst(ctx, 960, 330, 'POM!', 120 * (1 + 0.25 * (1 - smooth((t - t0) / 0.12))), '#ff6b9d')
    hud(ctx, w, t)


def i_top(ctx, w, t, lt, kw):
    ex, ez = w.ego_xz(t)
    view = HTop(-4.5, ez + 6.0, 30.0)
    draw_scene(ctx, view, w, t)
    horn_bubbles(ctx, view, t)
    if kw.get('trail'):
        pts = [view.pt((EGO_X(u), 0, ego_i.tr.z(u))) for u in np.arange(max(0, t - 6), t, 0.05)]
        if len(pts) > 2:
            arrow_path(ctx, pts, hexc('#ff6b9d'), 9, 0.85, None, 0)


engine.SCENES.update(i_cam=i_cam, auto_pov=auto_pov, i_top=i_top)

# ================================================================== NIAGARA PARKWAY (bottom panel)
SPEED_C = 16.2      # 58 km/h
ego_c = Track(1.8, SPEED_C, 0.0, 0.0, '#3a7bd5')
lead_c = Track(1.8, SPEED_C, 0.0, 62.0, '#f4f4f6')


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


ONC_C = [Rev(-1.8, 15.5, z, c) for z, c in ((120, '#e05d5d'), (290, '#c9c9d6'), (420, '#37b26c'), (560, '#f2a541'),
                                            (760, '#1c1c22'), (900, '#7a4fd0'))]
C_RIVER = hexc('#3f86c4')


class Parkway:
    """Niagara Parkway: two-lane road, trail + stone wall + river on the left, trees and houses on the right."""
    kind = 'parkway'
    sky = ('#5fb4f2', '#dcf1ff')

    def __init__(self):
        self.ground_col = hexc('#7cc062')
        r = random.Random(4)
        self.items = []
        for z in np.arange(-200, 1400, 9):
            self.items.append(('tree', (r.uniform(7, 11), z + r.uniform(-2, 2), 0.9 + r.uniform(0, 0.5))))
            if r.random() < 0.6:
                self.items.append(('tree', (r.uniform(13, 40), z + r.uniform(-3, 3), 1.0 + r.uniform(0, 0.6))))
            if r.random() < 0.28:
                self.items.append(('tree', (-r.uniform(5.6, 7.4), z + r.uniform(-2, 2), 0.9 + r.uniform(0, 0.4))))
        z = -150.0
        while z < 1400:
            w = r.uniform(11, 14)
            x0 = r.uniform(19, 24)
            self.items.append(('house', (x0, x0 + r.uniform(10, 13), z, z + w, r.uniform(5.5, 6.8),
                                         r.choice(['#f4efe6', '#d8c3a0', '#c9b9a6', '#e8dccb', '#b56f52']),
                                         r.choice(['#4a4f5c', '#6b3f32', '#38485a']))))
            z += w + r.uniform(26, 50)
        self.joggers = []

    def skyline(self, ctx, view):
        # US bank across the river (low tree line) + Skylon Tower / hotels / falls mist far ahead
        niagara.skylon(ctx, view)
        far_line(ctx, view, 1300, lambda x: 14 + 5 * math.sin(x / 45), x0=-2400, x1=-200, col='#5f9a5a')

    def ground(self, ctx, view, t):
        gquad(ctx, view, -700, -15.0, -400, 2500, C_RIVER)
        if not view.ortho:
            ez = world_c.ego_xz(t)[1]
            for k in range(60):
                rz = ez + (k * 37.0 + t * 6.0) % 600 - 40
                xx = -18 - (k * 53) % 120
                gquad(ctx, view, xx - 3, xx, rz, rz + 0.6, hexc('#8cc3ea'), 0.01)
        gquad(ctx, view, -15.0, -13.2, -400, 2500, hexc('#b9b2a0'))
        gquad(ctx, view, -11.6, -9.2, -400, 2500, hexc('#c9c1ac'))
        gquad(ctx, view, -4.4, 4.4, -400, 2500, hexc('#8d8f96'))
        gquad(ctx, view, -3.6, 3.6, -400, 2500, C_ASPH)
        gquad(ctx, view, -0.2, -0.07, -400, 2500, C_YEL, 0.01)
        gquad(ctx, view, 0.07, 0.2, -400, 2500, C_YEL, 0.01)
        for sx in (-1, 1):
            gquad(ctx, view, *sorted((sx * 3.45, sx * 3.6)), -400, 2500, C_LINE, 0.01)
        if not view.ortho:     # low stone wall along the river bank
            fill_poly(ctx, view, [(-13.2, 0, -400), (-13.2, 0, 2500), (-13.2, 0.8, 2500), (-13.2, 0.8, -400)], hexc('#a39a86'), OUTL, 2)
            fill_poly(ctx, view, [(-13.2, 0.8, -400), (-13.2, 0.8, 2500), (-13.8, 0.8, 2500), (-13.8, 0.8, -400)], hexc('#c9c1ac'))

    def objects(self, ctx, view, t):
        out = []
        ez = world_c.ego_xz(t)[1]
        for kind, a in self.items:
            if kind == 'tree':
                if ez - 60 < a[1] < ez + 700:
                    out.append(((a[0], 1.5, a[1]), lambda a=a: tree3(ctx, view, a[0], a[1], a[2] * (0.45 if view.ortho else 1.0), int(abs(a[1])) % 3)))
            elif kind == 'house':
                if ez - 60 < a[2] < ez + 700:
                    out.append((((a[0] + a[1]) / 2, 3, (a[2] + a[3]) / 2), lambda a=a: gable_house(ctx, view, *a)))
        out.append(((4.6, 1.5, 150.0), lambda: pkwy_sign(ctx, view, 4.6, 150.0)))
        return out


def pkwy_sign(ctx, view, x, z):
    if view.ortho:
        return
    corners = [(x - 1.1, 2.1, z), (x + 1.1, 2.1, z), (x + 1.1, 3.4, z), (x - 1.1, 3.4, z)]
    a, b = view.pt((x, 0, z)), view.pt((x, 2.1, z))
    if not a or not b:
        return
    ctx.move_to(*a)
    ctx.line_to(*b)
    setc(ctx, hexc('#6a6f7c'))
    ctx.set_line_width(max(2, (view.scale((x, 1, z)) or 10) * 0.08))
    ctx.stroke()
    if fill_poly(ctx, view, corners, hexc('#1f6f43'), (1, 1, 1), 2):
        c, s = view.pt((x, 2.75, z)), view.scale((x, 2.75, z))
        if c and s and s > 6:
            text_center(ctx, 'Niagara Pkwy', c[0], c[1] + 0.12 * s, 0.38 * s, (1, 1, 1))


JOG = [Ped(const(-10.0), Key([(0, 40), (40, 40 + 2.6 * 40)], 'lin'), top='#e05d5d', pants='#1c1c22'),
       Ped(const(-10.8), Key([(0, 230), (40, 230 - 1.3 * 40)], 'lin'), top='#3a7bd5', pants='#c8b48a', hair='#6b4a2f'),
       Ped(const(-10.3), Key([(0, 420), (40, 420 + 1.2 * 40)], 'lin'), top='#56b38a', pants='#2b3a63')]
world_c = CityWorld(DUR, [(0, 99, ego_c, [lead_c] + ONC_C)], JOG, Parkway(), 'kmh')


def c_in(ctx, w, t, lt, kw):
    view = ego_cam(w, t, 'inside')
    draw_scene(ctx, view, w, t, ego=False)
    citykit.cockpit(ctx, w, t)
    hud(ctx, w, t)


engine.SCENES.update(c_in=c_in)


# ================================================================== composer
PH = SH * SCALE               # 607.5
TOP_Y, BOT_Y = 340.0, 340.0 + PH + 64


def build(defs):
    shots, prev = [], 0.0
    for end, kind, kw in defs:
        s = Shot(end - prev, kind, **kw)
        s.start = prev
        shots.append(s)
        prev = end
    return shots


SH_I = build([
    (3.0, 'i_cam', dict(cam='chase')),
    (5.6, 'auto_pov', dict()),
    (8.0, 'i_cam', dict(cam='chase')),
    (11.0, 'i_top', dict(trail=True)),
    (14.6, 'i_cam', dict(cam='high')),
    (17.2, 'i_cam', dict(cam='front')),
    (20.2, 'auto_pov', dict()),
    (23.2, 'i_top', dict(trail=True)),
    (26.6, 'i_cam', dict(cam='chase')),
    (DUR, 'i_cam', dict(cam='high')),
])
SH_C = build([
    (3.0, 'm_cam', dict(cam='chase')),
    (6.0, 'c_in', dict()),
    (9.0, 'm_cam', dict(cam='follow', off=(-24, 12, -6), look=(0, 0, 10), f=900, hud=False)),
    (12.0, 'm_top', dict(horizontal=True, xc=-3.0, ahead=10.0, scale=30.0)),
    (15.0, 'm_cam', dict(cam='high')),
    (18.0, 'c_in', dict()),
    (21.0, 'm_cam', dict(cam='close_l')),
    (24.0, 'm_cam', dict(cam='follow', off=(2.5, 3.5, 14), look=(0, 1.0, 0), f=950)),
    (27.6, 'm_cam', dict(cam='chase')),
    (DUR, 'm_cam', dict(cam='follow', off=(-22, 16, -10), look=(-2, 0, 30), f=900, hud=False)),
])


def shot_at(shots, t):
    for s in shots:
        if s.start <= t < s.start + s.dur:
            return s
    return shots[-1]


def horns_by(t):
    return sum(1 for t0, a in HORNS if t0 <= t)


def counter(n, col):
    def fn(ctx, lt, d):
        rrect(ctx, 1500, 50, 370, 96, 48)
        setc(ctx, (0, 0, 0), 0.55)
        ctx.fill()
        # tiny horn icon
        poly(ctx, [(1540, 86), (1562, 86), (1600, 66), (1600, 130), (1562, 110), (1540, 110)])
        setc(ctx, hexc(col))
        ctx.fill()
        text_center(ctx, f'HORNS  {n(lt)}', 1730, 117, 50, (1, 1, 1))
    return fn


def hook_text(text):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.15) * smooth((d - lt) / 0.2)
        k = 1 + 0.08 * math.sin(lt * 9)
        ctx.save()
        ctx.translate(960, 330)
        ctx.scale(k, k)
        outlined_text(ctx, text, 0, 0, 120, (1, 0.86, 0.25) if a > 0.5 else (1, 1, 1), lw=18)
        ctx.restore()
    return fn


def stat_card(lines, col):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.25)
        setc(ctx, (0, 0, 0), 0.45 * a)
        ctx.paint()
        sc = 0.8 + 0.2 * smooth(lt / 0.3)
        ctx.save()
        ctx.translate(960, 560)
        ctx.scale(sc, sc)
        rrect(ctx, -560, -250, 1120, 470, 60)
        setc(ctx, hexc(col), 0.95 * a)
        ctx.fill()
        for i, (txt, size) in enumerate(lines):
            text_center(ctx, txt, 0, -130 + i * 150, size, (1, 1, 1), a=a)
        ctx.restore()
    return fn


T_END = 27.6
OV_I = [
    (0, DUR, location_tag('Mumbai, India')),
    (0, DUR, counter(lambda lt: horns_by(lt), '#ffd23f')),
    (0.0, 3.0, hook_text('Would YOU drive here?')),
    (3.2, 5.6, caption('No lanes. Just gaps.')),
    (8.2, 11.0, caption('Every gap gets filled')),
    (11.4, 14.6, caption('Cow on the road? Normal.')),
    (17.4, 20.2, caption("Horn = \"I'm here!\"")),
    (23.4, 26.6, caption('Bikes from every side')),
    (T_END, DUR, stat_card([(f'{sum(1 for t0, a in HORNS if t0 < DUR)} horns', 130), (f'{LANE_CHANGES} lane changes', 84)], '#e8590c')),
]
OV_C = [
    (0, DUR, location_tag('Niagara Parkway, Ontario, Canada')),
    (0, DUR, counter(lambda lt: 0, '#9fd3ff')),
    (0.0, 3.0, hook_text('...or here?')),
    (3.2, 6.0, caption('Lanes. Space. Calm.')),
    (9.2, 12.0, caption('Everyone keeps their lane')),
    (15.2, 18.0, caption('No horns. Just the river.')),
    (21.2, 24.0, caption('Lots of space ahead')),
    (T_END, DUR, stat_card([('0 horns', 130), ('0 lane changes', 84)], '#c8102e')),
]
PANELS = [(TOP_Y, world_i, SH_I, OV_I), (BOT_Y, world_c, SH_C, OV_C)]


def india_flag(ctx, x, y, w):
    h = w * 2 / 3
    for i, c in enumerate(('#ff9933', '#ffffff', '#138808')):
        ctx.rectangle(x, y + i * h / 3, w, h / 3)
        setc(ctx, hexc(c))
        ctx.fill()
    ctx.arc(x + w / 2, y + h / 2, h / 7, 0, 2 * math.pi)
    setc(ctx, hexc('#000080'))
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.rectangle(x, y, w, h)
    setc(ctx, OUTL)
    ctx.set_line_width(2)
    ctx.stroke()


def canada_flag(ctx, x, y, w):
    h = w / 2
    ctx.rectangle(x, y, w, h)
    setc(ctx, (1, 1, 1))
    ctx.fill()
    for xx in (x, x + w * 0.75):
        ctx.rectangle(xx, y, w / 4, h)
        setc(ctx, hexc('#d52b1e'))
        ctx.fill()
    cx, cy, s = x + w / 2, y + h / 2, h * 0.42
    leaf = [(0, -1.0), (0.12, -0.72), (0.3, -0.8), (0.24, -0.38), (0.55, -0.6), (0.5, -0.45), (0.78, -0.42), (0.62, -0.22),
            (0.7, -0.12), (0.3, 0.12), (0.34, 0.3), (0.04, 0.24), (0.04, 0.62), (-0.04, 0.62), (-0.04, 0.24), (-0.34, 0.3),
            (-0.3, 0.12), (-0.7, -0.12), (-0.62, -0.22), (-0.78, -0.42), (-0.5, -0.45), (-0.55, -0.6), (-0.24, -0.38),
            (-0.3, -0.8), (-0.12, -0.72)]
    poly(ctx, [(cx + px * s, cy + py * s) for px, py in leaf])
    setc(ctx, hexc('#d52b1e'))
    ctx.fill()
    ctx.rectangle(x, y, w, h)
    setc(ctx, OUTL)
    ctx.set_line_width(2)
    ctx.stroke()


class SplitVideo(Video):
    def __init__(self):
        super().__init__(['India vs Canada'], world_i, SH_I)
        self.dur = DUR

    def header(self, ctx, t):
        if t < T_END:
            ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(78)
            parts = [('INDIA', hexc('#ff9933')), ('  vs  ', (1, 1, 1)), ('CANADA', hexc('#ff4b4b'))]
            wsum = sum(ctx.text_extents(p)[4] for p, _ in parts)
            fw, gap = 78, 22
            x = W / 2 - wsum / 2
            india_flag(ctx, x - gap - fw, 162, fw)
            canada_flag(ctx, x + wsum + gap, 168, fw)
            for p, c in parts:
                ctx.move_to(x, 214)
                setc(ctx, c)
                ctx.show_text(p)
                x += ctx.text_extents(p)[4]
            text_center(ctx, 'Same 30 seconds on the road', W / 2, 292, 40, (0.8, 0.82, 0.88))
        else:
            u = smooth((t - T_END) / 0.3)
            text_center(ctx, 'Where would YOU drive?', W / 2, 200, 76, (1, 1, 1), a=u)
            text_center(ctx, 'Comment INDIA or CANADA', W / 2, 290, 62, hexc('#ffd23f'), a=u)

    def frame(self, ctx, t):
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        self.header(ctx, t)
        for y0, w, shots, ovs in PANELS:
            s = shot_at(shots, t)
            ctx.save()
            ctx.rectangle(0, y0, W, PH)
            ctx.clip()
            ctx.translate(0, y0)
            ctx.scale(SCALE, SCALE)
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
            SCENES[s.kind](ctx, w, t, t - s.start, s.kw)
            for t0, t1, fn in ovs:
                if t0 <= t < t1:
                    fn(ctx, t - t0, t1 - t0)
            ctx.restore()
        # VS badge between the panels
        cy = TOP_Y + PH + 32
        ctx.rectangle(0, cy - 3, W, 6)
        setc(ctx, (1, 1, 1), 0.85)
        ctx.fill()
        ellipse(ctx, W / 2, cy, 58, 58)
        fill_stroke(ctx, hexc('#e0393e'), (1, 1, 1), 6)
        text_center(ctx, 'VS', W / 2, cy + 17, 50, (1, 1, 1))


video = SplitVideo()


# ================================================================== sound
def horn_f(dur, f1, f2, bright=14, drive=1.6):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = np.zeros(n)
    for f in (f1, f2):
        ph = 2 * np.pi * f * tt * (1 + 0.003 * np.sin(2 * np.pi * 6 * tt))
        for k in range(1, bright):
            s += np.sin(k * ph) / k
    s = np.tanh(s * drive)
    s = bp(s, 250, 4200)
    return s * env_adsr(n, 0.01, 0.05) * 0.55


HORN_SND = {'auto': lambda: horn_f(0.16, 560, 700, 8, 2.2), 'bike': lambda: horn_f(0.22, 620, 780, 10),
            'car': lambda: horn_f(0.32, 410, 515), 'bus': lambda: horn_f(0.6, 280, 350, 16, 2.0)}


def two_stroke(dur, spd_fn):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    grid = np.arange(0, dur + 1, 0.05)
    sp = np.interp(tt, grid, [spd_fn(g) for g in grid])
    f = 38 + sp * 4.2
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.zeros(n)
    for k in range(1, 9):
        s += np.sin(k * ph + 0.3 * k) / k ** 0.8
    rasp = bp(noise(n), 600, 3000) * (0.5 + 0.5 * np.sin(ph)) ** 4
    return lp(np.tanh(s * 1.4), 1400) * 0.5 + rasp * 0.25


def sound():
    m = Mixer(DUR)
    n = int(DUR * SR)
    tt = np.arange(n) / SR
    # Mumbai bed: crowd murmur + traffic rumble + our auto's two-stroke buzz
    murmur = bp(noise(n), 250, 1700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * tt) ** 2)
    m.add(murmur, 0, 0.11)
    m.add(lp(noise(n), 180), 0, 0.5)
    m.add(two_stroke(DUR, ego_i.speed), 0, 0.16)
    # horns (all counted on screen)
    for t0, a in HORNS:
        kind = 'auto' if a is ego_i else getattr(a, 'kind', 'car')
        g = 0.75 if a is ego_i else 0.5
        x = a.pose(t0)[0] - ego_i.pose(t0)[0]
        m.add(HORN_SND[kind](), t0, g, clamp(x / 8, -0.7, 0.7))
        if a is ego_i:
            m.add(HORN_SND['auto'](), t0 + 0.2, g * 0.9)
    # bikes zipping past
    for t0 in np.arange(1.0, 30, 2.3):
        m.add(car_pass(1.2, 0.5, 150), t0, 0.18, np.linspace(0.6, -0.6, int(1.2 * SR)))
    m.add(heartbeat(2, 120), 0.1, 0.5)
    # Niagara: soft tyre/wind hush (quiet under the city)
    m.add(lp(noise(n), 500) * 0.6, 0, 0.12)
    for o in ONC_C:
        ez = lambda t: SPEED_C * t
        tp = (o.z0) / (o.v + SPEED_C)
        if 0.5 < tp < DUR - 1:
            m.add(car_pass(1.6, 0.5, 90), tp - 0.8, 0.22, np.linspace(-0.6, 0.6, int(1.6 * SR)))
    # end: stats + question
    m.add(impact(), T_END, 0.35)
    m.add(pop(), T_END + 0.1, 0.8)
    m.add(success_jingle(), T_END + 0.6, 0.8)
    return m.out(DUR)


# ================================================================== checks
def verify():
    print('mumbai vehicles kept:', len(OTHERS_I), 'oncoming:', len(ONC), 'horns:', len(HORNS))
    worst = (99, None)
    for i, (a, k, A) in enumerate(KEPT):
        for b, kb, B in KEPT[i + 1:]:
            xa, za, wa, la = A
            xb, zb, wb, lb = B
            lat = np.abs(xa - xb) - (wa + wb)
            lon = np.abs(za - zb) - (la + lb)
            over = (lon < LONM)
            if np.any(over):
                m_ = float(np.min(lat[over]))
                if m_ < worst[0]:
                    j = int(np.argmin(np.where(over, lat, 99)))
                    worst = (round(m_, 3), (k, kb, round(TG[j], 2)))
    print('closest lateral clearance while side by side (m):', worst)
    cnt = [sum(1 for a in OTHERS_I if abs(a.pose(t)[1] - ego_i.tr.z(t)) < 30) for t in range(0, 31)]
    print('vehicles within 30 m of the auto per second:', cnt)
    xs = [a.pose(t)[0] for a in OTHERS_I for t in (0, 15, 30)]
    print('x range of mumbai traffic', round(min(xs), 2), round(max(xs), 2))
    print('cow z', round(COW_Z, 1), 'ego x at cow', round(EGO_X(14.6), 2))
    print('canada gap to lead car (m):', round(lead_c.z(5) - ego_c.z(5) - 4.4, 1), 'speed km/h', round(SPEED_C * 3.6))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    elif len(sys.argv) > 2 and sys.argv[2] == 'still':
        for tt in sys.argv[3:]:
            video.render_still(float(tt), sys.argv[1].replace('.png', f'_{tt}.png'))
    else:
        video.render(sys.argv[1] if len(sys.argv) > 1 else 'india_canada.mp4', sound(), (sys.argv[1] if len(sys.argv) > 1 else 'ic') + '_work')
