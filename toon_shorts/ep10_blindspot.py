"""10 - ALWAYS check your blind spot (night highway, motorbike)."""
from kit import *

engine.DAY = False
bike = Vehicle('moto', -1.8, Key([(0, -40), (1.8, -6), (2.4, -1.9), (4.6, -1.5), (5.4, -1.2), (6.2, 2.6), (7.0, 8), (9.6, 30),
                                  (10.79, 30), (10.8, -1.9), (15.0, -1.5), (16.2, -1.0), (16.8, 2.5), (18.6, 22),
                                  (24.2, 60)], 'lin'), color='#e0393e')
slow = Vehicle('car', 1.8, Key([(0, 30), (9.6, 22), (10.79, 22), (10.8, 30), (20.0, 22), (22.2, 8), (24.2, -2)], 'lin'),
               color='#c9c9d6')
world = World(24.2, speed=Key([(0, 25), (24.2, 25)]),
              camx=Key([(0, 1.4), (5.0, 1.4), (5.6, 0.5), (5.8, 0.5), (6.4, 1.4), (20.0, 1.4), (21.4, -2.2), (24.2, -2.2)]),
              vehicles=[bike, slow], shake=Key([(5.6, 0), (5.7, 0.8), (6.6, 0)], 'lin'),
              blink_left=blinking([(4.7, 5.6), (18.6, 21.4)]))
shots = [
    Shot(2.6, 'pov2'),                                                                              # 0
    Shot(2.0, 'side_mirror'),                                                                       # 1
    Shot(2.4, 'pov2'),                                                                              # 2
    Shot(1.2, 'face', expr='terror', shake=1.0),                                                    # 3
    Shot(1.4, 'face', expr='relief', sweat=True),                                                   # 4
    Shot(1.2, 'rewind_seq'),                                                                        # 5
    Shot(2.0, 'side_mirror'),                                                                       # 6
    Shot(2.2, 'shoulder_check'),                                                                    # 7
    Shot(1.2, 'face', expr='focus'),                                                                # 8
    Shot(2.4, 'pov2'),                                                                              # 9
    Shot(1.0, 'dash2'),                                                                             # 10
    Shot(2.6, 'pov2'),                                                                              # 11
    Shot(2.0, 'face', expr='happy'),                                                                # 12
]
shots[5].kw.update(srcs=list(reversed(shots[0:5])), dur=shots[5].dur)
video = Video(['ALWAYS check', 'your blind spot!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[1] + 0.2, E[1], caption_in_scene('Mirror looks clear...')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2] + 0.2, S[2] + 1.0, caption_in_scene('...so he moves over')),
    (S[6], E[12], badge('RIGHT', '#22a356')),
    (S[6] + 0.2, E[6], caption_in_scene('1. Check your mirror')),
    (S[7] + 0.2, E[7], caption_in_scene('2. Look over your shoulder')),
    (S[8], E[9], caption_in_scene('3. Wait for it to pass')),
    (S[10], E[10], caption_in_scene('4. Signal')),
    (S[11] + 0.2, E[11], caption_in_scene('5. Then move over')),
    (S[12], E[12], caption_in_scene('Mirror. Shoulder. Go.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur), 0, 1.5)
    m.add(click(), 4.7, 0.7)
    indicator(m, 4.7, 5.6, 0.45, -0.2)
    m.add(moto_horn(0.5), 5.6, 1.0, -0.6)
    m.add(moto_horn(0.3), 6.2, 0.9, -0.5)
    m.add(screech(0.8, 1300), 5.75, 0.5)
    m.add(moto_pass(2.0), 5.6, 1.0, np.linspace(-0.8, -0.1, int(2.0 * SR)))
    m.add(impact(), S[3], 0.35)
    m.add(heartbeat(3, 120), S[4], 0.9)
    m.add(rewind_sfx(1.2), S[5], 1.0)
    m.add(head_swish(), S[7], 0.8, -0.5)
    m.add(moto_pass(2.6), S[7] + 1.0, 0.8, np.linspace(-0.9, -0.2, int(2.6 * SR)))
    m.add(click(), 18.6, 0.7)
    indicator(m, 18.6, 21.4, 0.45, -0.2)
    m.add(click(), 21.4, 0.6)
    m.add(success_jingle(), S[12] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep10_blindspot.mp4')
