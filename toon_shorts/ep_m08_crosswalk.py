"""Driver mistake #8: stopping on the crosswalk. Boston, Massachusetts (brick rowhouses, gold dome, lamps)."""
from mkit import *

CW = 4.0
CROSS0, CROSS1 = -CW - 4.0, -CW - 0.8        # crosswalk z range (-8 .. -4.8)
STOP_Z = -CW - 4.6                           # stop line -8.6
X = 1.75
egoW = Track(X, Key([(0, 9), (5.0, 9), (7.4, 0), (13.4, 0)], 'lin'), 7.4, -5.6, C_EGO)
egoR = Track(X, Key([(0, 9), (15.6, 9), (18.0, 0), (25.4, 0), (27.2, 6), (40, 8)], 'lin'), 18.0, STOP_Z - 2.6, C_EGO)


def cross_cars(t_ref):
    out = []
    for i in range(4):
        p = Path([('L', (300, 1.75), (-300, 1.75))])
        out.append(Mover(p, const(10), t_ref + i * 1.7, p.s_near(-20, 1.75), ['#3a7bd5', '#f2a541', '#c9c9d6', '#37b26c'][i], t0=-40, t1=120))
    return out


XW, XR = cross_cars(4.0), cross_cars(14.0)
_p = Path([('L', (300, 1.75), (-300, 1.75))])
XW.append(Mover(_p, const(10), 12.4, _p.s_near(-20, 1.75), '#e05d5d', t0=-40, t1=120))
# pedestrians: start on the right sidewalk, cross westward along the crosswalk centre z = -6.4
ZC = (CROSS0 + CROSS1) / 2
def detour(dx, dz):
    xs = [(0, 9.0 + dx), (7.8, 9.0 + dx), (9.0, 3.5 + dx), (9.6, 3.5 + dx), (11.0, -2.0 + dx), (11.6, -2.0 + dx), (13.4, -9.0 + dx)]
    zs = [(0, ZC + dz), (9.0, ZC + dz), (9.6, -2.4 + dz), (11.0, -2.4 + dz), (11.6, ZC + dz), (13.4, ZC + dz)]
    return Key(xs, 'lin'), Key(zs, 'lin')


KID_W = Ped(*detour(0.0, 0.0), top='#f2c230', pants='#3a7bd5', kid=True)
MOM_W = Ped(*detour(0.6, 0.5), top='#e05d5d', hair='#6b4a2f')
KID_R = Ped(Key([(0, 9.0), (19.0, 9.0), (25.0, -9.0), (40, -9.0)], 'lin'), const(ZC), top='#f2c230', pants='#3a7bd5', kid=True)
MOM_R = Ped(Key([(0, 9.6), (19.0, 9.6), (25.0, -8.4), (40, -8.4)], 'lin'), const(ZC + 0.6), top='#e05d5d', hair='#6b4a2f',
            wave=lambda t: 1.0 if 21.6 < t < 22.8 else 0.0)
walkers = [Ped(const(9.4), Key([(0, -40), (40, -10)], 'lin'), top='#56b38a'), Ped(const(-9.4), Key([(0, 20), (40, -20)], 'lin'), top='#9a6fd0')]


def boston_sky(ctx, view):
    towers(ctx, view, 1300, -380, 320, 22, 90, 230, seed=12, base='#8f9aa8')
    if view.ortho:
        return
    X0, Z0 = -120.0, 900.0
    b, s = view.pt((X0, 0, Z0)), view.scale((X0, 0, Z0))
    if b and s:
        ctx.rectangle(b[0] - 60 * s, b[1] - 40 * s, 120 * s, 40 * s)
        setc(ctx, mix(hexc('#c98b6b'), hexc('#d4e8f6'), 0.2))
        ctx.fill()
        ctx.rectangle(b[0] - 18 * s, b[1] - 54 * s, 36 * s, 14 * s)
        setc(ctx, mix(hexc('#f4efe6'), hexc('#d4e8f6'), 0.2))
        ctx.fill()
        ctx.new_sub_path()
        ctx.arc(b[0], b[1] - 54 * s, 17 * s, math.pi, 2 * math.pi)
        setc(ctx, hexc('#f2c230'))
        ctx.fill()
        ctx.rectangle(b[0] - 2 * s, b[1] - 80 * s, 4 * s, 10 * s)
        ctx.fill()


def extras(ctx, view, t):
    out = []
    for (x, z), fh in (((4.6, CROSS0 - 1.0), math.pi),):
        out.append(((x, 1.4, z), lambda x=x, z=z, fh=fh: ped_sign(ctx, view, x, z, fh)))
    return out


def ped_sign(ctx, view, x, z, fh):
    def icon(ctx, cx, cy, r):
        ellipse(ctx, cx, cy - r * 0.42, r * 0.12, r * 0.12)
        setc(ctx, OUTL)
        ctx.fill()
        ctx.move_to(cx, cy - r * 0.28)
        ctx.line_to(cx - r * 0.05, cy + r * 0.1)
        ctx.move_to(cx - r * 0.05, cy + r * 0.1)
        ctx.line_to(cx - r * 0.25, cy + r * 0.48)
        ctx.move_to(cx - r * 0.05, cy + r * 0.1)
        ctx.line_to(cx + r * 0.2, cy + r * 0.48)
        ctx.move_to(cx - r * 0.25, cy - r * 0.1)
        ctx.line_to(cx + r * 0.25, cy - r * 0.05)
        ctx.set_line_width(max(2, r * 0.1))
        ctx.stroke()
    diamond_sign(ctx, view, x, z, fh, icon, None, col='#c8e632')


city = Street('city', n=1, median='yellow', cross=0.0, cw=CW, sidewalk=True, seed=31, skyline=boston_sky, extras=extras, hmin=10, hmax=14,
              setback=0.5, palette=['#a35d43', '#8a4b38', '#9c4f3f', '#b56f52', '#7d3f30', '#c98b6b'])
world = SegWorld(29.4, [hook_seg(0, 3.0, 7.5, egoW, XW, [KID_W, MOM_W] + walkers), (3.0, 13.4, egoW, XW, [KID_W, MOM_W] + walkers),
                        (13.4, 99, egoR, XR, [KID_R, MOM_R] + walkers)], city, 'mph')


def top_post(ctx, view, t, lt):
    a = view.pt((-1.75, 0, ZC))
    label(ctx, a[0] - 120, a[1] - 60, 'Crosswalk', '#2f6f9f', 40)
    ex, ez, _ = world.ego(t).pose(t)
    p = view.pt((ex, 0, ez))
    if t < 13.4:
        label(ctx, p[0] + 300, p[1], 'Car blocks the crosswalk!', '#e0393e', 44)
    else:
        label(ctx, p[0] + 300, p[1], 'Stopped behind the line', '#22a356', 44)


HOOK_CAM = dict(cam='fixed', pos=(8.5, 1.7, -13.0), target=(1.0, 0.9, -4.0), f=1000)
TOP = dict(follow=False, horizontal=False, xc=3.0, zc=-5.0, scale=48.0)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (8.0, 'm_cam', dict(cam='inside')),
    (10.6, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'm_top', dict(TOP, post=top_post)),
    (13.4, 'rewind_seq', dict()),
    (16.8, 'm_cam', dict(cam='chase')),
    (19.6, 'm_top', dict(TOP, post=top_post)),
    (23.0, 'm_cam', dict(cam='fixed', pos=(0.5, 4.2, -21.0), target=(1.5, 0.9, -5.0), f=1000)),
    (25.8, 'm_cam', dict(cam='inside')),
    (29.4, 'm_cam', dict(cam='fixed', pos=(1.5, 20, -46), target=(1.5, 0, -4), hud=False)),
]
shots = build_shots(defs)
shots[5].kw.update(srcs=list(reversed(shots[1:5])), dur=shots[5].dur)
video = Video(['Driver MISTAKE #8', 'Blocking the crosswalk'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Where do they walk?', 290, 140, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(8, 'Stopping on the crosswalk')),
    (3.2, 5.8, location_tag('Boston, Massachusetts')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('He stops right ON the crosswalk')),
    (S[3] + 0.1, E[3], caption('A mom and kid must walk around... into traffic!')),
    (S[4] + 0.1, E[4], caption('The crosswalk belongs to people')),
    (S[4] + 0.3, E[4], x_mark),
    (S[6], E[9], badge('RIGHT', '#22a356')),
    (S[10] + 0.2, E[10], end_card('Stop at the white line. Every time.', 'Does this happen in YOUR city? Comment!')),
]
for n, (i, txt) in enumerate(((6, 'Slow down early'), (7, 'Stop BEHIND the white line'), (8, 'Let them cross safely'),
                              (9, 'Clear? Then go')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[9] + 1.2, E[9], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur, 1.4), 0, 0.25)
    m.add(engine_idle(video.dur), 0, 0.15)
    hook_sfx(m)
    m.add(horn(0.8), 1.2, 0.8, 0.4)
    m.add(brake_squeal(1.0), 6.6, 0.15)
    m.add(screech(0.9, 1300), 10.0, 0.7, 0.2)
    m.add(horn(1.0), 10.1, 0.9, 0.2)
    m.add(car_pass(1.6, 0.5, 100), 9.8, 0.8, np.linspace(0.8, -0.8, int(1.6 * SR)))
    sting_bad(m, S[4] + 0.3)
    m.add(rewind_sfx(1.0), S[5], 1.0)
    m.add(brake_squeal(1.0), 17.0, 0.1)
    tt = 19.0
    while tt < 25.0:
        m.add(footsteps(0.12, 100), tt, 0.25, 0.0)
        tt += 0.4
    m.add(bell(midi(88), 0.6), 21.8, 0.7)
    for i in range(6, 10):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[9] + 1.2)
    m.add(success_jingle(), S[10] + 0.2, 0.9)
    m.add(pop(), S[10] + 1.0, 0.8)
    return m.out(video.dur)


def verify():
    ezW = egoW.z(9)
    print('wrong: ego body z', round(ezW - 2.2, 2), round(ezW + 2.2, 2), 'crosswalk', CROSS0, CROSS1)
    gaps = [(t, abs(KID_W.z(t) - 1.75) - 0.92, abs(KID_W.x(t) - XW[-1].pose(t)[0]) - 2.2) for t in np.arange(9, 13.4, 0.01)]
    print('ped vs ego body clearance', round(min(min(abs(KID_W.x(t) - X) - 0.92, KID_W.z(t) - (egoW.z(t) + 2.2)) if -7.8 < KID_W.z(t) < -3.4 or KID_W.z(t) > -3.4 else 9 for t in np.arange(9, 12, 0.01)), 2))
    print('closest red cross car to kid (m, lat/long):', min(((round(a, 2), round(b, 2)) for t, a, b in gaps), key=lambda g: max(g)))
    ezR = egoR.z(20)
    print('right: ego front', round(ezR + 2.2, 2), 'stop line', STOP_Z, 'peds clear ego lane at',
          round(next(t for t in np.arange(19, 30, 0.01) if KID_R.x(t) < -0.5 and MOM_R.x(t) < -0.5), 2), 'ego moves 25.4')


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    else:
        run(video, sound, 'm08.mp4')
