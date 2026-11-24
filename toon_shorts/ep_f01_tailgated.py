"""Frustrated #1: tailgated with flashing high beams (I-35E Dallas). Right way: no brake-check, signal, move right, let go."""
from frustkit import *

T_LC0, T_LC1 = 14.3, 15.7
HX = lane_key((0, 1), (T_LC0, 1), (T_LC1, 2), (99, 2))


def hero_expr(t):
    return 'calm' if t < 4.5 else ('annoyed' if t < 12.0 else ('focus' if t < 16.5 else 'smile'))


HERO = hero_car(HX, const(V), hero_expr, blink=blinks((13.6, T_LC1 + 0.3, 'R')))
FLASH = lambda t: 4.0 < t < 15.6 and (t * 3.0) % 1 < 0.5
AS = spd((0, 34.0), (3.2, 34.0), (4.0, V), (15.6, V), (17.0, 36.0), (99, 36.0))
TG = Veh(LANES[1], AS, 6.0, HERO.z(6.0) - 4.5 - 5.0, '#30333d', occ=occ_of('husb', lambda t: 'annoyed'), flash=FLASH)
EP.glare = FLASH
TRAF = filler([(0, 40), (0, -50), (2, 60), (2, -80), (3, 20), (3, -30), (1, 120), (0, 160), (3, 140), (2, 200)])
AG = [TG] + TRAF + oncoming()

defs = [
    (3.0, 'cine', dict(cam='track', target=TG, off=(-2.4, 1.7, -8.0), look=(0, 1.0, 14.0), f=760, dt=5.0, shake=0.1, streak=0.6)),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=22.0, H=9.0, a0=-2.4, w=0.2, f=1000, oz=-3.0)),
    (9.0, 'cine', dict(cam='track', target=TG, off=(3.6, 1.0, 1.0), look=(0, 0.9, 4.0), f=700, shake=0.08, flare=0.3)),
    (11.5, 'dash_face', dict(expr='annoyed', turn=lambda lt: 0.25 * math.sin(lt * 1.5))),
    (14.0, 'interior_mirror', dict()),
    (16.5, 'cine', dict(cam='heli', target=HERO, R=20.0, H=9.0, a0=0.6, w=0.14, f=1000, oz=-4.0)),
    (19.0, 'cine', dict(cam='tele', target=HERO, off=(9.0, 3.0, 55.0), tz=-6.0, f=2400)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
texts = dict(hook='On your bumper. Flashing.', loc='I-35E, Dallas, Texas',
             c=[None, 'Rush hour. 65 mph. All good...', '...then HE shows up. 5 m behind.', 'You want to slam the brakes.',
                ("Don't brake-check. Breathe. Keep your speed.", 68), 'Signal. Move right when clear.', 'Let him go. Not your race.', None],
             steps={4: 1, 5: 2, 6: 3}, end=('Tailgated? Stay calm. Move over.', 'What do YOU do when tailgated? Comment!'))


def sfx(m, S, E):
    for t in (0.7, 1.6, S[2] + 0.5, S[2] + 1.4, S[2] + 1.7, S[3] + 0.6, S[4] + 1.0):
        m.add(horn(0.4), t, 0.6)
    m.add(v8(3.0, lambda u: 0.8), S[2], 0.35)
    m.add(click(), 13.6, 0.6)
    indicator(m, 13.6, T_LC1 + 0.3, 0.45, 0.2)
    m.add(v8(2.0, lambda u: 0.6 + 0.4 * min(1, u)), 15.6, 0.6)
    m.add(car_pass(1.4, 0.5, 120), S[6] + 0.4, 0.8, pans(1.4, -0.7, 0.7))
    m.add(chime(), S[6] + 1.2, 0.5)


ep = Episode('f01_tailgated', ['Someone tailgating you?', 'Do THIS, not that'], city_dallas(), HERO, AG, defs, texts, 22.0, sfx=sfx)
video = ep.video
if __name__ == '__main__':
    ep.run()
