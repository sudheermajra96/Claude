"""Cartoon people for the house style: 3D occupants (drawn inside car glass) and 2D close-up heads."""
import math

import cairo
import numpy as np

from mkit import *


PEOPLE = {
    'hero': dict(skin=SKIN, hair=HAIR, top=JACKET, glasses=True, curly=True),
    'lady': dict(skin=hexc('#e8b48f'), hair=hexc('#5a2a1e'), top=hexc('#ff6b9d'), long=True, lips=hexc('#d63a5a'), fem=True, earrings=True, shades=True),
    'husb': dict(skin=hexc('#e0a982'), hair=hexc('#9a9aa2'), top=hexc('#2f6f73'), mustache=True),
    'grandpa': dict(skin=hexc('#e8b896'), hair=hexc('#eeeeef'), top=hexc('#9fc3e6'), mustache=True),
    'medic': dict(skin=hexc('#b07a55'), hair=hexc('#1d1613'), top=hexc('#1f4e8c')),
    'daughter': dict(skin=hexc('#e8b48f'), hair=hexc('#2a1a14'), top=hexc('#7a4fd0'), long=True, lips=hexc('#c2455e'), fem=True),
}


# ------------------------------------------------------------------ 3D occupants
def person3d(ctx, view, Lf, seat_x, seat_z, who, look, expr):
    P = PEOPLE[who]
    fx, fz = -math.sin(look), math.cos(look)            # facing (car-local)
    rx, rz = fz, -fx                                     # person's right
    hc = (seat_x, 1.14, seat_z)

    def W(dx, dy, dz):
        return Lf(hc[0] + dx, hc[1] + dy, hc[2] + dz)

    C = W(0, 0, 0)
    p, s = view.pt(C), view.scale(C)
    if not p or not s:
        return
    r = 0.115 * s
    lwid = max(1.0, s / 70)
    cam = view.pos
    fw = (W(fx, 0, fz)[0] - C[0], W(fx, 0, fz)[2] - C[2])
    vx, vz = cam[0] - C[0], cam[2] - C[2]
    vn = math.hypot(vx, vz) or 1
    dot = (fw[0] * vx + fw[1] * vz) / vn
    # shoulders
    sh = view.pt(W(0, -0.27, 0))
    if sh:
        ellipse(ctx, sh[0], sh[1], 0.25 * s, 0.15 * s)
        fill_stroke(ctx, P['top'], OUTL, lwid)
    # long hair behind the head (in front of it when we see her from behind)
    def long_hair():
        q = view.pt(W(-fx * 0.03, -0.08, -fz * 0.03))
        if q:
            ellipse(ctx, q[0], q[1], 0.15 * s, 0.2 * s)
            fill_stroke(ctx, P['hair'], OUTL, lwid)
    if P.get('long') and dot >= 0:
        long_hair()
    ellipse(ctx, p[0], p[1], r * 0.95, r)
    fill_stroke(ctx, P['skin'], OUTL, lwid)
    # hair cap, shifted to the back of the head
    q = view.pt(W(-fx * 0.04, 0.045, -fz * 0.04))
    if q:
        ellipse(ctx, q[0], q[1], r * 0.98, r * 0.78)
        setc(ctx, P['hair'])
        ctx.fill()
        if P.get('curly'):
            for a in np.linspace(-1.2, 1.2, 6):
                b = view.pt(W(-fx * 0.04 + rx * 0.09 * math.sin(a), 0.06 + 0.05 * math.cos(a), -fz * 0.04 + rz * 0.09 * math.sin(a)))
                if b:
                    ellipse(ctx, b[0], b[1], r * 0.32, r * 0.32)
                    setc(ctx, P['hair'])
                    ctx.fill()
    if P.get('long') and dot < 0:
        long_hair()
    if dot > 0.1:
        k = min(1.0, dot * 1.6)
        for sgn in (-1, 1):
            e = view.pt(W(fx * 0.105 + rx * 0.042 * sgn, 0.012, fz * 0.105 + rz * 0.042 * sgn))
            if not e:
                continue
            if expr == 'dreamy':
                heart(ctx, e[0], e[1] + 0.01 * s, 0.05 * s * (1 + 0.15 * math.sin(view.pos[2] * 3)), hexc('#ff2d55'))
            elif expr in ('laugh',):
                ctx.arc(e[0], e[1] + 0.01 * s, 0.022 * s, math.pi * 1.1, math.pi * 1.9)
                setc(ctx, OUTL)
                ctx.set_line_width(max(1, s / 120))
                ctx.stroke()
            else:
                rr = 0.016 * s * (1.7 if expr == 'shock' else 1.0)
                ellipse(ctx, e[0], e[1], rr * k, rr)
                setc(ctx, OUTL)
                ctx.fill()
            if P.get('glasses'):
                ellipse(ctx, e[0], e[1], 0.032 * s * k, 0.028 * s)
                setc(ctx, OUTL)
                ctx.set_line_width(max(1, s / 110))
                ctx.stroke()
        m = view.pt(W(fx * 0.1, -0.05, fz * 0.1))
        if m:
            if P.get('mustache'):
                ellipse(ctx, m[0], m[1] - 0.012 * s, 0.035 * s * k, 0.012 * s)
                setc(ctx, P['hair'])
                ctx.fill()
            if expr in ('dreamy', 'laugh', 'smile', 'smug'):
                ctx.arc(m[0], m[1] - 0.012 * s, 0.03 * s * k, 0.15 * math.pi, 0.85 * math.pi)
                setc(ctx, OUTL)
                ctx.set_line_width(max(1, s / 110))
                ctx.stroke()
            elif expr == 'shock':
                ellipse(ctx, m[0], m[1], 0.014 * s * k, 0.02 * s)
                setc(ctx, OUTL)
                ctx.fill()
            elif expr == 'annoyed':
                ctx.move_to(m[0] - 0.025 * s * k, m[1])
                ctx.line_to(m[0] + 0.025 * s * k, m[1])
                setc(ctx, OUTL)
                ctx.set_line_width(max(1, s / 110))
                ctx.stroke()


def heart(ctx, x, y, r, col, a=1.0):
    ctx.move_to(x, y + r)
    ctx.curve_to(x - 1.6 * r, y - 0.2 * r, x - 0.9 * r, y - 1.4 * r, x, y - 0.55 * r)
    ctx.curve_to(x + 0.9 * r, y - 1.4 * r, x + 1.6 * r, y - 0.2 * r, x, y + r)
    ctx.close_path()
    fill_stroke(ctx, col, OUTL, max(1, r * 0.12), a)


def head2d(ctx, cx, cy, r, who, expr, turn, t, tilt=0.0):
    """Cartoon head + shoulders. turn: -1 (faces screen left) .. 1 (faces screen right)."""
    P = PEOPLE[who]
    ox = turn * 0.36 * r
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(tilt)
    # torso
    ctx.move_to(-1.35 * r, 2.6 * r)
    ctx.curve_to(-1.35 * r, 1.3 * r, -0.8 * r, 0.95 * r, 0, 0.95 * r)
    ctx.curve_to(0.8 * r, 0.95 * r, 1.35 * r, 1.3 * r, 1.35 * r, 2.6 * r)
    ctx.close_path()
    fill_stroke(ctx, P['top'], OUTL, r * 0.03)
    if who == 'hero':
        poly(ctx, [(-0.25 * r, 0.97 * r), (0.25 * r, 0.97 * r), (0, 1.5 * r)])
        fill_stroke(ctx, hexc('#f2efe6'), OUTL, r * 0.025)
    ctx.rectangle(-0.28 * r, 0.6 * r, 0.56 * r, 0.42 * r)
    fill_stroke(ctx, mix(P['skin'], (0, 0, 0), 0.12), OUTL, r * 0.025)
    if P.get('long'):
        ctx.move_to(-0.95 * r - ox * 0.3, -0.3 * r)
        ctx.curve_to(-1.25 * r, 0.6 * r, -1.1 * r, 1.4 * r, -0.6 * r, 1.45 * r)
        ctx.line_to(0.6 * r, 1.45 * r)
        ctx.curve_to(1.1 * r, 1.4 * r, 1.25 * r, 0.6 * r, 0.95 * r - ox * 0.3, -0.3 * r)
        ctx.close_path()
        fill_stroke(ctx, P['hair'], OUTL, r * 0.03)
    # ears
    for sgn in (-1, 1):
        if sgn * turn > 0.6:
            continue
        ellipse(ctx, sgn * 0.93 * r - ox * 0.5, 0.08 * r, 0.17 * r, 0.24 * r)
        fill_stroke(ctx, P['skin'], OUTL, r * 0.025)
    ellipse(ctx, 0, 0, 0.92 * r, r)
    fill_stroke(ctx, P['skin'], OUTL, r * 0.03)
    # hair
    if P.get('curly'):
        hairs = [(-0.8, -0.55, 0.34), (-0.5, -0.85, 0.38), (-0.08, -0.98, 0.4), (0.37, -0.92, 0.38), (0.74, -0.65, 0.34),
                 (-0.92, -0.22, 0.22), (0.9, -0.25, 0.22), (0.15, -0.8, 0.36), (-0.32, -0.8, 0.36)]
        ctx.new_path()
        for hx, hy, rr in hairs:
            ctx.new_sub_path()
            ctx.arc((hx - turn * 0.12) * r, hy * r, rr * r, 0, 2 * math.pi)
        setc(ctx, P['hair'])
        ctx.fill_preserve()
        setc(ctx, OUTL)
        ctx.set_line_width(r * 0.025)
        ctx.stroke()
        for hx, hy, rr in hairs:
            ctx.arc((hx - turn * 0.12) * r, hy * r, rr * r - r * 0.015, 0, 2 * math.pi)
            setc(ctx, P['hair'])
            ctx.fill()
    elif P.get('long'):
        ctx.move_to(-0.95 * r, -0.05 * r)
        ctx.curve_to(-1.0 * r, -1.05 * r, 1.0 * r, -1.15 * r, 0.95 * r, -0.05 * r)
        ctx.curve_to(0.6 * r + ox, -0.55 * r, -0.1 * r + ox, -0.7 * r, -0.95 * r, -0.05 * r)
        ctx.close_path()
        fill_stroke(ctx, P['hair'], OUTL, r * 0.03)
        # sunglasses pushed up on the head
        for sgn in (-1, 1) if P.get('shades') else ():
            ellipse(ctx, sgn * 0.3 * r + ox * 0.6, -0.72 * r, 0.2 * r, 0.12 * r)
            fill_stroke(ctx, hexc('#1c1c22'), OUTL, r * 0.02)
    else:
        ctx.move_to(-0.93 * r, -0.05 * r)
        ctx.curve_to(-0.95 * r, -0.85 * r, -0.4 * r, -1.05 * r, 0, -1.0 * r)
        ctx.curve_to(0.4 * r, -1.05 * r, 0.95 * r, -0.85 * r, 0.93 * r, -0.05 * r)
        ctx.curve_to(0.8 * r, -0.5 * r, 0.5 * r, -0.62 * r, 0.3 * r, -0.62 * r)
        ctx.curve_to(0.0, -0.55 * r, -0.4 * r, -0.62 * r, -0.93 * r, -0.05 * r)
        ctx.close_path()
        fill_stroke(ctx, P['hair'], OUTL, r * 0.03)
    # eyes
    for sgn in (-1, 1):
        k = 1 - 0.35 * max(0.0, -sgn * turn)          # the far eye is narrower
        ex_, ey_ = sgn * 0.36 * r * (1 - 0.25 * abs(turn)) + ox, 0.0
        if expr == 'dreamy':
            ellipse(ctx, ex_, ey_, 0.2 * r * k, 0.21 * r)
            fill_stroke(ctx, (1, 1, 1), OUTL, r * 0.025)
            heart(ctx, ex_, ey_ + 0.02 * r, 0.14 * r * (1 + 0.15 * math.sin(t * 10)), hexc('#ff2d55'))
        elif expr in ('closed', 'relieved'):
            ctx.arc(ex_, ey_ - 0.02 * r, 0.13 * r * k, 0.15 * math.pi, 0.85 * math.pi)
            setc(ctx, OUTL)
            ctx.set_line_width(r * 0.05)
            ctx.stroke()
        elif expr in ('laugh',):
            ctx.arc(ex_, ey_ + 0.05 * r, 0.13 * r * k, 1.1 * math.pi, 1.9 * math.pi)
            setc(ctx, OUTL)
            ctx.set_line_width(r * 0.05)
            ctx.stroke()
        else:
            big = 1.35 if expr == 'shock' else 1.0
            lid = 0.55 if expr in ('annoyed', 'smug') else (0.8 if expr == 'focus' else 1.0)
            ellipse(ctx, ex_, ey_, 0.18 * r * k * big, 0.2 * r * big * lid)
            fill_stroke(ctx, (1, 1, 1), OUTL, r * 0.025)
            pr = 0.08 * r * (0.7 if expr == 'shock' else 1.0)
            ellipse(ctx, ex_ + turn * 0.07 * r, ey_ + 0.02 * r, pr * k, pr * min(1, lid + 0.2))
            setc(ctx, OUTL)
            ctx.fill()
            ellipse(ctx, ex_ + turn * 0.07 * r + pr * 0.35, ey_ - pr * 0.3, pr * 0.3, pr * 0.3)
            setc(ctx, (1, 1, 1))
            ctx.fill()
            if lid < 1:
                ctx.rectangle(ex_ - 0.22 * r, ey_ - 0.26 * r, 0.44 * r, 0.16 * r)
                setc(ctx, P['skin'])
                ctx.fill()
                ctx.move_to(ex_ - 0.19 * r * k, ey_ - 0.1 * r)
                ctx.line_to(ex_ + 0.19 * r * k, ey_ - 0.1 * r)
                setc(ctx, OUTL)
                ctx.set_line_width(r * 0.03)
                ctx.stroke()
        if P.get('fem') and expr not in ('laugh', 'closed', 'relieved'):
            for j in range(3):
                a = -math.pi / 2 + (j - 1) * 0.45 + sgn * 0.5
                ctx.move_to(ex_ + math.cos(a) * 0.17 * r * k, ey_ + math.sin(a) * 0.19 * r)
                ctx.line_to(ex_ + math.cos(a) * 0.27 * r * k, ey_ + math.sin(a) * 0.29 * r)
            setc(ctx, OUTL)
            ctx.set_line_width(r * 0.025)
            ctx.stroke()
        if P.get('glasses'):
            rrect(ctx, ex_ - 0.3 * r * k, ey_ - 0.25 * r, 0.6 * r * k, 0.5 * r, 0.16 * r)
            setc(ctx, OUTL)
            ctx.set_line_width(r * 0.045)
            ctx.stroke()
        # brows
        by = ey_ - 0.36 * r - (0.12 * r if expr == 'shock' else 0)
        tl = 0.1 * r if expr in ('annoyed', 'focus') else (-0.05 * r if expr in ('dreamy', 'smile') else (-0.11 * r if expr in ('worried', 'relieved') else 0))
        ctx.move_to(ex_ - 0.2 * r * k, by - sgn * tl * (-1))
        ctx.line_to(ex_ + 0.2 * r * k, by + sgn * tl * (-1))
        setc(ctx, P['hair'] if not P.get('fem') else hexc('#3a1a12'))
        ctx.set_line_width(r * (0.08 if not P.get('fem') else 0.05))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    if P.get('glasses'):
        ctx.move_to(-0.06 * r + ox, -0.02 * r)
        ctx.line_to(0.06 * r + ox, -0.02 * r)
        setc(ctx, OUTL)
        ctx.set_line_width(r * 0.045)
        ctx.stroke()
    # nose
    ctx.move_to(ox * 1.25 - 0.02 * r, 0.12 * r)
    ctx.curve_to(ox * 1.25 - 0.1 * r, 0.3 * r, ox * 1.25 + 0.04 * r, 0.34 * r, ox * 1.25 + 0.09 * r, 0.3 * r)
    setc(ctx, mix(P['skin'], (0, 0, 0), 0.25))
    ctx.set_line_width(r * 0.03)
    ctx.stroke()
    if expr in ('dreamy', 'smile', 'laugh'):
        for sgn in (-1, 1):
            ellipse(ctx, sgn * 0.5 * r + ox * 0.8, 0.3 * r, 0.14 * r, 0.08 * r)
            setc(ctx, hexc('#ff8aa0'), 0.55)
            ctx.fill()
    # mustache
    mx, my = ox * 1.1, 0.5 * r
    if P.get('mustache'):
        ctx.move_to(mx - 0.3 * r, my - 0.04 * r)
        ctx.curve_to(mx - 0.15 * r, my - 0.2 * r, mx + 0.15 * r, my - 0.2 * r, mx + 0.3 * r, my - 0.04 * r)
        ctx.curve_to(mx + 0.1 * r, my - 0.08 * r, mx - 0.1 * r, my - 0.08 * r, mx - 0.3 * r, my - 0.04 * r)
        fill_stroke(ctx, P['hair'], OUTL, r * 0.02)
    lips = P.get('lips', OUTL)
    ctx.set_line_width(r * 0.04)
    if expr == 'dreamy':                    # goofy grin
        ctx.move_to(mx - 0.38 * r, my - 0.05 * r)
        ctx.curve_to(mx - 0.25 * r, my + 0.3 * r, mx + 0.25 * r, my + 0.3 * r, mx + 0.38 * r, my - 0.05 * r)
        ctx.close_path()
        fill_stroke(ctx, hexc('#7a1f25'), OUTL, r * 0.03)
        ctx.rectangle(mx - 0.28 * r, my - 0.04 * r, 0.56 * r, 0.08 * r)
        setc(ctx, (1, 1, 1))
        ctx.fill()
    elif expr in ('smile', 'smug', 'relieved'):
        ctx.arc(mx, my - 0.16 * r, 0.26 * r, 0.3 * math.pi, 0.7 * math.pi)
        setc(ctx, lips)
        ctx.stroke()
    elif expr == 'laugh':
        ctx.move_to(mx - 0.26 * r, my - 0.05 * r)
        ctx.curve_to(mx - 0.2 * r, my + 0.32 * r, mx + 0.2 * r, my + 0.32 * r, mx + 0.26 * r, my - 0.05 * r)
        ctx.close_path()
        fill_stroke(ctx, hexc('#7a1f25'), lips if P.get('fem') else OUTL, r * 0.035)
    elif expr == 'whistle':
        ellipse(ctx, mx + 0.04 * r, my + 0.02 * r, 0.08 * r, 0.1 * r)
        fill_stroke(ctx, hexc('#5e1419'), OUTL, r * 0.03)
        for i in range(3):
            ph = (t * 0.7 + i / 3) % 1
            nx, ny = mx + 0.5 * r + ph * 1.2 * r, my - 0.2 * r - ph * 1.6 * r
            a_ = math.sin(math.pi * ph)
            for col, lw in ((OUTL, 0.07 * r), ((1, 1, 1), 0.035 * r)):
                ctx.move_to(nx + 0.11 * r, ny - 0.02 * r)
                ctx.line_to(nx + 0.11 * r, ny - 0.4 * r)
                ctx.line_to(nx + 0.27 * r, ny - 0.32 * r)
                setc(ctx, col, a_)
                ctx.set_line_width(lw)
                ctx.stroke()
            ellipse(ctx, nx, ny, 0.13 * r, 0.1 * r, -0.4)
            fill_stroke(ctx, (1, 1, 1), OUTL, 0.025 * r, a_)
    elif expr == 'shock':
        ellipse(ctx, mx, my + 0.08 * r, 0.12 * r, 0.17 * r)
        fill_stroke(ctx, hexc('#5e1419'), OUTL, r * 0.03)
    elif expr in ('annoyed', 'worried'):
        ctx.arc(mx, my + 0.22 * r, 0.22 * r, 1.25 * math.pi, 1.75 * math.pi)
        setc(ctx, OUTL)
        ctx.stroke()
    else:
        ctx.move_to(mx - 0.15 * r, my)
        ctx.line_to(mx + 0.15 * r, my)
        setc(ctx, lips)
        ctx.stroke()
    if P.get('earrings'):
        for sgn in (-1, 1):
            if sgn * turn > 0.6:
                continue
            ellipse(ctx, sgn * 0.95 * r - ox * 0.5, 0.32 * r, 0.06 * r, 0.06 * r)
            fill_stroke(ctx, hexc('#f2c230'), OUTL, r * 0.015)
    ctx.restore()


