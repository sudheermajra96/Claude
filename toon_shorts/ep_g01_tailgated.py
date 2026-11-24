"""v2 #1 Tailgated (I-35E Dallas). WANT: brake-check him -> he rear-ends you. RIGHT: stay steady, signal, move right, let go."""
from frustkit2 import *

T_BC = 12.2                                     # (wrong) you brake-check
LEAD_V = spd((0, V), (T_BC, V), (T_BC + 1.5, V - 10.5), (99, V - 10.5))
zl, zf, T_IMP, V_REL, vl, vf = follow_sim(LEAD_V, 5.0, 0.9, 7.0, T_BC, bounce=0.6)
FLASH = lambda t: 4.0 < t < 22.0 and (t * 3.0) % 1 < 0.5
EP.glare = FLASH


def hero_expr(t):
    return 'calm' if t < 4.5 else 'annoyed'


HW = SimCar(LANES[1], zl, vl, HERO_COL, occ=occ_of('hero', lambda t: 'shock' if t > T_IMP - 0.3 else hero_expr(t)), damage=[('back', T_IMP)],
            blink=lambda t: 'B' if t > T_IMP + 2 and (t * 1.5) % 1 < 0.5 else None)
TGW = SimCar(LANES[1], zf, vf, '#30333d', occ=occ_of('husb', lambda t: 'shock' if t > T_IMP - 0.4 else 'annoyed'), flash=lambda t: FLASH(t) and t < T_IMP,
             damage=[('front', T_IMP)], mark=lambda t: True)
FX = CrashFX(T_IMP, lambda t: (LANES[1], 0.7, zl(t) - 2.25))

T_SIG, T_LC0, T_LC1 = 20.0, 20.8, 22.2
HR = hero_car(lane_key((0, 1), (T_LC0, 1), (T_LC1, 2), (99, 2)), const(V), lambda t: 'calm' if t < 4.5 else ('focus' if t < 22.5 else 'smile'),
              blink=blinks((T_SIG, T_LC1 + 0.3, 'R')), za=zl(0.0))
TGR = Veh(LANES[1], spd((0, V), (22.2, V), (23.4, 36.0), (99, 36.0)), 0.0, zf(0.0), '#30333d', occ=occ_of('husb', lambda t: 'annoyed'),
          flash=FLASH, mark=lambda t: True)
TRAF = filler([(0, 40), (0, -50), (2, 70), (2, -90), (3, 20), (3, -30), (1, 140), (0, 160), (3, 140), (2, 220)])
ONC = oncoming()
Z_IMP = zl(T_IMP) - 2.25
SM0 = T_IMP - 0.35
tm = TimeMap([(SM0, SM0 + 3.0, 0.35)])

shots = layout([
    (2.6, dict(kind='cine', world='w', cam='track', target=HW, off=(-5.0, 1.1, -3.5), look=(0, 0.9, -2.0), f=700, dt=T_IMP - 1.7, shake=0.1,
               jolt=(T_IMP, 0.6), hook='Brake-check him?!')),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=22.0, H=9.0, a0=-0.8, w=0.16, f=1000, oz=-2.0, loc='I-35E, Dallas, Texas',
               cap='Rush hour. 65 mph. All good...')),
    (2.8, dict(kind='cine', cam='track', target=HR, off=(0.35, 0.75, -2.7), look=(0.0, 1.0, -14.0), f=620, shake=0.06,
               cap='...then HE glues to your bumper. 5 metres.', capsize=68)),
    (1.6, dict(kind='dash_face', car=TGR, who='husb', expr='annoyed', turn=lambda lt: 0.1 * math.sin(lt * 8), cap='Flashing. Honking. Yelling.')),
    (1.6, dict(kind='dash_face', world='w', expr='annoyed', turn=lambda lt: 0.3, cap='What you WANT to do...')),
    (SM0 - 11.6, dict(kind='pedal_close', world='w', act='brake', hit=T_BC - 11.6 + 0.0, word='BRAKE-CHECK!')),
    (3.0, dict(kind='cine', world='w', cam='track', target=HW, off=(-4.3, 0.9, -1.0), look=(0, 0.8, -3.0), f=700, shake=0.05,
               jolt=(T_IMP, 0.5), x='WRONG: you brake-check, he hits YOU', vdelay=1.0)),
    (2.6, dict(kind='cine', world='w', cam='heli', target=HW, R=18.0, H=8.0, a0=2.6, w=-0.1, f=950, oz=-4.0,
               x='Crash. Injuries. YOU can be charged too.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=20.0, H=9.0, a0=-0.8, w=0.2, f=1000, oz=-2.0, rewind=(16.6, 10.0))),
    (3.0, dict(kind='interior_mirror', f=900, step=1, ok="Stay steady. Don't brake. Don't react.")),
    (3.0, dict(kind='cine', cam='heli', target=HR, R=20.0, H=9.0, a0=0.7, w=-0.14, f=1000, oz=-2.0, step=2, ok='Signal and move right when clear.')),
    (2.6, dict(kind='cine', cam='tele', target=HR, off=(9.0, 3.0, 55.0), tz=-6.0, f=2400, step=3, ok="Let him pass. It's not your race.")),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000,
               end_card=('Tailgated? Stay calm. Move over.', 'Have you ever brake-checked someone? Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(screech(0.9, 1100), 0.6, 0.6)
    m.add(crash(), 1.7, 0.8) if 'crash' in globals() else m.add(impact(), 1.7, 0.9)
    for t in (S[2] + 0.4, S[2] + 1.3, S[2] + 1.7, S[3] + 0.2, S[3] + 0.8):
        m.add(horn(0.4), t, 0.6)
    m.add(v8(2.6, lambda u: 0.8), S[2], 0.35)
    vi = tm.vt(T_IMP)
    m.add(slow(screech(1.2, 1150), 0.35), S[6] + 0.1, 0.6)
    m.add(slow(impact(), 0.5), vi, 1.0)
    m.add(braam(2.6, 41), S[6], 0.6)
    m.add(sad_violin(), S[7] + 0.3, 0.45)
    indicator(m, tm.vt(T_SIG), tm.vt(T_LC1 + 0.3), 0.45, 0.2)
    m.add(v8(2.0, lambda u: 0.6 + 0.4 * min(1, u)), tm.vt(22.2), 0.5)
    m.add(car_pass(1.4, 0.5, 120), S[11] + 0.6, 0.8, pans(1.4, -0.7, 0.7))


story = Story('g01_tailgated', ['Someone tailgating you?', 'Watch what happens if you react'], city_dallas(), HW, HR,
              [TGW, FX] + TRAF + ONC, [TGR] + TRAF + ONC, shots, DUR, tm=tm, sfx=sfx)
video = story.video
if __name__ == '__main__':
    story.run(lambda: print('impact', round(T_IMP, 2), 'closing mph', round(V_REL * 2.237, 1), 'video', round(tm.vt(T_IMP), 2)))
