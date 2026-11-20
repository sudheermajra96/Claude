"""Shared toolkit for city-street episodes in the 2D+3D house style.

Coordinates: +X east, +Z north, Y up. Heading h: 0 = north (+Z), +pi/2 = east. forward=(sin h, cos h),
right=(cos h, -sin h). Cars drive on the right (North America).

  Path / Mover      cars following lines, arcs and splines with a speed profile (anchored in time)
  Kinematic         bicycle-model car (steering + speed keys) for parking manoeuvres
  CityWorld         ego + other agents + pedestrians + a static "city" (ground, objects, skyline)
  draw_scene        renders everything for any camera (TCam perspective or TopN map view)
  scenes            c_cam (chase/close/high/fixed), c_inside, c_top, c_rear (reversing camera), c_shoulder
"""
import math
import random

import cairo
import numpy as np

from toronto import TCam, fill_poly, gquad, lbox, L, face_rect, tree3, location_tag, step_badge
from kit import *
import engine
import euro

C_ASPH = hexc('#5b5f6c')
C_WALK = hexc('#cfc8bb')
C_GRASS = hexc('#86c46a')
C_LINE = (0.97, 0.97, 0.97)
C_YEL = hexc('#f2c230')
C_EGO = '#e23b3b'


# ------------------------------------------------------------------ geometry
def catmull(pts, n=12):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, (P[i - 1], P[i], P[i + 1], P[i + 2]))
        for u in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(np.array(P[-2]))
    return out


class Path:
    def __init__(self, segs, step=0.25):
        pts = []
        for sg in segs:
            if sg[0] == 'L':
                (x0, z0), (x1, z1) = sg[1], sg[2]
                n = max(2, int(math.hypot(x1 - x0, z1 - z0) / step))
                pts += [(x0 + (x1 - x0) * u, z0 + (z1 - z0) * u) for u in np.linspace(0, 1, n)]
            elif sg[0] == 'A':
                (cx, cz), r, a0, a1 = sg[1], sg[2], math.radians(sg[3]), math.radians(sg[4])
                n = max(4, int(abs(a1 - a0) * r / step))
                pts += [(cx + r * math.cos(a), cz + r * math.sin(a)) for a in np.linspace(a0, a1, n)]
            else:
                pts += [tuple(p) for p in catmull(sg[1], 40)]
        clean = [pts[0]]
        for p in pts[1:]:
            if math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-4:
                clean.append(p)
        self.p = np.array(clean)
        d = np.hypot(*(self.p[1:] - self.p[:-1]).T)
        self.s = np.concatenate([[0], np.cumsum(d)])
        self.length = self.s[-1]

    def pos(self, s):
        return float(np.interp(s, self.s, self.p[:, 0])), float(np.interp(s, self.s, self.p[:, 1]))

    def heading(self, s):
        a, b = self.pos(s - 0.6), self.pos(s + 0.6)
        return math.atan2(b[0] - a[0], b[1] - a[1])

    def s_near(self, x, z):
        return float(self.s[np.argmin(np.hypot(self.p[:, 0] - x, self.p[:, 1] - z))])


class Mover:
    """Follows a path; speed from a Key, anchored so that s(t_anchor) = s_anchor."""

    def __init__(self, path, speed, t_anchor, s_anchor, col='#3a7bd5', blink=None, brake=None, t0=-5, t1=60):
        self.path, self.speed_k, self.col = path, speed, col
        self.blink = blink or (lambda t: None)
        self.brake = brake or (lambda t: 0.0)
        self.g = np.arange(t0, t1, 1 / 120)
        v = np.array([max(0.0, speed(t)) for t in self.g])
        s = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 / 120)])
        self.sv = s - float(np.interp(t_anchor, self.g, s)) + s_anchor
        self.reverse = False

    def s(self, t):
        return float(np.interp(t, self.g, self.sv))

    def pose(self, t):
        s = self.s(t)
        x, z = self.path.pos(s)
        return x, z, self.path.heading(s)

    def speed(self, t):
        return max(0.0, self.speed_k(t))

    def steer(self, t):
        if self.speed(t) < 0.3:
            return 0.0          # wheels straight while stopped
        s = self.s(t)
        dh = self.path.heading(s + 1.5) - self.path.heading(s - 1.5)
        dh = (dh + math.pi) % (2 * math.pi) - math.pi
        return clamp(dh * 4.5, -1.6, 1.6)

    def visible(self, t):
        return True


class Kinematic:
    """Bicycle model. pose = car centre. v(t) in m/s (negative = reverse), delta(t) steering (rad, + = right)."""

    def __init__(self, x, z, h, v, delta, col=C_EGO, t0=0.0, t1=60, wb=2.7, blink=None):
        self.col, self.v, self.delta, self.wb = col, v, delta, wb
        self.blink = blink or (lambda t: None)
        self.brake = lambda t: 0.0
        self.g = np.arange(t0, t1, 1 / 120)
        rx, rz = x - math.sin(h) * 1.35, z - math.cos(h) * 1.35
        X, Z, Hs = [], [], []
        for t in self.g:
            X.append(rx + math.sin(h) * 1.35)
            Z.append(rz + math.cos(h) * 1.35)
            Hs.append(h)
            vv, dd = v(t), delta(t)
            rx += vv * math.sin(h) / 120
            rz += vv * math.cos(h) / 120
            h += vv / wb * math.tan(dd) / 120
        self.X, self.Z, self.H = np.array(X), np.array(Z), np.array(Hs)

    def pose(self, t):
        return (float(np.interp(t, self.g, self.X)), float(np.interp(t, self.g, self.Z)),
                float(np.interp(t, self.g, self.H)))

    def speed(self, t):
        return abs(self.v(t))

    def steer(self, t):
        return clamp(self.delta(t) * 2.6, -1.6, 1.6)

    @property
    def reverse(self):
        return False

    def is_reversing(self, t):
        return self.v(t) < -0.05

    def visible(self, t):
        return True


class Ped:
    def __init__(self, x, z, top='#e05d5d', pants='#2b3a63', skin='#e8b48f', hair='#3a2316', kid=False, wave=None):
        self.x, self.z = x if callable(x) else const(x), z if callable(z) else const(z)
        self.top, self.pants, self.skin, self.hair, self.kid = top, pants, skin, hair, kid
        self.wave = wave or (lambda t: 0.0)

    def walking(self, t):
        return math.hypot(self.x(t + 0.1) - self.x(t - 0.1), self.z(t + 0.1) - self.z(t - 0.1)) > 0.05

    def draw(self, ctx, view, t):
        euro.ped_bb(ctx, view, self.x(t), self.z(t), t, self.top, self.pants, self.skin, self.hair, self.kid,
                    self.walking(t), self.wave(t))


# ------------------------------------------------------------------ vehicles
def draw_car_g(ctx, view, x, z, h, col, t, blink=None, brake=0.0, rev=False, lw=None, kind='car'):
    Lf = L(x, z, h)
    body = hexc(col)
    dark = mix(body, (0, 0, 0), 0.3)
    glass = hexc('#2a3448')
    d = view.depth((x, 0.8, z))
    lw = lw or max(1.5, min(4.5, 60 / max(d, 1)))
    tyre = {k: hexc('#1c1c22') for k in ('front', 'back', 'left', 'right', 'top')}
    for wx in (-0.86, 0.86):
        for wz in (-1.38, 1.38):
            lbox(ctx, view, Lf, h, wx - 0.15, wx + 0.15, 0, 0.62, wz - 0.33, wz + 0.33, tyre, lw)
    vis = lbox(ctx, view, Lf, h, -0.92, 0.92, 0.28, 0.88, -2.2, 2.2,
               {'front': body, 'back': body, 'left': dark, 'right': dark, 'top': body}, lw)
    roof = hexc('#f2c230') if kind == 'taxi' else body
    lbox(ctx, view, Lf, h, -0.78, 0.78, 0.88, 1.42, -1.25, 0.95,
         {'front': glass, 'back': glass, 'left': glass, 'right': glass, 'top': roof}, lw)
    amb, off = AMBER, hexc('#7a4a00')
    sides = {'L': -1, 'R': 1}
    sg = sides.get(blink)
    if 'back' in vis:
        for s in (-1, 1):
            on = brake > 0.5
            face_rect(ctx, view, Lf, 'back', s * 0.62 - 0.2, s * 0.62 + 0.2, 0.62, 0.78, -2.21,
                      hexc('#ff4040') if on else hexc('#b01818'), RED if on else None, 1.2)
        face_rect(ctx, view, Lf, 'back', -0.25, 0.25, 0.42, 0.56, -2.21, (1, 1, 1) if rev else hexc('#e8e8ee'),
                  WHITE_L if rev else None, 1.0)
        for s in (-1, 1):
            on = sg == s
            face_rect(ctx, view, Lf, 'back', s * 0.78 - 0.12, s * 0.78 + 0.12, 0.6, 0.8, -2.22,
                      amb if on else off, amb if on else None, 1.6)
    if 'front' in vis:
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'front', s * 0.6 - 0.22, s * 0.6 + 0.22, 0.6, 0.76, 2.21, hexc('#fff6d8'))
            on = sg == s
            face_rect(ctx, view, Lf, 'front', s * 0.8 - 0.1, s * 0.8 + 0.1, 0.6, 0.76, 2.22,
                      amb if on else off, amb if on else None, 1.2)
    for face, s in (('left', -1), ('right', 1)):
        if face in vis:
            on = sg == s
            face_rect(ctx, view, Lf, face, 1.2, 1.5, 0.6, 0.72, s * 0.93, amb if on else off, amb if on else None, 1.0)


def draw_car_top_g(ctx, view, x, z, h, col, t, blink=None, ego=False, num=None):
    cx, cy = view.pt((x, 0, z))
    s = view.s
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(math.atan2(-math.cos(h), math.sin(h)))
    Lr, Wr = 4.4 * s, 1.84 * s
    if ego:
        glow(ctx, 0, 0, 3.6 * s, hexc('#ffffff'), 0.45)
    rrect(ctx, -Lr / 2, -Wr / 2, Lr, Wr, Wr * 0.35)
    fill_stroke(ctx, hexc(col), OUTL, max(2, s / 5))
    poly(ctx, [(Lr * 0.12, -Wr * 0.4), (Lr * 0.3, -Wr * 0.34), (Lr * 0.3, Wr * 0.34), (Lr * 0.12, Wr * 0.4)])
    setc(ctx, hexc('#2a3448'))
    ctx.fill()
    poly(ctx, [(-Lr * 0.3, -Wr * 0.38), (-Lr * 0.2, -Wr * 0.36), (-Lr * 0.2, Wr * 0.36), (-Lr * 0.3, Wr * 0.38)])
    ctx.fill()
    sg = {'L': -1, 'R': 1}.get(blink)
    if sg:
        for px in (Lr * 0.46, -Lr * 0.46):
            glow(ctx, px, sg * Wr * 0.42, 1.6 * s, AMBER, 0.9)
            ellipse(ctx, px, sg * Wr * 0.42, 0.32 * s, 0.32 * s)
            setc(ctx, AMBER)
            ctx.fill()
    ctx.restore()
    if num is not None:
        ellipse(ctx, cx, cy, 1.15 * s, 1.15 * s)
        fill_stroke(ctx, (1, 1, 1), OUTL, 4)
        text_center(ctx, str(num), cx, cy + 0.55 * s, 1.5 * s, OUTL)


# ------------------------------------------------------------------ top view
class TopN:
    ortho = True

    def __init__(self, xc, zc, s, ox=960, oy=540):
        self.xc, self.zc, self.s, self.ox, self.oy = xc, zc, s, ox, oy
        self.pos = (0, 1000, 0)

    def pt(self, P):
        return (self.ox + (P[0] - self.xc) * self.s, self.oy - (P[2] - self.zc) * self.s)

    def poly(self, pts):
        return [self.pt(p) for p in pts]

    def depth(self, P):
        return 0.0

    def scale(self, P):
        return self.s


def look_at(pos, target, f=1000, cx=960, cy=540):
    dx, dy, dz = target[0] - pos[0], target[1] - pos[1], target[2] - pos[2]
    return TCam(pos, math.atan2(dx, dz), math.atan2(-dy, math.hypot(dx, dz)), f, cx, cy)


# ------------------------------------------------------------------ static helpers
def disc(ctx, view, cx, cz, r, col, y=0.0, n=56, stroke=None):
    pts = [(cx + r * math.cos(a), y, cz + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    fill_poly(ctx, view, pts, col, stroke, 3)


def ring(ctx, view, cx, cz, r0, r1, col, y=0.0, n=56):
    for a0, a1 in zip(np.linspace(0, 2 * math.pi, n, endpoint=False), np.linspace(0, 2 * math.pi, n + 1)[1:]):
        fill_poly(ctx, view, [(cx + r0 * math.cos(a0), y, cz + r0 * math.sin(a0)), (cx + r1 * math.cos(a0), y, cz + r1 * math.sin(a0)),
                              (cx + r1 * math.cos(a1), y, cz + r1 * math.sin(a1)), (cx + r0 * math.cos(a1), y, cz + r0 * math.sin(a1))], col)


def zebra(ctx, view, x0, x1, z0, z1, along='x', w=0.55, gap=0.55):
    """Crosswalk stripes. along='x': stripes run along z, repeated in x."""
    if along == 'x':
        x = x0 + 0.2
        while x < x1 - 0.1:
            gquad(ctx, view, x, min(x + w, x1), z0, z1, C_LINE, 0.012)
            x += w + gap
    else:
        z = z0 + 0.2
        while z < z1 - 0.1:
            gquad(ctx, view, x0, x1, z, min(z + w, z1), C_LINE, 0.012)
            z += w + gap


def building(ctx, view, x0, x1, z0, z1, h, col, win='#2d3f55', roof=None, floors=3.3, frame=None):
    c = hexc(col)
    cols = {'front': c, 'back': c, 'left': mix(c, (0, 0, 0), 0.14), 'right': mix(c, (0, 0, 0), 0.07),
            'top': roof or mix(c, (1, 1, 1), 0.15)}
    if view.ortho:
        fill_poly(ctx, view, [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)], cols['top'], OUTL, 2)
        return
    Lf = lambda a, b, cc: (a, b, cc)
    vis = lbox(ctx, view, Lf, 0.0, x0, x1, 0, h, z0, z1, cols, 2)
    sc = view.scale(((x0 + x1) / 2, h / 2, (z0 + z1) / 2))
    if not sc or sc < 6:
        return
    wc = hexc(win)
    for face in vis:
        if face == 'top':
            continue
        if face in ('front', 'back'):
            span, d = (x0, x1), (z1 + 0.03 if face == 'front' else z0 - 0.03)
        else:
            span, d = (z0, z1), (x1 + 0.03 if face == 'right' else x0 - 0.03)
        width = span[1] - span[0]
        ncol = max(1, int(width / 3.2))
        for f in range(int(h / floors)):
            y0 = f * floors + 0.9
            if y0 + 1.6 > h:
                break
            for c_ in range(ncol):
                a = span[0] + width * (c_ + 0.25) / ncol
                b = a + width * 0.5 / ncol
                if frame:
                    face_rect(ctx, view, Lf, face, a - 0.12, b + 0.12, y0 - 0.12, y0 + 1.72, d, hexc(frame))
                face_rect(ctx, view, Lf, face, a, b, y0, y0 + 1.6, d, wc)


def conifer(ctx, view, x, z, s=1.0):
    if view.ortho:
        p = view.pt((x, 0, z))
        r = 1.6 * s * view.s
        ellipse(ctx, p[0], p[1], r, r)
        fill_stroke(ctx, hexc('#2f6b3f'), OUTL, 3)
        return
    b, sc = view.pt((x, 0, z)), view.scale((x, 0, z))
    if not b or not sc:
        return
    lw = max(1, min(4, sc / 30))
    ctx.rectangle(b[0] - 0.2 * sc, b[1] - 1.2 * sc, 0.4 * sc, 1.2 * sc)
    fill_stroke(ctx, hexc('#6b4a2f'), OUTL, lw)
    for i, (w_, y0, y1) in enumerate(((2.2, 1.0, 4.2), (1.7, 2.8, 5.8), (1.2, 4.4, 7.4))):
        poly(ctx, [(b[0] - w_ * s * sc, b[1] - y0 * s * sc), (b[0] + w_ * s * sc, b[1] - y0 * s * sc), (b[0], b[1] - y1 * s * sc)])
        fill_stroke(ctx, hexc(['#2f6b3f', '#3a7d4a', '#2f6b3f'][i]), OUTL, lw)


def front_facing(view, x, z, face_h):
    """True if the camera sees the front of a sign that faces direction face_h."""
    fx, fz = math.sin(face_h), math.cos(face_h)
    return (view.pos[0] - x) * fx + (view.pos[2] - z) * fz > 0


def stop_sign(ctx, view, x, z, face_h, text='STOP', small_text=None):
    if view.ortho:
        p = view.pt((x, 0, z))
        r = 0.45 * view.s
        poly(ctx, [(p[0] + math.cos(math.pi / 8 + i * math.pi / 4) * r, p[1] + math.sin(math.pi / 8 + i * math.pi / 4) * r) for i in range(8)])
        fill_stroke(ctx, hexc('#d62828'), OUTL, 2)
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 2.2, z)), view.scale((x, 2.2, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.05 * s, tp[1], 0.1 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#9aa0aa'), OUTL, max(1, s / 40))
    r = 0.42 * s
    cx_, cy_ = tp[0], tp[1] - r * 0.6
    oct_ = lambda rr: [(cx_ + math.cos(math.pi / 8 + i * math.pi / 4) * rr, cy_ + math.sin(math.pi / 8 + i * math.pi / 4) * rr) for i in range(8)]
    if not front_facing(view, x, z, face_h):
        poly(ctx, oct_(r))
        fill_stroke(ctx, hexc('#9aa0aa'), OUTL, max(1, s / 40))
        return
    poly(ctx, oct_(r))
    fill_stroke(ctx, (1, 1, 1), OUTL, max(1, s / 40))
    poly(ctx, oct_(r * 0.86))
    setc(ctx, hexc('#d62828'))
    ctx.fill()
    if r > 5:
        text_center(ctx, text, cx_, cy_ + r * 0.2, r * 0.55, (1, 1, 1))
    if small_text and r > 8:
        rrect(ctx, cx_ - r * 0.9, cy_ + r * 1.1, r * 1.8, r * 0.55, r * 0.08)
        fill_stroke(ctx, (1, 1, 1), OUTL, max(1, s / 50))
        text_center(ctx, small_text, cx_, cy_ + r * 1.52, r * 0.36, hexc('#d62828'))


def diamond_sign(ctx, view, x, z, face_h, draw_icon, tab=None, col='#f2c230'):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 2.3, z)), view.scale((x, 2.3, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.05 * s, tp[1], 0.1 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#9aa0aa'), OUTL, max(1, s / 40))
    r = 0.6 * s
    cx_, cy_ = tp[0], tp[1] - r - (0.45 * s if tab else 0)
    if not front_facing(view, x, z, face_h):
        poly(ctx, [(cx_, cy_ - r), (cx_ + r, cy_), (cx_, cy_ + r), (cx_ - r, cy_)])
        fill_stroke(ctx, hexc('#9aa0aa'), OUTL, max(1, s / 40))
        return
    if tab:
        rrect(ctx, cx_ - 0.55 * s, tp[1] - 0.44 * s, 1.1 * s, 0.42 * s, 0.05 * s)
        fill_stroke(ctx, hexc(col), OUTL, max(1, s / 40))
        if s > 10:
            text_center(ctx, tab, cx_, tp[1] - 0.12 * s, 0.28 * s, OUTL)
    poly(ctx, [(cx_, cy_ - r), (cx_ + r, cy_), (cx_, cy_ + r), (cx_ - r, cy_)])
    fill_stroke(ctx, hexc(col), OUTL, max(1, s / 40))
    if r > 6:
        draw_icon(ctx, cx_, cy_, r)


def roundabout_icon(ctx, cx, cy, r):
    ctx.set_line_width(max(2, r * 0.12))
    setc(ctx, OUTL)
    for k in range(3):
        a0 = -math.pi / 2 + k * 2 * math.pi / 3
        ctx.new_sub_path()
        ctx.arc_negative(cx, cy, r * 0.38, a0 + 0.2, a0 - 1.6)
        ctx.stroke()
        a = a0 - 1.75
        px, py = cx + math.cos(a) * r * 0.38, cy + math.sin(a) * r * 0.38
        tx, ty = math.sin(a), -math.cos(a)
        poly(ctx, [(px + tx * r * 0.16, py + ty * r * 0.16), (px - math.cos(a) * r * 0.13, py - math.sin(a) * r * 0.13),
                   (px + math.cos(a) * r * 0.13, py + math.sin(a) * r * 0.13)])
        ctx.fill()


def signal_head(ctx, view, x, y, z, face_h, state):
    """Overhead 3-light signal at (x, y, z), facing direction face_h. state: red/yellow/green."""
    p, s = view.pt((x, y, z)), view.scale((x, y, z))
    if view.ortho or not p or not s:
        return
    hw, hh = 0.45 * s, 1.2 * s
    rrect(ctx, p[0] - hw / 2, p[1] - hh / 2, hw, hh, hw * 0.2)
    fill_stroke(ctx, hexc('#2a2c36'), OUTL, max(1, s / 40))
    if not front_facing(view, x, z, face_h):
        return
    cols = {'red': '#ff3030', 'yellow': '#ffc21a', 'green': '#2bdc6a'}
    for i, nm in enumerate(('red', 'yellow', 'green')):
        cy_ = p[1] - hh / 2 + hh * (0.18 + 0.32 * i)
        r = hw * 0.34
        on = state == nm
        ellipse(ctx, p[0], cy_, r, r)
        setc(ctx, hexc(cols[nm]) if on else mix(hexc(cols[nm]), (0, 0, 0), 0.72))
        ctx.fill()
        if on:
            glow(ctx, p[0], cy_, r * 3, hexc(cols[nm]), 0.6)


def mountains(ctx, view, peaks, z, snow=True):
    """Distant mountain range: peaks = [(x, height), ...] at distance z (north)."""
    if view.ortho:
        return
    pts = [view.pt((x, h, z)) for x, h in peaks]
    pts = [p for p in pts if p]
    if len(pts) < 2:
        return
    base = view.pt((0, 0, z))
    if not base:
        return
    by = base[1] + 4
    ctx.move_to(pts[0][0] - 2000, by)
    for p in pts:
        ctx.line_to(*p)
    ctx.line_to(pts[-1][0] + 2000, by)
    ctx.close_path()
    setc(ctx, hexc('#7f9ab8'))
    ctx.fill()
    if snow:
        for (x, h), p in zip(peaks, pts):
            if h > 0.75 * max(hh for _, hh in peaks):
                sc = view.scale((x, h, z))
                w = 160 * sc
                poly(ctx, [(p[0], p[1]), (p[0] + w, p[1] + w * 0.6), (p[0] + w * 0.3, p[1] + w * 0.5),
                           (p[0] - w * 0.2, p[1] + w * 0.7), (p[0] - w, p[1] + w * 0.6)])
                setc(ctx, (0.97, 0.98, 1))
                ctx.fill()


# ------------------------------------------------------------------ world
class CityWorld:
    def __init__(self, dur, ego_segments, peds, city, units='mph'):
        """ego_segments: [(t0, t1, ego, [others...]), ...] (one segment for most videos)."""
        self.dur, self.segs, self.peds, self.city, self.units = dur, ego_segments, peds, city, units
        self.headlights = const(0)
        self.shake = const(0)

    def seg(self, t):
        for s in self.segs:
            if s[0] <= t < s[1]:
                return s
        return self.segs[-1] if t >= self.segs[-1][0] else self.segs[0]

    def ego(self, t):
        return self.seg(t)[2]

    def others(self, t):
        return self.seg(t)[3]

    def ego_xz(self, t):
        x, z, h = self.ego(t).pose(t)
        return x, z

    def heading(self, t):
        return self.ego(t).pose(t)[2]

    def speed(self, t):
        return self.ego(t).speed(t)

    def steer(self, t):
        return self.ego(t).steer(t)

    def blink_left(self, t):
        b = self.ego(t).blink(t)
        return 1.0 if b == 'L' else 0.0

    def blink_right(self, t):
        b = self.ego(t).blink(t)
        return 1.0 if b == 'R' else 0.0

    def ego_brake(self, t):
        return 0.0

    def dist(self, t):
        return self.ego_xz(t)[1]

    def camx(self, t):
        return self.ego_xz(t)[0]


def draw_scene(ctx, view, w, t, ego=True, overlay=None, nums=None, ghost=None):
    city = w.city
    if view.ortho:
        setc(ctx, city.ground_col)
        ctx.paint()
    else:
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 700, 0, hy)
        g.add_color_stop_rgb(0, *hexc(city.sky[0]))
        g.add_color_stop_rgb(1, *hexc(city.sky[1]))
        ctx.set_source(g)
        ctx.rectangle(-50, -50, SW + 100, hy + 52)
        ctx.fill()
        for cx0, cy0, sc0 in ((260, 110, 1.0), (1000, 70, 0.8), (1640, 150, 1.1)):
            for dx, dy, r in ((0, 0, 60), (60, -25, 70), (130, 0, 55), (60, 15, 60)):
                ellipse(ctx, cx0 + dx * sc0, hy - 520 + cy0 + dy * sc0, r * sc0, r * sc0 * 0.8)
            setc(ctx, (1, 1, 1), 0.88)
            ctx.fill()
        setc(ctx, city.ground_col)
        ctx.rectangle(-50, hy, SW + 100, SH + 100 - hy)
        ctx.fill()
        city.skyline(ctx, view)
    city.ground(ctx, view, t)
    if overlay:
        overlay(ctx, view)
    items = list(city.objects(ctx, view, t))
    nums = nums or {}
    for i, a in enumerate(w.others(t)):
        if not a.visible(t):
            continue
        x, z, h = a.pose(t)
        n = nums.get(i)
        if view.ortho:
            items.append(((x, 0.8, z), lambda x=x, z=z, h=h, a=a, n=n: draw_car_top_g(ctx, view, x, z, h, a.col, t, a.blink(t), False, n)))
        else:
            items.append(((x, 0.8, z), lambda x=x, z=z, h=h, a=a: draw_car_g(ctx, view, x, z, h, a.col, t, a.blink(t), a.brake(t),
                                                                              kind=getattr(a, 'kind', 'car'))))
    for p in w.peds:
        items.append(((p.x(t), 0.9, p.z(t)), lambda p=p: p.draw(ctx, view, t)))
    if ego:
        e = w.ego(t)
        x, z, h = e.pose(t)
        rev = isinstance(e, Kinematic) and e.is_reversing(t)
        n = nums.get('ego')
        if view.ortho:
            items.append(((x, 0.8, z), lambda: draw_car_top_g(ctx, view, x, z, h, e.col, t, e.blink(t), True, n)))
        else:
            items.append(((x, 0.8, z), lambda: draw_car_g(ctx, view, x, z, h, e.col, t, e.blink(t), e.brake(t), rev)))
    if view.ortho:
        order = sorted(items, key=lambda it: it[0][1])
    else:
        order = sorted(items, key=lambda it: -view.depth(it[0]))
    for _, fn in order:
        fn()
    if not view.ortho:
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 30, 0, hy + 140)
        g.add_color_stop_rgba(0, 0.86, 0.95, 1, 0.0)
        g.add_color_stop_rgba(0.25, 0.86, 0.95, 1, 0.35)
        g.add_color_stop_rgba(1, 0.86, 0.95, 1, 0.0)
        ctx.set_source(g)
        ctx.rectangle(-50, hy - 30, SW + 100, 170)
        ctx.fill()


# ------------------------------------------------------------------ cameras & scenes
def ego_view(w, t, mode, **kw):
    x, z, h = w.ego(t).pose(t)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    if mode == 'chase':
        return TCam((x - fx * 10.5, 3.6, z - fz * 10.5), h, 0.16, 1000, cy=520)
    if mode == 'high':
        return TCam((x - fx * 13, 9.0, z - fz * 13), h, 0.42, 1000, cy=470)
    if mode == 'close_l':
        return TCam((x - fx * 5.6 - rx * 1.3, 1.7, z - fz * 5.6 - rz * 1.3), h + 0.13, 0.08, 1000)
    if mode == 'close_r':
        return TCam((x - fx * 5.6 + rx * 1.3, 1.7, z - fz * 5.6 + rz * 1.3), h - 0.13, 0.08, 1000)
    if mode == 'inside':
        yaw = kw.get('yaw', 0.0)
        return TCam((x - rx * 0.38 - fx * 0.2, 1.18, z - rz * 0.38 - fz * 0.2), h + yaw, 0.03, 1000, cy=470)
    raise ValueError(mode)


def hud(ctx, w, t):
    v = w.speed(t) * (2.237 if w.units == 'mph' else 3.6)
    unit = 'mph' if w.units == 'mph' else 'km/h'
    rrect(ctx, 1560, 900, 310, 130, 34)
    setc(ctx, (0, 0, 0), 0.5)
    ctx.fill()
    text_center(ctx, f"{int(round(v))}", 1675, 990, 84, (1, 1, 1))
    text_center(ctx, unit, 1800, 990, 34, (0.85, 0.85, 0.9))


def c_cam(ctx, w, t, lt, kw):
    if kw['cam'] == 'fixed':
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000))
    else:
        view = ego_view(w, t, kw['cam'])
    draw_scene(ctx, view, w, t, overlay=kw.get('overlay'))
    if kw.get('hud', True):
        hud(ctx, w, t)
    if kw.get('post'):
        kw['post'](ctx, view, t, lt)


def wheel(ctx, ang):
    ctx.save()
    ctx.translate(960, 1230)
    ctx.rotate(ang)
    ellipse(ctx, 0, 0, 470, 360)
    ellipse(ctx, 0, 0, 405, 300)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#1b1b24'), OUTL, 5)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    rrect(ctx, -60, -310, 120, 40, 12)
    setc(ctx, hexc('#ffd23f'))
    ctx.fill()
    for s in (-1, 1):
        hx, hy = s * 360, -240
        poly(ctx, [(hx + s * 40, hy + 30), (hx + s * 210, hy + 520), (hx - s * 120, hy + 560), (hx - s * 60, hy + 60)])
        fill_stroke(ctx, JACKET, OUTL, 5)
        ellipse(ctx, hx, hy, 85, 62, s * 0.5)
        fill_stroke(ctx, SKIN, OUTL, 5)
        ellipse(ctx, hx - s * 20, hy - 30, 50, 26, s * 0.3)
        fill_stroke(ctx, SKIN, OUTL, 4)
    ctx.restore()


def cockpit(ctx, w, t):
    setc(ctx, hexc('#2a2a36'))
    poly(ctx, [(250, -10), (360, -10), (175, 820), (50, 820)])
    ctx.fill()
    poly(ctx, [(1560, -10), (1670, -10), (1880, 820), (1755, 820)])
    ctx.fill()
    ctx.rectangle(-10, -10, SW + 20, 34)
    ctx.fill()
    ctx.move_to(-10, 830)
    ctx.curve_to(500, 790, 1400, 790, SW + 10, 830)
    ctx.line_to(SW + 10, SH + 10)
    ctx.line_to(-10, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, hexc('#3a3a4c'), hexc('#55566e'), 5)
    wheel(ctx, w.steer(t))
    for side, fn in ((-1, w.blink_left), (1, w.blink_right)):
        if fn(t) > 0.5:
            cx = 960 + side * 90
            glow(ctx, cx, 880, 70, hexc('#2bff6a'), 0.5)
            poly(ctx, [(cx + side * 30, 880), (cx - side * 10, 852), (cx - side * 10, 868), (cx - side * 40, 868),
                       (cx - side * 40, 892), (cx - side * 10, 892), (cx - side * 10, 908)])
            setc(ctx, hexc('#2bff6a'))
            ctx.fill()


def c_inside(ctx, w, t, lt, kw):
    view = ego_view(w, t, 'inside', yaw=key_or(kw, 'yaw', lt, 0.0))
    draw_scene(ctx, view, w, t, ego=False)
    if abs(key_or(kw, 'yaw', lt, 0.0)) < 0.3:
        cockpit(ctx, w, t)
    else:
        setc(ctx, hexc('#2a2a36'))
        ctx.rectangle(-10, -10, SW + 20, 40)
        ctx.fill()
        ctx.move_to(-10, 860)
        ctx.curve_to(600, 820, 1300, 820, SW + 10, 860)
        ctx.line_to(SW + 10, SH + 10)
        ctx.line_to(-10, SH + 10)
        ctx.close_path()
        fill_stroke(ctx, hexc('#3a3a4c'), hexc('#55566e'), 5)
    if kw.get('hud', True):
        hud(ctx, w, t)
    if kw.get('post'):
        kw['post'](ctx, view, t, lt)


def c_top(ctx, w, t, lt, kw):
    xc, zc = kw.get('center', (0, 0))
    if kw.get('follow'):
        ex, ez = w.ego_xz(t)
        xc, zc = ex + kw.get('off', (0, 0))[0], ez + kw.get('off', (0, 0))[1]
    view = TopN(xc, zc, kw.get('scale', 20.0))
    nums = kw.get('nums', lambda t, lt: {})(t, lt) if callable(kw.get('nums')) else kw.get('nums')
    draw_scene(ctx, view, w, t, overlay=lambda c, v: kw['under'](c, v, t, lt) if kw.get('under') else None, nums=nums)
    if kw.get('post'):
        kw['post'](ctx, view, t, lt)


def c_rear(ctx, w, t, lt, kw):
    """Reversing camera (mirrored image) with guideline overlay."""
    x, z, h = w.ego(t).pose(t)
    fx, fz = math.sin(h), math.cos(h)
    view = TCam((x - fx * 2.25, 1.0, z - fz * 2.25), h + math.pi, 0.42, 620, cy=380, mirror=True)
    draw_scene(ctx, view, w, t, ego=False)
    # guidelines
    for (y0, y1, col) in ((1080, 860, '#22c35e'), (860, 720, '#ffd23f'), (720, 640, '#e0393e')):
        for side in (-1, 1):
            xa, xb = 960 + side * (520 - (1080 - y0) * 0.75), 960 + side * (520 - (1080 - y1) * 0.75)
            ctx.move_to(xa, y0)
            ctx.line_to(xb, y1)
            setc(ctx, hexc(col))
            ctx.set_line_width(10)
            ctx.stroke()
        xb = 520 - (1080 - y1) * 0.75
        ctx.move_to(960 - xb, y1)
        ctx.line_to(960 - xb + 70, y1)
        ctx.move_to(960 + xb, y1)
        ctx.line_to(960 + xb - 70, y1)
        ctx.stroke()
    ctx.rectangle(0, 0, SW, 70)
    setc(ctx, (0, 0, 0), 0.55)
    ctx.fill()
    text_center(ctx, 'Check surroundings for safety', 960, 48, 36, (1, 1, 1))
    rrect(ctx, 30, 90, 160, 60, 14)
    setc(ctx, (0, 0, 0), 0.55)
    ctx.fill()
    text_center(ctx, 'R', 110, 135, 48, hexc('#ffd23f'))


def c_shoulder(ctx, w, t, lt, kw):
    """Over-the-shoulder look (side='R' right-rear, 'L' left-rear)."""
    x, z, h = w.ego(t).pose(t)
    rx, rz = math.cos(h), -math.sin(h)
    side = kw.get('side', 'R')
    sg = 1 if side == 'R' else -1
    view = TCam((x - rx * 0.35, 1.2, z - rz * 0.35), h + sg * 2.2, 0.05, 800, cx=960 + sg * 60)
    draw_scene(ctx, view, w, t, ego=False)
    ctx.save()
    if side == 'R':
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


def c_dash(ctx, w, t, lt, kw):
    engine.SCENES['dash2'](ctx, w, t, lt, kw)


engine.SCENES.update(c_cam=c_cam, c_inside=c_inside, c_top=c_top, c_rear=c_rear, c_shoulder=c_shoulder)


# ------------------------------------------------------------------ overlays / labels
def label(ctx, x, y, text, col, size=42):
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    w = ctx.text_extents(text).x_advance
    rrect(ctx, x - w / 2 - 18, y - size - 4, w + 36, size + 22, 14)
    fill_stroke(ctx, hexc(col) if isinstance(col, str) else col, (1, 1, 1), 3)
    ctx.move_to(x - w / 2, y + 2)
    setc(ctx, (1, 1, 1))
    ctx.show_text(text)


def arrow_path(ctx, pts, col, width=8, alpha=1.0, dash=None, head=26):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if dash:
        ctx.set_dash(dash)
    setc(ctx, col, alpha)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.set_dash([])
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    a = math.atan2(by - ay, bx - ax)
    poly(ctx, [(bx + math.cos(a) * head, by + math.sin(a) * head),
               (bx + math.cos(a + 2.4) * head, by + math.sin(a + 2.4) * head),
               (bx + math.cos(a - 2.4) * head, by + math.sin(a - 2.4) * head)])
    setc(ctx, col, alpha)
    ctx.fill()


def city_ambience(d, gain=1.0):
    t = np.arange(int(d * SR)) / SR
    return (lp(noise(len(t)), 260) * 0.35 + bp(noise(len(t)), 400, 2000) * 0.025) * gain


def engine_idle(d, f=32):
    t = np.arange(int(d * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 6))
    return lp(s, 300) * 0.15 * env_adsr(len(t), 0.2, 0.3)


def reverse_beeps(d, period=0.45):
    out = np.zeros(int(d * SR) + SR)
    tt = 0.0
    while tt < d:
        x = np.arange(int(0.12 * SR)) / SR
        place(out, np.sin(2 * np.pi * 1800 * x) * env_adsr(len(x), 0.005, 0.02) * 0.25, tt)
        tt += period
    return out[:int(d * SR)]
