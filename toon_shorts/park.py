"""Toronto waterfront park (multi-angle 2D house style): bench, promenade, lake, CN Tower skyline,
our hero (billboard, front/back views) and an original woman character (seated), top-view analysis.

World: +Z = north (toward the city / CN Tower), +X = east, Y up. Bench at the origin, facing south (-Z).
Promenade along X at Z -4..-1, lake south of Z = -12.
"""
import math
import random

import cairo
import numpy as np

from toronto import *          # TCam, skyline, tree3, fill_poly, gquad, kit + engine helpers
import toronto
import life
import psych

HER_HAIR = hexc('#7a3b2a')
HER_SKIN = hexc('#f0c29a')
HER_JACKET = hexc('#5a7d4f')
HER_JEANS = hexc('#3b5f9a')
HER_POS = (-0.3, 0.25)          # where she sits (x, z)
PATH_COL = hexc('#d9cdb4')
BENCH_WOOD = hexc('#a8673f')


# ------------------------------------------------------------- her drawing
HER_EXPR = {
    'read':     dict(eo=0.55, look=(0, 0.6), brow=0.0, tilt=0.0, mouth='smile_s'),
    'startled': dict(eo=1.25, look=(0, 0), brow=0.9, tilt=-0.3, mouth='o'),
    'unsure':   dict(eo=0.9, look=(0.3, 0), brow=0.35, tilt=-0.55, mouth='flat'),
    'smile':    dict(eo=0.95, look=(0.25, 0), brow=0.2, tilt=0.0, mouth='open_smile'),
    'laugh':    dict(eo=0.0, look=(0, 0), brow=0.3, tilt=0.0, mouth='laugh'),
}


def her_head(ctx, cx, cy, k, expr='read', t=0.0, rot=0.0):
    ex = HER_EXPR[expr]
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(k, k)
    # back hair (long, wavy ends)
    ctx.move_to(-250, -100)
    ctx.curve_to(-330, 80, -300, 300, -280, 420)
    for i in range(7):
        x0 = -280 + i * 80
        ctx.curve_to(x0 + 20, 460, x0 + 60, 380, x0 + 80, 430)
    ctx.curve_to(300, 300, 330, 80, 250, -100)
    ctx.curve_to(220, -320, -220, -320, -250, -100)
    ctx.close_path()
    fill_stroke(ctx, HER_HAIR, OUTL, 7)
    # face
    ellipse(ctx, 0, 20, 215, 250)
    fill_stroke(ctx, HER_SKIN, OUTL, 7)
    # earrings
    for s in (-1, 1):
        ctx.new_sub_path()
        ctx.arc(s * 212, 150, 22, 0, 2 * math.pi)
        setc(ctx, hexc('#e8b830'))
        ctx.set_line_width(7)
        ctx.stroke()
    # blush
    for s in (-1, 1):
        ellipse(ctx, s * 125, 125, 45, 26)
        setc(ctx, hexc('#ff8a8a'), 0.35)
        ctx.fill()
    # eyes
    blink = 1.0
    if ((t + 1.3) % 3.7) < 0.12 and 0.3 < ex['eo'] < 1.2:
        blink = 0.1
    eo = ex['eo'] * blink
    lx, ly = ex['look']
    for s in (-1, 1):
        x, y = s * 85, 40
        if eo < 0.05:
            ctx.move_to(x - 40, y + 8)
            ctx.curve_to(x - 20, y - 20, x + 20, y - 20, x + 40, y + 8)
            setc(ctx, OUTL)
            ctx.set_line_width(9)
            ctx.stroke()
        else:
            ellipse(ctx, x, y, 46, 42 * eo)
            fill_stroke(ctx, (1, 1, 1), OUTL, 4)
            ctx.save()
            ellipse(ctx, x, y, 46, 42 * eo)
            ctx.clip()
            ellipse(ctx, x + lx * 14, y + ly * 14, 23, 23)
            setc(ctx, hexc('#6b4a2f'))
            ctx.fill()
            ellipse(ctx, x + lx * 14, y + ly * 14, 12, 12)
            setc(ctx, OUTL)
            ctx.fill()
            ellipse(ctx, x + lx * 14 + 8, y + ly * 14 - 8, 6, 6)
            setc(ctx, (1, 1, 1))
            ctx.fill()
            ctx.restore()
            # upper lash line + flicks
            ctx.move_to(x - 48, y - 42 * eo * 0.2)
            ctx.curve_to(x - 30, y - 44 * eo - 6, x + 30, y - 44 * eo - 6, x + 50, y - 42 * eo * 0.3)
            setc(ctx, OUTL)
            ctx.set_line_width(8)
            ctx.stroke()
            ctx.move_to(x + s * 44, y - 30 * eo)
            ctx.line_to(x + s * 64, y - 44 * eo - 6)
            ctx.set_line_width(6)
            ctx.stroke()
        by = y - 78 - ex['brow'] * 32
        tl = ex['tilt'] * 22
        ctx.move_to(x - 48, by + s * tl + 6)
        ctx.curve_to(x - 15, by + s * tl - 8, x + 15, by - s * tl - 8, x + 48, by - s * tl + 2)
        setc(ctx, mix(HER_HAIR, (0, 0, 0), 0.25))
        ctx.set_line_width(12)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    # nose
    ctx.move_to(-6, 95)
    ctx.curve_to(-16, 120, 6, 128, 14, 118)
    setc(ctx, mix(HER_SKIN, (0, 0, 0), 0.25))
    ctx.set_line_width(6)
    ctx.stroke()
    # mouth
    m, my = ex['mouth'], 185
    lip = hexc('#d9534f')
    if m == 'smile_s':
        ctx.move_to(-38, my - 4)
        ctx.curve_to(-15, my + 16, 15, my + 16, 38, my - 4)
        setc(ctx, lip)
        ctx.set_line_width(8)
        ctx.stroke()
    elif m == 'flat':
        ctx.move_to(-35, my + 4)
        ctx.curve_to(-10, my - 2, 10, my + 2, 35, my - 2)
        setc(ctx, lip)
        ctx.set_line_width(8)
        ctx.stroke()
    elif m == 'o':
        ellipse(ctx, 0, my + 8, 26, 34)
        fill_stroke(ctx, hexc('#7a1f25'), lip, 6)
    elif m in ('open_smile', 'laugh'):
        h_ = 50 if m == 'open_smile' else 80
        ctx.move_to(-70, my - 12)
        ctx.curve_to(-50, my + h_, 50, my + h_, 70, my - 12)
        ctx.curve_to(30, my - 2, -30, my - 2, -70, my - 12)
        fill_stroke(ctx, hexc('#7a1f25'), lip, 6)
        ctx.save()
        ctx.move_to(-70, my - 12)
        ctx.curve_to(-50, my + h_, 50, my + h_, 70, my - 12)
        ctx.close_path()
        ctx.clip()
        ctx.rectangle(-70, my - 14, 140, 18)
        setc(ctx, (1, 1, 1))
        ctx.fill()
        ctx.restore()
    # front hair: side part with a big sweep to the left
    ctx.move_to(60, -262)
    ctx.curve_to(-120, -260, -240, -150, -238, 40)
    ctx.curve_to(-236, 120, -226, 170, -214, 210)
    ctx.curve_to(-190, 90, -170, -40, -40, -150)
    ctx.curve_to(10, -190, 50, -205, 60, -262)
    ctx.close_path()
    fill_stroke(ctx, HER_HAIR, OUTL, 6)
    ctx.move_to(60, -262)
    ctx.curve_to(170, -250, 240, -150, 228, 10)
    ctx.curve_to(200, -80, 150, -150, 80, -190)
    ctx.close_path()
    fill_stroke(ctx, HER_HAIR, OUTL, 6)
    ctx.move_to(-20, -235)
    ctx.curve_to(-120, -220, -190, -140, -200, -40)
    setc(ctx, mix(HER_HAIR, (1, 1, 1), 0.25))
    ctx.set_line_width(9)
    ctx.stroke()
    ctx.restore()


def her_seated(ctx, x, y, k, t, expr='read', pose='read', lean=0.0):
    """(x, y) = seat point between her hips; k = same scale units as life.person."""
    # lower legs + shoes
    for s in (-1, 1):
        kx = x + s * 55 * k
        hose(ctx, (kx, y + 55 * k), (kx + s * 6 * k, y + 195 * k), 0, 58 * k, HER_JEANS)
        ellipse(ctx, kx + s * 14 * k, y + 205 * k, 46 * k, 22 * k)
        fill_stroke(ctx, (0.97, 0.97, 0.97), OUTL, 4)
    # thighs (coming toward us, foreshortened)
    for s in (-1, 1):
        rrect(ctx, x + s * 55 * k - 40 * k, y - 15 * k, 80 * k, 85 * k, 34 * k)
        fill_stroke(ctx, HER_JEANS, OUTL, 5)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(lean)
    # torso: white tee + open olive jacket
    ctx.move_to(-92 * k, 10 * k)
    ctx.curve_to(-104 * k, -110 * k, -100 * k, -205 * k, 0, -215 * k)
    ctx.curve_to(100 * k, -205 * k, 104 * k, -110 * k, 92 * k, 10 * k)
    ctx.close_path()
    fill_stroke(ctx, HER_JACKET, OUTL, 5)
    poly(ctx, [(-40 * k, -212 * k), (40 * k, -212 * k), (32 * k, 8 * k), (-32 * k, 8 * k)])
    fill_stroke(ctx, (0.98, 0.98, 0.96), OUTL, 4)
    ctx.rectangle(-26 * k, -255 * k, 52 * k, 50 * k)
    fill_stroke(ctx, mix(HER_SKIN, (0, 0, 0), 0.12), OUTL, 4)
    # arms + hands
    if pose == 'read':
        hands = [(-60 * k, -95 * k), (60 * k, -95 * k)]
    elif pose == 'wave':
        hands = [(-70 * k, -20 * k), (120 * k, -300 * k + math.sin(t * 12) * 12 * k)]
    elif pose == 'shrug':
        hands = [(-150 * k, -150 * k), (150 * k, -150 * k)]
    else:
        hands = [(-55 * k, -10 * k), (55 * k, -10 * k)]
    for i, s in enumerate((-1, 1)):
        hose(ctx, (s * 85 * k, -195 * k), hands[i], s * 30 * k, 46 * k, HER_JACKET)
    if pose == 'read':
        rrect(ctx, -105 * k, -190 * k, 210 * k, 140 * k, 8 * k)
        fill_stroke(ctx, hexc('#2f6f9f'), OUTL, 4)
        ctx.rectangle(-75 * k, -165 * k, 150 * k, 14 * k)
        ctx.rectangle(-60 * k, -140 * k, 120 * k, 10 * k)
        setc(ctx, hexc('#f2c230'))
        ctx.fill()
    elif pose == 'show':
        rrect(ctx, -60 * k, -170 * k, 120 * k, 160 * k, 8 * k)
        fill_stroke(ctx, hexc('#2f6f9f'), OUTL, 4)
        ctx.rectangle(-40 * k, -140 * k, 80 * k, 12 * k)
        setc(ctx, hexc('#f2c230'))
        ctx.fill()
    for hx, hy in hands:
        ellipse(ctx, hx, hy, 24 * k, 22 * k)
        fill_stroke(ctx, HER_SKIN, OUTL, 4)
    her_head(ctx, 0, -360 * k, 0.5 * k, expr, t, -lean * 0.5)
    ctx.restore()


def her_back(ctx, x, y, k):
    """Back of her head and shoulders (big foreground for over-the-shoulder shots). (x, y) = neck base."""
    ctx.move_to(x - 300 * k, y + 400 * k)
    ctx.curve_to(x - 300 * k, y + 60 * k, x - 200 * k, y, x, y)
    ctx.curve_to(x + 200 * k, y, x + 300 * k, y + 60 * k, x + 300 * k, y + 400 * k)
    ctx.close_path()
    fill_stroke(ctx, HER_JACKET, OUTL, 6)
    ctx.move_to(x - 230 * k, y + 120 * k)
    ctx.curve_to(x - 300 * k, y - 120 * k, x - 260 * k, y - 470 * k, x, y - 480 * k)
    ctx.curve_to(x + 260 * k, y - 470 * k, x + 300 * k, y - 120 * k, x + 230 * k, y + 120 * k)
    for i in range(6):
        x0 = x + 230 * k - i * 92 * k
        ctx.curve_to(x0 - 20 * k, y + 170 * k, x0 - 70 * k, y + 90 * k, x0 - 92 * k, y + 140 * k)
    ctx.close_path()
    fill_stroke(ctx, HER_HAIR, OUTL, 6)
    for i in range(5):
        ctx.move_to(x - 160 * k + i * 80 * k, y - 380 * k)
        ctx.curve_to(x - 190 * k + i * 80 * k, y - 200 * k, x - 130 * k + i * 80 * k, y - 60 * k, x - 160 * k + i * 80 * k, y + 60 * k)
    setc(ctx, mix(HER_HAIR, (1, 1, 1), 0.2))
    ctx.set_line_width(7 * max(k, 0.5))
    ctx.stroke()


def hero_back(ctx, x, y, k, t, walking=True, hunch=0.0):
    """Our hero seen from behind (curly hair, mustard jacket). (x, y) = pelvis."""
    feet, hands, bob = psych.walk_pose(x, y, k, t, 1.4, walking)
    y -= bob
    for i, s in enumerate((-1, 1)):
        hose(ctx, (x + s * 45 * k, y), feet[i], s * 10 * k, 64 * k, life.PANTS)
        ellipse(ctx, feet[i][0] + s * 22 * k, feet[i][1] + 10 * k, 52 * k, 26 * k)
        fill_stroke(ctx, life.SHOE, OUTL, 5)
    ctx.move_to(x - 95 * k, y + 10 * k)
    ctx.curve_to(x - 110 * k, y - 120 * k, x - 105 * k, y - 230 * k, x, y - 240 * k)
    ctx.curve_to(x + 105 * k, y - 230 * k, x + 110 * k, y - 120 * k, x + 95 * k, y + 10 * k)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    ctx.move_to(x, y - 200 * k)
    ctx.line_to(x, y)
    setc(ctx, JACKET_SH)
    ctx.set_line_width(5)
    ctx.stroke()
    for i, s in enumerate((-1, 1)):
        hx, hy = hands[i]
        if hunch > 0.5:
            hx, hy = x + s * 70 * k, y + 5 * k
        hose(ctx, (x + s * 85 * k, y - 210 * k), (hx, hy), -s * 30 * k, 50 * k, JACKET)
        if hunch <= 0.5:
            ellipse(ctx, hx, hy, 30 * k, 30 * k)
            fill_stroke(ctx, SKIN, OUTL, 5)
    hy_ = y - 230 * k - 120 * k + hunch * 25 * k
    ctx.rectangle(x - 40 * k, y - 270 * k, 80 * k, 50 * k)
    fill_stroke(ctx, SKIN_SH, OUTL, 4)
    for s in (-1, 1):
        ellipse(ctx, x + s * 118 * k, hy_ + 15 * k, 24 * k, 31 * k)
        fill_stroke(ctx, SKIN, OUTL, 4)
    ellipse(ctx, x, hy_, 124 * k, 136 * k)
    fill_stroke(ctx, HAIR, OUTL, 6)
    for hx, hy2, r in ((-80, -60, 50), (0, -95, 55), (80, -60, 50), (-95, 20, 40), (95, 20, 40), (-40, 30, 45), (40, 30, 45)):
        ellipse(ctx, x + hx * k, hy_ + hy2 * k, r * k, r * k)
        setc(ctx, mix(HAIR, (1, 1, 1), 0.08))
        ctx.fill()
    ctx.move_to(x - 105 * k, hy_ - 10 * k)
    ctx.line_to(x - 95 * k, hy_ + 10 * k)
    setc(ctx, OUTL)
    ctx.set_line_width(5)
    ctx.stroke()


def hero_front_pose(ctx, x, y, k, t, expr, walking, mood, look=(0, 0), wave=0.0):
    """Front billboard of our hero. mood: 'nervous' (hunched, hands in pockets) or 'confident'."""
    feet, hands, bob = psych.walk_pose(x, y, k, t, 1.4 if mood == 'confident' else 1.0, walking)
    y -= bob
    if mood == 'nervous':
        hands = [(x - 70 * k, y + 5 * k), (x + 70 * k, y + 5 * k)]
        life.person(ctx, x, y, k, t, expr, lean=0.0, hands=hands, feet=feet, head_rot=0.12,
                    look=(0, 0.8), hand_bend=(10, -10))
    else:
        if wave > 0:
            hands = [hands[0], (x + 170 * k, y - 330 * k + math.sin(t * 12) * 15 * k)]
        life.person(ctx, x, y, k, t, expr, lean=0.0, hands=hands, feet=feet, look=look,
                    hand_bend=(40, -60 if wave > 0 else -40))


# ------------------------------------------------------------- park world
_rp = random.Random(9)
PTREES = [(x, z, 0.9 + _rp.uniform(0, 0.5)) for x, z in
          [(-9, 6), (9, 7), (13, 12), (-14, 11), (17, 5), (-18, 4), (11, 16),
           (-12, 17), (14, -9), (-13, -9), (21, 10), (-22, 12), (-7, 3), (7, 2.5)]]
LAMPS = [(-6, -0.6), (7, -0.6)]


def bench(ctx, view):
    Lf = lambda a, b, c: (a, b, c)
    wood, wood_d = BENCH_WOOD, mix(BENCH_WOOD, (0, 0, 0), 0.25)
    metal = hexc('#3a3d48')
    if view.ortho:
        fill_poly(ctx, view, [(-1.05, 0, -0.05), (1.05, 0, -0.05), (1.05, 0, 0.6), (-1.05, 0, 0.6)], wood, OUTL, 4)
        return
    for lx in (-0.95, 0.95):
        lbox(ctx, view, Lf, 0.0, lx - 0.05, lx + 0.05, 0, 0.45, 0.0, 0.5,
             {k: metal for k in ('front', 'back', 'left', 'right', 'top')}, 2)
        lbox(ctx, view, Lf, 0.0, lx - 0.05, lx + 0.05, 0.45, 0.95, 0.5, 0.58,
             {k: metal for k in ('front', 'back', 'left', 'right', 'top')}, 2)
    lbox(ctx, view, Lf, 0.0, -1.05, 1.05, 0.42, 0.48, 0.0, 0.52,
         {'front': wood_d, 'back': wood_d, 'left': wood_d, 'right': wood_d, 'top': wood}, 2)
    lbox(ctx, view, Lf, 0.0, -1.05, 1.05, 0.6, 0.95, 0.5, 0.58,
         {'front': wood, 'back': wood_d, 'left': wood_d, 'right': wood_d, 'top': wood}, 2)


def lamp(ctx, view, x, z):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 8, 8)
        setc(ctx, hexc('#3a3d48'))
        ctx.fill()
        return
    b, tp = view.pt((x, 0, z)), view.pt((x, 3.6, z))
    s = view.scale((x, 0, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.05 * s, tp[1], 0.1 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#3a3d48'), OUTL, 2)
    ellipse(ctx, tp[0], tp[1], 0.22 * s, 0.16 * s)
    fill_stroke(ctx, hexc('#fff3c4'), OUTL, 2)


class Actor:
    """Hero position/facing over time from waypoints [(t, x, z), ...]."""

    def __init__(self, way):
        self.way = way
        self.X = Key([(t, x) for t, x, z in way], 'lin')
        self.Z = Key([(t, z) for t, x, z in way], 'lin')

    def pos(self, t):
        return self.X(t), self.Z(t)

    def vel(self, t):
        a, b = self.pos(t - 0.1), self.pos(t + 0.1)
        return (b[0] - a[0]) / 0.2, (b[1] - a[1]) / 0.2

    def walking(self, t):
        vx, vz = self.vel(t)
        return math.hypot(vx, vz) > 0.25

    def facing(self, t, fallback):
        vx, vz = self.vel(t)
        if math.hypot(vx, vz) > 0.25:
            return math.atan2(vx, vz)
        return fallback


def draw_park(ctx, view, t, st, her=True, hero=True):
    """st: dict with hero (Actor), mood, hero_expr, her_expr, her_pose, her_lean, face_her (bool)."""
    if not view.ortho:
        hy = view.horizon()
        g = cairo.LinearGradient(0, hy - 700, 0, hy)
        g.add_color_stop_rgb(0, *hexc('#5fb4f2'))
        g.add_color_stop_rgb(1, *hexc('#d6f0ff'))
        ctx.set_source(g)
        ctx.rectangle(-50, -50, SW + 100, hy + 52)
        ctx.fill()
        for cx0, cy0, sc0 in ((300, 120, 1.0), (1000, 80, 0.8), (1600, 150, 1.1)):
            for dx, dy, r in ((0, 0, 60), (60, -25, 70), (130, 0, 55), (60, 15, 60)):
                ellipse(ctx, cx0 + dx * sc0, hy - 520 + cy0 + dy * sc0, r * sc0, r * sc0 * 0.8)
            setc(ctx, (1, 1, 1), 0.9)
            ctx.fill()
        setc(ctx, C_GRASS)
        ctx.rectangle(-50, hy, SW + 100, SH + 100 - hy)
        ctx.fill()
        toronto.skyline(ctx, view)
    else:
        setc(ctx, C_GRASS)
        ctx.paint()
    fill_poly(ctx, view, [(-400, 0, -12), (400, 0, -12), (400, 0, -2000), (-400, 0, -2000)], C_WATER)
    gquad(ctx, view, -400, 400, -4.2, -1.0, PATH_COL)
    gquad(ctx, view, -400, 400, -12.3, -11.6, hexc('#9aa0aa'))
    items = []
    for x, z, s in PTREES:
        s2 = s * 0.42 if view.ortho else s
        items.append(((x, 1.5, z), lambda x=x, z=z, s=s2: tree3(ctx, view, x, z, s, int(abs(x * 3 + z)) % 3)))
    for x, z in LAMPS:
        items.append(((x, 1.5, z), lambda x=x, z=z: lamp(ctx, view, x, z)))
    items.append(((0, 0.6, 0.3), lambda: bench(ctx, view)))
    if her:
        items.append(((HER_POS[0], 0.8, HER_POS[1] - 0.05), lambda: draw_her(ctx, view, t, st)))
    if hero:
        hx, hz = st['hero'].pos(t)
        items.append(((hx, 0.9, hz), lambda: draw_hero(ctx, view, t, st)))
    if view.ortho:
        for _, fn in items:
            fn()
    else:
        for _, fn in sorted(items, key=lambda it: -view.depth(it[0])):
            fn()


def draw_her(ctx, view, t, st):
    x, z = HER_POS
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 0.32 * view.s, 0.26 * view.s)
        fill_stroke(ctx, HER_JACKET, OUTL, 4)
        ellipse(ctx, p[0], p[1] - 0.02 * view.s, 0.17 * view.s, 0.17 * view.s)
        fill_stroke(ctx, HER_HAIR, OUTL, 3)
        return
    seat = view.pt((x, 0.47, z + 0.05))
    s = view.scale((x, 0.47, z + 0.05))
    if not seat or not s:
        return
    k = 1.75 * s / 785
    her_seated(ctx, seat[0], seat[1], k, t, st['her_expr'](t), st['her_pose'](t), st['her_lean'](t))


def draw_hero(ctx, view, t, st):
    a = st['hero']
    x, z = a.pos(t)
    hz_fall = math.atan2(HER_POS[0] - x, HER_POS[1] - z)
    f = a.facing(t, hz_fall)
    if view.ortho:
        p = view.pt((x, 0, z))
        r = 0.3 * view.s
        ellipse(ctx, p[0], p[1], r * 1.2, r)
        fill_stroke(ctx, JACKET, OUTL, 4)
        ellipse(ctx, p[0], p[1], r * 0.6, r * 0.6)
        fill_stroke(ctx, HAIR, OUTL, 3)
        ax, ay = math.sin(f), -math.cos(f)
        ctx.move_to(p[0] + ax * r * 1.2, p[1] + ay * r * 1.2)
        ctx.line_to(p[0] + ax * r * 2.2, p[1] + ay * r * 2.2)
        setc(ctx, OUTL)
        ctx.set_line_width(5)
        ctx.stroke()
        return
    feet = view.pt((x, 0, z))
    s = view.scale((x, 0, z))
    if not feet or not s:
        return
    k = 1.78 * s / 785
    px, py = feet[0], feet[1] - 300 * k
    cam = view.pos
    front = math.sin(f) * (cam[0] - x) + math.cos(f) * (cam[2] - z) > 0
    walking = a.walking(t)
    mood = st['mood'](t)
    if front:
        hero_front_pose(ctx, px, py, k, t, st['hero_expr'](t), walking, mood, wave=st.get('wave', lambda t: 0)(t))
    else:
        hero_back(ctx, px, py, k, t, walking, 1.0 if mood == 'nervous' else 0.0)
    if st.get('sweat') and st['sweat'](t) and front:
        sx, sy = px + 90 * k, py - 420 * k + (t * 40 % 30) * k
        ctx.move_to(sx, sy - 28 * k)
        ctx.curve_to(sx + 18 * k, sy, sx + 18 * k, sy + 18 * k, sx, sy + 18 * k)
        ctx.curve_to(sx - 18 * k, sy + 18 * k, sx - 18 * k, sy, sx, sy - 28 * k)
        fill_stroke(ctx, hexc('#8fd6ff'), OUTL, 3)


class ParkTop:
    ortho = True

    def __init__(self, xc=1.5, zc=1.0, s=70.0, ox=960, oy=540):
        self.xc, self.zc, self.s, self.ox, self.oy = xc, zc, s, ox, oy
        self.pos = (0, 1000, 0)

    def pt(self, P):
        return (self.ox + (P[0] - self.xc) * self.s, self.oy - (P[2] - self.zc) * self.s)

    def poly(self, pts):
        return [self.pt(p) for p in pts]

    def depth(self, P):
        return 0.0


def speech(ctx, x, y, text, size=46, tail=(0, 1), col=(1, 1, 1), alpha=1.0, italic=False):
    ctx.select_font_face("Inter", cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    w = ctx.text_extents(text).x_advance
    bw, bh = w + 70, size + 50
    bx, by = x - bw / 2, y - bh
    rrect(ctx, bx, by, bw, bh, bh / 2)
    fill_stroke(ctx, col, OUTL, 5, alpha)
    tx = x + tail[0] * bw * 0.25
    poly(ctx, [(tx - 18, by + bh - 3), (tx + 18, by + bh - 3), (tx + tail[0] * 40, by + bh + 38)])
    fill_stroke(ctx, col, OUTL, 5, alpha)
    rrect(ctx, tx - 20, by + bh - 12, 40, 12, 4)
    setc(ctx, col, alpha)
    ctx.fill()
    ctx.move_to(x - w / 2, by + bh / 2 + size * 0.35)
    setc(ctx, OUTL, alpha)
    ctx.show_text(text)
