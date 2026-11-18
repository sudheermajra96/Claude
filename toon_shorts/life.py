"""Lifestyle / self-improvement scenes: bedroom, kitchen, desk, park run, checklist, close-up.

Reuses the drawing helpers, Video composer and audio mixer from engine.py and
registers new scene kinds into engine.SCENES.
"""
from engine import *
import engine

PANTS = hexc('#2b3a63')
SHOE = hexc('#f2f2f5')

LIFE_EXPR = dict(EXPR)
LIFE_EXPR.update({
    'tired': dict(brow=-0.05, tilt=-0.2, eye=0.42, pupil=1.0, mouth='flat', mo=0.0),
    'sleep': dict(brow=0.0, tilt=0.0, eye=0.0, pupil=1.0, mouth='smile', mo=0.2),
    'yawn':  dict(brow=0.3, tilt=-0.2, eye=0.0, pupil=1.0, mouth='o', mo=1.0),
    'proud': dict(brow=0.15, tilt=0.15, eye=0.75, pupil=1.0, mouth='grin', mo=0.9),
    'focus': dict(brow=-0.1, tilt=0.25, eye=0.8, pupil=1.0, mouth='flat', mo=0.0),
})


# ------------------------------------------------------------------ character
def draw_head(ctx, cx, cy, k, expr='calm', t=0.0, rot=0.0, look=(0, 0)):
    ex = LIFE_EXPR[expr]
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(k, k)
    for s in (-1, 1):
        ellipse(ctx, s * 235, 30, 48, 62)
        fill_stroke(ctx, SKIN, OUTL, 6)
    ellipse(ctx, 0, 0, 245, 270)
    fill_stroke(ctx, SKIN, OUTL, 7)
    cel(ctx, lambda: ellipse(ctx, 0, 0, 245, 270), (-60, -50), a=0.2, rim=(14, 12), rim_w=12, outline=7)
    hairs = [(-200, -150, 85), (-120, -225, 95), (-20, -255, 100), (90, -240, 95), (180, -175, 85),
             (-230, -60, 55), (225, -70, 55), (40, -200, 90), (-80, -200, 90)]
    for hx, hy, r in hairs:
        ctx.new_sub_path()
        ctx.arc(hx, hy, r, 0, 2 * math.pi)
    setc(ctx, OUTL)
    ctx.set_line_width(12)
    ctx.stroke()
    for hx, hy, r in hairs:
        ctx.new_sub_path()
        ctx.arc(hx, hy, r, 0, 2 * math.pi)
    setc(ctx, HAIR)
    ctx.fill()
    for hx, hy, r in hairs[:6]:
        ctx.new_sub_path()
        ctx.arc(hx - r * 0.15, hy - r * 0.15, r * 0.55, math.pi * 1.05, math.pi * 1.55)
    setc(ctx, (1, 0.85, 0.7), 0.28)
    ctx.set_line_width(9)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    blink = 1.0
    if ((t + 0.7) % 3.3) < 0.12 and 0.3 < ex['eye'] < 1.3:
        blink = 0.1
    eo = ex['eye'] * blink
    for s in (-1, 1):
        x, y = s * 92, 10
        if eo < 0.05:
            ctx.move_to(x - 40, y)
            ctx.curve_to(x - 20, y + 22, x + 20, y + 22, x + 40, y)
            setc(ctx, OUTL)
            ctx.set_line_width(9)
            ctx.stroke()
        else:
            ellipse(ctx, x, y, 52 * min(max(ex['eye'], 0.8), 1.2), 52 * eo)
            fill_stroke(ctx, (1, 1, 1), OUTL, 5)
            pr = 18 * ex['pupil']
            ellipse(ctx, x + look[0] * 18, y + 6 * min(1, eo) + look[1] * 12, pr, pr * min(1, eo * 1.4))
            setc(ctx, OUTL)
            ctx.fill()
            if eo < 0.6:   # heavy eyelid
                ctx.rectangle(x - 60, y - 60, 120, 60 - 52 * eo + 4)
                setc(ctx, SKIN)
                ctx.fill()
                ctx.move_to(x - 52, y - 52 * eo + 4)
                ctx.line_to(x + 52, y - 52 * eo + 4)
                setc(ctx, OUTL)
                ctx.set_line_width(6)
                ctx.stroke()
        rrect(ctx, x - 82, y - 66, 164, 132, 46)
        setc(ctx, OUTL)
        ctx.set_line_width(11)
        ctx.stroke()
        ctx.move_to(x - 40, y - 40)
        ctx.line_to(x - 10, y - 54)
        setc(ctx, (1, 1, 1), 0.5)
        ctx.set_line_width(6)
        ctx.stroke()
        by = y - 92 - ex['brow'] * 45
        tl = ex['tilt'] * 30
        ctx.move_to(x - 60, by + s * tl)
        ctx.line_to(x + 60, by - s * tl)
        setc(ctx, HAIR)
        ctx.set_line_width(18)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    ctx.move_to(-18, 10)
    ctx.line_to(18, 10)
    setc(ctx, OUTL)
    ctx.set_line_width(11)
    ctx.stroke()
    ctx.move_to(-8, 60)
    ctx.curve_to(-30, 110, 10, 120, 22, 105)
    setc(ctx, SKIN_SH)
    ctx.set_line_width(7)
    ctx.stroke()
    m, my = ex['mouth'], 175
    ctx.set_line_width(8)
    if m == 'smile':
        ctx.arc(0, my - 40, 70, 0.35 * math.pi, 0.65 * math.pi)
        setc(ctx, OUTL)
        ctx.stroke()
    elif m == 'grin':
        ctx.move_to(-95, my - 15)
        ctx.curve_to(-60, my + 70, 60, my + 70, 95, my - 15)
        ctx.close_path()
        fill_stroke(ctx, hexc('#7a1f25'), OUTL, 6)
        ctx.rectangle(-75, my - 13, 150, 22)
        setc(ctx, (1, 1, 1))
        ctx.fill()
    elif m == 'flat':
        ctx.move_to(-55, my)
        ctx.line_to(55, my - 4)
        setc(ctx, OUTL)
        ctx.stroke()
    elif m == 'wavy':
        ctx.move_to(-70, my)
        for i in range(1, 8):
            ctx.line_to(-70 + i * 20, my + (8 if i % 2 else -8))
        setc(ctx, OUTL)
        ctx.stroke()
    elif m == 'o':
        ellipse(ctx, 0, my + 10, 38 + 10 * ex['mo'], 50 + 15 * ex['mo'])
        fill_stroke(ctx, hexc('#5e1419'), OUTL, 6)
    ctx.restore()


def hose(ctx, a, b, bend, w, color):
    """Rubber-hose limb from a to b, bowed sideways by `bend` px."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) + 1e-6
    cx, cy = mx - dy / L * bend, my + dx / L * bend
    for col, lw in ((OUTL, w + 10), (color, w)):
        ctx.move_to(*a)
        ctx.curve_to(cx, cy, cx, cy, *b)
        setc(ctx, col)
        ctx.set_line_width(lw)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def person(ctx, x, y, k, t, expr='calm', lean=0.0, hands=None, feet=None, head_rot=0.0,
           legs=True, look=(0, 0), hand_bend=(40, -40), prop=None):
    """(x, y) = pelvis. hands/feet are absolute points; defaults hang naturally."""
    sh_y = y - 230 * k
    sx = x + math.sin(lean) * 230 * k
    shoulders = [(sx - 85 * k, sh_y + 20 * k), (sx + 85 * k, sh_y + 20 * k)]
    hands = hands or [(x - 120 * k, y + 10 * k), (x + 120 * k, y + 10 * k)]
    if legs:
        feet = feet or [(x - 60 * k, y + 300 * k), (x + 60 * k, y + 300 * k)]
        for i, s in enumerate((-1, 1)):
            hip = (x + s * 45 * k, y)
            hose(ctx, hip, feet[i], s * 10 * k, 64 * k, PANTS)
            ellipse(ctx, feet[i][0] + s * 22 * k, feet[i][1] + 10 * k, 52 * k, 26 * k)
            fill_stroke(ctx, SHOE, OUTL, 5)
    # torso
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(lean)
    ctx.move_to(-95 * k, 10 * k)
    ctx.curve_to(-110 * k, -120 * k, -105 * k, -230 * k, 0, -240 * k)
    ctx.curve_to(105 * k, -230 * k, 110 * k, -120 * k, 95 * k, 10 * k)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)

    def torso_path():
        ctx.move_to(-95 * k, 10 * k)
        ctx.curve_to(-110 * k, -120 * k, -105 * k, -230 * k, 0, -240 * k)
        ctx.curve_to(105 * k, -230 * k, 110 * k, -120 * k, 95 * k, 10 * k)
        ctx.close_path()
    cel(ctx, torso_path, (-55 * k, -25 * k), a=0.22, rim=(9 * k, 7 * k), rim_w=7 * k)
    poly(ctx, [(-40 * k, -238 * k), (40 * k, -238 * k), (0, -190 * k)])
    fill_stroke(ctx, hexc('#f2efe6'), OUTL, 4)
    ctx.restore()
    for i in range(2):
        hose(ctx, shoulders[i], hands[i], hand_bend[i] * k, 50 * k, JACKET)
        ellipse(ctx, hands[i][0], hands[i][1], 30 * k, 30 * k)
        fill_stroke(ctx, SKIN, OUTL, 5)
    draw_head(ctx, sx, sh_y - 120 * k, 0.5 * k, expr, t, head_rot, look)
    if prop:
        prop(ctx, hands)
        for hp in hands:
            ellipse(ctx, hp[0], hp[1], 30 * k, 30 * k)
            fill_stroke(ctx, SKIN, OUTL, 5)


# ------------------------------------------------------------------ rooms
def light_wall(L):
    return mix(hexc('#1f2246'), hexc('#f4dcc0'), L)


def window(ctx, x, y, w, h, L, t, sun=True):
    rrect(ctx, x - 18, y - 18, w + 36, h + 36, 14)
    fill_stroke(ctx, mix(hexc('#3a3f6a'), hexc('#fff6ea'), L), OUTL, 6)
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, *mix(hexc('#070a24'), hexc('#7fb6ff'), L))
    g.add_color_stop_rgb(1, *mix(hexc('#1d2154'), hexc('#ffb36b'), L))
    ctx.set_source(g)
    ctx.paint()
    if L < 0.4:
        rnd = random.Random(5)
        for _ in range(18):
            setc(ctx, (1, 1, 1), 0.7 * (1 - L / 0.4))
            ctx.arc(x + rnd.uniform(0, w), y + rnd.uniform(0, h * 0.7), rnd.uniform(1.5, 3), 0, 2 * math.pi)
            ctx.fill()
    if sun and L > 0.2:
        sy = y + h + 60 - (L - 0.2) * h * 1.1
        glow(ctx, x + w * 0.65, sy, 260, hexc('#ffcf6b'), 0.6 * L)
        ellipse(ctx, x + w * 0.65, sy, 60, 60)
        setc(ctx, hexc('#ffe08a'))
        ctx.fill()
    ctx.move_to(x, y + h)
    for i in range(9):
        ctx.line_to(x + i * w / 8, y + h - 40 - 30 * math.sin(i * 1.7))
    ctx.line_to(x + w, y + h)
    setc(ctx, mix(hexc('#0a0c20'), hexc('#5b6a9a'), L))
    ctx.fill()
    ctx.restore()
    setc(ctx, mix(hexc('#3a3f6a'), hexc('#fff6ea'), L))
    ctx.rectangle(x + w / 2 - 8, y, 16, h)
    ctx.rectangle(x, y + h / 2 - 8, w, 16)
    ctx.fill()


def room_base(ctx, L, floor_y=820):
    setc(ctx, light_wall(L))
    ctx.paint()
    ctx.rectangle(0, floor_y, SW, SH - floor_y)
    setc(ctx, mix(hexc('#17142a'), hexc('#c99a6a'), L))
    ctx.fill()
    ctx.rectangle(0, floor_y - 14, SW, 20)
    setc(ctx, mix(hexc('#2a2a48'), hexc('#fff3e2'), L))
    ctx.fill()


def alarm_clock(ctx, x, y, text, ringing, t, L):
    jx = (math.sin(t * 90) * 8) if ringing else 0
    rrect(ctx, x - 110 + jx, y - 70, 220, 140, 30)
    fill_stroke(ctx, hexc('#30344f'), OUTL, 6)
    rrect(ctx, x - 85 + jx, y - 45, 170, 90, 14)
    setc(ctx, hexc('#0b0c14'))
    ctx.fill()
    ctx.select_font_face("DejaVu Sans Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(56)
    e = ctx.text_extents(text)
    ctx.move_to(x - e.x_advance / 2 + jx, y + 20)
    setc(ctx, hexc('#ff4b3a'))
    ctx.show_text(text)
    glow(ctx, x + jx, y, 120, hexc('#ff4b3a'), 0.25 * (1 - L))
    if ringing:
        for s in (-1, 1):
            for r in (150, 190):
                ctx.arc(x, y, r, -math.pi / 2 - 0.5 + (0 if s > 0 else math.pi), -math.pi / 2 + 0.5 + (0 if s > 0 else math.pi))
                ctx.new_sub_path()
        ctx.new_path()
        for s in (-1, 1):
            for r in (150, 195):
                a0 = -0.45 if s > 0 else math.pi - 0.45
                ctx.new_sub_path()
                ctx.arc(x, y, r, a0, a0 + 0.9)
        setc(ctx, hexc('#ffd23f'))
        ctx.set_line_width(10)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def key_or(kw, name, lt, default):
    v = kw.get(name, default)
    return v(lt) if callable(v) else v


def bedroom(ctx, world, t, lt, kw):
    L = key_or(kw, 'light', lt, 0.0)
    lamp = key_or(kw, 'lamp', lt, 0.0)
    room_base(ctx, L)
    window(ctx, 1080, 120, 520, 400, L, t)
    # curtains
    for cx in (1040, 1640):
        poly(ctx, [(cx - 50, 90), (cx + 50, 90), (cx + 30 + 10 * math.sin(t), 560), (cx - 40, 560)])
        fill_stroke(ctx, mix(hexc('#2b2350'), hexc('#7aa3c9'), L), OUTL, 5)
    # nightstand + lamp
    ctx.rectangle(150, 640, 300, 260)
    fill_stroke(ctx, mix(hexc('#2c2238'), hexc('#a8754a'), L), OUTL, 6)
    ctx.rectangle(170, 740, 260, 10)
    setc(ctx, OUTL)
    ctx.fill()
    ctx.rectangle(395, 470, 14, 170)
    fill_stroke(ctx, hexc('#3d3d4f'), OUTL, 3)
    poly(ctx, [(330, 470), (470, 470), (440, 380), (360, 380)])
    fill_stroke(ctx, mix(hexc('#6e5a8a'), hexc('#ffe1a6'), max(L, lamp)), OUTL, 5)
    if lamp > 0.01:
        glow(ctx, 400, 520, 520, hexc('#ffcf7a'), 0.55 * lamp)
    clock_txt = kw.get('clock', lambda lt: '5:00')(lt)
    ringing = key_or(kw, 'ring', lt, 0) > 0.5
    alarm_clock(ctx, 260, 570, clock_txt, ringing, t, L)
    taken = key_or(kw, 'taken', lt, 0) > 0.5
    drawer = key_or(kw, 'drawer', lt, 0)
    if drawer > 0.01:
        ctx.rectangle(160, 660, 280, 60 + 40 * drawer)
        setc(ctx, OUTL)
        ctx.fill()
        ctx.rectangle(140, 680 + 40 * drawer, 320, 70)
        fill_stroke(ctx, mix(hexc('#3a2e48'), hexc('#b8855a'), L), OUTL, 6)
    if kw.get('phone', False) and not taken:
        rrect(ctx, 330, 610, 90, 26, 6)
        fill_stroke(ctx, hexc('#111111'), OUTL, 3)
    # bed
    rrect(ctx, 480, 420, 60, 480, 20)
    fill_stroke(ctx, mix(hexc('#2c2238'), hexc('#8a5a3a'), L), OUTL, 6)
    rrect(ctx, 520, 640, 1000, 170, 30)
    fill_stroke(ctx, mix(hexc('#3a3a5a'), hexc('#f3f3f6'), L), OUTL, 6)
    ctx.rectangle(560, 800, 30, 100)
    ctx.rectangle(1460, 800, 30, 100)
    setc(ctx, mix(hexc('#2c2238'), hexc('#8a5a3a'), L))
    ctx.fill()
    rrect(ctx, 560, 570, 260, 100, 45)
    fill_stroke(ctx, mix(hexc('#4a4a6a'), hexc('#ffffff'), L), OUTL, 6)
    mode = kw.get('mode', 'sleep')
    expr = kw.get('expr', 'sleep')
    blanket_top = 640 if mode == 'sleep' else 700
    if mode == 'sleep':
        draw_head(ctx, 700, 560, 0.42, expr, t, -0.35)
        breathe = math.sin(t * 2.2) * 6
        ctx.move_to(760, 640 + breathe)
        ctx.curve_to(900, 590 + breathe, 1300, 600, 1520, 650)
        ctx.line_to(1520, 800)
        ctx.line_to(760, 800)
        ctx.close_path()
        fill_stroke(ctx, mix(hexc('#283a6e'), hexc('#5aa0d8'), L), OUTL, 6)
        if kw.get('slap') is not None:
            s = kw['slap'](lt)
            if s > 0.01:
                hand = (760 + (300 - 760) * s, 640 + (560 - 640) * s - math.sin(math.pi * s) * 80)
                hose(ctx, (800, 650), hand, -40, 46, JACKET)
                ellipse(ctx, hand[0], hand[1], 36, 30)
                fill_stroke(ctx, SKIN, OUTL, 5)
        if expr == 'sleep' and not ringing:
            for i in range(3):
                ph = (t * 0.5 + i / 3) % 1
                text_center(ctx, 'z', 860 + ph * 120 + i * 10, 470 - ph * 200, 40 + 40 * ph, (1, 1, 1), a=1 - ph)
    else:
        arms = mode
        sway = math.sin(t * 1.3) * 0.05 if expr == 'tired' else 0
        px, py = 800, 690
        if arms == 'stretch':
            u = smooth((lt - 0.2) / 0.6)
            hands = [(px - 140 - 90 * u, py - 160 - 330 * u), (px + 140 + 90 * u, py - 160 - 330 * u)]
            ex = 'yawn' if 0.3 < lt < 1.6 else expr
        elif arms == 'reach':
            u = key_or(kw, 'reach', lt, 0.0)
            tx, ty = kw.get('reach_to', (300, 500))
            rx, ry = kw.get('rest', (px - 130, py - 10))
            hands = [(rx + (tx - rx) * u, ry + (ty - ry) * u), (px + 120, py + 20)]
            ex = expr
        else:
            hands = [(px - 110, py + 20), (px + 120, py + 20)]
            ex = expr
        holding = taken and kw.get('phone_mode') == 'grab'

        def held_phone(ctx, hs):
            hx, hy = hs[0]
            rrect(ctx, hx - 40, hy - 85, 80, 150, 14)
            fill_stroke(ctx, hexc('#111111'), OUTL, 4)
            rrect(ctx, hx - 30, hy - 75, 60, 120, 8)
            setc(ctx, hexc('#7fb2ff'))
            ctx.fill()
            glow(ctx, hx, hy - 40, 380, hexc('#5f8cff'), 0.45)
        person(ctx, px, py, 0.95, t, ex, lean=sway, hands=hands, legs=False, head_rot=sway * 2,
               prop=held_phone if holding else None, look=kw.get('look', (0, 0)))
        ctx.move_to(700, blanket_top)
        ctx.curve_to(900, blanket_top - 30, 1300, 610, 1520, 650)
        ctx.line_to(1520, 800)
        ctx.line_to(700, 800)
        ctx.close_path()
        fill_stroke(ctx, mix(hexc('#283a6e'), hexc('#5aa0d8'), L), OUTL, 6)
    # darkness vignette at night
    if L < 0.5:
        g = cairo.RadialGradient(960, 540, 300, 960, 540, 1200)
        g.add_color_stop_rgba(0, 0, 0, 0.05, 0)
        g.add_color_stop_rgba(1, 0, 0, 0.05, 0.5 * (1 - L * 2))
        ctx.set_source(g)
        ctx.paint()


def kitchen(ctx, world, t, lt, kw):
    L = key_or(kw, 'light', lt, 0.8)
    room_base(ctx, L, 900)
    for i in range(0, SW, 80):
        for j in range(380, 640, 80):
            ctx.rectangle(i + 3, j + 3, 74, 74)
    setc(ctx, mix(hexc('#2a2c4a'), hexc('#e9f1f2'), L))
    ctx.fill()
    window(ctx, 260, 120, 420, 300, L, t)
    rrect(ctx, 1450, 120, 330, 780, 30)
    fill_stroke(ctx, mix(hexc('#3a3f5a'), hexc('#dfe6ee'), L), OUTL, 6)
    ctx.move_to(1450, 420)
    ctx.line_to(1780, 420)
    ctx.set_line_width(6)
    setc(ctx, OUTL)
    ctx.stroke()
    ctx.rectangle(1490, 180, 18, 180)
    ctx.rectangle(1490, 460, 18, 180)
    ctx.fill()
    u = key_or(kw, 'drink', lt, 0.0)
    px, py = 900, 640
    mouth = (px - 60, py - 230 * 0.95 - 120 * 0.95 + 175 * 0.475 + 30)
    hands = [(px - 120, py + 10), (px + 150 + (mouth[0] + 60 - px - 150) * u, py - 40 + (mouth[1] - py + 40) * u)]
    level = 1 - clamp((lt - kw.get('drain_t', 0.8)) / kw.get('drain_d', 1.2))

    def glass(ctx, hs):
        hx, hy = hs[1]
        ctx.save()
        ctx.translate(hx - 10, hy - 30)
        ctx.rotate(-1.2 * u)
        poly(ctx, [(-34, -70), (34, -70), (26, 60), (-26, 60)])
        setc(ctx, (0.85, 0.95, 1.0), 0.5)
        ctx.fill_preserve()
        setc(ctx, OUTL)
        ctx.set_line_width(5)
        ctx.stroke()
        if level > 0.02:
            h = 120 * level
            poly(ctx, [(-30, 60 - h), (30, 60 - h), (26, 60), (-26, 60)])
            setc(ctx, hexc('#5fc3ff'), 0.85)
            ctx.fill()
        ctx.restore()
    person(ctx, px, py, 0.95, t, kw.get('expr', 'calm'), hands=hands, prop=glass,
           head_rot=-0.15 * u, hand_bend=(40, 60))
    # counter in front
    ctx.rectangle(0, 860, SW, 40)
    fill_stroke(ctx, mix(hexc('#3a3550'), hexc('#f2f2f2'), L), OUTL, 6)
    ctx.rectangle(0, 900, SW, 200)
    fill_stroke(ctx, mix(hexc('#28304a'), hexc('#4f8a8b'), L), OUTL, 6)
    for x in range(120, SW, 360):
        ctx.rectangle(x, 940, 260, 140)
        setc(ctx, OUTL)
        ctx.set_line_width(5)
        ctx.stroke()


def desk(ctx, world, t, lt, kw):
    L = key_or(kw, 'light', lt, 0.4)
    action = kw.get('action', 'read')
    room_base(ctx, L)
    window(ctx, 1250, 110, 480, 360, L, t)
    # shelf
    ctx.rectangle(180, 260, 520, 22)
    fill_stroke(ctx, mix(hexc('#2c2238'), hexc('#a8754a'), L), OUTL, 5)
    n_books = int(key_or(kw, 'books', lt, 3))
    cols = ['#d1495b', '#edae49', '#00798c', '#30638e', '#66a182', '#8d6cab', '#e07a5f', '#3d405b']
    for i in range(n_books):
        h = 120 + (i * 37) % 50
        ctx.rectangle(200 + i * 58, 260 - h, 50, h)
        fill_stroke(ctx, hexc(cols[i % len(cols)]), OUTL, 4)
    # lamp glow
    glow(ctx, 1560, 640, 520, hexc('#ffd28a'), 0.45 * (1 - L * 0.7))
    px, py = 880, 760
    nod = 0.0
    if action == 'nod':
        cyc = lt % 1.6
        nod = 0.45 * smooth((cyc - 0.2) / 0.9) * (1 if cyc < 1.2 else 0)
    if action in ('read', 'nod'):
        hands = [(px - 170, py - 90 + nod * 120), (px + 170, py - 90 + nod * 120)]

        def book(ctx, hs):
            (x0, y0), (x1, y1) = hs
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 20
            poly(ctx, [(cx - 190, cy - 110), (cx, cy - 90), (cx + 190, cy - 110), (cx + 190, cy + 110), (cx, cy + 130), (cx - 190, cy + 110)])
            fill_stroke(ctx, hexc('#d1495b'), OUTL, 6)
            ctx.move_to(cx, cy - 90)
            ctx.line_to(cx, cy + 130)
            ctx.stroke()
        prop = book
    elif action == 'stress':
        hands = [(px - 150, py - 400 + math.sin(t * 40) * 6), (px + 150, py - 400 - math.sin(t * 40) * 6)]
        prop = lambda ctx, hs: None
    else:
        wx = math.sin(lt * 9) * 40 + (lt * 60) % 140
        hands = [(px - 160, py + 20), (px + 40 + wx, py + 30 + math.sin(lt * 23) * 6)]

        def pen(ctx, hs):
            hx, hy = hs[1]
            ctx.move_to(hx + 10, hy - 10)
            ctx.line_to(hx + 70, hy - 90)
            setc(ctx, hexc('#30638e'))
            ctx.set_line_width(14)
            ctx.stroke()
        prop = pen
    expr = kw.get('expr', 'focus')
    ctx_expr = 'sleep' if (action == 'nod' and nod > 0.25) else expr
    # chair back
    rrect(ctx, px - 230, py - 420, 460, 520, 60)
    fill_stroke(ctx, mix(hexc('#2a2a40'), hexc('#5a6b8c'), L), OUTL, 6)
    if action == 'stress':
        sh = math.sin(t * 50) * 10
        person(ctx, px + sh, py, 1.0, t, 'scream', hands=hands, legs=False, hand_bend=(-60, 60))
    elif action == 'write':
        person(ctx, px, py, 1.0, t, ctx_expr, hands=hands, legs=False, look=(0.2, 1), head_rot=0.12, prop=None)
    else:
        person(ctx, px, py, 1.0, t, ctx_expr, hands=hands, legs=False, head_rot=nod, look=(0, 0.6), prop=None)
    # desk
    ctx.rectangle(0, 800, SW, 50)
    fill_stroke(ctx, mix(hexc('#2c2238'), hexc('#b9875a'), L), OUTL, 6)
    ctx.rectangle(0, 850, SW, 300)
    setc(ctx, mix(hexc('#1c1828'), hexc('#8a5f3c'), L))
    ctx.fill()
    if action == 'write':
        # journal with checklist
        rrect(ctx, px - 220, 760, 480, 70, 10)
        fill_stroke(ctx, (0.98, 0.97, 0.92), OUTL, 5)
    # desk lamp
    ctx.rectangle(1540, 640, 16, 160)
    fill_stroke(ctx, hexc('#30344f'), OUTL, 3)
    poly(ctx, [(1470, 650), (1630, 650), (1590, 570), (1510, 570)])
    fill_stroke(ctx, hexc('#ffd28a'), OUTL, 5)
    rrect(ctx, 1470, 780, 160, 26, 8)
    fill_stroke(ctx, hexc('#30344f'), OUTL, 4)
    prop(ctx, hands)
    for i, hp in enumerate(hands if action != 'stress' else []):
        ellipse(ctx, hp[0], hp[1], 30, 30)
        fill_stroke(ctx, SKIN, OUTL, 5)
    if action == 'write':
        items = kw.get('items', [])
        rrect(ctx, 1080, 200, 0, 0, 0)
        rrect(ctx, 60, 330, 560, 80 + 80 * len(items), 24)
        fill_stroke(ctx, (0.98, 0.97, 0.92), OUTL, 6)
        for i, (t_on, label) in enumerate(items):
            if lt >= t_on:
                y = 410 + i * 80
                rrect(ctx, 100, y - 40, 44, 44, 8)
                fill_stroke(ctx, (1, 1, 1), OUTL, 4)
                if lt >= t_on + 0.35:
                    ctx.move_to(108, y - 18)
                    ctx.line_to(120, y - 4)
                    ctx.line_to(140, y - 34)
                    setc(ctx, hexc('#22a356'))
                    ctx.set_line_width(8)
                    ctx.stroke()
                ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(40)
                ctx.move_to(170, y - 2)
                setc(ctx, OUTL)
                ctx.show_text(label)
    if ctx_expr == 'sleep':
        text_center(ctx, 'z', px + 240, py - 520 + math.sin(t * 3) * 10, 70, (1, 1, 1))


def park(ctx, world, t, lt, kw):
    L = key_or(kw, 'light', lt, 0.85)
    speed = 520
    off = t * speed
    g = cairo.LinearGradient(0, 0, 0, 700)
    g.add_color_stop_rgb(0, *mix(hexc('#2a2e6a'), hexc('#8cc4ff'), L))
    g.add_color_stop_rgb(1, *mix(hexc('#ff8a5c'), hexc('#ffd9a0'), L))
    ctx.set_source(g)
    ctx.paint()
    sx, sy = 1450, 520 - L * 200
    glow(ctx, sx, sy, 420, hexc('#ffcf6b'), 0.7)
    ellipse(ctx, sx, sy, 90, 90)
    setc(ctx, hexc('#ffe08a'))
    ctx.fill()
    for layer, (col, base, amp, k) in enumerate(((hexc('#7a8fc9'), 640, 90, 0.1), (hexc('#4f7d6b'), 720, 70, 0.3))):
        ctx.move_to(0, SH)
        for x in range(0, SW + 41, 40):
            wx = x + off * k
            ctx.line_to(x, base - amp * (0.6 + 0.4 * math.sin(wx / 230)) - 30 * math.sin(wx / 97))
        ctx.line_to(SW, SH)
        ctx.close_path()
        setc(ctx, mix(col, hexc('#ffb38a'), 0.15))
        ctx.fill()
    # trees
    for i in range(-1, 8):
        x = (i * 330 - (off * 0.6) % 330)
        ctx.rectangle(x - 18, 600, 36, 230)
        fill_stroke(ctx, hexc('#6b4a3a'), OUTL, 5)
        ellipse(ctx, x, 560, 120, 130)
        fill_stroke(ctx, hexc('#3f8f5a') if i % 2 else hexc('#4fa36a'), OUTL, 6)
    ctx.rectangle(0, 820, SW, 300)
    setc(ctx, hexc('#6dbb6a'))
    ctx.fill()
    ctx.rectangle(0, 880, SW, 110)
    fill_stroke(ctx, hexc('#d8c3a0'), OUTL, 5)
    for i in range(-1, 12):
        x = i * 200 - off % 200
        ctx.rectangle(x, 930, 90, 10)
        setc(ctx, hexc('#bfa880'))
        ctx.fill()
    # runner
    ph = t * 2 * math.pi * kw.get('cadence', 1.4)
    bob = abs(math.sin(ph)) * 22
    px, py = 900, 640 - bob
    k = 0.95
    feet = [(px - 20 + math.sin(ph) * 120, 930 - max(0, math.cos(ph)) * 60),
            (px + 20 - math.sin(ph) * 120, 930 - max(0, -math.cos(ph)) * 60)]
    hands = [(px - 110 - math.sin(ph) * 90, py - 90 + math.cos(ph) * 20),
             (px + 110 + math.sin(ph) * 90, py - 90 - math.cos(ph) * 20)]
    person(ctx, px, py, k, t, kw.get('expr', 'happy'), lean=0.08, hands=hands, feet=feet,
           hand_bend=(60, -60))
    # dust puffs
    for i in range(3):
        u = (t * 2.8 + i / 3) % 1
        ellipse(ctx, px - 200 - u * 300, 940 - u * 30, 20 + 30 * u, 14 + 20 * u)
        setc(ctx, (1, 1, 1), 0.5 * (1 - u))
        ctx.fill()


def checklist(ctx, world, t, lt, kw):
    g = cairo.LinearGradient(0, 0, SW, SH)
    g.add_color_stop_rgb(0, *hexc('#1d2b53'))
    g.add_color_stop_rgb(1, *hexc('#3a5a9a'))
    ctx.set_source(g)
    ctx.paint()
    glow(ctx, 1600, 200, 700, hexc('#ffcf6b'), 0.25)
    text_center(ctx, kw.get('title', 'After 30 days'), 960, 170, 84)
    for i, (t_on, label) in enumerate(kw['items']):
        if lt < t_on:
            continue
        a = smooth((lt - t_on) / 0.25)
        y = 330 + i * 170
        x = 330 - (1 - a) * 80
        rrect(ctx, x, y - 70, 1260, 130, 40)
        setc(ctx, (1, 1, 1), 0.12 * a)
        ctx.fill()
        pop = 1 + 0.3 * (1 - smooth((lt - t_on) / 0.2))
        ellipse(ctx, x + 70, y - 5, 42 * pop, 42 * pop)
        fill_stroke(ctx, hexc('#22c35e'), OUTL, 5, a)
        ctx.move_to(x + 50, y - 5)
        ctx.line_to(x + 65, y + 12)
        ctx.line_to(x + 92, y - 25)
        setc(ctx, (1, 1, 1), a)
        ctx.set_line_width(9)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(60)
        ctx.move_to(x + 150, y + 16)
        setc(ctx, (1, 1, 1), a)
        ctx.show_text(label)


def closeup(ctx, world, t, lt, kw):
    L = key_or(kw, 'light', lt, 1.0)
    setc(ctx, light_wall(L))
    ctx.paint()
    window(ctx, 1280, 120, 460, 520, L, t)
    glow(ctx, 1500, 380, 700, hexc('#ffcf6b'), 0.35 * L)
    cx = 860
    ctx.move_to(cx - 470, SH + 10)
    ctx.curve_to(cx - 470, 860, cx - 300, 790, cx, 790)
    ctx.curve_to(cx + 300, 790, cx + 470, 860, cx + 470, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    poly(ctx, [(cx - 120, 795), (cx + 120, 795), (cx, 960)])
    fill_stroke(ctx, hexc('#f2efe6'), OUTL, 5)
    ctx.rectangle(cx - 80, 700, 160, 110)
    fill_stroke(ctx, SKIN_SH, OUTL, 5)
    draw_head(ctx, cx, 500, 1.0, kw.get('expr', 'proud'), t, math.sin(t * 1.5) * 0.04)
    if kw.get('sparkle', True):
        for i in range(4):
            ph = (t * 0.8 + i * 0.25) % 1
            x, y = cx + 340 + i * 60, 260 + i * 90
            s = math.sin(math.pi * ph) * 30
            poly(ctx, [(x, y - s), (x + s * 0.3, y - s * 0.3), (x + s, y), (x + s * 0.3, y + s * 0.3),
                       (x, y + s), (x - s * 0.3, y + s * 0.3), (x - s, y), (x - s * 0.3, y - s * 0.3)])
            setc(ctx, hexc('#ffe08a'))
            ctx.fill()


engine.SCENES.update(bedroom=bedroom, kitchen=kitchen, desk=desk, park=park, checklist=checklist,
                     closeup=closeup)


# ----------------------------------------------------------------- overlays
def day_badge(label):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.2) * smooth((d - lt) / 0.2)
        pop = 1 + 0.25 * (1 - smooth(lt / 0.25))
        ctx.save()
        ctx.translate(960, 110)
        ctx.scale(pop, pop)
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(76)
        w = ctx.text_extents(label).x_advance
        rrect(ctx, -w / 2 - 50, -60, w + 100, 120, 60)
        setc(ctx, hexc('#ffcf3f'), a)
        ctx.fill_preserve()
        setc(ctx, OUTL, a)
        ctx.set_line_width(6)
        ctx.stroke()
        ctx.move_to(-w / 2, 27)
        setc(ctx, OUTL, a)
        ctx.show_text(label)
        ctx.restore()
    return fn


def energy_bar(level_key):
    def fn(ctx, lt, d):
        lv = level_key(lt)
        x, y = 1580, 60
        text_center(ctx, 'ENERGY', x + 140, y + 20, 34, (1, 1, 1))
        rrect(ctx, x, y + 40, 270, 80, 16)
        fill_stroke(ctx, (0.1, 0.1, 0.15), (1, 1, 1), 6)
        ctx.rectangle(x + 272, y + 62, 18, 36)
        setc(ctx, (1, 1, 1))
        ctx.fill()
        col = mix(hexc('#ff4b3a'), hexc('#22c35e'), clamp((lv - 0.2) / 0.6))
        if lv > 0.01:
            rrect(ctx, x + 12, y + 52, 246 * lv, 56, 10)
            setc(ctx, col)
            ctx.fill()
    return fn


# -------------------------------------------------------------------- audio
def alarm_beeps(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sign(np.sin(2 * np.pi * 2048 * t)) * 0.5 + np.sin(2 * np.pi * 4096 * t) * 0.2
    gate = ((t % 0.5) < 0.32) & (((t % 0.5) % 0.08) < 0.05)
    return lp(tone * gate, 6000) * 0.35


def chirp():
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    f = 3200 + 1800 * np.sin(np.pi * t / 0.12) + 300 * np.sin(2 * np.pi * 40 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.12) ** 2 * 0.25


def birds(dur, seed=1):
    r = random.Random(seed)
    out = np.zeros(int(dur * SR) + SR)
    tt = 0.1
    while tt < dur:
        for j in range(r.randint(2, 4)):
            c = chirp()
            i = int((tt + j * 0.13) * SR)
            out[i:i + len(c)] += c[:len(out) - i] * r.uniform(0.5, 1)
        tt += r.uniform(0.6, 1.6)
    return out[:int(dur * SR)]


def crickets(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 4600 * t) * ((np.sin(2 * np.pi * 28 * t) > 0.3) & ((t % 0.9) < 0.35))
    return lp(s, 7000) * 0.06


def footsteps(dur, rate=2.8):
    out = np.zeros(int(dur * SR) + SR)
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    step = (bp(noise(n), 150, 1800) * np.exp(-tt / 0.025) + np.sin(2 * np.pi * 90 * tt) * np.exp(-tt / 0.04)) * 0.5
    t0 = 0.0
    while t0 < dur:
        i = int(t0 * SR)
        out[i:i + n] += step[:len(out) - i]
        t0 += 1 / rate
    return out[:int(dur * SR)]


def page_flip():
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    return bp(noise(n), 1500, 7000) * np.sin(np.pi * t / 0.22) ** 2 * 0.5


def scribble(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    am = np.abs(np.sin(2 * np.pi * 4.5 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.3 * t))
    return bp(noise(n), 2500, 8000) * am * 0.25


def gulp():
    n = int(0.11 * SR)
    t = np.arange(n) / SR
    f = 380 - 1800 * t
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.11) * 0.5


def pop():
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    f = 500 + 6000 * t
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.025) * 0.6


def sad_trombone():
    out = []
    for f0, d in ((392, 0.25), (370, 0.25), (349, 0.25), (330, 0.7)):
        n = int(d * SR)
        t = np.arange(n) / SR
        vib = 1 + (0.01 * np.sin(2 * np.pi * 5 * t) if d > 0.5 else 0)
        ph = 2 * np.pi * np.cumsum(f0 * vib) / SR
        s = sum(np.sin(k * ph) / k for k in range(1, 9))
        out.append(lp(s, 1800) * env_adsr(n, 0.02, 0.06))
    return np.concatenate(out) * 0.3


def soft_whoosh():
    return whoosh(0.5, 0.5) * 0.6


def music_bed(dur, bright_from=None):
    """Original gentle progression (Cmaj7 - Am7 - Fmaj7 - G6) with pad + pluck."""
    n = int(dur * SR) + SR
    out = np.zeros(n)
    chords = [[261.6, 329.6, 392.0, 493.9], [220.0, 261.6, 329.6, 392.0],
              [174.6, 220.0, 261.6, 329.6], [196.0, 246.9, 293.7, 329.6]]
    bar = 2.4
    t_bar = np.arange(int(bar * SR)) / SR
    for b in range(int(dur / bar) + 1):
        ch = chords[b % 4]
        i = int(b * bar * SR)
        pad = sum(np.sin(2 * np.pi * f * t_bar) + 0.3 * np.sin(2 * np.pi * 2 * f * t_bar) for f in ch)
        pad *= np.sin(np.pi * t_bar / bar) ** 0.6
        seg = pad * 0.05
        if bright_from is None or b * bar >= bright_from:
            for j, f in enumerate(ch + [ch[1] * 2, ch[2] * 2, ch[3] * 2, ch[2] * 2]):
                tt = np.clip(t_bar - j * bar / 8, 0, None)
                seg += np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt / 0.25) * (t_bar >= j * bar / 8) * 0.06
        out[i:i + len(seg)] += seg[:n - i]
    return lp(out, 3500)[:int(dur * SR)]
