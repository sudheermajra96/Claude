"""Episode: ALWAYS keep a safe distance!"""
import sys

from engine import *

world = World(
    dur=36,
    speed=Key([(0, 30), (11, 30), (14, 0), (16.7, 0), (16.71, 30), (26.8, 30), (32, 0), (36, 0)], 'lin'),
    camx=const(1.4),
    vehicles=[
        Vehicle('car', 1.8, Key([(0, 7), (7.6, 7), (9, 5.8), (10.5, 4.6), (12.1, 3.6), (13.6, 2.6), (14.7, 2.5),
                                 (16.7, 2.5), (16.71, 30), (26.6, 30), (28.3, 26), (29.9, 19), (32, 11), (36, 10.5)]),
                color='#c23b3b',
                brake=Key([(7.5, 0), (7.6, 1), (16.6, 1), (16.7, 0), (26.5, 0), (26.6, 1), (36, 1)], 'lin')),
    ],
    ego_brake=Key([(10.9, 0), (11.0, 1), (16.6, 1), (16.7, 0), (28.8, 0), (28.9, 1)], 'step'),
    shake=Key([(12.1, 0), (12.2, 1), (14.0, 0.5), (14.6, 0)], 'lin'),
)

shots = [
    Shot(3.5, 'pov'),
    Shot(1.8, 'dash'),
    Shot(1.8, 'face', expr='calm'),
    Shot(2.0, 'pov'),
    Shot(1.4, 'face', expr='shock', shake=0.6),
    Shot(1.6, 'pedals', pos=Key([(0, 0), (0.2, 0), (0.5, 1)]), press=Key([(0, 0), (0.5, 0), (0.6, 1)])),
    Shot(2.6, 'pov'),
    Shot(2.0, 'face', expr='relief', sweat=True),
    Shot(1.4, 'rewind', src_t=Key([(0, 14), (1.4, 2)], 'lin')),
    Shot(3.0, 'pov'),
    Shot(3.6, 'pov'),
    Shot(1.6, 'face', expr='calm'),
    Shot(2.0, 'pov'),
    Shot(1.6, 'pedals', pos=Key([(0, 0), (0.3, 0), (0.8, 1)]), press=Key([(0, 0), (0.8, 0), (1.3, 0.6)]),
         gas=0.4),
    Shot(3.0, 'pov'),
    Shot(2.6, 'face', expr='happy'),
]

overlays = [
    (0.5, 3.5, caption_in_scene('Way too close...')),
    (7.1, 16.7, badge('WRONG', '#e0393e')),
    (18.1, 35.5, badge('RIGHT', '#22a356')),
    (18.4, 21.1, caption_in_scene('Keep a 3-second gap')),
    (21.3, 22.3, caption_in_scene('1...', size=110)),
    (22.3, 23.3, caption_in_scene('2...', size=110)),
    (23.3, 24.6, caption_in_scene('3!', size=110)),
    (32.9, 35.5, caption_in_scene('Space = time to react')),
]

video = Video(['ALWAYS keep a safe', 'distance!'], world, shots, overlays)


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur), 0, 1.8)
    m.add(brake_squeal(1.2), 7.65, 0.5, 0.2)
    m.add(thud(), 10.85, 1.0)
    m.add(screech(3.0, 1050), 11.0, 0.8, 0)
    m.add(screech(2.4, 1400), 11.3, 0.4, 0.3)
    m.add(heartbeat(4, 115), 14.8, 1.1)
    m.add(rewind_sfx(1.4), 16.7, 1.0)
    for i, t in enumerate((21.3, 22.3, 23.3)):
        m.add(tick(True), t, 0.9)
        if i == 2:
            m.add(chime(), t, 0.6)
    m.add(brake_squeal(1.0), 26.65, 0.25, 0.2)
    m.add(thud(), 28.9, 0.45)
    m.add(chime(), 33.0, 0.8)
    return m.out(video.dur)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'distance.mp4'
    if len(sys.argv) > 2 and sys.argv[2] == 'stills':
        for s in shots:
            video.render_still(s.start + s.dur * 0.6, f'{out}_{s.start:05.1f}_{s.kind}.png')
    else:
        video.render(out, sound(), out + '_work')
