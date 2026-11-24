"""Frustrated #10: you change lanes politely and a road-rager loses it - tailgates, pulls alongside, honks and yells
(I-10 Phoenix, Arizona). Right way: no eye contact / no gestures, ease off and let him go, if he follows you don't drive
home - call 911 and head to a police station."""
from frustkit import *

T_LC0, T_LC1 = 5.0, 6.4
T_RB0, T_RB1 = 17.4, 18.8
HS = spd((0, V), (14.2, V), (15.2, V - 5.0), (18.0, V - 5.0), (19.5, V), (99, V))
HX = lane_key((0, 2), (T_LC0, 2), (T_LC1, 1), (99, 1))


def hero_expr(t):
    return 'calm' if t < 7.0 else ('worried' if t < 11.5 else ('focus' if t < 17.0 else 'smile'))


HERO = hero_car(HX, HS, hero_expr, blink=blinks((4.3, T_LC1 + 0.3, 'L')))
RS = spd((0, 31.0), (7.0, 31.0), (7.6, V), (9.4, V), (10.2, V + 7.0), (11.2, V + 7.0), (12.0, V), (14.4, V), (15.6, 36.0), (99, 36.0))
RX = lane_key((0, 1), (9.4, 1), (10.8, 0), (99, 0))
RAGE = Veh(RX, RS, 12.0, HERO.z(12.0), '#1c1c22', mark=lambda t: True,
           occ=occ_of('husb', lambda t: 'annoyed', look_fn=lambda t: 1.2 if 11.0 < t < 14.5 else 0.0),
           flash=lambda t: 7.0 < t < 9.4 and (t * 3) % 1 < 0.5)
SEMI = Veh(LANES[2], const(24.0), 0.0, 45.0 + 15.5, '#2f6f9f', kind='semi', trailer=('#f4f4f6', '#d35400', 'SONORAN'), cab='#7a4fd0')
TRAF = filler([(3, 20), (3, -50), (3, 120), (0, 160), (0, -120), (2, -110), (1, 200), (3, -160)], speed=V,
              cols=[c for c in COLS if c not in ('#1c1c22', '#e05d5d')])
AG = [RAGE, SEMI] + TRAF + oncoming()
EP.glare = lambda t: 7.0 < t < 9.4 and (t * 3) % 1 < 0.5


def info():
    print('rager gap when you merge', round(HERO.z(T_LC1) - 2.25 - RAGE.z(T_LC1) - 2.25, 1), 'm | tailgate min',
          round(min(HERO.z(t) - 4.5 - RAGE.z(t) for t in np.arange(6.5, 9.4, 0.05)), 1), 'm')


defs = [
    (3.0, 'cine', dict(cam='track', target=HERO, off=(0.6, 1.3, 5.5), look=(-1.8, 1.1, -0.5), f=640, dt=9.6, shake=0.08)),
    (6.0, 'cine', dict(cam='heli', target=HERO, R=24.0, H=10.0, a0=-0.7, w=0.12, f=1000, oz=12.0)),
    (9.0, 'interior_mirror', dict(f=900)),
    (11.5, 'dash_face', dict(expr='worried', turn=lambda lt: -0.3 * smooth(lt / 0.5) if lt < 1.6 else 0.0)),
    (14.0, 'cine', dict(cam='track', target=HERO, off=(0.4, 1.4, 6.0), look=(-1.6, 1.1, -0.5), f=660, shake=0.06)),
    (16.5, 'cine', dict(cam='heli', target=HERO, R=26.0, H=12.0, a0=-0.5, w=0.1, f=1000, oz=14.0)),
    (19.0, 'cine', dict(cam='tele', target=HERO, off=(11.0, 3.5, 60.0), tz=-8.0, f=2300)),
    (22.0, 'cine', dict(cam='crane', target=HERO, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000)),
]
texts = dict(hook='Why is he SO angry?!', loc='I-10, Phoenix, Arizona',
             c=[None, 'You signal and change lanes. Normal.', 'He loses it. Flashing. On your bumper.', "Now he's beside you. Yelling.",
                ("No eye contact. No gestures. Eyes forward.", 70), 'Ease off. Let him go ahead.', ("He follows you? Don't go home. Call 911.", 68), None],
             steps={4: 1, 5: 2, 6: 3}, end=("Road rage? Don't engage. Let them go.", 'Ever met a road-rager? Comment!'))


def sfx(m, S, E):
    for t in (0.4, 0.9, 1.3, 2.0):
        m.add(horn(0.45), t, 0.6, -0.4)
    m.add(v8(3.0, lambda u: 0.9), 0.0, 0.5)
    indicator(m, 4.3, T_LC1 + 0.3, 0.4, -0.2)
    m.add(v8(3.0, lambda u: 0.8 + 0.2 * math.sin(u * 4)), S[2], 0.5)
    for t in (S[2] + 0.4, S[2] + 1.2, S[2] + 1.5, S[3] + 0.3, S[3] + 0.9, S[4] + 0.5, S[4] + 1.4):
        m.add(horn(0.45), t, 0.6, -0.4)
    m.add(heartbeat(4, 125), S[3] + 0.2, 0.55)
    m.add(v8(2.0, lambda u: 0.7 + 0.3 * min(1, u)), 15.0, 0.6)
    m.add(car_pass(1.3, 0.5, 120), 15.6, 0.6, pans(1.3, -0.7, 0.2))
    m.add(chime(), S[6] + 1.0, 0.5)


ep = Episode('f10_roadrage', ['Road-rager targets you?', 'Do THIS'], city_phoenix(), HERO, AG, defs, texts, 22.0, sfx=sfx)
video = ep.video
if __name__ == '__main__':
    ep.run(info)
