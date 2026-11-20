"""Driver mistake #4: turning without signalling. Halifax, Nova Scotia (waterfront, harbour, hilltop clock tower)."""
from mkit import *

X = 1.75
TURN = Path([('L', (X, -400), (X, -9.0)), ('A', (9.0, -9.0), 7.25, 180, 90), ('L', (9.0, -1.75), (600, -1.75))])
S_ARC = TURN.s_near(X, -9.0)

egoW = OnPath(TURN, Key([(0, 13), (7.5, 13), (8.6, 4), (11.5, 4), (13.4, 7)], 'lin'), 8.8, S_ARC, C_EGO)
folW = Track(X, Key([(0, 13), (8.45, 13), (9.89, 0), (13.4, 0)], 'lin'), 9.89, -11.31, '#3a7bd5')
egoR = OnPath(TURN, Key([(0, 13), (17.5, 13), (19.5, 5), (23, 5), (25, 9)], 'lin'), 20.0, S_ARC, C_EGO,
              blink=blink_side([(16.4, 22.6)], 'R'))
folR = Track(X, Key([(0, 13), (17.6, 13), (19.8, 6), (22, 8), (40, 9)], 'lin'), 17.5, -58.9, '#3a7bd5')


def south(z_at0, t_at, col):
    p = Path([('L', (-X, 900), (-X, -900))])
    return Mover(p, const(11), t_at, p.s_near(-X, z_at0), col, t0=-40, t1=120)


OW = [south(-40, 6.0, '#f2a541'), south(60, 9.0, '#c9c9d6')]
OR = [south(-40, 18.0, '#f2a541'), south(80, 22.0, '#37b26c')]


def sailboat(ctx, view, x, z, s=1.0):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 3 * view.s, 1.0 * view.s)
        fill_stroke(ctx, (1, 1, 1), OUTL, 2)
        return
    b, sc = view.pt((x, 0.3, z)), view.scale((x, 0.3, z))
    if not b or not sc or sc < 0.6:
        return
    poly(ctx, [(b[0] - 4 * sc * s, b[1] - 0.8 * sc), (b[0] + 4 * sc * s, b[1] - 0.8 * sc), (b[0] + 3 * sc * s, b[1]), (b[0] - 3 * sc * s, b[1])])
    fill_stroke(ctx, hexc('#f4f4f6'), OUTL, max(1, sc / 40))
    ctx.move_to(b[0], b[1] - 0.8 * sc)
    ctx.line_to(b[0], b[1] - 11 * sc * s)
    setc(ctx, hexc('#6b4a2f'))
    ctx.set_line_width(max(1.5, 0.25 * sc))
    ctx.stroke()
    poly(ctx, [(b[0] + 0.2 * sc, b[1] - 10.5 * sc * s), (b[0] + 0.2 * sc, b[1] - 1.4 * sc), (b[0] + 4.2 * sc * s, b[1] - 1.4 * sc)])
    fill_stroke(ctx, (1, 1, 1), OUTL, max(1, sc / 50))


def harbour_extras(ctx, view, t):
    out = []
    for k, (x, z) in enumerate(((130, -60), (155, 40), (140, 140), (190, -10), (165, 260), (210, 120), (145, -180))):
        out.append(((x, 1, z), lambda x=x, z=z, k=k: sailboat(ctx, view, x, z, 1.0 + 0.2 * (k % 2))))
    for z in np.arange(-300, 500, 9):
        out.append(((85.5, 0.6, z), lambda z=z: bollard(ctx, view, 85.5, z)))
    return out


def bollard(ctx, view, x, z):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 0.9, z)), view.scale((x, 0, z))
    if b and tp and s and s > 2:
        ctx.rectangle(b[0] - 0.12 * s, tp[1], 0.24 * s, b[1] - tp[1])
        fill_stroke(ctx, hexc('#2a2c33'), OUTL, max(1, s / 60))


def halifax_sky(ctx, view):
    if view.ortho:
        return
    far_line(ctx, view, 2200, lambda x: 70 + 30 * math.sin(x / 200), col='#6f9a7a')
    # Citadel hill (left) with a white octagonal clock tower
    X0, Z0 = -260.0, 650.0
    pts = [view.pt((X0 + dx, 38 * math.exp(-(dx / 120) ** 2), Z0)) for dx in range(-260, 261, 20)]
    base = view.pt((X0, 0, Z0))
    if base and all(pts):
        ctx.move_to(pts[0][0], base[1])
        for q in pts:
            ctx.line_to(*q)
        ctx.line_to(pts[-1][0], base[1])
        ctx.close_path()
        setc(ctx, hexc('#7fb36a'))
        ctx.fill()
    b, s = view.pt((X0 + 30, 36, Z0)), view.scale((X0 + 30, 36, Z0))
    if b and s:
        ctx.rectangle(b[0] - 7 * s, b[1] - 12 * s, 14 * s, 12 * s)
        setc(ctx, hexc('#f4f2ec'))
        ctx.fill()
        ctx.rectangle(b[0] - 4.5 * s, b[1] - 22 * s, 9 * s, 10 * s)
        ctx.fill()
        ellipse(ctx, b[0], b[1] - 17 * s, 2.6 * s, 2.6 * s)
        setc(ctx, hexc('#2a3448'))
        ctx.fill()
        poly(ctx, [(b[0] - 3.5 * s, b[1] - 22 * s), (b[0] + 3.5 * s, b[1] - 22 * s), (b[0], b[1] - 29 * s)])
        setc(ctx, hexc('#4f8a5a'))
        ctx.fill()
    towers(ctx, view, 900, -260, -40, 10, 30, 70, seed=6, base='#9aa6b5')


class HalifaxStreet(Street):
    def ground(self, ctx, view, t):
        super().ground(ctx, view, t)
        gquad(ctx, view, 88.0, 1500, -900, 900, hexc('#3f8fc4'))
        for i in range(30):
            x0 = 95 + (i * 47) % 300
            z0 = -300 + (i * 71) % 700
            gquad(ctx, view, x0, x0 + 8, z0, z0 + 0.4, hexc('#8fd0f0'), 0.01)
        gquad(ctx, view, 86.0, 88.0, -900, 900, hexc('#7d6f63'))


city = HalifaxStreet('city', n=1, median='yellow', cross=0.0, cw=3.6, sidewalk=True, seed=13, skyline=halifax_sky,
                     extras=harbour_extras, hmin=9, hmax=16, palette=['#a35d43', '#8a4b38', '#c98b6b', '#d8c3a0', '#6e3b2e', '#b56f52', '#7d8a96'])
city.items = [it for it in city.items if not (it[0] == 'bld' and it[1][1] > 80)
              and not (it[0] in ('tree', 'lamp') and it[1][0] < 0 and -55 < it[1][1] < -10)]
world = SegWorld(28.0, [hook_seg(0, 3.0, 8.1, egoW, [folW] + OW), (3.0, 13.4, egoW, [folW] + OW, []),
                        (13.4, 99, egoR, [folR] + OR, [])], city, 'kmh')


def gap_post(ctx, view, t, lt):
    e, f = world.ego(t), world.others(t)[0]
    ex, ez, eh = e.pose(t)
    fx_, fz_, fh = f.pose(t)
    rear = (ex - math.sin(eh) * 2.2, ez - math.cos(eh) * 2.2)
    gap = math.hypot(rear[0] - fx_, rear[1] - (fz_ + 2.2)) if fz_ + 2.2 < rear[1] else 0
    p = view.pt((fx_, 0, fz_))
    col = '#e0393e' if t < 13.4 else '#22a356'
    label(ctx, p[0] + 10, p[1] + 95, f'Gap: {gap:.1f} m', col, 44)


HOOK_CAM = dict(cam='fixed', pos=(-3.0, 3.6, -25.0), target=(3.0, 0.8, -8.0), f=1000)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (8.4, 'm_cam', dict(cam='inside')),
    (10.6, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'm_top', dict(follow=False, zc=-10.0, xc=6.0, scale=30.0, post=gap_post)),
    (13.4, 'rewind_seq', dict()),
    (16.6, 'm_cam', dict(cam='chase')),
    (18.6, 'm_cam', dict(cam='close_r', hud=False)),
    (21.6, 'm_top', dict(follow=False, zc=-18.0, xc=6.0, scale=24.0, post=gap_post)),
    (24.8, 'm_cam', dict(cam='fixed', pos=(-3.0, 3.6, -22.0), target=(6.0, 0.8, -4.0), f=1000)),
    (28.0, 'm_cam', dict(cam='fixed', pos=(0.0, 34, -58), target=(14, 0, 4), hud=False)),
]
shots = build_shots(defs)
shots[5].kw.update(srcs=list(reversed(shots[1:5])), dur=shots[5].dur)
video = Video(['Driver MISTAKE #4', 'No turn signal'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Why did he stop?!', 290, 140, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(4, 'Turning without signalling')),
    (3.2, 5.8, location_tag('Halifax, Nova Scotia')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('No signal... then a sudden stop')),
    (S[3] + 0.1, E[3], caption('The car behind had NO warning')),
    (S[4] + 0.1, E[4], caption("Others can't read your mind")),
    (S[4] + 0.3, E[4], x_mark),
    (S[6], E[9], badge('RIGHT', '#22a356')),
    (S[10] + 0.2, E[10], end_card('Signal first. Slow down second.', 'What annoys YOU most on the road? Comment!')),
]
for n, (i, txt) in enumerate(((6, 'Signal ~3 seconds before'), (7, 'Then slow down gradually'), (8, 'The car behind has time to slow'),
                              (9, 'Turn smoothly')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[9] + 1.2, E[9], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur), 0, 0.15)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.1)
    hook_sfx(m)
    m.add(screech(1.4, 1250), 0.3, 0.7)
    m.add(horn(1.2), 0.9, 0.9)
    m.add(brake_squeal(1.0), 7.5, 0.3, 0.2)
    m.add(screech(1.5, 1250), 8.45, 0.9)
    m.add(horn(1.3), 9.4, 1.0)
    sting_bad(m, S[4] + 0.3)
    m.add(rewind_sfx(1.0), S[5], 1.0)
    m.add(click(), 16.4, 1.1)
    indicator(m, 16.4, 22.6, 1.4, 0.2)
    m.add(click(), 22.6, 1.0)
    for i in range(6, 10):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[9] + 1.2)
    m.add(success_jingle(), S[10] + 0.2, 0.9)
    m.add(pop(), S[10] + 1.0, 0.8)
    return m.out(video.dur)


def verify():
    def gap(e, f, t):
        ex, ez, eh = e.pose(t)
        fx_, fz_, _ = f.pose(t)
        rear = (ex - math.sin(eh) * 2.2, ez - math.cos(eh) * 2.2)
        if abs(rear[0] - fx_) > 2.0:
            return 99
        return rear[1] - (fz_ + 2.2)
    print('wrong min gap', round(min(gap(egoW, folW, t) for t in np.arange(3, 13.4, 0.01)), 2),
          'right min gap', round(min(gap(egoR, folR, t) for t in np.arange(13.4, 28, 0.01)), 2))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    else:
        run(video, sound, 'm04.mp4')
