"""Frustrated #3: you signal to pass a slow truck and the driver beside you speeds up to block you (I-35E Dallas).
Right way: don't force it, ease off and let him go, then merge into the gap behind him."""
from frustkit import *

VS = 25.0                                   # slow truck speed (56 mph)
T_SIG, T_LC0, T_LC1 = 6.4, 16.8, 18.2
HS = spd((0, VS), (18.0, VS), (20.0, V), (99, V))
HX = lane_key((0, 2), (T_LC0, 2), (T_LC1, 1), (99, 1))


def hero_expr(t):
    return 'calm' if t < 7.4 else ('annoyed' if t < 12.5 else ('focus' if t < 17.0 else 'smile'))


HERO = hero_car(HX, HS, hero_expr, blink=blinks((T_SIG, 11.8, 'L'), (16.2, T_LC1 + 0.3, 'L')))
SEMI = Veh(LANES[2], const(VS), 0.0, HERO.z(0) + 2.25 + 30.0 + 15.5, '#2f6f9f', kind='semi',
           trailer=('#f4f4f6', '#e0393e', 'LONE STAR'), cab='#c0392b')
BS = spd((0, VS), (T_SIG, VS), (7.3, 29.0), (8.6, VS), (12.6, VS), (13.8, 34.0), (99, 34.0))
BLK = Veh(LANES[1], BS, 6.0, HERO.z(6.0) - 9.0, '#f2a541', occ=occ_of('husb', lambda t: 'smug'), mark=lambda t: True)
TRAF = filler([(0, 30), (0, -40), (0, 110), (3, 15), (3, -60), (3, 90), (3, -150), (0, 200)], speed=V, cols=[c for c in COLS if c != '#f2a541'])
AG = [SEMI, BLK] + TRAF + oncoming()

defs = [
    (3.0, 'cine', dict(cam='heli', target=HERO, R=16.0, H=8.0, a0=-2.2, w=0.18, f=950, oz=1.0, dt=7.0)),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=24.0, H=10.0, a0=2.4, w=-0.18, f=1000, oz=8.0)),
    (9.0, 'cine', dict(cam='track', target=HERO, off=(1.6, 1.4, -9.0), look=(-1.6, 0.9, 6.0), f=700, shake=0.07)),
    (11.5, 'dash_face', dict(expr='annoyed', turn=lambda lt: -0.5 * smooth(lt / 0.6))),
    (14.0, 'interior_mirror', dict(blink=True)),
    (16.5, 'cine', dict(cam='heli', target=HERO, R=22.0, H=11.0, a0=-2.6, w=0.1, f=1000, oz=6.0)),
    (19.0, 'cine', dict(cam='tele', target=HERO, off=(9.5, 3.5, -55.0), tz=6.0, f=2300)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
texts = dict(hook='He speeds up. On purpose.', hook_size=104, loc='I-35E, Dallas, Texas',
             c=[None, 'Stuck behind a slow truck...', 'You signal left. He speeds up to block you.', 'He matches your speed. Again.',
                ("Don't force it. Stay in your lane.", 74), 'Ease off. Let him go.', 'Merge into the gap behind him', None],
             steps={4: 1, 5: 2, 6: 3}, end=("Blocked? Don't fight it. Merge behind.", 'Has someone done this to you? Comment!'))


def sfx(m, S, E):
    m.add(lp(noise(int(22 * SR)), 140), 0, 0.25)                       # truck rumble
    indicator(m, T_SIG, 11.8, 0.4, -0.2)
    m.add(click(), T_SIG, 0.6)
    m.add(v8(2.0, lambda u: 0.8 + 0.2 * min(1, u)), 0.0, 0.4)
    m.add(v8(2.0, lambda u: 0.6 + 0.4 * min(1, u / 0.8)), 6.6, 0.5)
    m.add(horn(0.5), S[3] + 0.4, 0.4)
    m.add(v8(2.0, lambda u: 0.6 + 0.4 * min(1, u / 0.6)), 12.6, 0.6)
    m.add(car_pass(1.3, 0.5, 120), 13.2, 0.6, pans(1.3, -0.6, 0.6))
    indicator(m, 16.2, T_LC1 + 0.3, 0.4, -0.2)
    m.add(chime(), S[6] + 1.6, 0.5)


ep = Episode('f03_blocker', ['Someone blocks your lane change?', "Don't take the bait"], city_dallas((900.0, 1700.0)), HERO, AG, defs, texts,
             22.0, sfx=sfx)
video = ep.video
if __name__ == '__main__':
    ep.run()
