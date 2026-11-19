"""Toronto highway-merge world in the flat 2D cartoon style, viewable from any camera:
inside the car, game-style chase cam, outside side mirror, over-the-shoulder, and top (map) view.

World axes (metres): +Z = direction of travel (east on the Gardiner), +X = right (south, toward the lake),
+Y = up. Through lanes: left -3.6..0, right 0..3.6; acceleration lane 3.6..7.2 from Z=0 to Z=400, taper to 460.
The on-ramp curves in from the right and joins the acceleration lane at Z=0.
"""
import math
import random

import cairo
import numpy as np

from kit import *
import kit
import engine

NEAR = 0.25
ACC0, ACC1, TAPER = 0.0, 400.0, 460.0
LANE_L, LANE_R, LANE_ACC = -1.8, 1.8, 5.4

C_GRASS = hexc('#86c46a')
C_ASPH = hexc('#5b5f6c')
C_SHOULDER = hexc('#7a7d88')
C_LINE = (0.97, 0.97, 0.97)
C_YEL = hexc('#f2c230')
C_WATER = hexc('#4f9fd6')
C_WALL = hexc('#c9c9c2')
C_EGO = '#e23b3b'


def ramp_x(z):
    return LANE_ACC + 0.004 * z * z if z < 0 else LANE_ACC


# ------------------------------------------------------------------ cameras
class TCam:
    """Perspective camera: position, yaw (0 = looking +Z, positive turns right), pitch (+ = down)."""
    ortho = False

    def __init__(self, pos, yaw, pitch=0.0, f=1000, cx=960, cy=540, mirror=False):
        self.pos = pos
        self.yaw, self.pitch, self.f, self.cx, self.cy = yaw, pitch, f, cx, cy
        self.cy_, self.sy_ = math.cos(yaw), math.sin(yaw)
        self.cp, self.sp = math.cos(pitch), math.sin(pitch)
        self.mirror = mirror

    def to_cam(self, P):
        dx, dy, dz = P[0] - self.pos[0], P[1] - self.pos[1], P[2] - self.pos[2]
        x1 = dx * self.cy_ - dz * self.sy_
        z1 = dx * self.sy_ + dz * self.cy_
        y2 = dy * self.cp + z1 * self.sp
        z2 = z1 * self.cp - dy * self.sp
        return (x1, y2, z2)

    def _scr(self, c):
        x = c[0] * self.f / c[2]
        if self.mirror:
            x = -x
        return (self.cx + x, self.cy - c[1] * self.f / c[2])

    def pt(self, P):
        c = self.to_cam(P)
        if c[2] < NEAR:
            return None
        return self._scr(c)

    def depth(self, P):
        return self.to_cam(P)[2]

    def scale(self, P):
        z = self.to_cam(P)[2]
        return self.f / z if z > NEAR else None

    def poly(self, pts):
        cs = [self.to_cam(p) for p in pts]
        out = []
        n = len(cs)
        for i in range(n):
            a, b = cs[i], cs[(i + 1) % n]
            ain, bin_ = a[2] >= NEAR, b[2] >= NEAR
            if ain:
                out.append(a)
            if ain != bin_:
                u = (NEAR - a[2]) / (b[2] - a[2])
                out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, NEAR))
        if len(out) < 3:
            return None
        return [self._scr(c) for c in out]

    def horizon(self):
        return self.cy - self.f * math.tan(self.pitch)


class TopView:
    """Orthographic map view: travel direction points right, +X (right of car) points down."""
    ortho = True

    def __init__(self, ez, xc=2.0, s=16.0, ox=760, oy=540):
        self.ez, self.xc, self.s, self.ox, self.oy = ez, xc, s, ox, oy
        self.pos = (0, 1000, 0)

    def pt(self, P):
        return (self.ox + (P[2] - self.ez) * self.s, self.oy + (P[0] - self.xc) * self.s)

    def poly(self, pts):
        return [self.pt(p) for p in pts]

    def depth(self, P):
        return 0.0


def fill_poly(ctx, view, pts, col, stroke=None, lw=3, alpha=1.0):
    sp = view.poly(pts)
    if not sp:
        return False
    poly(ctx, sp)
    if stroke is None:
        setc(ctx, col, alpha)
        ctx.fill()
    else:
        fill_stroke(ctx, col, stroke, lw, alpha)
    return True


def gquad(ctx, view, x0, x1, z0, z1, col, y=0.0):
    fill_poly(ctx, view, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], col)


# ------------------------------------------------------------------ world
class TorWorld:
    def __init__(self, dur, speed, z0, lat, blink_left, traffic, shake=None):
        self.dur, self.speed, self.lat = dur, speed, lat
        self.blink_left = blink_left
        self.blink_right = lambda t: 0.0
        self.headlights = const(0)
        self.ego_brake = const(0)
        self.shake = shake or const(0)
        self.traffic = traffic
        self._g = np.arange(0, dur + 2, 1 / 120)
        v = np.array([speed(t) for t in self._g])
        self._z = z0 + np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 / 120)])

    def blink_on(self, t):
        return self.blink_left(t) > 0.5

    def ego_z(self, t):
        return float(np.interp(t, self._g, self._z))

    def ego_xz(self, t):
        z = self.ego_z(t)
        x = ramp_x(z) if z < ACC0 else LANE_ACC + self.lat(t)
        return x, z

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
        """[(x, z, heading, color, blinkL, brake)] for all traffic (not the ego car)."""
        ez = self.ego_z(t)
        out = []
        for c in self.traffic:
            if c.get('oncoming'):
                z = c['z0'] - 25 * t
                out.append((c['x'], z, math.pi, c['col'], False, 0))
            else:
                out.append((c['x'], ez + c['rel'](t), 0.0, c['col'], False, 0))
        return out


# ------------------------------------------------------------------ objects
def L(x, z, h):
    ch, sh = math.cos(h), math.sin(h)
    return lambda lx, ly, lz: (x + lx * ch + lz * sh, ly, z - lx * sh + lz * ch)


def lbox(ctx, view, Lf, h, x0, x1, y0, y1, z0, z1, cols, lw=3):
    """Box in car-local coordinates; cols: dict face->colour (front/back/left/right/top)."""
    cam = view.pos
    ch, sh = math.cos(h), math.sin(h)
    faces = {
        'front': ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (sh, 0, ch)),
        'back': ([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], (-sh, 0, -ch)),
        'right': ([(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], (ch, 0, -sh)),
        'left': ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-ch, 0, sh)),
        'top': ([(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], (0, 1, 0)),
    }
    drawn = []
    for name, (pts, n) in faces.items():
        if name not in cols:
            continue
        wp = [Lf(*p) for p in pts]
        c = [sum(p[i] for p in wp) / 4 for i in range(3)]
        if (cam[0] - c[0]) * n[0] + (cam[1] - c[1]) * n[1] + (cam[2] - c[2]) * n[2] <= 0:
            continue
        if fill_poly(ctx, view, wp, cols[name], OUTL, lw):
            drawn.append(name)
    return drawn


def face_rect(ctx, view, Lf, face, a0, a1, b0, b1, d, col, glow_col=None, glow_r=0.0):
    """Rectangle decal on a box face. back/front: (a=x, b=y) at z=d ; left/right: (a=z, b=y) at x=d."""
    if face in ('back', 'front'):
        pts = [(a0, b0, d), (a1, b0, d), (a1, b1, d), (a0, b1, d)]
    else:
        pts = [(d, b0, a0), (d, b0, a1), (d, b1, a1), (d, b1, a0)]
    wp = [Lf(*p) for p in pts]
    if fill_poly(ctx, view, wp, col) and glow_col is not None and not view.ortho:
        c = [sum(p[i] for p in wp) / 4 for i in range(3)]
        p, s = view.pt(c), view.scale(c)
        if p and s:
            glow(ctx, p[0], p[1], min(glow_r * s, 260), glow_col, 0.7)


def draw_car3(ctx, view, x, z, h, col, t, blinkL=False, brake=0.0, lw=None):
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
    blink_on = bool(blinkL)
    if 'back' in vis:
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'back', s * 0.62 - 0.2, s * 0.62 + 0.2, 0.62, 0.78, -2.21,
                      hexc('#ff4040') if brake > 0.5 else hexc('#b01818'), RED if brake > 0.5 else None, 1.2)
        face_rect(ctx, view, Lf, 'back', -0.25, 0.25, 0.42, 0.56, -2.21, hexc('#e8e8ee'))
        face_rect(ctx, view, Lf, 'back', -0.9, -0.66, 0.6, 0.8, -2.22,
                  AMBER if blink_on else hexc('#7a4a00'), AMBER if blink_on else None, 1.6)
    if 'front' in vis:
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'front', s * 0.6 - 0.22, s * 0.6 + 0.22, 0.6, 0.76, 2.21, hexc('#fff6d8'))
        face_rect(ctx, view, Lf, 'front', -0.9, -0.7, 0.6, 0.76, 2.22,
                  AMBER if blink_on else hexc('#7a4a00'), AMBER if blink_on else None, 1.2)
    if 'left' in vis:
        face_rect(ctx, view, Lf, 'left', 1.2, 1.5, 0.6, 0.72, -0.93,
                  AMBER if blink_on else hexc('#7a4a00'), AMBER if blink_on else None, 1.0)


def draw_car_top(ctx, view, x, z, h, col, t, blinkL=False, ego=False):
    cx, cy = view.pt((x, 0, z))
    s = view.s
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(-h)          # heading 0 = pointing right
    Lr, Wr = 4.4 * s, 1.84 * s
    if ego:
        glow(ctx, 0, 0, 3.6 * s, hexc('#ffffff'), 0.35)
    ctx.save()
    ctx.translate(3, 5)
    rrect(ctx, -Lr / 2, -Wr / 2, Lr, Wr, Wr * 0.35)
    setc(ctx, (0, 0, 0), 0.25)
    ctx.fill()
    ctx.restore()
    rrect(ctx, -Lr / 2, -Wr / 2, Lr, Wr, Wr * 0.35)
    fill_stroke(ctx, hexc(col), OUTL, 4)
    poly(ctx, [(Lr * 0.12, -Wr * 0.4), (Lr * 0.3, -Wr * 0.34), (Lr * 0.3, Wr * 0.34), (Lr * 0.12, Wr * 0.4)])
    setc(ctx, hexc('#2a3448'))
    ctx.fill()
    poly(ctx, [(-Lr * 0.3, -Wr * 0.38), (-Lr * 0.2, -Wr * 0.36), (-Lr * 0.2, Wr * 0.36), (-Lr * 0.3, Wr * 0.38)])
    ctx.fill()
    rrect(ctx, -Lr * 0.2, -Wr * 0.36, Lr * 0.32, Wr * 0.72, 6)
    setc(ctx, mix(hexc(col), (1, 1, 1), 0.18))
    ctx.fill()
    if blinkL:
        for px in (Lr * 0.46, -Lr * 0.46):
            ellipse(ctx, px, -Wr * 0.42, 0.3 * s, 0.3 * s)
            setc(ctx, AMBER)
            ctx.fill()
            glow(ctx, px, -Wr * 0.42, 1.6 * s, AMBER, 0.8)
    ctx.restore()


def tree3(ctx, view, x, z, s=1.0, seed=0):
    cols = [hexc('#3f9a4c'), hexc('#58b05a'), hexc('#2f8a45')]
    if view.ortho:
        p = view.pt((x, 0, z))
        r = 2.2 * s * view.s
        ellipse(ctx, p[0] + 4, p[1] + 6, r, r)
        setc(ctx, (0, 0, 0), 0.2)
        ctx.fill()
        ellipse(ctx, p[0], p[1], r, r)
        fill_stroke(ctx, cols[seed % 3], OUTL, 3)
        ellipse(ctx, p[0] - r * 0.3, p[1] - r * 0.3, r * 0.4, r * 0.4)
        setc(ctx, (1, 1, 1), 0.15)
        ctx.fill()
        return
    b, tp = view.pt((x, 0, z)), view.pt((x, 3.4 * s, z))
    sc = view.scale((x, 0, z))
    if not b or not tp or not sc:
        return
    w = 0.35 * sc
    ctx.rectangle(b[0] - w / 2, tp[1], w, b[1] - tp[1])
    fill_stroke(ctx, hexc('#7b5434'), OUTL, max(1, min(4, sc / 30)))
    r = 2.0 * s * sc
    for i, (dx, dy) in enumerate(((-0.45, 0.1), (0.45, 0.15), (0, -0.4))):
        ellipse(ctx, tp[0] + dx * r, tp[1] + dy * r, r * 0.75, r * 0.7)
        fill_stroke(ctx, cols[(seed + i) % 3], OUTL, max(1, min(4, sc / 30)))


def condo(ctx, view, x0, x1, z0, z1, hgt, col, seed):
    c = hexc(col)
    cols = {'front': c, 'back': c, 'left': mix(c, (0, 0, 0), 0.15), 'right': mix(c, (0, 0, 0), 0.08),
            'top': mix(c, (1, 1, 1), 0.2)}
    if view.ortho:
        fill_poly(ctx, view, [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)], cols['top'], OUTL, 3)
        return
    Lf = lambda a, b, cc: (a, b, cc)
    vis = lbox(ctx, view, Lf, 0.0, x0, x1, 0, hgt, z0, z1, cols, 2)
    # floor lines on visible faces
    for y in np.arange(4, hgt, 4.5):
        for face in vis:
            if face == 'right':
                seg = [(x1 + 0.05, y, z0 + 1), (x1 + 0.05, y, z1 - 1)]
            elif face == 'back':
                seg = [(x0 + 1, y, z0 - 0.05), (x1 - 1, y, z0 - 0.05)]
            else:
                continue
            a, b = view.pt(seg[0]), view.pt(seg[1])
            if a and b:
                ctx.move_to(*a)
                ctx.line_to(*b)
    setc(ctx, hexc('#2f5f80'), 0.5)
    ctx.set_line_width(2)
    ctx.stroke()


def skyline(ctx, view):
    """Downtown Toronto skyline with the CN Tower, far ahead on the left."""
    if view.ortho:
        return
    haze = hexc('#b9d6ea')
    rnd = random.Random(12)
    blds = []
    for i in range(26):
        X = -760 + i * 45 + rnd.uniform(-10, 10)
        if abs(X + 120) < 45:
            continue
        blds.append((X, 1700 + rnd.uniform(-100, 100), rnd.uniform(30, 55), rnd.uniform(60, 220)))
    blds.sort(key=lambda b: -b[1])
    for X, Z, w, hgt in blds:
        b, tp = view.pt((X, 0, Z)), view.pt((X, hgt, Z))
        sc = view.scale((X, 0, Z))
        if not b or not tp:
            continue
        ww = w * sc
        ctx.rectangle(b[0] - ww / 2, tp[1], ww, b[1] - tp[1])
        setc(ctx, mix(hexc('#7d9bb5'), haze, 0.35 + 0.3 * rnd.random()))
        ctx.fill()
    # CN Tower
    X, Z = -120.0, 1450.0
    b = view.pt((X, 0, Z))
    sc = view.scale((X, 0, Z))
    if not b or not sc:
        return
    col, col2 = mix(hexc('#9aa6b8'), haze, 0.25), mix(hexc('#6f7c90'), haze, 0.2)
    bx, by = b

    def Y(m):
        return by - m * sc
    poly(ctx, [(bx - 34 * sc, by), (bx + 34 * sc, by), (bx + 8 * sc, Y(330)), (bx - 8 * sc, Y(330))])
    setc(ctx, col)
    ctx.fill()
    poly(ctx, [(bx - 8 * sc, Y(330)), (bx + 8 * sc, Y(330)), (bx + 6 * sc, Y(450)), (bx - 6 * sc, Y(450))])
    ctx.fill()
    # main pod
    poly(ctx, [(bx - 12 * sc, Y(322)), (bx + 12 * sc, Y(322)), (bx + 40 * sc, Y(342)), (bx + 40 * sc, Y(352)),
               (bx + 20 * sc, Y(370)), (bx - 20 * sc, Y(370)), (bx - 40 * sc, Y(352)), (bx - 40 * sc, Y(342))])
    setc(ctx, col2)
    ctx.fill()
    ctx.rectangle(bx - 40 * sc, Y(352), 80 * sc, 6 * sc)
    setc(ctx, mix(hexc('#2f4a66'), haze, 0.2))
    ctx.fill()
    # sky pod + antenna
    ctx.rectangle(bx - 9 * sc, Y(455), 18 * sc, 12 * sc)
    setc(ctx, col2)
    ctx.fill()
    poly(ctx, [(bx - 3.5 * sc, Y(455)), (bx + 3.5 * sc, Y(455)), (bx + 1 * sc, Y(553)), (bx - 1 * sc, Y(553))])
    setc(ctx, col)
    ctx.fill()


# ------------------------------------------------------------------ world render
TREES = []
_r = random.Random(3)
for zz in np.arange(-300, 1400, 14):
    TREES.append((-18 - _r.uniform(0, 6), zz + _r.uniform(-4, 4), 0.9 + _r.uniform(0, 0.5)))
    if zz > TAPER + 10 or zz < -170:
        TREES.append((12 + _r.uniform(0, 8), zz + _r.uniform(-4, 4), 0.9 + _r.uniform(0, 0.5)))
    elif zz > 10:
        TREES.append((13 + _r.uniform(0, 8), zz + _r.uniform(-4, 4), 0.9 + _r.uniform(0, 0.5)))
for zz in np.arange(-160, -20, 12):          # gore area between ramp and highway
    xr = ramp_x(zz)
    if xr > 13:
        TREES.append(((3.6 + xr - 2.2) / 2 + _r.uniform(-1, 1), zz, 0.8 + _r.uniform(0, 0.4)))
    TREES.append((xr + 7 + _r.uniform(0, 5), zz, 0.9 + _r.uniform(0, 0.5)))
CONDOS = []
for i, zz in enumerate(np.arange(-200, 1500, 75)):
    CONDOS.append((-75 - (i % 3) * 18, -50 - (i % 3) * 18, zz, zz + 28, 35 + (i * 37) % 70,
                   ['#a9cfe0', '#c7d3dc', '#9cc0d6', '#d8d2c4'][i % 4], i))


def ramp_strip(z0=-170, z1=4, step=2.0):
    zs = np.arange(z0, z1 + 0.01, step)
    return [(ramp_x(z), z) for z in zs]


RAMP = ramp_strip()


def offset_strip(pts, off):
    out = []
    for i, (x, z) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dz) or 1
        out.append((x + dz / n * off, z - dx / n * off))
    return out


def ribbon3(ctx, view, pts, w, col, y=0.0, off=0.0, step=1):
    left, right = offset_strip(pts, off - w / 2), offset_strip(pts, off + w / 2)
    for i in range(0, len(pts) - 1, step):
        j = min(i + step, len(pts) - 1)
        fill_poly(ctx, view, [(left[i][0], y, left[i][1]), (right[i][0], y, right[i][1]),
                              (right[j][0], y, right[j][1]), (left[j][0], y, left[j][1])], col)


def draw_world(ctx, view, world, t, ego=True, gap=None):
    ez = world.ego_z(t)
    zlo, zhi = ez - 220, ez + 900
    # sky + ground
    if view.ortho:
        setc(ctx, C_GRASS)
        ctx.paint()
    else:
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 700, 0, hy)
        g.add_color_stop_rgb(0, *hexc('#5fb4f2'))
        g.add_color_stop_rgb(1, *hexc('#d6f0ff'))
        ctx.set_source(g)
        ctx.rectangle(-50, -50, SW + 100, hy + 52)
        ctx.fill()
        for cx0, cy0, sc0 in ((260, 120, 1.0), (980, 70, 0.8), (1560, 160, 1.1)):
            for dx, dy, r in ((0, 0, 60), (60, -25, 70), (130, 0, 55), (60, 15, 60)):
                ellipse(ctx, cx0 + dx * sc0, hy - 520 + cy0 + dy * sc0, r * sc0, r * sc0 * 0.8)
            setc(ctx, (1, 1, 1), 0.9)
            ctx.fill()
        setc(ctx, C_GRASS)
        ctx.rectangle(-50, hy, SW + 100, SH + 100 - hy)
        ctx.fill()
        # lake on the right (south)
        fill_poly(ctx, view, [(60, 0, zlo - 2000), (4000, 0, zlo - 2000), (4000, 0, zhi + 3000), (60, 0, zhi + 3000)], C_WATER)
        skyline(ctx, view)
    if view.ortho:
        fill_poly(ctx, view, [(60, 0, zlo), (400, 0, zlo), (400, 0, zhi), (60, 0, zhi)], C_WATER)
    # opposite carriageway (westbound) beyond the median
    gquad(ctx, view, -13.2, -5.2, zlo, zhi, C_ASPH)
    for k in range(int(zlo // 12), int(zhi // 12) + 1):
        gquad(ctx, view, -8.9, -8.75, k * 12, k * 12 + 4, C_LINE, 0.01)
    # our carriageway
    gquad(ctx, view, -4.5, 3.6, zlo, zhi, C_ASPH)
    gquad(ctx, view, 3.6, 4.6, zlo, ACC0, C_SHOULDER)
    gquad(ctx, view, 3.6, 4.6, TAPER, zhi, C_SHOULDER)
    gquad(ctx, view, 3.6, 7.2, ACC0, ACC1, C_ASPH)
    fill_poly(ctx, view, [(3.6, 0, ACC1), (7.2, 0, ACC1), (3.6, 0, TAPER)], C_ASPH)
    ribbon3(ctx, view, RAMP, 4.4, C_ASPH)
    # markings
    for k in range(int(zlo // 12), int(zhi // 12) + 1):
        gquad(ctx, view, -0.08, 0.08, k * 12, k * 12 + 4, C_LINE, 0.01)
    gquad(ctx, view, -3.75, -3.6, zlo, zhi, C_YEL, 0.01)
    gquad(ctx, view, 3.5, 3.7, zlo, ACC0, C_LINE, 0.01)
    gquad(ctx, view, 3.5, 3.7, TAPER, zhi, C_LINE, 0.01)
    for k in range(int(ACC0 // 4), int(TAPER // 4)):
        gquad(ctx, view, 3.45, 3.75, k * 4, k * 4 + 2, C_LINE, 0.01)
    gquad(ctx, view, 7.1, 7.25, ACC0, ACC1, C_LINE, 0.01)
    fill_poly(ctx, view, [(7.1, 0.01, ACC1), (7.25, 0.01, ACC1), (3.75, 0.01, TAPER), (3.6, 0.01, TAPER)], C_LINE)
    ribbon3(ctx, view, RAMP, 0.16, C_LINE, 0.01, -2.05)
    ribbon3(ctx, view, RAMP, 0.16, C_LINE, 0.01, 2.05)
    if gap is not None:
        z0g, z1g, a = gap
        pulse = 0.35 + 0.15 * math.sin(t * 6)
        fill_poly(ctx, view, [(0.3, 0.02, z0g), (3.3, 0.02, z0g), (3.3, 0.02, z1g), (0.3, 0.02, z1g)],
                  hexc('#22c35e'), hexc('#ffffff'), 5, pulse * a + 0.2 * a)
    # far side (behind the median from our point of view) first
    objs_far, objs = [], []
    for x, z, s in TREES:
        if zlo < z < zhi:
            (objs_far if x < -5 else objs).append((z, x, lambda x=x, z=z, s=s: tree3(ctx, view, x, z, s, int(z) % 3)))
    for x0, x1, z0, z1, hgt, col, i in CONDOS:
        if z1 > zlo and z0 < zhi + 300:
            objs_far.append((z0, x0, lambda a=(x0, x1, z0, z1, hgt, col, i): condo(ctx, view, *a)))
    cars = world.cars(t)
    for x, z, h, col, bl, br in cars:
        if zlo < z < zhi:
            if view.ortho:
                fn = lambda x=x, z=z, h=h, col=col: draw_car_top(ctx, view, x, z, h, col, t)
            else:
                fn = lambda x=x, z=z, h=h, col=col, br=br: draw_car3(ctx, view, x, z, h, col, t, False, br)
            (objs_far if x < -5 else objs).append((z, x, fn))
    if ego:
        ex, ezz = world.ego_xz(t)
        h = world.heading(t)
        blinking_ = world.blink_on(t)
        if view.ortho:
            objs.append((ezz, ex, lambda: draw_car_top(ctx, view, ex, ezz, h, C_EGO, t, blinking_, True)))
        else:
            objs.append((ezz, ex, lambda: draw_car3(ctx, view, ex, ezz, h, C_EGO, t, blinking_)))

    def depth_key(o):
        return -view.depth((o[1], 1.0, o[0])) if not view.ortho else 0
    for o in sorted(objs_far, key=depth_key):
        o[2]()
    # median wall
    if view.ortho:
        gquad(ctx, view, -5.0, -4.6, zlo, zhi, C_WALL)
    else:
        fill_poly(ctx, view, [(-4.6, 0, zlo), (-4.6, 0, zhi), (-4.6, 1.0, zhi), (-4.6, 1.0, zlo)], mix(C_WALL, (0, 0, 0), 0.1))
        fill_poly(ctx, view, [(-5.0, 1.0, zlo), (-4.6, 1.0, zlo), (-4.6, 1.0, zhi), (-5.0, 1.0, zhi)], C_WALL)
    # overhead sign gantry
    objs.append((150.0, 0.0, lambda: gantry(ctx, view)))
    objs.append((-40.0, 9.0, lambda: merge_sign(ctx, view)))
    for o in sorted(objs, key=depth_key):
        o[2]()
    if not view.ortho:
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 30, 0, hy + 140)
        g.add_color_stop_rgba(0, 0.84, 0.94, 1, 0.0)
        g.add_color_stop_rgba(0.25, 0.84, 0.94, 1, 0.45)
        g.add_color_stop_rgba(1, 0.84, 0.94, 1, 0.0)
        ctx.set_source(g)
        ctx.rectangle(-50, hy - 30, SW + 100, 170)
        ctx.fill()


def gantry(ctx, view):
    z = 150.0
    if view.ortho:
        gquad(ctx, view, -5.0, 8.0, z - 0.4, z + 0.4, hexc('#6a6f7c'))
        return
    for px in (-5.2, 8.0):
        fill_poly(ctx, view, [(px - 0.25, 0, z), (px + 0.25, 0, z), (px + 0.25, 7.6, z), (px - 0.25, 7.6, z)],
                  hexc('#8a8f9c'), OUTL, 2)
    fill_poly(ctx, view, [(-5.2, 7.2, z), (8.0, 7.2, z), (8.0, 7.6, z), (-5.2, 7.6, z)], hexc('#8a8f9c'), OUTL, 2)
    pts = [(-3.4, 4.9, z - 0.05), (3.4, 4.9, z - 0.05), (3.4, 7.3, z - 0.05), (-3.4, 7.3, z - 0.05)]
    sp = view.poly(pts)
    if sp:
        poly(ctx, sp)
        fill_stroke(ctx, hexc('#1f7a43'), (1, 1, 1), 3)
        c, s = view.pt((0, 6.1, z)), view.scale((0, 6.1, z))
        if c and s and s > 8:
            text_center(ctx, 'Gardiner Expy  EAST', c[0], c[1] - 0.15 * s, 0.62 * s, (1, 1, 1))
            text_center(ctx, 'Downtown Toronto', c[0], c[1] + 0.75 * s, 0.55 * s, (1, 1, 1))


def merge_sign(ctx, view):
    """Yellow diamond 'merge' warning sign beside the ramp."""
    z = -40.0
    x = ramp_x(z) + 3.4
    if view.ortho:
        return
    b, tp = view.pt((x, 0, z)), view.pt((x, 2.6, z))
    s = view.scale((x, 2.6, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.06 * s, tp[1], 0.12 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#8a8f9c'), OUTL, 2)
    r = 0.6 * s
    cx_, cy_ = tp[0], tp[1] - r
    poly(ctx, [(cx_, cy_ - r), (cx_ + r, cy_), (cx_, cy_ + r), (cx_ - r, cy_)])
    fill_stroke(ctx, hexc('#f2c230'), OUTL, max(2, s / 25))
    ctx.move_to(cx_ - r * 0.1, cy_ + r * 0.6)
    ctx.line_to(cx_ - r * 0.1, cy_ - r * 0.55)
    ctx.move_to(cx_ + r * 0.35, cy_ + r * 0.6)
    ctx.curve_to(cx_ + r * 0.35, cy_ + r * 0.1, cx_ - r * 0.05, cy_ - r * 0.05, cx_ - r * 0.05, cy_ - r * 0.25)
    setc(ctx, OUTL)
    ctx.set_line_width(max(2, r * 0.13))
    ctx.stroke()


# ------------------------------------------------------------------ scenes
def ego_cam(world, t, mode):
    ex, ez = world.ego_xz(t)
    h = world.heading(t)
    sh = world.shake(t)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    if mode == 'chase':
        return TCam((ex - fx * 10.5, 3.6, ez - fz * 10.5), h, 0.16, 1000, cy=520)
    if mode == 'close':
        return TCam((ex - fx * 5.6 - rx * 1.2, 1.7, ez - fz * 5.6 - rz * 1.2), h + 0.12, 0.08, 1000)
    if mode == 'wide':
        return TCam((ex - fx * 17 + rx * 4, 7.5, ez - fz * 17 + rz * 4), h - 0.12, 0.2, 1000, cy=500)
    if mode == 'inside':
        return TCam((ex - rx * 0.38 - fx * 0.2, 1.18, ez - rz * 0.38 - fz * 0.2), h, 0.02, 1000, cy=470)
    raise ValueError(mode)


def hud_speed(ctx, world, t):
    kmh = world.speed(t) * 3.6
    rrect(ctx, 1560, 900, 310, 130, 34)
    setc(ctx, (0, 0, 0), 0.5)
    ctx.fill()
    text_center(ctx, f"{int(round(kmh))}", 1675, 990, 84, (1, 1, 1))
    text_center(ctx, 'km/h', 1800, 990, 34, (0.85, 0.85, 0.9))


def tor_chase(ctx, world, t, lt, kw):
    cam = ego_cam(world, t, kw.get('cam', 'chase'))
    draw_world(ctx, cam, world, t)
    if kw.get('hud', True):
        hud_speed(ctx, world, t)


def tor_inside(ctx, world, t, lt, kw):
    cam = ego_cam(world, t, 'inside')
    draw_world(ctx, cam, world, t, ego=False)
    kit.cockpit_day_nomirror(ctx, world, t, cam)
    if world.blink_on(t):
        glow(ctx, 870, 880, 70, hexc('#2bff6a'), 0.5)
        pts = [(840, 880), (880, 852), (880, 868), (910, 868), (910, 892), (880, 892), (880, 908)]
        poly(ctx, pts)
        setc(ctx, hexc('#2bff6a'))
        ctx.fill()


def tor_top(ctx, world, t, lt, kw):
    view = TopView(world.ego_z(t), xc=kw.get('xc', 1.0), s=kw.get('scale', 15.0))
    gap = None
    if kw.get('gap'):
        a = smooth(lt / 0.4)
        cars = world.cars(t)
        za = [z for x, z, h, c, b, r in cars if abs(x - LANE_R) < 0.5]
        ez = world.ego_z(t)
        ahead = min([z for z in za if z > ez - 2] or [ez + 30])
        behind = max([z for z in za if z < ez - 2] or [ez - 30])
        gap = (behind + 3.0, ahead - 3.0, a)
    draw_world(ctx, view, world, t, gap=gap)
    if gap:
        c = view.pt((LANE_R, 0, (gap[0] + gap[1]) / 2))
        text_center(ctx, 'GAP', c[0], c[1] + 18, 52, (1, 1, 1), a=gap[2])
        ex, ez = world.ego_xz(t)
        p0 = view.pt((ex - 0.4, 0, ez + 2.6))
        p1 = view.pt((LANE_R + 0.3, 0, (gap[0] + gap[1]) / 2 + 4))
        ctx.move_to(*p0)
        ctx.curve_to(p0[0] + 120, p0[1], p1[0] - 160, p1[1], p1[0], p1[1])
        ctx.set_dash([18, 14], -t * 60)
        setc(ctx, (1, 1, 1), gap[2])
        ctx.set_line_width(8)
        ctx.stroke()
        ctx.set_dash([])
        poly(ctx, [(p1[0] + 26, p1[1]), (p1[0] - 6, p1[1] - 18), (p1[0] - 6, p1[1] + 18)])
        setc(ctx, (1, 1, 1), gap[2])
        ctx.fill()


def tor_mirror(ctx, world, t, lt, kw):
    """Close-up of the LEFT outside mirror (seen from the driver's seat through the side window)."""
    ex, ez = world.ego_xz(t)
    h = world.heading(t)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    # blurred side-window background: looking left-forward
    bg = TCam((ex - rx * 0.4, 1.2, ez - rz * 0.4), h - 0.75, 0.05, 700)
    draw_world(ctx, bg, world, t, ego=False)
    setc(ctx, (0.05, 0.08, 0.15), 0.25)
    ctx.paint()
    # door + window frame on the right
    poly(ctx, [(1700, -10), (SW + 10, -10), (SW + 10, SH + 10), (1450, SH + 10), (1640, 600)])
    fill_stroke(ctx, hexc('#b92f2f'), OUTL, 6)
    poly(ctx, [(1640, 600), (1450, SH + 10), (1380, SH + 10), (1590, 560)])
    fill_stroke(ctx, hexc('#2a2a36'), OUTL, 4)
    mx, my, rot = 930, 520, -0.06
    ctx.save()
    ctx.translate(mx, my)
    ctx.rotate(rot)
    rrect(ctx, -560, -330, 1120, 660, 300)
    fill_stroke(ctx, hexc('#c23535'), OUTL, 7)
    rrect(ctx, -520, -290, 1040, 580, 260)
    fill_stroke(ctx, hexc('#0b1424'), OUTL, 5)
    ctx.restore()
    ctx.save()
    ctx.save()
    ctx.translate(mx, my)
    ctx.rotate(rot)
    rrect(ctx, -500, -270, 1000, 540, 240)
    ctx.restore()
    ctx.clip()
    mcam = TCam((ex - rx * 1.05 + fx * 0.6, 1.05, ez - rz * 1.05 + fz * 0.6), h + math.pi + 0.22, 0.04, 900,
                cx=mx + 120, cy=my - 40, mirror=True)
    draw_world(ctx, mcam, world, t, ego=False)
    poly(ctx, [(mx + 330, my - 40), (mx + 520, my - 90), (mx + 520, my + 300), (mx + 260, my + 300)])
    fill_stroke(ctx, hexc(C_EGO), OUTL, 5)
    g = cairo.LinearGradient(mx - 500, my - 270, mx + 100, my + 270)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.12)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    if world.blink_on(t):
        bx, by = mx - 430, my + 250
        rrect(ctx, bx - 70, by - 18, 140, 36, 18)
        setc(ctx, AMBER)
        ctx.fill()
        glow(ctx, bx, by, 200, AMBER, 0.7)


def tor_shoulder(ctx, world, t, lt, kw):
    """Over-the-left-shoulder look through the rear side window."""
    ex, ez = world.ego_xz(t)
    h = world.heading(t)
    rx, rz = math.cos(h), -math.sin(h)
    look = key_or(kw, 'look', lt, 1.0)
    cam = TCam((ex - rx * 0.35, 1.2, ez - rz * 0.35), h - 2.1 * look, 0.03, 800, cx=900)
    draw_world(ctx, cam, world, t, ego=False)
    # interior frame: roof, B-pillar, rear seat headrest, door line, driver's shoulder
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


engine.SCENES.update(tor_chase=tor_chase, tor_inside=tor_inside, tor_top=tor_top, tor_mirror=tor_mirror,
                     tor_shoulder=tor_shoulder)


def location_tag(text='Toronto, ON'):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.3) * smooth((d - lt) / 0.3)
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(54)
        w = ctx.text_extents(text).x_advance
        rrect(ctx, 50, 50, w + 140, 96, 48)
        setc(ctx, (0, 0, 0), 0.55 * a)
        ctx.fill()
        px, py = 105, 92
        ctx.move_to(px, py + 32)
        ctx.curve_to(px - 30, py, px - 26, py - 30, px, py - 30)
        ctx.curve_to(px + 26, py - 30, px + 30, py, px, py + 32)
        setc(ctx, hexc('#ff4b4b'), a)
        ctx.fill()
        ellipse(ctx, px, py - 8, 9, 9)
        setc(ctx, (1, 1, 1), a)
        ctx.fill()
        ctx.move_to(150, 117)
        setc(ctx, (1, 1, 1), a)
        ctx.show_text(text)
    return fn


def step_badge(n):
    return badge(f'STEP {n}', '#22a356')
