"""Frustrated #6: the driver beside you changes lanes INTO you without looking (I-70 Golden, Colorado).
Right way: tap the horn + ease off, never ride in someone's blind spot, let them in and breathe."""
from frustkit import *

T_M = 7.2
HS = spd((0, V), (7.4, V), (8.4, V - 5.0), (12.0, V - 5.0), (13.4, V - 2.0), (99, V - 2.0))
HX = Key([(0, LANES[1]), (7.3, LANES[1]), (7.8, LANES[1] - 0.65), (8.8, LANES[1] - 0.65), (9.8, LANES[1]), (99, LANES[1])])


def hero_expr(t):
    return 'calm' if t < 7.3 else ('shock' if t < 8.9 else ('annoyed' if t < 12.0 else ('focus' if t < 16.0 else 'smile')))


HERO = hero_car(HX, HS, hero_expr)
MX = Key([(0, LANES[2]), (T_M, LANES[2]), (7.9, 7.0), (8.6, LANES[2]), (13.6, LANES[2]), (15.0, LANES[1]), (99, LANES[1])])
MER = Veh(MX, const(V), T_M, HERO.z(T_M) + 3.0, '#2f6f73', mark=lambda t: True,
          occ=occ_of('lady', lambda t: 'shock' if 7.8 < t < 9.5 else 'calm', look_fn=lambda t: -0.8 if 7.9 < t < 9.0 else 0.0),
          blink=blinks((12.8, 15.2, 'L')))
TRAF = filler([(0, 90), (0, -90), (3, 10), (3, -40), (3, 70), (2, 120), (2, -80), (1, 160), (0, 200)], speed=V,
              cols=[c for c in COLS if c != '#2f6f73'])
AG = [MER] + TRAF + oncoming()


def gap_info():
    g = 99.0
    for t in np.arange(7.0, 9.5, 0.01):
        if abs(MER.z(t) - HERO.z(t)) < 4.5:
            g = min(g, (MER.xk(t) - 0.95) - (HERO.xk(t) + 0.95))
    print('sideswipe near miss lateral gap', round(g, 2), 'm')


defs = [
    (3.0, 'cine', dict(cam='heli', target=HERO, R=14.0, H=9.0, a0=-3.0, w=0.12, f=950, oz=2.0, dt=6.2, jolt=(7.7, 0.25))),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=24.0, H=10.0, a0=2.5, w=-0.16, f=1000, oz=4.0)),
    (9.0, 'cine', dict(cam='track', target=HERO, off=(1.8, 1.9, -10.0), look=(-0.4, 0.9, 6.0), f=720, shake=0.07, jolt=(7.7, 0.3), flare=0.4)),
    (11.5, 'dash_face', dict(expr='annoyed', turn=lambda lt: 0.45)),
    (14.0, 'cine', dict(cam='top', center=lambda t: (7.0, HERO.z(t) + 2.0), H=34.0, f=1000, dt=-4.6)),
    (16.5, 'cine', dict(cam='heli', target=HERO, R=22.0, H=10.0, a0=2.4, w=-0.14, f=1000, oz=8.0)),
    (19.0, 'interior_mirror', dict()),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
texts = dict(hook='She never looked!', loc='I-70, Golden, Colorado',
             c=[None, 'Cruising next to her...', 'She moves over... right into you.', "You're shaking. And furious.",
                ('Replay: you were in her BLIND SPOT. Drop back or pass.', 62), 'Tap the horn, ease off, make room', 'She signals now. Let her in. Breathe.', None],
             steps={4: 1, 5: 2, 6: 3}, end=("Stay out of blind spots. Let it go.", 'Has this happened to you? Comment!'))


def blind_zone(ctx, view, t, lt):
    """Top view: the merging car's blind spot drawn in red, our car green once it drops back."""
    x, z, h = MER.pose(t)
    a = smooth(lt / 0.4)
    pts = [view.pt(P) for P in ((x - 1.0, 0.03, z - 1.0), (x - 4.2, 0.03, z - 1.0), (x - 4.2, 0.03, z - 9.0), (x - 1.0, 0.03, z - 6.5))]
    if all(pts):
        poly(ctx, pts)
        setc(ctx, hexc('#ff4b4b'), 0.35 * a)
        ctx.fill()
        c = view.pt((x - 2.6, 0.03, z - 4.5))
        text_center(ctx, 'BLIND SPOT', c[0], c[1], 54, (1, 1, 1), a=a)


defs[4][2]['post'] = blind_zone


def sfx(m, S, E):
    m.add(horn(0.5), 1.4, 0.8, -0.2)
    m.add(brake_squeal(1.0), 1.5, 0.5)
    m.add(horn(0.5), 7.7, 0.8, -0.2)
    m.add(brake_squeal(1.0), 7.6, 0.5)
    m.add(car_pass(1.2, 0.5, 100), S[2] + 0.4, 0.5, pans(1.2, 0.4, -0.4))
    indicator(m, 12.8, 15.2, 0.35, 0.3)
    m.add(chime(), S[6] + 1.0, 0.5)


ep = Episode('f06_sideswipe', ['Driver merges INTO you?', 'Stay out of the danger zone'], city_golden((1000.0, 1800.0)), HERO, AG, defs, texts,
             22.0, sfx=sfx)
video = ep.video
if __name__ == '__main__':
    ep.run(gap_info)
