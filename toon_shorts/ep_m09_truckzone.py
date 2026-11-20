"""Driver mistake #9: lingering in a truck's blind spot. Texas Panhandle (flat plains, wind turbines, grain elevator)."""
from mkit import *

L1, L2 = 1.75, 5.25
V = 30.0
LENGTH = 4.0 + 12.3 + 3.0             # cab front (+6.15 from fifth wheel) to trailer rear (-15.3)


class Truck:
    """Tractor-trailer driving straight (or changing lanes) along +z. Pose = fifth wheel."""
    col = '#c8312f'

    def __init__(self, x, speed, t_anchor, z_anchor, blink=None):
        self.tr = Track(x, speed, t_anchor, z_anchor, '#c8312f')
        self.blink = blink or (lambda t: None)
        self.brake = lambda t: 0.0

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
        bl = self.blink(t)
        if view.ortho:
            Lr = L(x, z, h)
            return [((x, 1.5, z), lambda: (fill_poly(ctx, view, [Lr(-1.3, 0, -15.3), Lr(1.3, 0, -15.3), Lr(1.3, 0, 0.9), Lr(-1.3, 0, 0.9)],
                                                     hexc('#f4f4f6'), OUTL, 4),
                                           fill_poly(ctx, view, [Lr(-1.25, 0, -1.6), Lr(1.25, 0, -1.6), Lr(1.25, 0, 6.15), Lr(-1.25, 0, 6.15)],
                                                     hexc(self.col), OUTL, 4),
                                           [glow(ctx, *view.pt(Lr(-1.25, 0, lz)), 1.6 * view.s, AMBER, 0.9) for lz in (6.0, -15.2)] if bl == 'L' else None))]
        return [((x + math.sin(h) * 2.5, 1.5, z + math.cos(h) * 2.5), lambda: tractor_det(ctx, view, x, z, h, self.col, False, bl)),
                ((x - math.sin(h) * 7.2, 2.0, z - math.cos(h) * 7.2), lambda: trailer_det(ctx, view, x, z, h, False, False, False))]


# wrong: ego (left lane) sits alongside the trailer's right side? -> truck is in the RIGHT lane, ego in the LEFT lane beside the
# truck's driver-side rear (left blind spot); the truck signals left and starts to move over.
truckW = Truck(Key([(0, L2), (8.9, L2), (9.7, 4.2), (10.4, L2)]), V, 3.0, 0.0, blink=blink_side([(7.4, 10.6)], 'L'))
egoW = Track(L1, Key([(0, V), (9.4, V), (10.4, 24), (13.4, 26)], 'lin'), 3.0, -5.5, C_EGO)
# right: ego approaches, passes quickly and keeps going (never lingers), then later stays far behind
truckR = Truck(L2, 25.0, 13.4, 0.0)
egoR = Track(L1, Key([(0, 27), (17.8, 27), (18.8, 31), (23.5, 31), (24.5, 29), (40, 29)], 'lin'), 13.4, -32.0, C_EGO)


def other(lane, rel, base, col, t_anchor):
    return Track(lane, V, t_anchor, base.z(t_anchor) + rel, col)


OW = [other(L1, -70, egoW, '#3a7bd5', 3.0), other(L2, 60, egoW, '#f4f4f6', 3.0)]
OR = [Track(L1, 27, 13.4, -120, '#3a7bd5'), Track(L2, 25, 13.4, 60, '#f4f4f6')]


def south(x, z0, t0, col):
    p = Path([('L', (x, 2000), (x, -2000))])
    return Mover(p, const(30), t0, p.s_near(x, z0), col, t0=-40, t1=120)


SW_ = [south(-L1, 300, 3.0, '#f2a541'), south(-L2, 620, 3.0, '#37b26c')]
SR_ = [south(-L1, 400, 13.4, '#f2a541'), south(-L2, 760, 13.4, '#37b26c')]


def turbine(ctx, view, x, z, t, s=1.0):
    if view.ortho:
        return
    b, tp, sc = view.pt((x, 0, z)), view.pt((x, 80 * s, z)), view.scale((x, 0, z))
    if not b or not tp or not sc or sc < 0.05:
        return
    w = max(1.5, 2.2 * sc)
    poly(ctx, [(b[0] - w, b[1]), (b[0] + w, b[1]), (tp[0] + w * 0.5, tp[1]), (tp[0] - w * 0.5, tp[1])])
    setc(ctx, hexc('#f4f6f8'))
    ctx.fill()
    a0 = t * 1.4 + x * 0.1
    for k in range(3):
        a = a0 + k * 2 * math.pi / 3
        ctx.move_to(*tp)
        ctx.line_to(tp[0] + math.cos(a) * 38 * s * sc, tp[1] + math.sin(a) * 38 * s * sc)
        setc(ctx, hexc('#eef1f4'))
        ctx.set_line_width(max(1.5, 2.4 * sc))
        ctx.stroke()
    ellipse(ctx, tp[0], tp[1], max(2, 2.5 * sc), max(2, 2.5 * sc))
    setc(ctx, hexc('#dfe3e8'))
    ctx.fill()


def plains_sky(ctx, view):
    far_line(ctx, view, 3000, lambda x: 25 + 8 * math.sin(x / 300), col='#c9b98a')
    if view.ortho:
        return
    X, Z = 160.0, 1200.0
    b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
    if b and s:
        for k in range(4):
            ctx.rectangle(b[0] + (k * 13 - 26) * s, b[1] - 38 * s, 12 * s, 38 * s)
        setc(ctx, mix(hexc('#e9e6de'), hexc('#dcefff'), 0.3))
        ctx.fill()
        ctx.rectangle(b[0] - 30 * s, b[1] - 48 * s, 60 * s, 10 * s)
        ctx.fill()


def tx_extras(ctx, view, t):
    out = []
    for i, (x, z) in enumerate(((-260, 600), (-180, 900), (-320, 1100), (240, 700), (330, 1000), (200, 1300), (-420, 1400), (420, 1500))):
        out.append(((x, 40, z), lambda x=x, z=z: turbine(ctx, view, x, z, t)))
    for sx in (-1, 1):
        out.append(((sx * 14, 0.6, 400), lambda sx=sx: fence(ctx, view, sx * 14.0, -500, 1500, 6.0)))
    return out


city = Street('desert', n=2, median='barrier', sidewalk=False, seed=9, skyline=plains_sky, extras=tx_extras, ground='#cdb987')
world = SegWorld(30.6, [hook_seg(0, 3.0, 6.8, egoW, [truckW] + OW + SW_), (3.0, 13.4, egoW, [truckW] + OW + SW_, []),
                        (13.4, 99, egoR, [truckR] + OR + SR_, [])], city, 'mph')


def no_zones(ctx, view, t, lt):
    trk = world.others(t)[0]
    x, z, h = trk.pose(t)
    a = smooth(lt / 0.4)
    zones = [((x - 1.3 - 3.6, x - 1.3), (z - 9.0, z + 4.5), 'L'),          # driver side: alongside cab to mid-trailer
             ((x + 1.3, x + 1.3 + 7.2), (z - 15.3, z + 6.0), 'R'),         # passenger side: big, 2 lanes
             ((x - 1.6, x + 1.6), (z + 6.2, z + 12.2), 'F'),               # front
             ((x - 1.6, x + 1.6), (z - 15.4 - 9.0, z - 15.4), 'B')]        # rear
    for (x0, x1), (z0, z1), name in zones:
        fill_poly(ctx, view, [(x0, 0.02, z0), (x1, 0.02, z0), (x1, 0.02, z1), (x0, 0.02, z1)], hexc('#e0393e'), (1, 1, 1), 3, 0.38 * a)


def zone_post(ctx, view, t, lt):
    trk = world.others(t)[0]
    x, z, h = trk.pose(t)
    p = view.pt((x, 0, z - 5))
    label(ctx, 960, 175, "NO-ZONES: the driver can't see you", '#e0393e', 44)
    e = world.ego(t)
    ex, ez, _ = e.pose(t)
    q = view.pt((ex, 0, ez))
    if t < 13.4:
        label(ctx, q[0], q[1] - 70, 'You are HERE', '#c98a00', 40)


def mirror_rule(ctx, lt, d):
    label(ctx, 960, 200, "Can't see his mirrors? He can't see YOU.", '#2f6f9f', 48)


HOOK_CAM = dict(cam='follow', off=(-4.0, 3.4, -18.0), look=(2.5, 1.2, 4.0), f=950)
TOPV = dict(scale=30.0, ahead=4.0, xc=3.5, under=no_zones, post=zone_post)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (8.4, 'm_cam', dict(cam='inside', yaw=0.5)),
    (10.6, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'm_top', dict(TOPV)),
    (13.4, 'rewind_seq', dict()),
    (16.2, 'm_top', dict(TOPV)),
    (18.8, 'm_cam', dict(cam='inside')),
    (21.4, 'm_cam', dict(cam='chase')),
    (25.4, 'm_cam', dict(cam='follow', off=(-3.0, 6.0, -12.0), look=(2.0, 0.5, 22.0))),
    (30.6, 'm_cam', dict(cam='follow', off=(-18, 18, -30), look=(3, 0, 20), hud=False)),
]
shots = build_shots(defs)
shots[5].kw.update(srcs=list(reversed(shots[1:5])), dur=shots[5].dur)
video = Video(['Driver MISTAKE #9', "Truck blind spots"], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text("He can't see you!", 290, 150, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(9, "Driving in a truck's blind spot")),
    (3.2, 5.8, location_tag('Amarillo, Texas')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('Cruising right beside the truck...')),
    (S[3] + 0.1, E[3], caption('The truck moves over: it never saw him!')),
    (S[4] + 0.1, E[4], caption('He was in a NO-ZONE')),
    (S[4] + 0.3, E[4], x_mark),
    (S[6], E[9], badge('RIGHT', '#22a356')),
    (S[7] + 0.3, E[7], mirror_rule),
    (S[10] + 0.2, E[10], end_card("Pass quickly. Don't linger beside trucks.", 'Truck drivers: what do you wish cars knew? Comment!')),
]
for n, (i, txt) in enumerate(((6, 'Know the 4 no-zones'), (7, 'See the driver in his mirror'), (8, 'Pass quickly & steadily'),
                              (9, "Keep going: don't hang beside it")), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[9] + 2.5, E[9], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.12)
    m.add(lp(noise(int(video.dur * SR)), 200) * 0.08, 0, 1.0)
    hook_sfx(m)
    m.add(horn(1.0), 1.4, 0.9, 0.4)
    m.add(click(), 7.4, 0.8, 0.3)
    indicator(m, 7.4, 10.6, 1.2, 0.3)
    m.add(horn(1.4), 9.2, 1.0, 0.3)
    m.add(screech(1.4, 1200), 9.4, 0.8)
    m.add(horn(0.4, doppler=[0.62] * 4), 9.9, 0.9, 0.4)
    sting_bad(m, S[4] + 0.3)
    m.add(rewind_sfx(1.0), S[5], 1.0)
    m.add(car_pass(3.0, 0.5, 70), 19.5, 0.8, np.linspace(0.3, 0.6, int(3.0 * SR)))
    for i in range(6, 10):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[9] + 2.5)
    m.add(success_jingle(), S[10] + 0.2, 0.9)
    m.add(pop(), S[10] + 1.0, 0.8)
    return m.out(video.dur)


def verify():
    def lateral(t, ego, trk):
        ex, ez, _ = ego.pose(t)
        tx, tz, _ = trk.pose(t)
        return (tx - 1.3) - (ex + 0.92), ez - tz
    lw = min(lateral(t, egoW, truckW)[0] for t in np.arange(3, 13.4, 0.01))
    print('wrong: min side gap ego->trailer (m)', round(lw, 2), 'rel z at 9.0', round(lateral(9.0, egoW, truckW)[1], 1))
    lr = min(lateral(t, egoR, truckR)[0] for t in np.arange(13.4, 30.6, 0.01))
    beside = sum(1 for t in np.arange(13.4, 30.6, 0.01) if -17 < lateral(t, egoR, truckR)[1] < 8.5) * 0.01
    print('right: min side gap', round(lr, 2), 'time spent alongside truck (s)', round(beside, 1))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    else:
        run(video, sound, 'm09.mp4')
