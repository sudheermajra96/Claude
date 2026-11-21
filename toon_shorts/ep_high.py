"""PSA (funny): don't drive high. Toronto. Two friends, smoke, red eyes, weaving at 18 km/h, police stop,
field sobriety test, 7-day impound. Ontario: drug-impaired = 90-day licence suspension + 7-day vehicle impound."""
from mkit import *
import toronto
import life
import street

X1 = 1.75
CURB_X = 2.55                       # parked against the curb (lane edge 3.5 - half width 0.92)
T_STOP = 20.2                       # truck comes to rest at the curb
Z_STOP = 0.0


def weave(t):
    if t < 17.4:
        return 1.55 + 0.8 * math.sin(t * 1.15) + 0.2 * math.sin(t * 2.7)
    u = smooth((t - 17.4) / 2.8)
    w = 1.55 + 0.8 * math.sin(17.4 * 1.15) + 0.2 * math.sin(17.4 * 2.7)
    return w + (CURB_X - w) * u


ego = Track(weave, Key([(0, 5.0), (17.4, 5.0), (20.2, 0.0), (40, 0)], 'lin'), T_STOP, Z_STOP, C_EGO,
            blink=lambda t: 'R' if 17.6 < t < 22 and (t * 1.25) % 1 < 0.5 else None)


class Police:
    col = '#f4f4f6'

    def __init__(self):
        self.tr = Track(Key([(0, X1), (17.6, X1), (20.4, CURB_X)]), Key([(0, 5.0), (17.4, 5.0), (20.6, 0), (40, 0)], 'lin'),
                        T_STOP, Z_STOP - 9.0, '#f4f4f6')
        self.brake = lambda t: 0.0
        self.blink = lambda t: None

    def pose(self, t):
        return self.tr.pose(t)

    def speed(self, t):
        return self.tr.speed(t)

    def steer(self, t):
        return 0.0

    def visible(self, t):
        return t > 13.0

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        return [((x, 0.9, z), lambda: police_car(ctx, view, x, z, h, t))]


def police_car(ctx, view, x, z, h, t):
    draw_car_round(ctx, view, x, z, h, '#f4f4f6', t)
    Lf = L(x, z, h)
    if view.ortho:
        p = view.pt((x, 0, z))
        on = (t * 3.2) % 1 < 0.5
        glow(ctx, p[0] - 0.4 * view.s, p[1], 1.6 * view.s, hexc('#ff2a2a') if on else hexc('#2a6bff'), 0.9)
        return
    for face, sx in (('left', -1), ('right', 1)):
        fill_poly(ctx, view, [Lf(sx * 0.93, 0.5, -1.6), Lf(sx * 0.93, 0.5, 1.6), Lf(sx * 0.93, 0.68, 1.6), Lf(sx * 0.93, 0.68, -1.6)], hexc('#1c1d26'))
    on = (t * 3.2) % 1 < 0.5
    for sx, col, lit in ((-1, hexc('#ff2a2a'), on), (1, hexc('#2a6bff'), not on)):
        q = [Lf(sx * 0.05, 1.43, -0.25), Lf(sx * 0.55, 1.43, -0.25), Lf(sx * 0.55, 1.58, -0.25), Lf(sx * 0.05, 1.58, -0.25)]
        fill_poly(ctx, view, q, col if lit else mix(col, (0, 0, 0), 0.6), OUTL, 1.5)
        if lit:
            c = Lf(sx * 0.3, 1.5, -0.25)
            p, s = view.pt(c), view.scale(c)
            if p and s:
                glow(ctx, p[0], p[1], min(1.4 * s, 260), col, 0.55)


POL = Police()


def follower(tA, zA, col, x=X1, v=None):
    return Track(x, v or Key([(0, 5.0), (40, 5.0)], 'lin'), tA, zA, col)


# a queue behind the slow car; one gets fed up and passes on the left (no oncoming traffic then)
passer = Track(Key([(0, X1), (10.6, X1), (11.4, -1.75), (13.0, -1.75), (13.8, X1), (40, X1)]),
               Key([(0, 5.0), (10.6, 5.0), (11.6, 12.0), (13.6, 12.0), (14.4, 9.0), (40, 9.0)], 'lin'), 10.6, ego.z(10.6) - 8.5, '#3a7bd5')
behind = follower(10.6, ego.z(10.6) - 16.0, '#f2a541')
behind.vis = lambda t: t < 13.0


class Vis:
    def __init__(self, a, f):
        self.a, self.f, self.col = a, f, a.col

    def __getattr__(self, k):
        return getattr(self.a, k)

    def visible(self, t):
        return self.f(t)


TRAFFIC = [Vis(passer, lambda t: t < 16.0), Vis(behind, lambda t: t < 13.0)]


class Tow:
    """Flatbed tow truck carrying the red car, pulling away from the curb."""
    col = '#f2c230'

    def __init__(self):
        self.tr = Track(Key([(0, CURB_X), (29.6, CURB_X), (31.4, X1)]), Key([(0, 0), (29.0, 0), (31.0, 4.0), (40, 6)], 'lin'),
                        29.0, Z_STOP + 6.0, '#f2c230')
        self.brake = lambda t: 0.0
        self.blink = lambda t: 'L' if (t * 1.25) % 1 < 0.5 and t < 31.5 else None

    def pose(self, t):
        return self.tr.pose(t)

    def speed(self, t):
        return self.tr.speed(t)

    def steer(self, t):
        return 0.0

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        return [((x, 1.5, z), lambda: tow_truck(ctx, view, x, z, h, t, self.blink(t)))]


class Lift:
    """View wrapper that draws things raised by dy metres (car on the flatbed)."""

    def __init__(self, v, dy):
        self.v, self.dy = v, dy
        self.pos, self.ortho = v.pos, v.ortho

    def pt(self, P):
        return self.v.pt((P[0], P[1] + self.dy, P[2]))

    def poly(self, pts):
        return self.v.poly([(p[0], p[1] + self.dy, p[2]) for p in pts])

    def depth(self, P):
        return self.v.depth((P[0], P[1] + self.dy, P[2]))

    def scale(self, P):
        return self.v.scale((P[0], P[1] + self.dy, P[2]))


def tow_truck(ctx, view, x, z, h, t, bl):
    """Origin = cab rear axle; flatbed behind it, carrying the red car."""
    Lf = L(x, z, h)
    if view.ortho:
        fill_poly(ctx, view, [Lf(-1.25, 0, -8.5), Lf(1.25, 0, -8.5), Lf(1.25, 0, 6.15), Lf(-1.25, 0, 6.15)], hexc('#f2c230'), OUTL, 4)
        draw_car_top_g(ctx, view, x - math.sin(h) * 4.6, z - math.cos(h) * 4.6, h, C_EGO, t)
        return
    tractor_det(ctx, view, x, z, h, '#f2c230', False, bl)
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    lbox(ctx, view, Lf, h, -1.25, 1.25, 0.95, 1.2, -9.0, -0.2, allc(hexc('#3a3d48')), 2)
    for wz in (-6.0, -7.3):
        for wx in (-1.0, 1.0):
            lbox(ctx, view, Lf, h, wx - 0.2, wx + 0.2, 0, 0.95, wz - 0.45, wz + 0.45, allc(hexc('#1c1c22')), 2)
    cx, cz = x - math.sin(h) * 4.6, z - math.cos(h) * 4.6
    draw_car_round(ctx, Lift(view, 1.2), cx, cz, h, C_EGO, t)
    for sx in (-1, 1):
        q = [Lf(sx * 0.4, 1.95, 1.75), Lf(sx * 0.95, 1.95, 1.75), Lf(sx * 0.95, 2.1, 1.75), Lf(sx * 0.4, 2.1, 1.75)]
        on = (t * 2) % 1 < 0.5
        fill_poly(ctx, view, q, AMBER if on else hexc('#7a4a00'), OUTL, 1.5)


TOW = Tow()


# ---------------------------------------------------------------- pedestrians (field test + aftermath)
FRIEND_TOP, HERO_TOP = '#5a7d4f', '#d0912c'
test_walk = Ped(Key([(0, 4.6), (23.6, 4.6), (27.0, 4.6)], 'lin'), Key([(0, Z_STOP + 1.5), (23.6, Z_STOP + 1.5), (27.0, Z_STOP + 7.5)], 'lin'),
                top=HERO_TOP, hair='#3a2316')
_tx = test_walk.x
test_walk.x = lambda t: _tx(t) + (0.55 * math.sin((t - 23.6) * 4.2) if 23.6 < t < 27.0 else 0.0)
friend_wait = Ped(const(5.6), const(Z_STOP - 0.5), top=FRIEND_TOP, hair='#1d1613')
sad1 = Ped(const(4.8), const(Z_STOP + 2.0), top=HERO_TOP)
sad2 = Ped(const(5.5), const(Z_STOP + 2.6), top=FRIEND_TOP, hair='#1d1613')
others_peds = [Ped(const(8.6), Key([(0, -40), (40, 5)], 'lin'), top='#9a6fd0'), Ped(const(-8.6), Key([(0, 30), (40, -20)], 'lin'), top='#3a7bd5')]


def city_extras(ctx, view, t):
    out = []
    if 20.2 <= t < 29.0 or t < 3.0:
        out += officer_items(ctx, view, t)
    if t >= 13.0 or t < 3.0:
        out += smoke_items(ctx, view, t)
    return out


def officer_pos(t):
    if t < 3.0:
        t += 20.6
    if t < 23.6:
        u = smooth((t - 20.4) / 0.8)
        return 0.75 - 0.2 * u, (Z_STOP - 6.0) + (6.3 * u)
    return 6.8, Z_STOP - 0.5


def officer_items(ctx, view, t):
    x, z = officer_pos(t)
    if view.ortho:
        return []

    def draw():
        p, s = view.pt((x, 1.4, z)), view.scale((x, 1.4, z))
        g = view.pt((x, 0.0, z))
        if p and s and g and s > 3:
            k = 0.115 * s / 100
            top = p[1] + 300 * k
            for dx in (-0.16, 0.16):
                lx = p[0] + dx * s
                ctx.rectangle(lx - 0.1 * s, top, 0.2 * s, g[1] - top - 0.05 * s)
                fill_stroke(ctx, hexc('#16294d'), OUTL, max(1, s / 60))
                ellipse(ctx, lx + 0.04 * s, g[1] - 0.04 * s, 0.16 * s, 0.07 * s)
                fill_stroke(ctx, hexc('#111118'), OUTL, max(1, s / 60))
            street.officer(ctx, p[0], p[1], k, t, 'write', (t - 21.0) % 3, 'flat')
    return [((x, 1.0, z), draw)]


def smoke_puff(ctx, view, P, r, a):
    p, s = view.pt(P), view.scale(P)
    if not p or not s:
        return
    rr = r * s
    if rr < 1:
        return
    ellipse(ctx, p[0], p[1], rr, rr * 0.85)
    setc(ctx, (0.88, 0.89, 0.9), a)
    ctx.fill()


def smoke_items(ctx, view, t):
    """Smoke leaking from the car windows (and a big cloud when the window rolls down)."""
    tt = t + 20.6 if t < 3.0 else t
    if tt >= 29.0 or view.ortho:
        return []
    x, z, h = ego.pose(tt)
    big = smooth((tt - 21.3) / 0.5) if 21.3 <= tt < 23.6 else 0.0
    out = []
    rnd = random.Random(3)
    n = 10 + int(26 * big)
    for i in range(n):
        ph = (tt * (0.35 + 0.25 * rnd.random()) + rnd.random()) % 1.0
        side = -1
        sx = x + side * (0.95 + ph * (1.2 + 3.5 * big))
        sy = 1.25 + ph * (1.2 + 1.8 * big) + rnd.uniform(-0.1, 0.1)
        sz = z + rnd.uniform(-0.6, 0.6) - ph * (0.0 if big else ego.speed(tt) * 0.6)
        r = (0.18 + 0.5 * ph) * (1 + 2.2 * big)
        a = (0.75 if big else 0.4) * (1 - ph * 0.8)
        out.append(((sx, sy, sz), lambda P=(sx, sy, sz), r=r, a=a: smoke_puff(ctx, view, P, r, a)))
    return out


city = Street('city', n=1, median='yellow', cross=None, sidewalk=True, seed=51, skyline=lambda c, v: toronto.skyline(c, v),
              extras=city_extras, hmin=8, hmax=18, setback=1.0,
              palette=['#c9b9a6', '#a9b8c6', '#d8cfc0', '#8f9aa8', '#b7a28a', '#9fb3a0'])

city.items = [it for it in city.items if not (it[0] in ('tree', 'lamp') and it[1][0] > 0 and -24 < it[1][1] < 26)]
world = SegWorld(36.0, [
    (0.0, 3.0, Shift(ego, 20.6), [Shift(POL, 20.6)], []),
    (3.0, 20.2, ego, TRAFFIC + [POL], others_peds),
    (20.2, 23.6, ego, [POL], others_peds),
    (23.6, 29.0, ego, [POL], [test_walk, friend_wait] + others_peds),
    (29.0, 99, TOW, [POL], [sad1, sad2] + others_peds)], city, 'kmh')


# ---------------------------------------------------------------- the two-shot inside the car
life.LIFE_EXPR['stoned'] = dict(brow=-0.05, tilt=-0.15, eye=0.42, pupil=1.0, mouth='grin', mo=0.9)
life.LIFE_EXPR['stoned2'] = dict(brow=0.1, tilt=-0.2, eye=0.38, pupil=1.0, mouth='smile', mo=0.3)


def red_eyes(ctx, cx, cy, k, eo, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(k, k)
    for s in (-1, 1):
        ex, ey = s * 92, 10
        ctx.save()
        ellipse(ctx, ex, ey, 52, max(2, 52 * eo))
        ctx.clip()
        ellipse(ctx, ex, ey, 52, 52)
        setc(ctx, hexc('#ff6a6a'), 0.5)
        ctx.fill()
        for a in (-0.4, 0.2, 2.8, 3.4):
            ctx.move_to(ex + math.cos(a) * 50, ey + math.sin(a) * 50 * eo)
            ctx.line_to(ex + math.cos(a) * 28, ey + math.sin(a) * 22 * eo)
        setc(ctx, hexc('#d62828'))
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.restore()
        # puffy lower lid
        ctx.move_to(ex - 46, ey + 52 * eo * 0.6)
        ctx.curve_to(ex - 20, ey + 52 * eo + 14, ex + 20, ey + 52 * eo + 14, ex + 46, ey + 52 * eo * 0.6)
        setc(ctx, hexc('#c97a7a'))
        ctx.set_line_width(7)
        ctx.stroke()
    ctx.restore()


def beanie(ctx, cx, cy, k, rot):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(k, k)
    ctx.move_to(-250, -110)
    ctx.curve_to(-250, -360, 250, -360, 250, -110)
    ctx.close_path()
    fill_stroke(ctx, hexc('#2f6f9f'), OUTL, 7)
    rrect(ctx, -262, -150, 524, 70, 30)
    fill_stroke(ctx, hexc('#24577d'), OUTL, 6)
    ellipse(ctx, 0, -350, 50, 45)
    fill_stroke(ctx, hexc('#e0393e'), OUTL, 6)
    ctx.restore()


def two_shot(ctx, w, t, lt, kw):
    # through the windshield: dim interior, haze, two faces
    setc(ctx, hexc('#2a2a36'))
    ctx.paint()
    g = cairo.LinearGradient(0, 0, 0, 520)
    g.add_color_stop_rgb(0, *hexc('#5d6b80'))
    g.add_color_stop_rgb(1, *hexc('#3a4252'))
    ctx.set_source(g)
    rrect(ctx, 160, 60, 1600, 520, 90)
    ctx.fill()
    for sxp in (560, 1360):
        rrect(ctx, sxp - 270, 260, 540, 900, 120)
        fill_stroke(ctx, hexc('#3d3d50'), OUTL, 6)
        rrect(ctx, sxp - 160, 120, 320, 200, 70)
        fill_stroke(ctx, hexc('#46465c'), OUTL, 6)
    bob = math.sin(lt * 7) * 8
    for i, (px, expr, hair, skin, top, beanie_on) in enumerate(((560, 'stoned', life.HAIR, life.SKIN, life.JACKET, False),
                                                                (1360, 'stoned2', hexc('#1d1613'), hexc('#c58c6b'), hexc(FRIEND_TOP), True))):
        rot = math.sin(lt * 1.3 + i) * 0.06
        ctx.move_to(px - 330, SH + 10)
        ctx.curve_to(px - 330, 860, px - 200, 800, px, 800)
        ctx.curve_to(px + 200, 800, px + 330, 860, px + 330, SH + 10)
        ctx.close_path()
        fill_stroke(ctx, top, OUTL, 6)
        oh, osk = life.HAIR, life.SKIN
        life.HAIR, life.SKIN = hair, skin
        life.draw_head(ctx, px, 520 + (bob if i == 0 else -bob), 0.62, expr, t, rot, (0.2 if i == 0 else -0.2, 0.3))
        life.HAIR, life.SKIN = oh, osk
        eo = life.LIFE_EXPR[expr]['eye']
        red_eyes(ctx, px, 520 + (bob if i == 0 else -bob), 0.62, eo, rot)
        if beanie_on:
            beanie(ctx, px, 520 - bob, 0.62, rot)
    # drifting smoke haze
    rnd = random.Random(7)
    for k in range(34):
        x0, y0, r = rnd.uniform(0, SW), rnd.uniform(0, SH), rnd.uniform(60, 200)
        x = (x0 + lt * rnd.uniform(15, 45)) % (SW + 200) - 100
        y = y0 - (lt * rnd.uniform(10, 30)) % 200
        ellipse(ctx, x, y, r, r * 0.7)
        setc(ctx, (0.88, 0.89, 0.9), 0.13)
        ctx.fill()
    setc(ctx, (0.9, 0.9, 0.92), 0.18)
    ctx.paint()
    # windshield frame + dashboard edge (we look in from the hood)
    setc(ctx, hexc(C_EGO))
    ctx.rectangle(-10, 980, SW + 20, 120)
    ctx.fill()
    ctx.rectangle(-10, 965, SW + 20, 20)
    setc(ctx, OUTL)
    ctx.fill()
    for xx in (0, SW - 130):
        ctx.rectangle(xx, 0, 130, SH)
        setc(ctx, hexc(C_EGO))
        ctx.fill()
    ctx.rectangle(-10, -10, SW + 20, 60)
    ctx.fill()
    # giggle marks
    if (lt * 2) % 1 < 0.6:
        for px in (560, 1360):
            text_center(ctx, 'hehe', px + 230, 260 + math.sin(lt * 9) * 10, 54, (1, 1, 1))


def window_cloud(ctx, w, t, lt, kw):
    tt = t + 20.6 if t < 3.0 else t
    x, z, h = ego.pose(tt)
    view = look_at((x - 4.0, 2.0, z + 6.0), (x - 0.6, 1.3, z - 0.4), 1050)
    draw_scene(ctx, view, w, t)
    if (tt - 21.6) % 1.4 < 0.7 and tt > 21.6:
        ox, oz = officer_pos(tt)
        p = view.pt((ox, 2.0, oz))
        if p:
            outlined_text(ctx, '*cough*', p[0] - 40, p[1] - 30, 64, (1, 1, 1), lw=12)


def ticket_card(ctx, w, t, lt, kw):
    g = cairo.LinearGradient(0, 0, SW, SH)
    g.add_color_stop_rgb(0, *hexc('#1a1d2e'))
    g.add_color_stop_rgb(1, *hexc('#2b3150'))
    ctx.set_source(g)
    ctx.paint()
    a = smooth(lt / 0.3)
    text_center(ctx, 'Driving HIGH in Ontario = impaired driving', 960, 150, 58, hexc('#ffd23f'), a=a)
    rows = [(0.5, '90-day licence suspension', '#e0393e'), (1.3, '7-day vehicle impound', '#e0393e'),
            (2.1, 'Possible criminal charge', '#e0393e'), (2.9, 'Same law as drunk driving', '#2f6f9f')]
    for i, (t0, txt, col) in enumerate(rows):
        if lt < t0:
            continue
        b = smooth((lt - t0) / 0.25)
        y = 330 + i * 165
        rrect(ctx, 360 - 80 * (1 - b), y - 62, 1200, 120, 40)
        setc(ctx, (1, 1, 1), 0.1 * b)
        ctx.fill()
        ellipse(ctx, 440, y, 40, 40)
        fill_stroke(ctx, hexc(col), (1, 1, 1), 4, b)
        text_center(ctx, '!', 440, y + 22, 58, (1, 1, 1), a=b)
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(60)
        ctx.move_to(520, y + 22)
        setc(ctx, (1, 1, 1), b)
        ctx.show_text(txt)


engine.SCENES.update(two_shot=two_shot, window_cloud=window_cloud, ticket_card=ticket_card)


def big_caption(text, y=230, size=96, col=(1, 1, 1)):
    return big_text(text, y, size, col)


def stamp(text):
    def fn(ctx, lt, d):
        a = smooth(lt / 0.15)
        sc = 1 + 0.8 * (1 - a)
        ctx.save()
        ctx.translate(960, 300)
        ctx.rotate(-0.12)
        ctx.scale(sc, sc)
        rrect(ctx, -360, -95, 720, 170, 20)
        setc(ctx, hexc('#d62828'), a)
        ctx.set_line_width(14)
        ctx.stroke()
        text_center(ctx, text, 0, 38, 110, hexc('#d62828'), a=a)
        ctx.restore()
    return fn


HUDS = dict(cam='chase')
defs = [
    (3.0, 'window_cloud', dict()),                                                                   # hook
    (6.0, 'm_cam', dict(cam='follow', off=(-5.0, 2.4, -7.5), look=(0.5, 1.0, 3.0), f=950, hud=False)),   # title
    (9.6, 'two_shot', dict()),                                                                       # red eyes
    (13.0, 'm_cam', dict(cam='chase')),                                                              # weaving + honks
    (15.6, 'm_cam', dict(cam='inside')),                                                             # passer honks
    (17.6, 'm_mirror', dict(side='L')),                                                              # police in mirror
    (20.6, 'm_cam', dict(cam='follow', off=(-6.0, 4.0, -15.0), look=(1.0, 0.8, 3.0), f=1000)),       # pull over
    (23.6, 'window_cloud', dict()),                                                                  # smoke cloud
    (27.0, 'm_cam', dict(cam='fixed', pos=(1.2, 1.7, Z_STOP + 11.5), target=(4.8, 1.0, Z_STOP + 3.5), f=1000, hud=False)),  # field test
    (31.6, 'm_cam', dict(cam='fixed', pos=(-5.0, 3.6, Z_STOP + 17.0), target=(3.0, 1.2, Z_STOP + 3.0), f=950, hud=False)),  # tow
    (36.0, 'ticket_card', dict()),
]
shots = build_shots(defs)
video = Video(["DON'T drive high", '(it never ends well)'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]


def speed_note(ctx, lt, d):
    label(ctx, 960, 200, '18 km/h... in a 60 zone', '#e0393e', 58)


video.overlays = [
    (0.2, 3.0, big_text('"Officer... is there a problem?"', 250, 92, hexc('#ffd23f'), 0.2)),
    (3.0, 6.0, big_text('Driving HIGH: what really happens', 260, 84, (1, 1, 1))),
    (3.2, 5.8, location_tag('Toronto, Ontario')),
    (S[2] + 0.1, E[2], caption('Red eyes. Smoke. "I\'m fine to drive."')),
    (S[3] + 0.3, E[3], speed_note),
    (S[3] + 0.1, E[3], caption('Weaving all over the lane')),
    (S[4] + 0.1, E[4], caption('Everyone behind is NOT impressed')),
    (S[5] + 0.1, E[5], caption('Uh oh...')),
    (S[6] + 0.1, E[6], caption('Pulled over')),
    (S[7] + 0.1, E[7], caption('Window down... the smoke says it all')),
    (S[8] + 0.1, E[8], caption('Field sobriety test: not going great')),
    (S[9] + 0.1, E[9], caption('Car towed. Walking home.')),
    (S[9] + 0.6, E[9], stamp('IMPOUNDED')),
    (S[10] + 3.6, E[10], lambda ctx, lt, d: label(ctx, 960, 1010, "Who's YOUR designated driver? Comment!", '#22a356', 52)),
]


def giggle(d=1.2, f0=260):
    out = np.zeros(int(d * SR) + SR)
    tt = 0.0
    k = 0
    while tt < d:
        n = int(0.09 * SR)
        x = np.arange(n) / SR
        f = f0 * (1.15 if k % 2 else 1.0) * (1 + 0.1 * np.sin(2 * np.pi * 7 * x))
        s = sum(np.sin(2 * np.pi * np.cumsum(f * h) / SR) / h for h in (1, 2, 3))
        s = bp(s, 300, 2500) + bp(noise(n), 1500, 4000) * 0.3
        place(out, s * np.sin(np.pi * x / 0.09) * 0.35, tt)
        tt += 0.14 + 0.02 * (k % 3)
        k += 1
    return out[:int(d * SR)]


def cough():
    out = np.zeros(int(0.9 * SR))
    for o in (0.0, 0.28, 0.5):
        n = int(0.18 * SR)
        x = np.arange(n) / SR
        place(out, bp(noise(n), 250, 2200) * np.exp(-x / 0.06) * 0.8, o)
    return out


def winch(d):
    t = np.arange(int(d * SR)) / SR
    return lp(np.sign(np.sin(2 * np.pi * 90 * t)) * 0.3, 900) * 0.3 * env_adsr(len(t), 0.1, 0.2)


def window_motor(d=0.8):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * (180 + 20 * t) * t) * 0.3 + lp(noise(len(t)), 600) * 0.2) * env_adsr(len(t), 0.05, 0.1) * 0.6


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur, 1.2), 0, 0.22)
    m.add(engine_idle(video.dur), 0, 0.12)
    # hook
    m.add(window_motor(0.8), 0.0, 0.9, -0.3)
    m.add(whoosh(1.2, 0.3), 0.4, 0.8, -0.3)
    m.add(cough(), 0.9, 1.0, -0.4)
    m.add(boing(), 2.3, 0.6)
    m.add(impact(), 3.0, 0.4)
    # in the car
    m.add(giggle(2.6, 240), S[2] + 0.3, 1.0, -0.2)
    m.add(giggle(2.2, 300), S[2] + 1.0, 0.9, 0.3)
    # weaving: horns
    for k, tt in enumerate((9.9, 10.8, 11.6, 12.4, 13.4)):
        m.add(horn(0.5 + 0.3 * (k % 2), doppler=[0.9 + 0.06 * (k % 3)] * 4), tt, 0.75, -0.2 + 0.1 * k)
    m.add(car_pass(1.8, 0.5, 110), 12.0, 0.9, np.linspace(-0.6, 0.3, int(1.8 * SR)))
    m.add(rumble(1.0), 11.0, 0.6)
    # police
    m.add(street.siren_whoop(2), S[5] + 0.3, 1.0)
    m.add(heartbeat(3, 110), S[5] + 0.8, 0.9)
    m.add(click(), 17.6, 0.8)
    indicator(m, 17.6, 22.0, 1.0, 0.2)
    m.add(brake_squeal(0.8), 19.6, 0.15)
    # window cloud
    m.add(window_motor(0.8), 21.0, 0.9, -0.3)
    m.add(whoosh(1.4, 0.3), 21.3, 0.8, -0.3)
    for tt in (21.8, 23.2):
        m.add(cough(), tt, 1.0, -0.4)
    m.add(giggle(0.8, 260), 22.6, 0.6, 0.2)
    # field test
    for k in range(7):
        m.add(footsteps(0.12, 100), 23.8 + k * 0.45, 0.3, 0.2)
    m.add(boing(), 25.2, 0.7)
    m.add(slide_whistle(700, 300, 0.8), 26.0, 0.5)
    # tow
    m.add(winch(1.4), S[9] + 0.2, 0.8)
    m.add(impact(), S[9] + 0.6, 0.5)
    m.add(sad_trombone(), S[9] + 1.2, 0.9)
    m.add(car_pass(2.0, 0.6, 80), 30.4, 0.6)
    # card
    for k in range(4):
        m.add(pop(), S[10] + 0.5 + k * 0.8, 0.8)
    m.add(chime(), S[10] + 3.6, 0.7)
    return m.out(video.dur)


def verify():
    print('weave min x (yellow line at 0.2, car half-width 0.92):', round(min(weave(t) for t in np.arange(3, 17.4, 0.01)), 2),
          'max', round(max(weave(t) for t in np.arange(3, 20.2, 0.01)), 2), 'curb park x', CURB_X)
    print('passer vs ego', min_gap([ego, passer], 3, 16, lat=1.9), 'police vs ego', min_gap([ego, POL.tr], 13, 29, lat=1.9))
    print('tow start: car on bed vs police front', round((TOW.pose(29.0)[1] - 4.6 - 2.2) - (POL.pose(29.0)[1] + 2.2), 2))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    else:
        run(video, sound, 'high.mp4')
