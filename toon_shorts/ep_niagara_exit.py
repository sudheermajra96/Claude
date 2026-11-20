"""Niagara Falls (QEW): how to EXIT the highway, the right way. Multi-angle, SFX only."""
from niagara import *

engine.DAY = True
speed = Key([(0, 27.8), (17.0, 27.8), (21.6, 15.0), (23.4, 13.9), (40, 13.9)], 'lin')
lat = Key([(0, 0), (5.8, 0), (7.6, 3.6), (15.4, 3.6), (17.0, 7.2), (40, 7.2)])
Z0 = -418.0
traffic = [
    dict(x=LANE_R, col='#3a7bd5', z0=Z0 + 70, v=26.5),       # right lane, ahead
    dict(x=LANE_R, col='#f4f4f6', z0=Z0 - 50, v=29.2),       # right lane, behind: passes us as we slow
    dict(x=LANE_L, col='#37b26c', z0=Z0 - 70, v=32.0),       # left lane, faster: passes on the left
    dict(x=LANE_L, col='#f2a541', z0=Z0 + 160, v=29.5),
]
oncoming = [dict(x=-7.0, col='#e05d5d', z0=-100), dict(x=-10.6, col='#c9c9d6', z0=250),
            dict(x=-7.0, col='#7a4fd0', z0=600), dict(x=-10.6, col='#3a7bd5', z0=900)]
world = NWorld(28, speed, Z0, lat, blinking([(5.2, 7.9), (9.0, 17.4)]), traffic, oncoming)

shots = [
    Shot(3.4, 'n_chase', cam='chase'),                  # 0 establishing, left lane
    Shot(1.8, 'n_inside'),                              # 1 exit sign
    Shot(3.2, 'n_chase', cam='close_r', hud=False),     # 2 move to the right lane early
    Shot(2.0, 'dash2'),                                 # 3 signal right early
    Shot(2.0, 'n_mirror'),                              # 4 mirror
    Shot(1.8, 'n_shoulder'),                            # 5 shoulder
    Shot(3.2, 'n_top', scale=30.0, ox=430),             # 6 move into the exit lane (top view)
    Shot(2.8, 'n_chase', cam='chase'),                  # 7 slow down in the exit lane
    Shot(2.8, 'n_inside'),                              # 8 ramp speed
    Shot(3.6, 'n_chase', cam='wide', hud=False),        # 9 recap
]
video = Video(['How to EXIT', 'the highway'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
steps = ['Watch for your exit sign', 'Move to the right lane early', 'Signal right early', 'Check your mirror',
         'Shoulder check', 'Move into the exit lane', 'NOW slow down, in the exit lane', 'Follow the ramp speed']
video.overlays = [(0.3, E[0] - 0.2, location_tag('Niagara Falls, ON')),
                  (S[9] + 0.2, E[9], caption_in_scene('Sign. Lane. Signal. Check. Exit.'))]
for n, txt in enumerate(steps, 1):
    video.overlays += [(S[n], E[n], step_badge(n)), (S[n] + 0.15, E[n], caption_in_scene(txt))]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.14)
    for a, b in ((5.2, 7.9), (9.0, 17.4)):
        m.add(click(), a, 1.2)
        indicator(m, a, b, 0.65, 0.2)
        m.add(click(), b, 1.0)
    for i in range(1, 9):
        m.add(pop(), S[i] + 0.15, 0.8)
    m.add(head_swish(), S[4] + 0.05, 1.0, 0.5)
    m.add(head_swish(), S[5] + 0.05, 1.2, 0.6)
    m.add(car_pass(2.6, 0.5, 108), 15.9, 0.9, np.linspace(-0.2, -0.7, int(2.6 * SR)))     # left-lane car passes
    m.add(car_pass(2.6, 0.5, 112), 19.5, 1.0, np.linspace(-0.1, -0.5, int(2.6 * SR)))     # right-lane car passes as we slow
    m.add(brake_squeal(1.2), 18.8, 0.08)
    m.add(chime(), S[8] + 0.8, 0.5)
    m.add(success_jingle(), S[9] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'niagara_exit.mp4')
