"""Driver mistake #10: stopping too close behind the car ahead. Seattle (needle tower, Mount Rainier, rain-washed streets)."""
from mkit import *

X1, X2 = 1.75, 5.25
STOP_Z = -11.2
FRONT_Z = STOP_Z - 2.5          # front car centre at the light
GAP_W, GAP_R = 0.6, 3.4         # bumper gaps: wrong / right


def light_state(t):
    return 'red'


front = lambda tA: Track(X1, const(0), tA, FRONT_Z, '#3a7bd5')
frontW = front(3.0)
frontR = Track(X1, Key([(0, 0), (24.0, 0), (25.5, 4), (40, 6)], 'lin'), 13.4, FRONT_Z, '#3a7bd5')
egoW = Track(X1, Key([(0, 8), (4.0, 8), (5.6, 0), (9.0, 0), (9.12, 2.0), (9.24, 0), (13.4, 0)], 'lin'), 5.6, FRONT_Z - 4.4 - GAP_W, C_EGO)
egoR_x = const(X1)
egoR = Track(egoR_x, Key([(0, 8), (14.4, 8), (16.6, 0), (22.5, 0), (22.8, 1.6), (23.2, 1.6), (23.5, 0), (24.4, 0), (25.0, 2.5), (27.6, 3.5), (30, 4)], 'lin'), 16.6, FRONT_Z - 4.4 - GAP_R, C_EGO,
             )
# a distracted pickup arrives behind and can't stop in time
rearW = Track(X1, Key([(0, 13), (7.8, 13), (9.0, 2.0), (9.15, 0)], 'lin'), 9.0, egoW.z(9.0) - 4.4 - 0.0, '#2f6f73')
rearR = Track(X1, Key([(0, 13), (21.9, 13), (23.2, 2.0), (23.6, 0)], 'lin'), 23.6, egoR.z(23.6) - 4.4 - 0.9, '#2f6f73')
lane2 = lambda tA: [Track(X2, const(0), tA, FRONT_Z - 6.6 * i, COLS[(i * 3) % 10]) for i in range(0, 2)]
L2W, L2R = lane2(3.0), lane2(13.4)
L2R = [Track(X2, Key([(0, 0), (24.0, 0), (25.5, 4), (40, 6)], 'lin'), 13.4, FRONT_Z - 6.6 * i, COLS[(i * 3) % 10]) for i in range(0, 2)]


def cross(t0):
    out = []
    for i in range(4):
        p = Path([('L', (300, 1.75), (-300, 1.75))])
        out.append(Mover(p, const(11), t0 + i * 2.2, p.s_near(-20, 1.75), COLS[(i * 5) % 10], t0=-40, t1=120))
    return out


XW, XR = cross(3.5), cross(14.0)


def seattle_sky(ctx, view):
    if view.ortho:
        return
    X, Z = 600.0, 3600.0                          # big snowy volcano
    b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
    if b and s:
        poly(ctx, [(b[0] - 1400 * s, b[1]), (b[0] - 160 * s, b[1] - 420 * s), (b[0] + 160 * s, b[1] - 430 * s), (b[0] + 1400 * s, b[1])])
        setc(ctx, mix(hexc('#8fa6c0'), hexc('#dcefff'), 0.35))
        ctx.fill()
        poly(ctx, [(b[0] - 420 * s, b[1] - 300 * s), (b[0] - 160 * s, b[1] - 420 * s), (b[0] + 160 * s, b[1] - 430 * s), (b[0] + 440 * s, b[1] - 300 * s),
                   (b[0] + 200 * s, b[1] - 330 * s), (b[0] + 40 * s, b[1] - 300 * s), (b[0] - 150 * s, b[1] - 335 * s)])
        setc(ctx, hexc('#f6f8fb'))
        ctx.fill()
    towers(ctx, view, 1400, -380, 250, 22, 90, 240, seed=16, base='#8f9aa8')
    X, Z = -220.0, 1100.0                         # needle tower with a saucer top
    b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
    if b and s:
        col = mix(hexc('#e9e6de'), hexc('#d4e8f6'), 0.2)
        for sx in (-1, 1):
            ctx.move_to(b[0] + sx * 18 * s, b[1])
            ctx.curve_to(b[0] + sx * 3 * s, b[1] - 80 * s, b[0] + sx * 3 * s, b[1] - 120 * s, b[0] + sx * 8 * s, b[1] - 150 * s)
        setc(ctx, col)
        ctx.set_line_width(max(2, 5 * s))
        ctx.stroke()
        ellipse(ctx, b[0], b[1] - 152 * s, 26 * s, 6 * s)
        setc(ctx, col)
        ctx.fill()
        ellipse(ctx, b[0], b[1] - 158 * s, 18 * s, 5 * s)
        setc(ctx, hexc('#c9a24a'))
        ctx.fill()
        ctx.rectangle(b[0] - 1.2 * s, b[1] - 185 * s, 2.4 * s, 26 * s)
        setc(ctx, col)
        ctx.fill()


def extras(ctx, view, t):
    zp = 7.0 + 1.6

    def mast():
        if view.ortho:
            return
        b, tp, s = view.pt((8.8, 0, zp)), view.pt((8.8, 6.6, zp)), view.scale((8.8, 0, zp))
        if not b or not tp or not s:
            return
        ctx.rectangle(b[0] - 0.13 * s, tp[1], 0.26 * s, b[1] - tp[1])
        fill_stroke(ctx, hexc('#2a2c33'), OUTL, max(1, s / 50))
        a = view.pt((0.8, 6.5, zp))
        if a:
            ctx.move_to(*tp)
            ctx.line_to(*a)
            setc(ctx, hexc('#2a2c33'))
            ctx.set_line_width(max(2, 0.18 * s))
            ctx.stroke()
        for hx in (X1, X2):
            signal_head(ctx, view, hx, 5.7, zp, math.pi, 'red' if (t < 13.4 or t < 24.0) else 'green')
    return [((8.8, 4, zp), mast)]


city = Street('city', n=2, median='yellow', cross=0.0, cw=7.0, sidewalk=True, seed=41, skyline=seattle_sky, extras=extras, hmin=14, hmax=45,
              setback=0.5, sky=('#7fa6c9', '#dfeaf2'), palette=['#8f9aa8', '#a9b8c6', '#b7a28a', '#7d8a96', '#c9b9a6', '#5f6f80'])
world = SegWorld(30.6, [hook_seg(0, 3.0, 6.2, egoW, [frontW, rearW] + L2W + XW), (3.0, 13.4, egoW, [frontW, rearW] + L2W + XW, []),
                        (13.4, 99, egoR, [frontR, rearR] + L2R + XR, [])], city, 'mph')


class Bump:
    """Push the ego into the car ahead when hit from behind (wrong) / it absorbs the push in the gap (right)."""


def ego_push_w(t):
    return 0.0


# hit from behind: shove the ego forward by the gap size at the moment of impact (9.15)
_ew_pose = egoW.pose
egoW.pose = lambda t: (lambda p: (p[0], p[1] + (GAP_W - 0.05) * smooth((t - 9.15) / 0.15), p[2]))(_ew_pose(t))
_fw_pose = frontW.pose
frontW.pose = lambda t: (lambda p: (p[0], p[1] + 0.9 * smooth((t - 9.25) / 0.25), p[2]))(_fw_pose(t))


def gap_post(ctx, view, t, lt):
    e = world.ego(t)
    f = world.others(t)[0]
    ex, ez, _ = e.pose(t)
    fx_, fz_, _ = f.pose(t)
    g = fz_ - 2.2 - (ez + 2.2)
    p = view.pt((X1 - 2.6, 0, (ez + fz_) / 2))
    label(ctx, p[0], p[1], f'{max(0.0, g):.1f} m', '#e0393e' if g < 1.5 else '#22a356', 50)


def tyres_overlay(ctx, lt, d):
    label(ctx, 960, 200, 'See the tyres of the car ahead touching the road', '#2f6f9f', 44)


HOOK_CAM = dict(cam='fixed', pos=(-6.0, 1.8, -27.0), target=(1.8, 0.8, -18.0), f=950)
TOP = dict(follow=False, horizontal=False, xc=3.5, zc=FRONT_Z - 5.0, scale=46.0, post=gap_post)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (8.2, 'm_cam', dict(cam='inside')),
    (10.6, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'm_top', dict(TOP)),
    (13.4, 'rewind_seq', dict()),
    (17.4, 'm_cam', dict(cam='chase')),
    (19.6, 'm_cam', dict(cam='inside')),
    (22.0, 'm_mirror', dict(side='L')),
    (24.6, 'm_top', dict(TOP)),
    (27.6, 'm_cam', dict(cam='high')),
    (30.6, 'm_cam', dict(cam='fixed', pos=(-14, 18, -55), target=(3, 0, -10), hud=False)),
]
shots = build_shots(defs)
shots[5].kw.update(srcs=list(reversed(shots[1:5])), dur=shots[5].dur)
video = Video(['Driver MISTAKE #10', 'No space at a stop'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Nowhere to go!', 290, 150, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(10, 'Stopping too close')),
    (3.2, 5.8, location_tag('Seattle, Washington')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('Bumper-to-bumper at the red light')),
    (S[3] + 0.1, E[3], caption('Hit from behind... pushed into the car ahead!')),
    (S[4] + 0.1, E[4], caption('No gap = no escape = TWO crashes')),
    (S[4] + 0.3, E[4], x_mark),
    (S[6], E[10], badge('RIGHT', '#22a356')),
    (S[7] + 0.3, E[7], tyres_overlay),
    (S[11] + 0.2, E[11], end_card('See their tyres. Keep your escape route.', 'Did you know this trick? Comment!')),
]
for n, (i, txt) in enumerate(((6, 'Stop with room in front'), (7, 'The tyre rule'), (8, 'Check your mirror while stopped'),
                              (9, 'Car coming too fast? You can move!'), (10, 'Escape route = safety')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[10] + 1.0, E[10], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur, 1.4), 0, 0.22)
    m.add(engine_idle(video.dur), 0, 0.15)
    hook_sfx(m)
    m.add(screech(1.2, 1200), 0.8, 0.8)
    m.add(thud(), 2.95, 1.0)
    m.add(screech(1.4, 1200), 7.8, 0.8)
    m.add(thud(), 9.15, 1.2)
    m.add(impact(), 9.15, 0.6)
    m.add(thud(), 9.3, 0.9)
    sting_bad(m, S[4] + 0.3)
    m.add(rewind_sfx(1.0), S[5], 1.0)
    m.add(screech(1.8, 1200), 22.0, 0.8)
    m.add(horn(0.4), 22.4, 0.6)
    m.add(head_swish(), S[8] + 0.1, 0.9, -0.5)
    m.add(bell(midi(84), 0.5), 24.0, 0.6)
    for i in range(6, 11):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[10] + 1.0)
    m.add(success_jingle(), S[11] + 0.2, 0.9)
    m.add(pop(), S[11] + 1.0, 0.8)
    return m.out(video.dur)


def verify():
    print('wrong stopped gap', round(frontW.pose(8)[1] - 2.2 - (egoW.pose(8)[1] + 2.2), 2), 'pickup gap before hit',
          round(egoW.pose(9.0)[1] - 2.2 - (rearW.pose(9.0)[1] + 2.2), 2))
    print('right stopped gap', round(frontR.pose(20)[1] - 2.2 - (egoR.pose(20)[1] + 2.2), 2),
          'pickup final gap to ego', round(min(egoR.pose(t)[1] - 2.2 - (rearR.pose(t)[1] + 2.2) for t in np.arange(13.4, 30, 0.01)), 2))
    print('right ego never touches front car:', round(min(frontR.pose(t)[1] - 2.2 - (egoR.pose(t)[1] + 2.2)
                                                        for t in np.arange(13.4, 30, 0.01) if abs(egoR.pose(t)[0] - X1) < 1.8), 2))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    else:
        run(video, sound, 'm10.mp4')
