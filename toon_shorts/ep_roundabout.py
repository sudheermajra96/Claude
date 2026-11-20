"""Roundabout, the right way: Carmel, Indiana (single-lane modern roundabout, counter-clockwise, yield left)."""
import math
import random

from citykit import *

engine.DAY = True
R_ISL, R_APRON, R_OUT = 9.0, 10.5, 15.5
BRICK = ['#a35d43', '#8a4b38', '#c98b6b', '#d8c3a0', '#6e3b2e', '#b56f52']


def rot(p, k):
    """Rotate (x, z) by k*90 degrees counter-clockwise on the map (south leg -> east leg -> ...)."""
    x, z = p
    for _ in range(k % 4):
        x, z = -z, x
    return (x, z)


def blinkfn(intervals, side):
    b = blinking(intervals)
    return lambda t: side if b(t) > 0.5 else None


# straight-through path from the south leg to the north leg (counter-clockwise around the east side)
BASE = ([(1.85, z) for z in range(-160, -29, 6)] + [(2.3, -23), (3.6, -18.5), (5.2, -14.2), (6.5, -11.26)] +
        [(13 * math.cos(math.radians(a)), 13 * math.sin(math.radians(a))) for a in range(-50, 51, 10)] +
        [(6.5, 11.26), (5.2, 14.2), (3.6, 18.5), (2.3, 23)] + [(1.85, z) for z in range(30, 161, 6)])


def through_path(k):
    """k: 0 = from south, 1 = from east (map rotation), 2 = from north, 3 = from west."""
    return Path([('S', [rot(p, k) for p in BASE])])


EGO_P = through_path(0)
P_WEST = through_path(3)      # enters from the west, passes in front of our entry (from our LEFT)
P_NORTH = through_path(2)     # north -> south, exits past our approach (oncoming)
P_EAST = through_path(1)      # east -> west across the north side

ego_speed = Key([(0, 13.4), (2.9, 13.4), (6.9, 0), (9.7, 0), (10.7, 6), (11.95, 6), (12.95, 0), (15.0, 0),
                 (16.5, 6.7), (21.4, 6.7), (24.4, 13.4), (40, 13.4)], 'lin')
ego = Mover(EGO_P, ego_speed, 6.9, EGO_P.s_near(1.85, -34.5), C_EGO, blink=blinkfn([(18.8, 22.4)], 'R'))
c7 = lambda v: Key([(-10, v), (60, v)])
carA = Mover(P_WEST, c7(6.7), 14.4, P_WEST.s_near(*rot((13 * math.cos(math.radians(50)), 13 * math.sin(math.radians(50))), 3)),
             '#3a7bd5', blink=blinkfn([(15.6, 18.5)], 'R'))
carB = Mover(P_WEST, c7(6.7), 20.6, P_WEST.s_near(6.5, -11.26) if False else P_WEST.s_near(*rot((6.5, -11.26), 3)), '#f2a541')
carC = Mover(P_NORTH, c7(7.5), 3.5, P_NORTH.s_near(-1.85, -24), '#37b26c')
carD = Mover(P_EAST, c7(7.0), 18.5, P_EAST.s_near(0, 13), '#f4f4f6')
others = [carA, carB, carC, carD]

ped1 = Ped(Key([(0, 6.0), (4.5, 6.0), (13.1, -6.0)], 'lin'), const(-29.0), top='#9a6fd0')
ped2 = Ped(const(-6.2), const(29.6), top='#f2c230', hair='#c7782e')
ped3 = Ped(Key([(0, 30), (30, 70)], 'lin'), const(6.0), top='#56b38a', skin='#8d5a3b', hair='#1b1b1b')
ped4 = Ped(const(-6.0), Key([(0, -70), (30, -40)], 'lin'), top='#e05d5d')


class Carmel:
    ground_col = C_GRASS
    sky = ('#5fb4f2', '#dcf1ff')

    def __init__(self):
        r = random.Random(4)
        self.blds, self.trees = [], []
        for k in range(4):
            for side in (-1, 1):
                d = 26.0
                while d < 220:
                    w = r.uniform(9, 15)
                    x0, x1 = (8.0, 8.0 + r.uniform(10, 16)) if side > 0 else (-8.0 - r.uniform(10, 16), -8.0)
                    z0, z1 = -d - w, -d
                    a, b = rot((x0, z0), k), rot((x1, z1), k)
                    self.blds.append((min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]),
                                      r.uniform(7, 13), r.choice(BRICK)))
                    d += w + 0.6
                for d in np.arange(34, 220, 12):
                    self.trees.append(rot((side * 5.6, -d), k))

    def skyline(self, ctx, view):
        # distant tree line + a white water tower
        b, sc = view.pt((-120, 0, 420)), view.scale((-120, 0, 420))
        if b and sc:
            for i in range(-8, 9):
                p = view.pt((i * 40, 0, 430))
                s2 = view.scale((i * 40, 0, 430))
                if p and s2:
                    ellipse(ctx, p[0], p[1] - 9 * s2, 22 * s2, 14 * s2)
                    setc(ctx, hexc('#6fa86a'))
                    ctx.fill()
            for lx in (-4, 4):
                q = view.pt((-120 + lx, 0, 420))
                if q:
                    ctx.move_to(*q)
                    ctx.line_to(b[0] + lx * 0.4 * sc, b[1] - 32 * sc)
            setc(ctx, hexc('#c9ccd6'))
            ctx.set_line_width(max(1, 1.2 * sc))
            ctx.stroke()
            ellipse(ctx, b[0], b[1] - 38 * sc, 9 * sc, 7 * sc)
            setc(ctx, hexc('#eef1f6'))
            ctx.fill()

    def ground(self, ctx, view, t):
        ring(ctx, view, 0, 0, 15.5, 19.0, C_WALK)
        for k in range(4):
            q = lambda x0, x1, z0, z1, c, y=0.0: fill_poly(ctx, view, [(*_xz(rot((x0, z0), k)), y), (*_xz(rot((x1, z0), k)), y),
                                                                       (*_xz(rot((x1, z1), k)), y), (*_xz(rot((x0, z1), k)), y)], c) \
                if False else quad_rot(ctx, view, k, x0, x1, z0, z1, c, y)
            q(4.0, 7.0, -260, -18, C_WALK)
            q(-7.0, -4.0, -260, -18, C_WALK)
            q(-3.9, 3.9, -260, -12, C_ASPH)
        disc(ctx, view, 0, 0, R_OUT, C_ASPH)
        ring(ctx, view, 0, 0, R_OUT - 0.2, R_OUT, C_LINE, 0.01)
        disc(ctx, view, 0, 0, R_APRON, hexc('#c9a27c'), 0.05)
        disc(ctx, view, 0, 0, R_ISL, hexc('#7fc36b'), 0.15, stroke=OUTL)
        disc(ctx, view, 0, 0, 5.0, hexc('#e9a3c0'), 0.16)
        for k in range(4):
            quad_rot(ctx, view, k, -3.95, -3.75, -260, -18, C_LINE, 0.01)
            quad_rot(ctx, view, k, 3.75, 3.95, -260, -18, C_LINE, 0.01)
            quad_rot(ctx, view, k, -0.2, -0.06, -260, -33, C_YEL, 0.01)
            quad_rot(ctx, view, k, 0.06, 0.2, -260, -33, C_YEL, 0.01)
            # splitter island (raised) with a gap for the crosswalk
            for z0, z1, w0, w1 in ((-34, -31.2, 0.3, 0.55), (-26.8, -17.6, 0.75, 1.4)):
                pts = [rot((-w0, z0), k), rot((w0, z0), k), rot((w1, z1), k), rot((-w1, z1), k)]
                fill_poly(ctx, view, [(p[0], 0.15, p[1]) for p in pts], hexc('#d8d4cc'), OUTL, 2)
            fill_poly(ctx, view, [(p[0], 0.0, p[1]) for p in (rot((-0.55, -31.2), k), rot((0.55, -31.2), k),
                                                                rot((0.75, -26.8), k), rot((-0.75, -26.8), k))], C_ASPH)
            # crosswalk
            a, b = rot((-3.8, -31), k), rot((3.8, -27), k)
            zebra(ctx, view, min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), 'x' if k % 2 == 0 else 'z')
            # yield "shark teeth" across the entry lane
            for i in range(6):
                x0 = 0.9 + i * 0.5
                tri = [rot((x0, -17.9), k), rot((x0 + 0.36, -17.9), k), rot((x0 + 0.18, -17.3), k)]
                fill_poly(ctx, view, [(p[0], 0.012, p[1]) for p in tri], C_LINE)
            # entry arrow cue (white curved arrow painted in the circle)
        if view.ortho:
            return

    def objects(self, ctx, view, t):
        out = []
        for x0, x1, z0, z1, h, col in self.blds:
            out.append((((x0 + x1) / 2, h / 2, (z0 + z1) / 2),
                        lambda a=(x0, x1, z0, z1, h, col): building(ctx, view, *a, frame='#f4efe6')))
        for x, z in self.trees:
            out.append(((x, 1.5, z), lambda x=x, z=z: tree3(ctx, view, x, z, 0.45 if view.ortho else 1.0, int(abs(x + z)) % 3)))
        out.append(((0, 1.5, 0), lambda: tree3(ctx, view, 0, 0, 0.9 if view.ortho else 1.8, 1)))
        for k in range(4):
            sx, sz = rot((5.0, -46), k)
            out.append(((sx, 1.5, sz), lambda sx=sx, sz=sz, k=k: diamond_sign(ctx, view, sx, sz, math.pi - k * math.pi / 2 * -1 if False else
                                                                               ((math.pi + k * math.pi / 2) % (2 * math.pi)) * -1 % (2 * math.pi),
                                                                               roundabout_icon, '15 MPH')))
            yx, yz = rot((4.6, -19.0), k)
            out.append(((yx, 1.2, yz), lambda yx=yx, yz=yz, k=k: yield_sign(ctx, view, yx, yz, face_dir(k))))
        return out


def face_dir(k):
    """Heading a sign must face so drivers on leg k (approaching the centre) can read it."""
    fx, fz = rot((0, -1), k)          # pointing back toward the approaching traffic
    return math.atan2(fx, fz)


def _xz(p):
    return p


def quad_rot(ctx, view, k, x0, x1, z0, z1, col, y=0.0):
    pts = [rot((x0, z0), k), rot((x1, z0), k), rot((x1, z1), k), rot((x0, z1), k)]
    fill_poly(ctx, view, [(p[0], y, p[1]) for p in pts], col)


def yield_sign(ctx, view, x, z, face_h):
    if view.ortho:
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 2.1, z)), view.scale((x, 2.1, z))
    if not b or not tp or not s:
        return
    ctx.rectangle(b[0] - 0.05 * s, tp[1], 0.1 * s, b[1] - tp[1])
    fill_stroke(ctx, hexc('#9aa0aa'), OUTL, max(1, s / 40))
    r = 0.5 * s
    tri = [(tp[0] - r, tp[1] - r * 1.5), (tp[0] + r, tp[1] - r * 1.5), (tp[0], tp[1] + r * 0.2)]
    if not front_facing(view, x, z, face_h):
        poly(ctx, tri)
        fill_stroke(ctx, hexc('#9aa0aa'), OUTL, max(1, s / 40))
        return
    poly(ctx, tri)
    fill_stroke(ctx, hexc('#d62828'), OUTL, max(1, s / 40))
    poly(ctx, [(tp[0] - r * 0.6, tp[1] - r * 1.27), (tp[0] + r * 0.6, tp[1] - r * 1.27), (tp[0], tp[1] - r * 0.25)])
    setc(ctx, (1, 1, 1))
    ctx.fill()
    if r > 9:
        text_center(ctx, 'YIELD', tp[0], tp[1] - r * 0.85, r * 0.32, hexc('#d62828'))


city = Carmel()
world = CityWorld(28, [(0, 99, ego, others)], [ped1, ped2, ped3, ped4], city, 'mph')


def top_under(ctx, view, t, lt):
    a = smooth(lt / 0.4)
    for k in range(4):
        a0 = -70 + k * 90
        pts = [view.pt((13 * math.cos(math.radians(x)), 0, 13 * math.sin(math.radians(x)))) for x in range(a0, a0 + 55, 5)]
        arrow_path(ctx, pts, (1, 1, 1), 10, 0.85 * a, head=24)


def top_post(ctx, view, t, lt):
    a = smooth((lt - 0.4) / 0.4)
    if a <= 0:
        return
    ex, ez = world.ego_xz(t)
    p = view.pt((ex, 0, ez))
    ax, az, _ = carA.pose(t)
    q = view.pt((ax, 0, az))
    arrow_path(ctx, [(p[0] - 30, p[1] - 20), ((p[0] + q[0]) / 2, min(p[1], q[1]) - 60), (q[0] + 50, q[1] + 10)],
               hexc('#ffd23f'), 9, a, dash=[18, 12])
    label(ctx, q[0], q[1] - 70, 'Has the right of way', '#22a356', 38)
    label(ctx, p[0] + 190, p[1] + 20, 'You: YIELD', '#e0393e', 38)


C_REC = dict(cam='fixed', pos=(-16, 22, -44), target=(2, 0, -8), f=1000, hud=False)
shots = [
    Shot(3.0, 'c_cam', **C_REC),                                                        # 0 establishing
    Shot(2.6, 'c_cam', cam='chase'),                                                    # 1 slow down
    Shot(3.8, 'c_inside'),                                                              # 2 crosswalk
    Shot(3.0, 'c_top', center=(-4, -15), scale=16.0, under=top_under, post=top_post),    # 3 yield left
    Shot(2.8, 'c_inside', yaw=Key([(0, -0.75), (0.8, -0.65), (1.5, 0.05), (2.8, 0)])),     # 4 wait for a gap
    Shot(3.8, 'c_cam', cam='high'),                                                     # 5 enter, keep going
    Shot(2.2, 'c_cam', cam='close_r', hud=False),                                      # 6 signal right
    Shot(2.8, 'c_inside'),                                                              # 7 exit, watch for people
    Shot(3.2, 'c_cam', cam='fixed', pos=(-1.5, 16, 78), target=(0, 0, 18), hud=False),    # 8 recap
]
video = Video(['How to use a', 'ROUNDABOUT'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
steps = ['Slow down as you approach', 'Stop for people in the crosswalk', 'Yield to traffic on your LEFT',
         'Wait for a safe gap', 'Enter & keep moving, counter-clockwise', 'Signal right before your exit',
         'Exit & watch for people']
video.overlays = [(0.3, E[0] - 0.2, location_tag('Carmel, Indiana')),
                  (S[8] + 0.2, E[8], caption_in_scene('Slow. Yield left. Go. Signal out.'))]
for n, txt in enumerate(steps, 1):
    video.overlays += [(S[n], E[n], step_badge(n)), (S[n] + 0.15, E[n], caption_in_scene(txt))]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.12)
    m.add(city_ambience(video.dur), 0, 0.25)
    m.add(brake_squeal(1.4), 5.0, 0.06)
    tt = 4.5
    while tt < 13.1:
        m.add(footsteps(0.12, 100), tt, 0.05, 0.2)
        tt += 0.4
    m.add(car_pass(2.6, 0.5, 100), 12.4, 1.0, np.linspace(-0.8, 0.6, int(2.6 * SR)))
    m.add(car_pass(2.2, 0.5, 105), 2.4, 0.6, np.linspace(-0.3, -0.7, int(2.2 * SR)))
    m.add(click(), 18.8, 1.2)
    indicator(m, 18.8, 22.4, 1.0, 0.2)
    m.add(click(), 22.4, 1.0)
    for i in range(1, 8):
        m.add(pop(), S[i] + 0.15, 0.8)
    m.add(head_swish(), S[4] + 0.1, 1.0, -0.6)
    m.add(chime(), S[7] + 1.0, 0.5)
    m.add(success_jingle(), S[8] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'roundabout.mp4')
