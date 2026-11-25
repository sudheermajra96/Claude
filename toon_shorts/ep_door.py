"""Dooring (SE Hawthorne Blvd, Portland, Oregon; cinematic square). WRONG: driver shoves the door open with the near
hand without looking -> a cyclist in the bike lane hits it and is thrown. REWIND. RIGHT: check the mirror, open with
the FAR hand (Dutch Reach: it turns your body so you look back), let the bike pass, then open slowly.
Fact: opening a vehicle door into traffic is an offence in Oregon (ORS 811.490)."""
from frustkit2 import *
from streetkit import *

T_HIT = 11.0
VB = 5.5                                              # 12 mph
Z_HIT = 0.12 - 0.9                                    # cyclist centre when the bars reach the door tip
DOOR_W = lambda t: 0.0 if t < T_HIT - 0.55 else 1.22 * smooth((t - (T_HIT - 0.55)) / 0.4)
DOOR_R = lambda t: 0.0 if t < 12.3 else (0.6 * smooth((t - 12.3) / 0.8) if t < 13.4 else 0.6 + 0.6 * smooth((t - 13.4) / 0.6))
h_occ = lambda f: occ_of('hero', f, look_fn=lambda t: 0.0)
HW = ParkedCar(X_PARK, 0.0, HERO_COL, DOOR_W, occ=occ_of('hero', lambda t: 'shock' if t > T_HIT - 0.1 else 'calm'))
HR = ParkedCar(X_PARK, 0.0, HERO_COL, DOOR_R, occ=occ_of('hero', lambda t: 'focus' if 7.5 < t < 12.5 else 'smile',
                                                          look_fn=lambda t: -2.2 * smooth((t - 9.6) / 0.6) if 9.6 < t < 12.2 else 0.0))
BS_W = spd((0, VB), (T_HIT - 0.35, VB), (T_HIT, 4.6), (T_HIT + 0.05, 0.0), (99, 0.0))
CYW = Cyclist(X_BIKE, BS_W, T_HIT, Z_HIT, top='#2f6f73', helmet='#f2a541', crash=(T_HIT, fly_default),
              expr=lambda t: 'shock' if t > T_HIT - 0.4 else 'calm')
CYR = Cyclist(X_BIKE, const(VB), T_HIT, Z_HIT, top='#2f6f73', helmet='#f2a541')
FX = CrashFX(T_HIT, lambda t: (5.85, 0.9, 0.1), steam=0.0)
NOR = [c for c in COLS if c not in (HERO_COL, '#e23b3b')]
PARKED = [ParkedCar(X_PARK, 6.6 * k, NOR[(k * 3) % len(NOR)]) for k in range(-12, 40) if k != 0 and k % 5 != 3]
PARKED_L = [Rev(-5.2, 6.6 * k + 3.0, NOR[(k * 5 + 1) % len(NOR)], v=0.0) for k in range(-12, 40) if k % 4 != 1]
LANE = [Veh(X_LANE, const(11.0), 0.0, z, NOR[i % len(NOR)]) for i, z in enumerate((40.0, 120.0, 210.0, -150.0))]
ONC_ST = [Rev(-0.5, -100 + 70 * i, NOR[(i * 4) % len(NOR)], v=11.0) for i in range(14)]
COMMON = PARKED + PARKED_L + LANE + ONC_ST
tm = TimeMap([(10.6, 13.6, 0.3)])
VH = tm.vt(T_HIT)


def door_tip_gap():
    """Bars vs door tip clearance in the right world (cyclist passes before the door opens)."""
    g = 99.0
    for t in np.arange(9.0, 16.0, 0.02):
        tip = HR.door_tip(t)
        if abs(CYR.z(t) + 0.9 - tip[2]) < 1.2 or abs(CYR.z(t) - tip[2]) < 1.0:
            g = min(g, tip[0] - (X_BIKE + 0.3))
    return round(g, 2)


shots = layout([
    (2.6, dict(kind='cine', world='w', cam='fixed', pos=(5.0, 1.1, 5.2), target_pt=(6.3, 0.9, -3.0), f=700, dt=T_HIT - 1.6, jolt=(T_HIT, 0.5),
               hook="Don't open that door!", hook_size=104)),
    (2.6, dict(kind='cine', cam='crane', target=HR, ox=-9.0, oz0=-30.0, oz1=-14.0, y0=16.0, y1=4.0, tx=-1.0, tz=0.0, f=1000,
               loc='SE Hawthorne Blvd, Portland, Oregon', cap='You just parked. Time to hop out...')),
    (2.0, dict(kind='dash_face', expr='calm', turn=0.0, cap='Busy street. Bike lane right beside you.', capsize=70)),
    (1.8, dict(kind='reach_close', world='w', mode='wrong', cap='What most people do: left hand, no look, shove.', capsize=64)),
    (1.6, dict(kind='cine', world='w', cam='track', target=CYW, off=(-2.2, 1.0, 2.5), look=(0.6, 1.0, 2.0), f=660, shake=0.05,
               cap='...right as a cyclist rides by. 12 mph.')),
    (3.0, dict(kind='cine', world='w', cam='fixed', pos=(3.6, 1.1, 3.2), target_pt=(6.6, 0.9, -1.2), f=640, jolt=(T_HIT, 0.6),
               x='DOORED. She had no time to stop.', vdelay=round(VH - 13.6 + 3.0, 2))),
    (2.6, dict(kind='cine', world='w', cam='heli', target=HW, R=13.0, H=8.0, a0=-1.2, w=0.1, f=950, oz=2.0,
               x="She's hurt. It's illegal in Oregon (ORS 811.490).")),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=16.0, H=8.0, a0=-1.0, w=0.25, f=1000, rewind=(14.5, 6.0))),
    (3.0, dict(kind='side_mirror', car=HR, dt=-8.6, step=1, ok='Check your mirror for bikes.')),
    (3.0, dict(kind='reach_close', mode='right', car=HR, dt=-7.0, step=2, ok='Use your FAR hand: the Dutch Reach.')),
    (3.0, dict(kind='cine', cam='fixed', pos=(4.2, 1.0, 6.0), target_pt=(7.0, 0.9, -3.0), f=680, dt=-11.6, step=3,
               ok='It turns you to look back. Bike passes, THEN open.')),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=-8.0, oz0=-16.0, oz1=-26.0, y0=2.0, y1=18.0, tz=30.0, f=1000, dt=-6.0,
               end_card=('Dutch Reach: far hand, look back, then open.', 'Did you know the Dutch Reach? Comment!'))),
])
DUR = shots[-1]['end']


def bell():
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.25) for f in (2100, 2900)) * 0.3


def door_creak(d=0.4):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return bp(noise(n), 400, 1600) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * tt)) * np.exp(-tt / 0.3) * 0.5


def sfx(m, S, E):
    m.add(lp(noise(int(DUR * SR)), 500), 0, 0.12)                     # city street hum
    m.add(door_creak(), 1.6 - 0.55, 0.7)
    m.add(impact(), 1.6, 0.9)
    m.add(screech(0.5, 1500), 1.25, 0.4)
    for t in (3.0, 4.2):
        m.add(car_pass(1.4, 0.5, 90), t, 0.35, pans(1.4, 0.6, -0.6))
    m.add(door_creak(), S[3] + 0.6, 0.6)
    m.add(heartbeat(3, 120), S[4] + 0.1, 0.5)
    m.add(braam(2.6, 41), S[5], 0.6)
    m.add(slow(door_creak(), 0.3), tm.vt(T_HIT - 0.55), 0.6)
    m.add(slow(impact(), 0.45), VH, 1.0)
    m.add(slow(screech(0.6, 1400), 0.3), VH - 1.0, 0.4)
    m.add(sad_violin(), S[6] + 0.3, 0.45)
    m.add(bell(), S[8] + 1.4, 0.5)
    m.add(click(), S[9] + 1.0, 0.5)
    m.add(bell(), S[10] + 1.0, 0.45)
    m.add(door_creak(), S[10] + 2.2, 0.4)


EP.extra_ground = None
story = Story('door', ['Opening your car door?', 'Watch this first'], CityStreet(far=portland_far), HW, HR,
              [CYW, FX] + COMMON, [CYR] + COMMON, shots, DUR, tm=tm, sfx=sfx)
video = story.video
if __name__ == '__main__':
    story.run(lambda: print('hit video', round(VH, 2), '| right-world door-tip clearance', door_tip_gap(),
                            '| door tip x at 70deg', round(HW.door_tip(T_HIT)[0], 2), '| right door opens when bike is',
                            round(CYR.z(12.3) - HR.z(0), 1), 'm past'))
