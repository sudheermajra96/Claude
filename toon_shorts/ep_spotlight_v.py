"""Vertical (full 9:16) cut of the Spotlight Effect episode. Reuses the sound design of ep_spotlight."""
import sys

import ep_spotlight as ep
from psych import *

step = 'step'
walk_in = Key([(0, 520), (3.2, 860)], 'lin')
walk_out = Key([(0, 860), (0.9, 860), (2.4, 1080)], 'lin')
shots = [
    Shot(2.4, 'spill', bump=0.7, fx=990, fy=90),                                                            # 0
    Shot(1.4, 'shocked_face', fx=920, fy=150),                                                               # 1
    Shot(3.2, 'office', hero_x=walk_in, fx=walk_in, spot=Key([(0, 0), (0.25, 0), (0.26, 1)], step),
         stare=Key([(0, 0), (0.5, 0), (0.8, 1)]), expr='unsure', sweat=True),                        # 2
    Shot(2.0, 'eyes_montage', fx=960),                                                               # 3
    Shot(2.6, 'office', hero_x=860, fx=860, walking=False, spot=1, stare=1, hide=Key([(0, 0), (0.5, 1)]),
         hero_k=Key([(0, 0.95), (0.6, 0.95), (2.2, 0.62)]), expr='unsure', sweat=True),              # 4
    Shot(3.6, 'office', hero_x=860, walking=False, hero_k=0.62, hide=1, expr='unsure',
         fx=Key([(0, 860), (0.6, 860), (3.6, 1660)]),
         spot=Key([(0, 1), (0.3, 1), (0.31, 0)], step), stare=Key([(0, 1), (0.3, 1), (0.6, 0)])),     # 5
    Shot(3.4, 'office', hero_x=860, walking=False, hero_k=0.62, hide=1, expr='calm',
         fx=Key([(0, 260), (0.5, 260), (1.2, 680), (2.2, 1240), (2.9, 1660), (3.4, 1660)]),
         bubbles=[0.25, 1.0, 2.0, 2.7]),                                                             # 6
    Shot(2.4, 'office', hero_k=Key([(0, 0.62), (0.8, 0.95)]), hide=Key([(0, 1), (0.9, 1), (1.2, 0)]),
         hero_x=walk_out, fx=walk_out, expr='happy'),                                                 # 7
    Shot(4.4, 'stat_card_v', screen=True),                                                           # 8
    Shot(2.2, 'proud_end', fx=930, fy=150),                                                                  # 9
]
video = Video(["Everyone's staring", "at you?"], ep.world, shots, vertical=True)

# reuse the episode's sound design with this cut's timing
ep.shots, ep.video = shots, video
ep.S = [s.start for s in shots]
ep.E = [s.start + s.dur for s in shots]

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'spotlight_vertical.mp4'
    if len(sys.argv) > 2 and sys.argv[2] == 'stills':
        for s in shots:
            video.render_still(s.start + s.dur * 0.6, f'{out}_{s.start:05.1f}_{s.kind}.png')
    else:
        video.render(out, ep.sound(), out + '_work')
