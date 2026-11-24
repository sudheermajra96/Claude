"""v2 #10 Road rage (I-10 Phoenix). WANT: yell back, honk, race him -> he swerves at you, you dodge into a truck,
and HE drives away. RIGHT: no eye contact, ease off and let him go, if he follows you call 911 and drive to police."""
from frustkit2 import *

T_LC0, T_LC1 = 5.0, 6.4
T_HIT = 14.3
RS0 = [(0, 31.0), (7.0, 31.0), (7.6, V), (9.4, V), (10.2, V + 7.0), (11.2, V + 7.0), (12.0, V)]
RX = lane_key((0, 1), (9.4, 1), (10.8, 0), (99, 0))
r_occ = occ_of('husb', lambda t: 'annoyed', look_fn=lambda t: 1.2 if 11.0 < t < 14.5 else 0.0)
FLASH = lambda t: 7.0 < t < 9.4 and (t * 3) % 1 < 0.5
EP.glare = FLASH
HX0 = [(0, LANES[2]), (T_LC0, LANES[2]), (T_LC1, LANES[1])]
# ---------- wrong world: race him, he swerves at you, you hit the truck
HSW = spd((0, V), (12.6, V), (13.3, V + 5.0), (T_HIT, V + 5.0), (T_HIT + (V + 5.0) / 8.0, 0.0), (99, 0.0))
HXW = Key(HX0 + [(13.85, LANES[1]), (T_HIT, 6.45), (14.8, 5.6), (99, 5.6)])
HW = hero_car(HXW, HSW, lambda t: 'calm' if t < 7.0 else ('shock' if t > 13.8 else 'annoyed'), blink=blinks((4.3, T_LC1 + 0.3, 'L')),
              damage=[('front', T_HIT)])
RW = Veh(Key([(0, LANES[1]), (9.4, LANES[1]), (10.8, LANES[0]), (13.6, LANES[0]), (13.9, 2.9), (14.4, LANES[0]), (99, LANES[0])]),
         spd(*RS0, (12.6, V), (13.3, V + 5.0), (14.2, V + 5.0), (15.2, 38.0), (99, 38.0)), 12.0, None, '#1c1c22', occ=r_occ, mark=lambda t: True,
         flash=FLASH) if False else None
SEMI_Z = None
_probe = hero_car(HXW, HSW, lambda t: 'calm')
SEMI_W = Veh(LANES[2], spd((0, 24.0), (T_HIT, 24.0), (T_HIT + 3.0, 0.0), (99, 0.0)), T_HIT, _probe.z(T_HIT) + 6.0, '#2f6f9f', kind='semi',
             trailer=('#f4f4f6', '#d35400', 'SONORAN'), cab='#7a4fd0', brake=lambda t: 1.0 if t > T_HIT else 0.0)
RW = Veh(Key([(0, LANES[1]), (9.4, LANES[1]), (10.8, LANES[0]), (13.6, LANES[0]), (13.95, 2.9), (14.5, LANES[0]), (99, LANES[0])]),
         spd(*RS0, (12.6, V), (13.3, V + 5.0), (14.2, V + 5.0), (15.2, 38.0), (99, 38.0)), 12.0, _probe.z(12.0), '#1c1c22', occ=r_occ,
         mark=lambda t: True, flash=FLASH)
FX = CrashFX(T_HIT, lambda t: (7.4, 0.9, HW.z(T_HIT) + 1.6))
# ---------- right world (as before): no eye contact, ease off
HR = hero_car(Key(HX0 + [(99, LANES[1])]), spd((0, V), (14.2, V), (15.2, V - 5.0), (18.0, V - 5.0), (19.5, V), (99, V)),
              lambda t: 'calm' if t < 7.0 else ('worried' if t < 11.5 else ('focus' if t < 17.0 else 'smile')), blink=blinks((4.3, T_LC1 + 0.3, 'L')))
RR = Veh(RX, spd(*RS0, (14.4, V), (15.6, 36.0), (99, 36.0)), 12.0, _probe.z(12.0), '#1c1c22', occ=r_occ, mark=lambda t: True, flash=FLASH)
SEMI_R = Veh(LANES[2], const(24.0), T_HIT, _probe.z(T_HIT) + 6.0, '#2f6f9f', kind='semi', trailer=('#f4f4f6', '#d35400', 'SONORAN'), cab='#7a4fd0')
NOB = [c for c in COLS if c not in ('#1c1c22', '#e05d5d')]
TRAF = filler([(3, 20), (3, -50), (3, 120), (0, 160), (0, -120), (1, 200), (3, -160)], speed=V, cols=NOB)
ONC = oncoming()
tm = TimeMap([(12.0, 15.5, 0.2), (16.6, 19.6, 0.4)])
VH = tm.vt(T_HIT)

shots = layout([
    (2.4, dict(kind='cine', world='w', cam='heli', target=HW, R=16.0, H=9.0, a0=-0.4, w=0.12, f=950, oz=2.0, dt=T_HIT - 1.4, jolt=(T_HIT, 0.4),
               hook='Yell back at him?!')),
    (2.4, dict(kind='cine', cam='crane', target=HR, ox=-6.0, oz0=-20.0, oz1=-10.0, y0=16.0, y1=6.0, tz=6.0, f=1000, loc='I-10, Phoenix, Arizona',
               cap='You signal and change lanes. Normal.')),
    (3.0, dict(kind='interior_mirror', f=880, cap='He loses it. Flashing. On your bumper.')),
    (2.0, dict(kind='dash_face', car=RR, who='husb', expr='annoyed', turn=lambda lt: 0.1 * math.sin(lt * 9), cap='Screaming at you.')),
    (2.2, dict(kind='cine', cam='track', target=HR, off=(0.4, 1.4, 6.0), look=(-1.6, 1.1, -0.5), f=660, shake=0.06,
               cap="Now he's beside you. Yelling.")),
    (1.2, dict(kind='dash_face', world='w', expr='annoyed', turn=-0.6, cap='What you WANT to do: yell back...')),
    (1.3, dict(kind='horn_close', world='w', hits=(0.2, 0.55, 0.9), cap='...honk...')),
    (1.0, dict(kind='pedal_close', world='w', act='gas', hit=0.3, word='RACE HIM!')),
    (1.1, dict(kind='cine', world='w', cam='track', target=HW, off=(0.0, 0.6, -6.0), look=(-0.6, 0.8, 10.0), f=620, shake=0.14, streak=0.9)),
    (3.0, dict(kind='cine', world='w', cam='heli', target=HW, R=12.0, H=10.0, a0=-0.15, w=0.06, f=950, oz=2.0, jolt=(T_HIT, 0.5),
               x='He swerves at you. You dodge... into a truck.', vdelay=round(VH - 16.6, 2))),
    (2.6, dict(kind='cine', world='w', cam='tele', target=HW, off=(2.0, 2.5, 60.0), tx=1.5, f=2300, x='YOU crashed. He drove away.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=20.0, H=9.0, a0=-0.6, w=0.2, f=1000, rewind=(17.5, 9.0))),
    (3.0, dict(kind='cine', cam='track', target=HR, off=(0.4, 1.4, 6.0), look=(-1.6, 1.1, -0.5), f=660, shake=0.06, dt=-6.0, step=1,
               ok='No eye contact. No gestures. Eyes forward.')),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=26.0, H=12.0, a0=-0.5, w=0.1, f=1000, oz=14.0, dt=-5.0, step=2,
               ok='Ease off. Let him go ahead.')),
    (2.6, dict(kind='dash_face', expr='focus', turn=0.0, dt=-5.0, step=3, ok="He follows you? Don't go home. Call 911.")),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000, dt=-5.0,
               end_card=("Road rage? Don't engage. Let them go.", 'Ever met a road-rager? Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(impact(), 1.4, 0.9)
    m.add(screech(1.2, 900), 0.8, 0.5)
    m.add(air_horn(1.2), 1.5, 0.7)
    indicator(m, 4.3, T_LC1 + 0.3, 0.4, -0.2)
    m.add(v8(3.0, lambda u: 0.8 + 0.2 * math.sin(u * 4)), S[2], 0.5)
    for t in (S[2] + 0.4, S[2] + 1.2, S[2] + 1.6, S[3] + 0.3, S[3] + 0.9, S[4] + 0.5, S[4] + 1.4):
        m.add(horn(0.45), t, 0.6, -0.4)
    for k in (0.2, 0.55, 0.9):
        m.add(horn(0.3), S[6] + k, 0.8)
    m.add(v8(2.2, lambda u: 1.0), S[7], 0.7)
    m.add(braam(2.6, 41), S[9], 0.6)
    m.add(slow(screech(1.4, 900), 0.4), VH - 0.8, 0.6)
    m.add(slow(impact(), 0.5), VH, 1.0)
    m.add(air_horn(1.6), VH + 0.2, 0.6)
    m.add(v8(2.0, lambda u: 1.0), S[10] + 0.2, 0.5)
    m.add(sad_trombone(), S[10] + 0.9, 0.45)
    m.add(car_pass(1.3, 0.5, 120), S[13] + 0.8, 0.5, pans(1.3, -0.7, 0.2))


story = Story('g10_roadrage', ['Road-rager targets you?', 'Fight back? Watch this'], city_phoenix(), HW, HR,
              [RW, SEMI_W, FX] + [c for c in TRAF if not (c.xk(0) in (LANES[1], LANES[2]) and c.z(0) < 0)] + ONC, [RR, SEMI_R] + TRAF + ONC,
              shots, DUR, tm=tm, sfx=sfx)
video = story.video
if __name__ == '__main__':
    story.run(lambda: print('hit video', round(VH, 2), '| truck contact', lateral_gap(HW, SEMI_W, 13, 15), '| rager swerve gap',
                            lateral_gap(HW, RW, 13, 15)))
