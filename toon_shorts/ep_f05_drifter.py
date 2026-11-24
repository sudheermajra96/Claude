"""Frustrated #5: the driver ahead is on the phone - drifting, speeding up, slowing down (I-70 Golden, Colorado).
Right way: hang back, pass only when clear and don't linger beside him, report dangerous drivers (*CSP / *277 in
Colorado) hands-free or have a passenger call."""
from frustkit import *


def d_drift(t):
    return 0.3 * math.sin(1.3 * t) + 0.9 * math.exp(-((t - 7.6) / 0.6) ** 2) + 0.8 * math.exp(-((t - 10.6) / 0.6) ** 2)


DX = lambda t: LANES[1] + d_drift(t)
DS = lambda t: (26.0 + 2.5 * math.sin(0.7 * t)) * (1 - smooth((t - 12.0) / 1.5)) + 22.0 * smooth((t - 12.0) / 1.5)
DRIFT = Veh(DX, DS, 0.0, 40.0, '#c9c9d6', mark=lambda t: True,
            occ=occ_of('husb', lambda t: 'dreamy', look_fn=lambda t: 0.6))
T_LC0, T_LC1, T_RB0, T_RB1 = 14.6, 16.0, 21.2, 22.6
HX = lane_key((0, 1), (T_LC0, 1), (T_LC1, 0), (T_RB0, 0), (T_RB1, 1), (99, 1))
HS = spd((0, 26.0), (14.0, 26.0), (15.4, 33.5), (21.0, 33.5), (22.5, V), (99, V))


def hero_expr(t):
    return 'calm' if t < 6.5 else ('annoyed' if t < 12.5 else ('focus' if t < 18.5 else 'smile'))


HERO = hero_car(HX, HS, hero_expr, blink=blinks((14.0, T_LC1 + 0.3, 'L'), (20.6, T_RB1 + 0.3, 'R')))
L2 = Veh(LANES[2], const(V + 3), 7.6, DRIFT.z(7.6) + 0.5, '#37b26c')
TRAF = filler([(2, 160), (3, 40), (3, -30), (3, 110), (0, 160), (0, -120), (2, -150), (3, -110)], speed=V,
              cols=[c for c in COLS if c != '#c9c9d6'])
AG = [DRIFT, L2] + TRAF + oncoming()


def side_gap():
    g = 99.0
    for t in np.arange(6.5, 9.0, 0.01):
        if abs(L2.z(t) - DRIFT.z(t)) < 4.5:
            g = min(g, (L2.xk(t) - 0.95) - (DRIFT.xk(t) + 0.95))
    print('drift near miss lateral gap', round(g, 2), 'm | pass gap', lateral_gap(HERO, DRIFT, 14, 20))


defs = [
    (3.0, 'cine', dict(cam='heli', target=DRIFT, R=16.0, H=9.0, a0=-2.6, w=0.16, f=950, oz=0.0, dt=6.2)),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=24.0, H=10.0, a0=-2.4, w=0.16, f=1000, oz=8.0)),
    (9.0, 'cine', dict(cam='track', target=DRIFT, off=(-3.4, 1.3, -6.0), look=(0.5, 0.9, 6.0), f=740, shake=0.07, flare=0.4)),
    (11.5, 'dash_face', dict(expr='annoyed', turn=lambda lt: 0.2 * math.sin(lt * 2))),
    (14.0, 'interior_mirror', dict(f=1100)),
    (16.5, 'cine', dict(cam='heli', target=HERO, R=26.0, H=11.0, a0=-2.0, w=0.14, f=1000, oz=6.0)),
    (19.0, 'cine', dict(cam='tele', target=HERO, off=(-1.0, 3.5, 60.0), tx=1.5, tz=-10.0, f=2200)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
texts = dict(hook='Is he even looking?!', loc='I-70, Golden, Colorado',
             c=[None, 'Easy cruise toward the mountains...', 'The car ahead drifts. Brakes. Drifts again. Phone.',
                'You want to tailgate and honk.', ('Hang back. Give him LOTS of space.', 74),
                ("Pass only when clear. Don't linger beside him.", 66), ('Report it hands-free: *CSP (*277) in Colorado', 64), None],
             steps={4: 1, 5: 2, 6: 3}, end=('Distracted driver? Space, pass, report.', 'Seen someone texting at 65 mph? Comment!'))


def sfx(m, S, E):
    m.add(horn(0.8), 1.4, 0.7, 0.4)
    m.add(car_pass(1.2, 0.5, 120), 1.0, 0.6, pans(1.2, 0.5, -0.5))
    m.add(horn(0.8), 7.6, 0.6, 0.4)
    m.add(car_pass(1.2, 0.5, 120), 7.2, 0.5, pans(1.2, 0.5, -0.5))
    m.add(horn(0.4), S[3] + 0.5, 0.5)
    indicator(m, 14.0, T_LC1 + 0.3, 0.4, -0.2)
    m.add(v8(2.5, lambda u: 0.6 + 0.4 * min(1, u)), 14.6, 0.45)
    indicator(m, 20.6, T_RB1 + 0.3, 0.4, 0.2)
    for k, t in enumerate((S[6] + 0.6, S[6] + 0.8, S[6] + 1.0)):
        m.add(click(), t, 0.4)
    m.add(chime(), S[6] + 1.4, 0.5)


ep = Episode('f05_drifter', ['Driver ahead on their phone?', 'How to stay safe'], city_golden((700.0, 1500.0)), HERO, AG, defs, texts, 22.0,
             sfx=sfx)
video = ep.video
if __name__ == '__main__':
    ep.run(side_gap)
