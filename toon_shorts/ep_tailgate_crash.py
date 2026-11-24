"""Tailgating crash (cinematic, SQUARE 1:1, serious). I-35E into Dallas, Texas (same road as ep_sample_city.py).

Our driver follows a blue car only ~9 m (0.3 s) behind at 65 mph. Traffic ahead is stopped; the blue car brakes
hard (7.5 m/s^2). He needs ~1 s to react, so he hits her at ~17 mph closing speed (slow motion).
Lesson: keep at least 3 seconds of following distance. Built on cinetemplate.py (follow_sim, SimCar, CrashFX).
"""
from cinetemplate import *

T_B = 9.4                       # lead brakes (world t)
GAP0, REACT, DEC = 9.0, 1.0, 7.5
EP.tm = TimeMap([(10.6, 13.6, 0.35)])
LEAD_V = Key([(0, V), (T_B, V), (T_B + V / DEC, 0.0), (99, 0.0)], 'lin')
zl, zf, T_IMP, V_REL, vl, vf = follow_sim(LEAD_V, GAP0, REACT, DEC, T_B, bounce=0.4)


def hazard_after(t0):
    return lambda t: 'B' if t > t0 and (t * 1.5) % 1 < 0.5 else None


def hero_expr(t):
    if t < T_B + 0.3:
        return 'calm'
    return 'shock' if t < T_IMP + 2.5 else 'worried'


HERO = SimCar(LANES[1], zf, vf, '#e23b3b', occ=occ_of('hero', hero_expr), damage=[('front', T_IMP)],
              blink=hazard_after(T_IMP + 3.0))
LEAD = SimCar(LANES[1], zl, vl, '#3a7bd5', occ=occ_of('lady', lambda t: 'shock' if t > T_B else 'calm'),
              damage=[('back', T_IMP)], blink=hazard_after(T_IMP + 3.2))
Z_STOP = zl(40)
Z_IMP = zl(T_IMP) - 2.25
FX = CrashFX(T_IMP, lambda t: (LANES[1], 0.7, zl(t) - 2.25))

# stopped traffic jam ahead (all lanes), the blue car stops behind it
TRAF = []
for row in range(4):
    for lane in range(4):
        zz = Z_STOP + 9.0 + row * 7.5 + (lane % 2) * 2.0 + (2.5 if lane != 1 else 0)
        TRAF.append(Veh(LANES[lane], const(0.0), 0.0, zz, COLS[(row * 4 + lane) % 10], brake=lambda t: 1.0))
# side lanes: cars with a safe gap brake calmly and stop in time
SAFE = []
for lane, r, col in ((0, -6.0, COLS[5]), (2, 14.0, COLS[3]), (2, -40.0, COLS[7]), (3, -10.0, COLS[4]), (0, -55.0, COLS[6])):
    zstop = Z_STOP + 2.0 - (0 if r > 0 else 12.0 + abs(r) * 0.15)
    # speed key: cruise, then brake so that it stops at zstop
    v = Veh(LANES[lane], const(V), 0.0, r, col)
    z_cruise = v.z(T_B - 0.5)
    d = zstop - z_cruise
    a = V * V / (2 * max(d, 30.0))
    k = Key([(0, V), (T_B - 0.5, V), (T_B - 0.5 + V / a, 0.0), (99, 0.0)], 'lin')
    SAFE.append(Veh(LANES[lane], k, 0.0, r, col))
ONC = [Rev(-5.0 if i % 2 else -11.0, -200 + 47 * i, COLS[(i * 3) % 10]) for i in range(40)]
EP.hero = HERO
EP.shadows = [HERO, LEAD] + TRAF + SAFE + ONC


def far(ctx, view):
    city_skyline(ctx, view, Z=1600.0, xc=40.0, n=26, seed=11, base='#6f7690', hmin=70, hmax=230)


CITY = Highway(sky=('#3d6fb4', '#ffcf9a'), far=far, seed=2,
               gantries=[(Z_STOP - 160.0, [(1.0, 8.0, 'I-35E SOUTH', 'Downtown Dallas'), (9.5, 16.5, 'EXIT 429', 'Main St')])])
world = make_world(CITY, HERO, [LEAD, FX] + TRAF + SAFE + ONC)

DUR = 22.0
VT = EP.tm.wt
VI = EP.tm.vt(T_IMP)
defs = [
    (3.0, 'cine', dict(cam='track', target=HERO, off=(6.5, 1.5, -5.0), look=(0, 0.9, 5.0), f=720, dt=T_IMP - 1.6, shake=0.1,
                       jolt=(T_IMP, 0.6))),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=22.0, H=9.0, a0=-2.3, w=0.2, f=1000, oz=6.0)),
    (8.6, 'interior_mirror', dict(mirror=True, f=1900)),
    (10.6, 'cine', dict(cam='track', target=HERO, off=(-3.6, 0.8, 1.0), look=(0, 0.9, 8.0), f=700, shake=0.08, streak=0.5)),
    (13.6, 'cine', dict(cam='fixed', pos=(LANES[1] + 8.5, 1.3, Z_IMP + 7.0), target_pt=(LANES[1], 0.8, Z_IMP - 1.5), f=820,
                        jolt=(T_IMP, 0.4))),
    (15.6, 'dash_face', dict(expr=lambda lt: 'shock', turn=0.0)),
    (18.6, 'cine', dict(cam='heli', target=LEAD, R=26.0, H=12.0, a0=-1.6, w=0.12, f=1000, oz=-3.0)),
    (DUR, 'cine', dict(cam='crane', target=LEAD, ox=8.0, oz0=-24.0, oz1=-32.0, y0=2.0, y1=20.0, tz=-3.0, f=950)),
]
video = make_video(['Driving this close?', 'Watch what happens'], world, defs, DUR)
S, E = video.S, video.E


def gap_s(shot_i):
    dt = video.shots[shot_i].kw.get('dt', 0.0)

    def f(lt):
        t = VT(S[shot_i] + lt) + dt
        v = HERO.speed(t)
        if t > T_B or v < 1:
            return None
        return (zl(t) - zf(t) - 4.5) / v
    return f


video.overlays = [
    (0.0, 3.0, big_text('Too close to stop?', 300, 120, hexc('#ffd23f'), 0.15, True)),
    (3.0, 6.0, location_tag('I-35E, Dallas, Texas')),
    (3.2, 6.0, sq_caption(f'He drives just {GAP0:.0f} m behind her. At 65 mph.', 70)),
    (3.0, 6.0, value_tag(gap_s(1), 'GAP', 's', 3.0, 2.0, x=1600, y=1560, fmt='{:.1f}')),
    (S[2] + 0.2, E[2], sq_caption("All he sees is her car. Not the traffic ahead.", 66)),
    (S[3] + 0.1, E[3], sq_caption('Traffic stops. She brakes HARD.', 78)),
    (S[4], E[4], slowmo_tag),
    (S[4] + 0.2, VI, sq_caption('He needs 1 second to react...')),
    (VI + 0.05, E[4], sq_caption(f'CRASH. {V_REL * 2.237:.0f} mph into her bumper.', 76)),
    (VI + 0.15, E[4], x_mark),
    (S[5] + 0.2, E[5], sq_caption('Rear-end crashes are the most common crash in the US', 62)),
    (S[6], E[6], badge("DON'T FOLLOW TOO CLOSE", '#e0393e')),
    (S[6] + 0.2, E[6], sq_caption('Keep at least 3 seconds of space', 78)),
    (S[7] + 0.2, E[7], end_card("Don't follow too close. Keep 3 seconds.", 'How many seconds do YOU keep? Comment!')),
]


# ------------------------------------------------------------------ sound
def crunch(d=1.2):
    n = int(d * SR)
    tt = np.arange(n) / SR
    s = bp(noise(n), 120, 4000) * np.exp(-tt / 0.18)
    s += np.sin(2 * np.pi * 55 * tt) * np.exp(-tt / 0.25) * 1.2
    rr = np.zeros(n)
    rnd = np.random.default_rng(4)
    for k in rnd.uniform(0.05, 0.9, 18):        # glass / plastic bits
        i = int(k * SR)
        m_ = min(n - i, int(0.05 * SR))
        rr[i:i + m_] += bp(noise(m_), 2500, 8000) * np.exp(-np.arange(m_) / (0.01 * SR)) * 0.6
    return np.tanh((s + rr) * 1.4) * 0.8


def sound():
    m = Mixer(DUR)
    highway_bed(m, DUR)
    # hook: screech + crash (impact at video 1.6)
    m.add(braam(2.2, 46), 0.05, 0.7)
    m.add(screech(1.0, 1100), 0.6, 0.7)
    m.add(crunch(), 1.6, 1.0)
    # tension while tailgating
    m.add(heartbeat(4, 110), S[2] + 0.2, 0.5)
    m.add(car_pass(1.4, 0.5, 100), 4.0, 0.4, pans(1.4, -0.6, 0.6))
    # lead brakes (world T_B in shot 3), our driver brakes 1 s later
    m.add(brake_squeal(1.6), T_B, 0.6)
    m.add(screech(2.0, 1150), T_B + REACT, 0.8)
    # slow motion crash
    m.add(braam(2.6, 41), S[4], 0.6)
    m.add(slow(screech(1.2, 1150), 0.35), S[4], 0.6)
    m.add(slow(crunch(), 0.35), VI, 1.0)
    m.add(impact(), VI, 0.6)
    m.add(sad_violin(), S[5] + 0.2, 0.5)
    # aftermath: hazards ticking
    indicator(m, S[6], E[6], 0.25, 0.0)
    m.add(whoosh(0.5, 0.4), S[6] - 0.1, 0.4)
    m.add(chime(), S[7] + 0.3, 0.5)
    return m.out(DUR)


def verify():
    worst = verify_gaps([('HERO', HERO), ('LEAD', LEAD)] + [(f'J{i}', c) for i, c in enumerate(TRAF)] +
                        [(f'S{i}', c) for i, c in enumerate(SAFE)], 0.0, 30.0)
    print('impact world', round(T_IMP, 2), 'video', round(VI, 2), '| closing', round(V_REL, 2), 'm/s =', round(V_REL * 2.237, 1), 'mph',
          '| lead stops at', round(Z_STOP, 1), 'jam starts', round(min(c.z(0) for c in TRAF) - 2.25, 1))
    print('gap before braking', round(zl(5) - zf(5) - 4.5, 2), 'm =', round((zl(5) - zf(5) - 4.5) / V, 2), 's')
    for i, s in enumerate(video.shots):
        print(i, s.kind, s.kw.get('cam', ''), round(S[i], 2), '-', round(E[i], 2), 'world', round(VT(S[i]), 2), '-', round(VT(E[i]), 2))


if __name__ == '__main__':
    run(video, sound, verify, 'tailgate_crash.mp4')
