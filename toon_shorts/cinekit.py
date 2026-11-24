"""Cinematic look for the 2D+3D house style (cheap enough for fast renders).

  lighting      sun-lit faces for every solid()/lbox() (diffuse + sky term, warm key light), thinner outlines
  shadows       soft contact + cast shadows under vehicles (draw in draw_scene's overlay pass)
  post          golden-hour haze, sun glow + lens flare, colour grade (soft light), vignette, film grain,
                speed streaks
  cameras       shake(), heli() orbit, track() camera-car, tele() long-lens, crane()
Call enable_lighting() once after every drawing module is imported.
"""
import math
import random
import sys
import os

import cairo
import numpy as np

import engine
from engine import *
import toronto
import truckkit

SUN = None
SUN_COL = (1.0, 0.86, 0.66)


def set_sun(v):
    global SUN
    n = math.sqrt(sum(c * c for c in v))
    SUN = tuple(c / n for c in v)


set_sun((-0.62, 0.38, 0.69))      # low golden-hour sun, ahead-left


def lit(col, n, lift=0.0):
    if not isinstance(col, tuple) or len(col) != 3:
        return col
    d = max(0.0, n[0] * SUN[0] + n[1] * SUN[1] + n[2] * SUN[2])
    sky = 0.5 * (n[1] + 1.0)
    k = 0.6 + 0.16 * sky + 0.46 * d + lift
    r = col[0] * k * (1.0 + 0.10 * d) + 0.05 * d
    g = col[1] * k * (1.0 + 0.02 * d) + 0.03 * d
    b = col[2] * k * (1.0 - 0.08 * d) + 0.015 * sky
    return (min(1.0, r), min(1.0, g), min(1.0, b))


def _axes(Lf):
    o = Lf(0, 0, 0)
    ex = Lf(1, 0, 0)
    ez = Lf(0, 0, 1)
    a = (ex[0] - o[0], ex[1] - o[1], ex[2] - o[2])
    b = (ez[0] - o[0], ez[1] - o[1], ez[2] - o[2])
    return a, b


def _face_normals(Lf):
    a, b = _axes(Lf)
    return {'right': a, 'left': (-a[0], -a[1], -a[2]), 'front': b, 'back': (-b[0], -b[1], -b[2]), 'top': (0.0, 1.0, 0.0)}


_orig_solid = truckkit.solid
_orig_lbox = toronto.lbox
LW_K = 0.55


def lit_solid(ctx, view, Lf, bot, top, cols, lw):
    if view.ortho:
        return _orig_solid(ctx, view, Lf, bot, top, cols, lw)
    N = _face_normals(Lf)
    # sloped faces (greenhouse) look a little up
    tilt = {}
    for nm in ('front', 'back', 'left', 'right'):
        n = N[nm]
        tilt[nm] = (n[0] * 0.85, 0.5, n[2] * 0.85) if abs(top[0][1] - bot[0][1]) < 1.0 and top[0][1] > 1.0 else n
    tilt['top'] = N['top']
    c2 = {k: lit(v, tilt.get(k, (0, 1, 0))) for k, v in cols.items()}
    return _orig_solid(ctx, view, Lf, bot, top, c2, lw * LW_K)


def lit_lbox(ctx, view, Lf, h, x0, x1, y0, y1, z0, z1, cols, lw=3):
    if view.ortho:
        return _orig_lbox(ctx, view, Lf, h, x0, x1, y0, y1, z0, z1, cols, lw)
    N = _face_normals(Lf)
    c2 = {k: lit(v, N.get(k, (0, 1, 0))) for k, v in cols.items()}
    return _orig_lbox(ctx, view, Lf, h, x0, x1, y0, y1, z0, z1, c2, lw * LW_K)


def enable_lighting():
    here = os.path.dirname(os.path.abspath(__file__))
    for name, m in list(sys.modules.items()):
        f = getattr(m, '__file__', None) or ''
        if not f.startswith(here):
            continue
        if getattr(m, 'solid', None) is _orig_solid:
            m.solid = lit_solid
        if getattr(m, 'lbox', None) is _orig_lbox:
            m.lbox = lit_lbox


# ------------------------------------------------------------------ shadows
def _hull(pts):
    pts = sorted(set((round(p[0], 1), round(p[1], 1)) for p in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def shadow(ctx, view, x, z, h, z_lo, z_hi, half_w, hgt, alpha=0.42):
    """Ground shadow of a box footprint (local z from z_lo to z_hi, width 2*half_w) cast by the sun from height hgt."""
    if view.ortho:
        return
    ch, sh = math.cos(h), math.sin(h)
    P = lambda lx, lz: (x + lx * ch + lz * sh, 0.012, z - lx * sh + lz * ch)
    foot = [P(sx * half_w, zz) for sx in (-1, 1) for zz in (z_lo, z_hi)]
    ox, oz = -SUN[0] / SUN[1] * hgt * 0.75, -SUN[2] / SUN[1] * hgt * 0.75
    cast = [(p[0] + ox, p[1], p[2] + oz) for p in foot]
    sp = [view.pt(p) for p in foot + cast]
    if not all(sp):
        return
    hl = _hull(sp)
    poly(ctx, hl)
    setc(ctx, (0.08, 0.07, 0.16), alpha * 0.55)
    ctx.fill()
    cp = [view.pt(P(sx * (half_w * 0.95), zz)) for sx, zz in ((-1, z_lo), (1, z_lo), (1, z_hi), (-1, z_hi))]
    if all(cp):
        poly(ctx, cp)
        setc(ctx, (0.05, 0.04, 0.1), alpha)
        ctx.fill()


# ------------------------------------------------------------------ cameras
def shake(t, amp, freq=1.0, seed=0.0):
    """Smooth pseudo-noise in [-amp, amp] (sum of incommensurate sines)."""
    s = seed * 13.7
    return amp * (0.5 * math.sin(t * 7.3 * freq + s) + 0.3 * math.sin(t * 13.1 * freq + 1.7 + s) + 0.2 * math.sin(t * 23.9 * freq + 4.1 + s))


def look(pos, target, f, cx=960, cy=900, roll=0.0):
    from citykit import look_at
    return look_at(pos, target, f, cx, cy)


def heli(target, t, R, H, a0, w, f=1000, cy=900, lead=(0.0, 0.0, 0.0), amp=0.35):
    a = a0 + w * t
    tx, ty, tz = target
    pos = (tx + R * math.sin(a) + shake(t, amp, 0.4, 1), H + shake(t, amp * 0.6, 0.4, 2), tz - R * math.cos(a) + shake(t, amp, 0.4, 3))
    return look(pos, (tx + lead[0], ty + lead[1], tz + lead[2]), f, cy=cy)


# ------------------------------------------------------------------ post effects
_GRAIN = None


def _grain_surface():
    global _GRAIN
    if _GRAIN is None:
        n = 256
        rng = np.random.default_rng(7)
        a = (rng.integers(0, 255, (n, n))).astype(np.uint8)
        buf = np.zeros((n, n, 4), np.uint8)
        buf[..., 0] = a
        buf[..., 1] = a
        buf[..., 2] = a
        buf[..., 3] = 255
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, n, n)
        np.ndarray((n, n, 4), np.uint8, surf.get_data())[:] = buf
        surf.mark_dirty()
        _GRAIN = surf
    return _GRAIN


def sun_flare(ctx, view, Wd, Ht, strength=1.0):
    if view is None or view.ortho:
        return
    P = (view.pos[0] + SUN[0] * 6000, view.pos[1] + SUN[1] * 6000, view.pos[2] + SUN[2] * 6000)
    c = view.to_cam(P)
    if c[2] <= 0:
        return
    p = view.pt(P)
    if not p:
        return
    on = -300 < p[0] < Wd + 300 and -300 < p[1] < Ht + 300
    if not on:
        return
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_ADD)
    glow(ctx, p[0], p[1], 520, (1.0, 0.72, 0.38), 0.55 * strength, core=0.05)
    glow(ctx, p[0], p[1], 160, (1.0, 0.95, 0.8), 0.9 * strength, core=0.25)
    cx, cy = Wd / 2, Ht / 2
    for k, (u, r, col, a) in enumerate(((0.45, 60, (1.0, 0.6, 0.3), 0.18), (0.8, 30, (0.6, 0.8, 1.0), 0.2),
                                         (1.25, 110, (1.0, 0.5, 0.7), 0.1), (1.6, 46, (0.7, 1.0, 0.6), 0.14))):
        fx, fy = p[0] + (cx - p[0]) * u * 2, p[1] + (cy - p[1]) * u * 2
        glow(ctx, fx, fy, r, col, a * strength, core=0.6)
    # anamorphic streak
    g = cairo.LinearGradient(p[0] - 900, 0, p[0] + 900, 0)
    g.add_color_stop_rgba(0, 1.0, 0.7, 0.4, 0.0)
    g.add_color_stop_rgba(0.5, 1.0, 0.8, 0.55, 0.35 * strength)
    g.add_color_stop_rgba(1, 1.0, 0.7, 0.4, 0.0)
    ctx.set_source(g)
    ctx.rectangle(p[0] - 900, p[1] - 5, 1800, 10)
    ctx.fill()
    ctx.restore()


def warm_haze(ctx, view, Wd):
    if view is None or view.ortho:
        return
    hy = view.horizon()
    g = cairo.LinearGradient(0, hy - 260, 0, hy + 220)
    g.add_color_stop_rgba(0, 1.0, 0.78, 0.55, 0.0)
    g.add_color_stop_rgba(0.55, 1.0, 0.78, 0.55, 0.42)
    g.add_color_stop_rgba(1, 1.0, 0.78, 0.55, 0.0)
    ctx.set_source(g)
    ctx.rectangle(-50, hy - 260, Wd + 100, 480)
    ctx.fill()


def speed_streaks(ctx, t, amt, Wd, Ht, vp=None):
    if amt <= 0.02:
        return
    vx, vy = vp or (Wd / 2, Ht * 0.47)
    rnd = random.Random(int(t * 30))
    ctx.save()
    for k in range(int(26 * amt)):
        ang = rnd.uniform(0, 2 * math.pi)
        r0 = rnd.uniform(0.55, 0.85) * max(Wd, Ht)
        L_ = rnd.uniform(120, 420) * amt
        x0, y0 = vx + math.cos(ang) * r0, vy + math.sin(ang) * r0
        x1, y1 = vx + math.cos(ang) * (r0 + L_), vy + math.sin(ang) * (r0 + L_)
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        setc(ctx, (1, 1, 1), 0.16 * amt)
        ctx.set_line_width(rnd.uniform(2, 5))
        ctx.stroke()
    ctx.restore()


def grade(ctx, t, Wd, Ht, strength=1.0, vignette=0.55, grain=0.05):
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
    g = cairo.LinearGradient(0, 0, 0, Ht)
    g.add_color_stop_rgba(0, 1.0, 0.62, 0.32, 0.55 * strength)
    g.add_color_stop_rgba(0.55, 0.9, 0.55, 0.4, 0.25 * strength)
    g.add_color_stop_rgba(1, 0.1, 0.35, 0.5, 0.5 * strength)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    g = cairo.RadialGradient(Wd / 2, Ht / 2, min(Wd, Ht) * 0.38, Wd / 2, Ht / 2, max(Wd, Ht) * 0.78)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.03, 0.01, 0.05, vignette)
    ctx.set_source(g)
    ctx.paint()
    if grain > 0:
        gs = _grain_surface()
        rnd = random.Random(int(t * 30))
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_OVERLAY)
        pat = cairo.SurfacePattern(gs)
        pat.set_extend(cairo.EXTEND_REPEAT)
        m = cairo.Matrix(xx=0.5, yy=0.5, x0=rnd.uniform(0, 256), y0=rnd.uniform(0, 256))
        pat.set_matrix(m)
        ctx.set_source(pat)
        ctx.paint_with_alpha(grain)
        ctx.restore()


def whip(ctx, lt, d, Wd, Ht, length=0.18):
    """Whip-pan blur streak at the start / end of a shot."""
    for u in (lt, d - lt):
        if 0 <= u < length:
            a = 1 - u / length
            rnd = random.Random(int(lt * 60))
            for k in range(40):
                y = rnd.uniform(0, Ht)
                ctx.rectangle(0, y, Wd, rnd.uniform(8, 40) * a)
                setc(ctx, (1, 0.95, 0.9), 0.12 * a)
                ctx.fill()
