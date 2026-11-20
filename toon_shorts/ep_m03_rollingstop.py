"""Driver mistake #3: rolling through a stop sign. Woodstock, Vermont (village, white church, autumn maples)."""
from mkit import *

X = 1.75
STOP_Z = -8.2                 # stop line (northbound) ; car centre when stopped at the line = -10.7
egoW = Track(X, Key([(0, 11), (6.0, 11), (7.6, 2.5), (8.5, 2.5), (8.9, 0), (13.4, 0)], 'lin'), 8.9, -5.3, C_EGO)
egoR = Track(X, Key([(0, 11), (14.6, 11), (17.0, 0), (19.0, 0), (19.6, 1.0), (20.0, 0), (22.6, 0), (24.6, 7), (40, 9)], 'lin'),
             17.0, -10.7, C_EGO)


def east(t_at, col, z=-1.75, v=13.0):
    p = Path([('L', (-600, z), (600, z))])
    return Mover(p, const(v), t_at, p.s_near(X, z), col, t0=-40, t1=120)


def west(t_at, col, v=12.0):
    p = Path([('L', (600, 1.75), (-600, 1.75))])
    return Mover(p, const(v), t_at, p.s_near(-X, 1.75), col, t0=-40, t1=120)


carW = east(9.05, '#3a7bd5')
carR = east(20.6, '#3a7bd5')
OW = [west(5.0, '#f2a541'), east(4.0, '#c9c9d6')]
OR = [west(18.4, '#f2a541'), east(15.6, '#c9c9d6'), west(24.0, '#37b26c')]


def maple(ctx, view, x, z, s=1.0, seed=0):
    cols = [hexc('#e0582a'), hexc('#f2a541'), hexc('#c9302c'), hexc('#e8c23a')]
    if view.ortho:
        p = view.pt((x, 0, z))
        r = 2.0 * s * view.s
        ellipse(ctx, p[0], p[1], r, r)
        fill_stroke(ctx, cols[seed % 4], OUTL, 2)
        return
    b, tp = view.pt((x, 0, z)), view.pt((x, 3.4 * s, z))
    sc = view.scale((x, 0, z))
    if not b or not tp or not sc:
        return
    w = 0.35 * sc
    lw = max(1, min(4, sc / 30))
    ctx.rectangle(b[0] - w / 2, tp[1], w, b[1] - tp[1])
    fill_stroke(ctx, hexc('#6b4a2f'), OUTL, lw)
    r = 2.0 * s * sc
    for i, (dx, dy) in enumerate(((-0.45, 0.1), (0.45, 0.15), (0, -0.4))):
        ellipse(ctx, tp[0] + dx * r, tp[1] + dy * r, r * 0.75, r * 0.7)
        fill_stroke(ctx, cols[(seed + i) % 4], OUTL, lw)


def village_extras(ctx, view, t):
    out = [((14, 6, 15), lambda: church(ctx, view, 9.0, 21.0, 9.0, 23.0))]
    out.append(((X + 3.0, 1.5, STOP_Z - 0.6), lambda: stop_sign(ctx, view, 4.8, STOP_Z - 0.6, math.pi)))
    for k, (x, z) in enumerate(((-6.5, -30), (6.5, -42), (-6.5, -60), (6.5, -75), (-6.5, 22), (6.5, 34), (-6.5, 46), (6.5, -18),
                                (-6.5, -95), (6.5, -110), (-18, 12), (24, -14), (-20, -16))):
        out.append(((x, 2, z), lambda x=x, z=z, k=k: maple(ctx, view, x, z, 0.5 if view.ortho else 1.15, k)))
    return out


def green_mts(ctx, view):
    far_line(ctx, view, 2400, lambda x: 220 + 110 * math.sin(x / 260) + 50 * math.sin(x / 90), col='#6f9a6a')
    far_line(ctx, view, 1500, lambda x: 90 + 40 * math.sin(x / 150 + 2), col='#c98a4a')


city = Street('village', n=1, median='yellow', cross=0.0, cw=3.6, sidewalk=True, seed=7, skyline=green_mts, extras=village_extras,
              palette=['#f4efe6', '#e9e3d3', '#cfe0ea', '#f2d7b6', '#d6e5cf', '#e8cfd6', '#f6f4ee'], setback=3.0)
city.items = [it for it in city.items if it[0] != 'tree']
world = SegWorld(28.6, [hook_seg(0, 3.0, 7.4, egoW, [carW] + OW), (3.0, 13.4, egoW, [carW] + OW, []),
                        (13.4, 99, egoR, [carR] + OR, [])], city, 'mph')


def line_post(ctx, view, t, lt):
    x, z, h = world.ego(t).pose(t)
    a = view.pt((0.2, 0, STOP_Z))
    label(ctx, a[0] - 230, a[1] + 10, 'Stop line', '#2f6f9f', 40)
    front = z + 2.2
    if t < 13.4 and front > STOP_Z:
        p = view.pt((X, 0, front))
        label(ctx, p[0] + 260, p[1], f'{front - STOP_Z:.1f} m past the line!', '#e0393e', 42)


HOOK_CAM = dict(cam='fixed', pos=(-7.5, 2.3, -15.0), target=(1.2, 0.8, -3.5), f=950)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (8.4, 'm_cam', dict(cam='inside')),
    (10.4, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'm_top', dict(horizontal=False, xc=0.0, zc=-4.0, follow=False, scale=40.0, post=line_post)),
    (13.4, 'rewind_seq', dict()),
    (17.4, 'm_cam', dict(cam='chase')),
    (19.2, 'c_dash', dict()),
    (21.4, 'm_cam', dict(cam='inside', yaw=Key([(0, 0), (0.4, -0.85)]))),
    (22.6, 'm_cam', dict(cam='inside', yaw=Key([(0, -0.85), (0.4, 0.85)]))),
    (25.6, 'm_cam', dict(cam='high')),
    (28.6, 'm_cam', dict(cam='fixed', pos=(-22, 16, -40), target=(2, 0, 0), hud=False)),
]
engine.SCENES['c_dash'] = lambda ctx, w, t, lt, kw: engine.SCENES['dash2'](ctx, w, t, lt, kw)
shots = build_shots(defs)
shots[5].kw.update(srcs=list(reversed(shots[1:5])), dur=shots[5].dur)
video = Video(['Driver MISTAKE #3', 'Rolling stops'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('He thought it was clear...', 290, 120, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(3, 'Rolling through a STOP sign')),
    (3.2, 5.8, location_tag('Woodstock, Vermont')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('Slows down... but never stops')),
    (S[3] + 0.1, E[3], caption('Car from the left!')),
    (S[4] + 0.1, E[4], caption('A rolling stop is NOT a stop')),
    (S[4] + 0.3, E[4], x_mark),
    (S[6], E[10], badge('RIGHT', '#22a356')),
    (S[11] + 0.2, E[11], end_card('Stop. Count 2. Look left, right, left.', 'Be honest: do YOU roll stop signs? Comment!')),
]
for n, (i, txt) in enumerate(((6, 'Stop BEHIND the line'), (7, 'Full stop: 0 mph, count 1-2'), (8, 'Look LEFT'),
                              (9, 'Look RIGHT'), (10, 'Left again, then go')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[10] + 1.2, E[10], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur), 0, 0.12)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.1)
    hook_sfx(m)
    m.add(screech(1.0, 1300), 1.4, 0.7)
    m.add(horn(0.9), 1.5, 0.8, -0.4)
    m.add(screech(1.0, 1300), 8.5, 0.8)
    m.add(horn(1.0), 8.6, 0.9, -0.5)
    m.add(car_pass(1.6, 0.5, 105), 8.3, 0.9, np.linspace(-0.8, 0.8, int(1.6 * SR)))
    sting_bad(m, S[4] + 0.3)
    m.add(rewind_sfx(1.0), S[5], 1.0)
    m.add(brake_squeal(1.0), 16.2, 0.1)
    m.add(bell(midi(79), 0.5), 17.6, 0.7)
    m.add(bell(midi(84), 0.5), 18.6, 0.7)
    m.add(head_swish(), S[8] + 0.05, 1.0, -0.6)
    m.add(car_pass(1.8, 0.5, 100), 19.7, 1.0, np.linspace(-0.8, 0.8, int(1.8 * SR)))
    m.add(head_swish(), S[9] + 0.05, 1.0, 0.6)
    for i in range(6, 11):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[10] + 1.2)
    m.add(success_jingle(), S[11] + 0.2, 0.9)
    m.add(pop(), S[11] + 1.0, 0.8)
    return m.out(video.dur)


def verify():
    worst_w = min((carW.pose(t)[1] - 0.92) - (egoW.z(t) + 2.2) if abs(carW.pose(t)[0] - X) < 1.9 else 9 for t in np.arange(3, 13.4, 0.01))
    worst_r = min((carR.pose(t)[1] - 0.92) - (egoR.z(t) + 2.2) if abs(carR.pose(t)[0] - X) < 1.9 else 9 for t in np.arange(13.4, 28, 0.01))
    print('front of ego vs side of cross car (m): wrong', round(worst_w, 2), 'right', round(worst_r, 2))
    print('ego stopped centre (right)', round(egoR.z(18), 2), 'front', round(egoR.z(18) + 2.2, 2), 'line', STOP_Z)
    print('ego front when wrong car passes', round(egoW.z(9.05) + 2.2, 2), 'line', STOP_Z)
    print('right: ego enters cross street at', next(round(t, 2) for t in np.arange(20, 28, 0.01) if egoR.z(t) + 2.2 > -3.6),
          'carR clears at', round(next(t for t in np.arange(19, 28, 0.01) if carR.pose(t)[0] - 2.2 > X + 0.92), 2))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    else:
        run(video, sound, 'm03.mp4')
