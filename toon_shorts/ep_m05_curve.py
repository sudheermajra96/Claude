"""Driver mistake #5: speeding into a curve. Sea-to-Sky Highway, British Columbia (cliff road, ocean, mountains)."""
from mkit import *
from toronto import ribbon3

CX, CZ, RAD, ANG = -70.0, 0.0, 70.0, 70.0
_a = math.radians(ANG)
END = (CX + RAD * math.cos(_a), CZ + RAD * math.sin(_a))
TAN = (-math.sin(_a), math.cos(_a))
FAR = (END[0] + TAN[0] * 600, END[1] + TAN[1] * 600)
P = Path([('L', (0, -600), (0, 0)), ('A', (CX, CZ), RAD, 0, ANG), ('L', END, FAR)])
PREV = Path([('L', FAR, END), ('A', (CX, CZ), RAD, ANG, 0), ('L', (0, 0), (0, -600))])
S0 = P.s_near(0, 0)
RAIL = 4.75

egoW = OnPath(P, Key([(0, 25), (8.0, 25), (9.2, 17), (13.4, 17)], 'lin'), 8.0, S0, C_EGO,
              offset=Key([(0, 1.75), (8.3, 1.75), (9.1, 3.55), (9.7, 3.55), (10.8, 1.75)]))
egoR = OnPath(P, Key([(0, 25), (15.5, 25), (18.0, 13.9), (26.2, 13.9), (28.5, 20), (40, 22)], 'lin'), 20.0, S0, C_EGO,
              offset=const(1.75))


def onc(t_at, s_at, col):
    return OnPath(PREV, const(20), t_at, s_at, col, offset=const(1.75))


S_REV0 = PREV.s_near(*END)
OW = [onc(4.0, S_REV0 + 20, '#3a7bd5'), onc(10.5, S_REV0 + 60, '#f4f4f6')]
OR = [onc(16.0, S_REV0 - 40, '#3a7bd5'), onc(23.0, S_REV0 + 30, '#f2a541'), onc(27.0, S_REV0 + 10, '#37b26c')]


def path_pts(s0, s1, step=2.0):
    s0, s1 = max(0, s0), min(P.length, s1)
    return [P.pos(s) for s in np.arange(s0, s1, step)]


def normal_at(s):
    h = P.heading(s)
    return math.cos(h), -math.sin(h)          # right of travel


def curve_icon(ctx, cx, cy, r):
    ctx.move_to(cx + r * 0.15, cy + r * 0.55)
    ctx.curve_to(cx + r * 0.15, cy - r * 0.1, cx - r * 0.05, cy - r * 0.3, cx - r * 0.35, cy - r * 0.3)
    setc(ctx, OUTL)
    ctx.set_line_width(max(2, r * 0.13))
    ctx.stroke()
    poly(ctx, [(cx - r * 0.55, cy - r * 0.3), (cx - r * 0.3, cy - r * 0.5), (cx - r * 0.3, cy - r * 0.1)])
    ctx.fill()


class SeaToSky:
    ground_col = hexc('#6f9a5c')
    sky = ('#5aa6e6', '#e2f3ff')

    def __init__(self):
        r = random.Random(5)
        self.trees = []
        for s in np.arange(0, P.length, 5):
            nx, nz = normal_at(s)
            x, z = P.pos(s)
            for _ in range(2):
                d = -(10 + r.uniform(0, 45))
                self.trees.append((x + nx * d, z + nz * d, 0.9 + r.uniform(0, 0.6)))

    def skyline(self, ctx, view):
        r = random.Random(9)
        peaks = [(x, r.uniform(700, 1500) if i % 2 else r.uniform(400, 800)) for i, x in enumerate(range(-4000, 4001, 300))]
        mountains(ctx, view, peaks, 3200, snow=True)
        far_line(ctx, view, 2000, lambda x: 200 + 90 * math.sin(x / 230), col='#4f7a62')

    def ground(self, ctx, view, t):
        ez = world.ego(t).pose(t)
        s_e = P.s_near(ez[0], ez[1])
        pts = path_pts(s_e - 260, s_e + 420)
        ribbon3(ctx, view, pts, 400, hexc('#3f8fc4'), -0.02, 6.6 + 200)
        ribbon3(ctx, view, pts, 2.2, hexc('#8d8577'), 0.0, 5.6)
        ribbon3(ctx, view, pts, 9.4, hexc('#5b5f6c'), 0.0, 0.0)
        for off in (-0.13, 0.13):
            ribbon3(ctx, view, pts, 0.12, C_YEL, 0.01, off)
        for off in (-3.5, 3.5):
            ribbon3(ctx, view, pts, 0.15, C_LINE, 0.01, off)
        for i in range(25):
            x0 = 60 + (i * 53) % 400
            z0 = -200 + (i * 37) % 500
            gquad(ctx, view, x0, x0 + 9, z0, z0 + 0.4, hexc('#8fd0f0'), 0.0)

    def objects(self, ctx, view, t):
        ez = world.ego(t).pose(t)
        s_e = P.s_near(ez[0], ez[1])
        out = []
        for s in np.arange(max(0, s_e - 200), min(P.length, s_e + 400), 4.0):
            a, b = P.pos(s), P.pos(s + 4.0)
            na, nb = normal_at(s), normal_at(s + 4.0)
            pa = (a[0] + na[0] * RAIL, a[1] + na[1] * RAIL)
            pb = (b[0] + nb[0] * RAIL, b[1] + nb[1] * RAIL)
            out.append(((pa[0], 0.6, pa[1]), lambda pa=pa, pb=pb: rail_seg(ctx, view, pa, pb)))
            ra = (a[0] - na[0] * 6.0, a[1] - na[1] * 6.0)
            rb = (b[0] - nb[0] * 6.0, b[1] - nb[1] * 6.0)
            ta = (a[0] - na[0] * 9.0, a[1] - na[1] * 9.0)
            tb = (b[0] - nb[0] * 9.0, b[1] - nb[1] * 9.0)
            out.append(((ra[0], 3.0, ra[1]), lambda ra=ra, rb=rb, ta=ta, tb=tb, k=int(s / 4): rock_seg(ctx, view, ra, rb, ta, tb, k)))
        for x, z, sc in self.trees:
            if abs(P.s_near(x, z) - s_e) < 400:
                out.append(((x, 3, z), lambda x=x, z=z, sc=sc: conifer(ctx, view, x, z, sc * (0.5 if view.ortho else 1.25), 8.0)))
        sx, sz = P.pos(S0 - 125)
        n = normal_at(S0 - 125)
        sp = (sx + n[0] * 5.6, sz + n[1] * 5.6)
        out.append(((sp[0], 1.5, sp[1]), lambda: diamond_sign(ctx, view, sp[0], sp[1], math.pi, curve_icon, '50 km/h')))
        return out


def rail_seg(ctx, view, a, b):
    if view.ortho:
        p, q = view.pt((a[0], 0, a[1])), view.pt((b[0], 0, b[1]))
        ctx.move_to(*p)
        ctx.line_to(*q)
        setc(ctx, hexc('#c9ccd6'))
        ctx.set_line_width(max(2, 0.25 * view.s))
        ctx.stroke()
        return
    p0, p1 = view.pt((a[0], 0, a[1])), view.pt((a[0], 0.8, a[1]))
    if p0 and p1:
        s = view.scale((a[0], 0, a[1]))
        ctx.rectangle(p0[0] - 0.06 * s, p1[1], 0.12 * s, p0[1] - p1[1])
        fill_stroke(ctx, hexc('#8a8f9c'), OUTL, max(1, s / 60))
    fill_poly(ctx, view, [(a[0], 0.55, a[1]), (b[0], 0.55, b[1]), (b[0], 0.85, b[1]), (a[0], 0.85, a[1])], hexc('#d9dde4'), OUTL, 1.5)


def rock_seg(ctx, view, ra, rb, ta, tb, k):
    if view.ortho:
        fill_poly(ctx, view, [(ra[0], 0, ra[1]), (rb[0], 0, rb[1]), (tb[0], 0, tb[1]), (ta[0], 0, ta[1])], hexc('#8d8577'))
        return
    h = 8.0
    fill_poly(ctx, view, [(ra[0], 0, ra[1]), (rb[0], 0, rb[1]), (tb[0], h, tb[1]), (ta[0], h, ta[1])],
              mix(hexc('#9a9184'), hexc('#6f685e'), 0.2 * (k % 3)), OUTL, 1.5)


city = SeaToSky()
world = SegWorld(30.0, [hook_seg(0, 3.0, 7.7, egoW, OW), (3.0, 13.4, egoW, OW, []), (13.4, 99, egoR, OR, [])], city, 'kmh')


def rail_gap(e, t):
    x, z, h = e.pose(t)
    s = P.s_near(x, z)
    px, pz = P.pos(s)
    nx, nz = normal_at(s)
    off = (x - px) * nx + (z - pz) * nz
    return RAIL - (off + 0.92)


def gap_post(ctx, view, t, lt):
    g = min(rail_gap(egoW, tt) for tt in np.arange(8.0, 10.6, 0.02))
    x, z, h = egoW.pose(9.4)
    p = view.pt((x, 0, z))
    label(ctx, p[0] + 300, p[1] + 20, f'Only {g * 100:.0f} cm from the guardrail!', '#e0393e', 46)
    pts = [view.pt(egoW.pose(tt)[:1] + (0,) + egoW.pose(tt)[1:2]) for tt in np.arange(6.5, 11.5, 0.1)]
    arrow_path(ctx, pts, hexc('#e0393e'), 12, 1.0, dash=[18, 10], head=30)


def right_post(ctx, view, t, lt):
    pts = [view.pt(egoR.pose(tt)[:1] + (0,) + egoR.pose(tt)[1:2]) for tt in np.arange(18.5, 27.0, 0.1)]
    arrow_path(ctx, pts, hexc('#22a356'), 12, 1.0, dash=[18, 10], head=30)
    x, z = P.pos(S0 - 30)
    p = view.pt((x, 0, z))
    label(ctx, p[0] + 260, p[1], 'Brake HERE (straight)', '#22a356', 42)


HOOK_CAM = dict(cam='outer', hud=False)
TOPV = dict(follow=False, horizontal=False, xc=-14.0, zc=22.0, scale=17.0)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (8.0, 'm_cam', dict(cam='inside')),
    (10.4, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'm_top', dict(TOPV, post=gap_post)),
    (13.4, 'rewind_seq', dict()),
    (16.0, 'm_cam', dict(cam='inside')),
    (19.0, 'm_cam', dict(cam='chase')),
    (22.4, 'm_top', dict(TOPV, post=right_post)),
    (25.0, 'm_cam', dict(cam='inside')),
    (27.0, 'm_cam', dict(cam='high')),
    (30.0, 'm_cam', dict(cam='fixed', pos=(25, 45, -30), target=(-30, 0, 40), hud=False)),
]
shots = build_shots(defs)
shots[5].kw.update(srcs=list(reversed(shots[1:5])), dur=shots[5].dur)
video = Video(['Driver MISTAKE #5', 'Too fast into curves'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Will he make the turn?', 290, 130, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(5, 'Speeding into a curve')),
    (3.2, 5.8, location_tag('Sea-to-Sky Highway, BC')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('Curve sign says 50... he does 90')),
    (S[3] + 0.1, E[3], caption('Brakes IN the curve: the car slides wide')),
    (S[4] + 0.1, E[4], caption('Too fast = no grip left to turn')),
    (S[4] + 0.3, E[4], x_mark),
    (S[6], E[10], badge('RIGHT', '#22a356')),
    (S[11] + 0.2, E[11], end_card('Slow in. Steady through. Speed up out.', 'Scariest road YOU have driven? Comment!')),
]
for n, (i, txt) in enumerate(((6, 'Read the curve sign: 50 km/h'), (7, 'Brake BEFORE the curve'), (8, 'Steady speed through it'),
                              (9, 'Look where you want to go'), (10, 'Speed up gently on the way out')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[10] + 0.6, E[10], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.14)
    m.add(lp(noise(int(video.dur * SR)), 400) * 0.08, 0, 1.0)
    hook_sfx(m)
    m.add(screech(2.4, 1150), 0.5, 0.8)
    m.add(rumble(1.5), 1.3, 1.2)
    m.add(screech(2.6, 1150), 8.1, 0.9)
    m.add(rumble(1.5), 8.9, 1.4)
    m.add(heartbeat(3, 130), 10.4, 1.0)
    sting_bad(m, S[4] + 0.3)
    m.add(rewind_sfx(1.0), S[5], 1.0)
    m.add(brake_squeal(2.5), 15.5, 0.12)
    for i in range(6, 11):
        m.add(pop(), S[i] + 0.15, 0.7)
    m.add(car_pass(1.8, 0.5, 100), 23.5, 0.8, np.linspace(0.5, -0.8, int(1.8 * SR)))
    sting_good(m, S[10] + 0.6)
    m.add(success_jingle(), S[11] + 0.2, 0.9)
    m.add(pop(), S[11] + 1.0, 0.8)
    return m.out(video.dur)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        print('wrong min rail gap', round(min(rail_gap(egoW, t) for t in np.arange(3, 13.4, 0.01)), 3),
              'right min rail gap', round(min(rail_gap(egoR, t) for t in np.arange(13.4, 30, 0.01)), 3),
              'right speed in curve km/h', round(egoR.speed(22) * 3.6), 'enters curve at', round(egoR.speed(20.0) * 3.6))
    else:
        run(video, sound, 'm05.mp4')
