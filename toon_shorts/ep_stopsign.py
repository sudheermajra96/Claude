"""Episode: How to AVOID a STOP sign ticket (2D house style, daylight). No talking, SFX only."""
import sys

from street import *

engine.DAY = True
step = 'step'
speedA = Key([(0, 9.6), (5.0, 9.6), (6.4, 4.2), (6.9, 4.2), (7.6, 7), (9.5, 12), (11.4, 12), (12.6, 4), (13.4, 0), (22.6, 0)], 'lin')
speedB = Key([(22.6, 11), (23.4, 11), (25.6, 6), (27.0, 4.5), (28.4, 0), (33.9, 0), (35.0, 5), (36.4, 9), (41.5, 11)], 'lin')
world = StreetWorld(
    41.5, [(0, 62.0, speedA), (22.6, 43.5, speedB)],
    camx=Key([(0, DRIVER_X), (11.6, DRIVER_X), (13.0, 2.5), (21.2, 2.5), (21.21, DRIVER_X)]),
    police_flash=Key([(7.8, 0), (8.1, 1), (21.1, 1), (21.2, 0)], 'lin'))
world.headlights = const(0)

xA = Key([(4, -45), (6.4, -14), (7.1, -8), (21, -8)])
xB1 = Key([(31.2, -45), (32.9, 45)], 'lin')
xB2 = Key([(32.2, 45), (33.6, -45)], 'lin')
behind = Key([(7.6, 45), (9.0, 22), (10.0, 13), (13.6, 8)])


def cross_cars(t):
    out = []
    if 4 <= t < 21.2:
        out.append((xA(t), ZI - 3, '#3a7bd5'))
    if 31.2 <= t < 32.9:
        out.append((xB1(t), ZI - 3, '#37b26c'))
    if 32.2 <= t < 33.6:
        out.append((xB2(t), ZI + 3, '#f2a541'))
    return out


def police(t):
    if 7.6 <= t < 21.2:
        return [(world.ego_z(t) - behind(t), world.camx(t) + 0.45, True)]
    if t >= 30.0:
        return [(ZI + 4, 9.0, False)]
    return []


def officer_at(t):
    return [(ZI + 8.5, 6.2)] if t >= 30.0 else []


C = dict(cross_cars=cross_cars, police=police, officer_at=officer_at)
shots = [
    Shot(3.2, 'street_pov', **C),                                                                    # 0
    Shot(1.8, 'face_day', expr='calm'),                                                              # 1
    Shot(2.6, 'street_pov', **C),                                                                    # 2
    Shot(2.4, 'rear_mirror_day', **C),                                                               # 3
    Shot(1.4, 'face_day', expr='shock', shake=1.0),                                                  # 4
    Shot(2.2, 'street_pov', **C),                                                                    # 5
    Shot(3.6, 'window_ticket', give=Key([(0, 0), (2.5, 0), (3.3, 1)])),                              # 6
    Shot(2.4, 'ticket_close'),                                                                       # 7
    Shot(1.6, 'face_day', expr='sad'),                                                               # 8
    Shot(1.4, 'rewind_seq'),                                                                         # 9
    Shot(3.0, 'street_pov', **C),                                                                    # 10
    Shot(1.4, 'pedals', pos=Key([(0, 0), (0.4, 0), (0.9, 1)]), press=Key([(0, 0), (0.9, 0), (1.4, 0.55)]), gas=0.2),  # 11
    Shot(2.4, 'street_pov', **C),                                                                    # 12
    Shot(1.4, 'dash'),                                                                               # 13
    Shot(3.0, 'street_pov', look=Key([(0, 0), (0.25, 0), (0.7, 0.35), (1.1, 0.35), (1.6, -0.35), (2.0, -0.35),
                                      (2.4, 0.2), (2.7, 0.2), (3.0, 0)]), **C),                      # 14
    Shot(2.6, 'street_pov', **C),                                                                    # 15
    Shot(2.4, 'officer_ok'),                                                                         # 16
    Shot(2.2, 'face_day', expr='happy'),                                                             # 17
]
shots[9].kw.update(srcs=list(reversed(shots[0:9])), dur=shots[9].dur)
video = Video(['How to AVOID a', 'STOP sign ticket'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[2] + 0.2, E[2], caption_in_scene('Rolling stop...')),
    (S[2], E[8], badge('WRONG', '#e0393e')),
    (S[10], E[17], badge('RIGHT', '#22a356')),
    (S[10] + 0.2, E[10], caption_in_scene('1. Slow down early')),
    (S[12] + 0.2, E[13], caption_in_scene('2. FULL stop before the line')),
    (S[14], E[14], caption_in_scene('3. Look left, right, left')),
    (S[15], E[15], caption_in_scene("4. Go when it's clear")),
    (S[17], E[17], caption_in_scene('Stop. Look. Go.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.8), 0, 0.55)
    m.add(birds(video.dur, 3), 0, 0.3, 0.3)
    m.add(whistle_tune(), S[1] + 0.1, 1.0)
    # wrong way
    m.add(brake_squeal(0.8), 5.6, 0.15)
    m.add(brake_squeal(1.0), 6.6, 0.5, -0.5)
    m.add(horn(0.8), 7.0, 0.6, -0.5)
    m.add(siren_whoop(2), S[3] + 0.2, 1.0, 0.0)
    m.add(siren_wail(5.4), S[3] + 1.1, 0.8)
    m.add(impact(), S[4], 0.35)
    m.add(siren_whoop(1), S[5] + 0.1, 0.8)
    m.add(brake_squeal(0.8), S[5] + 1.0, 0.2)
    m.add(thud(), S[5] + 1.9, 0.4)
    m.add(knock(), S[6] + 0.1, 0.9, -0.4)
    m.add(window_motor(0.8), S[6] + 0.5, 0.8, -0.4)
    m.add(scribble(2.0), S[6] + 0.3, 1.2, -0.3)
    m.add(paper_rip(), S[6] + 2.4, 1.0, -0.3)
    m.add(paper_rustle(0.6), S[6] + 2.9, 1.0, -0.2)
    m.add(thud(), S[7] + 0.5, 0.7)
    m.add(impact(), S[7] + 0.5, 0.3)
    m.add(sad_violin(), S[7] + 0.8, 1.0)
    m.add(rewind_sfx(1.4), S[9], 1.0)
    # right way
    m.add(brake_squeal(1.0), S[11] + 0.6, 0.12)
    m.add(thud(), 28.4, 0.35)
    m.add(bell(midi(84), 0.8), S[13] + 0.3, 0.7)
    for k, tt in enumerate((0.6, 1.4, 2.3)):
        m.add(head_swish(), S[14] + tt, 0.6, (-0.5, 0.5, -0.5)[k])
    m.add(car_pass(1.9, 0.5, 100), S[14] + 0.4, 1.0, np.linspace(-0.9, 0.9, int(1.9 * SR)))
    m.add(car_pass(1.6, 0.5, 115), S[14] + 1.4, 0.9, np.linspace(0.9, -0.9, int(1.6 * SR)))
    m.add(success_jingle(), S[16] + 0.3, 0.9)
    m.add(sparkle(), S[16] + 0.4, 0.6, 0.3)
    m.add(chime(), S[17] + 0.1, 0.7)
    return m.out(video.dur)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'stopsign.mp4'
    if len(sys.argv) > 2 and sys.argv[2] == 'stills':
        for s in shots:
            video.render_still(s.start + s.dur * 0.6, f'{out}_{s.start:05.1f}_{s.kind}.png')
    else:
        video.render(out, sound(), out + '_work')
