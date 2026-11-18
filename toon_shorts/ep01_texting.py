"""01 - NEVER text while driving (day street)."""
from kit import *

engine.DAY = True
sp1 = const(12)
sp2 = Key([(14.1, 12), (20.9, 12), (21.9, 0), (40, 0)], 'lin')
world = StreetWorld(28, [(0, -60, sp1), (14.1, -60, sp2)],
                    camx=Key([(0, DRIVER_X), (7.0, DRIVER_X), (8.6, -0.7), (10.5, -0.7), (11.0, DRIVER_X),
                              (21.0, DRIVER_X), (22.2, 2.5)]))
world.headlights = const(0)
world.shake = Key([(10.4, 0), (10.5, 1), (11.6, 0)], 'lin')
world.blink_right = blinking([(20.8, 22.3)])
relA = Key([(0, 300), (6.8, 120), (8.0, 42), (8.6, 22), (9.2, 13), (10.5, 10), (11.1, 0), (12, -20)], 'lin')
relB = Key([(17.7, 90), (20.4, 0), (21, -15)], 'lin')


def extra(t):
    out = []
    if t < 12:
        out.append((world.ego_z(t) + relA(t), lambda c, cam, d: car_front_simple(c, cam, -1.75, d, '#3a7bd5', t)))
    if 17.7 <= t < 21:
        out.append((world.ego_z(t) + relB(t), lambda c, cam, d: car_front_simple(c, cam, -1.75, d, '#f2a541', t)))
    return out


P = dict(extra=extra)
shots = [
    Shot(2.6, 'street_pov2', **P),                                                                  # 0
    Shot(1.6, 'face_day', expr='focus'),                                                            # 1
    Shot(2.6, 'phone_close', swipes=[0.9, 1.5, 2.1], notifs=[(0.15, 'New message', '#22a356')]),   # 2
    Shot(2.4, 'street_pov2', phone_down=Key([(0, 0.0), (0.6, 0.55), (1.6, 0.55), (1.8, 0)]), **P),  # 3
    Shot(1.3, 'face_day', expr='shock', shake=1.0),                                                 # 4
    Shot(2.0, 'street_pov2', **P),                                                                  # 5
    Shot(1.6, 'face_day', expr='relief', sweat=True),                                               # 6
    Shot(1.2, 'rewind_seq'),                                                                        # 7
    Shot(2.4, 'phone_mount', muted=[1.0]),                                                          # 8
    Shot(3.0, 'street_pov2', **P),                                                                  # 9
    Shot(1.6, 'face_day', expr='calm'),                                                             # 10
    Shot(2.6, 'street_pov2', **P),                                                                  # 11
    Shot(2.0, 'face_day', expr='happy'),                                                            # 12
]
shots[7].kw.update(srcs=list(reversed(shots[0:7])), dur=shots[7].dur)
video = Video(['NEVER text', 'while driving!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[3], E[6], badge('WRONG', '#e0393e')),
    (S[3] + 0.3, E[3], caption_in_scene('Eyes off the road...')),
    (S[8], E[12], badge('RIGHT', '#22a356')),
    (S[8] + 0.2, E[8], caption_in_scene('1. Turn on Driving Focus')),
    (S[9] + 0.2, E[9], caption_in_scene('2. Eyes on the road')),
    (S[11] + 0.2, E[11], caption_in_scene('3. Need to reply? Pull over')),
    (S[12], E[12], caption_in_scene('The text can wait.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(car_ambience(world, video.dur), 0, 1.0)
    m.add(text_ping(), 1.6, 0.9, 0.2)
    m.add(text_ping(), S[2] + 0.15, 0.7)
    m.add(typing_taps(1.7), S[2] + 0.8, 0.8)
    m.add(horn(1.3), 8.3, 0.7, -0.3)
    m.add(impact(), S[4], 0.35)
    m.add(screech(1.1, 1150), S[5], 0.6)
    m.add(car_pass(1.6, 0.45, 110), S[5] + 0.1, 1.0, np.linspace(-0.3, -0.9, int(1.6 * SR)))
    m.add(horn(1.0, doppler=[1.05, 1.04, 0.93, 0.92]), S[5] + 0.1, 0.6, -0.5)
    m.add(heartbeat(3, 120), S[6], 0.9)
    m.add(rewind_sfx(1.2), S[7], 1.0)
    m.add(pop(), S[8] + 1.0, 0.4)
    m.add(car_pass(1.8, 0.5, 100), S[9] + 1.8, 0.7, np.linspace(-0.3, -0.9, int(1.8 * SR)))
    m.add(click(), 20.8, 0.6)
    indicator(m, 20.8, 22.3, 0.45, 0.2)
    m.add(click(), 22.3, 0.6)
    m.add(success_jingle(), S[12] + 0.1, 0.8)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep01_texting.mp4')
