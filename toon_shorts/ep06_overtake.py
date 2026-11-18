"""06 - NEVER overtake on a solid line (day street)."""
from kit import *

engine.DAY = True
spA = Key([(0, 8), (4.6, 8), (5.6, 12), (8.4, 12), (9.0, 6), (11.9, 8)], 'lin')
spB = Key([(13.1, 8), (21.4, 8), (22.4, 13), (24.5, 13), (27, 9)], 'lin')
world = StreetWorld(27, [(0, -80, spA), (13.1, -80, spB)],
                    camx=Key([(0, DRIVER_X), (4.6, DRIVER_X), (5.6, -1.9), (8.5, -1.9), (9.0, DRIVER_X),
                              (21.4, DRIVER_X), (22.4, -1.9), (23.6, -1.9), (24.4, DRIVER_X)]))
world.headlights = const(0)
world.shake = Key([(8.5, 0), (8.6, 1), (9.6, 0)], 'lin')
world.blink_left = blinking([(20.1, 22.4)])
world.blink_right = blinking([(23.4, 24.4)])
truckA = Key([(0, 14), (4.6, 14), (7.2, 6), (8.5, 4), (9.0, 8), (11.9, 12)], 'lin')
truckB = Key([(13.1, 14), (21.4, 14), (22.4, 7), (23.0, 0), (23.6, -6), (24.5, -14)], 'lin')
oncA = Key([(4.2, 110), (7.2, 14), (8.5, 6), (9.1, -10)], 'lin')
oncB = Key([(17.5, 60), (19.3, 0), (20, -15)], 'lin')


def extra(t):
    out = []
    tr = truckA if t < 13.1 else truckB
    out.append((world.ego_z(t) + tr(t), lambda c, cam, d: car_rear_simple(c, cam, 1.75, d, '#f2f2f2', t, 0, 'truck')))
    if 4.2 <= t < 9.1:
        out.append((world.ego_z(t) + oncA(t), lambda c, cam, d: car_front_simple(c, cam, -1.75, d, '#e05d5d', t)))
    if 17.5 <= t < 20:
        out.append((world.ego_z(t) + oncB(t), lambda c, cam, d: car_front_simple(c, cam, -1.75, d, '#3a7bd5', t)))
    return out


P = dict(extra=extra, dashed_from=lambda t: 1e9 if t < 13.1 else 340.0)
shots = [
    Shot(3.0, 'street_pov2', **P),                                                                  # 0
    Shot(1.4, 'face_day', expr='annoyed'),                                                          # 1
    Shot(2.8, 'street_pov2', **P),                                                                  # 2
    Shot(1.3, 'face_day', expr='terror', shake=1.0),                                                # 3
    Shot(2.0, 'street_pov2', **P),                                                                  # 4
    Shot(1.4, 'face_day', expr='relief', sweat=True),                                               # 5
    Shot(1.2, 'rewind_seq'),                                                                        # 6
    Shot(3.0, 'street_pov2', **P),                                                                  # 7
    Shot(1.4, 'face_day', expr='calm'),                                                             # 8
    Shot(2.6, 'street_pov2', **P),                                                                  # 9
    Shot(1.2, 'dash2'),                                                                             # 10
    Shot(3.2, 'street_pov2', **P),                                                                  # 11
    Shot(2.0, 'face_day', expr='happy'),                                                            # 12
]
shots[6].kw.update(srcs=list(reversed(shots[0:6])), dur=shots[6].dur)
video = Video(['NEVER overtake on', 'a solid line!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, S[2] + 1.6, caption_in_scene('Crossing the solid line...')),
    (S[7], E[12], badge('RIGHT', '#22a356')),
    (S[7] + 0.3, E[8], caption_in_scene('1. Solid line? Stay behind')),
    (S[9] + 0.3, E[9], caption_in_scene('2. Wait: dashed line + clear road')),
    (S[10], E[10], caption_in_scene('3. Signal')),
    (S[11] + 0.2, E[11], caption_in_scene('4. Pass, then move back')),
    (S[12], E[12], caption_in_scene('Patience saves lives.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(car_ambience(world, video.dur), 0, 1.0)
    m.add(rumble(10.0), 0, 0.5, 0.2)
    m.add(rumble(11.0), 13.1, 0.5, 0.2)
    m.add(horn(1.4), 6.0, 0.8, -0.3)
    m.add(impact(), S[3], 0.35)
    m.add(screech(1.0, 1150), S[4], 0.6)
    m.add(car_pass(1.4, 0.35, 110), S[4] + 0.1, 1.0, np.linspace(-0.3, -0.9, int(1.4 * SR)))
    m.add(horn(0.9, doppler=[1.05, 1.03, 0.93, 0.92]), S[4] + 0.1, 0.6, -0.6)
    m.add(heartbeat(3, 120), S[5], 0.9)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(car_pass(1.8, 0.5, 100), 18.3, 0.7, np.linspace(-0.3, -0.9, int(1.8 * SR)))
    m.add(click(), 20.1, 0.7)
    indicator(m, 20.1, 22.4, 0.45, -0.2)
    m.add(click(), 23.4, 0.6)
    indicator(m, 23.4, 24.4, 0.45, 0.2)
    m.add(success_jingle(), S[12] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep06_overtake.mp4')
