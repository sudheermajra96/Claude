"""09 - Slow down in the rain (night highway, rain + wipers)."""
from kit import *

engine.DAY = False
ahead = Vehicle('car', 1.8, Key([(0, 18), (4.2, 18), (4.8, 17), (6.4, 4), (6.8, 3.5), (10.7, 3.5), (10.71, 40),
                                 (17.5, 40), (18.1, 38), (20.3, 16), (22.3, 16)], 'lin'),
                color='#3a7bd5', brake=Key([(4.75, 0), (4.8, 1), (10.6, 1), (10.65, 0), (17.85, 0), (17.9, 1)], 'step'))
world = World(22.3, speed=Key([(0, 30), (4.8, 30), (5.3, 22), (6.6, 0), (10.7, 0), (10.71, 20), (17.9, 20), (20.3, 0),
                               (22.3, 0)], 'lin'),
              camx=Key([(0, 1.4), (5.2, 1.4), (5.8, 1.0), (6.3, 1.7), (6.8, 1.4)]),
              vehicles=[ahead], shake=Key([(5.0, 0), (5.1, 0.8), (6.8, 0.3), (7.2, 0)], 'lin'),
              ego_brake=Key([(5.0, 0), (5.05, 1), (10.6, 1), (10.65, 0), (18.0, 0), (18.05, 1)], 'step'))
R = dict(rain=1.0, wiper=lambda lt: wiper_angle(lt))
shots = [
    Shot(3.0, 'pov2', **R),                                                                         # 0
    Shot(1.2, 'dash2'),                                                                             # 1
    Shot(2.6, 'pov2', skid=Key([(0, 0), (0.9, 0), (1.3, 0.25), (1.7, -0.2), (2.1, 0.1), (2.6, 0)]), **R),  # 2
    Shot(1.3, 'face', expr='terror', shake=1.0),                                                    # 3
    Shot(1.4, 'face', expr='relief', sweat=True),                                                   # 4
    Shot(1.2, 'rewind_seq'),                                                                        # 5
    Shot(2.8, 'pov2', **R),                                                                         # 6
    Shot(1.2, 'dash2'),                                                                             # 7
    Shot(2.8, 'pov2', **R),                                                                         # 8
    Shot(2.8, 'pov2', **R),                                                                         # 9
    Shot(2.0, 'face', expr='happy'),                                                                # 10
]
shots[5].kw.update(srcs=list(reversed(shots[0:5])), dur=shots[5].dur)
video = Video(['Raining?', 'SLOW DOWN!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[1], E[4], badge('WRONG', '#e0393e')),
    (S[1] + 0.1, E[1], caption_in_scene('Too fast, too close...')),
    (S[6], E[10], badge('RIGHT', '#22a356')),
    (S[6] + 0.3, E[6], caption_in_scene('1. Slow down')),
    (S[7], E[7], caption_in_scene('2. Lights on')),
    (S[8] + 0.2, E[8], caption_in_scene('3. Double your gap')),
    (S[9] + 0.2, E[9], caption_in_scene('4. Brake early & gently')),
    (S[10], E[10], caption_in_scene('Wet road = slow road.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur), 0, 1.2)
    m.add(rain_sound(video.dur), 0, 1.0)
    for i in (0, 2, 6, 8, 9):
        m.add(wiper_thunks(shots[i].dur), S[i], 0.8)
    m.add(screech(1.7, 1050), 5.05, 0.8)
    m.add(whoosh(1.0, 0.5), 5.5, 0.6)
    m.add(horn(0.9), 6.5, 0.6, 0.1)
    m.add(impact(), S[3], 0.4)
    m.add(heartbeat(3, 120), S[4], 0.9)
    m.add(rewind_sfx(1.2), S[5], 1.0)
    m.add(brake_squeal(1.6), 18.2, 0.12)
    m.add(success_jingle(), S[10] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep09_rain.mp4')
