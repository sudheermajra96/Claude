"""v2 #2 Cut off (I-35E Dallas). WANT: chase him, honk, ride his bumper -> he brakes, you swerve into the next lane and
hit a car. RIGHT: ease off, rebuild a 3-second gap, let him go."""
from frustkit2 import *

T_C0, T_C1 = 6.0, 6.7
CX = lane_key((0, 2), (T_C0, 2), (T_C1, 1), (99, 1))
# wrong world: chase, he brakes, you swerve left and hit the car in lane 0
T_BR, T_SW = 11.5, 11.9
CS_W = spd((0, 31.0), (T_BR, 31.0), (12.3, 24.0), (12.8, 24.0), (13.8, 32.0), (99, 32.0))
HS_W = spd((0, V), (9.0, V), (10.0, 33.5), (11.0, 31.0), (T_SW, 31.0), (T_SW + 31.0 / 8.5, 0.0), (99, 0.0))
HX_W = Key([(0, LANES[1]), (T_SW, LANES[1]), (12.25, 3.68), (12.7, 4.3), (99, 4.3)])


def hw_expr(t):
    return 'calm' if t < 6.0 else ('shock' if 6.4 < t < 7.6 or t > T_SW else 'annoyed')


HW = hero_car(HX_W, HS_W, hw_expr, damage=[('front', 12.3)])
CUT_ANCHOR = HW.z(T_C1) + 4.5 + 4.0
CUTW = Veh(CX, CS_W, T_C1, CUT_ANCHOR, '#e8e8ee', occ=occ_of('husb', lambda t: 'smug'), mark=lambda t: True,
           brake=lambda t: 1.0 if T_BR < t < 12.8 else 0.0)
T_HIT = 12.25
L0 = Veh(Key([(0, LANES[0]), (T_HIT, LANES[0]), (12.8, 1.2), (99, 1.2)]), spd((0, V), (T_HIT, V), (T_HIT + V / 6.0, 0.0), (99, 0.0)),
         T_HIT, HW.z(T_HIT) - 0.8, '#37b26c', occ=occ_of('lady', lambda t: 'shock' if t > T_HIT - 0.3 else 'calm'), damage=[('front', T_HIT)],
         blink=lambda t: 'B' if t > T_HIT + 2 and (t * 1.5) % 1 < 0.5 else None)
FX = CrashFX(T_HIT, lambda t: (2.75, 0.7, HW.z(T_HIT) + 0.5))

# right world: ease off and let him go
HS_R = spd((0, V), (6.9, V), (7.9, V - 6.0), (14.0, V - 6.0), (15.5, V), (99, V))
HR = hero_car(const(LANES[1]), HS_R, lambda t: 'calm' if t < 6.0 else ('shock' if t < 7.6 else ('focus' if t < 19 else 'smile')))
CUTR = Veh(CX, const(31.0), T_C1, CUT_ANCHOR, '#e8e8ee', occ=occ_of('husb', lambda t: 'smug'), mark=lambda t: True)
L0R = Veh(LANES[0], const(V), T_HIT, HW.z(T_HIT) - 0.8, '#37b26c')
TRAF_ALL = filler([(0, -60), (3, 25), (3, -40), (2, 120), (0, 170), (3, 180), (2, -200), (1, -70)], cols=[c for c in COLS if c not in ('#e8e8ee', '#37b26c')])
TRAF = TRAF_ALL
TRAF_W = [c for c in TRAF_ALL if not (c.xk(0) in (LANES[0], LANES[1]) and c.z(0) < 0)]
ONC = oncoming()
tm = TimeMap([(8.1, 12.0, 0.2), (14.9, 17.9, 0.35)])


def gap_s(lt):
    t = tm.wt(story.video.S[11] + lt)
    return (CUTR.z(t) - 2.25 - HR.z(t) - 2.25) / max(1.0, HR.speed(t))


shots = layout([
    (2.6, dict(kind='cine', world='w', cam='top', center=lambda t: (4.0, HW.z(t) + 4.0), H=30.0, f=1000, dt=10.9, hook='Chase him?!')),
    (2.4, dict(kind='cine', cam='crane', target=HR, ox=-5.0, oz0=-30.0, oz1=-18.0, y0=14.0, y1=6.0, tz=8.0, f=1000, loc='I-35E, Dallas, Texas',
               cap='Easy drive into downtown...')),
    (1.6, dict(kind='interior_mirror', mirror=False, f=900, cap='WHOA. He cuts in. No signal.')),
    (1.5, dict(kind='cine', cam='track', target=CUTR, off=(2.6, 1.0, 3.0), look=(-1.0, 1.0, -3.0), f=620, cap='4 metres. At 65 mph.')),
    (1.5, dict(kind='dash_face', world='w', expr='annoyed', turn=0.0, cap='What you WANT to do...')),
    (1.3, dict(kind='horn_close', world='w', hits=(0.3, 0.75, 1.1), cap='Lay on the horn...')),
    (1.1, dict(kind='pedal_close', world='w', act='gas', hit=0.45, word='CHASE HIM!')),
    (2.9, dict(kind='cine', world='w', cam='track', target=HW, off=(-0.8, 0.45, -5.0), look=(0.2, 0.8, 8.0), f=620, shake=0.14, streak=0.9,
               cap="...ride his bumper. Show him!")),
    (3.0, dict(kind='cine', world='w', cam='heli', target=HW, R=13.0, H=6.0, a0=-0.9, w=0.12, f=900, oz=2.0, jolt=(T_HIT, 0.4),
               x='He brakes. You swerve... into her.', vdelay=1.4)),
    (2.4, dict(kind='cine', world='w', cam='tele', target=HW, off=(-2.0, 2.5, 55.0), tx=1.0, f=2200,
               x='Chasing him just caused a crash.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=20.0, H=9.0, a0=-0.5, w=0.2, f=1000, oz=0.0, rewind=(14.8, 6.5))),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=22.0, H=12.0, a0=-0.4, w=0.05, f=1000, oz=14.0, step=1,
               ok='Foot off the gas. Brake gently.')),
    (3.0, dict(kind='cine', cam='track', target=HR, off=(-3.4, 1.2, -6.0), look=(0.5, 0.9, 10.0), f=720, shake=0.05, step=2,
               ok='Rebuild your 3-second gap.')),
    (2.6, dict(kind='dash_face', expr='smile', turn=0.0, step=3, ok='Let him go. Keep your day.')),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000,
               end_card=('Cut off? Back off. Let it go.', 'Have you ever chased someone? Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(screech(1.0, 1100), 0.6, 0.7)
    m.add(impact(), 1.85, 0.9)
    m.add(car_pass(1.2, 0.5, 120), S[2] + 0.1, 0.7, pans(1.2, 0.6, -0.3))
    m.add(brake_squeal(0.8), S[2] + 0.5, 0.5)
    for k in (0.3, 0.75, 1.1):
        m.add(horn(0.35), S[5] + k, 0.8)
    m.add(v8(2.4, lambda u: 0.7 + 0.3 * min(1, u)), S[6], 0.7)
    m.add(horn(0.6), S[7] + 0.8, 0.6)
    vh = tm.vt(T_HIT)
    m.add(braam(2.6, 41), S[8], 0.6)
    m.add(slow(screech(1.2, 1100), 0.35), S[8] + 0.1, 0.6)
    m.add(slow(impact(), 0.5), vh, 1.0)
    m.add(sad_trombone(), S[9] + 0.5, 0.45)
    m.add(chime(), S[13] + 0.6, 0.4)


story = Story('g02_cutoff', ['Someone cuts you off?', "Chasing them? Watch this"], city_dallas((620.0, 1500.0)), HW, HR,
              [CUTW, L0, FX] + TRAF_W + ONC, [CUTR, L0R] + TRAF + ONC, shots, DUR, tm=tm, sfx=sfx)
video = story.video
story.video.overlays.append((story.video.S[12], story.video.E[12], value_tag(lambda lt: (CUTR.z(tm.wt(story.video.S[12] + lt)) - 2.25 -
                            HR.z(tm.wt(story.video.S[12] + lt)) - 2.25) / max(1.0, HR.speed(tm.wt(story.video.S[12] + lt))),
                            'GAP', 's', 3.0, 1.5, x=1600, y=300)))
if __name__ == '__main__':
    story.run(lambda: print('hit video', round(tm.vt(T_HIT), 2), '| side gap hero/CUT', lateral_gap(HW, CUTW, 11, 14),
                            '| hero/L0', lateral_gap(HW, L0, 11, 13)))
