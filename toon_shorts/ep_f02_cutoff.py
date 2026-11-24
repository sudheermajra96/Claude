"""Frustrated #2: cut off without a signal (I-35E Dallas). Right way: ease off, rebuild the gap, let it go - don't chase."""
from frustkit import *

T_C0, T_C1 = 7.0, 7.7
HS = spd((0, V), (7.3, V), (8.4, V - 6.0), (12.0, V - 6.0), (13.6, V), (99, V))


def hero_expr(t):
    return 'calm' if t < 7.0 else ('shock' if t < 8.6 else ('annoyed' if t < 12.0 else ('focus' if t < 16.5 else 'smile')))


HERO = hero_car(const(LANES[1]), HS, hero_expr)
CX = lane_key((0, 2), (T_C0, 2), (T_C1, 1), (99, 1))
CUT = Veh(CX, const(33.0), T_C1, HERO.z(T_C1) + 4.5 + 4.0, '#e8e8ee', occ=occ_of('husb', lambda t: 'smug'), mark=lambda t: True)
TRAF = filler([(0, 30), (0, -60), (3, 25), (3, -40), (2, 120), (0, 150), (3, 180), (2, -200)])
FOL = Veh(LANES[1], HS, 0.0, -48.0, COLS[5])
AG = [CUT, FOL] + TRAF + oncoming()


def gap_s(lt, i=5):
    t = EP.tm.wt(ep.video.S[i] + lt)
    return (CUT.z(t) - 2.25 - HERO.z(t) - 2.25) / max(1.0, HERO.speed(t))


defs = [
    (3.0, 'cine', dict(cam='track', target=HERO, off=(-3.8, 1.3, -3.0), look=(0, 0.9, 9.0), f=720, dt=5.9, shake=0.1, jolt=(7.4, 0.3))),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=22.0, H=9.0, a0=-2.4, w=0.2, f=1000, oz=2.0)),
    (9.0, 'cine', dict(cam='track', target=HERO, off=(-3.4, 1.0, -1.0), look=(1.0, 0.9, 9.0), f=700, shake=0.08, flare=0.4)),
    (11.5, 'dash_face', dict(expr=lambda lt: 'annoyed', turn=lambda lt: 0.2 * math.sin(lt * 2))),
    (14.0, 'interior_mirror', dict(mirror=True)),
    (16.5, 'cine', dict(cam='heli', target=HERO, R=24.0, H=12.0, a0=-2.8, w=0.08, f=1000, oz=12.0)),
    (19.0, 'cine', dict(cam='tele', target=HERO, off=(9.0, 3.0, 60.0), tz=10.0, f=2300)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
texts = dict(hook='No signal. 4 metres.', loc='I-35E, Dallas, Texas',
             c=[None, 'Easy drive into downtown...', 'He cuts in. No signal. Inches away.', 'Honk? Chase him? Teach him a lesson?',
                ('Ease off the gas. Brake gently.', 76), 'Rebuild your 3-second gap', ('Let it go. He saves 2 seconds. You keep your day.', 64), None],
             steps={4: 1, 5: 2, 6: 3}, end=('Cut off? Back off. Let it go.', 'Do you get angry when cut off? Comment!'))


def sfx(m, S, E):
    m.add(v8(2.0, lambda u: 0.9), 0.0, 0.5)
    m.add(car_pass(1.2, 0.5, 120), 0.6, 0.7, pans(1.2, 0.6, -0.4))
    m.add(brake_squeal(1.0), 1.5, 0.5)
    m.add(horn(0.6), 1.7, 0.6)
    m.add(v8(2.5, lambda u: 0.9), S[2] + 0.3, 0.45)
    m.add(car_pass(1.2, 0.5, 120), T_C0 - 0.4, 0.7, pans(1.2, 0.6, -0.3))
    m.add(brake_squeal(1.0), 7.4, 0.5)
    m.add(chime(), S[6] + 1.0, 0.5)


ep = Episode('f02_cutoff', ['Someone cuts you off?', "Here's the smart move"], city_dallas((620.0, 1500.0)), HERO, AG, defs, texts, 22.0, sfx=sfx,
             extra_overlays=[(14.0, 16.5, value_tag(lambda lt: gap_s(lt), 'GAP', 's', 3.0, 1.5, x=1600, y=1560))])
video = ep.video
if __name__ == '__main__':
    ep.run()
