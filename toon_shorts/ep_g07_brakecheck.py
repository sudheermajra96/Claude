"""v2 #7 Brake-checker (Highway 401 Toronto). WANT: crowd him and flash your high beams -> he brake-checks, you hit him,
and the car behind hits you: 3-car pile-up. RIGHT: drop way back, pass when safe without looking, call 911 if dangerous."""
from frustkit2 import *

T_BC = 11.2
BCS = spd((0, V), (T_BC, V), (T_BC + 1.6, V - 12.0), (99, V - 12.0))
(zl, zh, zf), (vl, vh, vf), (T1, T2) = chain_sim(BCS, [6.0, 11.0], [0.8, 1.1], 7.5, T_BC)
VR1 = VR2 = 0.0
FLASH = lambda t: 9.0 < t < T1 and (t * 3.0) % 1 < 0.5
EP.glare = lambda t: False
bc_occ = occ_of('husb', lambda t: 'shock' if t > T1 - 0.2 else 'smug')
BCW = SimCar(LANES[1], zl, vl, '#1c1c22', occ=bc_occ, mark=lambda t: True, damage=[('back', T1)],
             blink=lambda t: 'B' if t > T1 + 2 and (t * 1.5) % 1 < 0.5 else None)
OFF2 = 0.0
HW = SimCar(LANES[1], zh, vh, HERO_COL,
            occ=occ_of('hero', lambda t: 'annoyed' if t < T1 - 0.3 else 'shock'), flash=FLASH, damage=[('front', T1), ('back', T2)])
FOLW = SimCar(LANES[1], lambda t: zf(t) + OFF2, vf, '#f2a541', occ=occ_of('lady', lambda t: 'shock' if t > T2 - 0.3 else 'calm'),
              damage=[('front', T2)])
FX1 = CrashFX(T1, lambda t: (LANES[1], 0.7, zl(t) - 2.25))
FX2 = CrashFX(T2, lambda t: (LANES[1], 0.7, zf(t) + OFF2 + 2.25))
# right world: drop back, pass in lane 2
KS = spd((0, V), (6.4, V), (6.8, V - 8.0), (7.5, V - 8.0), (8.3, V), (99, V))
BCR = Veh(LANES[1], KS, 0.0, zl(0.0), '#1c1c22', occ=bc_occ, mark=lambda t: True, brake=lambda t: 1.0 if 6.4 < t < 7.6 else 0.0)
T_LC0, T_LC1 = 17.0, 18.4
HR = Veh(lane_key((0, 1), (T_LC0, 1), (T_LC1, 2), (99, 2)),
         spd((0, V), (6.6, V), (7.4, V - 9.0), (8.4, V - 6.0), (14.0, V - 6.0), (16.5, V), (17.8, V + 5.0), (23.0, V + 5.0), (24.0, V), (99, V)),
         0.0, zl(0.0) - 4.5 - 20.0, HERO_COL, occ=occ_of('hero', lambda t: 'calm' if t < 6.3 else ('shock' if t < 7.6 else ('focus' if t < 22 else 'smile'))),
         blink=blinks((16.4, T_LC1 + 0.3, 'R')))
FOLR = Veh(LANES[1], spd((0, V), (6.8, V), (7.8, V - 7.0), (14.0, V - 7.0), (16.5, V), (99, V)), 0.0, zl(0.0) - 4.5 - 20.0 - 4.5 - 30.0, '#f2a541')
NOO = [c for c in COLS if c not in ('#1c1c22', '#f2a541')]
TRAF = filler([(0, 30), (0, -60), (0, 120), (3, 10), (3, -50), (3, 80), (2, -160), (2, 160)], speed=V, cols=NOO)
ONC = oncoming()
tm = TimeMap([(9.0, 11.4, 0.3), (13.8, 16.8, 0.4)])
V1, V2 = tm.vt(T1), tm.vt(T2)


def gap_r(i):
    def f(lt):
        t = tm.wt(story.video.S[i] + lt)
        if HR.xk(t) > LANES[1] + 0.4:
            return None
        return (BCR.z(t) - 4.5 - HR.z(t)) / max(1.0, HR.speed(t))
    return f


shots = layout([
    (2.6, dict(kind='cine', world='w', cam='track', target=FOLW, off=(-1.0, 1.3, -9.0), look=(0.3, 1.0, 10.0), f=720, dt=T2 - 1.4,
               jolt=(T2, 0.5), hook='3-car pile-up?!')),
    (2.4, dict(kind='cine', cam='heli', target=HR, R=40.0, H=22.0, a0=-0.5, w=0.1, f=1000, oz=20.0, loc='Highway 401, Toronto, Ontario',
               cap='Morning commute on the 401...')),
    (2.0, dict(kind='interior_mirror', f=1000, mirror=False, cap='He brakes. For NOTHING.')),
    (2.0, dict(kind='dash_face', car=BCR, who='husb', expr='smug', turn=0.0, cap='And he LOVES it.')),
    (1.2, dict(kind='dash_face', world='w', expr='annoyed', turn=0.0, cap='What you WANT to do...')),
    (1.2, dict(kind='pedal_close', world='w', act='gas', hit=0.35, word='PUSH HIM!')),
    (2.4, dict(kind='cine', world='w', cam='track', target=HW, off=(-0.6, 1.8, -7.0), look=(0.0, 1.0, 12.0), f=760, shake=0.06,
               cap='Ride his bumper. Flash the high beams.', capsize=70)),
    (3.0, dict(kind='cine', world='w', cam='track', target=HW, off=(-5.5, 1.2, -1.0), look=(0.0, 0.9, -1.0), f=640, shake=0.05, jolt=(T1, 0.5),
               x='He brake-checks. You hit him...', vdelay=round(V1 - 13.8, 2))),
    (2.6, dict(kind='cine', world='w', cam='top', center=lambda t: (LANES[1], zh(t) - 2.0), H=36.0, f=1000,
               x='...and she hits you. 3-car pile-up.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=20.0, H=9.0, a0=-0.6, w=0.2, f=1000, rewind=(15.0, 6.0))),
    (3.0, dict(kind='cine', cam='track', target=HR, off=(-1.0, 2.2, -8.0), look=(0.0, 0.9, 30.0), f=900, shake=0.04, dt=-4.0, step=1,
               ok='Drop WAY back. 3+ seconds.')),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=22.0, H=10.0, a0=-2.3, w=0.12, f=1000, oz=6.0, dt=-3.5, step=2,
               ok="Pass when safe. Don't look at him.")),
    (2.6, dict(kind='dash_face', expr='focus', turn=0.0, dt=-2.0, step=3, ok='Dangerous? Call 911 when safe.')),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000, dt=-2.0,
               end_card=('Brake-checker? Back off. Get away.', 'Ever been brake-checked? Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(impact(), 1.4, 1.0)
    m.add(screech(1.0, 1100), 0.4, 0.5)
    m.add(brake_squeal(0.9), S[2] + 0.4, 0.5)
    m.add(v8(1.2, lambda u: 0.9), S[5] + 0.3, 0.6)
    m.add(horn(0.5), S[6] + 0.8, 0.5)
    m.add(braam(2.6, 41), S[7], 0.6)
    m.add(slow(screech(1.2, 1150), 0.4), V1 - 0.6, 0.6)
    m.add(slow(impact(), 0.5), V1, 1.0)
    m.add(impact(), V2, 0.9)
    m.add(sad_violin(), S[8] + 0.4, 0.45)
    indicator(m, tm.vt(16.4) - 2.0, tm.vt(T_LC1 + 0.3) - 2.0, 0.4, 0.2)


story = Story('g07_brakecheck', ['Someone brake-checking you?', 'Push back? Watch this'], city_401(), HW, HR,
              [BCW, FOLW, FX1, FX2] + [c for c in TRAF if not (c.xk(0) == LANES[1] and c.z(0) < 0)] + ONC, [BCR, FOLR] + TRAF + ONC,
              shots, DUR, tm=tm, sfx=sfx, unit='kmh')
video = story.video
story.video.overlays.append((story.video.S[10], story.video.E[10], value_tag(gap_r(10), 'GAP', 's', 3.0, 1.5, x=1600, y=300)))
if __name__ == '__main__':
    story.run(lambda: print('impacts', round(T1, 2), round(T2, 2), 'video', round(V1, 2), round(V2, 2), '| closing mph', round((vh(T1 - 0.01) - vl(T1 - 0.01)) * 2.237), round((vf(T2 - 0.01) - vh(T2 - 0.01)) * 2.237)))
