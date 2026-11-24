"""v2 #8 Lane closure 'line cutters' (Highway 401 Toronto). WANT: close the gap so she can't get in -> she noses in
anyway, fender-bender, BOTH lanes stop. RIGHT: it's the zipper merge - leave the gap, take turns, keep rolling."""
from frustkit2 import *

VQ, VC, SP_ = 8.0, 12.5, 20.0
T_SLOT = 15.0
Z_T = 10.0 + VQ * T_SLOT
T_HIT = 15.2
NOOR = [c for c in COLS if c != '#f2a541']


def merger(j, mine, stop_after=None):
    slot = SP_ * j + SP_ / 2
    tk = (Z_T - slot) / VQ
    sk = spd((0, VC), (tk - 2.6, VC), (tk - 1.6, VQ), (99, VQ))
    xk = lane_key((0, 3), (tk - 1.4, 3), (tk, 2), (99, 2))
    return Veh(xk, sk, tk, Z_T, '#f2a541' if mine else NOOR[(j * 7 + 4) % 9], blink=blinks((tk - 3.0, tk + 0.2, 'L')),
               mark=(lambda t: True) if mine else None, occ=occ_of('lady', lambda t: 'smile') if mine else None), tk


# ---------- right world (zipper)
HR = hero_car(const(LANES[2]), const(VQ), lambda t: 'calm' if t < 5 else ('annoyed' if t < 14 else 'smile'))
Q2 = [Veh(LANES[2], const(VQ), 0.0, SP_ * j, NOOR[(j * 3) % 9]) for j in range(-4, 12) if j != 0]
MR, MERGE_R = None, []
for j in range(-4, 11):
    c, tk = merger(j, j == 0)
    if tk < -2:
        continue
    MERGE_R.append(c)
    if j == 0:
        MR = c
SIDE = [Veh(LANES[l], const(VQ), 0.0, z + 7.0 * l, NOOR[(int(z) // 24 + l) % 9]) for l in (0, 1) for z in np.arange(-60.0, 300.0, 24.0)]
WZ = WorkZone(Z_T, 60.0, 400.0)

# ---------- wrong world: close the gap, she noses in, bump, everything stops
HSW = spd((0, VQ), (12.6, VQ), (13.4, 11.5), (14.8, 11.5), (T_HIT, 6.0), (T_HIT + 0.6, 0.0), (99, 0.0))
HW = hero_car(const(LANES[2]), HSW, lambda t: 'calm' if t < 5 else ('annoyed' if t < T_HIT - 0.2 else 'shock'), damage=[('front', T_HIT)],
              blink=lambda t: 'B' if t > T_HIT + 1.5 and (t * 1.5) % 1 < 0.5 else None)
MW = Veh(Key([(0, LANES[3]), (14.3, LANES[3]), (T_HIT, 10.62), (T_HIT + 0.5, 10.4), (99, 10.4)]),
         spd((0, VC), (11.0, VC), (12.2, VQ), (14.4, VQ), (T_HIT, 3.0), (T_HIT + 0.5, 0.0), (99, 0.0)), T_HIT, HW.z(T_HIT) + 4.0, '#f2a541',
         mark=lambda t: True, occ=occ_of('lady', lambda t: 'shock' if t > T_HIT - 0.3 else 'annoyed'), blink=blinks((11.0, 30.0, 'L')))
FX = CrashFX(T_HIT, lambda t: (9.7, 0.6, HW.z(T_HIT) + 2.1), steam=0.4)


def stopper(car_ahead_stop_z, x, z0, col, t_min):
    """Car at speed VQ that stops 2.5 m behind a stopped car (decel 3 m/s^2)."""
    target = car_ahead_stop_z - 4.5 - 2.5
    d_stop = VQ * VQ / 6.0
    ts = (target - d_stop - z0) / VQ
    ts = max(ts, t_min)
    return Veh(x, spd((0, VQ), (ts, VQ), (ts + VQ / 3.0, 0.0), (99, 0.0)), 0.0, z0, col, brake=lambda t, ts=ts: 1.0 if t > ts - 0.1 else 0.0)


Q2W, prev = [], HW.z(30.0)
for j in range(-1, -5, -1):
    c = stopper(prev, LANES[2], SP_ * j, NOOR[(j * 3) % 9], 0.0)
    Q2W.append(c)
    prev = c.z(40.0)
Q2W += [Veh(LANES[2], const(VQ), 0.0, SP_ * j, NOOR[(j * 3) % 9]) for j in range(1, 12)]
MERGE_W, prev = [], MW.z(30.0)
for j in range(1, 11):
    c, tk = merger(j, False)
    if tk > 1.0:
        MERGE_W.append(c)
for j in range(-1, -5, -1):                   # mergers behind her get stuck in the closing lane
    slot = SP_ * j + SP_ / 2
    tk = (Z_T - slot) / VQ
    col = NOOR[(j * 7 + 4) % 9]
    target = prev - 4.5 - 3.0
    c = Veh(LANES[3], spd((0, VC), (tk - 2.6 - 2.0, VC), (tk - 1.6 - 2.0, VQ), (99, VQ)), 0.0, 0.0, col)
    z_rel = c.z(30.0) - c.z(0.0)
    t_stop_guess = 0.0
    # simple: place it so it stops at `target` with a VC->0 profile when it reaches it
    sk = spd((0, VC), (T_HIT + 1.0 + (-j) * 1.2, VC), (T_HIT + 1.0 + (-j) * 1.2 + VC / 4.0, 0.0), (99, 0.0))
    c = Veh(LANES[3], sk, 40.0, target, col, blink=blinks((T_HIT + 1.0, 60.0, 'L')))
    MERGE_W.append(c)
    prev = target
SIDEW = SIDE
tm = TimeMap([(10.0, 12.6, 0.3), (16.6, 19.6, 0.4)])
VH = tm.vt(T_HIT)

shots = layout([
    (2.4, dict(kind='cine', world='w', cam='heli', target=HW, R=26.0, H=16.0, a0=-0.5, w=0.1, f=1000, oz=10.0, dt=T_HIT + 1.0,
               hook='Block the "cheaters"?!')),
    (2.6, dict(kind='cine', cam='heli', target=HR, R=24.0, H=10.0, a0=0.6, w=-0.12, f=1000, oz=8.0, loc='Highway 401, Toronto, Ontario',
               cap='Right lane closed. You lined up early...')),
    (3.0, dict(kind='cine', cam='track', target=HR, off=(0.3, 2.7, -9.0), look=(2.6, 0.9, 16.0), f=740, shake=0.05, flare=0.4,
               cap='...and they drive right past you to the end.', capsize=68)),
    (2.0, dict(kind='dash_face', expr='annoyed', turn=0.4, cap='Cheaters!')),
    (1.3, dict(kind='dash_face', world='w', expr='annoyed', turn=0.0, cap='What you WANT to do...')),
    (1.3, dict(kind='pedal_close', world='w', act='gas', hit=0.4, word='CLOSE THE GAP!')),
    (4.0, dict(kind='cine', world='w', cam='top', center=lambda t: (9.5, HW.z(t) + 6.0), H=34.0, f=1000,
               cap='No gap. Nobody gets in!')),
    (3.0, dict(kind='cine', world='w', cam='track', target=HW, off=(-2.4, 1.3, 2.5), look=(1.6, 0.8, 4.0), f=640, shake=0.03, jolt=(T_HIT, 0.3),
               x='She noses in anyway. Crunch.', vdelay=round(VH - 16.6, 2))),
    (2.6, dict(kind='cine', world='w', cam='heli', target=HW, R=34.0, H=20.0, a0=-0.4, w=0.06, f=1000, oz=-10.0,
               x='Fender-bender. Now BOTH lanes are stuck.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=24.0, H=12.0, a0=-0.5, w=0.2, f=1000, rewind=(17.5, 9.0))),
    (3.0, dict(kind='cine', cam='top', center=(9.5, Z_T - 15.0), H=48.0, f=1000, dt=-7.5, step=1,
               ok="It's the ZIPPER merge. They're not cheating.")),
    (3.0, dict(kind='interior_mirror', f=900, mirror=False, dt=-7.0, step=2, ok='Leave the gap. Let ONE car in.')),
    (2.6, dict(kind='cine', cam='heli', target=HR, R=24.0, H=12.0, a0=-0.4, w=0.08, f=1000, oz=12.0, dt=-6.0, step=3,
               ok='Take turns. Everyone keeps rolling.')),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=60.0, f=1000, dt=-6.0,
               end_card=('Lane closed? Zipper merge. Take turns.', 'Do you let them in? Comment YES or NO!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(lp(noise(int(DUR * SR)), 300), 0, 0.15)
    for t in np.arange(0.0, DUR, 0.62):
        m.add(click(), t, 0.05)
    m.add(impact(), 0.3, 0.5)
    m.add(horn(0.8), 0.6, 0.6)
    m.add(horn(0.5), S[3] + 0.5, 0.4)
    m.add(v8(1.3, lambda u: 0.7), S[5] + 0.3, 0.5)
    for k in (0.6, 1.4, 2.4, 3.2):
        m.add(horn(0.4), S[6] + k, 0.4, 0.4)
    m.add(braam(2.6, 41), S[7], 0.5)
    m.add(slow(impact(), 0.5), VH, 0.8)
    for k in (0.4, 0.9, 1.3, 1.8):
        m.add(horn(0.6), S[8] + k, 0.45, -0.5 + 0.3 * k)
    m.add(sad_trombone(), S[8] + 0.8, 0.4)
    indicator(m, S[11] + 0.2, E[11], 0.35, 0.3)


story = Story('g08_zipper', ['Cars "cutting in" at a lane closure?', 'Block them? Watch this'], city_401((Z_T + 600.0, Z_T + 1500.0)), HW, HR,
              [WZ, MW, FX] + MERGE_W + Q2W + SIDEW + oncoming(), [WZ, MR] + [m for m in MERGE_R if m is not MR] + Q2 + SIDE + oncoming(),
              shots, DUR, tm=tm, sfx=sfx, unit='kmh')
video = story.video
if __name__ == '__main__':
    story.run(lambda: print('hit video', round(VH, 2), '| bump', lateral_gap(HW, MW, 13, 17), '| gap ahead min',
                            round(min(Q2W[4].z(t) - 4.5 - HW.z(t) for t in np.arange(10, 20, 0.05)), 2)))
