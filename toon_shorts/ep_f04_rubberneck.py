"""Frustrated #4: the driver ahead slams on the brakes to stare at a crash on the other side (I-70 Golden, Colorado).
Right way: keep 3 seconds so you can brake smoothly, eyes on your road, don't slow down to look yourself."""
from frustkit import *

T_R = 7.0
RS = spd((0, V), (T_R, V), (8.1, 12.0), (12.0, 12.0), (14.5, V), (99, V))
HS = spd((0, V), (8.0, V), (9.2, 11.5), (12.4, 11.5), (14.8, V), (99, V))


def hero_expr(t):
    return 'calm' if t < 7.6 else ('shock' if t < 9.2 else ('annoyed' if t < 12.0 else ('focus' if t < 16.0 else 'smile')))


HERO = hero_car(const(LANES[0]), HS, hero_expr)
RUB = Veh(LANES[0], RS, 0.0, HERO.z(0) + 4.5 + 26.0, '#7a4fd0', mark=lambda t: True,
          occ=occ_of('lady', lambda t: 'shock' if T_R < t < 13 else 'calm', look_fn=lambda t: -1.1 * smooth((t - T_R) / 0.5) if T_R < t < 13 else 0.0))
Z_CR = RUB.z(10.0)
WRECK = [Veh(-14.6, const(0.0), 0.0, Z_CR + 3.0, '#37b26c', damage=[('back', -9)], blink=lambda t: 'B' if (t * 1.5) % 1 < 0.5 else None, brake=lambda t: 0.0),
         Veh(-14.6, const(0.0), 0.0, Z_CR - 3.2, '#c9c9d6', damage=[('front', -9)], brake=lambda t: 0.0),
         Veh(-14.6, const(0.0), 0.0, Z_CR - 13.0, '#f4f4f6', police=lambda t: True, brake=lambda t: 0.0)]
SLOW = spd((0, V), (8.0, V), (9.5, V - 8.0), (12.5, V - 8.0), (14.5, V), (99, V))
TRAF = filler([(1, 20), (1, -45), (2, 50), (2, -20), (3, 5), (3, -70), (1, 140), (2, 180)], speed=SLOW,
              cols=[c for c in COLS if c != '#7a4fd0'])
FOL = Veh(LANES[0], HS, 0.0, -60.0, COLS[6])
AG = [RUB, FOL] + WRECK + TRAF + oncoming()


def gap_m(i):
    def f(lt):
        t = EP.tm.wt(ep.video.S[i] + lt) + ep.video.shots[i].kw.get('dt', 0.0)
        return RUB.z(t) - 2.25 - HERO.z(t) - 2.25
    return f


defs = [
    (3.0, 'cine', dict(cam='track', target=HERO, off=(3.6, 1.3, -3.0), look=(-0.5, 0.9, 10.0), f=720, dt=7.1, shake=0.1, jolt=(8.3, 0.3))),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=24.0, H=10.0, a0=2.3, w=-0.18, f=1000, oz=12.0)),
    (9.0, 'cine', dict(cam='tele', target=RUB, off=(-1.0, 3.5, 70.0), tx=-6.0, tz=-6.0, f=2000)),
    (11.5, 'dash_face', dict(expr='annoyed', turn=lambda lt: 0.2 * math.sin(lt * 2))),
    (14.0, 'interior_mirror', dict()),
    (16.5, 'cine', dict(cam='heli', target=HERO, R=20.0, H=8.0, a0=-1.9, w=0.16, f=1000, oz=0.0)),
    (19.0, 'cine', dict(cam='track', target=HERO, off=(-2.6, 1.6, 2.0), look=(0.4, 0.9, 7.0), f=720, shake=0.06, streak=0.4, flare=0.4)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
texts = dict(hook='She stops... to LOOK?!', loc='I-70, Golden, Colorado',
             c=[None, 'Heading into the Rockies...', 'A crash on the OTHER side. She brakes hard to stare.', 'Seriously?!',
                ('Keep 3 seconds. Brake early and smooth.', 72), 'Eyes on YOUR road, not the crash', "Don't slow down to look. Keep moving.", None],
             steps={4: 1, 5: 2, 6: 3}, end=("Don't rubberneck. Eyes on your road.", 'Do you slow down to look? Be honest! Comment!'))


def sfx(m, S, E):
    m.add(brake_squeal(1.2), 0.2, 0.5)
    m.add(screech(0.9, 1100), 1.0, 0.6)
    m.add(horn(0.6), 1.9, 0.6)
    for k in np.arange(S[2], E[2], 0.38):
        m.add(click(), k, 0.07)
    m.add(brake_squeal(1.2), T_R, 0.5)
    m.add(screech(1.0, 1100), 7.9, 0.6)
    m.add(horn(0.7), S[3] + 0.3, 0.6)
    m.add(chime(), S[6] + 1.0, 0.5)


ep = Episode('f04_rubberneck', ['Driver brakes to stare at a crash?', 'Stay safe behind them'], city_golden(), HERO, AG, defs, texts, 22.0,
             sfx=sfx, extra_overlays=[(0.0, 3.0, value_tag(gap_m(0), 'GAP', 'm', 20.0, 8.0, x=1600, y=1560, fmt='{:.0f}'))])
video = ep.video
if __name__ == '__main__':
    ep.run()
