"""v2 #5 Driver on the phone (I-70 Golden). WANT: pull up beside him, honk and glare -> he drifts into you and pins you
against the wall. RIGHT: hang back, pass quickly when clear, report hands-free (*CSP / *277 in Colorado)."""
from frustkit2 import *

VD = 23.0
T_C = 13.0                                       # contact (wrong)


def drift_r(t):
    return 0.3 * math.sin(1.3 * t) + 0.9 * math.exp(-((t - 5.6) / 0.5) ** 2) + 0.7 * math.exp(-((t - 7.6) / 0.5) ** 2)


DX_R = lambda t: LANES[1] + drift_r(t)
DX_W = lambda t: LANES[1] + drift_r(t) * (1 - smooth((t - 12.3) / 0.3)) - (5.25 - 3.65) * smooth((t - 12.4) / 0.6) \
    + 0.35 * smooth((t - 13.0) / 0.4)
d_occ = occ_of('husb', lambda t: 'shock' if 12.9 < t < 16 else 'focus', look_fn=lambda t: 0.6)
DW = Veh(DX_W, spd((0, VD), (T_C, VD), (T_C + VD / 6.0, 0.0), (99, 0.0)), T_C, 0.0, '#c9c9d6', occ=d_occ, mark=lambda t: True,
         blink=lambda t: 'B' if t > T_C + 2 and (t * 1.5) % 1 < 0.5 else None)
HX_W = Key([(0, LANES[1]), (10.0, LANES[1]), (11.2, LANES[0]), (T_C, LANES[0]), (13.35, 0.55), (13.8, 0.75), (99, 0.75)])
HS_W = spd((0, VD), (9.8, VD), (10.6, 29.0), (12.0, 29.0), (12.6, VD), (T_C, VD), (T_C + VD / 7.0, 0.0), (99, 0.0))
HW = hero_car(HX_W, HS_W, lambda t: 'calm' if t < 5 else ('shock' if t > 12.9 else 'annoyed'), za=0.0)
# anchor the wrong-world hero alongside him at contact
HW = hero_car(HX_W, HS_W, lambda t: 'calm' if t < 5 else ('shock' if t > 12.9 else 'annoyed'))
off = DW.z(T_C) - HW.z(T_C)
HW = Veh(HX_W, HS_W, 0.0, off, HERO_COL, occ=occ_of('hero', lambda t: 'calm' if t < 5 else ('shock' if t > 12.9 else 'annoyed'),
                                                        look_fn=lambda t: 0.7 if 11.5 < t < 12.9 else 0.0),
         blink=blinks((9.6, 11.2, 'L')))
FX = CrashFX(T_C, lambda t: (2.75, 0.8, HW.z(T_C) + 0.5))
FX2 = CrashFX(13.35, lambda t: (-0.35, 0.6, HW.z(13.35) + 1.0), steam=0.5)
# right world
DR = Veh(DX_R, const(VD), T_C, 0.0, '#c9c9d6', occ=d_occ, mark=lambda t: True)
T_P0, T_P1, T_B0, T_B1 = 20.6, 21.8, 27.6, 28.8
HR = Veh(lane_key((0, 1), (T_P0, 1), (T_P1, 0), (T_B0, 0), (T_B1, 1), (99, 1)),
         spd((0, VD), (6.0, VD), (7.5, VD - 4.0), (17.5, VD - 4.0), (20.0, VD), (21.4, 35.0), (27.2, 35.0), (28.3, V), (99, V)), 0.0, off,
         HERO_COL, occ=occ_of('hero', lambda t: 'calm' if t < 5 else ('focus' if t < 24 else 'smile')),
         blink=blinks((T_P0 - 0.6, T_P1 + 0.3, 'L'), (T_B0 - 0.6, T_B1 + 0.3, 'R')))
L2 = Veh(LANES[2], const(V + 3), 5.6, DR.z(5.6) + 0.5, '#37b26c')
NOG = [c for c in COLS if c != '#c9c9d6']
TRAF = filler([(2, 160), (3, 40), (3, -30), (3, 110), (0, 260), (2, -150), (3, -110)], speed=V, cols=NOG)
ONC = oncoming()
tm = TimeMap([(9.6, 12.2, 0.25), (14.2, 17.2, 0.4)])


def gap_r(i):
    def f(lt):
        t = tm.wt(story.video.S[i] + lt)
        if HR.xk(t) < LANES[1] - 0.3:
            return None
        return (DR.z(t) - 4.5 - HR.z(t)) / max(1.0, HR.speed(t))
    return f


shots = layout([
    (2.4, dict(kind='cine', world='w', cam='track', target=HW, off=(0.4, 3.2, -5.0), look=(1.4, 1.0, 8.0), f=700, dt=T_C - 1.5,
               jolt=(T_C, 0.5), hook='Teach him a lesson?')),
    (2.6, dict(kind='cine', cam='track', target=HR, off=(-2.8, 0.5, -7.0), look=(0.6, 0.7, 12.0), f=640, shake=0.05, flare=0.4,
               loc='I-70, Golden, Colorado', cap='Cruising toward the Rockies...')),
    (2.6, dict(kind='cine', cam='heli', target=DR, R=18.0, H=9.0, a0=-2.6, w=0.14, f=950, cap='The car ahead drifts. Brakes. Drifts again.', capsize=70)),
    (2.0, dict(kind='dash_face', car=DR, who='husb', expr='focus', turn=0.55, cap="He's on his PHONE.")),
    (1.2, dict(kind='dash_face', world='w', expr='annoyed', turn=0.0, cap='What you WANT to do...')),
    (1.4, dict(kind='horn_close', world='w', hits=(0.3, 0.8), cap='Pull up beside him. Honk. Glare.')),
    (2.0, dict(kind='cine', world='w', cam='track', target=HW, off=(1.8, 1.3, 9.5), look=(1.6, 1.0, -1.0), f=700, shake=0.05,
               cap='...teach him a lesson.')),
    (3.0, dict(kind='cine', world='w', cam='heli', target=HW, R=11.0, H=11.0, a0=-0.3, w=0.08, f=950, oz=1.0, jolt=(T_C, 0.5),
               x='He drifts... right into you.', vdelay=round(tm.vt(T_C) - 14.2, 2))),
    (2.4, dict(kind='cine', world='w', cam='tele', target=HW, off=(3.0, 2.0, 55.0), tx=0.5, f=2300, x='Pinned against the wall.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=18.0, H=8.0, a0=-0.6, w=0.2, f=1000, rewind=(16.0, 5.0))),
    (3.0, dict(kind='cine', cam='track', target=HR, off=(-1.2, 2.2, -8.0), look=(0.3, 0.9, 30.0), f=900, shake=0.04, step=1,
               ok='Hang back. Give him LOTS of space.')),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=22.0, H=10.0, a0=-2.2, w=0.12, f=1000, oz=4.0, step=2, ok="Pass quickly when it's clear.")),
    (2.6, dict(kind='dash_face', expr='focus', turn=0.0, step=3, ok='Report it hands-free: *CSP (*277)')),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000,
               end_card=('Distracted driver? Space. Pass. Report.', 'Seen someone texting at 65 mph? Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(impact(), 1.5, 0.9)
    m.add(screech(1.4, 700), 1.6, 0.5)
    m.add(horn(0.8), S[2] + 0.6, 0.5, 0.4)
    m.add(car_pass(1.2, 0.5, 120), S[2] + 0.4, 0.5, pans(1.2, 0.5, -0.5))
    for k in (0.3, 0.8):
        m.add(horn(0.4), S[5] + k, 0.8)
    m.add(v8(2.0, lambda u: 0.8), S[6], 0.5)
    vc = tm.vt(T_C)
    m.add(braam(2.6, 41), S[7], 0.6)
    m.add(slow(impact(), 0.5), vc, 1.0)
    m.add(slow(screech(2.0, 650), 0.4), vc + 0.3, 0.6)
    m.add(sad_trombone(), S[8] + 0.6, 0.45)
    m.add(v8(2.5, lambda u: 0.6 + 0.4 * min(1, u)), tm.vt(T_P0), 0.45)
    for k in (0.5, 0.7, 0.9):
        m.add(click(), S[12] + k, 0.4)


story = Story('g05_drifter', ['Driver ahead on their phone?', 'Get close to scold them? Watch'], city_golden((700.0, 1500.0)), HW, HR,
              [DW, FX, FX2] + [c for c in TRAF if c.z(0) > 0] + ONC, [DR, L2] + TRAF + ONC, shots, DUR, tm=tm, sfx=sfx)
video = story.video
story.video.overlays.append((story.video.S[10], story.video.E[10], value_tag(gap_r(10), 'GAP', 's', 3.0, 1.5, x=1600, y=300)))
if __name__ == '__main__':
    story.run(lambda: print('contact video', round(tm.vt(T_C), 2), '| side contact', lateral_gap(HW, DW, 11, 14),
                            '| right pass gap', lateral_gap(HR, DR, 19, 26), '| hero x at barrier', HX_W(13.5)))
