"""07 - Dip your high beams for oncoming cars (night highway)."""
from kit import *

engine.DAY = False
slow_car = Vehicle('car', 1.8, Key([(0, 200), (8.0, 40), (8.6, 16), (9.6, 10), (11.6, 12), (11.61, 250),
                                    (17.8, 140), (20.8, 70), (23.2, 40), (25.5, 38)], 'lin'),
                   color='#c9c9d6', brake=Key([(8.4, 0), (8.45, 1), (11.6, 1), (11.65, 0), (21.0, 0), (21.05, 1)], 'step'))
world = World(25.5, speed=Key([(0, 25), (8.4, 25), (9.4, 10), (11.6, 12), (11.61, 25), (20.8, 25), (23.2, 18), (25.5, 18)], 'lin'),
              camx=const(1.4), vehicles=[slow_car],
              shake=Key([(8.4, 0), (8.5, 1), (9.5, 0)], 'lin'),
              ego_brake=Key([(8.4, 0), (8.45, 1), (11.6, 1), (11.65, 0)], 'step'))
onc = Oncoming(-8.1, Key([(0, 400), (4.2, 200), (7.0, 25), (7.6, -5), (12.8, -5), (12.81, 400), (15.4, 250),
                          (17.8, 160), (20.8, -5)], 'lin'),
               '#d8d8e0',
               highbeam=Key([(0, 1), (12.8, 1), (15.6, 1), (16.4, 0)], 'lin'),
               flash=Key([(4.4, 0), (4.45, 1), (4.65, 0), (4.8, 1), (5.0, 0)], 'step'))
ON = [onc]
shots = [
    Shot(3.0, 'pov2', highbeam=1, oncoming=ON),                                                     # 0
    Shot(1.2, 'dash2', highbeam=const(1)),                                                          # 1
    Shot(2.8, 'pov2', highbeam=1, oncoming=ON),                                                     # 2
    Shot(1.0, 'face', expr='shock', shake=0.8),                                                     # 3
    Shot(2.2, 'pov2', highbeam=1, oncoming=ON),                                                     # 4
    Shot(1.4, 'face', expr='relief', sweat=True),                                                   # 5
    Shot(1.2, 'rewind_seq'),                                                                        # 6
    Shot(2.6, 'pov2', highbeam=1, oncoming=ON),                                                     # 7
    Shot(1.4, 'stalk', angle=Key([(0, 0), (0.45, 0), (0.6, 6), (0.9, 0)])),                         # 8
    Shot(1.0, 'dash2', highbeam=const(0)),                                                          # 9
    Shot(3.0, 'pov2', highbeam=0, oncoming=ON),                                                     # 10
    Shot(2.4, 'pov2', highbeam=Key([(0, 0), (0.4, 0), (0.6, 1)], 'lin'), oncoming=ON),              # 11
    Shot(2.0, 'face', expr='happy'),                                                                # 12
]
shots[6].kw.update(srcs=list(reversed(shots[0:6])), dur=shots[6].dur)
video = Video(['DIP your high beams', 'for oncoming cars!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, E[2], caption_in_scene('Both on high beams...')),
    (S[7], E[12], badge('RIGHT', '#22a356')),
    (S[7] + 0.4, E[8], caption_in_scene('1. See headlights? Dip yours')),
    (S[10] + 0.1, S[10] + 1.5, caption_in_scene('2. They dip too')),
    (S[10] + 1.5, E[10], caption_in_scene('3. You spot hazards early')),
    (S[11] + 0.2, E[11], caption_in_scene('4. Passed? High beams back on')),
    (S[12], E[12], caption_in_scene('Be bright, not blinding.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur), 0, 1.6)
    m.add(click(), 4.45, 0.0)
    m.add(horn(0.5), 4.6, 0.4, -0.6)
    m.add(riser(1.6), 5.4, 0.7)
    m.add(car_pass(1.4, 0.4, 105), 6.9, 0.8, np.linspace(-0.3, -0.9, int(1.4 * SR)))
    m.add(impact(), S[3], 0.35)
    m.add(screech(1.3, 1150), 8.45, 0.8)
    m.add(heartbeat(3, 120), S[5], 0.9)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(click(), S[8] + 0.6, 1.0)
    m.add(chime(), S[9] + 0.2, 0.5)
    m.add(car_pass(1.6, 0.5, 100), 20.0, 0.7, np.linspace(-0.3, -0.9, int(1.6 * SR)))
    m.add(click(), S[11] + 0.45, 0.6)
    m.add(success_jingle(), S[12] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep07_highbeams.mp4')
