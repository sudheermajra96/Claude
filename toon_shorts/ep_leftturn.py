"""Left turn at a busy intersection, the right way: downtown Chicago (green ball, oncoming traffic, crosswalk)."""
import math
import random

from citykit import *

engine.DAY = True
HW = 7.0          # half width of each street (2 lanes each way)
GLASS = ['#9fb8cc', '#7f98ae', '#c9d3db', '#5f7488', '#d8cfc0', '#8c8f99', '#b3a58e']


def blinkfn(intervals, side):
    b = blinking(intervals)
    return lambda t: side if b(t) > 0.5 else None


EGO_P = Path([('L', (1.75, -160), (1.75, -5.5)), ('A', (-5.5, -5.5), 7.25, 0, 90), ('L', (-5.5, 1.75), (-160, 1.75))])
ego_speed = Key([(0, 11), (3.0, 11), (7.0, 0), (12.5, 0), (14.5, 5.5), (17, 9), (40, 9)], 'lin')
ego = Mover(EGO_P, ego_speed, 7.0, EGO_P.s_near(1.75, -5.5), C_EGO, blink=blinkfn([(1.5, 15.6)], 'L'))


def sb(x, tc, col, kind='car'):
    p = Path([('L', (x, 260), (x, -260))])
    m = Mover(p, const(11.0), tc, p.s_near(x, 0), col)
    m.kind = kind
    return m


def parked(x, z, h, col):
    p = Path([('L', (x - math.sin(h), z - math.cos(h)), (x + math.sin(h), z + math.cos(h)))])
    return Mover(p, const(0.0), 0, p.s_near(x, z), col)


others = [sb(-1.75, tc, c, k) for tc, c, k in ((4.6, '#3a7bd5', 'car'), (6.4, '#f2c230', 'taxi'), (8.3, '#f4f4f6', 'car'),
                                               (10.2, '#37b26c', 'car'), (12.0, '#7a4fd0', 'car'), (19.0, '#f2a541', 'car'))]
others += [sb(-5.25, tc, c, k) for tc, c, k in ((5.5, '#c9c9d6', 'car'), (7.4, '#e05d5d', 'car'), (9.3, '#f2c230', 'taxi'),
                                                (11.2, '#2f6f73', 'car'), (19.6, '#3a7bd5', 'car'))]
others += [parked(13.0, 1.75, -math.pi / 2, '#f4f4f6'), parked(13.0, 5.25, -math.pi / 2, '#37b26c'),
           parked(19.2, 1.75, -math.pi / 2, '#f2c230'),
           parked(-13.0, -1.75, math.pi / 2, '#3a7bd5'), parked(-13.0, -5.25, math.pi / 2, '#c9c9d6')]
p_rt = Path([('L', (5.25, -160), (5.25, 200))])
others.append(Mover(p_rt, const(10.5), 9.0, p_rt.s_near(5.25, 0), '#f4f4f6'))

ped1 = Ped(const(-9.6), Key([(0, -11), (2.0, -9.0), (15.8, 9.0), (30, 27)], 'lin'), top='#e05d5d')
peds = [ped1, Ped(const(-10.2), const(-9.6), top='#f2c230', hair='#c7782e'),
        Ped(const(9.6), Key([(0, -40), (30, -6)], 'lin'), top='#56b38a', skin='#8d5a3b', hair='#1b1b1b'),
        Ped(const(-9.8), Key([(0, 40), (30, 12)], 'lin'), top='#9a6fd0'),
        Ped(Key([(0, 30), (30, 12)], 'lin'), const(9.8), top='#3a7bd5')]


def state(approach, t):
    return 'green' if approach in ('N', 'S') else 'red'


class Chicago:
    ground_col = hexc('#a9a49a')
    sky = ('#5aa8e6', '#d8eefc')

    def __init__(self):
        r = random.Random(8)
        self.blds = []
        for sx in (-1, 1):
            for sz in (-1, 1):
                d = 12.0
                while d < 320:                      # along the N-S street
                    w = r.uniform(18, 30)
                    x0 = 12.0
                    self.blds.append(self._b(sx, sz, x0, x0 + r.uniform(16, 26), d, d + w, r))
                    d += w + 1.0
                d = 40.0
                while d < 320:                      # along the E-W street
                    w = r.uniform(18, 30)
                    self.blds.append(self._b(sx, sz, d, d + w, 12.0, 12.0 + r.uniform(16, 26), r))
                    d += w + 1.0

    def _b(self, sx, sz, a0, a1, b0, b1, r):
        xs = sorted((sx * a0, sx * a1))
        zs = sorted((sz * b0, sz * b1))
        return (xs[0], xs[1], zs[0], zs[1], r.choice([r.uniform(25, 60), r.uniform(45, 120)]), r.choice(GLASS))

    def skyline(self, ctx, view):
        r = random.Random(3)
        for i in range(30):
            X = -700 + i * 48 + r.uniform(-10, 10)
            self._tower(ctx, view, X, 900 + r.uniform(-100, 150), r.uniform(30, 50), r.uniform(80, 220),
                        mix(hexc('#8aa0b5'), hexc('#c8dcec'), r.uniform(0.2, 0.5)))
        # a black bundled supertall with twin antennas (inspired by the skyline), and a tapered black tower
        X, Z = -160.0, 1100.0
        b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
        if b and s:
            col = mix(hexc('#2b2f3a'), hexc('#c8dcec'), 0.25)
            for dx, w, h in ((-22, 22, 330), (0, 22, 442), (22, 22, 380), (-11, 22, 400), (11, 22, 360)):
                ctx.rectangle(b[0] + (dx - w / 2) * s, b[1] - h * s, w * s, h * s)
                setc(ctx, col)
                ctx.fill()
            for ax in (-8, 8):
                ctx.rectangle(b[0] + (ax - 1) * s, b[1] - 527 * s, 2 * s, 85 * s)
                ctx.fill()
        X, Z = 260.0, 1300.0
        b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
        if b and s:
            col = mix(hexc('#2b2f3a'), hexc('#c8dcec'), 0.3)
            poly(ctx, [(b[0] - 40 * s, b[1]), (b[0] + 40 * s, b[1]), (b[0] + 26 * s, b[1] - 344 * s), (b[0] - 26 * s, b[1] - 344 * s)])
            setc(ctx, col)
            ctx.fill()
            for ax in (-10, 10):
                ctx.rectangle(b[0] + (ax - 1) * s, b[1] - 440 * s, 2 * s, 96 * s)
                ctx.fill()

    def _tower(self, ctx, view, X, Z, w, h, col):
        b, tp, s = view.pt((X, 0, Z)), view.pt((X, h, Z)), view.scale((X, 0, Z))
        if b and tp:
            ctx.rectangle(b[0] - w * s / 2, tp[1], w * s, b[1] - tp[1])
            setc(ctx, col)
            ctx.fill()

    def ground(self, ctx, view, t):
        gquad(ctx, view, -HW, HW, -400, 400, C_ASPH)
        gquad(ctx, view, -400, 400, -HW, HW, C_ASPH)
        for a, b in ((-400, -HW - 4.5), (HW + 4.5, 400)):          # lane markings outside the box
            for sgn in (-1, 1):
                gquad(ctx, view, sgn * 0.06, sgn * 0.2, a, b, C_YEL, 0.01)
                fill_poly(ctx, view, [(a, 0.01, sgn * 0.06), (b, 0.01, sgn * 0.06), (b, 0.01, sgn * 0.2), (a, 0.01, sgn * 0.2)], C_YEL)
            for k in range(int(a // 9), int(b // 9)):
                for sgn in (-1, 1):
                    if a <= k * 9 and k * 9 + 3 <= b:
                        gquad(ctx, view, sgn * 3.42, sgn * 3.58, k * 9, k * 9 + 3, C_LINE, 0.01) if sgn > 0 else \
                            gquad(ctx, view, -3.58, -3.42, k * 9, k * 9 + 3, C_LINE, 0.01)
                        fill_poly(ctx, view, [(k * 9, 0.01, sgn * 3.42), (k * 9 + 3, 0.01, sgn * 3.42),
                                              (k * 9 + 3, 0.01, sgn * 3.58), (k * 9, 0.01, sgn * 3.58)], C_LINE)
        zebra(ctx, view, -HW, HW, -HW - 4, -HW - 0.8, 'x')
        zebra(ctx, view, -HW, HW, HW + 0.8, HW + 4, 'x')
        zebra(ctx, view, -HW - 4, -HW - 0.8, -HW, HW, 'z')
        zebra(ctx, view, HW + 0.8, HW + 4, -HW, HW, 'z')
        gquad(ctx, view, 0.2, HW, -HW - 5.0, -HW - 4.5, C_LINE, 0.012)
        gquad(ctx, view, -HW, -0.2, HW + 4.5, HW + 5.0, C_LINE, 0.012)
        fill_poly(ctx, view, [(HW + 4.5, 0.012, 0.2), (HW + 5.0, 0.012, 0.2), (HW + 5.0, 0.012, HW), (HW + 4.5, 0.012, HW)], C_LINE)
        fill_poly(ctx, view, [(-HW - 5.0, 0.012, -HW), (-HW - 4.5, 0.012, -HW), (-HW - 4.5, 0.012, -0.2), (-HW - 5.0, 0.012, -0.2)], C_LINE)
        # sidewalks
        for sx in (-1, 1):
            gquad(ctx, view, *sorted((sx * HW, sx * 12)), -400, -12, hexc('#cfc8bb'))
            gquad(ctx, view, *sorted((sx * HW, sx * 12)), 12, 400, hexc('#cfc8bb'))
            fill_poly(ctx, view, [(-400, 0, sx * HW), (-12, 0, sx * HW), (-12, 0, sx * 12), (-400, 0, sx * 12)], hexc('#cfc8bb'))
            fill_poly(ctx, view, [(12, 0, sx * HW), (400, 0, sx * HW), (400, 0, sx * 12), (12, 0, sx * 12)], hexc('#cfc8bb'))
        for sx in (-1, 1):
            for sz in (-1, 1):
                fill_poly(ctx, view, [(sx * HW, 0, sz * HW), (sx * 12, 0, sz * HW), (sx * 12, 0, sz * 12), (sx * HW, 0, sz * 12)],
                          hexc('#cfc8bb'))

    def objects(self, ctx, view, t):
        out = []
        for x0, x1, z0, z1, h, col in self.blds:
            out.append((((x0 + x1) / 2, h / 2, (z0 + z1) / 2), lambda a=(x0, x1, z0, z1, h, col): building(ctx, view, *a, win='#3b5872')))
        # signal poles + mast arms with heads over the lanes (heads face the approaching traffic)
        masts = [((8.6, 9.0), [(1.75, 9.0), (5.25, 9.0)], math.pi, 'S'),       # serves northbound (faces south)
                 ((-8.6, -9.0), [(-1.75, -9.0), (-5.25, -9.0)], 0.0, 'N'),     # serves southbound (faces north)
                 ((-9.0, 8.6), [(-9.0, 1.75), (-9.0, 5.25)], math.pi / 2, 'W'),
                 ((9.0, -8.6), [(9.0, -1.75), (9.0, -5.25)], -math.pi / 2, 'E')]
        for (px, pz), heads, fh, appr in masts:
            out.append(((px, 3, pz), lambda px=px, pz=pz, heads=heads, fh=fh, appr=appr: mast(ctx, view, px, pz, heads, fh, appr, t)))
        return out


def mast(ctx, view, px, pz, heads, fh, appr, t):
    if view.ortho:
        p = view.pt((px, 0, pz))
        ellipse(ctx, p[0], p[1], 0.35 * view.s, 0.35 * view.s)
        setc(ctx, hexc('#3a3d48'))
        ctx.fill()
        return
    b, tp, s = view.pt((px, 0, pz)), view.pt((px, 6.4, pz)), view.scale((px, 0, pz))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.13 * s, tp[1], 0.26 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#3a3d48'), OUTL, max(1, s / 50))
    far = heads[-1]
    a = view.pt((far[0], 6.3, far[1]))
    if a:
        ctx.move_to(*tp)
        ctx.line_to(*a)
        setc(ctx, hexc('#3a3d48'))
        ctx.set_line_width(max(2, 0.18 * s))
        ctx.stroke()
    st = 'green' if appr in ('S', 'N') else 'red'
    for hx, hz in heads:
        signal_head(ctx, view, hx, 5.6, hz, fh, st)


city = Chicago()
world = CityWorld(21, [(0, 99, ego, others)], peds, city, 'mph')
SB_GAP = (others[4], others[5])          # the last car before the gap, the first car after it


def top_under(ctx, view, t, lt):
    a = smooth((lt - 0.8) / 0.4)
    if a <= 0:
        return
    z_last = max(SB_GAP[0].pose(t)[1], -8)
    z_next = SB_GAP[1].pose(t)[1]
    fill_poly(ctx, view, [(-3.4, 0.02, z_last + 3), (-0.1, 0.02, z_last + 3), (-0.1, 0.02, z_next - 3), (-3.4, 0.02, z_next - 3)],
              hexc('#22c35e'), (1, 1, 1), 4, 0.45 * a)


def top_post(ctx, view, t, lt):
    a = smooth((lt - 0.8) / 0.4)
    pts = [view.pt((EGO_P.pos(s)[0], 0, EGO_P.pos(s)[1])) for s in np.arange(EGO_P.s_near(1.75, -6), EGO_P.s_near(-14, 1.75), 0.5)]
    arrow_path(ctx, pts, (1, 1, 1), 8, 0.9, dash=[16, 12], head=24)
    for x in (-1.75, -5.25):
        q0, q1 = view.pt((x, 0, 60)), view.pt((x, 0, 30))
        arrow_path(ctx, [q0, q1], (1, 1, 1), 6, 0.6, head=20)
    if a > 0:
        z_next = SB_GAP[1].pose(t)[1]
        c = view.pt((-1.75, 0, min(z_next - 8, 28)))
        label(ctx, c[0] - 160, c[1], 'Big gap: GO', '#22a356', 40)
    c = view.pt((-3.5, 0, 22))
    label(ctx, c[0] - 190, c[1], 'Oncoming', '#e0393e', 40)


shots = [
    Shot(3.0, 'c_cam', cam='fixed', pos=(1, 24, -62), target=(0, 0, 4), hud=False),          # 0 establishing
    Shot(2.4, 'c_cam', cam='close_l', hud=False),                                             # 1 left lane + signal
    Shot(2.6, 'c_cam', cam='high'),                                                           # 2 pull forward
    Shot(2.0, 'c_inside'),                                                                    # 3 wheels straight
    Shot(2.6, 'c_top', center=(-4, 9), scale=19.0, under=top_under, post=top_post),           # 4 oncoming + gap
    Shot(2.0, 'c_inside', yaw=Key([(0, -0.55), (1.4, -0.4), (2.0, -0.1)])),                   # 5 crosswalk
    Shot(3.0, 'c_cam', cam='chase'),                                                          # 6 turn into nearest lane
    Shot(3.2, 'c_cam', cam='fixed', pos=(-62, 15, -1), target=(-14, 0, 2), hud=False),       # 7 recap
]
video = Video(['LEFT TURN at a', 'busy intersection'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
steps = ['Left lane + signal early', 'Pull forward to wait', 'Keep your wheels STRAIGHT',
         'Wait for a big gap', 'Check the crosswalk', 'Turn into the nearest lane']
video.overlays = [(0.3, E[0] - 0.2, location_tag('Chicago, Illinois')),
                  (S[7] + 0.2, E[7], caption_in_scene('Signal. Wait. Gap. Look. Turn.'))]
for n, txt in enumerate(steps, 1):
    video.overlays += [(S[n], E[n], step_badge(n)), (S[n] + 0.15, E[n], caption_in_scene(txt))]


def wheel_note(ctx, lt, d):
    a = smooth(lt / 0.3)
    label(ctx, 960, 250, 'If hit from behind, you stay out of oncoming traffic', '#2f6f9f', 46)


video.overlays.append((S[3] + 0.3, E[3], wheel_note))


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.12)
    m.add(city_ambience(video.dur), 0, 0.3)
    m.add(click(), 1.5, 1.2)
    indicator(m, 1.5, 15.6, 1.1, -0.2)
    m.add(click(), 15.6, 1.0)
    for i, tc in enumerate((4.6, 5.5, 6.4, 7.4, 8.3, 9.3, 10.2, 11.2, 12.0)):
        m.add(car_pass(1.6, 0.5, 100 + i * 4), tc - 0.8, 0.22, np.linspace(-0.6, -0.1, int(1.6 * SR)))
    for i in range(1, 7):
        m.add(pop(), S[i] + 0.15, 0.8)
    m.add(head_swish(), S[5] + 0.05, 1.0, -0.6)
    tt = 2.0
    while tt < 15.8:
        m.add(footsteps(0.12, 100), tt, 0.04, -0.4)
        tt += 0.45
    m.add(chime(), 12.5, 0.6)
    m.add(success_jingle(), S[7] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'leftturn.mp4')
