"""MINIMAL STARTER (copy this for a new video): 10 s simple drive into a city, built only from cinetemplate.py.

Edit: traffic plan, Highway(...) dressing, defs (camera shots), overlays, sound().  Render:
  python3 ep_sample_city.py <out.mp4>        (check: <out.png> check | numbers: x verify)
"""
from cinetemplate import *

HERO = Veh(LANES[1], const(V), 0.0, 0.0, '#e23b3b', occ=occ_of('hero', lambda t: 'smile'))
TRAF = [Veh(LANES[i % 4], const(V + (i % 3) - 1), 0.0, z, COLS[i % 10]) for i, z in
        enumerate((-40, 35, 70, 110, -75, 150, 190, 230))]
TRAF = [c for c in TRAF if not (c.xk(0) == LANES[1] and abs(c.z(0)) < 30)]
ONC = [Rev(-5.0 if i % 2 else -11.0, -200 + 47 * i, COLS[(i * 3) % 10]) for i in range(30)]
EP.hero = HERO
EP.shadows = [HERO] + TRAF + ONC


def far(ctx, view):
    city_skyline(ctx, view, Z=1600.0, xc=40.0, n=26, seed=11, base='#6f7690', hmin=70, hmax=230)


CITY = Highway(sky=('#3d6fb4', '#ffcf9a'), far=far, seed=2,
               gantries=[(420.0, [(1.0, 8.0, 'I-35E SOUTH', 'Downtown Dallas'), (9.5, 16.5, 'EXIT 429', 'Main St')])])
world = make_world(CITY, HERO, TRAF + ONC)

DUR = 10.0
defs = [
    (3.0, 'cine', dict(cam='heli', target=HERO, R=24.0, H=10.0, a0=-2.4, w=0.2, f=1000, oz=4.0)),
    (5.5, 'cine', dict(cam='track', target=HERO, off=(-3.2, 0.9, 6.0), look=(0, 0.9, -2.0), f=760, streak=0.6)),
    (7.8, 'interior_mirror', dict(mirror=False)),
    (DUR, 'cine', dict(cam='crane', target=HERO, ox=5.0, oz0=-25.0, oz1=-35.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
video = make_video(['A calm drive into the city', 'Road Rules Animated'], world, defs, DUR)
S, E = video.S, video.E
video.overlays = [
    (0.2, 3.0, location_tag('I-35E, Dallas, Texas')),
    (S[1] + 0.2, E[1], sq_caption('Easy speed. Safe gap. No stress.')),
    (S[2] + 0.2, E[2], sq_caption('Eyes up, hands on the wheel')),
    (S[3] + 0.3, E[3], end_card('Drive calm, arrive calm.', 'Where do you drive every day? Comment!')),
]


def sound():
    m = Mixer(DUR)
    highway_bed(m, DUR)
    m.add(car_pass(1.4, 0.5, 100), 1.0, 0.6, pans(1.4, -0.6, 0.6))
    m.add(car_pass(1.4, 0.5, 110), 4.2, 0.6, pans(1.4, 0.6, -0.6))
    m.add(whoosh(0.5, 0.4), S[3] - 0.1, 0.4)
    m.add(success_jingle(), S[3] + 0.3, 0.7)
    return m.out(DUR)


def verify():
    verify_gaps([('HERO', HERO)] + [(f'T{i}', c) for i, c in enumerate(TRAF)], 0.0, DUR)


if __name__ == '__main__':
    run(video, sound, verify, 'sample_city.mp4')
