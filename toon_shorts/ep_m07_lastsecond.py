"""Driver mistake #7: cutting across lanes for an exit at the last second. Los Angeles freeway (palms, hills, downtown)."""
from mkit import *
from toronto import ribbon3

L1, L2, L3, LX = 1.75, 5.25, 8.75, 12.25
TAPER0, E1, KR = -70.0, 150.0, 0.0035
V = 29.0


def ramp_x(z):
    return LX + KR * (z - E1) ** 2 if z > E1 else LX


class EgoF(Track):
    """Track whose x follows the exit ramp once past the gore."""

    def pose(self, t):
        z = self.z(t)
        x = ramp_x(z) if z > E1 and self.xk(t) > 11 else self.xk(t)
        z2 = self.z(t + 0.15)
        x2 = ramp_x(z2) if z2 > E1 and self.xk(t + 0.15) > 11 else self.xk(t + 0.15)
        z1 = self.z(t - 0.15)
        x1 = ramp_x(z1) if z1 > E1 and self.xk(t - 0.15) > 11 else self.xk(t - 0.15)
        h = math.atan2(x2 - x1, z2 - z1) if abs(z2 - z1) > 0.02 else 0.0
        return x, z, h


egoW = EgoF(Key([(0, L1), (8.0, L1), (9.4, LX)]), Key([(0, V), (8.6, V), (9.6, 24), (40, 20)], 'lin'), 8.0, 95.0, C_EGO,
            blink=blink_side([(8.1, 9.6)], 'R'))
c3W = Track(L3, Key([(0, V), (8.6, V), (10.0, 19), (12.0, 24)], 'lin'), 8.7, 107.3, '#3a7bd5')
egoR = EgoF(Key([(0, L1), (15.2, L1), (16.8, L2), (19.4, L2), (21.0, L3), (23.8, L3), (25.4, LX)]),
            Key([(0, V), (24.0, V), (26.0, 24), (40, 20)], 'lin'), 13.4, -260.0, C_EGO,
            blink=blink_side([(14.0, 16.9), (18.0, 21.1), (22.4, 25.5)], 'R'))


def lane_traffic(ego, seed, t_anchor):
    r = random.Random(seed)
    cars = []
    for lane, rels in ((L1, (-40, 60)), (L2, (-70, 45, 110)), (L3, (-120, 80, 150)), (LX, (60,))):
        for k, rz in enumerate(rels):
            v = V - 2.5 if lane == LX else V + r.uniform(-1.5, 1.5)
            cars.append(Track(lane, v, t_anchor, ego.z(t_anchor) + rz, COLS[(k * 3 + int(lane) + seed) % 10]))
    return cars


TW = lane_traffic(egoW, 1, 8.0)
TR = lane_traffic(egoR, 5, 13.4)
TW = [c for c in TW if not (c.xk(0) == L3 and abs(c.z(8.7) - c3W.z(8.7)) < 30)]


def south_traffic(t0):
    out = []
    for i, (x, z0) in enumerate(((-L1, 200), (-L2, 380), (-L3, 90), (-L1, 600), (-L2, 760), (-L3, 520))):
        p = Path([('L', (x, 1500), (x, -1500))])
        out.append(Mover(p, const(28), t0, p.s_near(x, z0), COLS[(i * 7) % 10], t0=-40, t1=120))
    return out


SW_, SR_ = south_traffic(3.0), south_traffic(13.4)


def gantry(ctx, view, z, lines, arrow_x=LX, w0=-0.5, w1=14.5):
    if view.ortho:
        gquad(ctx, view, w0 - 1, w1 + 1, z - 0.5, z + 0.5, hexc('#6a6f7c'))
        return
    for px in (w0 - 1.0, w1 + 1.0):
        fill_poly(ctx, view, [(px - 0.25, 0, z), (px + 0.25, 0, z), (px + 0.25, 7.8, z), (px - 0.25, 7.8, z)], hexc('#8a8f9c'), OUTL, 2)
    fill_poly(ctx, view, [(w0 - 1, 7.4, z), (w1 + 1, 7.4, z), (w1 + 1, 7.8, z), (w0 - 1, 7.8, z)], hexc('#8a8f9c'), OUTL, 2)
    x0, x1 = arrow_x - 3.6, arrow_x + 2.2
    sp = view.poly([(x0, 4.4, z - 0.05), (x1, 4.4, z - 0.05), (x1, 7.6, z - 0.05), (x0, 7.6, z - 0.05)])
    if not sp:
        return
    poly(ctx, sp)
    fill_stroke(ctx, hexc('#1f7a43'), (1, 1, 1), 3)
    c, s = view.pt(((x0 + x1) / 2, 6.0, z)), view.scale(((x0 + x1) / 2, 6.0, z))
    if c and s and s > 5:
        rrect(ctx, c[0] - 2.4 * s, c[1] - 1.55 * s, 1.6 * s, 0.6 * s, 0.05 * s)
        fill_stroke(ctx, hexc('#f2c230'), OUTL, max(1, s / 30))
        text_center(ctx, 'EXIT 12', c[0] - 1.6 * s, c[1] - 1.12 * s, 0.38 * s, OUTL)
        for i, ln in enumerate(lines):
            text_center(ctx, ln, c[0] + 0.2 * s, c[1] + (0.05 + 0.85 * i) * s, (0.7 if i == 0 else 0.6) * s, (1, 1, 1))


def la_extras(ctx, view, t):
    out = []
    for z in np.arange(-700, 900, 24):
        for x in (-12.6, 13.8 if z < TAPER0 - 10 else 15.8 if z < E1 + 10 else None):
            if x is None:
                continue
            if x > 0 and z > E1 - 20:
                continue
            out.append(((x, 5, z), lambda x=x, z=z: palm(ctx, view, x, z, 1.2)))
    out.append(((6, 6, -200), lambda: gantry(ctx, view, -200, ['Downtown', '1 km'])))
    out.append(((6, 6, 60), lambda: gantry(ctx, view, 60, ['Downtown', 'EXIT ONLY'])))
    return out


def la_sky(ctx, view):
    far_line(ctx, view, 2600, lambda x: 160 + 80 * math.sin(x / 240) + 40 * math.sin(x / 70), col='#b9a77f')
    far_line(ctx, view, 1700, lambda x: 60 + 35 * math.sin(x / 120 + 1), col='#9cab7a')
    towers(ctx, view, 1500, -150, 250, 16, 80, 260, seed=4, base='#9aa6b8', haze='#efe6d6')


class LAFreeway(Street):
    def ground(self, ctx, view, t):
        super().ground(ctx, view, t)
        fill_poly(ctx, view, [(10.5, 0.0, TAPER0), (14.0, 0.0, 0.0), (10.5, 0.0, 0.0)], C_ASPH)
        gquad(ctx, view, 10.5, 14.0, 0.0, E1, C_ASPH)
        pts = [(ramp_x(z), z) for z in np.arange(E1 - 2, E1 + 220, 1.5)]
        ribbon3(ctx, view, pts, 3.8, C_ASPH)
        gquad(ctx, view, 10.35, 10.65, TAPER0 - 1, E1, C_ASPH, 0.005)
        for k in range(int(TAPER0 // 4), int(E1 // 4)):
            gquad(ctx, view, 10.35, 10.65, k * 4, k * 4 + 2, C_LINE, 0.012)
        gquad(ctx, view, 13.9, 14.05, 0.0, E1, C_LINE, 0.012)
        fill_poly(ctx, view, [(10.5, 0.012, TAPER0), (10.65, 0.012, TAPER0), (14.05, 0.012, 0.0), (13.9, 0.012, 0.0)], C_LINE)
        ribbon3(ctx, view, pts, 0.15, C_LINE, 0.012, 1.85)
        ribbon3(ctx, view, pts, 0.15, C_LINE, 0.012, -1.85)
        gquad(ctx, view, 10.35, 10.65, E1, 400, C_LINE, 0.012)


city = LAFreeway('freeway', n=3, median='barrier', sidewalk=False, seed=17, skyline=la_sky, extras=la_extras, hmin=8, hmax=18,
                 ground='#c9b98a', palette=['#e9d8b8', '#f2e2c4', '#d8c3a0', '#c9b9a6', '#efe6d6', '#e8cfb6'])
city.items = [it for it in city.items if not (it[0] == 'bld' and it[1][0] > 0 and it[1][3] > -100) and it[0] not in ('tree', 'lamp')]
world = SegWorld(32.4, [hook_seg(0, 3.0, 7.4, egoW, [c3W] + TW + SW_), (3.0, 13.4, egoW, [c3W] + TW + SW_, []),
                        (13.4, 99, egoR, TR + SR_, [])], city, 'kmh')


def path_post(color, ego, t0, t1, msg):
    def fn(ctx, view, t, lt):
        pts = [view.pt((ego.pose(tt)[0], 0, ego.pose(tt)[1])) for tt in np.arange(t0, t1, 0.1)]
        arrow_path(ctx, pts, hexc(color), 10, 1.0, dash=[18, 10], head=30)
        if msg:
            p = view.pt((-4.0, 0, ego.pose(t)[1]))
            label(ctx, p[0], p[1], msg, color, 44)
    return fn


HOOK_CAM = dict(cam='follow', off=(-5.0, 7.5, -24.0), look=(5.0, 0.0, 14.0), f=1000)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (8.0, 'm_cam', dict(cam='inside')),
    (10.2, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'm_top', dict(scale=18.0, ahead=-14.0, xc=6.0, post=path_post('#e0393e', egoW, 7.0, 11.4, 'Cut across 3 lanes!'))),
    (13.4, 'rewind_seq', dict()),
    (16.6, 'm_cam', dict(cam='inside')),
    (21.0, 'm_top', dict(scale=13.0, ahead=40.0, xc=6.0, post=path_post('#22a356', egoR, 13.6, 26.0, None))),
    (23.6, 'm_mirror', dict(side='R')),
    (26.4, 'm_cam', dict(cam='chase')),
    (29.0, 'm_cam', dict(cam='follow', off=(-6, 9, -26), look=(4, 0, 14))),
    (32.4, 'm_cam', dict(cam='fixed', pos=(1.0, 24, 60), target=(16, 0, 175), hud=False)),
]
shots = build_shots(defs)
shots[5].kw.update(srcs=list(reversed(shots[1:5])), dur=shots[5].dur)
video = Video(['Driver MISTAKE #7', 'Last-second exits'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('3 lanes in 1 second?!', 290, 130, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(7, 'Cutting across at the last second')),
    (3.2, 5.8, location_tag('Los Angeles, California')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('Exit coming... still in the far-left lane')),
    (S[3] + 0.1, E[3], caption('Swerves across 3 lanes!')),
    (S[4] + 0.1, E[4], caption('Everyone has to slam the brakes')),
    (S[4] + 0.3, E[4], x_mark),
    (S[6], E[10], badge('RIGHT', '#22a356')),
    (S[11] + 0.2, E[11], end_card('Missed your exit? Just take the next one.', 'Ever missed an exit? What did you do? Comment!')),
]
for n, (i, txt) in enumerate(((6, 'Watch for your exit sign early'), (7, 'Move right ONE lane at a time'), (8, 'Mirror + signal every time'),
                              (9, 'Into the exit lane early'), (10, 'Slow down on the ramp, not before')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[9] + 1.0, E[9], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.13)
    m.add(city_ambience(video.dur), 0, 0.1)
    hook_sfx(m)
    m.add(screech(1.4, 1200), 1.2, 0.8)
    m.add(horn(1.2), 1.4, 0.8, 0.3)
    m.add(click(), 8.1, 1.0)
    indicator(m, 8.1, 9.6, 1.4, 0.2)
    m.add(screech(1.6, 1200), 8.6, 0.9, 0.3)
    m.add(horn(1.4), 8.8, 1.0, 0.3)
    m.add(horn(0.6, doppler=[0.9] * 4), 9.6, 0.7, -0.2)
    sting_bad(m, S[4] + 0.3)
    m.add(rewind_sfx(1.0), S[5], 1.0)
    for a, b in ((14.0, 16.9), (18.0, 21.1), (22.4, 25.5)):
        m.add(click(), a, 1.0)
        indicator(m, a, b, 1.4, 0.2)
        m.add(click(), b, 0.9)
    m.add(head_swish(), S[8] + 0.1, 0.9, 0.5)
    for i in range(6, 11):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[9] + 1.0)
    m.add(success_jingle(), S[11] + 0.2, 0.9)
    m.add(pop(), S[11] + 1.0, 0.8)
    return m.out(video.dur)


def verify():
    print('wrong ego reaches exit lane at z', round(egoW.z(9.4), 1), '(gore at', E1, ')',
          'right reaches exit lane at z', round(egoR.z(25.4), 1), 'taper start', TAPER0)
    print('min gaps wrong', min_gap([egoW, c3W] + TW, 3, 13.4, lat=1.95), 'right', min_gap([egoR] + TR, 13.4, 32.4, lat=1.95))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    else:
        run(video, sound, 'm07.mp4')
