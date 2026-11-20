"""Backing a tractor-trailer into a loading dock (90-degree alley dock), the right way. Dallas, Texas.
Real tractor-trailer kinematics (trucksim.py)."""
import math
import random

from citykit import *
import trucksim as T

engine.DAY = True
P = {'x0': -30.0, 'z0': 15.0, 'x_turn': 16, 't_swing': 2.0, 't_straight': 2.0, 't_pause': 2.0, 'goal_z': 24,
     't_goal': 2.5, 'v_rev': 3.0, 'look': 8, 'k1': 2.2, 'k2': 5.0, 'settle': 4.0, 'v_fwd': 5.0}
OFF = 5.0                  # video t = sim t - OFF
LOG = np.array([l[:7] for l in T.simulate(P)])
PH = [l[7] for l in T.simulate(P)]
G = LOG[:, 0] - OFF
T_PAUSE = G[PH.index('pause')]
T_REV = G[PH.index('rev')]
T_GOAL0 = G[PH.index('goal')]
T_GOAL1 = G[len(PH) - 1 - PH[::-1].index('goal')]
T_DOCK = G[PH.index('done')]
DOOR_W, DOOR_SP = 3.0, 4.3
RED_CAB = '#c8312f'


def fx(arr, t):
    return float(np.interp(t, G, arr))


class Truck:
    col = RED_CAB

    def __init__(self):
        self.brake = lambda t: 0.0
        b = blinking([(T_PAUSE - 1.0, T_DOCK + 0.4)], 0.8)
        self.haz = lambda t: b(t) > 0.5

    def state(self, t):
        return fx(LOG[:, 1], t), fx(LOG[:, 2], t), fx(LOG[:, 3], t), fx(LOG[:, 4], t)

    def pose(self, t):
        x, z, h1, h2 = self.state(t)
        return x, z, h1

    def trailer_axle(self, t):
        x, z, h1, h2 = self.state(t)
        return x - T.L2 * math.sin(h2), z - T.L2 * math.cos(h2), h2

    def speed(self, t):
        return abs(fx(LOG[:, 5], t))

    def vel(self, t):
        return fx(LOG[:, 5], t)

    def delta(self, t):
        return fx(LOG[:, 6], t)

    def steer(self, t):
        return clamp(self.delta(t) * 2.6, -1.6, 1.6)

    def blink(self, t):
        return None

    def visible(self, t):
        return True

    def items(self, ctx, view, t):
        x, z, h1, h2 = self.state(t)
        rev = self.vel(t) < -0.05
        haz = self.haz(t)
        tc = (x + math.sin(h1) * 2.5, 1.5, z + math.cos(h1) * 2.5)
        trc = (x - math.sin(h2) * 7.2, 2.0, z - math.cos(h2) * 7.2)
        if view.ortho:
            return [(tc, lambda: tractor_top(ctx, view, x, z, h1, haz)), ((trc[0], 1.6, trc[2]), lambda: trailer_top(ctx, view, x, z, h2, haz))]
        return [(tc, lambda: tractor3(ctx, view, x, z, h1, haz)), (trc, lambda: trailer3(ctx, view, x, z, h2, haz, rev))]


def tractor3(ctx, view, x, z, h, haz):
    Lf = L(x, z, h)
    d = view.depth((x, 1, z))
    lw = max(1.5, min(4, 60 / max(d, 1)))
    red, red_d = hexc(RED_CAB), mix(hexc(RED_CAB), (0, 0, 0), 0.25)
    chrome, black, glass = hexc('#d9dde4'), hexc('#1c1c22'), hexc('#2a3448')
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    for wz in (-1.3, 0.0, 4.0):
        for wx in (-1.05, 1.05):
            lbox(ctx, view, Lf, h, wx - 0.2, wx + 0.2, 0, 1.0, wz - 0.5, wz + 0.5, allc(black), lw)
    lbox(ctx, view, Lf, h, -0.5, 0.5, 0.6, 1.0, -2.0, 5.6, allc(hexc('#3a3d48')), lw)
    lbox(ctx, view, Lf, h, -0.9, 0.9, 1.0, 1.15, -1.0, 0.8, allc(hexc('#2a2c33')), lw)          # fifth wheel
    for sx in (-1, 1):
        lbox(ctx, view, Lf, h, sx * 1.25 - 0.3, sx * 1.25 + 0.3, 0.6, 1.2, 1.0, 2.6, allc(chrome), lw)   # fuel tanks
    lbox(ctx, view, Lf, h, -1.25, 1.25, 1.0, 3.7, 0.2, 1.6, {'front': red_d, 'back': red_d, 'left': red_d, 'right': red_d, 'top': red_d}, lw)
    vis = lbox(ctx, view, Lf, h, -1.25, 1.25, 1.0, 3.4, 1.6, 3.6, {'front': red, 'back': red, 'left': red_d, 'right': red_d, 'top': red}, lw)
    hv = lbox(ctx, view, Lf, h, -1.0, 1.0, 1.0, 2.3, 3.6, 5.9, {'front': chrome, 'back': red, 'left': red_d, 'right': red_d, 'top': red}, lw)
    if 'front' in vis:
        face_rect(ctx, view, Lf, 'front', -1.1, 1.1, 2.4, 3.2, 3.61, glass)
    for side, face, dx in ((-1, 'left', -1.26), (1, 'right', 1.26)):
        if face in vis:
            face_rect(ctx, view, Lf, face, 2.2, 3.4, 2.2, 3.1, dx, glass)
    for sx in (-1, 1):
        lbox(ctx, view, Lf, h, sx * 1.3 - 0.08, sx * 1.3 + 0.08, 2.6, 4.4, 1.4, 1.56, allc(chrome), lw)   # stacks
        lbox(ctx, view, Lf, h, sx * 1.55 - 0.1, sx * 1.55 + 0.1, 2.3, 3.0, 3.3, 3.45, allc(hexc('#2a2c33')), lw)  # mirrors
    if 'front' in hv:
        for sx in (-1, 1):
            face_rect(ctx, view, Lf, 'front', sx * 0.75 - 0.18, sx * 0.75 + 0.18, 1.4, 1.65, 5.91, hexc('#fff6d8'))
            on = haz
            face_rect(ctx, view, Lf, 'front', sx * 0.93 - 0.06, sx * 0.93 + 0.06, 1.75, 1.95, 5.92,
                      AMBER if on else hexc('#7a4a00'), AMBER if on else None, 1.4)


def trailer3(ctx, view, x, z, h, haz, rev=False, col='#f4f4f6', stripe='#2f6f9f', docked=False):
    Lf = L(x, z, h)
    d = view.depth((x, 2, z - math.cos(h) * 7))
    lw = max(1.5, min(4, 80 / max(d, 1)))
    white = hexc(col)
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    for wz in (-12.3, -11.0):
        for wx in (-1.05, 1.05):
            lbox(ctx, view, Lf, h, wx - 0.2, wx + 0.2, 0, 1.0, wz - 0.5, wz + 0.5, allc(hexc('#1c1c22')), lw)
    if docked:
        for wx in (-0.9, 0.9):
            lbox(ctx, view, Lf, h, wx - 0.08, wx + 0.08, 0, 1.2, -2.6, -2.4, allc(hexc('#3a3d48')), lw)
    lbox(ctx, view, Lf, h, -1.2, 1.2, 0.45, 0.6, -15.35, -15.0, allc(hexc('#d62828')), lw)          # ICC bumper
    vis = lbox(ctx, view, Lf, h, -1.3, 1.3, 1.2, 4.1, -15.3, 0.9,
               {'front': white, 'back': mix(white, (0, 0, 0), 0.06), 'left': mix(white, (0, 0, 0), 0.1),
                'right': mix(white, (0, 0, 0), 0.04), 'top': white}, lw)
    for face, dx in (('left', -1.31), ('right', 1.31)):
        if face in vis:
            face_rect(ctx, view, Lf, face, -14.8, 0.4, 1.4, 1.7, dx, hexc(stripe))
            if not docked:
                face_rect(ctx, view, Lf, face, -11.0, -3.0, 2.3, 3.3, dx, hexc('#e8eef4'))
    if 'back' in vis:
        face_rect(ctx, view, Lf, 'back', -0.02, 0.02, 1.3, 4.0, -15.31, OUTL)
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'back', s * 1.1 - 0.12, s * 1.1 + 0.12, 1.3, 1.6, -15.32, hexc('#b01818'))
            face_rect(ctx, view, Lf, 'back', s * 1.1 - 0.1, s * 1.1 + 0.1, 1.65, 1.85, -15.32,
                      AMBER if haz else hexc('#7a4a00'), AMBER if haz else None, 1.6)
            if rev:
                face_rect(ctx, view, Lf, 'back', s * 0.75 - 0.1, s * 0.75 + 0.1, 1.3, 1.5, -15.32, (1, 1, 1), WHITE_L, 1.2)
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'back', s * 0.65 - 0.18, s * 0.65 + 0.18, 2.4, 2.48, -15.32, hexc('#9aa0aa'))


def tractor_top(ctx, view, x, z, h, haz):
    Lf = L(x, z, h)
    fill_poly(ctx, view, [Lf(-1.25, 0, -1.5), Lf(1.25, 0, -1.5), Lf(1.25, 0, 5.9), Lf(-1.25, 0, 5.9)], hexc(RED_CAB), OUTL, 4)
    fill_poly(ctx, view, [Lf(-1.15, 0, 2.6), Lf(1.15, 0, 2.6), Lf(1.15, 0, 3.4), Lf(-1.15, 0, 3.4)], hexc('#2a3448'))
    fill_poly(ctx, view, [Lf(-0.95, 0, 3.6), Lf(0.95, 0, 3.6), Lf(0.95, 0, 5.9), Lf(-0.95, 0, 5.9)], mix(hexc(RED_CAB), (1, 1, 1), 0.15), OUTL, 2)
    if haz:
        for lx, lz in ((-1.2, 5.8), (1.2, 5.8)):
            p = view.pt(Lf(lx, 0, lz))
            glow(ctx, p[0], p[1], 1.5 * view.s, AMBER, 0.9)


def trailer_top(ctx, view, x, z, h, haz, col='#f4f4f6'):
    Lf = L(x, z, h)
    fill_poly(ctx, view, [Lf(-1.3, 0, -15.3), Lf(1.3, 0, -15.3), Lf(1.3, 0, 0.9), Lf(-1.3, 0, 0.9)], hexc(col), OUTL, 4)
    fill_poly(ctx, view, [Lf(-1.3, 0, -15.3), Lf(1.3, 0, -15.3), Lf(1.3, 0, -14.8), Lf(-1.3, 0, -14.8)], hexc('#d62828'))
    if haz:
        for lx in (-1.25, 1.25):
            p = view.pt(Lf(lx, 0, -15.2))
            glow(ctx, p[0], p[1], 1.5 * view.s, AMBER, 0.9)


class DallasYard:
    ground_col = hexc('#8f8c86')
    sky = ('#4ea6e8', '#d9efff')

    def skyline(self, ctx, view):
        if view.ortho:
            return
        r = random.Random(14)
        for i in range(24):
            X = -500 + i * 45 + r.uniform(-8, 8)
            Z = 2600 + r.uniform(-80, 120)
            b, tp, s = view.pt((X, 0, Z)), view.pt((X, r.uniform(60, 240), Z)), view.scale((X, 0, Z))
            if b and tp:
                w = r.uniform(25, 45) * s
                ctx.rectangle(b[0] - w / 2, tp[1], w, b[1] - tp[1])
                setc(ctx, mix(hexc('#7f9ab8'), hexc('#cfe6f7'), r.uniform(0.25, 0.5)))
                ctx.fill()
        X, Z = -620.0, 2500.0          # tall column with a lattice ball on top
        b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
        if b and s:
            col = mix(hexc('#8a93a3'), hexc('#cfe6f7'), 0.3)
            for dx in (-8, 0, 8):
                ctx.rectangle(b[0] + (dx - 3) * s, b[1] - 150 * s, 6 * s, 150 * s)
                setc(ctx, col)
                ctx.fill()
            ellipse(ctx, b[0], b[1] - 165 * s, 22 * s, 22 * s)
            setc(ctx, mix(hexc('#c9ccd6'), hexc('#cfe6f7'), 0.2))
            ctx.fill()
            for k in range(-2, 3):
                ctx.move_to(b[0] - 21 * s, b[1] - (165 + k * 8) * s)
                ctx.line_to(b[0] + 21 * s, b[1] - (165 + k * 8) * s)
            setc(ctx, mix(hexc('#7f8aa0'), hexc('#cfe6f7'), 0.2))
            ctx.set_line_width(max(1, 1.2 * s))
            ctx.stroke()

    def ground(self, ctx, view, t):
        gquad(ctx, view, -90, 90, 22, 40, hexc('#c4c0b6'))            # concrete dock apron
        for k in range(-4, 5):
            for sx in (-1, 1):
                gquad(ctx, view, k * DOOR_SP + sx * 1.7 - 0.07, k * DOOR_SP + sx * 1.7 + 0.07, 25, 39.9, C_YEL, 0.01)
        for k in range(-6, 7):                                         # yard parking stripes
            gquad(ctx, view, k * 6.0 - 0.07, k * 6.0 + 0.07, -40, -24, C_LINE, 0.01)
        gquad(ctx, view, -90, 90, -24.1, -23.9, C_YEL, 0.01)

    def objects(self, ctx, view, t):
        out = [((0, 6, 60), lambda: warehouse(ctx, view, t))]
        for k in (-3, -2, -1, 1, 2, 3):
            if k in (-2, 2, 3):
                kx = k * DOOR_SP
                out.append(((kx, 2, 32), lambda kx=kx, k=k: (trailer_top(ctx, view, kx, 24.55, math.pi, False, '#e8e8ee') if view.ortho
                                                             else trailer3(ctx, view, kx, 24.55, math.pi, False, False,
                                                                           ['#e8e8ee', '#f4f4f6', '#dfe6ee'][k % 3], '#e0393e', True))))
        for (px, pz) in ((-55, -30), (55, -30), (-55, 18), (60, 18)):
            out.append(((px, 5, pz), lambda px=px, pz=pz: light_pole(ctx, view, px, pz)))
        for i, (tx, tz) in enumerate(((-30, -32), (-18, -32), (18, -32))):
            out.append(((tx, 2, tz), lambda tx=tx, tz=tz: (trailer_top(ctx, view, tx, tz, 0.0, False, '#dfe6ee') if view.ortho
                                                           else trailer3(ctx, view, tx, tz, 0.0, False, False, '#dfe6ee', '#37b26c', True))))
        return out


def light_pole(ctx, view, x, z):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 10, z)), view.scale((x, 0, z))
    if b and tp and s:
        ctx.rectangle(b[0] - 0.12 * s, tp[1], 0.24 * s, b[1] - tp[1])
        fill_stroke(ctx, hexc('#6a6f7c'), OUTL, max(1, s / 60))
        rrect(ctx, tp[0] - 0.6 * s, tp[1] - 0.2 * s, 1.2 * s, 0.4 * s, 0.1 * s)
        fill_stroke(ctx, hexc('#c9ccd6'), OUTL, max(1, s / 60))


def warehouse(ctx, view, t):
    x0, x1, z0, z1, h = -70, 70, 40, 90, 12
    building(ctx, view, x0, x1, z0, z1, h, '#d9cbb0', win='#9aa6b5', roof=hexc('#c9c4ba'), floors=99)
    if view.ortho:
        text_center(ctx, 'WAREHOUSE', *view.pt((0, 0, 62)), 60, hexc('#8a7f6c'))
        return
    if not front_facing(view, 0, z0, math.pi):
        return
    Lf = lambda a, b, c: (a, b, c)
    face_rect(ctx, view, Lf, 'back', x0, x1, 9.5, 10.3, z0 - 0.02, hexc('#2f6f9f'))
    for k in range(-4, 5):
        cx = k * DOOR_SP
        face_rect(ctx, view, Lf, 'back', cx - DOOR_W / 2 - 0.25, cx + DOOR_W / 2 + 0.25, 0.0, 4.65, z0 - 0.03, hexc('#3a3d48'))
        if k == 0:
            face_rect(ctx, view, Lf, 'back', cx - DOOR_W / 2, cx + DOOR_W / 2, 1.2, 4.4, z0 - 0.04, hexc('#141820'))
        else:
            face_rect(ctx, view, Lf, 'back', cx - DOOR_W / 2, cx + DOOR_W / 2, 1.2, 4.4, z0 - 0.04, hexc('#b8bec8'))
            for y in np.arange(1.5, 4.4, 0.35):
                face_rect(ctx, view, Lf, 'back', cx - DOOR_W / 2, cx + DOOR_W / 2, y, y + 0.05, z0 - 0.05, hexc('#9aa0aa'))
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'back', cx + s * 1.25 - 0.22, cx + s * 1.25 + 0.22, 0.75, 1.15, z0 - 0.06, hexc('#1c1c22'))
        lit = (k == 0) and (t >= T_DOCK)
        c = hexc('#2bdc6a') if lit else (hexc('#ff3030') if k == 0 else hexc('#6a3030'))
        face_rect(ctx, view, Lf, 'back', cx + 1.9, cx + 2.15, 2.6, 2.85, z0 - 0.06, c, c if k == 0 else None, 0.8)
        text_center_world(ctx, view, (cx, 5.1, z0 - 0.06), str(12 + k), 0.55)


def text_center_world(ctx, view, P, txt, size_m):
    p, s = view.pt(P), view.scale(P)
    if p and s and s * size_m > 8:
        text_center(ctx, txt, p[0], p[1] + s * size_m * 0.35, s * size_m, (1, 1, 1))


TRUCK = Truck()
city = DallasYard()
driver = Ped(const(-1.9), const(31.5), top='#d0912c', pants='#2b3a63', skin='#e9b98f', hair='#3a2316')
world = CityWorld(32.4, [(0, 99, TRUCK, [])], [], city, 'mph')


def goal_ped_draw(ctx, view, t, lt):
    pass


# ------------------------------------------------------------- scenes
def cam_behind_trailer(t, back=9.0, up=3.6, side=-2.5):
    ax, az, h2 = TRUCK.trailer_axle(t)
    bx, bz = -math.sin(h2), -math.cos(h2)
    rx, rz = math.cos(h2), -math.sin(h2)
    pos = (ax + bx * (3.0 + back) + rx * side, up, az + bz * (3.0 + back) + rz * side)
    return look_at(pos, (ax - bx * 2.0, 2.2, az - bz * 2.0), 950)


def t_cam(ctx, w, t, lt, kw):
    mode = kw['cam']
    if mode == 'behind_trailer':
        view = cam_behind_trailer(t)
    elif mode == 'over_cab':
        x, z, h1 = TRUCK.pose(t)
        fx_, fz_ = math.sin(h1), math.cos(h1)
        pos = (x + fx_ * 15, 10.5, z + fz_ * 15)
        ax, az, h2 = TRUCK.trailer_axle(t)
        view = look_at(pos, (ax, 1.0, az + 4), 1050)
    else:
        view = look_at(kw['pos'], kw['target'], kw.get('f', 1000))
    draw_scene(ctx, view, w, t)
    if kw.get('driver'):
        driver.draw(ctx, view, t)
    if kw.get('dock_frame'):
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.rectangle(-10, -10, SW + 20, SH + 20)
        rrect(ctx, 330, 150, 1260, 900, 10)
        setc(ctx, hexc('#1a1d24'))
        ctx.fill()
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        for y in (150, 1050):
            ctx.rectangle(330, y - 10, 1260, 20)
        setc(ctx, hexc('#3a3d48'))
        ctx.fill()
    if kw.get('hud', True):
        hud(ctx, w, t)


def t_mirror(ctx, w, t, lt, kw):
    """Driver's (left) West-Coast mirror: tall mirror showing the trailer side and the dock behind."""
    x, z, h1 = TRUCK.pose(t)
    Lf = L(x, z, h1)
    mp = Lf(-1.6, 2.7, 3.35)
    bg = TCam(Lf(-0.6, 2.6, 2.8), h1 - 1.1, 0.12, 650)
    draw_scene(ctx, bg, w, t, ego=False)
    setc(ctx, (0.04, 0.05, 0.1), 0.35)
    ctx.paint()
    poly(ctx, [(1650, -10), (SW + 10, -10), (SW + 10, SH + 10), (1500, SH + 10)])
    fill_stroke(ctx, hexc(RED_CAB), OUTL, 6)
    mx, my, mw, mh = 980, 545, 560, 900
    ctx.move_to(mx + mw / 2 - 40, my - mh / 2 - 60)
    ctx.line_to(1700, 200)
    ctx.move_to(mx + mw / 2 - 40, my + mh / 2 + 40)
    ctx.line_to(1700, 900)
    setc(ctx, hexc('#2a2c33'))
    ctx.set_line_width(26)
    ctx.stroke()
    rrect(ctx, mx - mw / 2 - 26, my - mh / 2 - 26, mw + 52, mh + 52, 40)
    fill_stroke(ctx, hexc('#2a2c33'), OUTL, 7)
    ctx.save()
    rrect(ctx, mx - mw / 2, my - mh / 2, mw, mh, 26)
    ctx.clip()
    view = TCam(mp, h1 + math.pi + 0.05, 0.08, 650, cx=mx - 40, cy=my - 60, mirror=True)
    draw_scene(ctx, view, w, t)
    g = cairo.LinearGradient(mx - mw / 2, my - mh / 2, mx + mw / 2, my + mh / 2)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.12)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()


def t_top(ctx, w, t, lt, kw):
    view = TopN(kw.get('xc', 5.0), kw.get('zc', 18.0), kw.get('scale', 17.0))

    def under(c, v):
        if kw.get('ghost'):
            i0, i1 = np.searchsorted(G, max(t, T_REV)), np.searchsorted(G, T_DOCK)
            pts = []
            for i in range(i0, i1, 10):
                x, z, h2 = LOG[i, 1], LOG[i, 2], LOG[i, 4]
                rx_, rz_ = x - (T.L2 + 3.0) * math.sin(h2), z - (T.L2 + 3.0) * math.cos(h2)
                pts.append(v.pt((rx_, 0, rz_)))
            if len(pts) > 1:
                arrow_path(c, pts, (1, 1, 1), 7, 0.85, dash=[16, 12], head=24)
        fill_poly(c, v, [(-1.5, 0.02, 24.6), (1.5, 0.02, 24.6), (1.5, 0.02, 39.9), (-1.5, 0.02, 39.9)],
                  hexc('#22c35e'), (1, 1, 1), 4, 0.35)
    draw_scene(ctx, view, w, t, overlay=under)
    if kw.get('post'):
        kw['post'](ctx, view, t, lt)


engine.SCENES.update(t_cam=t_cam, t_mirror=t_mirror, t_top=t_top)


def wheel_hud(ctx, lt, d):
    t = T_REV + lt
    ang = TRUCK.delta(t)
    cx, cy, r = 1700, 230, 85
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang / T.DMAX * 1.6)
    ctx.new_sub_path()
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    setc(ctx, (0.1, 0.1, 0.14), 0.85)
    ctx.fill_preserve()
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(14)
    ctx.stroke()
    for a0 in (math.pi / 2, math.pi * 7 / 6, -math.pi / 6):
        ctx.move_to(0, 0)
        ctx.line_to(math.cos(a0) * r, math.sin(a0) * r)
    ctx.set_line_width(12)
    ctx.stroke()
    rrect(ctx, -14, -r - 10, 28, 22, 6)
    setc(ctx, hexc('#ffd23f'))
    ctx.fill()
    ctx.restore()
    txt = 'RIGHT' if ang > 0.08 else ('LEFT' if ang < -0.08 else 'STRAIGHT')
    label(ctx, cx, cy + r + 75, 'Wheel ' + txt, '#2f6f9f', 34)


def opposite_post(ctx, view, t, lt):
    ang = TRUCK.delta(t)
    if abs(ang) < 0.08:
        return
    ax, az, h2 = TRUCK.trailer_axle(t)
    rx, rz = ax - 3.0 * math.sin(h2), az - 3.0 * math.cos(h2)
    p = view.pt((rx, 0, rz))
    # rear of the trailer swings opposite to the wheel when reversing
    sgn = -1 if ang > 0 else 1          # wheel right -> trailer rear goes left (relative to the truck)
    lx, lz = math.cos(h2) * sgn, -math.sin(h2) * sgn
    q = view.pt((rx + lx * 6, 0, rz + lz * 6))
    arrow_path(ctx, [p, q], hexc('#ffd23f'), 10, 1.0, head=28)
    label(ctx, q[0], q[1] - 40, 'Trailer goes ' + ('LEFT' if sgn < 0 else 'RIGHT'), '#e0393e', 38)


def goal_post(ctx, view, t, lt):
    pass


S0 = OFF
shots_def = [
    (8.0 - OFF, 't_cam', dict(cam='fixed', pos=(-12, 13, -6), target=(10, 1, 18), hud=False)),            # 0 establishing
    (11.0 - OFF, 't_top', dict(xc=10.0, zc=20.0, scale=20.0)),                                            # 1 pull past the dock
    (14.0 - OFF, 't_cam', dict(cam='fixed', pos=(44, 12, -14), target=(20, 1, 10), hud=False)),          # 2 swing away
    (T_REV, 't_cam', dict(cam='behind_trailer', hud=False)),                                             # 3 flashers, check
    (T_REV + 4.4, 't_top', dict(xc=6.0, zc=22.0, scale=16.0, ghost=True, post=opposite_post)),           # 4 back slowly, opposite
    (T_GOAL0, 't_mirror', dict()),                                                                       # 5 mirrors
    (T_GOAL1, 't_cam', dict(cam='fixed', pos=(-7.5, 2.4, 38.5), target=(0, 1.6, 26), driver=True, hud=False)),  # 6 GOAL
    (T_GOAL1 + 3.6, 't_cam', dict(cam='over_cab', hud=False)),                                            # 7 small corrections
    (T_DOCK + 0.8, 't_cam', dict(cam='fixed', pos=(0, 2.9, 47), target=(0, 2.4, 28), dock_frame=True, hud=False)),  # 8 stop at bumper
    (T_DOCK + 3.8, 't_cam', dict(cam='fixed', pos=(16, 16, 6), target=(0, 2, 30), hud=False)),            # 9 recap
]
shots, prev = [], 0.0
for end, kind, kw in shots_def:
    shots.append(Shot(end - prev, kind, **kw))
    prev = end
video = Video(['Backing a truck', 'into a loading dock'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
steps = ['Pull forward past your dock', 'Swing away to angle the trailer', 'Flashers on, check all around',
         'Back slowly: steer the OPPOSITE way', 'Watch your mirrors', 'G.O.A.L. Get Out And Look',
         'Small corrections, straighten up', 'Stop gently at the dock bumper']
video.overlays = [(0.3, E[0] - 0.2, location_tag('Dallas, Texas')),
                  (S[9] + 0.2, E[9], caption_in_scene('Set up. Go slow. Look. Straighten.')),
                  (T_REV, T_DOCK + 0.5, wheel_hud)]
for n, txt in enumerate(steps, 1):
    video.overlays += [(S[n], E[n], step_badge(n)), (S[n] + 0.15, E[n], caption_in_scene(txt))]


def goal_label(ctx, lt, d):
    ax, az, h2 = TRUCK.trailer_axle(T_GOAL0 + 0.1)
    gap = 40.0 - (az + 3.0)
    label(ctx, 960, 250, f'About {gap:.0f} m to go: path clear', '#22a356', 44)


video.overlays.append((S[6] + 0.3, E[6], goal_label))


def truck_engine(d):
    t = np.arange(int(d * SR)) / SR
    f = 24
    s = sum(np.sin(2 * np.pi * f * k * t + k) / k for k in range(1, 8))
    s *= 1 + 0.3 * np.sin(2 * np.pi * 3.0 * t)
    return lp(s, 260) * 0.25


def air_brake():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    return hp(noise(n), 2500) * np.exp(-t / 0.25) * 0.5


def backup_alarm(d):
    out = np.zeros(int(d * SR) + SR)
    tt = 0.0
    while tt < d:
        x = np.arange(int(0.5 * SR)) / SR
        place(out, np.sign(np.sin(2 * np.pi * 1100 * x)) * env_adsr(len(x), 0.01, 0.03) * 0.12, tt)
        tt += 1.0
    return out[:int(d * SR)]


def truck_horn(d=0.35):
    return horn(d, doppler=[0.62] * 4) * 1.2


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur), 0, 0.2)
    m.add(truck_engine(video.dur), 0, 0.13)
    m.add(air_brake(), T_PAUSE - 0.3, 0.9, 0.3)
    m.add(click(), T_PAUSE - 1.0, 1.1)
    indicator(m, T_PAUSE - 1.0, T_DOCK + 0.4, 0.75, 0.0)
    m.add(truck_horn(0.3), T_REV - 1.2, 0.8)
    m.add(truck_horn(0.3), T_REV - 0.7, 0.8)
    m.add(backup_alarm(T_GOAL0 - T_REV), T_REV, 1.5)
    m.add(air_brake(), T_GOAL0, 0.7, 0.3)
    m.add(footsteps(0.12, 100), S[6] + 0.3, 0.3, -0.3)
    m.add(footsteps(0.12, 100), S[6] + 0.8, 0.3, -0.3)
    m.add(backup_alarm(T_DOCK - T_GOAL1), T_GOAL1, 1.5)
    m.add(thud(), T_DOCK, 1.0)
    m.add(air_brake(), T_DOCK + 0.2, 0.9)
    m.add(chime(), T_DOCK + 0.4, 0.8)
    for i in range(1, 9):
        m.add(pop(), S[i] + 0.15, 0.8)
    m.add(success_jingle(), S[9] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'truckdock.mp4')
