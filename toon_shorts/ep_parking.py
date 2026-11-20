"""Parallel parking, step by step: San Francisco (Victorian row houses). Real bicycle-model manoeuvre."""
import math
import random

from citykit import *

engine.DAY = True
CURB = 6.0
PARK_X = 4.85
FRONT_Z, REAR_Z = 10.0, -1.4            # parked cars' centres: space between z 0.8 and 7.8
X0, Z0 = 2.21, 10.0                      # stop beside the front car, rear bumpers aligned
DMAX = 0.58
VIC = ['#e8a0b8', '#a0c8e8', '#f2d06b', '#9fd6b0', '#f4b183', '#c7a2e0', '#f6efe2', '#8fc3c7']


class Scripted:
    """Ego manoeuvre built from explicit phases (forward approach, stop, reverse with steering, pull forward)."""

    def __init__(self, col=C_EGO):
        self.col = col
        self.brake = lambda t: 0.0
        b = blinking([(3.0, 17.0)])
        self.blink = lambda t: 'R' if b(t) > 0.5 else None
        T, X, Z, H, V, D = [], [], [], [], [], []
        dt = 1 / 120
        t, h = 0.0, 0.0
        rx, rz = X0, Z0 - 24.0 - 1.35         # rear axle; approach from 24 m back
        spd = Key([(0, 6), (3.0, 6), (5.0, 0)], 'lin')

        def rec(v, d):
            T.append(t)
            X.append(rx + math.sin(h) * 1.35)
            Z.append(rz + math.cos(h) * 1.35)
            H.append(h)
            V.append(v)
            D.append(d)
        while t < 5.0:                         # approach and stop beside the front car
            v = spd(t)
            rec(v, 0)
            rz += v * dt
            t += dt
        while t < 8.0:                         # stopped: signal, mirrors, shoulder check
            rec(0, 0)
            t += dt
        phases = [(-0.8, 0.0, lambda: travelled < 0.3), (-0.8, DMAX, lambda: h > -math.radians(46)),
                  (-0.8, -DMAX, lambda: h < 0)]
        for v, d, cond in phases:
            travelled = 0.0
            while cond():
                rec(v, d)
                rx += v * math.sin(h) * dt
                rz += v * math.cos(h) * dt
                h += v / 2.7 * math.tan(d) * dt
                travelled += abs(v) * dt
                t += dt
        h = 0.0
        self.t_reverse_end = t
        t_end = t + 0.5
        while t < t_end:
            rec(0, 0)
            t += dt
        travelled = 0.0
        while travelled < 0.55:                 # pull forward to centre the car in the space
            rec(0.5, 0)
            rz += 0.5 * dt
            travelled += 0.5 * dt
            t += dt
        self.t_done = t
        while t < 40:
            rec(0, 0)
            t += dt
        self.g, self.X, self.Z, self.H, self.V, self.D = map(np.array, (T, X, Z, H, V, D))

    def pose(self, t):
        return (float(np.interp(t, self.g, self.X)), float(np.interp(t, self.g, self.Z)), float(np.interp(t, self.g, self.H)))

    def speed(self, t):
        return abs(float(np.interp(t, self.g, self.V)))

    def vel(self, t):
        return float(np.interp(t, self.g, self.V))

    def steer_angle(self, t):
        return float(np.interp(t, self.g, self.D))

    def steer(self, t):
        return clamp(self.steer_angle(t) * 2.6, -1.6, 1.6)

    def is_reversing(self, t):
        return self.vel(t) < -0.05

    def visible(self, t):
        return True


ego = Scripted()
T_REV0 = 8.0
T_LEFT = float(ego.g[np.argmax((ego.g > 8.0) & (ego.D < -0.1))])      # when the wheel goes full left
T_REV1 = ego.t_reverse_end


def parked(x, z, col, h=0.0):
    p = Path([('L', (x - math.sin(h), z - math.cos(h)), (x + math.sin(h), z + math.cos(h)))])
    return Mover(p, const(0.0), 0, p.s_near(x, z), col)


others = [parked(PARK_X, FRONT_Z, '#3a7bd5'), parked(PARK_X, REAR_Z, '#f4f4f6')]
for z, c in ((16.4, '#37b26c'), (22.8, '#c9c9d6'), (-7.8, '#f2a541'), (-14.2, '#7a4fd0'), (-20.6, '#2f6f73')):
    others.append(parked(PARK_X, z, c))
for z, c in ((-12, '#e05d5d'), (-5.6, '#3a7bd5'), (0.8, '#f2c230'), (7.2, '#c9c9d6'), (13.6, '#37b26c'), (20.0, '#f4f4f6')):
    others.append(parked(-PARK_X, z, c, math.pi))
p_sb = Path([('L', (-1.75, 200), (-1.75, -200))])
others += [Mover(p_sb, const(8.0), 2.6, p_sb.s_near(-1.75, 0), '#f2a541'), Mover(p_sb, const(8.0), 14.5, p_sb.s_near(-1.75, 0), '#e05d5d')]

peds = [Ped(const(7.6), Key([(0, -30), (25, 2)], 'lin'), top='#56b38a'),
        Ped(const(-7.6), Key([(0, 25), (25, -5)], 'lin'), top='#e05d5d', hair='#c7782e'),
        Ped(const(8.2), const(14.0), top='#9a6fd0', skin='#8d5a3b', hair='#1b1b1b')]


def victorian(ctx, view, x0, x1, z0, z1, h, col, side):
    building(ctx, view, x0, x1, z0, z1, h, col, win='#3b5872', roof=hexc('#5a5f66'), floors=3.2, frame='#ffffff')
    if view.ortho:
        return
    fx = x0 if side > 0 else x1           # street-facing wall
    out = -0.8 if side > 0 else 0.8
    zm = (z0 + z1) / 2
    bay_c = mix(hexc(col), (1, 1, 1), 0.25)
    bx0, bx1 = sorted((fx, fx + out))
    building(ctx, view, bx0, bx1, zm - 1.4, zm + 1.4, h - 2.2, '#%02x%02x%02x' % tuple(int(c * 255) for c in bay_c),
             win='#3b5872', floors=3.2, frame='#ffffff')
    rh = 3.0
    fill_poly(ctx, view, [(fx, h, z0), (fx, h, z1), (fx, h + rh, zm)], mix(hexc(col), (1, 1, 1), 0.15), OUTL, 2)
    fill_poly(ctx, view, [(fx, h + 0.1, z0 + 0.3), (fx, h + 0.1, z1 - 0.3), (fx, h + 0.45, z1 - 0.3), (fx, h + 0.45, z0 + 0.3)], (1, 1, 1))


class SanFrancisco:
    ground_col = hexc('#b9b2a4')
    sky = ('#7cc0ee', '#e6f4ff')

    def __init__(self):
        r = random.Random(21)
        self.houses = []
        for side in (-1, 1):
            z = -120.0
            while z < 160:
                w = r.uniform(6.0, 7.5)
                x0, x1 = (9.5, 9.5 + 14) if side > 0 else (-9.5 - 14, -9.5)
                self.houses.append((x0, x1, z, z + w, r.uniform(9.5, 12.5), r.choice(VIC), side))
                z += w + 0.15

    def skyline(self, ctx, view):
        if view.ortho:
            return
        r = random.Random(9)
        # rolling hills with houses + a white pyramid tower far ahead
        pts = [view.pt((x, 40 + 30 * math.sin(x / 140) + 20 * math.sin(x / 61), 900)) for x in range(-1600, 1601, 80)]
        base = view.pt((0, 0, 900))
        if base and all(pts):
            ctx.move_to(pts[0][0] - 1000, base[1] + 4)
            for p in pts:
                ctx.line_to(*p)
            ctx.line_to(pts[-1][0] + 1000, base[1] + 4)
            ctx.close_path()
            setc(ctx, hexc('#a7b98f'))
            ctx.fill()
            for i in range(140):
                x = r.uniform(-1500, 1500)
                y = r.uniform(5, 35 + 30 * math.sin(x / 140) + 20 * math.sin(x / 61))
                p, s = view.pt((x, y, 880)), view.scale((x, y, 880))
                if p and s:
                    ctx.rectangle(p[0], p[1], 9 * s, 6 * s)
                    setc(ctx, hexc(r.choice(['#f4efe6', '#f2d7b6', '#cfe0ea', '#e8cfd6'])))
                    ctx.fill()
        X, Z = -60.0, 700.0
        b, s = view.pt((X, 0, Z)), view.scale((X, 0, Z))
        if b and s:
            poly(ctx, [(b[0] - 26 * s, b[1]), (b[0] + 26 * s, b[1]), (b[0], b[1] - 260 * s)])
            setc(ctx, hexc('#eef1f4'))
            ctx.fill()
            poly(ctx, [(b[0], b[1]), (b[0] + 26 * s, b[1]), (b[0], b[1] - 260 * s)])
            setc(ctx, hexc('#d3d9e0'))
            ctx.fill()

    def ground(self, ctx, view, t):
        gquad(ctx, view, -CURB, CURB, -300, 300, C_ASPH)
        for sg in (-1, 1):
            gquad(ctx, view, *sorted((sg * CURB, sg * 9.5)), -300, 300, C_WALK)
            gquad(ctx, view, *sorted((sg * CURB, sg * (CURB + 0.2))), -300, 300, hexc('#9a958c'), 0.01)
            gquad(ctx, view, *sorted((sg * 3.5, sg * 3.62)), -300, 300, C_LINE, 0.01)
        gquad(ctx, view, -0.18, -0.06, -300, 300, C_YEL, 0.01)
        gquad(ctx, view, 0.06, 0.18, -300, 300, C_YEL, 0.01)
        for z in np.arange(-24, 30, 6.4):        # parking-space tick marks
            gquad(ctx, view, 3.6, 4.4, z + 0.8 - 0.06, z + 0.8 + 0.06, C_LINE, 0.012)

    def objects(self, ctx, view, t):
        out = []
        for a in self.houses:
            out.append((((a[0] + a[1]) / 2, 5, (a[2] + a[3]) / 2), lambda a=a: victorian(ctx, view, *a)))
        for z in np.arange(-60, 120, 13):
            for x in (8.6, -8.6):
                out.append(((x, 1.5, z + 3), lambda x=x, z=z: tree3(ctx, view, x, z + 3, 0.4 if view.ortho else 0.9, int(abs(z)) % 3)))
        return out


city = SanFrancisco()
world = CityWorld(23, [(0, 99, ego, others)], peds, city, 'mph')
TOPV = dict(center=(3.0, 5.0), scale=60.0)


def path_overlay(ctx, view, t, lt):
    """Dashed ghost of the whole reverse path (rear-axle style footprints of the car centre)."""
    i0, i1 = np.searchsorted(ego.g, T_REV0), np.searchsorted(ego.g, T_REV1)
    pts = [view.pt((ego.X[i], 0, ego.Z[i])) for i in range(i0, i1, 12)]
    if len(pts) > 1:
        arrow_path(ctx, pts, (1, 1, 1), 7, 0.75, dash=[14, 10], head=22)


def space_post(ctx, view, t, lt):
    a = smooth((lt - 0.3) / 0.4)
    if a <= 0:
        return
    p0, p1 = view.pt((CURB - 0.6, 0, 0.8)), view.pt((CURB - 0.6, 0, 7.8))
    ctx.move_to(*p0)
    ctx.line_to(*p1)
    setc(ctx, hexc('#ffd23f'), a)
    ctx.set_line_width(7)
    ctx.stroke()
    for p in (p0, p1):
        ctx.move_to(p[0] - 30, p[1])
        ctx.line_to(p[0] + 30, p[1])
        ctx.stroke()
    label(ctx, p0[0] + 250, (p0[1] + p1[1]) / 2 + 20, '1.5x your car', '#22a356', 44)


def gap_post(ctx, view, t, lt):
    a = smooth((lt - 0.4) / 0.4)
    if a <= 0:
        return
    x, z, h = ego.pose(t)
    p, q = view.pt((x + 0.92, 0, z)), view.pt((CURB, 0, z))
    ctx.move_to(*p)
    ctx.line_to(*q)
    setc(ctx, hexc('#ffd23f'), a)
    ctx.set_line_width(6)
    ctx.stroke()
    label(ctx, q[0] + 220, q[1] + 15, '~30 cm from curb', '#22a356', 42)


def wheel_hud(ctx, lt, d):
    """Steering-wheel indicator (top right) during the manoeuvre."""
    t = T_REV0 + lt
    ang = ego.steer_angle(t)
    cx, cy, r = 1700, 230, 85
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(ang / DMAX * 1.6)
    ctx.new_sub_path()
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    setc(ctx, (0.1, 0.1, 0.14), 0.85)
    ctx.fill_preserve()
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(14)
    ctx.stroke()
    for a0 in (math.pi / 2, math.pi * 7 / 6, -math.pi / 6):
        ctx.move_to(0, 0)
        ctx.line_to(math.cos(a0) * r, math.sin(a0) * r)
    ctx.set_line_width(12)
    ctx.stroke()
    rrect(ctx, -14, -r - 10, 28, 22, 6)
    setc(ctx, hexc('#ffd23f'))
    ctx.fill()
    ctx.restore()
    txt = 'FULL RIGHT' if ang > 0.2 else ('FULL LEFT' if ang < -0.2 else 'STRAIGHT')
    col = '#e0393e' if ang > 0.2 else ('#2f6f9f' if ang < -0.2 else '#22a356')
    label(ctx, cx, cy + r + 75, txt, col, 36)


shots = [
    Shot(3.0, 'c_cam', cam='fixed', pos=(-2.5, 8.5, 34), target=(3, 0, 2), hud=False),                # 0 establishing
    Shot(2.6, 'c_top', post=space_post, **TOPV),                                                     # 1 find a space
    Shot(1.8, 'c_cam', cam='close_r', hud=False),                                                    # 2 signal, stop beside
    Shot(1.6, 'c_shoulder', side='R'),                                                               # 3 mirrors/shoulder
    Shot(3.6, 'c_top', under=path_overlay, **TOPV),                                                  # 4 reverse, full right
    Shot(2.6, 'c_rear'),                                                                             # 5 at 45 deg, full left
    Shot(3.0, 'c_cam', cam='fixed', pos=(0.2, 4.6, -4.5), target=(4.4, 0.4, 5.2), f=900, hud=False),             # 6 swing in
    Shot(2.4, 'c_top', post=gap_post, **TOPV),                                                       # 7 straighten, centre
    Shot(2.4, 'c_cam', cam='fixed', pos=(-0.5, 5.2, 15), target=(4.6, 0.4, 4.0), f=950, hud=False),             # 8 recap
]
video = Video(['PARALLEL PARKING', 'step by step'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
steps = ['Find a space about 1.5x your car', 'Signal & stop beside the front car', 'Check mirrors & over your shoulder',
         'Reverse slowly, wheel FULL RIGHT', 'At about 45°, wheel FULL LEFT', 'Swing in close to the curb',
         'Straighten & centre in the space']
video.overlays = [(0.3, E[0] - 0.2, location_tag('San Francisco, CA')),
                  (S[8] + 0.2, E[8], caption_in_scene('Signal. Align. Right. Left. Straighten.')),
                  (T_REV0, T_REV1 + 0.6, wheel_hud)]
for n, txt in enumerate(steps, 1):
    video.overlays += [(S[n], E[n], step_badge(n)), (S[n] + 0.15, E[n], caption_in_scene(txt))]


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur), 0, 0.3)
    m.add(ambience(world, 5.5, inside=0.9), 0, 0.12)
    m.add(engine_idle(video.dur - 5.0), 5.0, 0.25)
    m.add(click(), 3.0, 1.2)
    indicator(m, 3.0, 17.0, 0.7, 0.2)
    m.add(click(), 17.0, 1.0)
    m.add(brake_squeal(0.8), 4.4, 0.05)
    m.add(head_swish(), S[3] + 0.1, 1.0, 0.6)
    m.add(click(), T_REV0 - 0.3, 0.8)            # shift into reverse
    m.add(reverse_beeps(T_REV1 - T_REV0, 0.42), T_REV0, 0.55)
    for i in range(1, 8):
        m.add(pop(), S[i] + 0.15, 0.8)
    m.add(car_pass(2.0, 0.5, 100), 1.8, 0.5, np.linspace(0.6, -0.6, int(2.0 * SR)))
    m.add(car_pass(2.0, 0.5, 105), 13.7, 0.5, np.linspace(0.6, -0.6, int(2.0 * SR)))
    m.add(success_jingle(), S[8] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'parking.mp4')
