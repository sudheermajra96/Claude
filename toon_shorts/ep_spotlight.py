"""Episode (psychology): The Spotlight Effect. No dialogue, no music: SFX + emotional cues."""
import sys

from psych import *


def proud_end(ctx, world, t, lt, kw):
    engine.SCENES['face_scene'](ctx, world, t, lt, dict(expr='happy', light=1.0, sparkle=True))
    if engine.layer('mid'):
        stain(ctx, 860 + 150, 930, 70, 7)


engine.SCENES['proud_end'] = proud_end
engine.LAYERED_SCENES.add('proud_end')

world = World(dur=30, speed=const(0), camx=const(0))
step = 'step'
shots = [
    Shot(2.4, 'spill', bump=0.7),                                                                    # 0
    Shot(1.4, 'shocked_face'),                                                                       # 1
    Shot(3.2, 'office', hero_x=Key([(0, 520), (3.2, 860)], 'lin'), spot=Key([(0, 0), (0.25, 0), (0.26, 1)], step),
         stare=Key([(0, 0), (0.5, 0), (0.8, 1)]), expr='unsure', sweat=True),                        # 2
    Shot(2.0, 'eyes_montage'),                                                                       # 3
    Shot(2.6, 'office', hero_x=860, walking=False, spot=1, stare=1, hide=Key([(0, 0), (0.5, 1)]),
         hero_k=Key([(0, 0.95), (0.6, 0.95), (2.2, 0.62)]), expr='unsure', sweat=True),              # 4
    Shot(3.6, 'office', hero_x=860, walking=False, hero_k=0.62, hide=1, expr='unsure',
         spot=Key([(0, 1), (0.3, 1), (0.31, 0)], step), stare=Key([(0, 1), (0.3, 1), (0.6, 0)])),     # 5
    Shot(3.0, 'office', hero_x=860, walking=False, hero_k=0.62, hide=1, expr='calm',
         bubbles=[0.3, 0.8, 1.3, 1.8]),                                                              # 6
    Shot(2.4, 'office', hero_k=Key([(0, 0.62), (0.8, 0.95)]), hide=Key([(0, 1), (0.9, 1), (1.2, 0)]),
         hero_x=Key([(0, 860), (0.9, 860), (2.4, 1080)], 'lin'), expr='happy'),                       # 7
    Shot(4.4, 'stat_card'),                                                                          # 8
    Shot(2.2, 'proud_end'),                                                                          # 9
]
video = Video(['Why it feels like EVERYONE', 'is staring at you'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]


def sound():
    m = Mixer(video.dur)
    m.add(office_tone(S[3]), 0, 1.0)
    m.add(office_tone(video.dur - S[4]), S[4], 1.6)
    for i in (2, 3, 4, 6, 8, 9):
        m.add(cut_whoosh(), S[i] - 0.12, 0.45)
    # 0-1: the spill
    b = S[0] + 0.7
    m.add(head_swish(), b - 0.25, 0.8, 0.5)
    m.add(thud(), b, 0.6, 0.3)
    m.add(splash(), b + 0.05, 1.0, 0.1)
    m.add(sad_violin(), b + 0.4, 1.0)
    m.add(impact(), S[1], 0.35)
    # 2: spotlight + everyone turns
    t = S[2] + 0.1
    while t < E[2]:
        m.add(footsteps(0.12, 100), t, 0.5)
        t += 1 / 2.8
    m.add(spotlight_clunk(), S[2] + 0.25, 1.0)
    m.add(hum(E[5] - S[2] - 0.25), S[2] + 0.25, 0.35)
    for j, n in enumerate(NPCS):
        m.add(head_swish(), S[2] + 0.5 + j * 0.06, 0.7, (n['x'] - 960) / 960)
    m.add(murmur(2.6), S[2] + 0.7, 0.3)
    # 3: eyes everywhere
    m.add(heartbeat(5, 125), S[3], 1.0)
    for j in range(14):
        m.add(pop(), S[3] + j * 0.1, 0.25, (-1) ** j * 0.5)
    # 4: hide + shrink
    m.add(page_flip(), S[4] + 0.2, 0.8)
    m.add(murmur(2.4), S[4], 0.22)
    m.add(slide_whistle(900, 260, 1.6), S[4] + 0.6, 0.5)
    # 5: reality check
    m.add(record_scratch(), S[5], 0.9)
    m.add(spotlight_clunk(), S[5] + 0.3, 0.7)
    m.add(typing(6.4), S[5] + 0.4, 3.5, -0.6)
    m.add(notif(), S[5] + 1.0, 1.6, -0.25)
    m.add(sip(), S[5] + 1.5, 2.2, 0.3)
    m.add(snore(6.4), S[5] + 0.4, 2.6, 0.75)
    # 6: their own worries
    for j, b0 in enumerate(shots[6].kw['bubbles']):
        m.add(pop(), S[6] + b0, 1.8, (NPCS[j]['x'] - 960) / 960)
        m.add(bell(midi(88 + j * 2), 0.5), S[6] + b0 + 0.05, 0.5, (NPCS[j]['x'] - 960) / 960)
    m.add(sip(), S[6] + 2.2, 1.8, 0.3)
    # 7: relief
    m.add(slide_whistle(300, 1000, 0.8), S[7], 0.5)
    m.add(success_jingle(), S[7] + 1.0, 0.9)
    t = S[7] + 0.95
    while t < E[7]:
        m.add(footsteps(0.12, 100), t, 0.5)
        t += 1 / 2.8
    # 8: the stat card
    m.add(impact(), S[8], 0.4)
    m.add(pop(), S[8] + 0.7, 0.8)
    m.add(bell(midi(57), 1.0), S[8] + 1.3, 0.9)
    m.add(pop(), S[8] + 1.6, 0.8)
    m.add(success_jingle(), S[8] + 2.2, 0.8)
    m.add(chime(), S[8] + 2.6, 0.5)
    # 9: proud
    m.add(sparkle(), S[9] + 0.1, 1.6, 0.3)
    m.add(success_jingle(), S[9] + 0.2, 0.6)
    return m.out(video.dur)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'spotlight.mp4'
    if len(sys.argv) > 2 and sys.argv[2] == 'stills':
        for s in shots:
            video.render_still(s.start + s.dur * 0.6, f'{out}_{s.start:05.1f}_{s.kind}.png')
    else:
        video.render(out, sound(), out + '_work')
