"""Episode: What happens if you wake up at 5 AM for 30 days?"""
import sys

from life import *

world = World(dur=45, speed=const(0), camx=const(0))
ring_slap = Key([(0, 0), (1.3, 0), (1.7, 1), (2.0, 1), (2.4, 0)])

shots = [
    Shot(1.0, 'bedroom', mode='sleep', light=0.05, clock=lambda lt: '4:59'),                        # 0
    Shot(2.4, 'bedroom', mode='sleep', expr='tired', light=0.05, clock=lambda lt: '5:00',
         ring=Key([(0, 1), (1.7, 1), (1.71, 0)], 'step'), slap=ring_slap),                            # 1
    Shot(2.6, 'bedroom', mode='sit', expr='tired', light=0.1, clock=lambda lt: '5:01'),              # 2
    Shot(2.8, 'desk', action='nod', expr='tired', light=0.15),                                        # 3
    Shot(3.2, 'bedroom', mode='sleep', light=0.0, lamp=Key([(0, 1), (1.6, 1), (1.61, 0)], 'step'),
         phone=True, clock=lambda lt: '22:00'),                                                       # 4
    Shot(2.6, 'bedroom', mode='reach', expr='calm', light=0.15, clock=lambda lt: '5:00',
         ring=Key([(0, 1), (0.6, 1), (0.61, 0)], 'step'),
         reach=Key([(0, 0), (0.55, 1), (1.0, 1), (1.5, 0)])),                                         # 5
    Shot(2.6, 'kitchen', light=0.35, drink=Key([(0, 0), (0.6, 1), (2.0, 1), (2.4, 0)])),              # 6
    Shot(3.4, 'park', light=0.6, expr='happy'),                                                        # 7
    Shot(3.0, 'desk', action='write', expr='focus', light=0.5,
         items=[(0.3, 'Read 10 pages'), (1.1, 'Workout'), (1.9, 'Deep work')]),                        # 8
    Shot(3.2, 'bedroom', mode='stretch', expr='happy', light=0.35, clock=lambda lt: '4:58'),          # 9
    Shot(1.0, 'park', light=0.85, expr='happy'),                                                       # 10
    Shot(1.0, 'desk', action='read', expr='focus', light=0.8, books=8),                                # 11
    Shot(1.0, 'kitchen', light=0.9, expr='happy', drink=Key([(0, 0.0), (0.5, 1)])),                    # 12
    Shot(4.4, 'checklist', title='After 30 days', items=[
        (0.3, '2 quiet hours just for you'), (1.1, 'Calm, unrushed mornings'),
        (1.9, 'Time to move & plan'), (2.7, 'Easier every single week')]),                           # 13
    Shot(3.0, 'closeup', expr='proud', light=1.0),                                                     # 14
]
video = Video(['What happens if you wake up', 'at 5 AM for 30 days?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]

energy = Key([(0, 0.1), (S[5], 0.1), (S[5] + 0.5, 0.5), (S[9], 0.5), (S[9] + 0.6, 0.95), (E[12], 1.0)])
video.overlays = [
    (S[0], E[3], day_badge('DAY 1')),
    (S[5], E[8], day_badge('DAY 7')),
    (S[9], E[12], day_badge('DAY 30')),
    (S[0], E[12], energy_bar(lambda lt: energy(lt))),
    (S[2] + 0.2, E[2], caption_in_scene('Day 1: this is AWFUL')),
    (S[3] + 0.2, E[3], caption_in_scene('Brain: still asleep')),
    (S[4] + 0.2, E[4], caption_in_scene('The secret: bed by 10 PM')),
    (S[6] + 0.2, E[6], caption_in_scene('Water first')),
    (S[7] + 0.2, E[7], caption_in_scene('Move your body')),
    (S[8] + 0.2, E[8], caption_in_scene('Plan the day', y=1020)),
    (S[9] + 0.2, E[9], caption_in_scene('Wakes up BEFORE the alarm')),
    (S[14] + 0.2, E[14], caption_in_scene('Small habits. Big change.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(music_bed(video.dur, bright_from=S[5]), 0, 1.0)
    m.add(crickets(E[1]), 0, 1.0)
    m.add(crickets(shots[4].dur), S[4], 1.0)
    m.add(alarm_beeps(1.7), S[1], 0.8, -0.3)
    m.add(thud(), S[1] + 1.7, 0.7, -0.3)
    m.add(click(), S[1] + 1.7, 0.8, -0.3)
    m.add(sad_trombone(), S[2] + 0.3, 0.9)
    for c in (0, 1.6):
        m.add(soft_whoosh(), S[3] + c + 0.4, 0.6)
        m.add(pop(), S[3] + c + 1.2, 0.6)
    m.add(page_flip(), S[3] + 2.5, 0.6)
    m.add(click(), S[4] + 1.6, 0.9, -0.3)
    m.add(soft_whoosh(), S[5], 0.8)
    m.add(alarm_beeps(0.6), S[5], 0.7, -0.3)
    m.add(click(), S[5] + 0.6, 0.8, -0.3)
    for g in (0.8, 1.1, 1.4, 1.7):
        m.add(gulp(), S[6] + g, 0.9)
    m.add(birds(shots[7].dur), S[7], 0.8, 0.3)
    m.add(footsteps(shots[7].dur), S[7], 0.8)
    m.add(scribble(2.6), S[8] + 0.2, 0.8, 0.1)
    for t_on, _ in shots[8].kw['items']:
        m.add(pop(), S[8] + t_on + 0.35, 0.7)
    m.add(soft_whoosh(), S[9], 0.8)
    m.add(birds(shots[9].dur, 4), S[9], 0.6, 0.4)
    m.add(chime(), S[9] + 0.8, 0.6)
    for i in (10, 11, 12, 13):
        m.add(soft_whoosh(), S[i], 0.6)
    m.add(footsteps(1.0), S[10], 0.6)
    m.add(page_flip(), S[11] + 0.3, 0.6)
    m.add(gulp(), S[12] + 0.6, 0.8)
    for t_on, _ in shots[13].kw['items']:
        m.add(pop(), S[13] + t_on, 0.8)
    m.add(chime(), S[14] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'wake5am.mp4'
    if len(sys.argv) > 2 and sys.argv[2] == 'stills':
        for s in shots:
            video.render_still(s.start + s.dur * 0.6, f'{out}_{s.start:05.1f}_{s.kind}.png')
    else:
        video.render(out, sound(), out + '_work')
