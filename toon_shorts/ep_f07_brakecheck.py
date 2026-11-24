"""Frustrated #7: the driver ahead keeps brake-checking you (Highway 401, Toronto).
Right way: drop way back (3+ seconds), pass when safe without looking at him, never retaliate - call 911 if it's dangerous."""
from frustkit import *

EP.unit = 'kmh'
KS = spd((0, V), (6.4, V), (6.8, V - 8.0), (7.5, V - 8.0), (8.3, V), (9.0, V), (9.4, V - 8.0), (10.2, V - 8.0), (11.0, V), (99, V))
T_LC0, T_LC1 = 14.6, 16.0
HS2 = spd((11.0, KS(10.4)), (12.0, V - 4.0), (14.2, V - 4.0), (15.4, V + 4.5), (20.0, V + 4.5), (21.0, V), (99, V))
HS = lambda t: KS(t - 0.6) if t < 11.0 else HS2(t)
HX = lane_key((0, 1), (T_LC0, 1), (T_LC1, 2), (99, 2))


def hero_expr(t):
    return 'calm' if t < 6.5 else ('shock' if t < 7.6 else ('annoyed' if t < 12.0 else ('focus' if t < 17.5 else 'smile')))


HERO = hero_car(HX, HS, hero_expr, blink=blinks((14.0, T_LC1 + 0.3, 'R')))
BC = Veh(LANES[1], KS, 0.0, HERO.z(0) + 4.5 + 20.0, '#1c1c22', mark=lambda t: True, occ=occ_of('husb', lambda t: 'smug' if t < 15 else 'annoyed'),
         brake=lambda t: 1.0 if (6.4 < t < 7.6) or (9.0 < t < 10.3) else 0.0)
TRAF = filler([(0, 30), (0, -40), (0, 120), (3, 10), (3, -50), (3, 80), (2, -140), (2, 160), (1, -90)], speed=V,
              cols=[c for c in COLS if c != '#1c1c22'])
TRAF[-1].sk = TRAF[-1].sk                    # lane-1 follower far back
AG = [BC] + TRAF + oncoming()


def gap_s(i):
    def f(lt):
        t = EP.tm.wt(ep.video.S[i] + lt) + ep.video.shots[i].kw.get('dt', 0.0)
        if HERO.xk(t) > LANES[1] + 0.5:
            return None
        return (BC.z(t) - 2.25 - HERO.z(t) - 2.25) / max(1.0, HERO.speed(t))
    return f


defs = [
    (3.0, 'cine', dict(cam='track', target=HERO, off=(-2.6, 1.6, -7.0), look=(0, 1.0, 14.0), f=760, dt=5.5, shake=0.1, jolt=(6.7, 0.25))),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=24.0, H=10.0, a0=-0.7, w=0.12, f=1000, oz=10.0)),
    (9.0, 'interior_mirror', dict(f=1100)),
    (11.5, 'dash_face', dict(expr='annoyed', turn=lambda lt: 0.15 * math.sin(lt * 2.5))),
    (14.0, 'cine', dict(cam='heli', target=HERO, R=28.0, H=13.0, a0=-0.5, w=0.06, f=1000, oz=12.0)),
    (16.5, 'cine', dict(cam='track', target=HERO, off=(3.4, 1.2, -6.0), look=(-1.0, 0.9, 8.0), f=740, shake=0.07, flare=0.4)),
    (19.0, 'cine', dict(cam='tele', target=HERO, off=(10.0, 3.5, 60.0), tz=-8.0, f=2300)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
texts = dict(hook='He brakes. For NOTHING.', loc='Highway 401, Toronto, Ontario',
             c=[None, 'Morning commute on the 401...', 'The car ahead slams the brakes. Again. And again.', 'He WANTS you to react.',
                ('Drop way back. 3 seconds or more.', 74), 'Pass when safe. Signal. Eyes forward.', ("Don't retaliate. Dangerous? Call 911 when safe.", 64), None],
             steps={4: 1, 5: 2, 6: 3}, end=('Brake-checker? Back off. Get away.', 'Ever been brake-checked? Comment!'))


def sfx(m, S, E):
    for t in (1.2, 6.4, 9.0):
        m.add(brake_squeal(0.9), t, 0.5)
    for t in (1.8, 7.1, 9.7):
        m.add(screech(0.5, 1100), t, 0.45)
    m.add(horn(0.6), 2.2, 0.5)
    m.add(heartbeat(4, 120), S[2] + 0.2, 0.5)
    indicator(m, 14.0, T_LC1 + 0.3, 0.4, 0.2)
    m.add(v8(2.5, lambda u: 0.6 + 0.4 * min(1, u)), 15.0, 0.4)
    m.add(car_pass(1.3, 0.5, 100), S[5] + 1.2, 0.5, pans(1.3, -0.5, 0.5))
    m.add(chime(), S[6] + 1.0, 0.5)


ep = Episode('f07_brakecheck', ['Someone brake-checking you?', 'Get away safely'], city_401(), HERO, AG, defs, texts, 22.0, sfx=sfx,
             extra_overlays=[(6.0, 9.0, value_tag(gap_s(2), 'GAP', 's', 2.5, 1.0, x=1600, y=1250)),
                             (11.5, 14.0, value_tag(gap_s(4), 'GAP', 's', 2.5, 1.0, x=1600, y=1560))])
video = ep.video
if __name__ == '__main__':
    ep.run()
