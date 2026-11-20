"""Driver mistake #6: on the phone at a red light. New York City (avenue, yellow cabs, tall towers)."""
from mkit import *
import life2           # phone_close scene
import kit             # phone_mount scene

CW = 5.0
STOP_Z = -CW - 4.6           # -9.6
EGO_Z = STOP_Z - 2.5         # ego centre when stopped at the line
CROSS_Z = -CW - 2.4          # crosswalk centre
X1, X2 = 1.75, 5.25
CAB = '#f2c230'


def light_state(t):
    if t < 3.0:
        t += 8.7
    if t < 13.4:
        return 'red' if t < 6.5 else ('green' if t < 10.4 else ('yellow' if t < 11.4 else 'red'))
    return 'red' if t < 18.5 else 'green'


egoW = Track(X1, Key([(0, 0), (10.0, 0), (10.25, 3.0), (10.45, 0), (13.4, 0)], 'lin'), 5.0, EGO_Z, C_EGO)
egoR = Track(X1, Key([(0, 0), (22.0, 0), (24.0, 9), (40, 10)], 'lin'), 15.0, EGO_Z, C_EGO)


def queue(ego_go, lane_go, seg_t, seed):
    cars = []
    for i in range(1, 6):        # behind the ego, same lane (they only move when the ego moves)
        go = ego_go + 0.8 * i
        k = Key([(0, 0), (go, 0), (go + 2.0, 9), (60, 10)], 'lin') if ego_go < 90 else const(0)
        cars.append(Track(X1, k, seg_t, EGO_Z - 6.8 * i, CAB if i % 2 else COLS[(i + seed) % 10]))
    for i in range(0, 6):        # lane 2: they go on green
        go = lane_go + 0.8 * i
        cars.append(Track(X2, Key([(0, 0), (go, 0), (go + 2.0, 9), (60, 10)], 'lin'), seg_t, EGO_Z - 6.8 * i, CAB if i % 2 == 0 else COLS[(i * 3 + seed) % 10]))
    return cars


def cross_cars(t_end, seg_t0):
    out = []
    for i in range(6):
        p = Path([('L', (300, 1.75), (-300, 1.75))])
        out.append(Mover(p, const(11), seg_t0 + 0.2 + i * 1.6, p.s_near(-30, 1.75) - (i % 2) * 0, CAB if i % 2 else '#c9c9d6', t0=-40, t1=120))
    return [c for c in out]


QW = queue(99, 7.0, 5.0, 1)
QR = queue(22.0, 18.8, 15.0, 2)
XW = [c for c in cross_cars(6.0, 0.6)]
XR = [c for c in cross_cars(18.2, 11.0)]


class Gate:
    """Hide cross traffic once the avenue light turns green."""

    def __init__(self, a, t_end):
        self.a, self.t_end, self.col = a, t_end, a.col

    def __getattr__(self, k):
        return getattr(self.a, k)

    def visible(self, t):
        x = self.a.pose(t)[0]
        return t < self.t_end or x < -12


XW = [Gate(c, 6.0) for c in XW]
XR = [Gate(c, 18.2) for c in XR]
pedW = Ped(Key([(0, -9.0), (5.95, -9.0), (10.2, 1.75 * 0 + 1.75), (20, 14)], 'lin'), const(CROSS_Z), top='#e05d5d')
pedR = Ped(Key([(0, -9.0), (16.5, -9.0), (19.9, 1.75), (21.6, 4.1), (30, 16)], 'lin'), const(CROSS_Z), top='#56b38a', hair='#c7782e')
sidewalk_peds = [Ped(const(9.2), Key([(0, -60), (40, -10)], 'lin'), top='#9a6fd0'), Ped(const(-9.2), Key([(0, 30), (40, -20)], 'lin'), top='#3a7bd5'),
                 Ped(const(9.8), Key([(0, 20), (40, 50)], 'lin'), top='#f2a541', skin='#8d5a3b', hair='#1b1b1b')]


def signals(ctx, view, t):
    st = light_state(t)
    out = []
    zp = CW + 1.6
    out.append(((8.8, 4, zp), lambda: mast(ctx, view, st)))
    return out


def mast(ctx, view, st):
    zp = CW + 1.6
    if view.ortho:
        return
    b, tp, s = view.pt((8.6, 0, zp)), view.pt((8.6, 6.6, zp)), view.scale((8.6, 0, zp))
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
        signal_head(ctx, view, hx, 5.7, zp, math.pi, st)


def nyc_sky(ctx, view):
    towers(ctx, view, 1400, -500, 500, 34, 120, 320, seed=8, w=(26, 46))
    if view.ortho:
        return
    X, Z = 40.0, 1150.0            # art-deco spire tower
    b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
    if b and s:
        col = mix(hexc('#9aa6b8'), hexc('#d4e8f6'), 0.25)
        for w, h0, h1 in ((60, 0, 250), (44, 250, 330), (30, 330, 380), (18, 380, 410)):
            ctx.rectangle(b[0] - w / 2 * s, b[1] - h1 * s, w * s, (h1 - h0) * s)
            setc(ctx, col)
            ctx.fill()
        poly(ctx, [(b[0] - 6 * s, b[1] - 410 * s), (b[0] + 6 * s, b[1] - 410 * s), (b[0], b[1] - 470 * s)])
        ctx.fill()


city = Street('city', n=2, median='yellow', cross=0.0, cw=CW, sidewalk=True, seed=21, skyline=nyc_sky, extras=signals,
              hmin=30, hmax=90, setback=1.0, palette=['#c9b9a6', '#a9b8c6', '#8f9aa8', '#b7a28a', '#7d8a96', '#d8cfc0', '#9fb0c4'])
world = SegWorld(28.0, [hook_seg(0, 3.0, 8.7, egoW, QW + XW, [pedW] + sidewalk_peds), (3.0, 13.4, egoW, QW + XW, [pedW] + sidewalk_peds),
                        (13.4, 99, egoR, QR + XR, [pedR] + sidewalk_peds)], city, 'mph')


def face_shock(ctx, w, t, lt, kw):
    engine.SCENES['face_day'](ctx, w, t, lt, dict(expr='shock', shake=1.0))


engine.SCENES['face_shock'] = face_shock

HOOK_CAM = dict(cam='fixed', pos=(-7.0, 2.0, -3.5), target=(2.0, 0.8, -9.5), f=950)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='high')),
    (8.2, 'phone_close', dict(swipes=[0.6, 1.2, 1.8], notifs=[(0.1, 'New message', '#22a356')])),
    (9.8, 'm_cam', dict(cam='fixed', pos=(-0.8, 5.5, -46), target=(3.0, 4.2, 6), hud=False)),
    (11.4, 'm_cam', dict(HOOK_CAM)),
    (12.4, 'face_shock', dict()),
    (13.4, 'rewind_seq', dict()),
    (16.0, 'phone_mount', dict(muted=[0.9])),
    (19.4, 'm_cam', dict(cam='inside')),
    (22.0, 'm_cam', dict(cam='inside')),
    (24.8, 'm_cam', dict(cam='chase')),
    (28.0, 'm_cam', dict(cam='fixed', pos=(-6, 22, -60), target=(3, 2, 0), hud=False)),
]
shots = build_shots(defs)
shots[6].kw.update(srcs=list(reversed(shots[1:6])), dur=shots[6].dur)
video = Video(['Driver MISTAKE #6', 'Phone at a red light'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Look up!', 290, 170, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(6, 'Phone at a red light')),
    (3.2, 5.8, location_tag('New York City')),
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.1, E[2], caption('"Just one quick message..."')),
    (S[3] + 0.1, E[3], caption("Green light... everyone's honking")),
    (S[4] + 0.1, E[4], caption('He rushes... someone is still crossing!')),
    (S[5] + 0.1, E[5], caption('Red light is NOT phone time')),
    (S[5] + 0.3, E[5], x_mark),
    (S[7], E[10], badge('RIGHT', '#22a356')),
    (S[11] + 0.2, E[11], end_card('Phone away. Eyes up. Then go.', 'Do YOU check your phone at red lights? Comment!')),
]
for n, (i, txt) in enumerate(((7, 'Phone away: Driving Focus ON'), (8, 'Eyes on the light'), (9, 'Green? Check the crosswalk first'),
                              (10, 'Then go smoothly')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[10] + 1.0, E[10], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur, 1.6), 0, 0.3)
    m.add(engine_idle(video.dur), 0, 0.2)
    hook_sfx(m)
    m.add(screech(0.8, 1300), 1.3, 0.8)
    m.add(horn(0.8), 0.6, 0.7, 0.3)
    m.add(text_ping(), S[2] + 0.1, 1.0)
    m.add(typing(1.8, 5) * 1.2, S[2] + 0.5, 0.9)
    for k, tt in enumerate((7.9, 8.5, 9.0, 9.4)):
        m.add(horn(0.5 + 0.2 * k, doppler=[0.9 + 0.05 * k] * 4), tt, 0.8, (-1) ** k * 0.3)
    m.add(screech(0.8, 1300), 10.25, 0.9)
    m.add(impact(), S[5], 0.4)
    sting_bad(m, S[5] + 0.3)
    m.add(rewind_sfx(1.0), S[6], 1.0)
    m.add(pop(), S[7] + 0.9, 0.5)
    m.add(bell(midi(84), 0.6), 18.5, 0.7)
    for i in range(7, 11):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[10] + 1.0)
    m.add(success_jingle(), S[11] + 0.2, 0.9)
    m.add(pop(), S[11] + 1.0, 0.8)
    return m.out(video.dur)


def verify():
    gw = min(CROSS_Z - 0.3 - (egoW.z(t) + 2.2) for t in np.arange(9.9, 10.6, 0.005) if abs(pedW.x(t) - X1) < 1.3)
    print('wrong: ego front to pedestrian (m)', round(gw, 2), 'ego front final', round(egoW.z(11) + 2.2, 2), 'stop line', STOP_Z)
    tclear = next(t for t in np.arange(19, 24, 0.01) if pedR.x(t) > X1 + 0.92 + 1.5)
    print('right: ped clears lane at', round(tclear, 2), 'ego moves at 22.0; green at 18.5')
    print('queue min gap wrong', min_gap([egoW] + QW, 3, 13.4), 'right', min_gap([egoR] + QR, 13.4, 28.0))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        verify()
    else:
        run(video, sound, 'm06.mp4')
