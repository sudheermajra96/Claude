"""Episode: ALWAYS signal before changing lanes!"""
import sys

from engine import *

RIGHT_X, LEFT_X = 1.4, -2.2          # driver position in each lane

world = World(
    dur=44,
    speed=Key([(0, 27), (14.6, 27), (16.2, 22), (19, 26), (21, 27), (36, 27), (39, 31), (44, 31)]),
    camx=Key([(0, RIGHT_X), (9.4, RIGHT_X), (10.8, LEFT_X), (16.4, LEFT_X), (17.3, RIGHT_X),
              (36.4, RIGHT_X), (38.2, LEFT_X), (44, LEFT_X)]),
    vehicles=[
        Vehicle('truck', 1.8, Key([(0, 60), (9.4, 19), (14, 16), (19, 22), (21, 22), (22.39, 22),
                                   (22.4, 40), (36.1, 21), (38.2, 12), (40.5, -14), (44, -40)])),
        # the car we cut off
        Vehicle('car', -1.8, Key([(0, -200), (6.2, -60), (8.8, -27), (11.4, -12), (13.2, -6), (14.8, -4.2),
                                  (16.6, -4), (17.6, 3), (19, 30), (20, 600)], 'lin'),
                color='#d8d8e0', highbeam=Key([(11.3, 0), (11.5, 1), (15, 1), (16, 0)], 'lin')),
        # the car we wait for in the good version
        Vehicle('car', -1.8, Key([(0, -600), (24.9, -32), (27.4, -5), (28.4, 6), (29.5, 30), (31, 90)], 'lin'),
                color='#3fa66b'),
    ],
    blink_left=blinking([(31.5, 38.6)]),
    shake=Key([(14.7, 0), (14.8, 1), (16.4, 0.6), (17.4, 0.6), (18.4, 0)], 'lin'),
)

shots = [
    Shot(4.0, 'pov'),
    Shot(2.2, 'face', expr='annoyed'),
    Shot(2.6, 'side_mirror'),
    Shot(2.6, 'pov'),
    Shot(1.8, 'side_mirror'),
    Shot(1.6, 'rear_mirror'),
    Shot(1.6, 'face', expr='scream', shake=1.0),
    Shot(2.6, 'pov'),
    Shot(2.0, 'face', expr='relief', sweat=True),
    Shot(1.4, 'rewind', src_t=Key([(0, 18.5), (1.4, 5)], 'lin')),
    Shot(2.5, 'pov'),
    Shot(2.6, 'side_mirror'),
    Shot(2.0, 'pov'),
    Shot(1.6, 'side_mirror'),
    Shot(1.6, 'stalk', angle=Key([(0, 0), (0.3, 0), (0.42, -6)])),
    Shot(1.6, 'dash'),
    Shot(1.8, 'side_mirror'),
    Shot(4.4, 'pov'),
    Shot(2.6, 'face', expr='happy'),
]

overlays = [
    (9.0, 21.0, badge('WRONG', '#e0393e')),
    (9.3, 11.4, caption_in_scene('No signal...')),
    (22.4, 43.6, badge('RIGHT', '#22a356')),
    (29.5, 31.1, caption_in_scene('1. Mirror')),
    (31.1, 34.3, caption_in_scene('2. Signal')),
    (36.1, 38.6, caption_in_scene('3. Move')),
    (40.6, 43.6, caption_in_scene('Mirror. Signal. Move.')),
]

video = Video(['ALWAYS signal before', 'changing lanes!'], world, shots, overlays)


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur), 0, 1.8)
    m.add(horn(1.1), 11.45, 0.6, -0.45)
    m.add(screech(1.6, 1250), 11.6, 0.55, -0.35)
    m.add(horn(0.35), 12.8, 0.6, -0.45)
    m.add(horn(1.5), 13.3, 0.65, -0.4)
    m.add(whoosh(1.2, 0.6), 14.7, 0.7, 0)
    pan = np.linspace(-0.2, -0.85, int(2.4 * SR))
    m.add(car_pass(2.4, 0.4), 16.4, 1.1, pan)
    m.add(horn(1.3, doppler=[1.06, 1.05, 0.93, 0.92]), 16.6, 0.8, pan[int(0.2 * SR):])
    m.add(heartbeat(3, 105), 19.1, 1.0)
    m.add(rewind_sfx(1.4), 21.0, 1.0)
    pan2 = np.linspace(-0.3, -0.85, int(2.6 * SR))
    m.add(car_pass(2.6, 0.45, 110), 26.6, 1.0, pan2)
    m.add(click(), 31.42, 0.9, -0.1)
    indicator(m, 31.5, 38.6, 0.5, -0.15)
    m.add(click(), 38.62, 0.8, -0.1)
    m.add(rumble(4.0), 36.6, 0.9, 0.5)
    m.add(chime(), 40.7, 0.8)
    return m.out(video.dur)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'signal.mp4'
    if len(sys.argv) > 2 and sys.argv[2] == 'stills':
        for s in shots:
            video.render_still(s.start + s.dur * 0.6, f'{out}_{s.start:05.1f}_{s.kind}.png')
    else:
        video.render(out, sound(), out + '_work')
