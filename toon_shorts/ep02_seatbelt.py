"""02 - ALWAYS wear your seatbelt (day street)."""
from kit import *

engine.DAY = True
# part A: drive, sudden stop at ~7.6 s ; part B (after rewind at 12.4) same drive but belted
spA = Key([(0, 0), (1.5, 0), (3.5, 11), (7.5, 11), (8.0, 0), (12.4, 0)], 'lin')
spB = Key([(12.4, 0), (16.2, 0), (18.2, 11), (21.6, 11), (22.4, 0), (40, 0)], 'lin')
world = StreetWorld(30, [(0, -40, spA), (12.4, -40, spB)], camx=const(DRIVER_X))
world.headlights = const(0)
world.shake = Key([(7.4, 0), (7.5, 1), (8.4, 0), (21.5, 0), (21.6, 0.5), (22.2, 0)], 'lin')
world.ego_brake = Key([(7.45, 0), (7.5, 1), (11.9, 1), (12.0, 0), (21.55, 0), (21.6, 1), (23, 1)], 'step')
# a ball rolls out / car ahead brakes: use a car ahead that brakes hard
relA = Key([(0, 40), (7.4, 26), (8.0, 9), (12.4, 9)], 'lin')
relB = Key([(12.4, 40), (21.5, 26), (22.2, 14), (30, 14)], 'lin')


def extra(t):
    rel, br = (relA, 7.4) if t < 12.4 else (relB, 21.5)
    brake = 1.0 if t >= br else 0.0
    return [(world.ego_z(t) + rel(t), lambda c, cam, d: car_rear_simple(c, cam, 1.75, d, '#7a4fd0', t, brake))]


P = dict(extra=extra)
shots = [
    Shot(2.0, 'dash2', belt_warn=1),                                                               # 0
    Shot(1.6, 'face_day', expr='annoyed', belt=False),                                            # 1
    Shot(3.8, 'street_pov2', **P),                                                                 # 2
    Shot(1.6, 'face_day', expr='terror', belt=False, shake=1.0,
         lurch=Key([(0, 0), (0.15, 1), (0.6, 0.85), (1.6, 0.3)])),                                  # 3
    Shot(1.8, 'street_pov2', **P),                                                                 # 4
    Shot(1.6, 'face_day', expr='sad', belt=False),                                                 # 5
    Shot(1.2, 'rewind_seq'),                                                                       # 6
    Shot(2.4, 'buckle', pull=Key([(0, 0), (1.3, 1)]), click_t=1.35),                               # 7
    Shot(1.4, 'dash2', belt_warn=0),                                                               # 8
    Shot(3.6, 'street_pov2', **P),                                                                 # 9
    Shot(1.8, 'face_day', expr='relief', lurch=Key([(0, 0), (0.15, 0.25), (0.5, 0)])),             # 10
    Shot(2.6, 'face_day', expr='happy'),                                                           # 11
]
shots[6].kw.update(srcs=list(reversed(shots[0:6])), dur=shots[6].dur)
video = Video(['ALWAYS wear', 'your seatbelt!'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (S[1], E[5], badge('WRONG', '#e0393e')),
    (S[1] + 0.2, E[1], caption_in_scene('"Just a short drive..."')),
    (S[7], E[11], badge('RIGHT', '#22a356')),
    (S[7] + 0.2, E[7], caption_in_scene('1. Click it before you go')),
    (S[9] + 0.3, E[10], caption_in_scene('2. Sudden stop? You stay safe')),
    (S[11], E[11], caption_in_scene('Every trip. Every seat.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(car_ambience(world, video.dur), 0, 1.0)
    m.add(seatbelt_chime(5), 0.2, 0.9)
    m.add(screech(1.1, 1250), 7.45, 0.8)
    m.add(thud(), S[3] + 0.12, 1.0)
    m.add(impact(), S[3] + 0.12, 0.5)
    m.add(sad_violin(), S[5] + 0.1, 0.9)
    m.add(rewind_sfx(1.2), S[6], 1.0)
    m.add(paper_rustle(1.0), S[7] + 0.2, 0.6)
    m.add(click(), S[7] + 1.35, 1.2)
    m.add(chime(), S[8] + 0.2, 0.6)
    m.add(screech(0.9, 1200), 21.55, 0.6)
    m.add(thud(), 21.65, 0.35)
    m.add(success_jingle(), S[11] + 0.1, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'ep02_seatbelt.mp4')
