"""04 - ALWAYS stop for people at crossings (day street)."""
from kit import *

engine.DAY = True
spA = const(11)
spB = Key([(10.9, 11), (12.4, 11), (15.4, 0), (18.6, 0), (20.4, 7), (30, 9)], 'lin')
world = StreetWorld(25, [(0, 66, spA), (10.9, 35.5, spB)], camx=const(DRIVER_X))
world.headlights = const(0)
world.ego_brake = Key([(12.4, 0), (12.5, 1), (18.6, 1), (18.7, 0)], 'step')
ZC = ZI - 8.1          # centre of the zebra crossing
pxA = Key([(0, 4.6), (5.2, 4.6), (5.7, 3.4), (6.3, 4.9), (11, 4.9)])
pxB = Key([(0, 4.6), (15.6, 4.6), (18.4, -4.9)], 'lin')


def extra(t):
    if t < 10.9:
        startle = 1.0 if 5.6 <= t < 9 else 0.0
        return [(ZC + 0.6, lambda c, cam, d: pedestrian(c, cam, pxA(t), d, t, top='#e05d5d', walking=5.2 <= t < 5.7,
                                                         startle=startle))]
    walking = 15.6 <= t < 18.4
    wave = 1.0 if 16.4 <= t < 17.4 else 0.0
    return [(ZC + 0.4, lambda c, cam, d: pedestrian(c, cam, pxB(t), d, t, top='#56b38a', walking=walking, wave=wave)),
            (ZC + 1.1, lambda c, cam, d: pedestrian(c, cam, pxB(t - 0.35) + 0.5, d, t + 0.2, top='#3a7bd5',
                                                    pants='#c46a3c', kid=True, walking=walking))]


P = dict(extra=extra, no_stop=True)
shots = [
    Shot(3.0, 'street_pov2', **P),                                                                  # 0
    Shot(1.6, 'face_day', expr='whistle'),                                                          # 1
    Shot(2.4, 'street_pov2', **P),                                                                  # 2
    Shot(1.3, 'face_day', expr='shock', shake=1.0),                                                 # 3
    Shot(1.4, 'face_day', expr='sad'),                                                              # 4
    Shot(1.2, 'rewind_seq'),                                                                        # 5
    Shot(3.0, 'street_pov2', **P),                                                                  # 6
    Shot(1.2, 'pedals', pos=Key([(0, 0), (0.2, 0), (0.7, 1)]), press=Key([(0, 0), (0.7, 0), (1.1, 0.5)]), gas=0.2),  # 7
    Shot(3.2, 'street_pov2', **P),                                                                  # 8
    Shot(1.6, 'face_day', expr='calm'),                                                             # 9
    Shot(2.4, 'street_pov2', **P),                                                                  # 10
    Shot(2.0, 'face_day', expr='happy'),                                                            # 11
]
shots[5].kw.update(srcs=list(reversed(shots[0:5])), dur=shots[5].dur)
video = Video(['ALWAYS stop for people', 'at crossings!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[1], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, E[2], caption_in_scene('Didn\'t even slow down...')),
    (S[6], E[11], badge('RIGHT', '#22a356')),
    (S[6] + 0.4, E[7], caption_in_scene('1. Someone waiting? Slow down')),
    (S[8] + 0.2, E[8], caption_in_scene('2. Stop & let them cross')),
    (S[10] + 0.2, E[10], caption_in_scene('3. Go when they\'re across')),
    (S[11], E[11], caption_in_scene('People first.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(car_ambience(world, video.dur), 0, 1.0)
    m.add(whistle_tune(), S[1] + 0.1, 1.0)
    m.add(boing(), 5.65, 0.7, 0.5)
    m.add(screech(0.7, 1300), 5.8, 0.45)
    m.add(whoosh(0.8, 0.4), 5.9, 0.6, 0.6)
    m.add(impact(), S[3], 0.35)
    m.add(sad_violin(), S[4] + 0.1, 1.0)
    m.add(rewind_sfx(1.2), S[5], 1.0)
    m.add(brake_squeal(1.4), 13.6, 0.12)
    m.add(thud(), 15.4, 0.3)
    t = 15.6
    while t < 18.4:
        m.add(footsteps(0.12, 100), t, 0.35, 0.0)
        t += 0.32
    m.add(bell(midi(88), 0.6), 16.5, 0.6)
    m.add(success_jingle(), S[11] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep04_crosswalk.mp4')
