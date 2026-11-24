"""Frustrated #9: stuck in a jam while someone races past on the shoulder (Highway 401, Toronto).
Right way: stay in your lane (never block or chase him), the shoulder is for emergencies, let police handle it."""
from frustkit import *

EP.unit = 'kmh'
VJ = 6.3                                    # jam crawl 23 km/h
T_PASS = 7.5
SS = spd((0, 18.0), (11.0, 18.0), (12.5, 0.0), (99, 0.0))


def hero_expr(t):
    return 'calm' if t < 6.0 else ('annoyed' if t < 12.0 else ('focus' if t < 17.0 else 'smile'))


HERO = hero_car(const(LANES[3]), const(VJ), hero_expr)
SH = Veh(SHOULDER, SS, T_PASS, HERO.z(T_PASS), '#e8e8ee', mark=lambda t: True, occ=occ_of('husb', lambda t: 'smug' if t < 11.5 else 'shock'),
         blink=lambda t: 'B' if t > 13.0 and (t * 1.5) % 1 < 0.5 else None)
Z_STOP = SH.z(30)
PCAR = Veh(SHOULDER, const(0.0), 0.0, Z_STOP + 4.5 + 4.0, '#f4f4f6', police=lambda t: t > 10.4, brake=lambda t: 0.0)
COP = Trooper(17.0, Z_STOP + 0.6, lambda t: ('write', t % 3), None, lambda t: 'flat')
COP.visible = lambda t: t > 13.8
T_HP = (Z_STOP - HERO.z(0)) / VJ
QUEUE = [Veh(LANES[l], const(VJ), 0.0, z + 5.0 * l, COLS[(int(z) // 12 + l) % 10]) for l in range(4) for z in np.arange(-48.0, 240.0, 12.0)
         if not (l == 3 and abs(z + 15.0) < 8.0)]
AG = [SH, PCAR, COP] + QUEUE + oncoming()


def info():
    print('shoulder car stops at', round(Z_STOP, 1), '| hero passes the ticket stop at t', round(T_HP, 2),
          '| side gap passing hero', lateral_gap(SH, HERO, 6, 9))


defs = [
    (3.0, 'cine', dict(cam='track', target=SH, off=(1.4, 1.5, -7.5), look=(-1.0, 1.0, 10.0), f=740, dt=5.0, shake=0.12, streak=0.7)),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=26.0, H=12.0, a0=-0.6, w=0.12, f=1000, oz=12.0)),
    (9.0, 'interior_mirror', dict(f=850)),
    (11.5, 'dash_face', dict(expr='annoyed', turn=lambda lt: 0.3)),
    (14.0, 'cine', dict(cam='heli', target=SH, R=24.0, H=11.0, a0=-0.5, w=0.1, f=1000, oz=4.0)),
    (16.5, 'cine', dict(cam='top', center=lambda t: (9.0, HERO.z(t) + 30.0), H=60.0, f=1000)),
    (19.0, 'cine', dict(cam='fixed', pos=(17.4, 2.0, Z_STOP + 22.0), target_pt=(14.0, 1.0, Z_STOP - 6.0), f=820)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=-4.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=120.0, f=1000)),
]
texts = dict(hook='He skips the WHOLE jam?!', loc='Highway 401, Toronto, Ontario',
             c=[None, 'Stop-and-go on the 401...', '...then HE flies past. On the shoulder.', 'Block him! Follow him!',
                ('Stay in your lane. Never block or chase.', 72), ('Shoulder = emergencies only. Passing on it is illegal.', 62),
                'Police handle it. You just drive.', None],
             steps={4: 1, 5: 2, 6: 3}, end=('Shoulder cheater? Stay in your lane.', 'Have you seen this on your highway? Comment!'))


def red_shoulder(ctx, view, t, lt):
    a = smooth(lt / 0.4)
    z = HERO.z(t)
    pts = [view.pt((14.0, 0.02, z - 30)), view.pt((17.5, 0.02, z - 30)), view.pt((17.5, 0.02, z + 120)), view.pt((14.0, 0.02, z + 120))]
    if all(pts):
        poly(ctx, pts)
        setc(ctx, hexc('#ff4b4b'), 0.3 * a)
        ctx.fill()


defs[5][2]['post'] = red_shoulder


def sfx(m, S, E):
    m.add(v8(3.0, lambda u: 0.9), 0.0, 0.6)
    m.add(car_pass(1.4, 0.5, 120), 1.6, 0.8, pans(1.4, -0.4, 0.7))
    for t in (2.2, S[2] + 1.8, S[3] + 0.5):
        m.add(horn(0.5), t, 0.5)
    m.add(v8(2.5, lambda u: 0.9), S[2], 0.5)
    m.add(car_pass(1.4, 0.5, 120), T_PASS - 0.7, 0.8, pans(1.4, -0.3, 0.8))
    from street import siren_whoop
    m.add(siren_whoop(2), 10.5, 0.6)
    m.add(brake_squeal(1.2), 11.0, 0.6)
    m.add(chime(), S[6] + 0.8, 0.4)
    m.add(sad_trombone(), S[6] + 1.2, 0.45)


ep = Episode('f09_shoulder', ['Someone skips traffic on the shoulder?', "Don't do this"], city_401((Z_STOP + 500.0, Z_STOP + 1300.0)), HERO, AG,
             defs, texts, 22.0, sfx=sfx)
video = ep.video
if __name__ == '__main__':
    ep.run(info)
