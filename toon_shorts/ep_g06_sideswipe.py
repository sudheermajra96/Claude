"""v2 #6 She merges into you (I-70 Golden). WANT: speed up and ride beside her to 'teach her' -> she merges again,
you're in her blind spot, both cars spin out. RIGHT: brake + tap the horn, stay out of blind spots, let her in."""
from frustkit2 import *


class SpinVeh(Veh):
    def __init__(self, *a, spin=None, **k):
        super().__init__(*a, **k)
        self.spin = spin or (lambda t: 0.0)

    def pose(self, t):
        x, z, h = super().pose(t)
        return x, z, h + self.spin(t)


T_M = 7.2
T_HIT = 12.25
# shared: near miss at 7.2-8.6 (she drifts in, hero brakes and dodges left)
HX0 = [(0, LANES[1]), (7.3, LANES[1]), (7.8, LANES[1] - 0.65), (8.8, LANES[1] - 0.65), (9.8, LANES[1])]
MX0 = [(0, LANES[2]), (T_M, LANES[2]), (7.9, 7.0), (8.6, LANES[2])]
m_occ = occ_of('lady', lambda t: 'shock' if 7.8 < t < 9.5 or t > T_HIT - 0.2 else 'calm', look_fn=lambda t: -0.8 if 7.9 < t < 9.0 else 0.0)
# wrong world: hero speeds up to ride beside her, she merges again at 12.0
HW = SpinVeh(Key(HX0 + [(T_HIT, LANES[1]), (13.4, 3.0), (99, 3.0)]),
             spd((0, V), (7.4, V), (8.4, V - 5.0), (9.6, V - 5.0), (10.6, V + 5.0), (11.3, V + 5.0), (11.6, V), (T_HIT, V), (T_HIT + V / 7.0, 0.0), (99, 0.0)),
             T_HIT, 0.0, HERO_COL, occ=occ_of('hero', lambda t: 'calm' if t < 7.3 else ('shock' if t < 8.9 or t > T_HIT - 0.2 else 'annoyed'),
                                              look_fn=lambda t: 0.7 if 10.8 < t < T_HIT else 0.0),
             spin=lambda t: -0.9 * smooth((t - T_HIT) / 1.2) if t > T_HIT else 0.0)
MW = SpinVeh(Key(MX0 + [(11.9, LANES[2]), (T_HIT, 7.15), (13.4, 9.6), (99, 9.6)]), spd((0, V), (T_HIT, V), (T_HIT + V / 7.0, 0.0), (99, 0.0)),
             T_HIT, 0.0, '#2f6f73', occ=m_occ, mark=lambda t: True, spin=lambda t: 0.7 * smooth((t - T_HIT) / 1.2) if t > T_HIT else 0.0,
             blink=lambda t: 'B' if t > T_HIT + 2.5 and (t * 1.5) % 1 < 0.5 else None)
FX = CrashFX(T_HIT, lambda t: (6.2, 0.8, HW.z(T_HIT)))
# right world: brake, let her in (she signals and merges ahead at 13.6-15.0)
HR = hero_car(Key(HX0 + [(99, LANES[1])]), spd((0, V), (7.4, V), (8.4, V - 5.0), (12.0, V - 5.0), (13.4, V - 2.0), (99, V - 2.0)),
              lambda t: 'calm' if t < 7.3 else ('shock' if t < 8.9 else ('focus' if t < 15 else 'smile')))
MR = Veh(Key(MX0 + [(13.6, LANES[2]), (15.0, LANES[1]), (99, LANES[1])]), const(V), T_M, HW.z(T_M) + 3.0, '#2f6f73', occ=m_occ,
         mark=lambda t: True, blink=blinks((12.8, 15.2, 'L')))
HR_OFF = HW.z(0.0) - HR.z(0.0)
HR = hero_car(Key(HX0 + [(99, LANES[1])]), spd((0, V), (7.4, V), (8.4, V - 5.0), (12.0, V - 5.0), (13.4, V - 2.0), (99, V - 2.0)),
              lambda t: 'calm' if t < 7.3 else ('shock' if t < 8.9 else ('focus' if t < 15 else 'smile')), za=HW.z(0.0))
MW_ANCHOR_CHECK = MW.z(T_M) - HW.z(T_M)
NOT = [c for c in COLS if c != '#2f6f73']
TRAF = filler([(0, 90), (3, 10), (3, -40), (3, 70), (2, 120), (1, 160), (0, 200)], speed=V, cols=NOT)
ONC = oncoming()
tm = TimeMap([(9.4, 11.8, 0.25), (13.2, 16.2, 0.4)])
VH = tm.vt(T_HIT)


def blind_zone(ctx, view, t, lt):
    x, z, h = MR.pose(t)
    a = smooth(lt / 0.4)
    pts = [view.pt(P) for P in ((x - 1.0, 0.03, z - 1.0), (x - 4.2, 0.03, z - 1.0), (x - 4.2, 0.03, z - 9.0), (x - 1.0, 0.03, z - 6.5))]
    if all(pts):
        poly(ctx, pts)
        setc(ctx, hexc('#ff4b4b'), 0.38 * a)
        ctx.fill()
        c = view.pt((x - 2.6, 0.03, z - 4.5))
        text_center(ctx, 'BLIND SPOT', c[0], c[1], 58, (1, 1, 1), a=a)


shots = layout([
    (2.4, dict(kind='cine', world='w', cam='top', center=lambda t: (6.0, HW.z(t) + 2.0), H=28.0, f=1000, dt=T_HIT - 1.3, hook='Teach her a lesson?')),
    (2.6, dict(kind='cine', cam='tele', target=HR, off=(-6.0, 3.0, -80.0), tx=1.5, tz=3.0, f=2400, loc='I-70, Golden, Colorado',
               cap='Cruising next to her...')),
    (2.4, dict(kind='cine', cam='track', target=HR, off=(1.6, 1.9, -9.0), look=(-0.2, 0.9, 6.0), f=720, shake=0.07, jolt=(7.7, 0.3), flare=0.4,
               cap='She moves over... right into you!')),
    (2.0, dict(kind='dash_face', car=MR, who='lady', expr='shock', turn=lambda lt: -0.6, cap="She never even looked.")),
    (1.2, dict(kind='dash_face', world='w', expr='annoyed', turn=0.45, cap='What you WANT to do...')),
    (1.2, dict(kind='pedal_close', world='w', act='gas', hit=0.35, word='CATCH HER!')),
    (1.4, dict(kind='horn_close', world='w', hits=(0.25, 0.7, 1.05), cap='Ride beside her. Honk!')),
    (3.0, dict(kind='cine', world='w', cam='track', target=HW, off=(-2.6, 0.6, -2.5), look=(2.0, 0.8, 4.0), f=640, shake=0.05, jolt=(T_HIT, 0.6),
               x="You're in her blind spot. Again.", vdelay=round(VH - 13.2 - 0.3, 2))),
    (2.4, dict(kind='cine', world='w', cam='heli', target=HW, R=14.0, H=12.0, a0=-0.2, w=0.1, f=950, x='Both cars spin out.')),
    (1.6, dict(kind='cine', world='w', cam='heli', target=HW, R=18.0, H=8.0, a0=-0.6, w=0.2, f=1000, rewind=(16.0, 7.0))),
    (3.0, dict(kind='cine', cam='top', center=lambda t: (7.0, HR.z(t) + 2.0), H=32.0, f=1000, dt=-9.4, post=blind_zone, step=1,
               ok='Brake. Tap the horn. Make room.')),
    (3.0, dict(kind='interior_mirror', f=900, mirror=False, dt=-7.3, step=2, ok='She signals now. Let her in.')),
    (2.6, dict(kind='cine', cam='heli', target=HR, R=22.0, H=10.0, a0=2.4, w=-0.14, f=1000, oz=8.0, dt=-6.0, step=3,
               ok="Never ride in someone's blind spot.")),
    (3.0, dict(kind='cine', cam='crane', target=HR, ox=6.0, oz0=-26.0, oz1=-36.0, y0=2.0, y1=22.0, tz=160.0, f=1000, dt=-6.0,
               end_card=('Stay out of blind spots. Let it go.', 'Has this happened to you? Comment!'))),
])
DUR = shots[-1]['end']


def sfx(m, S, E):
    m.add(impact(), 1.3, 0.9)
    m.add(screech(1.8, 800), 1.3, 0.6)
    m.add(horn(0.5), 7.7, 0.8, -0.2)
    m.add(brake_squeal(1.0), 7.6, 0.5)
    m.add(v8(1.2, lambda u: 0.9), S[5] + 0.3, 0.6)
    for k in (0.25, 0.7, 1.05):
        m.add(horn(0.35), S[6] + k, 0.8)
    m.add(braam(2.6, 41), S[7], 0.6)
    m.add(slow(impact(), 0.5), VH, 1.0)
    m.add(slow(screech(2.2, 700), 0.4), VH + 0.1, 0.7)
    m.add(sad_trombone(), S[8] + 0.6, 0.45)
    m.add(horn(0.25), S[10] + 0.6, 0.5)
    indicator(m, S[11] + 0.2, E[11], 0.35, 0.3)


story = Story('g06_sideswipe', ['Driver merges INTO you?', 'Getting even? Watch this'], city_golden((1000.0, 1800.0)), HW, HR,
              [MW, FX] + TRAF + ONC, [MR] + TRAF + ONC, shots, DUR, tm=tm, sfx=sfx)
video = story.video
if __name__ == '__main__':
    story.run(lambda: print('hit video', round(VH, 2), '| contact', lateral_gap(HW, MW, 11, 13), '| her offset at near miss',
                            round(MW_ANCHOR_CHECK, 2), round(MR.z(T_M) - HR.z(T_M), 2)))
