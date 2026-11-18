"""03 - Yellow light? Slow down and STOP (day street, traffic light, red-light camera)."""
from kit import *
import street

engine.DAY = True
street.TICKET_TEXT = 'Ran a RED light'
spA = Key([(0, 12), (3.0, 12), (4.0, 16.5), (13.3, 16.5)], 'lin')
spB = Key([(13.3, 12), (14.5, 12), (18.6, 0), (22.6, 0), (24.3, 8), (30, 10)], 'lin')
world = StreetWorld(27, [(0, 76.7, spA), (13.3, 42.5, spB)], camx=const(DRIVER_X))
world.headlights = const(0)
world.ego_brake = Key([(14.5, 0), (14.6, 1), (22.6, 1), (22.7, 0)], 'step')


def light_state(t):
    if t < 13.3:
        return 'green' if t < 2.4 else ('yellow' if t < 4.9 else 'red')
    return 'green' if t < 14.3 else ('yellow' if t < 16.3 else ('red' if t < 22.3 else 'green'))


xA = Key([(4.5, -45), (5.9, -12), (6.4, -9), (13, -9)])
xB = Key([(21.4, -45), (22.2, 45)], 'lin')


def cross_cars(t):
    if 4.5 <= t < 13.3:
        return [(xA(t), ZI - 3, '#3a7bd5')]
    if 21.4 <= t < 22.2:
        return [(xB(t), ZI - 3, '#37b26c')]
    return []


def extra(t):
    st = light_state(t)
    return [(ZI + 6.5, lambda c, cam, d: traffic_light_overhead(c, cam, 4.8, d, st))]


P = dict(extra=extra, cross_cars=cross_cars, no_stop=True)
shots = [
    Shot(3.0, 'street_pov2', **P),                                                                  # 0
    Shot(1.2, 'pedals', pos=const(0), press=const(0), gas=1.0),                                     # 1
    Shot(2.8, 'street_pov2', cam_flash=Key([(0, 0), (1.45, 0), (1.5, 1), (1.75, 0)], 'lin'), **P),  # 2
    Shot(1.3, 'face_day', expr='shock', shake=1.0),                                                 # 3
    Shot(2.4, 'ticket_close'),                                                                      # 4
    Shot(1.4, 'face_day', expr='sad'),                                                              # 5
    Shot(1.2, 'rewind_seq'),                                                                        # 6
    Shot(3.0, 'street_pov2', **P),                                                                  # 7
    Shot(1.4, 'pedals', pos=Key([(0, 0), (0.3, 0), (0.8, 1)]), press=Key([(0, 0), (0.8, 0), (1.3, 0.5)]), gas=0.2),  # 8
    Shot(2.6, 'street_pov2', **P),                                                                  # 9
    Shot(1.2, 'dash2'),                                                                             # 10
    Shot(2.8, 'street_pov2', **P),                                                                  # 11
    Shot(2.0, 'face_day', expr='happy'),                                                            # 12
]
shots[6].kw.update(srcs=list(reversed(shots[0:6])), dur=shots[6].dur)
video = Video(['Yellow light?', 'Slow down & STOP!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[1], E[5], badge('WRONG', '#e0393e')),
    (S[1] + 0.1, E[1], caption_in_scene('Speeding up to "make it"...')),
    (S[7], E[12], badge('RIGHT', '#22a356')),
    (S[7] + 1.0, E[8], caption_in_scene('1. Yellow? Ease off & brake')),
    (S[9] + 0.3, E[10], caption_in_scene('2. Stop before the line')),
    (S[11] + 0.9, E[11], caption_in_scene('3. Go on green, when clear')),
    (S[12], E[12], caption_in_scene('Yellow = slow down, not speed up')),
]


def sound():
    m = Mixer(video.dur)
    m.add(car_ambience(world, video.dur), 0, 1.0)
    m.add(ambience(world, 1.4)[:int(1.2 * SR)] * 0, 0, 0)
    m.add(rumble(1.4), S[1], 0.8)
    m.add(shutter(), S[2] + 1.5, 1.2, 0.4)
    m.add(brake_squeal(1.0), 5.9, 0.5, -0.5)
    m.add(horn(1.0), 6.0, 0.6, -0.5)
    m.add(impact(), S[3], 0.35)
    m.add(thud(), S[4] + 0.5, 0.7)
    m.add(sad_violin(), S[4] + 0.8, 1.0)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(brake_squeal(1.6), 16.6, 0.12)
    m.add(thud(), 18.6, 0.3)
    m.add(bell(midi(84), 0.8), S[10] + 0.3, 0.6)
    m.add(car_pass(1.4, 0.5, 100), 21.2, 0.8, np.linspace(-0.9, 0.9, int(1.4 * SR)))
    m.add(pop(), 22.3, 0.5)
    m.add(success_jingle(), S[12] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep03_yellow.mp4')
