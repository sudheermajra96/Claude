"""4-way stop: who goes first? Vancouver, BC (residential, North Shore mountains). 3 situations + a comment quiz."""
import math
import random

from citykit import *

engine.DAY = True
STOPC = 8.7          # car-centre distance from the intersection centre when stopped at the line
HOUSE = ['#e9e3d3', '#cfe0ea', '#f2d7b6', '#d6e5cf', '#e8cfd6', '#c9ccd6', '#f4efe6']
ROOF = ['#4a4f5c', '#6b3f32', '#38485a', '#5a5f52']


def blinkfn(intervals, side):
    b = blinking(intervals)
    return lambda t: side if b(t) > 0.5 else None


P = {'N': Path([('L', (1.75, -160), (1.75, 160))]), 'S': Path([('L', (-1.75, 160), (-1.75, -160))]),
     'E': Path([('L', (-160, -1.75), (160, -1.75))]), 'W': Path([('L', (160, 1.75), (-160, 1.75))])}
STOP_PT = {'N': (1.75, -STOPC), 'S': (-1.75, STOPC), 'E': (-STOPC, -1.75), 'W': (STOPC, 1.75)}
P_LEFT = Path([('L', (1.75, -160), (1.75, -4.25)), ('A', (-4.25, -4.25), 6.0, 0, 90), ('L', (-4.25, 1.75), (-160, 1.75))])


def stop_go(path, stop_pt, ta, tg, col, blink=None):
    """Arrive and come to a full stop at ta, go at tg."""
    k = Key([(-20, 11), (ta - 2.6, 11), (ta, 0), (tg, 0), (tg + 2.0, 6), (tg + 4.0, 10), (90, 10)], 'lin')
    return Mover(path, k, ta, path.s_near(*stop_pt), col, blink=blink, t0=-20, t1=90)


def parked(path, stop_pt, col):
    return Mover(path, const(0.0), 0, path.s_near(*stop_pt), col, t0=-20, t1=90)


ego1 = stop_go(P['N'], STOP_PT['N'], 3.2, 6.4, C_EGO)
blue1 = stop_go(P['E'], STOP_PT['E'], 1.0, 4.0, '#3a7bd5')
ego2 = stop_go(P['N'], STOP_PT['N'], 12.0, 15.4, C_EGO)
green2 = stop_go(P['W'], STOP_PT['W'], 12.0, 13.0, '#37b26c')
ego3 = stop_go(P_LEFT, STOP_PT['N'], 21.4, 24.6, C_EGO, blink=blinkfn([(19.2, 27.4)], 'L'))
yellow3 = stop_go(P['S'], STOP_PT['S'], 21.4, 22.4, '#f2c230')
egoQ = parked(P['N'], STOP_PT['N'], C_EGO)
blueQ = parked(P['E'], STOP_PT['E'], '#3a7bd5')
SEGS = [(0, 9.6, ego1, [blue1]), (9.6, 19.0, ego2, [green2]), (19.0, 28.4, ego3, [yellow3]), (28.4, 99, egoQ, [blueQ])]

peds = [Ped(const(6.2), Key([(0, -40), (40, 10)], 'lin'), top='#56b38a'),
        Ped(Key([(0, -30), (40, -8)], 'lin'), const(-6.4), top='#9a6fd0', hair='#c7782e'),
        Ped(const(-6.4), Key([(0, 40), (40, 14)], 'lin'), top='#e05d5d', skin='#c58c6b')]


def house(ctx, view, x0, x1, z0, z1, h, col, roof):
    building(ctx, view, x0, x1, z0, z1, h, col, win='#3b5872', roof=hexc(roof), floors=2.9, frame='#ffffff')
    if view.ortho:
        return
    rh = 2.6
    along_x = (x1 - x0) >= (z1 - z0)
    if along_x:
        zm = (z0 + z1) / 2
        slopes = [[(x0, h, z0), (x1, h, z0), (x1, h + rh, zm), (x0, h + rh, zm)],
                  [(x0, h, z1), (x1, h, z1), (x1, h + rh, zm), (x0, h + rh, zm)]]
        gables = [([(x0, h, z0), (x0, h, z1), (x0, h + rh, zm)], -math.pi / 2), ([(x1, h, z0), (x1, h, z1), (x1, h + rh, zm)], math.pi / 2)]
    else:
        xm = (x0 + x1) / 2
        slopes = [[(x0, h, z0), (x0, h, z1), (xm, h + rh, z1), (xm, h + rh, z0)],
                  [(x1, h, z0), (x1, h, z1), (xm, h + rh, z1), (xm, h + rh, z0)]]
        gables = [([(x0, h, z0), (x1, h, z0), (xm, h + rh, z0)], math.pi), ([(x0, h, z1), (x1, h, z1), (xm, h + rh, z1)], 0.0)]
    for pts, fh in gables:
        c = (sum(p[0] for p in pts) / 3, sum(p[2] for p in pts) / 3)
        if front_facing(view, c[0], c[1], fh):
            fill_poly(ctx, view, pts, hexc(col), OUTL, 2)
    for pts in sorted(slopes, key=lambda q: -view.depth((sum(p[0] for p in q) / 4, h + 1, sum(p[2] for p in q) / 4))):
        fill_poly(ctx, view, pts, hexc(roof), OUTL, 2)


class Vancouver:
    ground_col = hexc('#86c46a')
    sky = ('#6db3e8', '#e3f3ff')

    def __init__(self):
        r = random.Random(12)
        self.houses, self.trees = [], []
        for sx in (-1, 1):
            for sz in (-1, 1):
                for i in range(6):          # houses facing the N-S street
                    d = 13 + i * 16
                    self.houses.append(self._h(sx, sz, 12.5, 22.5, d, d + 10, r))
                for i in range(1, 6):       # houses facing the E-W street
                    d = 29 + i * 16 - 16
                    self.houses.append(self._h(sx, sz, d, d + 10, 12.5, 22.5, r, flip=True))
                for d in np.arange(17, 120, 11):
                    self.trees.append((sx * 4.6, sz * d, r.random() < 0.5))
                    self.trees.append((sx * d, sz * 4.6, r.random() < 0.5))

    def _h(self, sx, sz, a0, a1, b0, b1, r, flip=False):
        xs, zs = sorted((sx * a0, sx * a1)), sorted((sz * b0, sz * b1))
        return (xs[0], xs[1], zs[0], zs[1], r.uniform(5.5, 6.5), r.choice(HOUSE), r.choice(ROOF))

    def skyline(self, ctx, view):
        r = random.Random(5)
        peaks = [(x, r.uniform(500, 1300) if i % 2 else r.uniform(300, 700)) for i, x in enumerate(range(-4000, 4001, 400))]
        mountains(ctx, view, peaks, 3200, snow=True)
        p2 = [(x, r.uniform(150, 350)) for x in range(-4000, 4001, 300)]
        if not view.ortho:
            pts = [view.pt((x, h, 2200)) for x, h in p2]
            base = view.pt((0, 0, 2200))
            if base and all(pts):
                ctx.move_to(pts[0][0] - 2000, base[1] + 4)
                for p in pts:
                    ctx.line_to(*p)
                ctx.line_to(pts[-1][0] + 2000, base[1] + 4)
                ctx.close_path()
                setc(ctx, hexc('#4f7d6b'))
                ctx.fill()

    def ground(self, ctx, view, t):
        gquad(ctx, view, -3.6, 3.6, -300, 300, C_ASPH)
        fill_poly(ctx, view, [(-300, 0, -3.6), (300, 0, -3.6), (300, 0, 3.6), (-300, 0, 3.6)], C_ASPH)
        for sx in (-1, 1):
            gquad(ctx, view, *sorted((sx * 5.6, sx * 7.0)), -300, -5.6, C_WALK)
            gquad(ctx, view, *sorted((sx * 5.6, sx * 7.0)), 5.6, 300, C_WALK)
            fill_poly(ctx, view, [(-300, 0, sx * 5.6), (-5.6, 0, sx * 5.6), (-5.6, 0, sx * 7.0), (-300, 0, sx * 7.0)], C_WALK)
            fill_poly(ctx, view, [(5.6, 0, sx * 5.6), (300, 0, sx * 5.6), (300, 0, sx * 7.0), (5.6, 0, sx * 7.0)], C_WALK)
        for a, b in ((-300, -6.0), (6.0, 300)):
            gquad(ctx, view, -0.08, 0.08, a, b, C_YEL, 0.01)
            fill_poly(ctx, view, [(a, 0.01, -0.08), (b, 0.01, -0.08), (b, 0.01, 0.08), (a, 0.01, 0.08)], C_YEL)
        gquad(ctx, view, 0.1, 3.5, -6.5, -6.0, C_LINE, 0.012)
        gquad(ctx, view, -3.5, -0.1, 6.0, 6.5, C_LINE, 0.012)
        fill_poly(ctx, view, [(-6.5, 0.012, -3.5), (-6.0, 0.012, -3.5), (-6.0, 0.012, -0.1), (-6.5, 0.012, -0.1)], C_LINE)
        fill_poly(ctx, view, [(6.0, 0.012, 0.1), (6.5, 0.012, 0.1), (6.5, 0.012, 3.5), (6.0, 0.012, 3.5)], C_LINE)

    def objects(self, ctx, view, t):
        out = []
        for a in self.houses:
            out.append((((a[0] + a[1]) / 2, 3, (a[2] + a[3]) / 2), lambda a=a: house(ctx, view, *a)))
        for x, z, con in self.trees:
            if view.ortho:
                out.append(((x, 0.5, z), lambda x=x, z=z, con=con: conifer(ctx, view, x, z, 0.8) if con else tree3(ctx, view, x, z, 0.5, int(abs(z)) % 3)))
            else:
                out.append(((x, 2, z), lambda x=x, z=z, con=con: conifer(ctx, view, x, z, 1.0) if con else tree3(ctx, view, x, z, 1.1, int(abs(z)) % 3)))
        for (x, z), fh in (((4.4, -6.6), math.pi), ((-4.4, 6.6), 0.0), ((-6.6, -4.4), -math.pi / 2), ((6.6, 4.4), math.pi / 2)):
            out.append(((x, 1.4, z), lambda x=x, z=z, fh=fh: stop_sign(ctx, view, x, z, fh, 'STOP', 'ALL WAY')))
        return out


city = Vancouver()
world = CityWorld(32.6, SEGS, peds, city, 'kmh')


def nums_for(order):
    def fn(t, lt):
        return order if lt > 0.35 else {}
    return fn


def rule_post(*lines):
    def fn(ctx, view, t, lt):
        a = smooth((lt - 0.35) / 0.3)
        if a <= 0:
            return
        for i, ln in enumerate(lines):
            ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(40)
            w = ctx.text_extents(ln).x_advance
            label(ctx, 50 + w / 2 + 18, 230 + i * 82, ln, '#22a356' if i == 0 else '#2f6f9f', 40)
    return fn


def quiz_post(ctx, view, t, lt):
    for (x, z), name, col in (((1.75, -STOPC), 'A', '#e23b3b'), ((-STOPC, -1.75), 'B', '#3a7bd5')):
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0] + (90 if name == 'A' else -10), p[1] + (10 if name == 'A' else 95), 46, 46)
        fill_stroke(ctx, hexc(col), (1, 1, 1), 5)
        text_center(ctx, name, p[0] + (90 if name == 'A' else -10), p[1] + (32 if name == 'A' else 117), 60, (1, 1, 1))
    a = smooth(lt / 0.3)
    label(ctx, 410, 230, 'Both stopped at the', '#2f6f9f', 40)
    label(ctx, 410, 312, 'SAME time.', '#2f6f9f', 40)
    label(ctx, 1480, 260, 'Who goes first?', '#e0393e', 52)
    label(ctx, 1480, 360, 'A or B?', '#e0393e', 60)
    if lt > 1.4:
        b = smooth((lt - 1.4) / 0.3)
        pop_ = 1 + 0.2 * (1 - b)
        ctx.save()
        ctx.translate(1480, 820)
        ctx.scale(pop_, pop_)
        label(ctx, 0, 0, 'Comment below!', '#22a356', 50)
        ctx.restore()


TOP = dict(center=(0, 0), scale=36.0)
shots = [
    Shot(2.6, 'c_cam', cam='fixed', pos=(5.5, 12, -30), target=(-1, 0, 0), hud=False),                         # S1 wide
    Shot(3.0, 'c_top', nums=nums_for({0: 1, 'ego': 2}), post=rule_post('Rule 1:', 'First to STOP, first to GO'), **TOP),
    Shot(4.0, 'c_cam', cam='high'),                                                                            # S1 go
    Shot(2.8, 'c_inside', yaw=Key([(0, 0), (1.2, 0), (1.8, 0.6), (2.8, 0.6)])),                               # S2 arrive, look right
    Shot(3.0, 'c_top', nums=nums_for({0: 1, 'ego': 2}), post=rule_post('Rule 2: Same time?', 'Car on the RIGHT goes first'), **TOP),
    Shot(3.6, 'c_cam', cam='chase'),                                                                           # S2 go
    Shot(2.8, 'c_cam', cam='close_l', hud=False),                                                              # S3 arrive, signal left
    Shot(2.8, 'c_top', nums=nums_for({0: 1, 'ego': 2}),
         post=rule_post('Rule 3: Facing each other?', 'Left turn waits for straight'), **TOP),
    Shot(3.8, 'c_cam', cam='high'),                                                                            # S3 turn
    Shot(4.2, 'c_top', post=quiz_post, **TOP),                                                                 # quiz
]
video = Video(['4-WAY STOP:', 'who goes first?'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [(0.3, E[0] - 0.2, location_tag('Vancouver, BC'))]
for n, i0, i1 in ((1, 0, 2), (2, 3, 5), (3, 6, 8)):
    video.overlays.append((S[i0], E[i1], badge(f'SITUATION {n}', '#2f6f9f')))
video.overlays += [(S[9], E[9], badge('QUIZ', '#e0393e'))]
video.overlays += [(S[3] + 0.2, E[3], caption_in_scene('You both stop at the same time...')),
                   (S[6] + 0.2, E[6], caption_in_scene('You want to turn left...')),
                   (S[2] + 0.4, E[2], caption_in_scene('Blue goes, then you')),
                   (S[5] + 0.4, E[5], caption_in_scene('Green goes, then you')),
                   (S[8] + 0.4, E[8], caption_in_scene('Yellow goes, then you turn'))]


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.12)
    m.add(city_ambience(video.dur), 0, 0.2)
    for ta in (1.0, 3.2, 12.0, 21.4):
        m.add(brake_squeal(1.0), ta - 0.9, 0.06)
    m.add(click(), 19.2, 1.2)
    indicator(m, 19.2, 27.4, 1.0, -0.2)
    m.add(click(), 27.4, 1.0)
    for i in (1, 4, 7):
        m.add(pop(), S[i] + 0.35, 0.9)
        m.add(bell(midi(84), 0.6), S[i] + 0.4, 0.5)
    for i in (3, 6, 9):
        m.add(whoosh(0.5, 0.4), S[i] - 0.1, 0.4)
    m.add(head_swish(), S[3] + 1.3, 1.0, 0.6)
    m.add(boing(), S[9] + 0.3, 0.6)
    m.add(pop(), S[9] + 1.4, 0.9)
    m.add(chime(), S[9] + 1.5, 0.7)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'fourway.mp4')
