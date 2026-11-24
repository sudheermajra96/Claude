"""v2 #4 Rubbernecker (I-70 Golden, Colorado). WANT: ride her bumper, honk, and glance at the crash yourself ->
you rear-end her. RIGHT (rewind to the start): keep 3 seconds, brake early and smooth, eyes on your own road."""
from frustkit2 import *

T_R = 9.9
RS = spd((0, V), (T_R, V), (T_R + 4.25, 12.0), (14.5, 12.0), (17.0, V), (99, V))
zl, zf, T_IMP, V_REL, vl, vf = follow_sim(RS, 8.0, 1.8, 7.0, T_R, bounce=0.5)
RUBX = LANES[0]
rub_occ = occ_of('lady', lambda t: 'shock' if t > T_IMP - 0.3 else 'calm', look_fn=lambda t: -1.1 * smooth((t - 7.6) / 0.5) if 7.6 < t < 13 else 0.0)
RUBW = SimCar(RUBX, zl, vl, '#7a4fd0', occ=rub_occ, mark=lambda t: True, damage=[('back', T_IMP)],
              blink=lambda t: 'B' if t > T_IMP + 2 and (t * 1.5) % 1 < 0.5 else None)
HW = SimCar(RUBX, zf, vf, HERO_COL, occ=occ_of('hero', lambda t: 'annoyed' if t < T_IMP - 0.4 else 'shock',
                                              look_fn=lambda t: -1.0 if 8.6 < t < T_IMP - 0.2 else 0.0), damage=[('front', T_IMP)])
FX = CrashFX(T_IMP, lambda t: (RUBX, 0.7, zl(t) - 2.25))
Z_CR = zl(10.5)
WRECK = [Veh(-14.6, const(0.0), 0.0, Z_CR + 3.0, '#37b26c', damage=[('back', -9)], blink=lambda t: 'B' if (t * 1.5) % 1 < 0.5 else None,
             brake=lambda t: 0.0),
         Veh(-14.6, const(0.0), 0.0, Z_CR - 3.2, '#c9c9d6', damage=[('front', -9)], brake=lambda t: 0.0),
         Veh(-14.6, const(0.0), 0.0, Z_CR - 13.0, '#f4f4f6', police=lambda t: True, brake=lambda t: 0.0)]
# right world: same lady, our hero 3 seconds back, brakes early and smoothly
RUBR = Veh(RUBX, RS, 0.0, zl(0.0), '#7a4fd0', occ=rub_occ, mark=lambda t: True)
HR = hero_car(const(RUBX), spd((0, V), (10.6, V), (14.8, 12.5), (16.0, 12.5), (18.5, V), (99, V)),
              lambda t: 'calm' if t < 8 else ('focus' if t < 15 else 'smile'), za=zl(0.0) - 4.5 - 3.0 * V)
SLOW = spd((0, V), (9.0, V), (10.5, V - 8.0), (13.5, V - 8.0), (15.5, V), (99, V))
NOP = [c for c in COLS if c != '#7a4fd0']
TRAF = filler([(1, 20), (1, -45), (2, 50), (2, -20), (3, 5), (3, -70), (1, 140), (2, 180)], speed=SLOW, cols=NOP)
ONC = oncoming()
tm = TimeMap([(10.4, 13.4, 0.25), (13.4, 16.4, 0.4)])
VI = tm.vt(T_IMP)


def gap_r(lt, i):
    t = tm.wt(story.video.S[i] + lt) + story.video.shots[i].get('dt', 0.0) if False else tm.wt(story.video.S[i] + lt)
    return (RUBR.z(t) - 2.25 - HR.z(t) - 2.25) / max(1.0, HR.speed(t))


shots = layout([
    (2.4, dict(kind='cine', world='w', cam='track', target=RUBW, off=(-6.0, 1.4, 5.0), look=(0.0, 0.8, -3.0), f=720, dt=T_IMP - 1.4,
               jolt=(T_IMP, 0.3), hook='Too close to stop?!')),
    (2.6, dict(kind='cine', world='w', cam='crane', target=HW, ox=5.0, oz0=-12.0, oz1=-22.0, y0=18.0, y1=5.0, tz=10.0, f=1000,
               loc='I-70, Golden, Colorado', cap="Heading into the Rockies. You're close behind her...", capsize=64)),
    (2.6, dict(kind='cine', world='w', cam='fixed', pos=(-17.0, 2.3, Z_CR - 22.0), target_pt=(-6.0, 1.0, Z_CR - 75.0), f=780,
               cap='A crash on the OTHER side...')),
    (2.8, dict(kind='dash_face', world='w', car=RUBW, who='lady', expr='shock', turn=lambda lt: -0.7 * smooth(lt / 0.6),
               cap='...she slows right down to stare.')),
    (1.6, dict(kind='horn_close', world='w', hits=(0.25, 0.7, 1.15), cap='What you WANT: honk at her!')),
    (1.4, dict(kind='dash_face', world='w', expr='annoyed', turn=lambda lt: -0.8 * smooth(lt / 0.4), cap='...and you look at the crash too.')),
    (3.0, dict(kind='cine', world='w', cam='track', target=HW, off=(-3.6, 0.9, 0.5), look=(0.6, 0.8, 5.0), f=640, shake=0.04,
               jolt=(T_IMP, 0.6), x='Two seconds of looking... BANG.', vdelay=round(VI - 13.4, 2))),
    (2.4, dict(kind='cine', world='w', cam='heli', target=HW, R=16.0, H=7.0, a0=2.2, w=-0.12, f=950, oz=2.0,
               x='You rear-ended her. Your fault.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=22.0, H=10.0, a0=-0.6, w=0.2, f=1000, rewind=(16.0, 2.0))),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=26.0, H=12.0, a0=-0.4, w=0.08, f=1000, oz=40.0, dt=-6.0, step=1,
               ok='Keep 3 seconds behind. Always.')),
    (3.0, dict(kind='interior_mirror', f=1000, mirror=False, dt=-6.0, step=2, ok='She brakes? You brake early and smooth.')),
    (2.8, dict(kind='cine', cam='track', target=HR, off=(-2.6, 1.6, 2.0), look=(0.4, 0.9, 9.0), f=720, shake=0.05, flare=0.4, dt=-6.0, step=3,
               ok='Eyes on YOUR road, not the crash.')),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000, dt=-6.0,
               end_card=("Don't rubberneck. Keep 3 seconds.", 'Do you slow down to look? Be honest! Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(screech(0.8, 1100), 0.4, 0.6)
    m.add(impact(), 1.4, 0.9)
    for k in np.arange(S[2], E[3], 0.38):
        m.add(click(), k, 0.06)
    m.add(brake_squeal(1.2), S[3] + 0.2, 0.5)
    for k in (0.25, 0.7, 1.15):
        m.add(horn(0.35), S[4] + k, 0.8)
    m.add(braam(2.6, 41), S[6], 0.6)
    m.add(slow(screech(1.0, 1100), 0.4), VI - 0.9, 0.6)
    m.add(slow(impact(), 0.5), VI, 1.0)
    m.add(sad_violin(), S[7] + 0.4, 0.45)
    m.add(brake_squeal(1.0), S[10] + 0.6, 0.25)


story = Story('g04_rubberneck', ['Driver brakes to stare at a crash?', "Too close? Watch this"], city_golden((1500.0, 2300.0)), HW, HR,
              [RUBW, FX] + WRECK + TRAF + ONC, [RUBR] + WRECK + TRAF + ONC, shots, DUR, tm=tm, sfx=sfx)
video = story.video
story.video.overlays.append((story.video.S[9], story.video.E[9], value_tag(lambda lt: 3.0, 'GAP', 's', 2.9, 1.5, x=1600, y=300)))
if __name__ == '__main__':
    story.run(lambda: print('impact', round(T_IMP, 2), 'closing mph', round(V_REL * 2.237, 1), 'video', round(VI, 2),
                            '| right min gap s', round(min((RUBR.z(t) - 4.5 - HR.z(t)) / max(1, HR.speed(t)) for t in np.arange(0, 25, 0.05)), 2)))
