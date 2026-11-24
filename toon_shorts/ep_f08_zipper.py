"""Frustrated #8: right lane closed for construction - cars drive up the closing lane and merge at the end, and you
feel they are cutting in line (Highway 401, Toronto). Right way: that IS the zipper merge - take turns, leave the gap."""
from frustkit import *

EP.unit = 'kmh'
VQ, VC = 8.0, 12.5                  # queue 29 km/h, closing lane 45 km/h
SP_ = 20.0                          # lane-2 car spacing (centre to centre)
Z_T = 10.0 + VQ * 17.5              # taper end: the slot in front of our hero merges at t = 17.5


def hero_expr(t):
    return 'calm' if t < 5.5 else ('annoyed' if t < 12.5 else ('focus' if t < 16.5 else 'smile'))


HERO = hero_car(const(LANES[2]), const(VQ), hero_expr)
NOOR = [c for c in COLS if c != '#f2a541']
Q2 = [Veh(LANES[2], const(VQ), 0.0, SP_ * j, NOOR[(j * 3) % 9]) for j in range(-4, 12) if j != 0]
MERGE, MK = [], None
for j in range(-4, 11):
    slot = SP_ * j + SP_ / 2
    tk = (Z_T - slot) / VQ
    if tk < -2:
        continue
    sk = spd((0, VC), (tk - 2.6, VC), (tk - 1.6, VQ), (99, VQ))
    xk = lane_key((0, 3), (tk - 1.4, 3), (tk, 2), (99, 2))
    mine = j == 0
    c = Veh(xk, sk, tk, Z_T, '#f2a541' if mine else NOOR[(j * 7 + 4) % 9], blink=blinks((tk - 3.0, tk + 0.2, 'L')),
            mark=(lambda t: True) if mine else None, occ=occ_of('lady', lambda t: 'smile') if mine else None)
    MERGE.append(c)
    if mine:
        MK = c
SIDE = [Veh(LANES[l], const(VQ), 0.0, z + 7.0 * l, NOOR[(int(z) // 24 + l) % 9]) for l in (0, 1) for z in np.arange(-60.0, 300.0, 24.0)]
WZ = WorkZone(Z_T, 60.0, 400.0)
AG = [WZ, MK] + [m for m in MERGE if m is not MK] + Q2 + SIDE + oncoming()


def lc_check():
    print('Z_T', round(Z_T, 1), '| my merger at taper t', round((Z_T - SP_ / 2) / VQ, 2), '| merge cars', len(MERGE))


defs = [
    (3.0, 'cine', dict(cam='heli', target=HERO, R=30.0, H=18.0, a0=-0.5, w=0.1, f=1000, oz=14.0, dt=14.5)),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=24.0, H=10.0, a0=0.6, w=-0.12, f=1000, oz=8.0)),
    (9.0, 'cine', dict(cam='track', target=HERO, off=(0.3, 2.7, -9.0), look=(2.6, 0.9, 16.0), f=740, shake=0.05, flare=0.4)),
    (11.5, 'dash_face', dict(expr='annoyed', turn=lambda lt: 0.4)),
    (14.0, 'cine', dict(cam='top', center=(9.5, Z_T - 15.0), H=48.0, f=1000)),
    (16.5, 'cine', dict(cam='heli', target=HERO, R=26.0, H=14.0, a0=-0.4, w=0.08, f=1000, oz=12.0)),
    (19.0, 'interior_mirror', dict(f=900)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=60.0, f=1000)),
]
texts = dict(hook='They ALL cut in line?!', loc='Highway 401, Toronto, Ontario',
             c=[None, 'Right lane closed. You line up early...', '...and they drive right past you to the end.', 'Cheaters! Block them!',
                ("They're not cheating: it's the ZIPPER merge", 66), 'Use both lanes to the end. Then take turns.', 'Leave the gap. Let ONE in. Keep rolling.', None],
             steps={4: 1, 5: 2, 6: 3}, end=('Lane closed? Zipper merge. Take turns.', 'Do you let them in? Comment YES or NO!'))


def sfx(m, S, E):
    m.add(lp(noise(int(22 * SR)), 300), 0, 0.15)
    for t in np.arange(0.0, 22.0, 0.62):
        m.add(click(), t, 0.05)                       # arrow board ticking
    m.add(horn(0.5), S[2] + 1.2, 0.5)
    m.add(horn(0.3), S[3] + 0.5, 0.4)
    indicator(m, 14.5, 17.7, 0.35, 0.3)
    m.add(chime(), S[6] + 1.5, 0.5)


ep = Episode('f08_zipper', ['Cars "cutting in" at a lane closure?', "Here's the truth"], city_401((Z_T + 600.0, Z_T + 1500.0)), HERO, AG,
             defs, texts, 22.0, sfx=sfx)
video = ep.video
if __name__ == '__main__':
    ep.run(lc_check)
