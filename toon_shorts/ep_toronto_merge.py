"""Toronto: how to MERGE onto the highway (the right way). Multi-angle: chase cam, inside, mirror,
shoulder check, top view, dashboard. SFX only."""
from toronto import *

engine.DAY = True
speed = Key([(0, 15), (6.6, 15), (11.0, 25), (40, 25)], 'lin')
traffic = [
    dict(x=LANE_R, col='#3a7bd5', rel=Key([(0, -60), (11, -16), (13.2, -6), (14.4, -4), (15.2, -1), (16.2, 4),
                                            (17.4, 10), (18.8, 14), (22, 16), (40, 16)])),          # A: passes us
    dict(x=LANE_R, col='#f4f4f6', rel=Key([(0, -130), (11, -48), (15.2, -34), (18.8, -22), (22, -18), (40, -18)])),  # B
    dict(x=LANE_R, col='#37b26c', rel=Key([(0, -175), (40, -52)])),
    dict(x=LANE_R, col='#7a4fd0', rel=Key([(0, 60), (40, 72)])),
    dict(x=LANE_L, col='#c9c9d6', rel=Key([(0, -90), (40, 160)], 'lin')),
    dict(x=LANE_L, col='#f2a541', rel=Key([(0, 30), (40, 120)], 'lin')),
    dict(x=-7.0, col='#e05d5d', oncoming=True, z0=400),
    dict(x=-10.6, col='#f4f4f6', oncoming=True, z0=700),
    dict(x=-7.0, col='#3a7bd5', oncoming=True, z0=1000),
]
world = TorWorld(28, speed, -110.0, Key([(0, 0), (19.3, 0), (21.5, -3.6), (40, -3.6)]),
                 blinking([(4.3, 22.4)]), traffic)
shots = [
    Shot(4.0, 'tor_chase', cam='chase'),                         # 0  establishing: ramp + CN Tower
    Shot(2.6, 'tor_chase', cam='close', hud=False),              # 1  signal early (blinking indicator)
    Shot(3.0, 'tor_inside'),                                     # 2  speed up on the ramp
    Shot(1.4, 'dash2'),                                          # 3  matching traffic speed
    Shot(2.2, 'tor_mirror'),                                     # 4  mirror check
    Shot(2.0, 'tor_shoulder'),                                   # 5  shoulder check
    Shot(3.6, 'tor_top', gap=True, scale=30.0, xc=2.6),                              # 6  find a gap (top view)
    Shot(3.2, 'tor_chase', cam='chase'),                         # 7  merge smoothly
    Shot(2.6, 'tor_inside'),                                     # 8  signal off, keep pace
    Shot(3.0, 'tor_chase', cam='wide', hud=False),               # 9  recap
]
video = Video(['How to MERGE onto', 'the highway'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.3, E[0] - 0.2, location_tag('Toronto, ON')),
    (S[1], E[1], step_badge(1)), (S[1] + 0.2, E[1], caption_in_scene('Signal early')),
    (S[2], E[3], step_badge(2)), (S[2] + 0.2, E[3], caption_in_scene('Speed up to match traffic')),
    (S[4], E[4], step_badge(3)), (S[4] + 0.2, E[4], caption_in_scene('Check your mirror')),
    (S[5], E[5], step_badge(4)), (S[5] + 0.2, E[5], caption_in_scene('Shoulder check: blind spot!')),
    (S[6], E[6], step_badge(5)), (S[6] + 0.2, E[6], caption_in_scene('Find a safe gap')),
    (S[7], E[7], step_badge(6)), (S[7] + 0.2, E[7], caption_in_scene('Merge smoothly')),
    (S[8], E[8], step_badge(7)), (S[8] + 0.3, E[8], caption_in_scene('Signal off, keep pace')),
    (S[9] + 0.2, E[9], caption_in_scene('Signal. Speed up. Check. Merge.')),
]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.28)
    m.add(click(), 4.3, 0.8)
    indicator(m, 4.3, 22.4, 0.4, -0.2)
    m.add(click(), 22.4, 0.7)
    for i in (1, 2, 4, 5, 6, 7, 8):
        m.add(pop(), S[i] + 0.2, 0.6)
    m.add(head_swish(), S[4] + 0.05, 1.0, -0.5)
    m.add(head_swish(), S[5] + 0.05, 1.2, -0.6)
    m.add(car_pass(2.6, 0.45, 105), 13.6, 0.9, np.linspace(-0.6, 0.1, int(2.6 * SR)))
    m.add(rumble(3.0), 6.6, 0.8)
    m.add(car_pass(2.4, 0.5, 110), 9.6, 0.6, np.linspace(-0.7, -0.2, int(2.4 * SR)))
    m.add(whoosh(1.2, 0.5), 19.6, 0.8, -0.3)
    m.add(chime(), S[8] + 0.35, 0.5)
    m.add(success_jingle(), S[9] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'toronto_merge.mp4')
