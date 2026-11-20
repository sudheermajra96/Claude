"""Skilled truck driving: a one-lane truss bridge in the Alberta Rockies. Hook in the first 3 seconds.
Physics: pure-pursuit tractor + kingpin-follower trailer (bridgesim.py)."""
import math
import random

import cairo
import numpy as np

import bridgesim as B
from citykit import *
from truckkit import tractor_det, trailer_det, draw_car_round, wheel3
import citykit

engine.DAY = True
VOFF = 2.0                                                      # video time = sim time + VOFF (after the hook)
SPEED = Key([(0, 14), (3.5, 14), (8.0, 4), (9.6, 0), (12.6, 0), (14.2, 5), (21, 5), (23, 4.2), (80, 4.2)], 'lin')
PRO = B.make_path(6, 10, 3.0, 0.0, 10)
NOOB = B.make_path(14, 13, 0.0)
LOGP = B.simulate(PRO, SPEED, x0=110.0, dur=50)
LOGN = B.simulate(NOOB, SPEED, x0=110.0, dur=50)
GT = LOGP[:, 0] + VOFF


def fx(arr, t):
    return float(np.interp(t, GT, arr))


def corners_all(i, log=LOGP):
    t, x, z, h1, h2, v, d = log[i]
    return B.corners_trailer(x, z, h2) + B.corners_tractor(x, z, h1)


on_bridge = [any(B.BRIDGE_Z0 - 0.2 < cz < B.BRIDGE_Z1 + 0.2 for cx, cz in corners_all(i)) for i in range(len(LOGP))]
I_ON = on_bridge.index(True)
I_OFF = len(on_bridge) - 1 - on_bridge[::-1].index(True)
T_ON, T_OFF = GT[I_ON], GT[I_OFF]
T_STOP = GT[np.argmax((LOGP[:, 0] > 5) & (LOGP[:, 5] < 0.05))]
T_GO = 12.6 + VOFF
CLEAR_L = min(min(cx + B.BRIDGE_HALF for cx, cz in corners_all(i) if B.BRIDGE_Z0 - 0.2 < cz < B.BRIDGE_Z1 + 0.2)
              for i in range(I_ON, I_OFF, 6))
CLEAR_R = min(min(B.BRIDGE_HALF - cx for cx, cz in corners_all(i) if B.BRIDGE_Z0 - 0.2 < cz < B.BRIDGE_Z1 + 0.2)
              for i in range(I_ON, I_OFF, 6))
# beginner hits the rock: first collision index
I_HIT = next(i for i in range(len(LOGN)) if any(B.in_rock(cx, cz) for cx, cz in corners_all(i, LOGN)))


class Truck:
    col = '#c8312f'

    def state(self, t):
        return fx(LOGP[:, 1], t), fx(LOGP[:, 2], t), fx(LOGP[:, 3], t), fx(LOGP[:, 4], t)

    def pose(self, t):
        x, z, h1, h2 = self.state(t)
        return x, z, h1

    def speed(self, t):
        return fx(LOGP[:, 5], t)

    def steer(self, t):
        return clamp(fx(LOGP[:, 6], t) * 2.6, -1.6, 1.6)

    def blink(self, t):
        return 'R' if T_STOP - 2.0 < t < T_GO + 6.0 and (t * 1.25) % 1 < 0.5 else None

    brake = staticmethod(lambda t: 0.0)

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        x, z, h1, h2 = self.state(t)
        bl = self.blink(t)
        braking = self.speed(t + 0.3) < self.speed(t) - 0.05
        tc = (x + math.sin(h1) * 2.5, 1.5, z + math.cos(h1) * 2.5)
        trc = (x - math.sin(h2) * 7.2, 2.0, z - math.cos(h2) * 7.2)
        if view.ortho:
            return [(tc, lambda: truck_top(ctx, view, x, z, h1, h2, bl, self.col))]
        return [(tc, lambda: tractor_det(ctx, view, x, z, h1, self.col, False, bl)),
                (trc, lambda: trailer_det(ctx, view, x, z, h2, False, False, braking))]


def truck_top(ctx, view, x, z, h1, h2, bl, col, alpha=1.0, outline=None):
    Lt, Lr = L(x, z, h2), L(x, z, h1)
    fill_poly(ctx, view, [Lt(-1.3, 0, -15.3), Lt(1.3, 0, -15.3), Lt(1.3, 0, 0.9), Lt(-1.3, 0, 0.9)],
              hexc('#f4f4f6'), outline or OUTL, 4, alpha)
    fill_poly(ctx, view, [Lt(-1.3, 0, -15.3), Lt(1.3, 0, -15.3), Lt(1.3, 0, -14.8), Lt(-1.3, 0, -14.8)], hexc('#d62828'), None, 3, alpha)
    fill_poly(ctx, view, [Lr(-1.25, 0, -1.6), Lr(1.25, 0, -1.6), Lr(1.25, 0, 6.15), Lr(-1.25, 0, 6.15)], hexc(col), outline or OUTL, 4, alpha)
    fill_poly(ctx, view, [Lr(-1.1, 0, 2.6), Lr(1.1, 0, 2.6), Lr(1.1, 0, 3.4), Lr(-1.1, 0, 3.4)], hexc('#2a3448'), None, 3, alpha)
    if bl == 'R':
        for lz in (6.0, -14.9):
            Lf = Lr if lz > 0 else Lt
            p = view.pt(Lf(1.25, 0, lz))
            glow(ctx, p[0], p[1], 1.6 * view.s, AMBER, 0.9)


class Car:
    """Oncoming car: crosses the bridge southbound, turns left (east) and passes the waiting truck."""

    def __init__(self):
        self.path = Path([('L', (0, 140), (0, 4)), ('S', [(0, 4), (-0.6, -6), (-1.8, -16), (-1.8, -34)]),
                          ('A', (5.2, -39.8), 7.0, 180, 270), ('L', (5.2, -46.8), (200, -46.8))])
        k = Key([(-10, 9), (60, 9)])
        self.m = Mover(self.path, k, 13.6, self.path.s_near(20.0, -46.8), '#3a7bd5', t0=-10, t1=60)
        self.col = '#3a7bd5'

    def pose(self, t):
        return self.m.pose(t)

    def blink(self, t):
        x, z, h = self.pose(t)
        return 'L' if -40 < z < -12 and (t * 1.25) % 1 < 0.5 else None

    def brake(self, t):
        return 0.0

    def visible(self, t):
        return True


CAR = Car()


# ------------------------------------------------------------- scenery
def fillet_pts(n=24):
    c, r = B.FILLET_C, B.FILLET_R
    return [(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))) for a in np.linspace(270, 180, n)]


ROCK_OUTLINE = [(B.ROCK_X, -1.5)] + [(B.ROCK_X, B.FILLET_C[1])] + fillet_pts()[::-1][1:-1] + [(B.FILLET_C[0], B.ROCK_Z), (60, B.ROCK_Z), (60, -1.5)]


def rock_wall(ctx, view, h=7.0):
    pts = ROCK_OUTLINE
    top = [(x, h + 1.5 * math.sin(x * 0.7 + z * 0.3), z) for x, z in pts]
    if view.ortho:
        fill_poly(ctx, view, [(x, 0, z) for x, z in pts], hexc('#8d8577'), OUTL, 3)
        return
    faces = []
    for (x0, z0), (x1, z1), t0, t1 in zip(pts, pts[1:], top, top[1:]):
        nx, nz = (z1 - z0), -(x1 - x0)                 # outward normal (polygon is clockwise on the map)
        if (view.pos[0] - x0) * nx + (view.pos[2] - z0) * nz <= 0:
            continue
        q = [(x0, 0, z0), (x1, 0, z1), t1, t0]
        faces.append((view.depth(((x0 + x1) / 2, h / 2, (z0 + z1) / 2)), q, (x0 + z0) % 3))
    for _, q, k in sorted(faces, key=lambda f: -f[0]):
        fill_poly(ctx, view, q, mix(hexc('#9a9184'), hexc('#6f685e'), 0.25 * k), OUTL, 2)
        a, b = view.pt(((q[0][0] + q[1][0]) / 2, 1.5, (q[0][2] + q[1][2]) / 2)), view.pt(((q[0][0] + q[1][0]) / 2, 4.5, (q[0][2] + q[1][2]) / 2))
        if a and b:
            ctx.move_to(*a)
            ctx.line_to(b[0] + 6, b[1])
            setc(ctx, hexc('#5f584f'))
            ctx.set_line_width(2)
            ctx.stroke()
    if view.pos[1] > h:
        fill_poly(ctx, view, top, hexc('#5f8a4f'), OUTL, 2)


def beam(ctx, view, a, b, w=0.22, col='#5d6b7a'):
    """3D-ish steel member from a to b drawn as a thick outlined line with perspective width."""
    pa, pb = view.pt(a), view.pt(b)
    if not pa or not pb:
        return
    sa, sb = view.scale(a), view.scale(b)
    wd = max(2.0, min(60, w * (sa + sb) / 2))
    ctx.move_to(*pa)
    ctx.line_to(*pb)
    setc(ctx, OUTL)
    ctx.set_line_width(wd + 4)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    ctx.move_to(*pa)
    ctx.line_to(*pb)
    setc(ctx, hexc(col))
    ctx.set_line_width(wd)
    ctx.stroke()


BAY = 5.0
TRUSS_X = 2.15
TRUSS_H = 5.6


def truss_side(ctx, view, sx):
    x = sx * TRUSS_X
    zs = np.arange(B.BRIDGE_Z0, B.BRIDGE_Z1 + 0.01, BAY)
    segs = []
    for z0, z1 in zip(zs, zs[1:]):
        segs.append(((x, 0.4, z0), (x, 0.4, z1), 0.32))
        segs.append(((x, TRUSS_H, z0), (x, TRUSS_H, z1), 0.32))
        segs.append(((x, 0.4, z0), (x, TRUSS_H, z1) if int(z0 / BAY) % 2 == 0 else (x, TRUSS_H, z0), 0.22))
        segs.append(((x, TRUSS_H, z0), (x, 0.4, z1)) + (0.22,) if int(z0 / BAY) % 2 == 0 else ((x, 0.4, z0), (x, TRUSS_H, z1), 0.22))
    for z in zs:
        segs.append(((x, 0.0, z), (x, TRUSS_H, z), 0.26))
    segs.append(((x, 1.0, B.BRIDGE_Z0), (x, 1.0, B.BRIDGE_Z1), 0.12))         # inner rub rail
    for a, b, w in sorted(segs, key=lambda s: -view.depth(((s[0][0] + s[1][0]) / 2, (s[0][1] + s[1][1]) / 2, (s[0][2] + s[1][2]) / 2))):
        beam(ctx, view, a, b, w)


def truss_top(ctx, view):
    for z in np.arange(B.BRIDGE_Z0, B.BRIDGE_Z1 + 0.01, BAY):
        beam(ctx, view, (-TRUSS_X, TRUSS_H, z), (TRUSS_X, TRUSS_H, z), 0.22)
    for z0 in np.arange(B.BRIDGE_Z0, B.BRIDGE_Z1, BAY):
        beam(ctx, view, (-TRUSS_X, TRUSS_H, z0), (TRUSS_X, TRUSS_H, z0 + BAY), 0.1)


def portal_sign(ctx, view, z, face_h):
    pts = [(-1.6, TRUSS_H - 0.1, z), (1.6, TRUSS_H - 0.1, z), (1.6, TRUSS_H - 1.0, z), (-1.6, TRUSS_H - 1.0, z)]
    if not front_facing(view, 0, z, face_h):
        fill_poly(ctx, view, pts, hexc('#9aa0aa'), OUTL, 2)
        return
    fill_poly(ctx, view, pts, hexc('#f2c230'), OUTL, 2)
    c, s = view.pt((0, TRUSS_H - 0.55, z)), view.scale((0, TRUSS_H - 0.55, z))
    if c and s and s > 12:
        text_center(ctx, 'ONE LANE BRIDGE', c[0], c[1] + s * 0.14, s * 0.36, OUTL)


def bridge(ctx, view, t):
    z0, z1 = B.BRIDGE_Z0, B.BRIDGE_Z1
    if view.ortho:
        fill_poly(ctx, view, [(-TRUSS_X - 0.3, 0, z0), (TRUSS_X + 0.3, 0, z0), (TRUSS_X + 0.3, 0, z1), (-TRUSS_X - 0.3, 0, z1)], hexc('#5d6b7a'), OUTL, 3)
        fill_poly(ctx, view, [(-1.8, 0, z0), (1.8, 0, z1 * 0 + z0), (1.8, 0, z1), (-1.8, 0, z1)], hexc('#8a7a66'))
        return
    # piers + deck
    for zz in (z0 + 0.5, (z0 + z1) / 2, z1 - 0.5):
        fill_poly(ctx, view, [(-2.4, -6, zz), (2.4, -6, zz), (2.4, -0.4, zz), (-2.4, -0.4, zz)], hexc('#9aa0aa'), OUTL, 2)
    fill_poly(ctx, view, [(-TRUSS_X - 0.3, -0.45, z0), (TRUSS_X + 0.3, -0.45, z0), (TRUSS_X + 0.3, 0, z0), (-TRUSS_X - 0.3, 0, z0)], hexc('#5d6b7a'), OUTL, 2)
    fill_poly(ctx, view, [(-1.8, 0.02, z0), (1.8, 0.02, z0), (1.8, 0.02, z1), (-1.8, 0.02, z1)], hexc('#8a7a66'))
    for zz in np.arange(z0, z1, 0.6):
        fill_poly(ctx, view, [(-1.8, 0.025, zz), (1.8, 0.025, zz), (1.8, 0.025, zz + 0.05), (-1.8, 0.025, zz + 0.05)], hexc('#6e604f'))
    for sx in (-1, 1):
        fill_poly(ctx, view, [(sx * 1.8, 0.0, z0), (sx * 1.8, 0.0, z1), (sx * 1.8, 0.35, z1), (sx * 1.8, 0.35, z0)], hexc('#c9c4ba'), OUTL, 1.5)


def river(ctx, view, t):
    gquad(ctx, view, -400, 400, 1.0, 39.0, hexc('#3fb5c4'))
    for i in range(26):
        x0 = ((i * 37) % 300 - 150) + (t * 1.8) % 30 - 15
        z0 = 4 + (i * 7) % 32
        gquad(ctx, view, x0, x0 + 6, z0, z0 + 0.25, hexc('#8fe0e8'), 0.01)
    gquad(ctx, view, -400, 400, -0.5, 1.0, hexc('#a39a8c'))
    gquad(ctx, view, -400, 400, 39.0, 40.5, hexc('#a39a8c'))


class Rockies:
    ground_col = hexc('#6f9a5c')
    sky = ('#5fa6e0', '#e4f3ff')

    def __init__(self):
        r = random.Random(7)
        self.trees = []
        for _ in range(420):
            x, z = r.uniform(-160, 160), r.uniform(-140, 200)
            if -50.5 < z < -39.5 and x > -8:          # main road
                continue
            if -1 < z < 41:                          # river
                continue
            if -5 < x < 5 and z > -50:              # stub road / bridge / north road
                continue
            if B.ROCK_X < x < 60 and -41.4 < z < -1.5:   # rock outcrop (trees on top added separately)
                continue
            if x < -8 and -50.5 < z < -39.5:
                continue
            self.trees.append((x, z, r.uniform(0.8, 1.5)))
        self.rock_trees = []
        for _ in range(60):
            x, z = r.uniform(6, 58), r.uniform(-39, -3)
            if B.in_rock(x, z) and math.hypot(x - B.FILLET_C[0], z - B.FILLET_C[1]) > B.FILLET_R + 2.5:
                self.rock_trees.append((x, z, r.uniform(0.8, 1.2)))

    def skyline(self, ctx, view):
        r = random.Random(3)
        peaks = []
        for i, x in enumerate(range(-3600, 3601, 260)):
            peaks.append((x, r.uniform(900, 1700) if i % 2 else r.uniform(500, 900)))
        mountains(ctx, view, peaks, 3000, snow=True)
        if view.ortho:
            return
        pts = [view.pt((x, 220 + 120 * math.sin(x / 260) + 60 * math.sin(x / 90), 1400)) for x in range(-2400, 2401, 120)]
        base = view.pt((0, 0, 1400))
        if base and all(pts):
            ctx.move_to(pts[0][0] - 2000, base[1] + 4)
            for p in pts:
                ctx.line_to(*p)
            ctx.line_to(pts[-1][0] + 2000, base[1] + 4)
            ctx.close_path()
            setc(ctx, hexc('#3f6b52'))
            ctx.fill()

    def ground(self, ctx, view, t):
        river(ctx, view, t)
        fill_poly(ctx, view, [(-400, 0, -48.6), (400, 0, -48.6), (400, 0, -41.4), (-400, 0, -41.4)], C_ASPH)
        gquad(ctx, view, -3.6, 3.6, -41.5, -1.0, C_ASPH)
        fill_poly(ctx, view, [(3.6, 0, -41.4), (B.FILLET_C[0], 0, -41.4)] + [(x, 0, z) for x, z in fillet_pts()] + [(3.6, 0, B.FILLET_C[1])], C_ASPH)
        fill_poly(ctx, view, [(-3.6, 0, -6), (-1.8, 0, -1.0), (-3.6, 0, -1.0)], hexc('#6f9a5c'))
        fill_poly(ctx, view, [(3.6, 0, -6), (1.8, 0, -1.0), (3.6, 0, -1.0)], hexc('#8d8577'))
        gquad(ctx, view, -1.8, 1.8, -1.0, 0.0, C_ASPH)
        gquad(ctx, view, -3.6, 3.6, 40.5, 400, C_ASPH)
        for k in range(-40, 40):
            if not (-8 < k * 9 < 16):
                fill_poly(ctx, view, [(k * 9, 0.01, -45.08), (k * 9 + 4, 0.01, -45.08), (k * 9 + 4, 0.01, -44.92), (k * 9, 0.01, -44.92)], C_YEL)
        for zz in (-48.45, -41.55):
            fill_poly(ctx, view, [(-400, 0.01, zz - 0.08), (400, 0.01, zz - 0.08), (400, 0.01, zz + 0.08), (-400, 0.01, zz + 0.08)], C_LINE)
        gquad(ctx, view, -0.08, 0.08, 41, 400, C_YEL, 0.01)
        gquad(ctx, view, -0.08, 0.08, -38, -8, C_YEL, 0.01)
        fill_poly(ctx, view, [(-3.5, 0.012, -8.4), (0, 0.012, -8.4), (0, 0.012, -7.9), (-3.5, 0.012, -7.9)], C_LINE)   # yield line (southbound side has priority)

    def objects(self, ctx, view, t):
        out = [((5, 3, -20), lambda: rock_wall(ctx, view))]
        out.append(((0, 2.5, 20), lambda: bridge_all(ctx, view, t)))
        for x, z, s in self.trees:
            out.append(((x, 3, z), lambda x=x, z=z, s=s: conifer(ctx, view, x, z, s * (0.55 if view.ortho else 1.25))))
        for x, z, s in self.rock_trees:
            yy = 7.0 + 1.5 * math.sin(x * 0.7 + z * 0.3)
            out.append(((x, yy + 3, z), lambda x=x, z=z, s=s, yy=yy: conifer(ctx, view, x, z, s * (0.55 if view.ortho else 1.15), yy - 0.4)))
        # guardrail along the south edge of the main road (valley side)
        if not view.ortho:
            out.append(((0, 0.6, -49.4), lambda: guardrail(ctx, view)))
        out.append(((-4.6, 1.4, -14), lambda: diamond_sign(ctx, view, 4.6, -16, math.pi, one_lane_icon, 'ONE LANE')))
        out.append(((4.6, 1.4, -16), lambda: diamond_sign(ctx, view, 4.6, -16, math.pi, one_lane_icon, 'ONE LANE')))
        out.append(((-4.6, 1.4, -9), lambda: yield_sign_t(ctx, view, -4.6, -9.5, 0.0)))
        return out


def bridge_all(ctx, view, t):
    bridge(ctx, view, t)
    if view.ortho:
        return
    far = sorted((-1, 1), key=lambda sx: -abs(view.pos[0] - sx * TRUSS_X))
    truss_side(ctx, view, far[0])
    truss_top(ctx, view)
    portal_sign(ctx, view, B.BRIDGE_Z0, math.pi)
    portal_sign(ctx, view, B.BRIDGE_Z1, 0.0)
    truss_side(ctx, view, far[1])


def guardrail(ctx, view):
    for x in range(-200, 200, 4):
        beam(ctx, view, (x, 0, -49.3), (x, 0.8, -49.3), 0.12, '#9aa0aa')
    beam(ctx, view, (-200, 0.7, -49.3), (200, 0.7, -49.3), 0.25, '#c9ccd6')


def one_lane_icon(ctx, cx, cy, r):
    for sx in (-1, 1):
        ctx.move_to(cx + sx * r * 0.45, cy + r * 0.55)
        ctx.curve_to(cx + sx * r * 0.45, cy + r * 0.1, cx + sx * r * 0.18, cy - r * 0.1, cx + sx * r * 0.18, cy - r * 0.55)
    setc(ctx, OUTL)
    ctx.set_line_width(max(2, r * 0.12))
    ctx.stroke()


def yield_sign_t(ctx, view, x, z, face_h):
    import ep_roundabout
    ep_roundabout.yield_sign(ctx, view, x, z, face_h)


TRUCK = Truck()
city = Rockies()
world = CityWorld(44, [(0, 99, TRUCK, [CAR])], [], city, 'kmh')
citykit.draw_car_g = draw_car_round           # round tyres for every car in this episode


# ------------------------------------------------------------- cameras & scenes
def truck_cam(mode, t, yaw=0.0):
    x, z, h1, h2 = TRUCK.state(t)
    fx_, fz_ = math.sin(h1), math.cos(h1)
    rx, rz = math.cos(h1), -math.sin(h1)
    ax, az = x - B.L2 * math.sin(h2), z - B.L2 * math.cos(h2)
    bx, bz = -math.sin(h2), -math.cos(h2)
    if mode == 'chase':          # behind & above the trailer
        return look_at((ax + bx * 14, 7.5, az + bz * 14), (x + fx_ * 6, 1.5, z + fz_ * 6), 1000)
    if mode == 'cab':            # driver's seat (left), high
        return TCam((x - rx * 0.55 + fx_ * 2.9, 2.75, z - rz * 0.55 + fz_ * 2.9), h1 + yaw, 0.06, 900, cy=430)
    if mode == 'over':           # high over the cab looking ahead (lining up)
        return look_at((x - fx_ * 7 - rx * 3.2, 7.5, z - fz_ * 7 - rz * 3.2), (x + fx_ * 20, 1.0, z + fz_ * 20), 950)
    raise ValueError(mode)


def b_cam(ctx, w, t, lt, kw):
    tw = t + kw.get('shift', 0.0)
    if kw['cam'] == 'fixed':
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000))
    else:
        view = truck_cam(kw['cam'], tw, key_or(kw, 'yaw', lt, 0.0))
    draw_scene(ctx, view, w, tw)
    if kw['cam'] == 'cab' and abs(key_or(kw, 'yaw', lt, 0.0)) < 0.3:
        cab_frame(ctx, w, tw)
    elif kw['cam'] == 'cab':
        side_window_frame(ctx)
    if kw.get('hud'):
        hud(ctx, w, tw)


def side_window_frame(ctx):
    setc(ctx, hexc('#24242e'))
    ctx.rectangle(-10, -10, SW + 20, 70)
    ctx.fill()
    poly(ctx, [(-10, -10), (240, -10), (160, 900), (-10, 900)])
    ctx.fill()
    ctx.rectangle(-10, 860, SW + 20, 240)
    setc(ctx, hexc('#c8312f'))
    ctx.fill()
    ctx.rectangle(-10, 850, SW + 20, 20)
    setc(ctx, OUTL)
    ctx.fill()


def cab_frame(ctx, w, t):
    setc(ctx, hexc('#24242e'))
    poly(ctx, [(-10, -10), (200, -10), (90, 860), (-10, 860)])
    ctx.fill()
    poly(ctx, [(1720, -10), (SW + 10, -10), (SW + 10, 860), (1830, 860)])
    ctx.fill()
    ctx.rectangle(-10, -10, SW + 20, 60)
    ctx.fill()
    ctx.move_to(-10, 860)
    ctx.curve_to(600, 830, 1300, 830, SW + 10, 860)
    ctx.line_to(SW + 10, SH + 10)
    ctx.line_to(-10, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, hexc('#34343f'), hexc('#4a4a5c'), 5)
    for i, (gx, lab) in enumerate(((760, 'km/h'), (1160, 'RPM'))):
        ellipse(ctx, gx, 960, 80, 80)
        fill_stroke(ctx, hexc('#101018'), hexc('#7a7f90'), 5)
        v = w.speed(t) * 3.6 if i == 0 else 900 + w.speed(t) * 70
        a = math.radians(140 + 260 * clamp(v / (120 if i == 0 else 2400)))
        ctx.move_to(gx, 960)
        ctx.line_to(gx + math.cos(a) * 62, 960 + math.sin(a) * 62)
        setc(ctx, hexc('#ff5a36'))
        ctx.set_line_width(6)
        ctx.stroke()
        text_center(ctx, lab, gx, 1010, 22, (0.8, 0.8, 0.9))
    citykit.wheel(ctx, w.steer(t) * 0.7)


def b_mirror(ctx, w, t, lt, kw):
    side = kw['side']
    sg = -1 if side == 'L' else 1
    x, z, h1, h2 = TRUCK.state(t)
    Lf = L(x, z, h1)
    mp = Lf(sg * 1.7, 2.7, 3.4)
    draw_scene(ctx, TCam(Lf(sg * 0.6, 2.6, 2.9), h1 + sg * 1.1, 0.12, 650), w, t, ego=False)
    setc(ctx, (0.04, 0.05, 0.1), 0.35)
    ctx.paint()
    ctx.save()
    if side == 'R':
        ctx.translate(SW, 0)
        ctx.scale(-1, 1)
    poly(ctx, [(1650, -10), (SW + 10, -10), (SW + 10, SH + 10), (1500, SH + 10)])
    fill_stroke(ctx, hexc(TRUCK.col), OUTL, 6)
    for y0, y1 in ((-60, 200), (40 + 900, 900)):
        ctx.move_to(980 + 240, 545 + (-450 - 60 if y0 < 0 else 450 + 40))
        ctx.line_to(1700, y1)
    setc(ctx, hexc('#2a2c33'))
    ctx.set_line_width(26)
    ctx.stroke()
    rrect(ctx, 980 - 306, 545 - 476, 612, 952, 40)
    fill_stroke(ctx, hexc('#2a2c33'), OUTL, 7)
    ctx.restore()
    mx = 980 if side == 'L' else SW - 980
    ctx.save()
    rrect(ctx, mx - 280, 545 - 450, 560, 900, 26)
    ctx.clip()
    view = TCam(mp, h1 + math.pi - sg * 0.06, 0.1, 650, cx=mx - sg * 40, cy=480, mirror=True)
    draw_scene(ctx, view, w, t)
    g = cairo.LinearGradient(mx - 280, 95, mx + 280, 995)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.12)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()


def b_top(ctx, w, t, lt, kw):
    view = TopN(kw.get('xc', 4.0), kw.get('zc', -30.0), kw.get('scale', 17.0))

    def under(c, v):
        a = smooth((lt - 0.3) / 0.4)
        pts = [v.pt((x, 0, z)) for x, z in PRO[::6] if -60 < z < 10 and x < 40]
        if a > 0 and len(pts) > 1:
            arrow_path(c, pts, hexc('#22c35e'), 9, a, dash=[18, 12], head=26)
    draw_scene(ctx, view, w, t, overlay=under)
    b = smooth((lt - 0.8) / 0.4)
    if b > 0:
        tt, x, z, h1, h2, v, d = LOGN[I_HIT + 30]
        truck_top(ctx, view, x, z, h1, h2, None, '#e0393e', 0.55 * b, hexc('#e0393e'))
        cx, cz = max(B.corners_trailer(x, z, h2), key=lambda p: (p[0] > B.ROCK_X) * 10 - abs(p[1] + 30))
        p = view.pt((cx, 0, cz))
        for rr in (40, 60):
            ctx.new_sub_path()
            ctx.arc(p[0], p[1], rr * b, 0, 2 * math.pi)
        setc(ctx, hexc('#e0393e'), b)
        ctx.set_line_width(6)
        ctx.stroke()
        label(ctx, p[0] + 260, p[1] + 10, 'Turn too early: trailer hits the rock', '#e0393e', 36)
        q = view.pt((-6, 0, -18))
        label(ctx, q[0] - 230, q[1], 'Pro: swing wide, line up', '#22a356', 36)


engine.SCENES.update(b_cam=b_cam, b_mirror=b_mirror, b_top=b_top)


# ------------------------------------------------------------- overlays
def clearance_meter(ctx, lt, d):
    t = T_ON + lt
    i = int(np.searchsorted(GT, t))
    pts = [(cx, cz) for cx, cz in corners_all(min(i, len(LOGP) - 1)) if B.BRIDGE_Z0 - 0.2 < cz < B.BRIDGE_Z1 + 0.2]
    if not pts:
        return
    l = min(cx + B.BRIDGE_HALF for cx, cz in pts) * 100
    r = min(B.BRIDGE_HALF - cx for cx, cz in pts) * 100
    rrect(ctx, 450, 880, 1020, 165, 36)
    setc(ctx, (0, 0, 0), 0.65)
    ctx.fill()
    for x0, lab, val in ((600, 'LEFT', l), (1320, 'RIGHT', r)):
        col = hexc('#22c35e') if val > 40 else (hexc('#ffd23f') if val > 25 else hexc('#ff4b4b'))
        text_center(ctx, lab, x0, 935, 40, (0.85, 0.85, 0.9))
        text_center(ctx, f'{int(round(val))} cm', x0, 1015, 76, col)
    text_center(ctx, 'CLEARANCE', 960, 980, 40, (1, 1, 1))


def big_text(text, y, size, col=(1, 1, 1), delay=0.0, pulse=False):
    def fn(ctx, lt, d):
        u = lt - delay
        if u < 0:
            return
        a = smooth(u / 0.2)
        sc = 1 + 0.35 * (1 - smooth(u / 0.25))
        if pulse:
            sc *= 1 + 0.04 * math.sin(lt * 9)
        ctx.save()
        ctx.translate(960, y)
        ctx.scale(sc, sc)
        outlined_text(ctx, text, 0, 0, size, col, lw=size * 0.2)
        ctx.restore()
    return fn


def gap_markers(ctx, lt, d):
    """Red pulsing brackets on both sides of the truck in the hook shot."""
    a = 0.6 + 0.4 * math.sin(lt * 10)
    for sx in (-1, 1):
        x = 960 + sx * 380
        ctx.move_to(x - sx * 40, 520)
        ctx.line_to(x, 520)
        ctx.line_to(x, 820)
        ctx.line_to(x - sx * 40, 820)
        setc(ctx, hexc('#ff4b4b'), a)
        ctx.set_line_width(10)
        ctx.stroke()


def end_card(ctx, lt, d):
    a = smooth(lt / 0.3)
    label(ctx, 960, 200, f'Made it! Only {int(round(min(CLEAR_L, CLEAR_R) * 100))} cm to spare', '#22a356', 66)
    if lt > 1.0:
        b = smooth((lt - 1.0) / 0.3)
        ctx.save()
        ctx.translate(960, 330)
        ctx.scale(0.8 + 0.2 * b, 0.8 + 0.2 * b)
        label(ctx, 0, 0, 'Could YOU drive this? Comment YES or NO', '#e0393e', 58)
        ctx.restore()


T_HOOK = T_ON + 6.5          # tractor halfway over the bridge
HOOK = 3.0
shots_def = [
    (HOOK, 'b_cam', dict(cam='fixed', pos=(0.25, 2.0, 42.5), target=(0, 2.5, 24), f=1000, shift=T_HOOK - 0.0)),   # HOOK (flash-forward)
    (HOOK + 2.6, 'b_cam', dict(cam='fixed', pos=(70, 34, -110), target=(4, 0, -22), f=1000)),                   # establishing
    (T_STOP - 0.2, 'b_cam', dict(cam='chase', hud=True)),                                                       # 1 slow down
    (T_GO + 0.3, 'b_cam', dict(cam='cab', yaw=0.12)),                               # 2 oncoming: wait
    (T_GO + 6.2, 'b_top', dict(xc=6.0, zc=-30.0, scale=18.0)),                                                  # 3 swing wide
    (T_ON + 0.2, 'b_cam', dict(cam='over')),                                                                    # 4 line up straight
    (T_ON + 3.6, 'b_mirror', dict(side='L')),                                                                   # 5 mirrors
    (T_ON + 6.6, 'b_mirror', dict(side='R')),
    (T_ON + 10.2, 'b_cam', dict(cam='cab')),                                                                    # 6 slow & steady
    (T_OFF + 0.6, 'b_cam', dict(cam='fixed', pos=(-7.5, 3.2, 52), target=(0, 2.0, 34), f=950)),                 # 7 trailer clears
    (T_OFF + 5.0, 'b_cam', dict(cam='fixed', pos=(-48, 30, -6), target=(0, 2, 30), f=1000)),                    # end
]
shots, prev = [], 0.0
for end, kind, kw in shots_def:
    shots.append(Shot(end - prev, kind, **kw))
    prev = end
video = Video(['Can this truck fit', 'on a one-lane bridge?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
steps = ['Slow down early', 'Oncoming traffic? Stop & wait', 'Swing wide so the trailer clears',
         'Line up dead straight', 'Watch BOTH mirrors', None, 'Slow & steady: no sudden moves', 'Check the trailer clears the end']
video.overlays = [
    (0.0, HOOK, gap_markers),
    (0.0, HOOK, big_text('Only 50 cm each side...', 190, 118)),
    (0.0, HOOK, big_text('Will it fit?', 360, 170, hexc('#ffd23f'), 0.9, True)),
    (HOOK, HOOK + 2.6, big_text('Watch how a PRO does it', 230, 108, hexc('#ffd23f'))),
    (HOOK + 0.3, HOOK + 2.4, location_tag('Kananaskis, Alberta')),
    (T_ON, T_OFF + 0.4, clearance_meter),
    (S[10] + 0.2, E[10], end_card),
]
n = 0
for i, txt in enumerate(steps):
    k = i + 2
    if txt is None:
        continue
    n += 1
    e_ = E[k + 1] if txt == 'Watch BOTH mirrors' else E[k]
    video.overlays += [(S[k], e_, step_badge(n)), (S[k] + 0.15, e_, caption_in_scene(txt) if k < 6 else
                                                                         (lambda txt=txt: (lambda ctx, lt, d: label(ctx, 960, 830, txt, (0.1, 0.1, 0.12), 48)))())]


# ------------------------------------------------------------- sound
def river_sound(d):
    t = np.arange(int(d * SR)) / SR
    return bp(noise(len(t)), 300, 4000) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t)) * 0.18


def diesel(d, speed_fn):
    t = np.arange(int(d * SR)) / SR
    grid = np.arange(0, d + 1, 1 / 30)
    v = np.interp(t, grid, [speed_fn(g) for g in grid])
    f0 = 22 + v * 2.2
    ph = 2 * np.pi * np.cumsum(f0) / SR
    s = sum(np.sin(k * ph + k) / k for k in range(1, 8))
    return lp(s * (1 + 0.25 * np.sin(ph * 0.5)), 300) * 0.22


def air_brake():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    return hp(noise(n), 2500) * np.exp(-t / 0.25) * 0.5


def deck_thump():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.06) + bp(noise(n), 200, 1500) * np.exp(-t / 0.03) * 0.4) * 0.6


def creak(d=1.2):
    t = np.arange(int(d * SR)) / SR
    f = 180 + 40 * np.sin(2 * np.pi * 0.8 * t) + lp(noise(len(t)), 5) * 200
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.2
    return bp(s, 200, 2000) * env_adsr(len(t), 0.3, 0.3) * 0.5


def sound():
    m = Mixer(video.dur)
    m.add(river_sound(video.dur), 0, 0.14)
    hook_speed = lambda t: TRUCK.speed(t + T_HOOK) if t < HOOK else TRUCK.speed(t)
    m.add(diesel(video.dur, hook_speed), 0, 0.17)
    m.add(heartbeat(3, 110), 0.1, 1.4)
    m.add(riser(2.6), 0.2, 0.9)
    m.add(creak(1.4), 0.6, 0.6)
    m.add(impact(), HOOK, 0.6)
    m.add(whoosh(0.6, 0.4), HOOK - 0.15, 0.7)
    m.add(air_brake(), T_STOP - 0.2, 0.9, 0.3)
    m.add(click(), T_STOP - 2.0, 1.0)
    indicator(m, T_STOP - 2.0, T_GO + 6.0, 1.0, 0.2)
    m.add(car_pass(2.4, 0.5, 105), CAR.m.g[np.argmin(np.abs(np.array([CAR.pose(g)[0] for g in CAR.m.g]) - 18))] - 1.2, 1.0,
          np.linspace(-0.6, 0.6, int(2.4 * SR)))
    # deck joint thumps: every 5 m an axle crosses a joint while on the bridge
    for axle_lz in (4.0, 0.0, -1.32):
        for zj in np.arange(0, 41, 5):
            for i in range(I_ON, min(I_OFF + 200, len(LOGP) - 1)):
                t_, x, z, h1, h2, v, d = LOGP[i]
                if abs(z + axle_lz - zj) < 0.03:
                    m.add(deck_thump(), GT[i], 1.1)
                    break
    for i in range(2, 11):
        m.add(pop(), S[i] + 0.15, 0.7)
    m.add(head_swish(), S[6] + 0.05, 0.9, -0.5)
    m.add(head_swish(), S[7] + 0.05, 0.9, 0.5)
    m.add(chime(), T_OFF, 0.8)
    m.add(success_jingle(), S[10] + 0.2, 1.0)
    m.add(pop(), S[10] + 1.0, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'bridge.mp4')
