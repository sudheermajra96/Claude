"""v2 #3 Blocked lane change (I-35E Dallas). WANT: force your way in -> sideswipe, both cars wrecked.
RIGHT: don't force it, ease off and let him go, merge in behind him."""
from frustkit2 import *

VS = 25.0
T_SIG = 6.4
T_F, T_HIT = 10.5, 10.9
BS0 = [(0, VS), (T_SIG, VS), (7.3, 29.0), (8.6, VS)]
SEMI = Veh(LANES[2], const(VS), 0.0, 2.25 + 30.0 + 15.5, '#2f6f9f', kind='semi', trailer=('#f4f4f6', '#e0393e', 'LONE STAR'), cab='#c0392b')


def angry(t):
    return 'calm' if t < 7.4 else 'annoyed'


# wrong world: force it
HW = hero_car(Key([(0, LANES[2]), (T_F, LANES[2]), (T_HIT, 7.15), (11.3, 7.9), (99, 7.9)]),
              spd((0, VS), (T_HIT, VS), (T_HIT + VS / 6.0, 0.0), (99, 0.0)), lambda t: 'shock' if t > T_HIT - 0.2 else angry(t),
              blink=blinks((T_SIG, T_F, 'L')))
BW = Veh(Key([(0, LANES[1]), (T_HIT, LANES[1]), (11.3, 4.6), (99, 4.6)]), spd(*BS0, (T_HIT, VS), (T_HIT + VS / 6.0, 0.0), (99, 0.0)),
         T_HIT, HW.z(T_HIT), '#f2a541', occ=occ_of('husb', lambda t: 'shock' if t > T_HIT - 0.2 else 'smug'), mark=lambda t: True,
         blink=lambda t: 'B' if t > T_HIT + 2 and (t * 1.5) % 1 < 0.5 else None)
FX = CrashFX(T_HIT, lambda t: (6.2, 0.8, HW.z(T_HIT)))
# right world
T_LC0, T_LC1 = 18.5, 19.9
HR = hero_car(lane_key((0, 2), (T_LC0, 2), (T_LC1, 1), (99, 1)), spd((0, VS), (15.0, VS), (16.0, 21.0), (18.0, 21.0), (21.0, V), (99, V)),
              lambda t: angry(t) if t < 14.5 else ('focus' if t < 20 else 'smile'), blink=blinks((T_SIG, 11.5, 'L'), (17.8, T_LC1 + 0.3, 'L')))
BR = Veh(LANES[1], spd(*BS0, (16.0, VS), (17.2, 34.0), (99, 34.0)), T_HIT, HW.z(T_HIT), '#f2a541', occ=occ_of('husb', lambda t: 'smug'),
         mark=lambda t: True)
NOOR = [c for c in COLS if c != '#f2a541']
TRAF = filler([(0, 30), (0, -40), (0, 110), (3, 15), (3, -60), (3, 90), (3, -150), (0, 200)], speed=V, cols=NOOR)
ONC = oncoming()
tm = TimeMap([(9.8, 12.4, 0.25), (12.4, 15.4, 0.4)])
VH = tm.vt(T_HIT)

shots = layout([
    (2.6, dict(kind='cine', world='w', cam='track', target=HW, off=(0.0, 3.4, -5.0), look=(-1.6, 1.0, 9.0), f=700, dt=T_HIT - 1.6,
               jolt=(T_HIT, 0.5), hook='Force your way in?!')),
    (2.6, dict(kind='cine', cam='tele', target=HR, off=(3.0, 4.0, -95.0), tz=12.0, f=2600, loc='I-35E, Dallas, Texas',
               cap='Stuck behind a slow truck...')),
    (2.6, dict(kind='dash_face', car=BR, who='husb', expr='smug', turn=lambda lt: 0.5, cap='You signal. He speeds up to block you.', capsize=70)),
    (2.0, dict(kind='interior_mirror', f=850, blink=True, mirror_glow=lambda t: True, cap='Again. And again.')),
    (1.4, dict(kind='dash_face', world='w', expr='annoyed', turn=lambda lt: -0.5, cap='What you WANT to do...')),
    (1.2, dict(kind='pedal_close', world='w', act='gas', hit=0.4, word='SQUEEZE IN!')),
    (3.0, dict(kind='cine', world='w', cam='track', target=HW, off=(-1.9, 1.5, -8.5), look=(-1.0, 0.8, 4.0), f=680, shake=0.05, flare=0.3,
               jolt=(T_HIT, 0.6), x="You force it. He doesn't move.", vdelay=1.2)),
    (2.4, dict(kind='cine', world='w', cam='top', center=lambda t: (6.5, HW.z(t)), H=26.0, f=1000,
               x='Sideswipe. Both cars wrecked.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=20.0, H=9.0, a0=-0.6, w=0.2, f=1000, rewind=(14.0, 7.0))),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=22.0, H=10.0, a0=0.6, w=-0.12, f=1000, oz=4.0, step=1, ok="Don't force it. Ease off.")),
    (3.0, dict(kind='interior_mirror', f=820, blink=True, step=2, ok='Let him go. Signal again.')),
    (2.8, dict(kind='cine', cam='tele', target=HR, off=(10.0, 3.5, -55.0), tz=6.0, f=2300, step=3, ok='Merge in behind him. Done.')),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000,
               end_card=("Blocked? Don't force it.", 'Has someone blocked YOU like this? Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(lp(noise(int(DUR * SR)), 140), 0, 0.22)
    m.add(impact(), 1.6, 0.9)
    m.add(screech(1.0, 900), 1.6, 0.5)
    indicator(m, T_SIG, 9.8, 0.4, -0.2)
    m.add(v8(2.0, lambda u: 0.6 + 0.4 * min(1, u / 0.8)), 6.6, 0.5)
    m.add(horn(0.4), S[3] + 1.2, 0.4)
    m.add(v8(1.4, lambda u: 0.9), S[5] + 0.3, 0.6)
    m.add(braam(2.6, 41), S[6], 0.6)
    m.add(slow(impact(), 0.5), VH, 1.0)
    m.add(slow(screech(1.6, 800), 0.45), VH, 0.6)
    m.add(sad_trombone(), S[7] + 0.6, 0.45)
    indicator(m, tm.vt(17.8), tm.vt(T_LC1 + 0.3), 0.4, -0.2)


story = Story('g03_blocker', ['Someone blocks your lane change?', 'Forcing it? Watch this'], city_dallas((900.0, 1700.0)), HW, HR,
              [SEMI, BW, FX] + [c for c in TRAF if not (c.xk(0) in (LANES[0],) and c.z(0) < 0)] + ONC, [SEMI, BR] + TRAF + ONC, shots, DUR, tm=tm,
              sfx=sfx)
video = story.video
if __name__ == '__main__':
    story.run(lambda: print('hit video', round(VH, 2), '| contact', lateral_gap(HW, BW, 9, 12)))
