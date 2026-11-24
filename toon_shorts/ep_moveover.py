"""Move Over law (cinematic, SQUARE 1:1, emotional). I-70 at Golden, Colorado, golden hour, Rockies ahead.

A state trooper is writing a ticket at the driver's window of a car pulled over on the right shoulder: he stands
~0.7 m from the lane line.  Wrong way: a driver stays in the right lane at 70 mph and passes ~1 m from him
(slow motion).  Right way (our hero): sees the lights early, checks the mirror, signals, moves over a full lane and
slows down; the trooper gives a thumbs up.  Step 3: a driver who CAN'T move over (semi beside her) slows right down.
Fact: every US state has a Move Over law (police, fire, EMS, tow trucks; many states also cover any stopped vehicle
with hazards).  Built on cinetemplate.py.
"""
from cinetemplate import *

T_B = 8.0                       # world time the careless driver passes the trooper
T_SIG, T_LC0, T_LC1 = 11.3, 12.0, 13.4
T_HP = 17.0                     # hero passes the trooper (solved below)
T_C = 20.4                      # step-3 car passes the trooper
EP.tm = TimeMap([(7.6, 10.6, 0.35)])


def hazard(t):
    return 'B' if (t * 1.5) % 1 < 0.5 else None


# hero: lane 4 -> lane 3, slows to 52 mph past the scene
HS = Key([(0, V), (12.6, V), (14.0, V - 6.0), (18.6, V - 6.0), (20.4, V), (99, V)], 'lin')
HX = Key([(0, LANES[3]), (T_LC0, LANES[3]), (T_LC1, LANES[2]), (99, LANES[2])])
HERO = Veh(HX, HS, 0.0, 0.0, '#e23b3b', occ=occ_of('hero', lambda t: 'focus' if 10.5 < t < 18 else 'calm'),
           blink=blink_side([(T_SIG, T_LC1 + 0.3)], 'R'))
ZS = HERO.z(T_HP)               # the trooper stands here
OFF_X = 14.7

STOP = Veh(16.1, const(0.0), 0.0, ZS - 0.6, '#d8c3a0', blink=hazard, brake=lambda t: 1.0,
           occ=occ_of('grandpa', lambda t: 'worried', look_fn=lambda t: -0.9))
PCAR = Veh(16.1, const(0.0), 0.0, ZS - 9.6, '#f4f4f6', police=lambda t: True, brake=lambda t: 0.0)

# careless driver: right lane, 31 m/s (69 mph), never moves over
B = Veh(LANES[3], const(31.0), T_B, ZS, '#6b6f7a', occ=occ_of('husb', lambda t: 'calm'))


def lean(t):
    u = t - (T_B - 0.05)
    return 0.16 * math.exp(-u * 2.2) * math.sin(min(u, 0.25) / 0.25 * math.pi / 2) if u > 0 else 0.0


def off_pose(t):
    if t > T_HP + 0.4 and t < T_HP + 7.0:
        return 'thumbs', t - T_HP - 0.4
    if t > 22.5:
        return 'thumbs', t - 22.5
    return 'write', t % 3


def off_expr(t):
    if T_HP + 0.4 < t < T_HP + 7.0 or t > 22.5:
        return 'smile'
    return 'flat'


TROOPER = Trooper(OFF_X, ZS + 0.9, off_pose, lean, off_expr)

# step 3: she can't move over (semi alongside) -> slows to 34 mph past the scene
CS = Key([(0, V), (17.4, V), (19.4, 15.0), (21.6, 15.0), (23.6, V), (99, V)], 'lin')
C = Veh(LANES[3], CS, T_C, ZS, '#3a7bd5', occ=occ_of('lady', lambda t: 'focus'))
SEMI = Veh(LANES[2], CS, T_C, ZS + 3.5, '#2f6f9f', kind='semi', trailer=('#f4f4f6', '#2f6f9f', 'ROCKY MTN FREIGHT'), cab='#c0392b')

TRAF = []


def car(lane, speed, ta, za, col):
    v = Veh(LANES[lane], speed, ta, za, col)
    TRAF.append(v)
    return v


# traffic: left lanes flow; lane 3 ahead of the hero is clear for the lane change; the car behind the hero follows him
car(1, HS, 0.0, -12.0, COLS[0])
car(0, const(V + 1), 0.0, 30.0, COLS[3])
car(1, const(V), 0.0, 60.0, COLS[5])
car(2, HS, 0.0, -42.0, COLS[6])
car(0, const(V + 1), 0.0, -70.0, COLS[7])
car(2, const(V), 0.0, 210.0, COLS[1])
car(1, const(V), 0.0, 170.0, COLS[9])
car(0, const(V), 0.0, 120.0, COLS[4])
for i in range(5):
    car([0, 1, 2, 0, 1][i], const(V), 0.0, 300.0 + 34 * i, COLS[(i + 2) % 10])
# traffic behind the step-3 pair (all slow with them)
car(1, CS, T_C, ZS - 18.0, COLS[8])
car(0, Key([(0, V), (17.6, V), (19.6, 20.0), (21.6, 20.0), (23.6, V), (99, V)], 'lin'), T_C, ZS - 40.0, COLS[2])

ONC = [Rev(-5.0 if i % 2 else -11.0, -200 + 47 * i, COLS[(i * 3) % 10]) for i in range(40)]
EP.hero = HERO
EP.shadows = [HERO, B, STOP, PCAR, C, SEMI] + TRAF + ONC


def far(ctx, view):
    mountains(ctx, view, Z=ZS + 3400, col='#6c7895', hmax=620, seed=8)
    city_skyline(ctx, view, Z=ZS + 2500, xc=-600, n=6, seed=4, base='#8a7f93', hmin=30, hmax=60)


CITY = Highway(sky=('#3d6fb4', '#ffcf9a'), grass='#a9a565', hills='#8a8a5a', far=far, roadside='pines', seed=7,
               gantries=[(ZS - 520, [(1.0, 8.0, 'I-70 WEST', 'Mountain Resorts'), (9.5, 16.5, 'EXIT 263', 'Golden')]),
                         (ZS + 700, [(1.0, 8.0, 'I-70 WEST', 'Idaho Springs'), (9.5, 16.5, 'EXIT 260', 'C-470')])])
world = make_world(CITY, HERO, [B, STOP, PCAR, TROOPER, C, SEMI] + TRAF + ONC)


# ------------------------------------------------------------------ shots (video time; world = EP.tm.wt)
def lesson(ctx, view, t, lt):
    """Top view: red danger lane next to the scene, green 'moved over' lane."""
    a = smooth(lt / 0.5)
    for x0, x1, col in ((10.5, 14.0, '#ff4b4b'), (7.0, 10.5, '#22c35e')):
        pts = [view.pt((x0, 0.02, ZS - 70)), view.pt((x1, 0.02, ZS - 70)), view.pt((x1, 0.02, ZS + 20)), view.pt((x0, 0.02, ZS + 20))]
        if all(pts):
            poly(ctx, pts)
            setc(ctx, hexc(col), 0.33 * a)
            ctx.fill()


DUR = 34.0
VT = EP.tm.wt
defs = [
    (3.0, 'cine', dict(cam='fixed', pos=(17.4, 2.1, ZS + 15.0), target_pt=(13.6, 1.3, ZS - 6.0), f=900, dt=6.6, jolt=(T_B, 0.35))),
    (6.0, 'cine', dict(cam='heli', target=STOP, R=30.0, H=13.0, a0=-2.3, w=0.16, f=1000, oz=-4.0)),
    (7.6, 'cine', dict(cam='track', target=B, off=(-2.6, 1.1, -8.5), look=(0, 0.9, 6.0), f=760, shake=0.08, streak=0.5)),
    (10.6, 'cine', dict(cam='fixed', pos=(15.5, 1.55, ZS + 7.5), target_pt=(13.4, 1.25, ZS - 10.0), f=760, jolt=(T_B, 0.25))),
    (13.0, 'cine', dict(cam='fixed', pos=(15.6, 1.55, ZS + 5.0), target_pt=(14.6, 1.35, ZS + 0.9), f=640)),
    (15.6, 'interior_mirror', dict(blink=True, mirror_glow=lambda t: t < 11.9)),
    (18.0, 'cine', dict(cam='heli', target=HERO, R=26.0, H=12.0, a0=0.9, w=-0.12, f=1000, oz=4.0)),
    (20.6, 'cine', dict(cam='fixed', pos=(16.4, 1.4, ZS + 12.0), target_pt=(12.0, 1.2, ZS - 8.0), f=820)),
    (23.6, 'cine', dict(cam='tele', target=C, off=(17.5, 3.0, 48.0), tx=0.5, tz=-2.0, f=2400)),
    (26.6, 'cine', dict(cam='top', center=(9.0, ZS - 14.0), H=60.0, f=1000, post=lesson)),
    (30.0, 'cine', dict(cam='fixed', pos=(15.3, 1.6, ZS + 4.2), target_pt=(14.6, 1.4, ZS + 0.9), f=560)),
    (DUR, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-28.0, oz1=-40.0, y0=2.0, y1=24.0, tx=0.0, tz=200.0, f=1000)),
]
video = make_video(['Lights on the shoulder?', 'Move over. Here\'s why.'], world, defs, DUR)
S, E = video.S, video.E


B_GAP = lateral_gap(B, TROOPER, 0, 30)[0]
H_GAP = lateral_gap(HERO, TROOPER, 0, 30)[0]
C_GAP = lateral_gap(C, TROOPER, 0, 30)[0]


def show_after(t_world, val):
    """Meter value that appears once the car reaches the trooper (lt -> value or None)."""
    def f(shot_i):
        dt = video.shots[shot_i].kw.get('dt', 0.0)

        def g(lt):
            return val if VT(S[shot_i] + lt) + dt > t_world - 0.15 else None
        return g
    return f


def c_speed(lt):
    return C.speed(VT(S[8] + lt)) * 2.237


video.overlays = [
    (0.0, 3.0, big_text('Would YOU move over?', 300, 116, hexc('#ffd23f'), 0.15, True)),
    (0.0, 3.0, value_tag(show_after(T_B, B_GAP)(0), 'SPACE', 'm', 3.0, 1.5, x=1600, y=1560)),
    (3.0, 6.0, location_tag('I-70, Golden, Colorado')),
    (3.2, 6.0, sq_caption('A trooper stops a driver on the shoulder', 76)),
    (S[2] + 0.1, E[2], sq_caption('This driver sees the lights... and stays put', 72)),
    (S[3], E[3], slowmo_tag),
    (S[3], E[3], value_tag(show_after(T_B, B_GAP)(3), 'SPACE', 'm', 3.0, 1.5, x=1600, y=1560)),
    (S[3] + 0.3, E[3], sq_caption(f'{B_GAP:.1f} metres. At 70 mph.')),
    (vt_x := EP.tm.vt(T_B) + 0.1, E[3], x_mark),
    (S[4] + 0.2, E[4], sq_caption('Every year, roadside workers are hit and killed', 70)),
    (S[5], E[5], step_badge(1)),
    (S[5] + 0.15, E[5], sq_caption('See lights ahead? Check your mirror. Signal.', 70)),
    (S[6], E[6], step_badge(2)),
    (S[6] + 0.15, E[6], sq_caption('Move over a full lane and slow down', 76)),
    (S[7] + 0.2, E[7], value_tag(show_after(T_HP, H_GAP)(7), 'SPACE', 'm', 3.0, 1.5, x=1600, y=1560)),
    (EP.tm.vt(T_HP) + 0.3, E[7], check_mark),
    (S[7] + 0.2, E[7], sq_caption(f'{H_GAP:.1f} metres of space. He feels it.', 74)),
    (S[8], E[8], step_badge(3)),
    (S[8] + 0.15, E[8], sq_caption("Can't move over? SLOW DOWN well below the limit", 64)),
    (S[8] + 0.3, E[8], value_tag(c_speed, 'HER SPEED', 'mph', 40, 60, x=1600, y=1560, fmt='{:.0f}', higher_is_good=False)),
    (S[9], E[9], badge('MOVE OVER LAW', '#e0393e')),
    (S[9] + 0.2, E[9], sq_caption('All 50 US states: police, fire, EMS, tow trucks', 66)),
    (S[10] + 0.3, E[10], sq_caption('Move over... so he gets home tonight.', 76)),
    (S[11] + 0.2, E[11], end_card('Move over. Slow down. Everyone gets home.', 'Did you know this was the law? Comment YES or NO')),
]


# ------------------------------------------------------------------ sound
def wind_gust(d=1.4):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return bp(noise(n), 200, 1600) * np.exp(-((tt - 0.35) / 0.25) ** 2) * 0.9


def sound():
    m = Mixer(DUR)
    highway_bed(m, DUR)
    vb = EP.tm.vt(T_B)
    # hook: car blasts past the trooper (world 8.0 at video 1.4)
    m.add(braam(2.2, 46), 0.05, 0.8)
    m.add(heartbeat(3, 115), 0.1, 0.7)
    m.add(car_pass(1.4, 0.5, 120), 1.4 - 0.7, 1.0, pans(1.4, 0.7, -0.7))
    m.add(wind_gust(), 1.4 - 0.2, 0.7)
    # police lights tick (subtle) in the scene shots
    for t0, t1 in ((3.0, 6.0), (S[4], E[4]), (S[10], E[10])):
        for k in np.arange(t0, t1, 0.38):
            m.add(click(), k, 0.08)
    # wrong way, slow-mo pass
    m.add(v8(1.6, lambda u: 0.75), S[2], 0.35)
    m.add(braam(2.6, 41), S[3], 0.6)
    m.add(slow(car_pass(1.4, 0.5, 120), 0.35), vb - 1.3, 1.0)
    m.add(slow(wind_gust(), 0.35), vb - 0.4, 0.8)
    m.add(slow(heartbeat(3, 120), 0.35), S[3] + 0.1, 0.7)
    m.add(impact(), vt_x, 0.35)
    m.add(sad_violin(), S[4] + 0.2, 0.45)
    # right way
    m.add(click(), EP.tm.vt(T_SIG), 0.7)
    indicator(m, EP.tm.vt(T_SIG), EP.tm.vt(T_LC1 + 0.3), 0.45, 0.2)
    m.add(car_pass(2.0, 0.5, 90), EP.tm.vt(T_HP) - 1.0, 0.55, pans(2.0, 0.5, -0.5))
    m.add(chime(), EP.tm.vt(T_HP) + 0.3, 0.6)
    # step 3: slow truck + car
    m.add(lp(noise(int(3 * SR)), 160), S[8], 0.5)
    m.add(air_horn(0.5), S[8] + 2.2, 0.0)
    for i in (5, 6, 8):
        m.add(pop(), S[i] + 0.15, 0.6)
    m.add(whoosh(0.5, 0.4), S[9] - 0.1, 0.5)
    m.add(chime(), S[10] + 0.6, 0.45)
    m.add(success_jingle(), S[11] + 0.3, 0.8)
    return m.out(DUR)


# ------------------------------------------------------------------ checks
def verify():
    agents = [('HERO', HERO), ('B', B), ('STOP', STOP), ('PCAR', PCAR), ('C', C), ('SEMI', SEMI), ('TROOPER', TROOPER)] + \
             [(f'T{i}', c) for i, c in enumerate(TRAF)]
    verify_gaps(agents, 0.0, 32.0)
    print('ZS', round(ZS, 1), '| trooper lateral gaps: B', B_GAP, 'hero', H_GAP, 'C', C_GAP)
    print('hero passes at world', lateral_gap(HERO, TROOPER, 0, 30)[1], 'video', round(EP.tm.vt(T_HP), 2),
          '| B passes video', round(EP.tm.vt(T_B), 2), '| C passes video', round(EP.tm.vt(T_C), 2), 'C mph', round(CS(T_C) * 2.237))
    for i, s in enumerate(video.shots):
        print(i, s.kind, s.kw.get('cam', ''), 'video', round(S[i], 2), '-', round(E[i], 2), 'world', round(VT(S[i]), 2), '-', round(VT(E[i]), 2))


if __name__ == '__main__':
    run(video, sound, verify, 'moveover.mp4')
