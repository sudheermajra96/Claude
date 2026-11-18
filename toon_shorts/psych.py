"""Psychology scenes: office with coworkers, spotlight, staring eyes, thought bubbles, stat card.
Plus emotional SFX cues (sad violin, success chimes, slide whistle, murmurs...)."""
from life2 import *
from life2 import _t
import engine

NPCS = [
    dict(x=260, skin='#f1c7a3', hair='#c7782e', style='bun', top='#5b8def', action='type', icon='stain'),
    dict(x=680, skin='#8d5a3b', hair='#1b1b1b', style='short', top='#e05d5d', action='phone', icon='clock'),
    dict(x=1240, skin='#e8b48f', hair='#6b4a2f', style='long', top='#56b38a', action='sip', icon='pimple'),
    dict(x=1660, skin='#c58c6b', hair='#2b2b2b', style='bald', top='#9a6fd0', action='sleep', icon='battery'),
]
STAIN = hexc('#6b3f1f')


def stain(ctx, x, y, r, seed=1):
    rnd = random.Random(seed)
    pts = []
    for i in range(14):
        a = i / 14 * 2 * math.pi
        rr = r * rnd.uniform(0.7, 1.15)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    ctx.move_to(*pts[0])
    for i in range(1, len(pts) + 1):
        p0, p1 = pts[i - 1], pts[i % len(pts)]
        ctx.curve_to(p0[0], p0[1], (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, p1[0], p1[1])
    ctx.close_path()
    setc(ctx, STAIN, 0.9)
    ctx.fill()
    for i in range(3):
        a = rnd.uniform(0, 2 * math.pi)
        ellipse(ctx, x + math.cos(a) * r * 1.4, y + math.sin(a) * r * 1.4, r * 0.15, r * 0.15)
        ctx.fill()


# ------------------------------------------------------------------ office
def office_bg(ctx, L=1.0):
    g = cairo.LinearGradient(0, 0, 0, SH)
    g.add_color_stop_rgb(0, *hexc('#dfe7ef'))
    g.add_color_stop_rgb(1, *hexc('#c9d4df'))
    ctx.set_source(g)
    ctx.paint()
    # window strip with skyline
    ctx.rectangle(0, 90, SW, 230)
    setc(ctx, hexc('#9fd0f5'))
    ctx.fill()
    rnd = random.Random(4)
    x = 0
    while x < SW:
        w, h = rnd.randint(60, 140), rnd.randint(60, 190)
        ctx.rectangle(x, 320 - h, w - 6, h)
        setc(ctx, hexc('#7fa9c9'))
        ctx.fill()
        x += w
    for i in range(0, SW + 1, 240):
        ctx.rectangle(i - 8, 90, 16, 230)
        setc(ctx, hexc('#f4f7fa'))
        ctx.fill()
    ctx.rectangle(0, 82, SW, 16)
    ctx.rectangle(0, 314, SW, 16)
    setc(ctx, hexc('#f4f7fa'))
    ctx.fill()
    # ceiling lights
    for i in range(4):
        rrect(ctx, 160 + i * 460, 20, 220, 26, 10)
        fill_stroke(ctx, hexc('#ffffff'), OUTL, 4)
    # floor
    ctx.rectangle(0, 880, SW, 200)
    setc(ctx, hexc('#b9a58a'))
    ctx.fill()
    ctx.rectangle(0, 874, SW, 10)
    setc(ctx, hexc('#8d7a62'))
    ctx.fill()
    # plant
    rrect(ctx, 1880, 700, 70, 180, 10)
    fill_stroke(ctx, hexc('#c46a3c'), OUTL, 4)


def npc_head(ctx, n, x, y, t, mode, hero_x, stare):
    turn = clamp((hero_x - x) / 500, -1, 1) * 22 * stare
    rot = 0.0
    if mode == 'sleep' and stare < 0.5:
        rot = 0.35
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    hair = hexc(n['hair'])
    if n['style'] == 'long':
        ctx.move_to(-90, -40)
        ctx.curve_to(-120, 60, -110, 140, -95, 180)
        ctx.line_to(95, 180)
        ctx.curve_to(110, 140, 120, 60, 90, -40)
        ctx.close_path()
        fill_stroke(ctx, hair, OUTL, 5)
    if n['style'] == 'bun':
        ellipse(ctx, 0, -110, 42, 38)
        fill_stroke(ctx, hair, OUTL, 5)
    for s in (-1, 1):
        ellipse(ctx, s * 80, 6, 18, 24)
        fill_stroke(ctx, hexc(n['skin']), OUTL, 4)
    ellipse(ctx, 0, 0, 82, 92)
    fill_stroke(ctx, hexc(n['skin']), OUTL, 5)
    if n['style'] in ('bun', 'long', 'short'):
        ctx.move_to(-84, 0)
        ctx.curve_to(-90, -90, -40, -100, 0, -96)
        ctx.curve_to(50, -100, 92, -80, 84, 0)
        ctx.curve_to(60, -50, 20 + turn, -60, -10 + turn, -40)
        ctx.curve_to(-40, -60, -70, -40, -84, 0)
        ctx.close_path()
        fill_stroke(ctx, hair, OUTL, 5)
    ex = turn
    if stare > 0.5:
        pass   # eyes drawn later on top of the spotlight darkness
    elif mode == 'sleep':
        for s in (-1, 1):
            ctx.move_to(ex + s * 30 - 14, 10)
            ctx.curve_to(ex + s * 30 - 6, 18, ex + s * 30 + 6, 18, ex + s * 30 + 14, 10)
        setc(ctx, OUTL)
        ctx.set_line_width(5)
        ctx.stroke()
    else:
        dy = 10 if mode in ('type', 'phone') else 0
        for s in (-1, 1):
            ellipse(ctx, ex + s * 30, 6 + dy, 8, 10 if dy == 0 else 5)
            setc(ctx, OUTL)
            ctx.fill()
    # mouth
    if stare > 0.5:
        ellipse(ctx, ex, 52, 12, 15)
        fill_stroke(ctx, hexc('#5e1419'), OUTL, 3)
    else:
        ctx.move_to(ex - 18, 50)
        ctx.curve_to(ex - 6, 58 if mode != 'sleep' else 52, ex + 6, 58, ex + 18, 50)
        setc(ctx, OUTL)
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.restore()


def npc_eyes(ctx, n, y, hero_x, stare, t, glow_eyes=False):
    x = n['x']
    turn = clamp((hero_x - x) / 500, -1, 1) * 22
    look = clamp((hero_x - x) / 400, -1, 1)
    blink = ((t * 0.9 + x * 0.001) % 2.7) < 0.1
    for s in (-1, 1):
        cx_, cy_ = x + turn + s * 30, y + 2
        if glow_eyes:
            glow(ctx, cx_, cy_, 70, (1, 1, 0.9), 0.25 * stare)
        ellipse(ctx, cx_, cy_, 22, 26 * (0.15 if blink else 1))
        fill_stroke(ctx, (1, 1, 1), OUTL, 4, stare)
        if not blink:
            ellipse(ctx, cx_ + look * 9, cy_ + 2, 9, 10)
            setc(ctx, OUTL, stare)
            ctx.fill()
        ctx.move_to(cx_ - 20, cy_ - 40)
        ctx.line_to(cx_ + 20, cy_ - 44 - s * 4)
        setc(ctx, hexc(n['hair']), stare)
        ctx.set_line_width(7)
        ctx.stroke()


def npc(ctx, n, t, hero_x, stare):
    x, y = n['x'], 700
    mode = n['action']
    rrect(ctx, x - 120, 440, 240, 300, 50)
    fill_stroke(ctx, hexc('#3f4660'), OUTL, 5)
    top = hexc(n['top'])
    ctx.move_to(x - 100, 720)
    ctx.curve_to(x - 110, 600, x - 90, 520, x, 515)
    ctx.curve_to(x + 90, 520, x + 110, 600, x + 100, 720)
    ctx.close_path()
    fill_stroke(ctx, top, OUTL, 5)
    hy = 420
    npc_head(ctx, n, x, hy, t, mode, hero_x, stare)
    # desk
    ctx.rectangle(x - 210, 680, 420, 28)
    fill_stroke(ctx, hexc('#f2f2f2'), OUTL, 5)
    ctx.rectangle(x - 195, 708, 390, 172)
    fill_stroke(ctx, hexc('#a3b1c2'), OUTL, 5)
    skin = hexc(n['skin'])
    busy = stare < 0.5
    if mode == 'type':
        rrect(ctx, x - 95, 575, 190, 108, 8)
        fill_stroke(ctx, hexc('#c6ccd8'), OUTL, 5)
        ellipse(ctx, x, 628, 14, 14)
        setc(ctx, (1, 1, 1))
        ctx.fill()
        hands = [(x - 60, 676 + (math.sin(t * 31) * 5 if busy else 0)), (x + 60, 676 + (math.sin(t * 27 + 1) * 5 if busy else 0))]
    elif mode == 'phone' and busy:
        hands = [(x - 20, 600), (x + 120, 676)]
        rrect(ctx, x - 50, 560, 60, 90, 10)
        fill_stroke(ctx, hexc('#111111'), OUTL, 4)
        glow(ctx, x - 20, 590, 110, hexc('#7fb2ff'), 0.4)
    elif mode == 'sip' and busy:
        cyc = (t % 2.6) / 2.6
        up = smooth((cyc - 0.1) / 0.15) * (1 - smooth((cyc - 0.55) / 0.15))
        hands = [(x - 110, 676), (x + 70 - 50 * up, 670 - 190 * up)]
        mx, my = hands[1]
        rrect(ctx, mx - 26, my - 60, 52, 64, 8)
        fill_stroke(ctx, hexc('#ffffff'), OUTL, 4)
        if up < 0.2 and cyc > 0.7:
            for k in range(2):
                ctx.move_to(mx - 8 + k * 14, my - 70)
                ctx.curve_to(mx - 20 + k * 14, my - 95, mx + 4 + k * 14, my - 110, mx - 8 + k * 14, my - 130)
            setc(ctx, (1, 1, 1), 0.8)
            ctx.set_line_width(4)
            ctx.stroke()
    else:
        hands = [(x - 110, 676), (x + 110, 676)]
    for hx_, hy_ in hands:
        hose(ctx, (x - 70 if hx_ < x else x + 70, 560), (hx_, hy_), 20 if hx_ < x else -20, 34, top)
        ellipse(ctx, hx_, hy_, 22, 20)
        fill_stroke(ctx, skin, OUTL, 4)
    if mode == 'sleep' and busy:
        for i in range(3):
            ph = (t * 0.6 + i / 3) % 1
            text_center(ctx, 'z', x + 90 + ph * 80, hy - 90 - ph * 140, 34 + 30 * ph, hexc('#5b6b8a'), a=1 - ph)


def bubble(ctx, x, y, icon, a):
    if a <= 0:
        return
    s = 0.4 + 0.6 * a
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for i, (dx, dy, r) in enumerate(((-70, 150, 14), (-45, 110, 22))):
        ellipse(ctx, dx, dy, r, r)
        fill_stroke(ctx, (1, 1, 1), OUTL, 4)
    rx, ry = 120, 90
    for k in range(9):
        a_ = k / 9 * 2 * math.pi
        ellipse(ctx, math.cos(a_) * rx * 0.75, math.sin(a_) * ry * 0.7, 55, 50)
        fill_stroke(ctx, (1, 1, 1), OUTL, 4)
    ellipse(ctx, 0, 0, rx * 0.95, ry * 0.85)
    setc(ctx, (1, 1, 1))
    ctx.fill()
    if icon == 'stain':
        poly(ctx, [(-55, -45), (-25, -60), (25, -60), (55, -45), (70, -10), (40, 0), (40, 60), (-40, 60), (-40, 0), (-70, -10)])
        fill_stroke(ctx, hexc('#5b8def'), OUTL, 4)
        stain(ctx, 5, 20, 18, 3)
    elif icon == 'clock':
        ellipse(ctx, 0, 0, 60, 60)
        fill_stroke(ctx, (1, 1, 1), OUTL, 6)
        ctx.move_to(0, 0)
        ctx.line_to(0, -42)
        ctx.move_to(0, 0)
        ctx.line_to(30, 10)
        setc(ctx, hexc('#e0393e'))
        ctx.set_line_width(7)
        ctx.stroke()
        text_center(ctx, '!', 85, 20, 60, hexc('#e0393e'))
    elif icon == 'pimple':
        ellipse(ctx, 0, 0, 58, 64)
        fill_stroke(ctx, hexc('#e8b48f'), OUTL, 5)
        for s in (-1, 1):
            ellipse(ctx, s * 20, -8, 6, 8)
            setc(ctx, OUTL)
            ctx.fill()
        ellipse(ctx, 22, 26, 10, 10)
        setc(ctx, hexc('#e0393e'))
        ctx.fill()
        ctx.move_to(-16, 34)
        ctx.line_to(4, 30)
        setc(ctx, OUTL)
        ctx.set_line_width(4)
        ctx.stroke()
    elif icon == 'battery':
        rrect(ctx, -60, -30, 110, 60, 8)
        fill_stroke(ctx, (1, 1, 1), OUTL, 6)
        ctx.rectangle(52, -12, 12, 24)
        setc(ctx, OUTL)
        ctx.fill()
        ctx.rectangle(-50, -20, 20, 40)
        setc(ctx, hexc('#e0393e'))
        ctx.fill()
    ctx.restore()


def walk_pose(x, y, k, t, cadence=1.4, moving=True):
    ph = t * 2 * math.pi * cadence if moving else 0
    fy = y + 300 * k
    feet = [(x - 25 * k + math.sin(ph) * 70 * k, fy - max(0, math.cos(ph)) * 30 * k),
            (x + 25 * k - math.sin(ph) * 70 * k, fy - max(0, -math.cos(ph)) * 30 * k)]
    hands = [(x - 120 * k - math.sin(ph) * 40 * k, y + 10 * k), (x + 120 * k + math.sin(ph) * 40 * k, y + 10 * k)]
    bob = abs(math.sin(ph)) * 8 * k if moving else 0
    return feet, hands, bob


def office(ctx, world, t, lt, kw):
    if engine.layer('bg'):
        office_bg(ctx)
    hx = key_or(kw, 'hero_x', lt, 900)
    hk = key_or(kw, 'hero_k', lt, 0.95)
    stare = key_or(kw, 'stare', lt, 0.0)
    spot = key_or(kw, 'spot', lt, 0.0)
    hide = key_or(kw, 'hide', lt, 0.0)
    moving = kw.get('walking', True)
    if engine.layer('bg'):
        for n in NPCS:
            npc(ctx, n, t, hx, stare)
    # hero (feet on the floor line)
    floor = 1040
    py = floor - 300 * hk
    feet, hands, bob = walk_pose(hx, py, hk, t, kw.get('cadence', 1.4), moving)
    py -= bob
    chest = (hx + 18 * hk, py - 130 * hk)
    if hide > 0.01:
        hands = [(hands[0][0] + (chest[0] - 40 * hk - hands[0][0]) * hide, hands[0][1] + (chest[1] - hands[0][1]) * hide),
                 (hands[1][0] + (chest[0] + 50 * hk - hands[1][0]) * hide, hands[1][1] + (chest[1] + 10 * hk - hands[1][1]) * hide)]

    def folder(ctx, hs):
        if hide > 0.3:
            (x0, y0), (x1, y1) = hs
            cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
            ctx.save()
            ctx.translate(cx_, cy_)
            ctx.rotate(-0.12)
            rrect(ctx, -95 * hk, -80 * hk, 190 * hk, 150 * hk, 10)
            fill_stroke(ctx, hexc('#3d7be0'), OUTL, 5)
            ctx.rectangle(-95 * hk, -80 * hk, 70 * hk, 18 * hk)
            setc(ctx, hexc('#2c5fb3'))
            ctx.fill()
            ctx.restore()

    if engine.layer('bg'):
        ellipse(ctx, hx, floor + 14, 120 * hk, 18 * hk)
        setc(ctx, (0, 0, 0), 0.18)
        ctx.fill()
    if not engine.layer('mid'):
        pass
    elif kw.get('stain', True) and hide < 0.3:
        # draw hero, then stain on top of torso, then arms again via prop trick
        person(ctx, hx, py, hk, t, kw.get('expr', 'calm'), hands=hands, feet=feet,
               prop=lambda ctx, hs: stain(ctx, chest[0], chest[1], 34 * hk, 7))
    else:
        person(ctx, hx, py, hk, t, kw.get('expr', 'calm'), hands=hands, feet=feet, prop=folder)
    head_y = py - 230 * hk - 120 * hk
    if kw.get('sweat') and engine.layer('mid'):
        sx_, sy_ = hx + 125 * hk, head_y - 40 * hk + (t * 40) % 30
        ctx.move_to(sx_, sy_ - 28)
        ctx.curve_to(sx_ + 18, sy_, sx_ + 18, sy_ + 18, sx_, sy_ + 18)
        ctx.curve_to(sx_ - 18, sy_ + 18, sx_ - 18, sy_, sx_, sy_ - 28)
        fill_stroke(ctx, hexc('#8fd6ff'), OUTL, 3)
    if not engine.layer('post'):
        return
    # spotlight
    if spot > 0.01:
        top_w, bot_w = 90, 300 * hk + 60
        cone = [(hx - top_w, -10), (hx + top_w, -10), (hx + bot_w, floor + 30), (hx - bot_w, floor + 30)]
        ctx.save()
        ctx.rectangle(-10, -10, SW + 20, SH + 20)
        poly(ctx, cone)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        setc(ctx, hexc('#05050d'), 0.82 * spot)
        ctx.fill()
        ctx.restore()
        g = cairo.LinearGradient(0, 0, 0, SH)
        g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.30 * spot)
        g.add_color_stop_rgba(1, 1, 0.95, 0.75, 0.08 * spot)
        ctx.save()
        poly(ctx, cone)
        ctx.clip()
        ctx.set_operator(cairo.OPERATOR_ADD)
        ctx.set_source(g)
        ctx.paint()
        ctx.restore()
        ellipse(ctx, hx, floor + 20, bot_w, 40)
        setc(ctx, (1, 0.95, 0.75), 0.25 * spot)
        ctx.fill()
    if stare > 0.01:
        for n in NPCS:
            npc_eyes(ctx, n, 422, hx, stare, t, glow_eyes=spot > 0.3)
    for i, n in enumerate(NPCS):
        b0 = kw.get('bubbles', [None] * 4)[i]
        if b0 is not None and lt >= b0:
            a = smooth((lt - b0) / 0.25)
            bubble(ctx, n['x'] + 110, 210, n['icon'], a)


def spill(ctx, world, t, lt, kw):
    if engine.layer('bg'):
        office_bg(ctx)
        for n in NPCS:
            npc(ctx, n, t, 960, 0)
        setc(ctx, (0.85, 0.9, 0.95), 0.55 if engine.LAYER == 'all' else 0.3)
        ctx.paint()
    if not engine.layer('mid'):
        return
    bump = kw.get('bump', 0.7)
    k = 1.7
    px, py = 900, 1120
    hit = smooth((lt - bump) / 0.12)
    jolt = math.sin(clamp((lt - bump) / 0.3) * math.pi) * 30 if lt > bump else 0
    chest = (px + 30 * k, py - 135 * k)
    cup_hand = (px + 150 * k + jolt, py - 120 * k - 60 * hit)
    expr = 'calm' if lt < bump + 0.25 else 'shock'

    def cup(ctx, hs):
        hx_, hy_ = hs[1]
        ctx.save()
        ctx.translate(hx_, hy_ - 20)
        ctx.rotate(-1.3 * hit)
        poly(ctx, [(-40, -70), (40, -70), (30, 50), (-30, 50)])
        fill_stroke(ctx, hexc('#ffffff'), OUTL, 6)
        ctx.rectangle(-36, -30, 72, 34)
        setc(ctx, hexc('#c46a3c'))
        ctx.fill()
        ctx.restore()
        if lt >= bump + 0.25:
            r = 50 * smooth((lt - bump - 0.25) / 0.2)
            stain(ctx, chest[0], chest[1], r, 7)

    person(ctx, px - jolt * 0.3, py, k, t, expr, hands=[(px - 140 * k, py), cup_hand], legs=False,
           prop=cup, head_rot=0.06 * jolt / 30)
    # splash droplets flying from cup to chest
    if bump + 0.05 < lt < bump + 0.6:
        u = (lt - bump - 0.05) / 0.55
        rnd = random.Random(5)
        for i in range(14):
            sx_, sy_ = cup_hand[0] - 40, cup_hand[1] - 80
            ex_, ey_ = chest[0] + rnd.uniform(-90, 90), chest[1] + rnd.uniform(-60, 90)
            v = clamp(u * rnd.uniform(1.0, 1.6))
            x = sx_ + (ex_ - sx_) * v
            y = sy_ + (ey_ - sy_) * v - math.sin(math.pi * v) * rnd.uniform(60, 200)
            ellipse(ctx, x, y, 14, 18)
            fill_stroke(ctx, hexc('#8a4f26'), OUTL, 3)
    # passer-by shoulder bumping in from the right
    sx = SW + 200 - 760 * smooth((lt - bump + 0.25) / 0.25) + 900 * smooth((lt - bump - 0.1) / 0.4)
    ellipse(ctx, sx, 700, 260, 420)
    fill_stroke(ctx, hexc('#566079'), OUTL, 7)
    if bump < lt < bump + 0.35:
        for kk in range(5):
            a = math.pi + (kk - 2) * 0.35
            ctx.move_to(cup_hand[0] + math.cos(a) * 120, cup_hand[1] + math.sin(a) * 120)
            ctx.line_to(cup_hand[0] + math.cos(a) * 180, cup_hand[1] + math.sin(a) * 180)
        setc(ctx, OUTL)
        ctx.set_line_width(8)
        ctx.stroke()


def shocked_face(ctx, world, t, lt, kw):
    engine.SCENES['face_scene'](ctx, world, t, lt, dict(expr='shock', light=0.9, shake=Key([(0, 1), (0.8, 0.2)], 'lin')))
    if not engine.layer('mid'):
        return
    jx = math.sin(t * 70) * 16 * (1 - clamp(lt / 0.8)) * 0.8
    stain(ctx, 860 + 150 + jx, 930, 70, 7)


def eyes_montage(ctx, world, t, lt, kw):
    setc(ctx, hexc('#07070f'))
    ctx.paint()
    rnd = random.Random(21)
    vert = engine.VERTICAL
    for i in range(14):
        if vert:
            x, y = rnd.uniform(700, 1220), rnd.uniform(60, 1000)
            if abs(x - 960) < 170 and 250 < y < 950:
                x += 230 if x > 960 else -230
            sz = rnd.uniform(0.45, 0.8)
        else:
            x, y = rnd.uniform(150, 1770), rnd.uniform(120, 960)
            if abs(x - 960) < 260 and abs(y - 560) < 260:
                x += 520 if x > 960 else -520
            sz = rnd.uniform(0.6, 1.4)
        t_on = i * 0.1
        if lt < t_on:
            continue
        a = smooth((lt - t_on) / 0.15)
        blink = ((t * 1.1 + i * 0.37) % 2.2) < 0.1
        look = (960 - x) / 900, (560 - y) / 700
        for s in (-1, 1):
            ex_, ey_ = x + s * 50 * sz, y
            glow(ctx, ex_, ey_, 110 * sz, (1, 1, 0.85), 0.12 * a)
            ellipse(ctx, ex_, ey_, 36 * sz * a, 40 * sz * a * (0.12 if blink else 1))
            fill_stroke(ctx, (1, 1, 1), OUTL, 4)
            if not blink:
                ellipse(ctx, ex_ + look[0] * 14 * sz, ey_ + look[1] * 14 * sz, 14 * sz * a, 15 * sz * a)
                setc(ctx, OUTL)
                ctx.fill()
    # tiny hero in a spotlight in the middle
    cone = [(900, -10), (1020, -10), (1180, 900), (740, 900)]
    g = cairo.LinearGradient(0, 0, 0, 900)
    g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.35)
    g.add_color_stop_rgba(1, 1, 0.95, 0.75, 0.12)
    poly(ctx, cone)
    ctx.set_source(g)
    ctx.fill()
    k = 0.55 - 0.05 * clamp(lt / 2)
    person(ctx, 960, 900 - 300 * k, k, t, 'unsure', hands=[(960 + 30 * k, 900 - 430 * k), (960 + 70 * k, 900 - 420 * k)])
    stain(ctx, 960 + 18 * k, 900 - 300 * k - 130 * k, 30 * k, 7)


def stat_card(ctx, world, t, lt, kw):
    g = cairo.LinearGradient(0, 0, SW, SH)
    g.add_color_stop_rgb(0, *hexc('#14213d'))
    g.add_color_stop_rgb(1, *hexc('#2b4a7a'))
    ctx.set_source(g)
    ctx.paint()
    a = smooth(lt / 0.3)
    pop_ = 1 + 0.2 * (1 - a)
    ctx.save()
    ctx.translate(960, 190)
    ctx.scale(pop_, pop_)
    text_center(ctx, 'The Spotlight Effect', 0, 0, 104, hexc('#ffcf3f'), a=a)
    ctx.restore()
    text_center(ctx, 'How many people noticed the embarrassing T-shirt?', 960, 300, 46, (0.85, 0.88, 1), cairo.FONT_WEIGHT_NORMAL, a)
    rows = [(0.7, 'They guessed', 46, '#ff5a5a'), (1.6, 'Really', 23, '#22c35e')]
    for i, (t_on, label, pct, col) in enumerate(rows):
        if lt < t_on:
            continue
        u = smooth((lt - t_on) / 0.6)
        y = 470 + i * 220
        text_center(ctx, label, 330, y + 30, 58, (1, 1, 1))
        rrect(ctx, 560, y - 50, 1100, 110, 24)
        setc(ctx, (1, 1, 1), 0.12)
        ctx.fill()
        w = 1100 * pct / 50 * u
        rrect(ctx, 560, y - 50, max(w, 30), 110, 24)
        fill_stroke(ctx, hexc(col), OUTL, 5)
        text_center(ctx, f"{int(round(pct * u))}%", 560 + max(w, 30) + 100, y + 28, 70, (1, 1, 1))
    if lt > 2.6:
        b = smooth((lt - 2.6) / 0.3)
        text_center(ctx, "People notice you about HALF as much as you think.", 960, 960, 50, (1, 1, 1), a=b)
    text_center(ctx, 'Gilovich, Medvec & Savitsky (2000)', 1620, 1050, 28, (0.6, 0.65, 0.8), cairo.FONT_WEIGHT_NORMAL)


engine.LAYERED_SCENES.update({'office', 'spill', 'shocked_face'})
engine.SCENES.update(office=office, spill=spill, shocked_face=shocked_face, eyes_montage=eyes_montage,
                     stat_card=stat_card)


# --------------------------------------------------------------- emotion SFX
def violin_note(f, d, vib_delay=0.15):
    t = _t(d)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - vib_delay) / 0.2, 0, 1)
    ph = np.cumsum(f * vib) / SR
    s = 2 * (ph % 1) - 1
    s = bp(s, 400, 5000) + 0.6 * bp(s, 900, 1300) + 0.4 * bp(s, 2200, 3200)
    bow = 0.8 + 0.2 * lp(noise(len(t)), 8) * 6
    return s * env_adsr(len(t), 0.09, 0.18) * bow * 0.35


def sad_violin(notes=((76, 0.42), (74, 0.42), (72, 0.42), (71, 1.3))):
    """Short descending minor phrase, doubled a third below."""
    out = np.zeros(int(sum(d for _, d in notes) * SR) + SR)
    tt = 0.0
    for n, d in notes:
        place(out, violin_note(midi(n), d + 0.08), tt)
        place(out, violin_note(midi(n - 3), d + 0.08) * 0.55, tt)
        tt += d
    return lp(out, 6000)


def bell(f, d=1.2):
    t = _t(d)
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (dd)) for r, a, dd in
            ((1, 1.0, 0.5), (2.0, 0.35, 0.3), (2.76, 0.25, 0.18), (5.4, 0.12, 0.08)))
    return s * 0.3


def success_jingle():
    out = np.zeros(int(1.6 * SR))
    for i, n in enumerate((72, 76, 79, 84)):
        place(out, bell(midi(n)), i * 0.09)
    place(out, sparkle(), 0.35, 0.6)
    return out


def slide_whistle(f0, f1, d):
    t = _t(d)
    f = f0 * (f1 / f0) ** (t / d)
    s = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.01 * np.sin(2 * np.pi * 6 * t))) / SR)
    s += bp(noise(len(t)), 800, 4000) * 0.05
    return s * env_adsr(len(t), 0.03, 0.08) * 0.35


def spotlight_clunk():
    t = _t(0.6)
    s = np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.12) * 0.9
    s += bp(noise(len(t)), 2500, 7000) * np.exp(-t / 0.02) * 0.8
    s += np.sin(2 * np.pi * 2300 * t) * np.exp(-t / 0.05) * 0.3
    return s * 0.8


def hum(d):
    t = _t(d)
    s = np.sign(np.sin(2 * np.pi * 100 * t)) * 0.3 + np.sin(2 * np.pi * 50 * t)
    return lp(s, 400) * 0.06 * env_adsr(len(t), 0.05, 0.2)


def splash():
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    s = bp(noise(n), 300, 3500) * np.exp(-t / 0.09) * 0.9
    r = random.Random(3)
    for _ in range(9):
        o = r.uniform(0.05, 0.5)
        f = r.uniform(900, 2200)
        tt = np.clip(t - o, 0, None)
        s += np.where(t >= o, np.sin(2 * np.pi * (f + 3000 * tt) * tt) * np.exp(-tt / 0.03), 0) * 0.35
    return s * 0.8


def murmur(d, voices=4):
    out = np.zeros(int(d * SR))
    t = _t(d)
    for v in range(voices):
        r = np.random.default_rng(v + 10)
        am = lp(np.abs(r.standard_normal(len(t))), 6)
        am = np.clip(am / (am.std() + 1e-9) - 0.3, 0, None)
        out += bp(r.standard_normal(len(t)), 400 + v * 150, 2400) * am * 0.15
    return out * env_adsr(len(t), 0.3, 0.3)


def typing(d, seed=2):
    out = np.zeros(int(d * SR) + SR)
    r = random.Random(seed)
    tt = 0.0
    while tt < d:
        n = int(0.025 * SR)
        x = np.arange(n) / SR
        place(out, bp(noise(n), 2000, 6000) * np.exp(-x / 0.004) * r.uniform(0.3, 0.6), tt)
        tt += r.uniform(0.05, 0.16)
    return out[:int(d * SR)]


def sip():
    t = _t(0.5)
    f = 500 + 900 * t / 0.5
    s = bp(noise(len(t)), 600, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR * 0.02))
    return s * np.sin(np.pi * t / 0.5) * 0.35


def snore(d):
    t = _t(d)
    env = np.clip(np.sin(2 * np.pi * t / 2.0), 0, None) ** 2
    s = lp(noise(len(t)), 300) * (1 + 0.5 * np.sin(2 * np.pi * 32 * t))
    return s * env * 0.6


def head_swish():
    return whoosh(0.25, 0.4) * 0.5


def office_tone(d):
    t = _t(d)
    return lp(noise(len(t)), 250) * 0.10 + hp(lp(noise(len(t)), 3000), 800) * 0.01


def stat_card_v(ctx, world, t, lt, kw):
    """Full 1080x1920 result card: two bars growing upward."""
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc('#14213d'))
    g.add_color_stop_rgb(1, *hexc('#2b4a7a'))
    ctx.set_source(g)
    ctx.paint()
    a = smooth(lt / 0.3)
    ctx.save()
    ctx.translate(W / 2, 560)
    ctx.scale(1 + 0.2 * (1 - a), 1 + 0.2 * (1 - a))
    outlined_text(ctx, 'The Spotlight', 0, 0, 104, hexc('#ffcf3f'), lw=10)
    outlined_text(ctx, 'Effect', 0, 112, 104, hexc('#ffcf3f'), lw=10)
    ctx.restore()
    base = 1500
    for i, (t_on, label, pct, col) in enumerate(((0.6, 'We think', 46, '#ff5a5a'), (1.5, 'Reality', 23, '#22c35e'))):
        x = 330 + i * 420
        text_center(ctx, label, x, base + 80, 56, (1, 1, 1))
        if lt < t_on:
            continue
        u = smooth((lt - t_on) / 0.6)
        h = 640 * pct / 46 * u
        rrect(ctx, x - 120, base - h, 240, max(h, 20), 26)
        fill_stroke(ctx, hexc(col), OUTL, 6)
        outlined_text(ctx, f"{int(round(pct * u))}%", x, base - h - 30, 90, lw=10)
    text_center(ctx, 'Gilovich et al. (2000)', W / 2, 1760, 30, (0.6, 0.65, 0.8), cairo.FONT_WEIGHT_NORMAL)


engine.SCENES['stat_card_v'] = stat_card_v
