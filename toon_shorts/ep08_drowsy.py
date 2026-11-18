"""08 - Feeling sleepy? Pull over and rest (night highway)."""
from kit import *

engine.DAY = False
world = World(23.6, speed=Key([(0, 27), (12.4, 27), (14.6, 27), (17.4, 6), (17.6, 0), (21.6, 0), (23.6, 20)], 'lin'),
              camx=Key([(0, 1.4), (4.6, 1.4), (6.8, 3.0), (9.0, 3.9), (9.4, 3.9), (10.0, 1.4), (12.4, 1.4),
                        (15.0, 1.4), (16.6, 3.6), (21.6, 3.6), (23.6, 1.4)]),
              shake=Key([(8.0, 0), (8.05, 0.8), (9.0, 0.8), (9.6, 0)], 'lin'),
              blink_right=blinking([(14.4, 17.6)]))
SIGN = [(Key([(12.4, 300), (13.8, 200), (15.4, 28), (16.3, 6), (16.6, -5)], 'lin'), ['REST AREA', '500 m'])]
shots = [
    Shot(2.6, 'pov2'),                                                                              # 0
    Shot(1.6, 'face', expr='drowsy'),                                                               # 1
    Shot(2.6, 'pov2', eyelids=Key([(0, 0), (0.8, 0.85), (1.2, 0.3), (2.0, 1.0)])),                   # 2
    Shot(1.2, 'face', expr='asleep'),                                                               # 3
    Shot(2.0, 'pov2', eyelids=Key([(0, 1), (0.15, 0)])),                                            # 4
    Shot(1.2, 'face', expr='shock', shake=1.0),                                                     # 5
    Shot(1.2, 'rewind_seq'),                                                                        # 6
    Shot(1.4, 'face', expr='yawn'),                                                                 # 7
    Shot(2.8, 'pov2', signs=SIGN),                                                                  # 8
    Shot(1.0, 'dash2'),                                                                             # 9
    Shot(2.4, 'face', expr='asleep'),                                                               # 10
    Shot(1.6, 'face', expr='happy'),                                                                # 11
    Shot(2.0, 'pov2'),                                                                              # 12
]
shots[6].kw.update(srcs=list(reversed(shots[0:6])), dur=shots[6].dur)
video = Video(['Feeling sleepy?', 'PULL OVER & rest!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[0] + 0.3, E[0], caption_in_scene('2 AM, long drive home...')),
    (S[2], E[5], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, E[2], caption_in_scene('"Just a bit further..."')),
    (S[7], E[12], badge('RIGHT', '#22a356')),
    (S[7] + 0.1, E[7], caption_in_scene('1. Yawning? That\'s the sign')),
    (S[8] + 0.2, E[9], caption_in_scene('2. Pull over somewhere safe')),
    (S[10] + 0.1, E[10], caption_in_scene('3. Take a 20-min power nap')),
    (S[11], E[12], caption_in_scene('4. Drive on refreshed')),
]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur), 0, 1.5)
    m.add(yawn_sound(), S[1] + 0.2, 1.0)
    m.add(heartbeat(4, 60), S[2], 0.5)
    m.add(rumble_strip(1.0), 8.0, 1.2, 0.5)
    m.add(horn(1.0), 8.3, 0.7, 0.2)
    m.add(impact(), S[5], 0.35)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(yawn_sound(), S[7] + 0.1, 1.0)
    m.add(click(), 14.4, 0.7)
    indicator(m, 14.4, 17.6, 0.45, 0.2)
    m.add(click(), 17.6, 0.6)
    m.add(bell(midi(84), 0.8), S[11] + 0.1, 0.7)
    m.add(success_jingle(), S[12] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep08_drowsy.mp4')
