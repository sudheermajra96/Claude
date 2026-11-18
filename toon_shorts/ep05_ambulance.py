"""05 - Make way for ambulances (day street)."""
import kit
from kit import *

engine.DAY = True
kit.EMERGENCY['kind'] = 'ambulance'
spA = Key([(0, 11), (6.3, 11), (7.3, 0), (13.3, 0)], 'lin')
spB = Key([(13.3, 11), (17.2, 11), (19.0, 0), (22.6, 0), (24.7, 9), (30, 10)], 'lin')
world = StreetWorld(27, [(0, -80, spA), (13.3, -80, spB)],
                    camx=Key([(0, DRIVER_X), (16.9, DRIVER_X), (18.4, 2.7), (22.8, 2.7), (24.0, DRIVER_X)]),
                    police_flash=Key([(3.5, 0), (4.8, 0.7), (12.1, 0.7), (12.2, 0), (14.5, 0), (15.5, 0.6), (20.6, 0.6), (21.2, 0)], 'lin'))
world.headlights = const(0)
world.shake = Key([(6.3, 0), (6.4, 0.7), (7.4, 0)], 'lin')
world.blink_right = blinking([(15.5, 19.5)])
world.ego_brake = Key([(6.3, 0), (6.35, 1), (12, 1), (12.1, 0), (17.2, 0), (17.3, 1), (22.6, 1), (22.7, 0)], 'step')
behindA = Key([(1.4, 120), (2.6, 70), (4.8, 25), (6.1, 15), (7.3, 8), (8.7, 6), (12.1, 6)])
behindB = Key([(13.3, 70), (15.5, 30), (16.9, 20), (19.0, 10), (19.9, 5)])
aheadB = Key([(19.9, -2), (20.6, 4), (21.6, 12), (22.5, 25)], "lin")


def police(t):
    if 1.4 <= t < 12.1:
        return [(world.ego_z(t) - behindA(t), 1.75, True)]
    if 13.3 <= t < 19.9:
        return [(world.ego_z(t) - behindB(t), 1.75 - 1.2 * smooth((t - 17) / 2.5), True)]
    return []


def extra(t):
    if 19.9 <= t < 23:
        return [(world.ego_z(t) + aheadB(t), lambda c, cam, d: ambulance_rear(c, cam, 0.4, d, t))]
    return []


P = dict(police=police, extra=extra)
shots = [
    Shot(2.6, 'street_pov2', **P),                                                                  # 0
    Shot(2.2, 'rear_mirror_day', **P),                                                              # 1
    Shot(1.3, 'face_day', expr='unsure'),                                                           # 2
    Shot(2.6, 'street_pov2', **P),                                                                  # 3
    Shot(2.0, 'rear_mirror_day', **P),                                                              # 4
    Shot(1.4, 'face_day', expr='sad'),                                                              # 5
    Shot(1.2, 'rewind_seq'),                                                                        # 6
    Shot(2.2, 'rear_mirror_day', **P),                                                              # 7
    Shot(1.4, 'dash2'),                                                                             # 8
    Shot(3.0, 'street_pov2', **P),                                                                  # 9
    Shot(2.6, 'street_pov2', **P),                                                                  # 10
    Shot(2.2, 'street_pov2', **P),                                                                  # 11
    Shot(2.0, 'face_day', expr='happy'),                                                            # 12
]
shots[6].kw.update(srcs=list(reversed(shots[0:6])), dur=shots[6].dur)
video = Video(['Hear a siren?', 'MAKE WAY!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[3], E[5], badge('WRONG', '#e0393e')),
    (S[3] + 1.3, E[4], caption_in_scene('Stopped right in its way...')),
    (S[7], E[12], badge('RIGHT', '#22a356')),
    (S[7] + 0.2, E[7], caption_in_scene('1. Check your mirrors')),
    (S[8] + 0.1, E[9], caption_in_scene('2. Signal & pull over right')),
    (S[10] + 0.2, E[10], caption_in_scene('3. Let it pass')),
    (S[11] + 0.2, E[11], caption_in_scene('4. Then carry on safely')),
    (S[12], E[12], caption_in_scene('Every second counts.')),
]


def siren_track(t0, t1, env_keys, doppler=None):
    d = t1 - t0
    sig = ambulance_siren(d, doppler)
    tt = np.arange(len(sig)) / SR + t0
    env = np.interp(tt, [k[0] for k in env_keys], [k[1] for k in env_keys])
    return sig * env


def sound():
    m = Mixer(video.dur)
    m.add(car_ambience(world, video.dur), 0, 1.0)
    m.add(siren_track(1.2, 12.1, [(1.2, 0.1), (4.8, 0.7), (8, 1.0), (12.1, 1.0)]), 1.2, 1.0, -0.1)
    m.add(screech(0.9, 1200), 6.35, 0.55)
    m.add(horn(0.9, doppler=[0.75] * 4), S[4] + 0.2, 0.9)
    m.add(horn(1.2, doppler=[0.75] * 4), S[4] + 1.2, 0.9)
    m.add(sad_violin(), S[5] + 0.1, 0.9)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(siren_track(13.3, 22.8, [(13.3, 0.4), (15.5, 0.8), (20.2, 1.0), (21.0, 0.6), (22.8, 0.1)],
                      doppler=[1.0] * 7 + [0.94] * 3), 13.3, 1.0, -0.1)
    m.add(click(), 15.5, 0.7)
    indicator(m, 15.5, 19.5, 0.45, 0.2)
    m.add(click(), 19.5, 0.6)
    m.add(car_pass(1.6, 0.4, 85), 19.9, 1.0, np.linspace(-0.2, -0.6, int(1.6 * SR)))
    m.add(chime(), S[11] + 0.1, 0.5)
    m.add(success_jingle(), S[12] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep05_ambulance.mp4')
