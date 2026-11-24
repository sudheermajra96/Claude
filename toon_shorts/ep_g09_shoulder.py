"""v2 #9 Shoulder driver in a jam (Highway 401 Toronto). WANT: swerve onto the shoulder to block him -> he can't stop,
crash, and YOU get a ticket too. RIGHT: stay in your lane, the shoulder is for emergencies, police handle it."""
from frustkit2 import *

VJ = 6.3
T_SW0, T_SW1, T_BR = 7.4, 8.2, 8.0
T_PASS = 7.5
SS = spd((0, 18.0), (11.0, 18.0), (12.5, 0.0), (99, 0.0))
QUEUE_R = [Veh(LANES[l], const(VJ), 0.0, z + 5.0 * l, COLS[(int(z) // 12 + l) % 10]) for l in range(4) for z in np.arange(-48.0, 240.0, 12.0)
           if not (l == 3 and abs(z + 15.0) < 8.0)]
# ---------- right world
HR = hero_car(const(LANES[3]), const(VJ), lambda t: 'calm' if t < 6.0 else ('annoyed' if t < 12.0 else ('focus' if t < 17.0 else 'smile')))
s_occ = occ_of('husb', lambda t: 'smug' if t < 8.3 else 'shock')
SR = Veh(SHOULDER, SS, T_PASS, HR.z(T_PASS), '#e8e8ee', mark=lambda t: True, occ=s_occ, blink=lambda t: 'B' if t > 13.0 and (t * 1.5) % 1 < 0.5 else None)
Z_STOP = SR.z(30)
PCAR = Veh(SHOULDER, const(0.0), 0.0, Z_STOP + 8.5, '#f4f4f6', police=lambda t: t > 10.4, brake=lambda t: 0.0)
COP = Trooper(17.0, Z_STOP + 0.6, lambda t: ('write', t % 3), None, lambda t: 'flat')
COP.visible = lambda t: t > 13.8
# ---------- wrong world: block him
HXW = Key([(0, LANES[3]), (T_SW0, LANES[3]), (T_SW1, 14.6), (99, 14.6)])
HSW = spd((0, VJ), (T_SW0, VJ), (T_SW1, 4.0), (8.9, 2.0), (8.95, 5.5), (9.7, 0.0), (99, 0.0))
HW = hero_car(HXW, HSW, lambda t: 'annoyed' if t < 8.7 else 'shock', damage=[('back', 8.9)],
              blink=lambda t: 'B' if t > 10.0 and (t * 1.5) % 1 < 0.5 else None)
SSW = spd((0, 18.0), (T_BR, 18.0), (8.9, 10.8), (8.95, 3.5), (9.35, 0.0), (99, 0.0))
SW = Veh(SHOULDER, SSW, T_PASS, HR.z(T_PASS), '#e8e8ee', mark=lambda t: True, occ=s_occ, damage=[('front', 8.9)])
_z_hit = HW.z(8.9) - 4.5
SW = Veh(SHOULDER, SSW, 8.9, _z_hit, '#e8e8ee', mark=lambda t: True, occ=s_occ, damage=[('front', 8.9)])
T_I = 8.9
FX = CrashFX(T_I, lambda t: (15.1, 0.7, HW.z(T_I) - 2.25))
COPW = Trooper(12.9, 0.0, lambda t: ('write', t % 3), None, lambda t: 'flat')
COPW.zz = HW.z(20.0) + 1.0
COPW.visible = lambda t: t > 11.0
QUEUE_W = [c for c in QUEUE_R if not (c.xk(0) == LANES[3] and -40 < c.z(0) < 0)]
tm = TimeMap([(7.0, 8.2, 0.25), (9.4, 12.4, 0.35)])
VI = tm.vt(T_I)


def red_shoulder(ctx, view, t, lt):
    a = smooth(lt / 0.4)
    z = HR.z(t)
    pts = [view.pt((14.0, 0.02, z - 30)), view.pt((17.5, 0.02, z - 30)), view.pt((17.5, 0.02, z + 120)), view.pt((14.0, 0.02, z + 120))]
    if all(pts):
        poly(ctx, pts)
        setc(ctx, hexc('#ff4b4b'), 0.3 * a)
        ctx.fill()


shots = layout([
    (2.4, dict(kind='cine', world='w', cam='track', target=SW, off=(1.5, 1.6, -9.0), look=(-1.0, 1.0, 8.0), f=740, dt=T_I - 1.5, jolt=(T_I, 0.5),
               hook='Block him?!')),
    (2.6, dict(kind='cine', cam='heli', target=HR, R=30.0, H=14.0, a0=-0.6, w=0.12, f=1000, oz=14.0, loc='Highway 401, Toronto, Ontario',
               cap='Stop-and-go on the 401...')),
    (2.0, dict(kind='interior_mirror', f=850, mirror_glow=lambda t: True, cap="Someone's flying up... on the SHOULDER.", capsize=70)),
    (1.2, dict(kind='dash_face', world='w', expr='annoyed', turn=0.6, cap='What you WANT to do...')),
    (1.2, dict(kind='cine', world='w', cam='top', center=lambda t: (13.5, HW.z(t) - 4.0), H=30.0, f=1000, cap='Swerve out. Block him!')),
    (3.0, dict(kind='cine', world='w', cam='track', target=HW, off=(4.4, 0.8, -1.0), look=(0.0, 0.8, -4.0), f=640, shake=0.04, jolt=(T_I, 0.6),
               x="He can't stop in time.", vdelay=round(VI - 9.4, 2))),
    (2.8, dict(kind='cine', world='w', cam='fixed', pos=(11.2, 1.7, HW.z(20.0) + 7.0), target_pt=(13.6, 1.2, HW.z(20.0) - 2.0), f=700,
               x='Crash. And YOU get a ticket too.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=24.0, H=12.0, a0=-0.6, w=0.2, f=1000, rewind=(13.0, 5.0))),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=24.0, H=11.0, a0=-0.5, w=0.1, f=1000, oz=4.0, dt=-6.5, step=1,
               ok='Stay in your lane. Never block or chase.')),
    (3.0, dict(kind='cine', cam='top', center=lambda t: (9.0, HR.z(t) + 30.0), H=60.0, f=1000, post=red_shoulder, dt=-6.0, step=2,
               ok='Shoulder = emergencies only.')),
    (2.8, dict(kind='cine', cam='fixed', pos=(17.4, 2.0, Z_STOP + 22.0), target_pt=(14.0, 1.0, Z_STOP - 6.0), f=820, dt=-6.0, step=3,
               ok='Police handle it. You just drive.')),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=-4.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=120.0, f=1000, dt=-6.0,
               end_card=('Shoulder cheater? Stay in your lane.', 'Have you seen this on your highway? Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(v8(2.4, lambda u: 0.9), 0.0, 0.5)
    m.add(screech(1.0, 1100), 0.6, 0.6)
    m.add(impact(), 1.5, 0.9)
    m.add(v8(2.0, lambda u: 0.9), S[2], 0.5)
    m.add(horn(0.5), S[2] + 1.4, 0.5)
    m.add(braam(2.6, 41), S[5], 0.6)
    m.add(slow(screech(1.2, 1100), 0.35), S[5] + 0.1, 0.6)
    m.add(slow(impact(), 0.5), VI, 1.0)
    from street import siren_whoop
    m.add(siren_whoop(2), S[6] + 0.2, 0.5)
    m.add(sad_trombone(), S[6] + 1.0, 0.45)
    m.add(car_pass(1.4, 0.5, 120), S[8] + 0.6, 0.7, pans(1.4, -0.3, 0.8))
    m.add(siren_whoop(2), S[10] + 0.3, 0.4)


story = Story('g09_shoulder', ['Someone skips traffic on the shoulder?', 'Block him? Watch this'], city_401((Z_STOP + 500.0, Z_STOP + 1300.0)),
              HW, HR, [SW, FX, COPW] + QUEUE_W + oncoming(), [SR, PCAR, COP] + QUEUE_R + oncoming(), shots, DUR, tm=tm, sfx=sfx, unit='kmh')
video = story.video
if __name__ == '__main__':
    story.run(lambda: print('impact video', round(VI, 2), '| closing kmh', round((SW.speed(T_I - 0.01) - HW.speed(T_I - 0.01)) * 3.6),
                            '| rear contact gap', round(HW.z(T_I) - 2.25 - SW.z(T_I) - 2.25, 2), '| lateral', round(HW.xk(T_I) - SHOULDER, 2)))
