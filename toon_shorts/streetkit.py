"""City-street kit for the cinematic square template: a two-way street with painted bike lanes, parked cars, sidewalks,
shop buildings, trees and lamps; a 3D bicycle + rider (pedalling, braking, thrown in a crash); car doors that swing
open; close-ups for the door: side-mirror view and the Dutch Reach (far-hand) scene.

Street cross-section (x, metres): right sidewalk 9.0..12.5 | parking 6.6..9.0 (cars at 7.75) | bike lane 4.8..6.6 |
travel lane 1.4..4.8 | double yellow 1.2..1.4 | travel -2.2..1.2 | bike lane -4.0..-2.2 | parking -6.4..-4.0 | sidewalk.
"""
from cinetemplate import *

X_PARK, X_BIKE, X_LANE = 7.75, 5.7, 3.1
C_GREEN = hexc('#3f9a5a')


# ------------------------------------------------------------------ world
def bldg(ctx, view, x0, x1, z0, z1, hgt, col, face_x, seed):
    """Shop building box; street facade at face_x with windows, door and an awning."""
    Lf = L(0.0, 0.0, 0.0)
    c = hexc(col)
    lbox(ctx, view, Lf, 0.0, x0, x1, 0.0, hgt, z0, z1, {k: c for k in ('front', 'back', 'left', 'right', 'top')}, 2)
    r = random.Random(seed)
    sgn = -1 if face_x == x0 else 1
    fx = face_x + sgn * 0.02
    nz = max(1, int((z1 - z0) / 3.2))
    for fl in range(1, int(hgt / 3.2)):
        for k in range(nz):
            za, zb = z0 + (k + 0.25) * (z1 - z0) / nz, z0 + (k + 0.75) * (z1 - z0) / nz
            ya, yb = fl * 3.2 + 0.8, fl * 3.2 + 2.3
            fill_poly(ctx, view, [(fx, ya, za), (fx, ya, zb), (fx, yb, zb), (fx, yb, za)],
                      hexc('#2c3e57') if r.random() < 0.7 else hexc('#ffd98a'), OUTL, 1)
    # shop window + awning
    fill_poly(ctx, view, [(fx, 0.3, z0 + 0.6), (fx, 0.3, z1 - 2.2), (fx, 2.6, z1 - 2.2), (fx, 2.6, z0 + 0.6)], hexc('#9fd3ea'), OUTL, 2)
    fill_poly(ctx, view, [(fx, 0.0, z1 - 1.8), (fx, 0.0, z1 - 0.6), (fx, 2.4, z1 - 0.6), (fx, 2.4, z1 - 1.8)], hexc('#5a3b2a'), OUTL, 2)
    aw = hexc(r.choice(['#e0393e', '#2f6f73', '#f2a541', '#3a7bd5', '#7a4fd0']))
    fill_poly(ctx, view, [(fx, 3.1, z0 + 0.3), (fx, 3.1, z1 - 0.3), (fx - sgn * 1.4, 2.6, z1 - 0.3), (fx - sgn * 1.4, 2.6, z0 + 0.3)], aw, OUTL, 2)


def bike_symbol(ctx, view, x, z):
    for dz in (-0.55, 0.55):
        pts = [view.pt((x + 0.42 * math.cos(a), 0.012, z + dz + 0.42 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 14)]
        if all(pts):
            poly(ctx, pts)
            setc(ctx, (1, 1, 1), 0.85)
            ctx.set_line_width(max(1, (view.scale((x, 0, z)) or 5) * 0.06))
            ctx.stroke()
    a, b = view.pt((x, 0.012, z - 0.55)), view.pt((x, 0.012, z + 0.55))
    if a and b:
        ctx.move_to(*a)
        ctx.line_to(*b)
        ctx.stroke()


class CityStreet:
    def __init__(self, sky=('#4a86c8', '#ffd8a8'), far=None, seed=5, z0=-200.0, z1=700.0):
        self.sky, self.ground_col, self.far = sky, hexc('#9aa070'), far
        r = random.Random(seed)
        self.bl = []
        for side, (xa, xb) in ((1, (12.5, 22.0)), (-1, (-19.5, -9.9))):
            z = z0
            while z < z1:
                w = r.uniform(9, 16)
                self.bl.append((xa, xb, z, z + w - 0.4, r.uniform(7, 15), r.choice(['#c98d6a', '#d8c3a0', '#a7b6c2', '#e2b07a', '#b97a6a', '#9db08a']),
                                xa if side == 1 else xb, int(z)))
                z += w
        self.trees = [(10.6 if k % 2 else -8.0, z) for k, z in enumerate(np.arange(z0, z1, 17.0))]
        self.lamps = [(9.4 if k % 2 else -6.8, z + 8) for k, z in enumerate(np.arange(z0, z1, 26.0))]

    def skyline(self, ctx, view):
        if view.ortho:
            return
        if self.far:
            self.far(ctx, view)

    def ground(self, ctx, view, t):
        ez = view.pos[2] if not view.ortho else view.zc
        zlo, zhi = ez - 120, ez + 900
        gquad(ctx, view, -30, 30, zlo, zhi, hexc('#b9b3a6'))                     # sidewalks / plazas
        gquad(ctx, view, -6.4, 9.0, zlo, zhi, hexc('#55565f'))                   # asphalt
        for xa, xb in ((4.8, 6.6), (-4.0, -2.2)):
            gquad(ctx, view, xa, xb, zlo, zhi, C_GREEN, 0.005)                    # green bike lanes
        for xl in (4.8, 6.6, -4.0, -2.2):
            gquad(ctx, view, xl - 0.08, xl + 0.08, zlo, zhi, (0.95, 0.95, 0.92), 0.01)
        for xl in (1.15, 1.45):
            gquad(ctx, view, xl - 0.06, xl + 0.06, zlo, zhi, C_YEL, 0.01)
        for xc in (9.0, -6.4):                                                    # curbs
            gquad(ctx, view, xc - 0.15, xc + 0.15, zlo, zhi, hexc('#d9d4c8'), 0.02)
        if not view.ortho:
            for k in range(int(zlo // 40), int(min(zhi, ez + 300) // 40) + 1):
                bike_symbol(ctx, view, X_BIKE, k * 40.0 + 10)
                bike_symbol(ctx, view, -3.1, k * 40.0 + 30)
            for k in range(int(zlo // 6.5), int(min(zhi, ez + 200) // 6.5) + 1):  # parking stall ticks
                gquad(ctx, view, 8.6, 9.0, k * 6.5 - 0.05, k * 6.5 + 0.05, (0.95, 0.95, 0.92), 0.01)
        if EP.extra_ground:
            EP.extra_ground(ctx, view, t)
        for a in EP.shadows:
            x, z, h = a.pose(t)
            if not view.ortho:
                d = view.depth((x, 1, z))
                if d < -25 or d > 400:
                    continue
            lo, hi, hw, hg = a.ext
            shadow(ctx, view, x, z, h, lo, hi, hw, hg)

    def objects(self, ctx, view, t):
        out = []
        ez = view.pos[2] if not view.ortho else view.zc
        lo, hi = ez - 60, ez + 400
        for b in self.bl:
            xa, xb, za, zb, hg, col, fx, sd = b
            if zb > lo and za < hi:
                out.append((((xa + xb) / 2, hg / 2, (za + zb) / 2), lambda b=b: bldg(ctx, view, *b)))
        for x, z in self.trees:
            if lo < z < hi:
                out.append(((x, 2, z), lambda x=x, z=z: tree3(ctx, view, x, z, 0.9 * (0.45 if view.ortho else 1.0), int(abs(z)) % 3)))
        if not view.ortho:
            for x, z in self.lamps:
                if lo < z < hi:
                    out.append(((x, 3, z), lambda x=x, z=z: lamp_post(ctx, view, x, z, 1 if x > 0 else -1)))
        return out


# ------------------------------------------------------------------ car door
def door_poly(Lf, ang, side=-1):
    """Driver door (left side by default) swung open by ang (rad) about its front hinge."""
    hx, hz, Ld = side * 0.92, 0.5, 1.1
    ex, ez = hx + side * math.sin(ang) * Ld, hz - math.cos(ang) * Ld
    return ((hx, hz), (ex, ez))


def draw_door(ctx, view, x, z, h, ang, col, side=-1):
    if ang <= 0.01 or view.ortho:
        return
    Lf = L(x, z, h)
    (hx, hz), (ex, ez) = door_poly(Lf, ang, side)
    body = [Lf(hx, 0.3, hz), Lf(ex, 0.3, ez), Lf(ex, 0.92, ez), Lf(hx, 0.92, hz)]
    glass = [Lf(hx, 0.95, hz), Lf(ex + (hx - ex) * 0.05, 0.95, ez + (hz - ez) * 0.05), Lf(ex + (hx - ex) * 0.2, 1.36, ez + (hz - ez) * 0.2),
             Lf(hx, 1.36, hz)]
    for pts, c in ((body, col), (glass, hexc('#9fd3ea'))):
        q = [view.pt(P) for P in pts]
        if all(q):
            poly(ctx, q)
            fill_stroke(ctx, c, OUTL, max(1.0, (view.scale(Lf(hx, 0.6, hz)) or 10) / 45))
    # inner trim + handle
    q = [view.pt(Lf(hx + (ex - hx) * u, 0.62, hz + (ez - hz) * u)) for u in (0.55, 0.75)]
    if all(q):
        ctx.move_to(*q[0])
        ctx.line_to(*q[1])
        setc(ctx, hexc('#2a2a33'))
        ctx.set_line_width(max(2, (view.scale(Lf(ex, 0.6, ez)) or 10) * 0.05))
        ctx.stroke()


class ParkedCar(Veh):
    """Stationary car with an opening driver door: door_fn(t) -> angle (rad)."""

    def __init__(self, x, z, col, door_fn=None, occ=None, mark=None, blink=None):
        super().__init__(x, const(0.0), 0.0, z, col, occ=occ, mark=mark, brake=lambda t: 0.0, blink=blink)
        self.door_fn = door_fn or (lambda t: 0.0)

    def items(self, ctx, view, t):
        base = super().items(ctx, view, t)
        ang = self.door_fn(t)
        if ang <= 0.01 or view.ortho:
            return base
        x, z, h = self.pose(t)
        Lf = L(x, z, h)
        (hx, hz), (ex, ez) = door_poly(Lf, ang)
        P = Lf((hx + ex) / 2, 0.7, (hz + ez) / 2)
        return base + [(P, lambda: draw_door(ctx, view, x, z, h, ang, hexc(self.col)))]

    def door_tip(self, t):
        x, z, h = self.pose(t)
        Lf = L(x, z, h)
        (hx, hz), (ex, ez) = door_poly(Lf, self.door_fn(t))
        return Lf(ex, 0.6, ez)


# ------------------------------------------------------------------ bicycle + rider
def _limb(ctx, a, b, w, col):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(*a)
    ctx.line_to(*b)
    setc(ctx, OUTL)
    ctx.set_line_width(w + 4)
    ctx.stroke()
    ctx.move_to(*a)
    ctx.line_to(*b)
    setc(ctx, col)
    ctx.set_line_width(w)
    ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)


def bicycle(ctx, view, x, y, z, h, roll, phase, col='#e0393e'):
    """Bicycle (wheelbase 1.05 m) at ground point (x, z); roll tilts it sideways (rad)."""
    cr, sr = math.cos(roll), math.sin(roll)

    def P(lx, ly, lz):
        lx2, ly2 = lx * cr - ly * sr, lx * sr + ly * cr
        return L(x, z, h)(lx2, ly2 + y, lz)
    s = view.scale(P(0, 0.5, 0)) or 10
    w = max(2.0, 0.045 * s)
    for wz in (-0.52, 0.52):
        c = P(0, 0.34, wz)
        pts = [view.pt(P(0, 0.34 + 0.34 * math.sin(a), wz + 0.34 * math.cos(a))) for a in np.linspace(0, 2 * math.pi, 26)]
        if all(pts):
            poly(ctx, pts)
            setc(ctx, hexc('#1b1b22'))
            ctx.set_line_width(max(2.5, 0.07 * s))
            ctx.stroke()
            poly(ctx, pts)
            setc(ctx, hexc('#c9ccd6'))
            ctx.set_line_width(max(1, 0.02 * s))
            ctx.stroke()
        hub = view.pt(c)
        if hub:
            ellipse(ctx, hub[0], hub[1], max(2, 0.03 * s), max(2, 0.03 * s))
            setc(ctx, hexc('#555'.replace('#555', '#555555')))
            ctx.fill()
    J = {'rear': P(0, 0.34, -0.52), 'front': P(0, 0.34, 0.52), 'bb': P(0, 0.3, -0.05), 'seat': P(0, 0.88, -0.28), 'head': P(0, 0.92, 0.36),
         'bar': P(0, 1.02, 0.4), 'saddle': P(0, 0.95, -0.32)}
    Q = {k: view.pt(v) for k, v in J.items()}
    if not all(Q.values()):
        return
    c = hexc(col)
    for a, b in (('rear', 'bb'), ('bb', 'seat'), ('seat', 'rear'), ('seat', 'head'), ('bb', 'head'), ('head', 'front'), ('head', 'bar')):
        ctx.move_to(*Q[a])
        ctx.line_to(*Q[b])
    setc(ctx, OUTL)
    ctx.set_line_width(w + 3)
    ctx.stroke()
    for a, b in (('rear', 'bb'), ('bb', 'seat'), ('seat', 'rear'), ('seat', 'head'), ('bb', 'head'), ('head', 'front'), ('head', 'bar')):
        ctx.move_to(*Q[a])
        ctx.line_to(*Q[b])
    setc(ctx, c)
    ctx.set_line_width(w)
    ctx.stroke()
    for sx in (-0.24, 0.24):
        q = view.pt(P(sx, 1.02, 0.4))
        if q:
            ctx.move_to(*Q['bar'])
            ctx.line_to(*q)
    setc(ctx, hexc('#1b1b22'))
    ctx.set_line_width(max(2, 0.035 * s))
    ctx.stroke()
    sp = [view.pt(P(sx, 0.95, zz)) for sx, zz in ((-0.07, -0.42), (0.07, -0.42), (0.05, -0.2), (-0.05, -0.2))]
    if all(sp):
        poly(ctx, sp)
        fill_stroke(ctx, hexc('#1b1b22'), OUTL, 1)


def rider_pts(phase, pose='ride'):
    """Rider joints in bike-local coords (x right, y up, z forward)."""
    pa = phase * 2 * math.pi
    if pose == 'ride':
        J = dict(hip=(0, 1.02, -0.3), sh=(0, 1.5, 0.05), head=(0, 1.72, 0.18), hand=(0, 1.04, 0.4))
        feet = []
        for sx, off in ((-0.15, 0.0), (0.15, math.pi)):
            fz, fy = -0.05 + 0.17 * math.cos(pa + off), 0.3 + 0.17 * math.sin(pa + off)
            kz, ky = (J['hip'][2] + fz) / 2 + 0.22, (J['hip'][1] + fy) / 2 + 0.08
            feet.append(((sx, ky, kz), (sx, fy, fz)))
        return J, feet
    # 'tuck': arms forward, knees up (flying)
    J = dict(hip=(0, 0.0, 0.0), sh=(0, 0.5, 0.15), head=(0, 0.72, 0.25), hand=(0, 0.35, 0.65))
    feet = [((sx, 0.05, 0.35), (sx, -0.35, 0.2)) for sx in (-0.15, 0.15)]
    return J, feet


def draw_rider(ctx, view, T, phase, pose='ride', top='#2f6f73', pants='#2a2a33', helmet='#f2a541', skin=None, expr='calm'):
    """T(lx, ly, lz) -> world point for the rider frame."""
    skin = skin or SKIN
    J, feet = rider_pts(phase, pose)
    Pt = {k: view.pt(T(*v)) for k, v in J.items()}
    s = view.scale(T(*J['sh'])) or 10
    if not all(Pt.values()):
        return
    w = max(3.0, 0.11 * s)
    # far leg first, then body, then near leg (simple: both legs then body)
    for knee, foot in feet:
        k, f = view.pt(T(*knee)), view.pt(T(*foot))
        if k and f:
            _limb(ctx, Pt['hip'], k, w * 1.1, hexc(pants))
            _limb(ctx, k, f, w, hexc(pants))
            ellipse(ctx, f[0], f[1], w * 0.6, w * 0.4)
            fill_stroke(ctx, hexc('#1b1b22'), OUTL, 1)
    _limb(ctx, Pt['hip'], Pt['sh'], w * 1.9, hexc(top))
    _limb(ctx, Pt['sh'], Pt['hand'], w * 0.8, hexc(top))
    ellipse(ctx, Pt['hand'][0], Pt['hand'][1], w * 0.45, w * 0.45)
    fill_stroke(ctx, skin, OUTL, 1)
    hp = Pt['head']
    r = 0.13 * s
    ellipse(ctx, hp[0], hp[1], r, r * 1.05)
    fill_stroke(ctx, skin, OUTL, max(1, s / 60))
    ctx.arc(hp[0], hp[1] - r * 0.1, r * 1.12, math.pi, 2 * math.pi)
    ctx.close_path()
    fill_stroke(ctx, hexc(helmet), OUTL, max(1, s / 60))
    if expr == 'shock' and r > 6:
        ellipse(ctx, hp[0], hp[1] + r * 0.45, r * 0.18, r * 0.25)
        setc(ctx, OUTL)
        ctx.fill()


class Cyclist(Track):
    """Bike + rider. crash=(t_hit, fly_fn) where fly_fn(u) gives rider (dx, dy, dz, pitch) after impact (u = t - t_hit);
    the bike stops dead and falls over (roll) after t_hit."""

    def __init__(self, x, speed, ta, za, top='#2f6f73', bike='#e0393e', helmet='#f2a541', crash=None, mark=None, expr=None):
        super().__init__(x, speed, ta, za, bike)
        self.top, self.bike_col, self.helmet, self.crash, self.mark = top, bike, helmet, crash, mark
        self.expr = expr or (lambda t: 'calm')
        self.ext = (-0.9, 0.9, 0.3, 1.6)
        self.kind = 'bike'

    def pedal_phase(self, t):
        return self.z(t) / (2 * math.pi * 0.34 * 2.4)

    def items(self, ctx, view, t):
        x, z, h = self.pose(t)
        if view.ortho:
            def top():
                p = view.pt((x, 0, z))
                rrect(ctx, p[0] - 0.25 * view.s, p[1] - 0.9 * view.s, 0.5 * view.s, 1.8 * view.s, 0.2 * view.s)
                fill_stroke(ctx, hexc(self.top), OUTL, 2)
            return [((x, 1.0, z), top)]
        d = view.depth((x, 1, z))
        if d < -5 or d > 260:
            return []
        ph = self.pedal_phase(t)
        crashed = self.crash and t >= self.crash[0]
        roll = 0.0
        if crashed:
            u = t - self.crash[0]
            roll = -1.45 * smooth(u / 0.7)
        out = []

        def bike():
            if self.mark and self.mark(t):
                mark_ring(ctx, view, x, z, h, t)
            bicycle(ctx, view, x, 0.0, z, h, roll, ph, self.bike_col)
            if self.mark and self.mark(t):
                mark_arrow(ctx, view, x, z, t)
        out.append(((x, 0.6, z), bike))
        if not crashed:
            Lf = L(x, z, h)
            out.append(((x, 1.3, z - 0.05), lambda: draw_rider(ctx, view, lambda a, b, c: Lf(a, b, c), ph, 'ride', self.top,
                                                               helmet=self.helmet, expr=self.expr(t))))
        else:
            u = t - self.crash[0]
            dx, dy, dz, pitch, pose = self.crash[1](u)
            cx_, cy_, cz_ = x + dx, dy, z + dz
            cp, sp = math.cos(pitch), math.sin(pitch)

            def T(a, b, c):
                b2, c2 = b * cp - c * sp, b * sp + c * cp
                return (cx_ + a, cy_ + b2, cz_ + c2)
            out.append(((cx_, cy_ + 0.3, cz_), lambda: draw_rider(ctx, view, T, 0.25, pose, self.top, helmet=self.helmet, expr='shock')))
        return out


def fly_default(u, v0=4.5):
    """Thrown over the door: up and forward, pitching over, lands lying on the road (pose tuck -> lying)."""
    tf = 0.75
    if u < tf:
        k = u / tf
        return (-0.6 * k, 1.1 + 0.9 * math.sin(math.pi * k) - 0.6 * k, v0 * u * 0.8, 1.6 * k, 'tuck')
    k = min(1.0, (u - tf) / 0.5)
    return (-0.6 - 0.25 * k, 0.5 - 0.25 * k, v0 * tf * 0.8 + 0.6 * k, 1.6 + 0.1 * k, 'tuck')


# ------------------------------------------------------------------ close-ups
def side_mirror(ctx, w, t, lt, kw):
    """Driver's side mirror (left): oval glass showing the street behind (the bike lane), car door + window frame."""
    H = kw.get('car', EP.hero)
    t = t + kw.get('dt', 0.0)
    x, z, h = H.pose(t)
    view = TCam((x - 1.2, 1.25, z + 1.0), 0.0, 0.03, 900, cx=960, cy=1000)
    draw_scene(ctx, view, w, t, ego=False)
    warm_haze(ctx, view, CANVAS)
    # car window frame (we look out of the driver window)
    setc(ctx, hexc('#24252e'))
    ctx.rectangle(-10, -10, CANVAS + 20, 160)
    ctx.fill()
    ctx.rectangle(-10, 1560, CANVAS + 20, 400)
    ctx.fill()
    ctx.rectangle(1640, -10, 300, CANVAS + 20)
    ctx.fill()
    rrect(ctx, 520, 600, 900, 620, 260)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, 8)
    ctx.save()
    rrect(ctx, 560, 640, 820, 540, 230)
    ctx.clip()
    mc = TCam((x - 1.05, 1.15, z + 0.7), math.pi + 0.06, 0.04, 650, cx=960, cy=930, mirror=True)
    draw_scene(ctx, mc, w, t, ego=False)
    g = cairo.LinearGradient(560, 640, 1380, 1180)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.18)
    g.add_color_stop_rgba(0.5, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    if kw.get('glow', True):
        rrect(ctx, 560, 640, 820, 540, 230)
        setc(ctx, hexc('#ffd23f'), 0.6 + 0.4 * math.sin(lt * 8))
        ctx.set_line_width(12)
        ctx.stroke()
    grade(ctx, t, CANVAS, CANVAS, 0.7)


def reach_close(ctx, w, t, lt, kw):
    """Inside the car, looking at the driver from the passenger side. mode 'wrong': left (near) hand pushes the door,
    eyes forward. mode 'right': Dutch Reach - right (far) hand crosses the body to the handle, shoulders turn, head looks
    back over the left shoulder."""
    mode = kw.get('mode', 'right')
    g = cairo.LinearGradient(0, 0, 0, CANVAS)
    g.add_color_stop_rgb(0, *hexc('#2b2838'))
    g.add_color_stop_rgb(1, *hexc('#15131c'))
    ctx.set_source(g)
    ctx.paint()
    # driver window + door panel on the left of the frame
    rrect(ctx, 40, 260, 620, 560, 60)
    fill_stroke(ctx, hexc('#9fd3ea'), OUTL, 8)
    H = kw.get('car', EP.hero)
    tw = t + kw.get('dt', 0.0)
    x, z, h = H.pose(tw)
    ctx.save()
    rrect(ctx, 40, 260, 620, 560, 60)
    ctx.clip()
    view = TCam((x - 0.4, 1.3, z - 0.3), math.pi + 0.9, 0.05, 560, cx=350, cy=560)
    draw_scene(ctx, view, w, tw, ego=False)
    ctx.restore()
    rrect(ctx, 0, 820, 700, 1100, 40)
    fill_stroke(ctx, hexc('#3a3650'), OUTL, 8)
    hx, hy = 520, 980                                          # door handle
    rrect(ctx, hx - 70, hy - 26, 140, 52, 26)
    fill_stroke(ctx, hexc('#b8bccb'), OUTL, 6)
    # seat
    rrect(ctx, 760, 520, 620, 1400, 200)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 8)
    u = smooth(lt / 0.8)
    turn = (-0.75 * u) if mode == 'right' else 0.0
    # body (shoulders rotate for the reach)
    bx = 1080 - 120 * u * (1 if mode == 'right' else 0)
    ctx.save()
    ctx.translate(bx, 1300)
    ctx.rotate(-0.18 * u if mode == 'right' else 0.0)
    rrect(ctx, -280, -260, 560, 720, 160)
    fill_stroke(ctx, JACKET, OUTL, 8)
    ctx.restore()
    head2d(ctx, bx + (-60 * u if mode == 'right' else 0), 900, 210, 'hero', 'focus' if mode == 'right' else 'calm', turn, t)
    # arm to the handle
    if mode == 'right':
        sx, sy = bx + 230, 1120                               # far (right) shoulder
        k = smooth((lt - 0.2) / 0.8)
        ex, ey = sx + (hx + 60 - sx) * k, sy + (hy - sy) * k
        _limb(ctx, (sx, sy), ((sx + ex) / 2 + 60, (sy + ey) / 2 + 120), 90, JACKET)
        _limb(ctx, ((sx + ex) / 2 + 60, (sy + ey) / 2 + 120), (ex, ey), 80, JACKET)
        ellipse(ctx, ex - 10, ey, 70, 55)
        fill_stroke(ctx, SKIN, OUTL, 6)
        if lt > 1.2:
            ctx.save()
            ctx.translate(1300, 260)
            outlined_text(ctx, 'FAR HAND', 0, 0, 110, hexc('#22c35e'), lw=20)
            ctx.restore()
    else:
        sx, sy = bx - 230, 1120                               # near (left) shoulder
        k = smooth((lt - 0.2) / 0.6)
        ex, ey = sx + (hx + 40 - sx) * k, sy + (hy - sy) * k - 40 * k
        _limb(ctx, (sx, sy), (ex, ey), 90, JACKET)
        ellipse(ctx, ex, ey, 70, 55)
        fill_stroke(ctx, SKIN, OUTL, 6)
        if lt > 0.9:
            ctx.save()
            ctx.translate(980, 300)
            ctx.rotate(-0.1)
            outlined_text(ctx, 'SHOVE!', 0, 0, 140, hexc('#ffd23f'), lw=24)
            ctx.restore()
    grade(ctx, t, CANVAS, CANVAS, 0.6, grain=0.04)


engine.SCENES.update(side_mirror=side_mirror, reach_close=reach_close)


def portland_far(ctx, view):
    """Backdrop: Mount Hood-like snow peak above the city."""
    if view.ortho:
        return
    Zb = view.pos[2]
    mountains(ctx, view, Z=Zb + 3600, col='#7d8db0', snow='#ffffff', haze='#ffd8a8', seed=3, peaks=2, hmax=900, x0=-900, x1=1500)
