"""Left-lane camper (cinematic, SQUARE 1:1, funny). Highway 401, Toronto, Ontario (template: city_401).

Walt drives 60 km/h in the LEFT lane of a 100 km/h highway, whistling. Behind him the left lane fills up: cars arrive
at 100, brake hard (brake-light wave) and crawl in a long queue, while the right lanes are almost empty.
A frustrated driver passes on the right and cuts back in front of him (near miss, slow motion).
Lesson: Ontario Highway Traffic Act s.147 - slower traffic must keep to the right lane. Walt finally signals and moves
right, and the whole lane flows again.  The queue is an IDM car-following sim (queue_sim) so the wave is physical.
"""
from cinetemplate import *
import street

EP.unit = 'kmh'
VG, VF = 16.7, 27.8                       # Walt 60 km/h, everybody else 100 km/h
T_W0, T_W1 = 11.5, 12.7                   # weaver pulls out to lane 1
T_C0, T_C1, T_CUT = 14.7, 15.5, 15.4      # weaver cuts back in front of Walt
T_GS, T_G0, T_G1 = 19.0, 19.6, 21.0       # Walt signals and moves right
EP.tm = TimeMap([(15.0, 17.5, 0.35)])


def walt_expr(t):
    if T_C0 + 0.3 < t < T_C1 + 1.6:
        return 'shock'
    return 'whistle' if t < T_GS else 'smile'


GX = Key([(0, LANES[0]), (T_G0, LANES[0]), (T_G1, LANES[1]), (99, LANES[1])])
WALT = Veh(GX, const(VG), 0.0, 0.0, '#d8c3a0', occ=occ_of('grandpa', walt_expr), blink=blink_side([(T_GS, T_G1 + 0.3)], 'R'))

# weaver: in the queue right behind Walt, pulls out right, passes, cuts back in ~6 m ahead of him
WX = Key([(0, LANES[0]), (T_W0, LANES[0]), (T_W1, LANES[1]), (T_C0, LANES[1]), (T_C1, LANES[0]), (99, LANES[0])])
WS = Key([(0, VG), (T_W0, VG), (13.0, 25.5), (T_C1, 25.5), (17.5, VF + 1), (99, VF + 1)], 'lin')
W = Veh(WX, WS, T_CUT, WALT.z(T_CUT) + 4.5 + 6.0, '#7a4fd0', occ=occ_of('husb', lambda t: 'annoyed'),
        blink=lambda t: 'R' if T_W0 - 1.0 < t < T_W1 and (t * 1.6) % 1 < 0.5 else ('L' if T_C0 - 0.8 < t < T_C1 and (t * 1.6) % 1 < 0.5 else None))


def in_lane0(a, t):
    return abs(a.xk(t) - LANES[0]) < 1.9


def queue_sim(starts, t0=-2.0, t1=45.0, dt=1 / 60, v0=VF, T=1.1, s0=3.0, amax=1.6, b=3.0):
    """IDM followers in lane 0. starts: [(z0, v0)] at t0 (front to back). Leaders: Walt, the weaver (while in lane 0)
    and the car ahead. Returns [(z_fn, v_fn)]."""
    ts = np.arange(t0, t1, dt)
    n = len(starts)
    z = np.array([s[0] for s in starts], float)
    v = np.array([s[1] for s in starts], float)
    Z, Vv = [z.copy()], [v.copy()]
    for t in ts[1:]:
        lz = []
        if in_lane0(WALT, t):
            lz.append((WALT.z(t), WALT.speed(t)))
        if in_lane0(W, t) and not (T_C0 < t < T_C1 + 0.2):
            lz.append((W.z(t), W.speed(t)))
        acc = np.zeros(n)
        for i in range(n):
            cand = [(zz, vv) for zz, vv in lz if zz > z[i]] + [(z[j], v[j]) for j in range(i) if z[j] > z[i]]
            ss, dv = 1e9, 0.0
            if cand:
                zz, vv = min(cand, key=lambda c: c[0])
                ss, dv = max(0.5, zz - z[i] - 4.5), v[i] - vv
            sstar = s0 + max(0.0, v[i] * T + v[i] * dv / (2 * math.sqrt(amax * b)))
            acc[i] = amax * (1 - (v[i] / v0) ** 4 - (sstar / ss) ** 2)
        acc = np.clip(acc, -8.0, amax)
        v = np.maximum(0.0, v + acc * dt)
        z = z + v * dt
        Z.append(z.copy())
        Vv.append(v.copy())
    Z, Vv = np.array(Z), np.array(Vv)
    return [((lambda t, i=i: float(np.interp(t, ts, Z[:, i]))), (lambda t, i=i: float(np.interp(t, ts, Vv[:, i])))) for i in range(n)]


z_w0 = W.z(-2.0)
starts = [(z_w0 - 15.0, VG), (z_w0 - 30.0, VG), (z_w0 - 45.0, VG)] + [(z_w0 - 45.0 - 34.0 * k, VF) for k in range(1, 11)]
QCOL = ['#e23b3b', '#3a7bd5', '#f2a541', '#37b26c', '#f4f4f6', '#2f6f73', '#c9c9d6', '#e05d5d', '#1c1c22', '#3a7bd5', '#f2a541', '#37b26c', '#7a4fd0']
QUEUE = []
for i, (zf_, vf_) in enumerate(queue_sim(starts)):
    who = ['husb', 'lady', 'daughter', 'hero'][i % 4] if i < 6 else None
    occ = occ_of(who, lambda t: 'annoyed') if who else None
    QUEUE.append(SimCar(LANES[0], zf_, vf_, QCOL[i], occ=occ))

# right lanes: light, fast traffic (lane 1 kept clear around the weaver and around Walt's lane change)
TRAF = []
for lane, z0, col in ((2, -300.0, COLS[2]), (1, 140.0, COLS[5]), (2, -60.0, COLS[3]), (2, -240.0, COLS[7]), (2, 90.0, COLS[0]),
                      (3, -20.0, COLS[4]), (3, -150.0, COLS[6]), (3, 60.0, COLS[1]), (2, -400.0, COLS[9]), (3, -330.0, COLS[8])):
    TRAF.append(Veh(LANES[lane], const(VF), 0.0, z0, col))
ONC = [Rev(-5.0 if i % 2 else -11.0, -300 + 47 * i, COLS[(i * 3) % 10]) for i in range(40)]
EP.hero = WALT
EP.shadows = [WALT, W] + QUEUE + TRAF + ONC

CITY = city_401((WALT.z(12.0) + 260.0, WALT.z(24.0) + 420.0))
world = make_world(CITY, WALT, [W] + QUEUE + TRAF + ONC)

DUR = 27.0
VT = EP.tm.wt
VC = EP.tm.vt(T_CUT)
LAST = QUEUE[-1]


def lesson(ctx, view, t, lt):
    a = smooth(lt / 0.5)
    zw = WALT.z(t)
    for x0, x1, z0, z1, col in ((0.0, 3.5, zw - 45, zw - 3, '#ff4b4b'), (3.5, 14.0, zw - 45, zw + 120, '#22c35e')):
        pts = [view.pt((x0, 0.02, z0)), view.pt((x1, 0.02, z0)), view.pt((x1, 0.02, z1)), view.pt((x0, 0.02, z1))]
        if all(pts):
            poly(ctx, pts)
            setc(ctx, hexc(col), 0.28 * a)
            ctx.fill()


defs = [
    (3.0, 'cine', dict(cam='crane', target=WALT, ox=4.0, oz0=-105.0, oz1=-85.0, y0=15.0, y1=18.0, tx=0.0, tz=-35.0, f=1000, dt=9.0)),
    (6.0, 'dash_face', dict(who='grandpa', expr='whistle', turn=lambda lt: 0.15 * math.sin(lt * 2))),
    (9.0, 'interior_mirror', dict(f=900, sleeve=hexc('#9fc3e6'), mirror_glow=lambda t: True)),
    (12.0, 'cine', dict(cam='tele', target=WALT, off=(7.0, 4.5, -330.0), tx=-1.0, tz=-70.0, f=2400)),
    (15.0, 'cine', dict(cam='track', target=W, off=(3.4, 1.1, -6.5), look=(-1.2, 0.9, 5.0), f=760, shake=0.08, streak=0.5, flare=0.35)),
    (17.5, 'cine', dict(cam='heli', target=WALT, R=20.0, H=9.0, a0=0.7, w=0.1, f=950, oz=5.0)),
    (20.5, 'cine', dict(cam='top', center=lambda t: (6.0, WALT.z(t) - 30.0), H=75.0, f=1000, post=lesson)),
    (24.0, 'cine', dict(cam='heli', target=WALT, R=40.0, H=18.0, a0=-2.6, w=0.12, f=1000, oz=-25.0)),
    (DUR, 'cine', dict(cam='crane', target=WALT, ox=8.0, oz0=-30.0, oz1=-40.0, y0=2.0, y1=24.0, tz=150.0, f=1000)),
]
video = make_video(['Slow in the LEFT lane?', 'Look what happens behind you'], world, defs, DUR)
S, E = video.S, video.E


def kmh(a, shot):
    return lambda lt: a.speed(VT(S[shot] + lt) + video.shots[shot].kw.get('dt', 0.0)) * 3.6


video.overlays = [
    (0.0, 3.0, big_text('Why is the LEFT lane stuck?', 300, 104, hexc('#ffd23f'), 0.15, True)),
    (3.0, 6.0, location_tag('Highway 401, Toronto, Ontario')),
    (3.2, 6.0, sq_caption('Meet Walt. 60 km/h. In the passing lane.', 74)),
    (S[2] + 0.2, E[2], sq_caption('Behind him... everyone has to brake', 76)),
    (S[3] + 0.2, E[3], sq_caption('A jam out of nothing. Right lanes: empty.', 72)),
    (S[3] + 0.3, E[3], value_tag(kmh(QUEUE[8], 3), 'LEFT LANE', 'km/h', 90, 70, x=1600, y=1560, fmt='{:.0f}')),
    (S[4] + 0.2, E[4], sq_caption('Frustrated drivers pass on the right...', 74)),
    (S[5], E[5], slowmo_tag),
    (S[5] + 0.2, E[5], sq_caption('...and cut back in. That is how crashes start.', 68)),
    (VC + 0.2, E[5], x_mark),
    (S[6], E[6], badge('KEEP RIGHT EXCEPT TO PASS', '#22a356')),
    (S[6] + 0.2, E[6], sq_caption('Ontario law: slower traffic keeps right (HTA s.147)', 62)),
    (S[7] + 0.2, E[7], sq_caption('Walt moves right. Traffic flows again.', 74)),
    (EP.tm.vt(T_G1) + 0.6, E[7], check_mark),
    (S[8] + 0.2, E[8], end_card('Left lane = passing lane.', 'Ever been stuck behind a left-lane camper? Comment!')),
]


# ------------------------------------------------------------------ sound (original style)
def sound():
    m = Mixer(DUR)
    highway_bed(m, DUR)
    m.add(braam(2.0, 52), 0.05, 0.6)
    for k, tt in enumerate((0.6, 1.4, 2.2)):
        m.add(horn(0.4), tt, 0.45, -0.3 + 0.3 * k)
    m.add(street.whistle_tune(), 3.3, 0.9)
    m.add(street.whistle_tune(), 5.0, 0.6)
    # mirror: horns and brakes behind him
    for tt in (S[2] + 0.5, S[2] + 1.6, S[2] + 2.3):
        m.add(horn(0.35), tt, 0.4, 0.0)
    m.add(brake_squeal(1.0), S[2] + 1.0, 0.3)
    # brake wave: every arriving car brakes
    for q in QUEUE[3:]:
        for t in np.arange(0.0, 15.0, 0.05):
            if q.vfn(t) > 26.0 and q.vfn(t + 0.3) < q.vfn(t) - 0.6:
                if S[3] <= t < E[3]:
                    m.add(brake_squeal(0.8), t, 0.25, 0.0)
                break
    m.add(heartbeat(3, 110), S[3] + 0.3, 0.4)
    # weaver
    m.add(v8(3.0, lambda u: 0.7 + 0.3 * min(1, u / 1.2)), S[4], 0.45)
    m.add(car_pass(1.4, 0.5, 110), S[4] + 1.6, 0.6, pans(1.4, 0.6, -0.6))
    m.add(braam(2.4, 41), S[5], 0.5)
    m.add(slow(brake_squeal(1.2), 0.35), VC - 0.6, 0.6)
    m.add(slow(horn(0.8), 0.35), VC + 0.1, 0.6)
    m.add(impact(), VC + 0.2, 0.3)
    m.add(sad_trombone(), E[5] - 1.3, 0.45)
    # lesson + resolution
    m.add(pop(), S[6] + 0.15, 0.6)
    m.add(click(), EP.tm.vt(T_GS), 0.6)
    indicator(m, EP.tm.vt(T_GS), EP.tm.vt(T_G1 + 0.3), 0.4, 0.2)
    for k in range(4):
        m.add(car_pass(1.2, 0.5, 100 + 8 * k), S[7] + 1.0 + 0.5 * k, 0.45, pans(1.2, -0.6, 0.6))
    m.add(chime(), EP.tm.vt(T_G1) + 0.6, 0.6)
    m.add(success_jingle(), S[8] + 0.3, 0.8)
    return m.out(DUR)


def verify():
    agents = [('WALT', WALT), ('W', W)] + [(f'Q{i}', q) for i, q in enumerate(QUEUE)] + [(f'T{i}', c) for i, c in enumerate(TRAF)]
    verify_gaps(agents, 0.0, 26.0)
    print('weaver start offset behind Walt', round(W.z(0) - WALT.z(0), 1), '| cut-in gap', round(W.z(T_CUT) - 2.25 - WALT.z(T_CUT) - 2.25, 1),
          '| video cut-in', round(VC, 2))
    print('queue min speed km/h', [round(min(q.vfn(t) for t in np.arange(0, 20, 0.1)) * 3.6) for q in QUEUE])
    print('queue speeds at 18 / 24 s', [round(q.vfn(18) * 3.6) for q in QUEUE], [round(q.vfn(24) * 3.6) for q in QUEUE])
    for i, s in enumerate(video.shots):
        print(i, s.kind, s.kw.get('cam', ''), round(S[i], 2), '-', round(E[i], 2), 'world', round(VT(S[i]), 2), '-', round(VT(E[i]), 2))


if __name__ == '__main__':
    run(video, sound, verify, 'leftlane.mp4')
