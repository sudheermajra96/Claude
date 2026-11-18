"""Episode: Phone first thing in the morning vs. phone LAST (no dialogue, beat-synced)."""
import sys

from life2 import *

MUSIC = '--music' in sys.argv  # default: sound effects only
world = World(dur=32, speed=const(0), camx=const(0))
PHONE_SPOT = (375, 600)

shots = [
    Shot(2.0, 'bedroom', mode='reach', phone=True, phone_mode='grab', expr='tired', light=0.05,
         clock=lambda lt: '7:00', ring=Key([(0, 1), (0.6, 1), (0.61, 0)], 'step'),
         reach_to=PHONE_SPOT, rest=(740, 520), look=(0, 1),
         reach=Key([(0, 0), (0.4, 0), (0.8, 1), (0.9, 1), (1.4, 0)]),
         taken=Key([(0, 0), (0.85, 0), (0.86, 1)], 'step')),                                        # 0
    Shot(3.0, 'phone_close', swipes=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5],
         notifs=[(0.75, '12 new likes', '#ff3b5c'), (1.75, 'You were tagged', '#118ab2'),
                 (2.25, 'Breaking news!', '#ff9f1c')]),                                           # 1
    Shot(2.0, 'face_scene', expr='tired', light=0.0, phone_glow=True, flicks=[0.0, 0.5, 1.0, 1.5]),  # 2
    Shot(2.0, 'clock_spin', mins=Key([(0, 1), (1.0, 9), (1.6, 33), (2.0, 58)], 'lin'),
         panic=Key([(0, 0), (2.0, 1)], 'lin')),                                                    # 3
    Shot(1.0, 'face_scene', expr='shock', light=0.25, shake=Key([(0, 1), (1, 0.3)], 'lin'), red=0.6),  # 4
    Shot(2.0, 'chaos'),                                                                              # 5
    Shot(1.0, 'rewind_seq'),                                                                         # 6
    Shot(2.0, 'bedroom', mode='reach', phone=True, phone_mode='stash', expr='calm', light=0.4,
         clock=lambda lt: '7:00', ring=Key([(0, 1), (0.5, 1), (0.51, 0)], 'step'),
         reach_to=PHONE_SPOT, reach=Key([(0, 0), (0.5, 0), (0.9, 1), (1.1, 1), (1.5, 0)]),
         taken=Key([(0, 0), (1.0, 0), (1.01, 1)], 'step'),
         drawer=Key([(0, 0), (0.95, 0), (1.15, 1), (1.5, 1), (1.75, 0)])),                          # 7
    Shot(2.0, 'bedroom', mode='stretch', expr='happy', light=0.6, clock=lambda lt: '7:05'),       # 8
    Shot(2.0, 'kitchen', light=0.7, expr='calm', drink=Key([(0, 0), (0.4, 1), (1.5, 1), (1.9, 0)]),
         drain_t=0.5, drain_d=1.0),                                                                # 9
    Shot(2.0, 'park', light=0.8, expr='happy', cadence=2.0),                                        # 10
    Shot(3.0, 'desk', action='write', expr='focus', light=0.85,
         items=[(0.15, 'Read 10 pages'), (1.15, 'Workout'), (2.15, 'Deep work')]),                 # 11
    Shot(2.0, 'face_scene', expr='proud', light=1.0, sparkle=True),                                 # 12
    Shot(3.0, 'split'),                                                                              # 13
]
shots[6].kw.update(srcs=list(reversed(shots[0:6])), dur=shots[6].dur)

video = Video(['Phone first thing in the morning', 'vs. phone LAST'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[0], E[5], badge('PHONE FIRST', '#e0393e')),
    (S[7], E[12], badge('PHONE LAST', '#22a356')),
]


def sound():
    m = Mixer(video.dur)
    # ---- music: tense pulse -> tape stop on the "late" hit; drop into happy groove after rewind
    if MUSIC:
        tense = tape_stop(music_tense(S[4], riser_from=S[3]))
        m.add(tense, 0, 1.25)
        happy = music_happy(video.dur - S[7])
        fade = np.ones(len(happy))
        fade[-int(0.6 * SR):] = np.linspace(1, 0, int(0.6 * SR))
        m.add(happy * fade, S[7], 0.75)
    else:
        # room tone instead of music: night crickets for A, morning birds for B
        m.add(crickets(S[3]), 0, 1.2)
        m.add(birds(video.dur - S[7], 9), S[7], 0.25, 0.4)
    # ---- transitions
    for i in (1, 2, 3, 5, 8, 9, 10, 11, 12):
        m.add(cut_whoosh(), S[i] - 0.12, 0.6)
    m.add(riser(2.0), S[3], 0.8)
    m.add(clock_ticks(2.0), S[3], 0.7)
    m.add(record_scratch(), S[4], 1.0)
    m.add(impact(), S[4], 0.9)
    m.add(rewind_sfx(1.0), S[6], 0.9)
    m.add(reverse_cymbal(1.0), S[6], 0.8)
    m.add(impact(), S[13], 0.8)
    m.add(whoosh(0.6, 0.3), S[13], 0.7)
    # ---- A: phone first
    m.add(alarm_beeps(0.6), S[0], 0.7, -0.3)
    m.add(cut_whoosh(), S[0] + 0.45, 0.6, -0.2)
    m.add(click(), S[0] + 0.85, 0.7, -0.2)
    for s0 in shots[1].kw['swipes']:
        m.add(swipe(), S[1] + s0, 1.2, 0.15)
    for n0, _, _ in shots[1].kw['notifs']:
        m.add(notif(), S[1] + n0, 0.8, 0.2)
    for f in shots[2].kw['flicks']:
        m.add(swipe(), S[2] + f, 0.45, 0.1)
    m.add(notif(), S[2] + 1.25, 0.5, 0.3)
    for b in (0.0, 0.75, 1.5):
        m.add(buzz(0.55), S[5] + b, 0.9, 0.35)
    for k in range(5):
        m.add(whoosh(0.4, 0.4), S[5] + k * 0.38, 0.35, (-1) ** k * 0.5)
    m.add(heartbeat(4, 150), S[5], 0.9)
    # ---- B: phone last
    m.add(alarm_beeps(0.5), S[7], 0.6, -0.3)
    m.add(drawer_slide(), S[7] + 0.95, 0.9, -0.3)
    m.add(thud(), S[7] + 1.72, 0.5, -0.3)
    m.add(click(), S[7] + 1.72, 0.5, -0.3)
    m.add(boing(), S[8] + 0.2, 0.8)
    m.add(birds(6.0, 7), S[8], 0.35, 0.4)
    for g in (0.5, 0.75, 1.0, 1.25):
        m.add(gulp(), S[9] + g, 0.9)
    m.add(chime(), S[9] + 1.6, 0.3)
    t = 0.125
    while t < E[10]:
        if t >= S[10]:
            m.add(footsteps(0.12, 100), t, 0.8, 0.0)
        t += 0.25
    m.add(scribble(2.9), S[11] + 0.05, 0.7, 0.1)
    for t_on, _ in shots[11].kw['items']:
        m.add(pop(), S[11] + t_on + 0.35, 0.8)
    m.add(sparkle(), S[12] + 0.1, 0.8, 0.3)
    m.add(chime(), S[13] + 0.25, 0.6)
    return m.out(video.dur)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'phone.mp4'
    if len(sys.argv) > 2 and sys.argv[2] == 'stills':
        for s in shots:
            video.render_still(s.start + s.dur * 0.6, f'{out}_{s.start:05.1f}_{s.kind}.png')
    else:
        video.render(out, sound(), out + '_work')
