"""Driver mistake #1: not checking the blind spot. Calgary freeway (3 lanes each way)."""
from mkit import *

L1, L2, L3 = 1.75, 5.25, 8.75
V = 27.0


class Rel:
    """Car whose z is the ego's z plus a relative key (exactly controllable gaps)."""

    def __init__(self, base, x, rel, col, blink=None):
        self.base, self.xk, self.rel, self.col = base, x if callable(x) else const(x), rel, col
        self.blink = blink or (lambda t: None)
        self.brake = lambda t: 0.0

    def pose(self, t):
        x = self.xk(t)
        z = self.base.z(t) + self.rel(t)
        dx = self.xk(t + 0.15) - self.xk(t - 0.15)
        return x, z, math.atan2(dx, 8.0)

    def speed(self, t):
        return (self.base.z(t + 0.05) + self.rel(t + 0.05) - self.base.z(t - 0.05) - self.rel(t - 0.05)) / 0.1

    def steer(self, t):
        return 0.0

    def visible(self, t):
        return True


def south(x, z0, v, col):
    p = Path([('L', (x, 900), (x, -900))])
    return Mover(p, const(v), 0.0, p.s_near(x, z0), col, t0=-40, t1=120)


# ---------------- WRONG (world time 3 .. 13.4)
egoW = Track(Key([(0, L2), (8.3, L2), (9.0, 4.0), (9.8, L2)]), V, 3.0, 0.0, C_EGO, blink=blink_side([(6.0, 9.0)], 'L'))
bW = Rel(egoW, L1, Key([(0, -45), (3, -30), (6.0, -1.2), (12.4, -1.2), (13.4, 12)]), '#3a7bd5')
# ---------------- RIGHT (world time 13.4 .. 31)
egoR = Track(Key([(0, L2), (25.0, L2), (26.6, L1)]), V, 13.4, 0.0, C_EGO, blink=blink_side([(16.0, 26.8)], 'L'))
bR = Rel(egoR, L1, Key([(0, -1.2), (21.0, -1.2), (22.5, 6), (24.0, 20), (26, 40), (31, 70)]), '#3a7bd5')


def traffic(ego, seed):
    r = random.Random(seed)
    cars = [Rel(ego, L3, const(rz), COLS[(i * 3 + seed) % 10]) for i, rz in enumerate((-34, -12, 14, 38, 66))]
    cars += [Rel(ego, L1, const(rz), COLS[(i * 5 + seed + 2) % 10]) for i, rz in enumerate((120, 165))]
    cars += [Rel(ego, L2, const(rz), COLS[(i * 7 + seed + 4) % 10]) for i, rz in enumerate((32, -28))]
    cars += [south(x, z0, 27, COLS[i % 10]) for i, (x, z0) in enumerate(((-L1, 120), (-L2, 260), (-L3, 60), (-L1, 420), (-L2, 520), (-L3, 330)))]
    return cars


TW, TR = traffic(egoW, 1), traffic(egoR, 5)


def calgary(ctx, view):
    far_line(ctx, view, 2800, lambda x: 160 + 120 * math.sin(x / 210) + 60 * math.sin(x / 70) if x < -400 else 40, col='#8aa2c0')
    towers(ctx, view, 1700, -300, 260, 24, 60, 220, seed=3)
    if view.ortho:
        return
    X, Z = -60.0, 1600.0
    b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
    if b and s:
        col = mix(hexc('#c9ccd6'), hexc('#d4e8f6'), 0.25)
        poly(ctx, [(b[0] - 9 * s, b[1]), (b[0] + 9 * s, b[1]), (b[0] + 6 * s, b[1] - 150 * s), (b[0] - 6 * s, b[1] - 150 * s)])
        setc(ctx, col)
        ctx.fill()
        poly(ctx, [(b[0] - 7 * s, b[1] - 150 * s), (b[0] + 7 * s, b[1] - 150 * s), (b[0] + 16 * s, b[1] - 166 * s), (b[0] - 16 * s, b[1] - 166 * s)])
        setc(ctx, mix(hexc('#3b4a5c'), hexc('#d4e8f6'), 0.25))
        ctx.fill()
        ctx.rectangle(b[0] - 14 * s, b[1] - 174 * s, 28 * s, 8 * s)
        setc(ctx, mix(hexc('#d62828'), hexc('#d4e8f6'), 0.2))
        ctx.fill()
        ctx.rectangle(b[0] - 1.5 * s, b[1] - 192 * s, 3 * s, 18 * s)
        ctx.fill()


city = Street('freeway', n=3, median='barrier', sidewalk=False, seed=11, skyline=calgary, hmin=10, hmax=26,
              palette=['#c9b9a6', '#a9b8c6', '#d8cfc0', '#8f9aa8', '#b7c2cc'])
world = SegWorld(31.0, [hook_seg(0, 3.0, 7.0, egoW, [bW] + TW), (3.0, 13.4, egoW, [bW] + TW, []),
                        (13.4, 99, egoR, [bR] + TR, [])], city, 'kmh')


def blind_zone(ctx, view, t, lt):
    x, z, h = world.ego(t).pose(t)
    a = smooth(lt / 0.4)
    fill_poly(ctx, view, [(x - 0.95, 0.02, z - 4.6), (x - 4.4, 0.02, z - 4.6), (x - 4.4, 0.02, z + 0.4), (x - 0.95, 0.02, z + 0.4)],
              hexc('#ffd23f'), (1, 1, 1), 4, 0.45 * a)
    # what the mirror covers (grey wedge, further back)
    fill_poly(ctx, view, [(x - 1.0, 0.02, z + 0.6), (x - 7.6, 0.02, z - 18), (x - 1.0, 0.02, z - 18)], hexc('#9fd3ff'), None, 3, 0.3 * a)


def blind_post(ctx, view, t, lt):
    x, z, h = world.ego(t).pose(t)
    p = view.pt((x - 2.7, 0, z - 2.1))
    label(ctx, p[0] + 40, p[1] - 140, 'BLIND SPOT', '#e0393e' if t < 13.4 else '#c98a00', 46)
    q = view.pt((x - 4.0, 0, z - 13))
    label(ctx, q[0], q[1] - 120, 'Mirror sees this', '#2f6f9f', 42)


def pass_post(ctx, view, t, lt):
    blind_post(ctx, view, t, lt)


HOOK_CAM = dict(cam='follow', off=(-6.5, 3.4, -10.0), look=(-2.0, 0.8, 2.0), f=1000)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (7.8, 'm_cam', dict(cam='close_l', hud=False)),
    (9.0, 'm_mirror', dict(side='L')),
    (11.0, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'm_top', dict(scale=34.0, ahead=-3.0, under=blind_zone, post=blind_post)),
    (13.4, 'rewind_seq', dict()),
    (16.0, 'm_mirror', dict(side='L')),
    (18.0, 'm_cam', dict(cam='close_l', hud=False)),
    (20.4, 'c_shoulder', dict(side='L')),
    (23.0, 'm_top', dict(scale=34.0, ahead=-1.0, under=blind_zone, post=pass_post)),
    (24.6, 'c_shoulder', dict(side='L')),
    (27.4, 'm_cam', dict(cam='chase')),
    (31.0, 'm_cam', dict(cam='follow', off=(-9, 15, -24), look=(-2, 0, 14), hud=False)),
]
shots = build_shots(defs)
shots[6].kw.update(srcs=list(reversed(shots[1:6])), dur=shots[6].dur)
video = Video(['Driver MISTAKE #1', 'Blind spots'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Is the lane clear?', 290, 150, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(1, 'Not checking the blind spot')),
    (3.2, 5.8, location_tag('Calgary, Alberta')),
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('He signals...')),
    (S[3] + 0.1, E[3], caption('Mirror looks clear...')),
    (S[4] + 0.1, E[4], caption('...but he never looked over his shoulder')),
    (S[4] + 0.6, E[4], x_mark),
    (S[5] + 0.1, E[5], caption('The car was hiding in his BLIND SPOT')),
    (S[7], E[12], badge('RIGHT', '#22a356')),
    (S[13] + 0.2, E[13], end_card('Mirror. Signal. Shoulder check. Go.', 'Do YOU shoulder check every time? Comment!')),
]
for n, (i, txt) in enumerate(((7, 'Check your mirror'), (8, 'Signal'), (9, 'Shoulder check: a car is there!'),
                              (10, 'Wait for it to pass'), (11, 'Check again: clear'), (12, 'Move over smoothly')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[12] + 1.5, E[12], check_mark))


def sound():
    m = Mixer(video.dur)
    series_sound_base(m, world, video.dur, 0.18, 0.12)
    hook_sfx(m)
    m.add(horn(0.9), 1.6, 0.9, -0.5)
    m.add(whoosh(0.6, 0.4), 2.9, 0.6)
    m.add(click(), 6.0, 1.0)
    indicator(m, 6.0, 9.0, 1.5, -0.2)
    m.add(horn(1.1), 8.6, 0.7, -0.6)
    m.add(screech(0.8, 1250), 8.8, 0.5, -0.4)
    sting_bad(m, S[5])
    m.add(rewind_sfx(1.0), S[6], 1.0)
    m.add(click(), 16.0, 1.0)
    indicator(m, 16.0, 26.8, 1.5, -0.2)
    m.add(click(), 26.8, 0.9)
    m.add(head_swish(), S[9] + 0.05, 1.0, -0.6)
    m.add(head_swish(), S[11] + 0.05, 1.0, -0.6)
    m.add(car_pass(2.2, 0.5, 108), 21.2, 0.9, np.linspace(-0.7, -0.1, int(2.2 * SR)))
    for i in range(7, 13):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[12] + 1.5)
    m.add(success_jingle(), S[13] + 0.2, 0.9)
    m.add(pop(), S[13] + 1.0, 0.8)
    return m.out(video.dur)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        print('wrong', min_gap([egoW, bW] + TW, 3, 13.4), 'right', min_gap([egoR, bR] + TR, 13.4, 31))
    else:
        run(video, sound, 'm01.mp4')
