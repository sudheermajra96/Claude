"""Tiny procedural 2D cartoon engine for vertical night-driving safety shorts.

Everything is drawn with Cairo in a flat, outlined cartoon style and the sound
effects are synthesised with numpy (no samples, no external assets).

Canvas: 1080x1920 (9:16). A 16:9 "scene band" sits in the middle of a black
frame with a two-line caption above it.
"""
import math
import os
import random
import subprocess
import wave

import cairo
import numpy as np
from scipy import signal

W, H = 1080, 1920
SW, SH = 1920, 1080                 # logical scene size
SCALE = W / SW
SCENE_H = SH * SCALE
SCENE_Y = (H - SCENE_H) / 2
FPS = 30
SR = 44100


# ----------------------------------------------------------------- helpers
def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def brighten(c, k):
    return tuple(min(1.0, x * (1 + k) + 0.04 * k) for x in c)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def setc(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def ellipse(ctx, x, y, rx, ry, rot=0.0):
    ctx.save()
    ctx.new_sub_path()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def fill_stroke(ctx, fill, stroke=(0.04, 0.04, 0.07), lw=4, alpha=1.0):
    setc(ctx, fill, alpha)
    if stroke is None:
        ctx.fill()
    else:
        ctx.fill_preserve()
        setc(ctx, stroke, alpha)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()


def glow(ctx, x, y, r, color, a=1.0, core=0.15):
    if r <= 0.5 or a <= 0.002:
        return
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *color, a)
    g.add_color_stop_rgba(core, *color, a * 0.75)
    g.add_color_stop_rgba(0.45, *color, a * 0.22)
    g.add_color_stop_rgba(1, *color, 0)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def text_center(ctx, s, x, y, size, color=(1, 1, 1), weight=cairo.FONT_WEIGHT_BOLD, a=1.0):
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, weight)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    ctx.move_to(x - ext.x_advance / 2, y)
    setc(ctx, color, a)
    ctx.show_text(s)


VERTICAL = False
COCKPIT_MIRROR = True   # draw the small side mirror on the dashboard (legacy episodes only)
LAYER = 'all'          # 'all' | 'bg' | 'mid' | 'post' while rendering layered frames
LAYERED_SCENES = set()  # scene kinds that split their drawing with layer()


def layer(name):
    return LAYER == 'all' or LAYER == name


def cel(ctx, path_fn, off, a=0.22, rim=(10, 8), rim_a=0.35, rim_w=8, outline=6):
    """Cel-shade the shape drawn by path_fn: shadow crescent away from a top-left light, rim light,
    then re-stroke the outline."""
    ctx.save()
    path_fn()
    ctx.clip()
    ctx.new_path()
    ctx.rectangle(-20000, -20000, 40000, 40000)
    ctx.save()
    ctx.translate(*off)
    path_fn()
    ctx.restore()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgba(0.16, 0.05, 0.14, a)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.save()
    ctx.translate(*rim)
    path_fn()
    ctx.restore()
    ctx.set_source_rgba(1, 0.97, 0.9, rim_a)
    ctx.set_line_width(rim_w)
    ctx.stroke()
    ctx.restore()
    path_fn()
    setc(ctx, OUTL)
    ctx.set_line_width(outline)
    ctx.stroke()


def outlined_text(ctx, s, x, y, size, color=(1, 1, 1), stroke=(0, 0, 0), lw=12):
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    ctx.move_to(x - ext.x_advance / 2, y)
    ctx.text_path(s)
    setc(ctx, stroke)
    ctx.set_line_width(lw)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke_preserve()
    setc(ctx, color)
    ctx.fill()


class Key:
    """Keyframed value: Key([(t, v), ...]) with smoothstep (or 'lin'/'step') easing."""

    def __init__(self, pts, ease='smooth'):
        self.pts = sorted(pts)
        self.ease = ease

    def __call__(self, t):
        p = self.pts
        if t <= p[0][0]:
            return p[0][1]
        if t >= p[-1][0]:
            return p[-1][1]
        for (t0, v0), (t1, v1) in zip(p, p[1:]):
            if t0 <= t <= t1:
                if self.ease == 'step':
                    return v0
                u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
                if self.ease == 'smooth':
                    u = smooth(u)
                return v0 + (v1 - v0) * u
        return p[-1][1]


def const(v):
    return Key([(0, v)])


def blinking(intervals, period=0.8):
    """1/0 blinker on during any of [(t0, t1), ...]; on for first half of each period."""
    def f(t):
        for t0, t1 in intervals:
            if t0 <= t < t1:
                return 1.0 if ((t - t0) % period) < period / 2 else 0.0
        return 0.0
    return f


# ------------------------------------------------------------------ palette
SKY_TOP = hexc('#05061a')
SKY_HOR = hexc('#1e2154')
MTN_FAR = hexc('#181a3c')
MTN_NEAR = hexc('#0c0d20')
GROUND = hexc('#0f1024')
ROAD = hexc('#24243a')
LINE = hexc('#6a6c88')
RAIL = hexc('#5d6078')
POST = hexc('#3a3c52')
OUTL = hexc('#08080e')
SKIN = hexc('#e9b98f')
SKIN_SH = hexc('#c99470')
JACKET = hexc('#d0912c')
JACKET_SH = hexc('#a66f1c')
HAIR = hexc('#3a2316')
AMBER = hexc('#ffb21e')
RED = hexc('#ff2a2a')
WHITE_L = hexc('#fff7e6')


# ------------------------------------------------------------------- world
class Vehicle:
    def __init__(self, kind, X, Z, color='#c23b3b', brake=None, highbeam=None):
        self.kind = kind            # 'car' or 'truck'
        self.X = X if callable(X) else const(X)
        self.Z = Z if callable(Z) else const(Z)   # metres ahead of ego (negative = behind)
        self.color = hexc(color)
        self.brake = brake or const(0)
        self.highbeam = highbeam or const(0)


class World:
    """Continuous state shared by every shot so cuts stay consistent."""

    def __init__(self, dur, speed, camx, headlights=None, vehicles=(), blink_left=None,
                 blink_right=None, shake=None, ego_brake=None):
        self.dur = dur
        self.speed = speed          # m/s
        self.camx = camx
        self.headlights = headlights or const(1)
        self.vehicles = list(vehicles)
        self.blink_left = blink_left or (lambda t: 0.0)
        self.blink_right = blink_right or (lambda t: 0.0)
        self.shake = shake or const(0)
        self.ego_brake = ego_brake or const(0)
        n = int(dur * FPS) + 2
        ts = np.arange(n) / FPS
        v = np.array([speed(t) for t in ts])
        self._d = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 / FPS)])
        self._ts = ts

    def dist(self, t):
        return float(np.interp(t, self._ts, self._d))

    def steer(self, t):
        dt = 0.12
        vx = (self.camx(t + dt) - self.camx(t - dt)) / (2 * dt)
        return vx / max(self.speed(t), 4.0)


class Cam:
    def __init__(self, cx, hy, f, camx, camh=1.2, yaw_px=0.0):
        self.cx, self.hy, self.f, self.camx, self.camh, self.yaw = cx, hy, f, camx, camh, yaw_px

    def p(self, X, Y, Z):
        return (self.cx + self.yaw + (X - self.camx) * self.f / Z,
                self.hy + (self.camh - Y) * self.f / Z)


# ------------------------------------------------------------- road scenery
_rng = random.Random(7)
MTN_A = [(x, 70 + 90 * math.sin(x / 260) + 60 * math.sin(x / 97 + 1) + _rng.uniform(0, 25))
         for x in range(-600, 2600, 40)]
MTN_B = [(x, 30 + 60 * math.sin(x / 180 + 2) + 40 * math.sin(x / 61) + _rng.uniform(0, 15))
         for x in range(-600, 2600, 30)]
STARS = [(_rng.uniform(0, SW), _rng.uniform(0, 380), _rng.uniform(0.8, 2.2)) for _ in range(70)]

LANE_W = 3.6
EDGE = 3.75
RAIL_X = 5.2


DAY = False


def draw_sky(ctx, hy, yaw, x0=0, x1=SW):
    if DAY:
        return draw_sky_day(ctx, hy, yaw, x0, x1)
    g = cairo.LinearGradient(0, hy - 600, 0, hy)
    g.add_color_stop_rgb(0, *SKY_TOP)
    g.add_color_stop_rgb(1, *SKY_HOR)
    ctx.set_source(g)
    ctx.rectangle(x0, -50, x1 - x0, hy + 50)
    ctx.fill()
    for sx, sy, r in STARS:
        if sy < hy - 120:
            setc(ctx, (0.8, 0.82, 1.0), 0.35)
            ctx.arc((sx + yaw * 0.95) % SW, sy, r, 0, 2 * math.pi)
            ctx.fill()
    for pts, col, k in ((MTN_A, MTN_FAR, 0.95), (MTN_B, MTN_NEAR, 0.97)):
        ctx.move_to(-800, hy + 2)
        for x, h in pts:
            ctx.line_to(x + yaw * k, hy - h)
        ctx.line_to(3000, hy + 2)
        ctx.close_path()
        setc(ctx, col)
        ctx.fill()


def draw_sky_day(ctx, hy, yaw, x0=0, x1=SW):
    g = cairo.LinearGradient(0, hy - 600, 0, hy)
    g.add_color_stop_rgb(0, *hexc('#5fb4f2'))
    g.add_color_stop_rgb(1, *hexc('#cfeeff'))
    ctx.set_source(g)
    ctx.rectangle(x0 - 400, -50, x1 - x0 + 800, hy + 52)
    ctx.fill()
    glow(ctx, 1550 + yaw * 0.9, hy - 420, 300, hexc('#fff3c4'), 0.5)
    ellipse(ctx, 1550 + yaw * 0.9, hy - 420, 60, 60)
    setc(ctx, hexc('#fff6d8'))
    ctx.fill()
    for cx0, cy0, sc in ((300, 140, 1.0), (900, 90, 0.8), (1400, 200, 1.1), (1900, 120, 0.9)):
        cx_ = (cx0 + yaw * 0.95) % (SW + 600) - 300
        for dx, dy, r in ((0, 0, 60), (60, -25, 70), (130, 0, 55), (60, 15, 60)):
            ellipse(ctx, cx_ + dx * sc, hy - 600 + cy0 + dy * sc + 100, r * sc, r * sc * 0.8)
        setc(ctx, (1, 1, 1), 0.92)
        ctx.fill()
    for pts, col, k in ((MTN_A, hexc('#9cc9a0'), 0.95), (MTN_B, hexc('#6fae74'), 0.97)):
        ctx.move_to(-800, hy + 2)
        for x, h in pts:
            ctx.line_to(x + yaw * k, hy - h * 0.6)
        ctx.line_to(3000, hy + 2)
        ctx.close_path()
        setc(ctx, col)
        ctx.fill()


def zlist(zn, zf, n):
    return [zn * (zf / zn) ** (i / n) for i in range(n + 1)]


def draw_road(ctx, cam, dist, light, sign=1, zn=1.6, zf=420, lit_fn=None, dash_light=1.0):
    """sign=+1 looking forward, -1 looking backward (dash scroll reversed)."""
    lit_fn = lit_fn or (lambda Z: 0.0)
    hy = cam.hy
    # ground
    setc(ctx, GROUND)
    ctx.rectangle(-200, hy, SW + 400, SH)
    ctx.fill()
    # road surface
    a, b = cam.p(-RAIL_X, 0, zn), cam.p(RAIL_X, 0, zn)
    c, d = cam.p(RAIL_X, 0, zf), cam.p(-RAIL_X, 0, zf)
    poly(ctx, [a, b, c, d])
    g = cairo.LinearGradient(0, hy, 0, a[1])
    g.add_color_stop_rgb(0, *mix(ROAD, SKY_HOR, 0.5))
    g.add_color_stop_rgb(0.25, *ROAD)
    g.add_color_stop_rgb(1, *brighten(ROAD, 0.25))
    ctx.set_source(g)
    ctx.fill()
    zs = zlist(zn, zf, 46)

    def segcol(base, Z, extra=0.0):
        fog = clamp((Z - 25) / 260)
        c = mix(base, SKY_HOR, fog * 0.75)
        return brighten(c, lit_fn(Z) * (0.9 + extra))

    # solid edge lines
    for ex in (-EDGE, EDGE):
        for z0, z1 in zip(zs, zs[1:]):
            poly(ctx, [cam.p(ex - .08, 0, z0), cam.p(ex + .08, 0, z0),
                       cam.p(ex + .08, 0, z1), cam.p(ex - .08, 0, z1)])
            setc(ctx, segcol(mix(LINE, (1, 1, 1), 0.3 * dash_light), z0, 1.0))
            ctx.fill()
    # centre dashes (world positions every 12 m)
    first = math.floor((dist - (zf if sign < 0 else 0)) / 12) - 1
    for n in range(first, first + int(zf / 12) + 3):
        p0, p1 = n * 12.0, n * 12.0 + 3.5
        z0, z1 = sorted(((p0 - dist) * sign, (p1 - dist) * sign))
        z0, z1 = max(z0, zn), min(z1, zf)
        if z1 <= z0:
            continue
        poly(ctx, [cam.p(-.09, 0, z0), cam.p(.09, 0, z0), cam.p(.09, 0, z1), cam.p(-.09, 0, z1)])
        setc(ctx, segcol(mix(LINE, (1, 1, 1), 0.35 * dash_light), z0, 1.0))
        ctx.fill()
    # guardrails + posts
    for side in (-1, 1):
        gx = RAIL_X * side
        posts = []
        firstp = math.floor((dist - (zf if sign < 0 else 0)) / 4) - 1
        for n in range(firstp, firstp + int(min(zf, 140) / 4) + 3):
            z = (n * 4.0 - dist) * sign
            if zn < z < 140:
                posts.append(z)
        for z in sorted(posts, reverse=True):
            x0, y0 = cam.p(gx, 0, z)
            x1, y1 = cam.p(gx, 0.78, z)
            w = 0.12 * cam.f / z
            ctx.rectangle(x0 - w / 2, y1, w, y0 - y1)
            setc(ctx, segcol(POST, z))
            ctx.fill()
        for z0, z1 in zip(zs, zs[1:]):
            poly(ctx, [cam.p(gx, 0.42, z0), cam.p(gx, 0.42, z1), cam.p(gx, 0.78, z1), cam.p(gx, 0.78, z0)])
            setc(ctx, segcol(RAIL, z0))
            ctx.fill()
            poly(ctx, [cam.p(gx, 0.42, z0), cam.p(gx, 0.42, z1), cam.p(gx, 0.5, z1), cam.p(gx, 0.5, z0)])
            setc(ctx, segcol(mix(RAIL, OUTL, 0.5), z0))
            ctx.fill()
    # headlight pool on the asphalt
    if light > 0.01:
        ctx.save()
        poly(ctx, [a, b, c, d])
        ctx.clip()
        px, py = cam.p(0.2 + cam.camx, 0, 9)
        ctx.translate(px, py)
        ctx.scale(2.6, 1.0)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 330)
        g.add_color_stop_rgba(0, 1, 0.95, 0.8, 0.30 * light)
        g.add_color_stop_rgba(0.5, 1, 0.95, 0.8, 0.12 * light)
        g.add_color_stop_rgba(1, 1, 0.95, 0.8, 0)
        ctx.set_operator(cairo.OPERATOR_ADD)
        ctx.set_source(g)
        ctx.paint()
        ctx.restore()


# ---------------------------------------------------------------- vehicles
def box(ctx, cam, x0, x1, y0, y1, zr, zf, c_face, c_side, c_top=None, lw=3):
    """Axis-aligned box seen from cam; zr = face nearest the camera."""
    faces = []
    if x1 < cam.camx:
        faces.append(([(x1, y0, zr), (x1, y1, zr), (x1, y1, zf), (x1, y0, zf)], c_side))
    if x0 > cam.camx:
        faces.append(([(x0, y0, zr), (x0, y1, zr), (x0, y1, zf), (x0, y0, zf)], c_side))
    if y1 < cam.camh and c_top is not None:
        faces.append(([(x0, y1, zr), (x1, y1, zr), (x1, y1, zf), (x0, y1, zf)], c_top))
    faces.append(([(x0, y0, zr), (x1, y0, zr), (x1, y1, zr), (x0, y1, zr)], c_face))
    for pts, col in faces:
        poly(ctx, [cam.p(*p) for p in pts])
        fill_stroke(ctx, col, OUTL, lw)


def draw_vehicle_rear(ctx, cam, v, t, X, Z, lit):
    """Vehicle ahead of the camera: we see its back."""
    k = lit * 1.4
    lw = max(1.5, min(5, 40 / Z))
    if v.kind == 'truck':
        hw = 1.25
        # wheels / chassis
        box(ctx, cam, X - hw + .1, X + hw - .1, 0, 1.0, Z + 0.3, Z + 12, hexc('#121218'), hexc('#121218'), lw=lw)
        side = brighten(hexc('#2b39c9'), k * 0.6 + 0.15)
        doors = brighten(hexc('#9a9db0'), k * 0.8)
        box(ctx, cam, X - hw, X + hw, 1.0, 3.9, Z, Z + 13, mix(doors, (0, 0, 0), 0.35), side,
            brighten(hexc('#3442d8'), k * 0.4), lw=lw)
        # door seam + bumper
        a, b = cam.p(X, 1.05, Z), cam.p(X, 3.85, Z)
        setc(ctx, OUTL)
        ctx.set_line_width(lw)
        ctx.move_to(*a)
        ctx.line_to(*b)
        ctx.stroke()
        b0, b1 = cam.p(X - hw, 0.55, Z - 0.05), cam.p(X + hw, 0.75, Z - 0.05)
        ctx.rectangle(b0[0], b1[1], b1[0] - b0[0], b0[1] - b1[1])
        fill_stroke(ctx, brighten(hexc('#d8d8e0'), k * 0.3), OUTL, lw)
        ly = 0.92
        lx = hw - 0.2
    else:
        hw = 0.9
        body = brighten(mix(v.color, (0, 0, 0), 0.35), k)
        side = brighten(mix(v.color, (0, 0, 0), 0.55), k * 0.7)
        box(ctx, cam, X - hw + .05, X + hw - .05, 0, 0.36, Z + 0.4, Z + 3.8, hexc('#0d0d12'), hexc('#0d0d12'), lw=lw)
        box(ctx, cam, X - hw, X + hw, 0.28, 0.86, Z, Z + 4.4, body, side, body, lw=lw)
        box(ctx, cam, X - hw + .14, X + hw - .14, 0.86, 1.38, Z + 0.9, Z + 3.4,
            brighten(hexc('#14161f'), k * 0.5), brighten(hexc('#191b26'), k * 0.4), body, lw=lw)
        # plate
        p0, p1 = cam.p(X - .26, .42, Z - .01), cam.p(X + .26, .56, Z - .01)
        ctx.rectangle(p0[0], p1[1], p1[0] - p0[0], p0[1] - p1[1])
        fill_stroke(ctx, brighten(hexc('#c9c9d2'), k * 0.4 + 0.2), OUTL, lw * 0.6)
        ly = 0.72
        lx = hw - 0.22
    br = v.brake(t)
    for s in (-1, 1):
        q0 = cam.p(X + s * lx - 0.17, ly - 0.07, Z - 0.02)
        q1 = cam.p(X + s * lx + 0.17, ly + 0.07, Z - 0.02)
        rrect(ctx, q0[0], q1[1], q1[0] - q0[0], q0[1] - q1[1], 4)
        setc(ctx, mix(hexc('#8a1010'), hexc('#ff5050'), 0.35 + 0.65 * br))
        ctx.fill()
        cx, cy = (q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2
        r = (0.9 + 1.6 * br) * cam.f / Z
        glow(ctx, cx, cy, min(r, 420), RED, 0.35 + 0.6 * br)
    if br > 0.05 and v.kind == 'car':
        cx, cy = cam.p(X, 1.3, Z + 3.35)
        glow(ctx, cx, cy, min(0.8 * cam.f / Z, 260), RED, 0.7 * br)


def draw_vehicle_front(ctx, cam, v, t, X, D, scene_light=1.0):
    """Vehicle behind the camera (rear-facing camera / mirror): we see its nose."""
    hw = 0.9 if v.kind == 'car' else 1.25
    lw = max(1.5, min(5, 40 / D))
    hb = v.highbeam(t)
    body = mix(v.color, (0, 0, 0), 0.72)
    box(ctx, cam, X - hw, X + hw, 0.22, 0.85, D, D + 4.4, body, mix(body, (0, 0, 0), 0.3), body, lw=lw)
    box(ctx, cam, X - hw + .16, X + hw - .16, 0.85, 1.38, D + 1.2, D + 3.0, hexc('#0c0d16'), hexc('#0c0d16'), body, lw=lw)
    # light spill on road between it and us
    px, py = cam.p(X, 0, max(D * 0.55, 1.8))
    glow(ctx, px, py, min(5.5 * cam.f / D, 900), (1, 0.95, 0.85), 0.18 + 0.25 * hb)
    for s in (-1, 1):
        cx, cy = cam.p(X + s * (hw - 0.25), 0.66, D - 0.02)
        rr = 0.16 * cam.f / D
        ellipse(ctx, cx, cy, rr * 1.3, rr * 0.8)
        setc(ctx, (1, 1, 1))
        ctx.fill()
        glow(ctx, cx, cy, min((1.4 + 2.5 * hb) * cam.f / D, 1100), WHITE_L, 0.75 + 0.25 * hb, core=0.1)


# ------------------------------------------------------------------ shots
class Shot:
    def __init__(self, dur, kind, **kw):
        self.dur, self.kind, self.kw = dur, kind, kw
        self.start = 0.0


def lit_profile(hl):
    return lambda Z: hl * clamp(1 - (Z - 6) / 50) * 0.5


def pov(ctx, world, t, lt, kw):
    camx = world.camx(t)
    spd = world.speed(t)
    yaw = -world.steer(t) * 1400 + kw.get('yaw', 0)
    shake = world.shake(t)
    bob = math.sin(t * 11) * 1.2 * min(spd / 30, 1) + shake * 14 * math.sin(t * 71)
    cam = Cam(960 + shake * 10 * math.sin(t * 53), 470 + bob, 1000, camx, 1.2, yaw)
    hl = world.headlights(t)
    lit = lit_profile(hl)
    draw_sky(ctx, cam.hy, yaw)
    draw_road(ctx, cam, world.dist(t), hl, 1, lit_fn=lit, dash_light=0.4 + 0.6 * hl)
    vs = [(v.Z(t), v) for v in world.vehicles]
    for Z, v in sorted(vs, key=lambda x: -x[0]):
        if 2.2 < Z < 400:
            draw_vehicle_rear(ctx, cam, v, t, v.X(t), Z, lit(Z))
    cockpit(ctx, world, t, cam)


def cockpit(ctx, world, t, cam):
    # pillars + roof
    setc(ctx, hexc('#17171f'))
    poly(ctx, [(250, -10), (360, -10), (175, 820), (50, 820)])
    ctx.fill()
    poly(ctx, [(1560, -10), (1670, -10), (1880, 820), (1755, 820)])
    ctx.fill()
    ctx.rectangle(-10, -10, SW + 20, 34)
    ctx.fill()
    # dashboard
    ctx.move_to(-10, 830)
    ctx.curve_to(500, 790, 1400, 790, SW + 10, 830)
    ctx.line_to(SW + 10, SH + 10)
    ctx.line_to(-10, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, hexc('#2c2c3d'), hexc('#45455e'), 5)
    # left mirror with live reflection (legacy look; new episodes switch it off)
    mx, my = 120, 850
    if not COCKPIT_MIRROR:
        return cockpit_wheel(ctx, world, t)
    ellipse(ctx, mx, my, 205, 128, -0.08)
    fill_stroke(ctx, hexc('#1f4a86'), OUTL, 5)
    ctx.save()
    ellipse(ctx, mx + 10, my, 170, 100, -0.08)
    ctx.clip()
    mirror_view(ctx, world, t, Cam(mx + 70, my - 22, 260, world.camx(t) - 0.9, 1.0), small=True)
    ctx.restore()
    ellipse(ctx, mx + 10, my, 170, 100, -0.08)
    setc(ctx, OUTL)
    ctx.set_line_width(5)
    ctx.stroke()
    if world.blink_left(t) > 0.5:
        glow(ctx, mx - 150, my + 40, 120, AMBER, 0.9)
    cockpit_wheel(ctx, world, t)


def cockpit_wheel(ctx, world, t):
    # steering wheel + hands
    ang = clamp(world.steer(t) * 3.5, -0.3, 0.3)
    wx, wy = 960, 1230
    ctx.save()
    ctx.translate(wx, wy)
    ctx.rotate(ang)
    ellipse(ctx, 0, 0, 470, 360)
    ellipse(ctx, 0, 0, 405, 300)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#1b1b24'), OUTL, 5)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for s in (-1, 1):
        hx, hy = s * 360, -240
        poly(ctx, [(hx + s * 40, hy + 30), (hx + s * 210, hy + 520), (hx - s * 120, hy + 560), (hx - s * 60, hy + 60)])
        fill_stroke(ctx, JACKET, OUTL, 5)
        ellipse(ctx, hx, hy, 85, 62, s * 0.5)
        fill_stroke(ctx, SKIN, OUTL, 5)
        ellipse(ctx, hx - s * 20, hy - 30, 50, 26, s * 0.3)
        fill_stroke(ctx, SKIN, OUTL, 4)
    ctx.restore()
    hl = world.headlights(t)
    if hl > 0.5:
        glow(ctx, 960, 860, 80, (0.2, 1, 0.4), 0.25)


def mirror_view(ctx, world, t, cam, small=False):
    """Rear-facing view used inside mirrors."""
    draw_sky(ctx, cam.hy, 0)
    draw_road(ctx, cam, world.dist(t), 0, -1, zn=1.5, zf=300, dash_light=0.3)
    vs = [(-v.Z(t), v) for v in world.vehicles]
    for D, v in sorted(vs, key=lambda x: -x[0]):
        if 1.6 < D < 300:
            draw_vehicle_front(ctx, cam, v, t, v.X(t), D)


def side_mirror(ctx, world, t, lt, kw):
    camx = world.camx(t)
    yaw = -world.steer(t) * 900
    shake = world.shake(t)
    jitter = shake * 10 * math.sin(t * 61)
    # out-of-focus side window background
    cam = Cam(1500 + yaw, 330 + jitter, 700, camx - 1.0, 1.0)
    draw_sky(ctx, cam.hy, yaw)
    draw_road(ctx, cam, world.dist(t), world.headlights(t) * 0.5, 1, zn=3, lit_fn=lit_profile(world.headlights(t)))
    setc(ctx, (0.02, 0.02, 0.06), 0.35)
    ctx.paint()
    # door + window frame at the right
    poly(ctx, [(1700, -10), (SW + 10, -10), (SW + 10, SH + 10), (1450, SH + 10), (1640, 600)])
    fill_stroke(ctx, hexc('#24304a'), OUTL, 6)
    poly(ctx, [(1640, 600), (1450, SH + 10), (1380, SH + 10), (1590, 560)])
    fill_stroke(ctx, hexc('#141826'), OUTL, 4)
    # mirror housing
    mx, my = 930 + jitter, 520
    rot = -0.06
    ctx.save()
    ctx.translate(mx, my)
    ctx.rotate(rot)
    rrect(ctx, -560, -330, 1120, 660, 300)
    fill_stroke(ctx, hexc('#1c3b63'), OUTL, 7)
    rrect(ctx, -520, -290, 1040, 580, 260)
    fill_stroke(ctx, hexc('#0b1424'), OUTL, 5)
    ctx.restore()
    # reflection
    ctx.save()
    ctx.save()
    ctx.translate(mx, my)
    ctx.rotate(rot)
    rrect(ctx, -500, -270, 1000, 540, 240)
    ctx.restore()
    ctx.clip()
    mcam = Cam(mx + 230, my - 70, 900, camx - 1.0, 1.0)
    mirror_view(ctx, world, t, mcam)
    # own car body sliver in the glass
    poly(ctx, [(mx + 330, my - 40), (mx + 520, my - 90), (mx + 520, my + 300), (mx + 260, my + 300)])
    fill_stroke(ctx, hexc('#2d5ea8'), OUTL, 5)
    poly(ctx, [(mx + 300, my + 40), (mx + 520, my + 10), (mx + 520, my + 30), (mx + 296, my + 62)])
    setc(ctx, hexc('#5b8fd6'))
    ctx.fill()
    # glass sheen
    g = cairo.LinearGradient(mx - 500, my - 270, mx + 100, my + 270)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.10)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    if world.blink_left(t) > 0.5:
        bx, by = mx - 430, my + 250
        rrect(ctx, bx - 70, by - 18, 140, 36, 18)
        setc(ctx, AMBER)
        ctx.fill()
        glow(ctx, bx, by, 330, AMBER, 0.9)
        glow(ctx, mx - 120, my + 200, 160, AMBER, 0.35)


def rear_mirror(ctx, world, t, lt, kw):
    camx = world.camx(t)
    shake = world.shake(t)
    jitter = shake * 10 * math.sin(t * 61)
    # windshield top behind the mirror
    draw_sky(ctx, 900, -world.steer(t) * 900)
    setc(ctx, hexc('#191925'))
    ctx.move_to(-10, -10)
    ctx.line_to(SW + 10, -10)
    ctx.line_to(SW + 10, 120)
    ctx.curve_to(1300, 170, 600, 170, -10, 120)
    ctx.close_path()
    ctx.fill()
    # stem
    ctx.rectangle(920, 100, 80, 120)
    fill_stroke(ctx, hexc('#24243a'), OUTL, 5)
    mx, my = 960 + jitter, 560
    rrect(ctx, mx - 800, my - 340, 1600, 680, 120)
    fill_stroke(ctx, hexc('#222230'), OUTL, 7)
    ctx.save()
    rrect(ctx, mx - 760, my - 300, 1520, 600, 90)
    ctx.clip()
    mcam = Cam(mx, my - 20, 1100, camx, 1.25)
    mirror_view(ctx, world, t, mcam)
    # rear cabin silhouette (rear window frame, headrests)
    setc(ctx, hexc('#121219'))
    ctx.rectangle(mx - 800, my - 340, 1600, 680)
    rrect(ctx, mx - 560, my - 230, 1120, 380, 70)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for hx in (mx - 360, mx + 360):
        rrect(ctx, hx - 130, my + 60, 260, 200, 60)
        fill_stroke(ctx, hexc('#2a2a36'), OUTL, 4)
    hb = max([v.highbeam(t) * clamp(1 - (-v.Z(t) - 3) / 25) for v in world.vehicles if v.Z(t) < -1] + [0])
    if hb > 0:
        ctx.save()
        rrect(ctx, mx - 560, my - 230, 1120, 380, 70)
        ctx.clip()
        setc(ctx, (1, 0.98, 0.92), 0.45 * hb)
        ctx.paint()
        ctx.restore()
        glow(ctx, mx, my - 40, 900, WHITE_L, 0.5 * hb)
    g = cairo.LinearGradient(mx - 760, my - 300, mx, my + 300)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.08)
    g.add_color_stop_rgba(0.6, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()


def dash(ctx, world, t, lt, kw):
    spd = world.speed(t) * 3.6
    ctx.set_source_rgb(*hexc('#0d0e1c'))
    ctx.paint()
    # hood
    ctx.move_to(60, SH + 10)
    ctx.line_to(60, 300)
    ctx.curve_to(400, 60, 1520, 60, 1860, 300)
    ctx.line_to(1860, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, hexc('#1c1d2e'), OUTL, 6)
    for gx, maxv, label, val, major in ((620, 240, 'km/h', spd, 20), (1300, 8, 'x1000 rpm', 0.8 + spd / 55, 1)):
        R = 290
        gy = 590
        ellipse(ctx, gx, gy, R, R)
        fill_stroke(ctx, hexc('#090a14'), hexc('#3d4060'), 10)
        a0, a1 = math.radians(140), math.radians(400)
        steps = int(maxv / major)
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            ctx.move_to(gx + math.cos(a) * (R - 20), gy + math.sin(a) * (R - 20))
            ctx.line_to(gx + math.cos(a) * (R - 55), gy + math.sin(a) * (R - 55))
            setc(ctx, (0.9, 0.92, 1.0) if not (maxv == 8 and i >= 6) else (1, 0.3, 0.25))
            ctx.set_line_width(6)
            ctx.stroke()
            if maxv == 8 or i % 2 == 0:
                text_center(ctx, str(i * major), gx + math.cos(a) * (R - 95), gy + math.sin(a) * (R - 95) + 14,
                            38, (0.85, 0.87, 1.0), cairo.FONT_WEIGHT_NORMAL)
        text_center(ctx, label, gx, gy + 150, 34, (0.6, 0.62, 0.8), cairo.FONT_WEIGHT_NORMAL)
        a = a0 + (a1 - a0) * clamp(val / maxv)
        ctx.move_to(gx - math.cos(a) * 40, gy - math.sin(a) * 40)
        ctx.line_to(gx + math.cos(a) * (R - 40), gy + math.sin(a) * (R - 40))
        setc(ctx, hexc('#ff5a36'))
        ctx.set_line_width(12)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        glow(ctx, gx + math.cos(a) * (R - 80), gy + math.sin(a) * (R - 80), 90, hexc('#ff5a36'), 0.25)
        ellipse(ctx, gx, gy, 34, 34)
        fill_stroke(ctx, hexc('#2a2c40'), OUTL, 4)
    text_center(ctx, f"{int(spd):d}", 620, 760, 70, (1, 1, 1))
    # turn arrows
    for side, fn in ((-1, world.blink_left), (1, world.blink_right)):
        on = fn(t) > 0.5
        cx, cy = 960 + side * 80, 300
        pts = [(cx + side * 60, cy), (cx, cy - 50), (cx, cy - 22), (cx - side * 55, cy - 22),
               (cx - side * 55, cy + 22), (cx, cy + 22), (cx, cy + 50)]
        poly(ctx, pts)
        setc(ctx, hexc('#2bff6a') if on else hexc('#1d3326'))
        ctx.fill()
        if on:
            glow(ctx, cx, cy, 180, hexc('#2bff6a'), 0.6)
    # headlight icon
    hl = world.headlights(t)
    col = hexc('#3cff7a') if hl > 0.5 else hexc('#1d3326')
    ix, iy = 960, 520
    ctx.arc(ix - 10, iy, 34, math.pi / 2, 3 * math.pi / 2)
    ctx.close_path()
    setc(ctx, col)
    ctx.fill()
    for k in range(4):
        ctx.move_to(ix + 36, iy - 30 + k * 20)
        ctx.line_to(ix + 80, iy - 22 + k * 20)
    ctx.set_line_width(7)
    ctx.stroke()
    if world.ego_brake(t) > 0.5:
        text_center(ctx, "(!)", 960, 700, 64, hexc('#ff4040'))


def stalk(ctx, world, t, lt, kw):
    ctx.set_source_rgb(*hexc('#3b3a55'))
    ctx.paint()
    g = cairo.RadialGradient(900, 540, 200, 900, 540, 1200)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    ctx.set_source(g)
    ctx.paint()
    ang = kw['angle'](lt) if 'angle' in kw else 0.0          # degrees, + = down
    ring = kw['ring'](lt) if 'ring' in kw else 0.0           # 0 = OFF, 1 = lights
    px, py = 2150, 520
    ctx.save()
    ctx.translate(px, py)
    ctx.rotate(math.radians(ang))
    ctx.translate(-px, -py)
    # palm behind
    ellipse(ctx, 360, 600, 330, 200, 0.05)
    fill_stroke(ctx, SKIN, OUTL, 6)
    poly(ctx, [(-40, 500), (120, 520), (200, 900), (-40, 940)])
    fill_stroke(ctx, JACKET, OUTL, 6)
    # stalk
    ctx.move_to(px, py - 60)
    ctx.line_to(420, py - 78)
    ctx.curve_to(330, py - 80, 330, py + 80, 420, py + 82)
    ctx.line_to(px, py + 60)
    ctx.close_path()
    fill_stroke(ctx, hexc('#18181f'), OUTL, 6)
    # rotating ring
    rx = 960
    rrect(ctx, rx - 30, py - 92, 70, 184, 30)
    fill_stroke(ctx, hexc('#232330'), OUTL, 5)
    ctx.move_to(rx - 14, py - 88)
    ctx.curve_to(rx - 44, py - 30, rx - 44, py + 30, rx - 14, py + 88)
    setc(ctx, (0.95, 0.95, 1))
    ctx.set_line_width(5)
    ctx.stroke()
    labels = ['OFF', 'AUTO', '●']
    for i, lab in enumerate(labels):
        y = py + 44 - (i - ring) * 44
        if py - 80 < y < py + 90:
            text_center(ctx, lab, rx + 110, y, 34 if i < 2 else 26, (0.95, 0.95, 1) if abs(i - ring - 0) < 0.4 else (0.55, 0.55, 0.7))
    # headlight symbol on stalk
    hx, hy = rx + 90, py - 60
    ctx.arc(hx, hy, 14, -math.pi / 2, math.pi / 2)
    ctx.close_path()
    setc(ctx, (0.85, 0.85, 0.95))
    ctx.fill()
    ctx.move_to(rx + 30, py + 44 - (0 - ring) * 0)
    # pointer triangle
    poly(ctx, [(rx - 70, py + 30), (rx - 50, py + 44), (rx - 70, py + 58)])
    setc(ctx, (0.95, 0.95, 1))
    ctx.fill()
    # fingers wrapping over the tip
    ellipse(ctx, 560, 470, 150, 70, -0.12)
    fill_stroke(ctx, SKIN, OUTL, 6)
    ellipse(ctx, 610, 560, 70, 110, 0.0)
    fill_stroke(ctx, SKIN, OUTL, 6)
    ctx.restore()
    if world.blink_left(t) > 0.5 or world.blink_right(t) > 0.5:
        glow(ctx, 1700, 900, 120, hexc('#2bff6a'), 0.35)


def pedals(ctx, world, t, lt, kw):
    ctx.set_source_rgb(*hexc('#2e2e40'))
    ctx.paint()
    poly(ctx, [(-10, 760), (SW + 10, 640), (SW + 10, SH + 10), (-10, SH + 10)])
    setc(ctx, hexc('#232334'))
    ctx.fill()
    pos = kw['pos'](lt) if 'pos' in kw else 0.0          # 0 gas, 1 brake
    press = kw['press'](lt) if 'press' in kw else 0.0
    gas_press = (1 - pos) * kw.get('gas', 0.6)
    # brake pedal arm + pad
    bx, by = 700, 600 + press * 70
    ctx.rectangle(bx - 25, -10, 50, by - 60)
    fill_stroke(ctx, hexc('#2a2a36'), OUTL, 5)
    ctx.save()
    ctx.translate(bx, by)
    ctx.rotate(-0.25 + press * 0.15)
    rrect(ctx, -170, -110, 340, 220, 30)
    fill_stroke(ctx, hexc('#17171f'), OUTL, 6)
    for i in range(-3, 4):
        rrect(ctx, -140, i * 26 - 6, 280, 12, 6)
        setc(ctx, hexc('#3c3c4c'))
        ctx.fill()
    ctx.restore()
    # gas pedal
    gx, gy = 1260, 560 + gas_press * 40
    ctx.save()
    ctx.translate(gx, gy)
    ctx.rotate(-0.22 + gas_press * 0.1)
    rrect(ctx, -85, -200, 170, 400, 26)
    fill_stroke(ctx, hexc('#17171f'), OUTL, 6)
    for i in range(-6, 7):
        rrect(ctx, -60, i * 28 - 5, 120, 10, 5)
        setc(ctx, hexc('#3c3c4c'))
        ctx.fill()
    ctx.restore()
    # leg + shoe
    sx = gx + (bx - gx) * pos
    sy = gy + (by - gy) * pos - math.sin(math.pi * pos) * 120 + 20
    poly(ctx, [(sx + 120, sy - 60), (sx + 1100, sy - 900), (sx + 1500, sy - 500), (sx + 320, sy + 90)])
    fill_stroke(ctx, hexc('#2a3657'), OUTL, 6)
    ctx.save()
    ctx.translate(sx, sy)
    ctx.rotate(-0.28)
    ctx.move_to(-240, -40)
    ctx.curve_to(-260, -120, -60, -150, 120, -120)
    ctx.line_to(330, -90)
    ctx.line_to(330, 90)
    ctx.line_to(-170, 90)
    ctx.curve_to(-260, 90, -270, 40, -240, -40)
    ctx.close_path()
    fill_stroke(ctx, hexc('#121216'), OUTL, 6)
    rrect(ctx, -260, 60, 600, 40, 20)
    fill_stroke(ctx, hexc('#e8e8ee'), OUTL, 5)
    ctx.restore()
    if press > 0.7:
        for k in range(3):
            a = -2.4 + k * 0.35
            ctx.move_to(bx + math.cos(a) * 240, by + math.sin(a) * 240)
            ctx.line_to(bx + math.cos(a) * 320, by + math.sin(a) * 320)
        setc(ctx, (1, 1, 1), 0.8)
        ctx.set_line_width(8)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


# expression presets: brow (raise), browtilt (+ angry, - worried), eye (open), pupil, mouth, sweat
EXPR = {
    'calm':    dict(brow=0.0, tilt=0.0, eye=1.0, pupil=1.0, mouth='smile', mo=0.3),
    'happy':   dict(brow=0.25, tilt=-0.1, eye=1.0, pupil=1.0, mouth='grin', mo=0.9),
    'annoyed': dict(brow=-0.2, tilt=0.5, eye=0.6, pupil=1.0, mouth='flat', mo=0.0),
    'unsure':  dict(brow=0.2, tilt=-0.45, eye=1.0, pupil=1.0, mouth='wavy', mo=0.3),
    'shock':   dict(brow=0.9, tilt=-0.4, eye=1.35, pupil=0.55, mouth='o', mo=1.0),
    'scream':  dict(brow=1.0, tilt=-0.6, eye=1.45, pupil=0.45, mouth='scream', mo=1.0),
    'relief':  dict(brow=0.4, tilt=-0.5, eye=0.7, pupil=1.0, mouth='wavy', mo=0.5),
    'sad':     dict(brow=0.3, tilt=-0.7, eye=0.75, pupil=1.0, mouth='frown', mo=0.5),
    'whistle': dict(brow=0.3, tilt=-0.1, eye=0.9, pupil=1.0, mouth='pucker', mo=0.5),
    'drowsy':  dict(brow=-0.1, tilt=-0.2, eye=0.28, pupil=1.0, mouth='flat', mo=0.0),
    'asleep':  dict(brow=-0.1, tilt=0.0, eye=0.06, pupil=1.0, mouth='o', mo=0.2),
    'yawn':    dict(brow=0.35, tilt=-0.2, eye=0.1, pupil=1.0, mouth='scream', mo=1.0),
    'focus':   dict(brow=-0.1, tilt=0.3, eye=0.8, pupil=1.0, mouth='flat', mo=0.0),
}


def face(ctx, world, t, lt, kw):
    ex = EXPR[kw.get('expr', 'calm')]
    shake = kw.get('shake', 0.0) * (1 if lt < 1.2 else 0.3)
    jx = math.sin(lt * 70) * 14 * shake
    sweat = kw.get('sweat', False)
    # interior behind driver: rear window, seats
    draw_sky(ctx, 520, (t * 40) % 400)
    setc(ctx, hexc('#14141d'))
    ctx.rectangle(-10, -10, SW + 20, SH + 20)
    rrect(ctx, 200, 60, 1520, 520, 120)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    # passing light sweeping the cabin
    sweep = (t * 0.35) % 1
    glow(ctx, 200 + sweep * 1600, 300, 300, (0.6, 0.65, 1.0), 0.10)
    # seat
    rrect(ctx, 420 + jx * 0.3, 220, 1080, 1000, 220)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 6)
    rrect(ctx, 680 + jx * 0.3, 70, 560, 300, 120)
    fill_stroke(ctx, hexc('#46465c'), OUTL, 6)
    cx, cy = 960 + jx, 520
    lurch = kw['lurch'](lt) if 'lurch' in kw else 0.0
    ctx.save()
    ctx.translate(960, 1000)
    ctx.scale(1 + 0.22 * lurch, 1 + 0.22 * lurch)
    ctx.translate(-960, -1000 - 70 * lurch)
    # body
    ctx.move_to(cx - 470, SH + 10)
    ctx.curve_to(cx - 470, 860, cx - 300, 790, cx, 790)
    ctx.curve_to(cx + 300, 790, cx + 470, 860, cx + 470, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    poly(ctx, [(cx - 120, 795), (cx + 120, 795), (cx, 960)])
    fill_stroke(ctx, hexc('#f2efe6'), OUTL, 5)
    # seatbelt
    if kw.get('belt', True):
        poly(ctx, [(cx + 330, 800), (cx + 410, 830), (cx - 250, SH + 10), (cx - 360, SH + 10)])
        fill_stroke(ctx, hexc('#2a2a33'), OUTL, 5)
    # neck
    ctx.rectangle(cx - 80, 700, 160, 110)
    fill_stroke(ctx, SKIN_SH, OUTL, 5)
    # ears
    for s in (-1, 1):
        ellipse(ctx, cx + s * 235, cy + 30, 48, 62)
        fill_stroke(ctx, SKIN, OUTL, 6)
    # head
    ellipse(ctx, cx, cy, 245, 270)
    fill_stroke(ctx, SKIN, OUTL, 7)
    # hair (curly top)
    ctx.save()
    hairs = [(-200, -150, 85), (-120, -225, 95), (-20, -255, 100), (90, -240, 95), (180, -175, 85),
             (-230, -60, 55), (225, -70, 55), (40, -200, 90), (-80, -200, 90)]
    for hx, hy, r in hairs:
        ctx.new_sub_path()
        ctx.arc(cx + hx, cy + hy, r, 0, 2 * math.pi)
    setc(ctx, HAIR)
    ctx.fill_preserve()
    setc(ctx, OUTL)
    ctx.set_line_width(6)
    ctx.stroke()
    for hx, hy, r in hairs:
        ctx.arc(cx + hx, cy + hy, r - 3, 0, 2 * math.pi)
        setc(ctx, HAIR)
        ctx.fill()
    ctx.restore()
    # eyes
    blink = 1.0
    bp = (t + 0.7) % 3.3
    if bp < 0.12 and ex['eye'] < 1.3:
        blink = 0.1
    eo = ex['eye'] * blink
    for s in (-1, 1):
        ex_x, ex_y = cx + s * 92, cy + 10
        ellipse(ctx, ex_x, ex_y, 52 * min(ex['eye'], 1.2), 52 * eo)
        fill_stroke(ctx, (1, 1, 1), OUTL, 5)
        if eo > 0.2:
            pr = 18 * ex['pupil']
            ellipse(ctx, ex_x + s * 2, ex_y + 6, pr, pr * min(1, eo))
            setc(ctx, OUTL)
            ctx.fill()
            ellipse(ctx, ex_x + s * 2 + pr * 0.35, ex_y + 6 - pr * 0.35, pr * 0.3, pr * 0.3)
            setc(ctx, (1, 1, 1))
            ctx.fill()
        # glasses
        rrect(ctx, ex_x - 82, ex_y - 66, 164, 132, 46)
        setc(ctx, OUTL)
        ctx.set_line_width(11)
        ctx.stroke()
        ctx.move_to(ex_x - 40, ex_y - 40)
        ctx.line_to(ex_x - 10, ex_y - 54)
        setc(ctx, (1, 1, 1), 0.5)
        ctx.set_line_width(6)
        ctx.stroke()
        # brows
        by = ex_y - 92 - ex['brow'] * 45
        tl = ex['tilt'] * 30
        ctx.move_to(ex_x - s * 60, by - (-tl) * 0 + (tl if s > 0 else tl) * 0)
        ctx.move_to(ex_x - 60, by + s * tl)
        ctx.line_to(ex_x + 60, by - s * tl)
        setc(ctx, HAIR)
        ctx.set_line_width(18)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    ctx.move_to(cx - 18, cy + 10)
    ctx.line_to(cx + 18, cy + 10)
    setc(ctx, OUTL)
    ctx.set_line_width(11)
    ctx.stroke()
    # nose
    ctx.move_to(cx - 8, cy + 60)
    ctx.curve_to(cx - 30, cy + 110, cx + 10, cy + 120, cx + 22, cy + 105)
    setc(ctx, SKIN_SH)
    ctx.set_line_width(7)
    ctx.stroke()
    # mouth
    m, mo, my = ex['mouth'], ex['mo'], cy + 175
    ctx.set_line_width(8)
    if m == 'smile':
        ctx.arc(cx, my - 40, 70, 0.35 * math.pi, 0.65 * math.pi)
        setc(ctx, OUTL)
        ctx.stroke()
    elif m == 'grin':
        ctx.move_to(cx - 95, my - 15)
        ctx.curve_to(cx - 60, my + 70, cx + 60, my + 70, cx + 95, my - 15)
        ctx.close_path()
        fill_stroke(ctx, hexc('#7a1f25'), OUTL, 6)
        ctx.rectangle(cx - 75, my - 13, 150, 22)
        setc(ctx, (1, 1, 1))
        ctx.fill()
    elif m == 'flat':
        ctx.move_to(cx - 60, my)
        ctx.line_to(cx + 60, my - 6)
        setc(ctx, OUTL)
        ctx.stroke()
    elif m == 'pucker':
        ellipse(ctx, cx + 6, my + 4, 20, 24)
        fill_stroke(ctx, hexc('#5e1419'), OUTL, 6)
        for i in range(3):
            ph = (t * 0.7 + i / 3) % 1
            nx, ny = cx + 90 + ph * 260 + i * 10, my - 30 - ph * 320
            a = math.sin(math.pi * ph)
            for col, lw in ((OUTL, 15), ((1, 1, 1), 7)):
                ctx.move_to(nx + 24, ny - 4)
                ctx.line_to(nx + 24, ny - 90)
                ctx.line_to(nx + 60, ny - 72)
                setc(ctx, col, a)
                ctx.set_line_width(lw)
                ctx.stroke()
            ellipse(ctx, nx, ny, 30, 22, -0.4)
            fill_stroke(ctx, (1, 1, 1), OUTL, 5, a)
    elif m == 'frown':
        ctx.arc(cx, my + 50, 60, 1.25 * math.pi, 1.75 * math.pi)
        setc(ctx, OUTL)
        ctx.stroke()
    elif m == 'wavy':
        ctx.move_to(cx - 70, my)
        for i in range(1, 8):
            ctx.line_to(cx - 70 + i * 20, my + (8 if i % 2 else -8))
        setc(ctx, OUTL)
        ctx.stroke()
    elif m == 'o':
        ellipse(ctx, cx, my + 10, 38, 50)
        fill_stroke(ctx, hexc('#5e1419'), OUTL, 6)
    elif m == 'scream':
        ctx.move_to(cx - 110, my - 30)
        ctx.curve_to(cx - 120, my + 120, cx + 120, my + 120, cx + 110, my - 30)
        ctx.curve_to(cx + 40, my - 50, cx - 40, my - 50, cx - 110, my - 30)
        fill_stroke(ctx, hexc('#5e1419'), OUTL, 7)
        ctx.save()
        ctx.move_to(cx - 110, my - 30)
        ctx.curve_to(cx - 120, my + 120, cx + 120, my + 120, cx + 110, my - 30)
        ctx.curve_to(cx + 40, my - 50, cx - 40, my - 50, cx - 110, my - 30)
        ctx.clip()
        ctx.rectangle(cx - 120, my - 50, 240, 32)
        setc(ctx, (1, 1, 1))
        ctx.fill()
        ellipse(ctx, cx, my + 90, 60, 35)
        setc(ctx, hexc('#d0545e'))
        ctx.fill()
        ctx.restore()
    if sweat:
        sx, sy = cx + 200, cy - 90 + (lt * 40) % 60
        ctx.move_to(sx, sy - 45)
        ctx.curve_to(sx + 30, sy, sx + 30, sy + 30, sx, sy + 30)
        ctx.curve_to(sx - 30, sy + 30, sx - 30, sy, sx, sy - 45)
        fill_stroke(ctx, hexc('#8fd6ff'), OUTL, 4)
    # wheel rim + hands in foreground
    ellipse(ctx, cx * 0 + 960, SH + 260, 640, 330)
    ellipse(ctx, 960, SH + 260, 570, 270)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#1b1b24'), OUTL, 6)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for s in (-1, 1):
        ellipse(ctx, 960 + s * 560, SH + 30, 95, 70, s * 0.4)
        fill_stroke(ctx, SKIN, OUTL, 6)
    # shock lines
    if kw.get('expr') in ('scream', 'shock') and lt < 1.5:
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.35
            r0 = 330 + 20 * math.sin(lt * 30 + k)
            ctx.move_to(cx + math.cos(a) * r0, cy - 40 + math.sin(a) * r0)
            ctx.line_to(cx + math.cos(a) * (r0 + 70), cy - 40 + math.sin(a) * (r0 + 70))
        setc(ctx, (1, 1, 1), 0.9)
        ctx.set_line_width(10)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    ctx.restore()


def rewind(ctx, world, t, lt, kw):
    # replays a POV moment at a scrambled time with VHS treatment
    src = kw['src_t'](lt)
    pov(ctx, world, src, lt, {})
    setc(ctx, (0.05, 0.05, 0.15), 0.45)
    ctx.paint()
    rnd = random.Random(int(lt * 30))
    for _ in range(9):
        y = rnd.uniform(0, SH)
        ctx.rectangle(0, y, SW, rnd.uniform(3, 14))
        setc(ctx, (1, 1, 1), rnd.uniform(0.05, 0.25))
        ctx.fill()
    for i in range(2):
        x = 120 + i * 70
        poly(ctx, [(x + 70, 90), (x, 140), (x + 70, 190)])
        setc(ctx, (1, 1, 1))
        ctx.fill()
    text_center(ctx, "REWIND", 440, 162, 70)
    text_center(ctx, kw.get('label', "Let's try that again..."), 960, 600, 84)


SCENES = dict(pov=pov, side_mirror=side_mirror, rear_mirror=rear_mirror, dash=dash,
              stalk=stalk, pedals=pedals, face=face, rewind=rewind)


# --------------------------------------------------------------- composer
class Video:
    def __init__(self, caption, world, shots, overlays=None, vertical=False, layered=False):
        global VERTICAL
        VERTICAL = vertical
        self.layered = layered
        self.vertical = vertical        # True: scenes fill the 9:16 frame (camera follows shot 'fx')
        self.caption = caption          # list of lines
        self.world = world
        self.shots = shots
        t = 0.0
        for s in shots:
            s.start = t
            t += s.dur
        self.dur = t
        self.overlays = overlays or []   # (t0, t1, fn(ctx, t))

    def shot_at(self, t):
        for s in self.shots:
            if s.start <= t < s.start + s.dur:
                return s
        return self.shots[-1]

    def frame(self, ctx, t):
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        if self.vertical:
            return self.frame_vertical(ctx, t)
        n = len(self.caption)
        size = 56
        y0 = SCENE_Y - 40 - (n - 1) * 70
        for i, line in enumerate(self.caption):
            text_center(ctx, line, W / 2, y0 + i * 70, size)
        s = self.shot_at(t)
        ctx.save()
        ctx.rectangle(0, SCENE_Y, W, SCENE_H)
        ctx.clip()
        ctx.translate(0, SCENE_Y)
        ctx.scale(SCALE, SCALE)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        SCENES[s.kind](ctx, self.world, t, t - s.start, s.kw)
        for t0, t1, fn in self.overlays:
            if t0 <= t < t1:
                fn(ctx, t - t0, t1 - t0)
        ctx.restore()

    def frame_vertical(self, ctx, t):
        s = self.shot_at(t)
        lt = t - s.start
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        if s.kw.get('screen'):
            SCENES[s.kind](ctx, self.world, t, lt, s.kw)
        elif self.layered and s.kind in LAYERED_SCENES:
            ctx.restore()
            self.frame_layered(ctx, s, t, lt)
            ctx.save()
        else:
            k = H / SH
            fx = s.kw.get('fx', SW / 2)
            fx = fx(lt) if callable(fx) else fx
            tx = min(0.0, max(W - SW * k, W / 2 - fx * k))
            ctx.translate(tx, s.kw.get('fy', 0) * k)
            ctx.scale(k, k)
            SCENES[s.kind](ctx, self.world, t, lt, s.kw)
            for t0, t1, fn in self.overlays:
                if t0 <= t < t1:
                    fn(ctx, t - t0, t1 - t0)
        ctx.restore()
        # title: outlined text near the top, safe from the Shorts UI
        if s.kw.get('screen') or s.kw.get('no_title'):
            return
        for i, line in enumerate(self.caption):
            outlined_text(ctx, line, W / 2, 230 + i * 84, 70)

    def _cam(self, ctx, fx, fy, zoom):
        k = H / SH * zoom
        tx = min(0.0, max(W - SW * k, W / 2 - fx * k))
        ty = (H - SH * k) / 2 + fy * (H / SH)
        ctx.translate(tx, ty)
        ctx.scale(k, k)

    def frame_layered(self, ctx, s, t, lt):
        """Multiplane render: blurred background, shaded characters with a soft drop shadow,
        effects on top, slow push-in with parallax, dust motes and a vignette."""
        global LAYER
        fx = s.kw.get('fx', SW / 2)
        fx = fx(lt) if callable(fx) else fx
        fy = s.kw.get('fy', 0)
        u = lt / s.dur
        push = s.kw.get('push', 0.06)
        par = s.kw.get('parallax', 0.5 if s.kind in ('face_scene', 'shocked_face', 'proud_end', 'spill') else 0.0)
        zoom_fg = 1 + push * u
        zoom_bg = 1 + push * u * (1 - par)
        surfs = {}
        for name in ('bg', 'mid', 'post'):
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            c = cairo.Context(surf)
            c.set_line_cap(cairo.LINE_CAP_BUTT)
            fxl = SW / 2 + (fx - SW / 2) * (1 - par * 0.3) if name == 'bg' else fx
            self._cam(c, fxl, fy, zoom_bg if name == 'bg' else zoom_fg)
            LAYER = name
            SCENES[s.kind](c, self.world, t, lt, s.kw)
            surf.flush()
            surfs[name] = surf
        LAYER = 'all'
        dof = s.kw.get('dof', 5)
        if dof > 0:
            _blur_surface(surfs['bg'], dof)
        ctx.set_source_surface(surfs['bg'], 0, 0)
        ctx.paint()
        sh = _shadow_surface(surfs['mid'], 16, 0.35)
        ctx.set_source_surface(sh, 16, 26)
        ctx.paint()
        ctx.set_source_surface(surfs['mid'], 0, 0)
        ctx.paint()
        ctx.set_source_surface(surfs['post'], 0, 0)
        ctx.paint()
        # dust motes drifting in front
        rnd = random.Random(99)
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ADD)
        for _ in range(26):
            x0, y0, sp, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(15, 45), rnd.uniform(2, 6)
            x = (x0 + math.sin(t * 0.6 + x0) * 30) % W
            y = (y0 - t * sp) % H
            g = cairo.RadialGradient(x, y, 0, x, y, r * 3)
            g.add_color_stop_rgba(0, 1, 0.97, 0.85, 0.35)
            g.add_color_stop_rgba(1, 1, 0.97, 0.85, 0)
            ctx.set_source(g)
            ctx.arc(x, y, r * 3, 0, 2 * math.pi)
            ctx.fill()
        ctx.restore()
        g = cairo.RadialGradient(W / 2, H * 0.45, W * 0.35, W / 2, H * 0.45, H * 0.75)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(1, 0.02, 0.0, 0.06, 0.45)
        ctx.set_source(g)
        ctx.paint()

    def render_still(self, t, path):
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        self.frame(cairo.Context(surf), t)
        surf.write_to_png(path)

    def render(self, out_path, audio, workdir):
        os.makedirs(workdir, exist_ok=True)
        wav = os.path.join(workdir, 'audio.wav')
        write_wav(wav, audio)
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        ctx = cairo.Context(surf)
        cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', f'{W}x{H}',
               '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
               '-pix_fmt', 'yuv420p', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '44100', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
               out_path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n = int(round(self.dur * FPS))
        for i in range(n):
            self.frame(ctx, i / FPS)
            surf.flush()
            p.stdin.write(bytes(surf.get_data()))
        p.stdin.close()
        p.wait()


def badge(text, color):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.2) * smooth((d - lt) / 0.2)
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(64)
        w = ctx.text_extents(text).x_advance
        rrect(ctx, 60, 50, w + 80, 100, 50)
        setc(ctx, hexc(color), 0.92 * a)
        ctx.fill()
        ctx.move_to(100, 123)
        setc(ctx, (1, 1, 1), a)
        ctx.show_text(text)
    return fn


def caption_in_scene(text, y=980, size=78):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.15) * smooth((d - lt) / 0.15)
        pop = 1 + 0.15 * (1 - smooth(lt / 0.2))
        ctx.save()
        ctx.translate(960, y)
        ctx.scale(pop, pop)
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(size)
        w = ctx.text_extents(text).x_advance
        rrect(ctx, -w / 2 - 40, -size - 10, w + 80, size + 50, 30)
        setc(ctx, (0, 0, 0), 0.6 * a)
        ctx.fill()
        ctx.move_to(-w / 2, 0)
        setc(ctx, (1, 1, 1), a)
        ctx.show_text(text)
        ctx.restore()
    return fn


# ------------------------------------------------------------------- audio
_nrng = np.random.default_rng(3)


def _sos(kind, f, order=2):
    f = np.atleast_1d(f) / (SR / 2)
    f = np.clip(f, 1e-4, 0.999)
    return signal.butter(order, f if len(f) > 1 else f[0], btype=kind, output='sos')


def lp(x, f, order=2):
    return signal.sosfilt(_sos('lowpass', f, order), x)


def hp(x, f, order=2):
    return signal.sosfilt(_sos('highpass', f, order), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos('bandpass', [lo, hi], order), x)


def noise(n):
    return _nrng.standard_normal(n)


def env_adsr(n, a=0.01, r=0.05):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


class Mixer:
    def __init__(self, dur):
        self.n = int(dur * SR) + SR
        self.L = np.zeros(self.n)
        self.R = np.zeros(self.n)

    def add(self, sig, t0, gain=1.0, pan=0.0):
        i = int(t0 * SR)
        if i >= self.n:
            return
        s = sig[:self.n - i] * gain
        if np.ndim(pan) == 0:
            pan = np.full(len(s), float(pan))
        else:
            pan = np.asarray(pan)[:len(s)]
        th = (pan + 1) * math.pi / 4
        self.L[i:i + len(s)] += s * np.cos(th)
        self.R[i:i + len(s)] += s * np.sin(th)

    def out(self, dur):
        n = int(dur * SR)
        st = np.stack([self.L[:n], self.R[:n]], 1)
        st = np.tanh(st * 1.1) / 1.1
        peak = np.max(np.abs(st)) + 1e-9
        return st / peak * 0.89


def write_wav(path, st):
    data = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def ambience(world, dur, inside=0.8):
    """Engine + tyre/road roar + wind, following the speed curve."""
    n = int(dur * SR) + SR
    ts = np.arange(n) / SR
    grid = np.arange(0, dur + 1, 1 / FPS)
    spd = np.interp(ts, grid, [world.speed(t) for t in grid])
    acc = np.gradient(np.interp(ts, grid, [world.speed(t) for t in grid])) * SR
    rpm = 850 + spd * 58 + np.clip(acc, 0, 5) * 120
    f0 = rpm / 30.0
    ph = 2 * np.pi * np.cumsum(f0) / SR
    eng = np.zeros(n)
    for k, a in enumerate([1.0, 0.6, 0.45, 0.25, 0.18, 0.12, 0.08], 1):
        eng += a * np.sin(k * ph + 0.3 * np.sin(ph * 0.5 + k))
    eng *= 1 + 0.25 * np.sin(ph * 0.5)
    eng = lp(eng, 380) * 0.20
    roar = lp(np.cumsum(noise(n)) * 0.02, 420, 2)
    roar -= lp(roar, 25)
    roar = roar / (np.std(roar) + 1e-9) * 0.16
    hiss = bp(noise(n), 900, 2600) * 0.025
    wind = bp(noise(n), 250, 900) * (0.6 + 0.4 * np.sin(ts * 0.7) ** 2) * 0.04
    k = np.clip(spd / 30, 0, 1.3)
    out = eng * (0.6 + 0.4 * k) + (roar + hiss) * k ** 1.3 + wind * k ** 2
    return lp(out, 2500 * inside + 600)


def tick(high=True):
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    e = np.exp(-t / 0.004)
    f = 3100 if high else 2200
    s = (bp(noise(n), 1500, 7000) * 0.6 + np.sin(2 * np.pi * f * t)) * e
    s += np.sin(2 * np.pi * (700 if high else 520) * t) * np.exp(-t / 0.008) * 0.6
    return s * 0.5


def click():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for t0, f, g in ((0.0, 2600, 1.0), (0.028, 1400, 0.8)):
        tt = np.clip(t - t0, 0, None)
        e = np.where(t >= t0, np.exp(-tt / 0.006), 0)
        s += (bp(noise(n), 1000, 6000) * 0.7 + np.sin(2 * np.pi * f * tt)) * e * g
        s += np.sin(2 * np.pi * 450 * tt) * np.where(t >= t0, np.exp(-tt / 0.012), 0) * 0.6 * g
    return s * 0.7


def horn(dur, doppler=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    fac = np.ones(n) if doppler is None else np.interp(t, np.linspace(0, dur, len(doppler)), doppler)
    s = np.zeros(n)
    for f in (410, 515):
        ph = 2 * np.pi * np.cumsum(f * fac * (1 + 0.004 * np.sin(2 * np.pi * 6 * t))) / SR
        for k in range(1, 14):
            s += np.sin(k * ph) / k
    s = np.tanh(s * 1.6)
    s = bp(s, 280, 3800)
    return s * env_adsr(n, 0.012, 0.06) * 0.55


def screech(dur, f=1150):
    n = int(dur * SR)
    t = np.arange(n) / SR
    wob = lp(noise(n), 6) * 900
    ph = 2 * np.pi * np.cumsum(f + wob + 80 * np.sin(2 * np.pi * 9 * t)) / SR
    tone = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)
    nz = bp(noise(n), 1400, 5200) * 0.8
    e = env_adsr(n, 0.04, 0.25) * (0.8 + 0.2 * lp(noise(n), 4) * 8)
    return (tone * 0.5 + nz) * np.clip(e, 0, 1.2) * 0.5


def whoosh(dur, peak=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    e = np.exp(-((t - dur * peak) / (dur * 0.18)) ** 2)
    nz = noise(n)
    lo = lp(nz, 500)
    hi = bp(nz, 700, 3500)
    s = lo * 0.8 + hi * e * 0.9
    return s * e * 0.6


def car_pass(dur, peak=0.5, f=95):
    """Engine of a vehicle passing close by (with doppler) + air whoosh."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (t - dur * peak) / (dur * 0.2)
    fac = 1 + 0.12 * (-np.tanh(x))
    ph = 2 * np.pi * np.cumsum(f * fac) / SR
    eng = sum(np.sin(k * ph) / k for k in range(1, 8))
    eng = lp(eng, 700)
    e = 1 / (1 + x ** 2)
    return (eng * 0.35 * e + whoosh(dur, peak)[:n])


def thud():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 58 * t) * np.exp(-t / 0.09) + bp(noise(n), 80, 600) * np.exp(-t / 0.03) * 0.6) * 0.8


def heartbeat(beats=3, bpm=110):
    per = 60 / bpm
    n = int((beats * per + 0.4) * SR)
    s = np.zeros(n)
    t1 = np.arange(int(0.25 * SR)) / SR
    th = np.sin(2 * np.pi * 50 * t1) * np.exp(-t1 / 0.07)
    for b in range(beats):
        for off, g in ((0, 1.0), (0.16, 0.7)):
            i = int((b * per + off) * SR)
            s[i:i + len(th)] += th[:n - i] * g
    return s * 0.9


def rewind_sfx(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 600 + 2600 * (t / dur) ** 0.6
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.15 * np.sin(2 * np.pi * 23 * t))) / SR
    s = np.sign(np.sin(ph)) * 0.25 + bp(noise(n), 1500, 6000) * 0.4
    s *= 0.6 + 0.4 * (np.sin(2 * np.pi * 31 * t) > 0)
    s = lp(s, 6000) * env_adsr(n, 0.05, 0.15) * 0.45
    return s


def brake_squeal(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (2900 + 60 * np.sin(2 * np.pi * 7 * t)) * t) * 0.3 + bp(noise(n), 2000, 5000) * 0.3
    return s * env_adsr(n, 0.05, 0.2) * 0.4


def rumble(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    e = np.sin(np.pi * t / dur) ** 2
    return lp(noise(n), 160, 4) * e * 2.2


def chime():
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k, f in enumerate((880, 1320)):
        tt = np.clip(t - k * 0.12, 0, None)
        s += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.18) * (t >= k * 0.12)
    return s * 0.35


def indicator(mixer, t0, t1, gain=0.5, pan=-0.2):
    t = t0
    hi = True
    while t < t1:
        mixer.add(tick(hi), t, gain, pan)
        hi = not hi
        t += 0.4


def _arr(surf):
    return np.ndarray((surf.get_height(), surf.get_width(), 4), np.uint8, surf.get_data())


def _blur_surface(surf, r):
    from PIL import Image, ImageFilter
    a = _arr(surf)
    h, w = a.shape[:2]
    img = Image.fromarray(a.copy()).resize((w // 2, h // 2), Image.BILINEAR)
    img = img.filter(ImageFilter.GaussianBlur(r / 2)).resize((w, h), Image.BILINEAR)
    a[:] = np.asarray(img)
    surf.mark_dirty()


def _shadow_surface(surf, r, strength):
    from PIL import Image, ImageFilter
    a = _arr(surf)
    h, w = a.shape[:2]
    al = Image.fromarray(a[..., 3].copy()).resize((w // 2, h // 2), Image.BILINEAR)
    al = al.filter(ImageFilter.GaussianBlur(r / 2)).resize((w, h), Image.BILINEAR)
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    o = _arr(out)
    o[..., 3] = (np.asarray(al) * strength).astype(np.uint8)
    out.mark_dirty()
    return out
