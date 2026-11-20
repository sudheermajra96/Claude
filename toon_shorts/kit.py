"""Shared kit for the traffic-safety series (house style: 2D, letterboxed 16:9 band, SFX only).

Fixes applied to every new episode:
  * no side mirror drawn on the dashboard (engine.COCKPIT_MIRROR = False, street cockpit has none)
  * small, realistic emergency lights (no giant glows), subtle flash tint
  * no bird / chirp ambience
  * clean modern dashboard (dash2)
  * whistling uses a puckered mouth with music notes
"""
from street import *
from street import _t
import street
import engine

engine.COCKPIT_MIRROR = False


# ---------------------------------------------------------------- dashboard
def seatbelt_icon(ctx, x, y, s, col):
    ellipse(ctx, x, y - 30 * s, 13 * s, 13 * s)
    setc(ctx, col)
    ctx.fill()
    ctx.move_to(x - 22 * s, y + 38 * s)
    ctx.curve_to(x - 24 * s, y - 10 * s, x + 24 * s, y - 10 * s, x + 22 * s, y + 38 * s)
    ctx.close_path()
    ctx.fill()
    ctx.move_to(x + 20 * s, y - 14 * s)
    ctx.line_to(x - 14 * s, y + 34 * s)
    setc(ctx, hexc('#0d0f1c'))
    ctx.set_line_width(6 * s)
    ctx.stroke()


def beam_icon(ctx, x, y, s, col, high=False):
    ctx.arc(x - 8 * s, y, 24 * s, math.pi / 2, 3 * math.pi / 2)
    ctx.close_path()
    setc(ctx, col)
    ctx.fill()
    for k in range(4):
        dy = (-22 + k * 15) * s
        ctx.move_to(x + 22 * s, y + dy)
        ctx.line_to(x + 52 * s, y + dy + (0 if high else 8 * s))
    ctx.set_line_width(5 * s)
    ctx.stroke()


def dash2(ctx, world, t, lt, kw):
    """Clean instrument cluster: one big speed ring with a digital readout, arrows, warning icons."""
    g = cairo.LinearGradient(0, 0, 0, SH)
    g.add_color_stop_rgb(0, *hexc('#0b0d18'))
    g.add_color_stop_rgb(1, *hexc('#161a2e'))
    ctx.set_source(g)
    ctx.paint()
    rrect(ctx, 260, 110, 1400, 860, 180)
    fill_stroke(ctx, hexc('#11142a'), hexc('#2c3150'), 8)
    mph = kw.get('unit') == 'mph' or getattr(world, 'units', '') == 'mph'
    spd = world.speed(t) * (2.237 if mph else 3.6)
    cx, cy, R = 960, 560, 330
    a0, a1 = math.radians(135), math.radians(405)
    ctx.arc(cx, cy, R, a0, a1)
    setc(ctx, hexc('#23284a'))
    ctx.set_line_width(30)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.stroke()
    frac = clamp(spd / 200)
    if frac > 0.003:
        lim = kw.get('limit')
        col = hexc('#ff4b4b') if (lim and spd > lim + 1) else hexc('#3cc9ff')
        ctx.arc(cx, cy, R, a0, a0 + (a1 - a0) * frac)
        setc(ctx, col)
        ctx.set_line_width(30)
        ctx.stroke()
        ex, ey = cx + math.cos(a0 + (a1 - a0) * frac) * R, cy + math.sin(a0 + (a1 - a0) * frac) * R
        glow(ctx, ex, ey, 70, col, 0.35)
    for v in range(0, 201, 40):
        a = a0 + (a1 - a0) * v / 200
        text_center(ctx, str(v), cx + math.cos(a) * (R - 75), cy + math.sin(a) * (R - 75) + 12, 34,
                    hexc('#8d94c0'), cairo.FONT_WEIGHT_NORMAL)
    text_center(ctx, f"{int(round(spd))}", cx, cy + 50, 170, (1, 1, 1))
    text_center(ctx, 'mph' if mph else 'km/h', cx, cy + 120, 42, hexc('#8d94c0'), cairo.FONT_WEIGHT_NORMAL)
    # turn arrows (outside the ring, top corners)
    for side, fn in ((-1, world.blink_left), (1, world.blink_right)):
        on = fn(t) > 0.5
        ax, ay = cx + side * 470, 230
        pts = [(ax + side * 50, ay), (ax, ay - 42), (ax, ay - 18), (ax - side * 46, ay - 18),
               (ax - side * 46, ay + 18), (ax, ay + 18), (ax, ay + 42)]
        poly(ctx, pts)
        setc(ctx, hexc('#2bff6a') if on else hexc('#1f3a2a'))
        ctx.fill()
        if on:
            glow(ctx, ax, ay, 110, hexc('#2bff6a'), 0.45)
    # warning row
    wy = 890
    belt = kw.get('belt_warn')
    on = bool(belt) and (belt(lt) > 0.5 if callable(belt) else True) and ((t * 2) % 1 < 0.6)
    seatbelt_icon(ctx, 720, wy, 1.0, hexc('#ff3b3b') if on else hexc('#3a2a33'))
    hl = world.headlights(t)
    hb = kw.get('highbeam', lambda lt: 0)(lt)
    beam_icon(ctx, 960, wy, 1.0, hexc('#2f7bff') if hb > 0.5 else (hexc('#3cff7a') if hl > 0.5 else hexc('#1f3a2a')), hb > 0.5)
    rrect(ctx, 1150, wy - 30, 110, 60, 14)
    setc(ctx, hexc('#ff5a36') if world.ego_brake(t) > 0.5 else hexc('#2a2233'))
    ctx.set_line_width(6)
    ctx.stroke()
    text_center(ctx, '!', 1205, wy + 18, 46, hexc('#ff5a36') if world.ego_brake(t) > 0.5 else hexc('#2a2233'))


# ------------------------------------------------------- objects on the street
def pedestrian(ctx, cam, x, z, t, top='#e05d5d', pants='#2b3a63', skin='#e8b48f', hair='#3a2316',
               kid=False, walking=True, wave=0.0, startle=0.0):
    if z < 1.6:
        return
    H_ = 1.25 if kid else 1.72
    s = cam.f / z
    bx, by = cam.p(x, 0, z)
    ph = t * 2 * math.pi * 1.6 if walking else 0
    lw = max(2, min(5, 60 / z))
    leg = H_ * 0.45 * s
    hip = (bx, by - leg)
    for k in (-1, 1):
        fx = bx + k * math.sin(ph) * leg * 0.35
        ctx.move_to(*hip)
        ctx.line_to(fx, by)
        setc(ctx, OUTL)
        ctx.set_line_width(H_ * 0.11 * s + lw)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        ctx.move_to(*hip)
        ctx.line_to(fx, by)
        setc(ctx, hexc(pants))
        ctx.set_line_width(H_ * 0.11 * s)
        ctx.stroke()
    bw, bh = H_ * 0.26 * s, H_ * 0.36 * s
    jump = startle * 0.08 * s
    rrect(ctx, bx - bw / 2, hip[1] - bh - jump, bw, bh + bw * 0.1, bw * 0.35)
    fill_stroke(ctx, hexc(top), OUTL, lw)
    if kid:
        rrect(ctx, bx - bw * 0.65, hip[1] - bh * 0.9 - jump, bw * 0.35, bh * 0.6, bw * 0.12)
        fill_stroke(ctx, hexc('#f2c230'), OUTL, lw)
    shy = hip[1] - bh * 0.9 - jump
    for k in (-1, 1):
        if k > 0 and wave > 0:
            ex_, ey_ = bx + bw * 0.9, shy - bh * 0.6 - math.sin(t * 12) * bw * 0.25 * wave
        elif startle > 0:
            ex_, ey_ = bx + k * bw * 1.0, shy - bh * 0.5
        else:
            ex_, ey_ = bx + k * bw * 0.55 - k * math.sin(ph) * bw * 0.3, hip[1] - bh * 0.1 - jump
        ctx.move_to(bx + k * bw * 0.45, shy)
        ctx.line_to(ex_, ey_)
        setc(ctx, OUTL)
        ctx.set_line_width(H_ * 0.07 * s + lw)
        ctx.stroke()
        ctx.move_to(bx + k * bw * 0.45, shy)
        ctx.line_to(ex_, ey_)
        setc(ctx, hexc(top))
        ctx.set_line_width(H_ * 0.07 * s)
        ctx.stroke()
        ellipse(ctx, ex_, ey_, H_ * 0.035 * s, H_ * 0.035 * s)
        fill_stroke(ctx, hexc(skin), OUTL, lw * 0.6)
    hr = H_ * 0.11 * s
    hx, hy = bx, hip[1] - bh - hr * 0.9 - jump
    ellipse(ctx, hx, hy, hr, hr * 1.08)
    fill_stroke(ctx, hexc(skin), OUTL, lw)
    ctx.arc(hx, hy - hr * 0.15, hr * 1.02, math.pi * 1.0, math.pi * 2.0)
    ctx.close_path()
    setc(ctx, hexc(hair))
    ctx.fill()
    for k in (-1, 1):
        ellipse(ctx, hx + k * hr * 0.38, hy + hr * 0.15, hr * (0.16 if startle else 0.1), hr * (0.2 if startle else 0.12))
        setc(ctx, OUTL)
        ctx.fill()
    if startle:
        ellipse(ctx, hx, hy + hr * 0.6, hr * 0.18, hr * 0.22)
        setc(ctx, hexc('#5e1419'))
        ctx.fill()


def traffic_light_overhead(ctx, cam, x_pole, z, state, x_head=1.6):
    """Mast-arm signal: pole on the corner, big housing hanging over our lane (readable on screen)."""
    if z < 2:
        return
    lw = max(1, 30 / z)
    bx, by = cam.p(x_pole, 0, z)
    tx, ty = cam.p(x_pole, 5.6, z)
    w = 0.22 * cam.f / z
    ctx.rectangle(bx - w / 2, ty, w, by - ty)
    fill_stroke(ctx, hexc('#4a4e5c'), OUTL, lw)
    ax, ay = cam.p(x_head - 0.6, 5.6, z)
    th = 0.18 * cam.f / z
    ctx.rectangle(ax, ay - th / 2, tx - ax, th)
    fill_stroke(ctx, hexc('#4a4e5c'), OUTL, lw)
    hx, hy = cam.p(x_head, 5.6, z)
    hw, hh = 0.9 * cam.f / z, 2.3 * cam.f / z
    rrect(ctx, hx - hw / 2, hy, hw, hh, hw * 0.2)
    fill_stroke(ctx, hexc('#22242e'), OUTL, lw)
    cols = {'red': '#ff3030', 'yellow': '#ffc21a', 'green': '#2bdc6a'}
    for i, nm in enumerate(('red', 'yellow', 'green')):
        cy_ = hy + hh * (0.18 + 0.32 * i)
        r = hw * 0.34
        on = state == nm
        ellipse(ctx, hx, cy_, r, r)
        setc(ctx, hexc(cols[nm]) if on else mix(hexc(cols[nm]), (0, 0, 0), 0.72))
        ctx.fill()
        if on:
            glow(ctx, hx, cy_, r * 3.0, hexc(cols[nm]), 0.6)


def traffic_light(ctx, cam, x, z, state):
    """state: 'red' | 'yellow' | 'green'. Pole on the far corner, housing at 3.4 m."""
    if z < 2:
        return
    bx, by = cam.p(x, 0, z)
    tx, ty = cam.p(x, 3.0, z)
    w = 0.13 * cam.f / z
    ctx.rectangle(bx - w / 2, ty, w, by - ty)
    fill_stroke(ctx, hexc('#4a4e5c'), OUTL, max(1, 30 / z))
    hw, hh = 0.42 * cam.f / z, 1.2 * cam.f / z
    hx, hy = tx, ty - hh
    rrect(ctx, hx - hw / 2, hy, hw, hh, hw * 0.25)
    fill_stroke(ctx, hexc('#22242e'), OUTL, max(1, 30 / z))
    cols = {'red': '#ff3030', 'yellow': '#ffc21a', 'green': '#2bdc6a'}
    for i, nm in enumerate(('red', 'yellow', 'green')):
        cy_ = hy + hh * (0.2 + 0.3 * i)
        r = hw * 0.32
        on = state == nm
        ellipse(ctx, hx, cy_, r, r)
        setc(ctx, hexc(cols[nm]) if on else mix(hexc(cols[nm]), (0, 0, 0), 0.72))
        ctx.fill()
        if on:
            glow(ctx, hx, cy_, r * 3.2, hexc(cols[nm]), 0.55)


def emergency_lights(ctx, cam, x, y, z, t, w=1.3):
    """Compact light bar: alternating red / blue, modest glow."""
    ph = (t * 3.2) % 1 < 0.5
    bw = w * cam.f / z
    cx_, cy_ = cam.p(x, y, z)
    bh = 0.16 * cam.f / z
    rrect(ctx, cx_ - bw / 2, cy_ - bh / 2, bw, bh, bh * 0.4)
    fill_stroke(ctx, hexc('#2a2a33'), OUTL, max(1, 30 / z))
    for s, col, on in ((-1, hexc('#ff2a2a'), ph), (1, hexc('#2a6bff'), not ph)):
        lx = cx_ + s * bw * 0.25
        rrect(ctx, lx - bw * 0.22, cy_ - bh * 0.4, bw * 0.44, bh * 0.8, bh * 0.3)
        setc(ctx, col if on else mix(col, (0, 0, 0), 0.6))
        ctx.fill()
        if on:
            glow(ctx, lx, cy_, min(0.7 * cam.f / z, 140), col, 0.45)


def police_lightbar_small(ctx, cam, x, y, z, t, w=1.2, bright=1.0):
    emergency_lights(ctx, cam, x, y, z, t, w)


street.police_lightbar = police_lightbar_small     # fix the oversized police glows


def ambulance_front(ctx, cam, x, z, t, lights=True):
    lw = max(1.5, min(4, 50 / z))
    white, red = hexc('#f6f6f6'), hexc('#e23a3a')
    box(ctx, cam, x - 1.0, x + 1.0, 0.3, 2.6, z + 1.6, z + 6.2, white, mix(white, (0, 0, 0), 0.12), white, lw)
    box(ctx, cam, x - 1.0, x + 1.0, 0.3, 1.5, z, z + 1.6, white, mix(white, (0, 0, 0), 0.12), white, lw)
    box(ctx, cam, x - 0.85, x + 0.85, 1.5, 2.1, z + 0.6, z + 1.6, hexc('#2a3448'), hexc('#2a3448'), white, lw)
    a, b = cam.p(x - 1.0, 1.0, z - 0.01), cam.p(x + 1.0, 1.15, z - 0.01)
    ctx.rectangle(a[0], b[1], b[0] - a[0], a[1] - b[1])
    setc(ctx, red)
    ctx.fill()
    for s in (-1, 1):
        cx_, cy_ = cam.p(x + s * 0.7, 0.7, z - 0.02)
        rr = 0.14 * cam.f / z
        ellipse(ctx, cx_, cy_, rr * 1.3, rr * 0.8)
        setc(ctx, (1, 1, 0.92))
        ctx.fill()
    if lights:
        emergency_lights(ctx, cam, x, 2.7, z + 1.62, t, 1.5)


def ambulance_rear(ctx, cam, x, z, t):
    lw = max(1.5, min(4, 50 / z))
    white, red = hexc('#f6f6f6'), hexc('#e23a3a')
    box(ctx, cam, x - 1.0, x + 1.0, 0.3, 2.6, z, z + 6.0, white, mix(white, (0, 0, 0), 0.12), white, lw)
    a, b = cam.p(x - 1.0, 1.0, z - 0.01), cam.p(x + 1.0, 1.2, z - 0.01)
    ctx.rectangle(a[0], b[1], b[0] - a[0], a[1] - b[1])
    setc(ctx, red)
    ctx.fill()
    cx_, cy_ = cam.p(x, 1.8, z - 0.01)
    r = 0.35 * cam.f / z
    for rect in ((cx_ - r * 0.3, cy_ - r, r * 0.6, r * 2), (cx_ - r, cy_ - r * 0.3, r * 2, r * 0.6)):
        ctx.rectangle(*rect)
    setc(ctx, red)
    ctx.fill()
    emergency_lights(ctx, cam, x, 2.7, z + 0.2, t, 1.5)


def car_rear_simple(ctx, cam, x, z, col, t, brake=0.0, kind='car'):
    v = Vehicle(kind, x, z, col, brake=const(brake))
    draw_vehicle_rear(ctx, cam, v, t, x, z, 0.0)


def car_front_simple(ctx, cam, x, z, col, t, highbeam=0.0):
    v = Vehicle('car', x, z, col, highbeam=const(highbeam))
    draw_vehicle_front(ctx, cam, v, t, x, z)


def moto_front(ctx, cam, x, d, t):
    lw = max(1.5, min(4, 40 / d))
    s = cam.f / d
    bx, by = cam.p(x, 0, d)
    ctx.rectangle(bx - 0.12 * s, by - 0.65 * s, 0.24 * s, 0.65 * s)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, lw)
    rrect(ctx, bx - 0.3 * s, by - 1.05 * s, 0.6 * s, 0.45 * s, 0.1 * s)
    fill_stroke(ctx, hexc('#e0393e'), OUTL, lw)
    rrect(ctx, bx - 0.22 * s, by - 1.55 * s, 0.44 * s, 0.6 * s, 0.15 * s)
    fill_stroke(ctx, hexc('#2b3a63'), OUTL, lw)
    ellipse(ctx, bx, by - 1.75 * s, 0.17 * s, 0.19 * s)
    fill_stroke(ctx, hexc('#f2c230'), OUTL, lw)
    ellipse(ctx, bx, by - 1.72 * s, 0.12 * s, 0.07 * s)
    setc(ctx, hexc('#1b2030'))
    ctx.fill()
    hx, hy = bx, by - 0.85 * s
    ellipse(ctx, hx, hy, 0.09 * s, 0.07 * s)
    setc(ctx, (1, 1, 0.92))
    ctx.fill()
    glow(ctx, hx, hy, min(1.2 * s, 500), WHITE_L, 0.8)


def moto_rear(ctx, cam, x, z, t):
    if z < 1.8:
        return
    lw = max(1.5, min(4, 40 / z))
    s = cam.f / z
    bx, by = cam.p(x, 0, z)
    ctx.rectangle(bx - 0.12 * s, by - 0.65 * s, 0.24 * s, 0.65 * s)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, lw)
    rrect(ctx, bx - 0.3 * s, by - 1.0 * s, 0.6 * s, 0.4 * s, 0.1 * s)
    fill_stroke(ctx, hexc('#e0393e'), OUTL, lw)
    rrect(ctx, bx - 0.24 * s, by - 1.55 * s, 0.48 * s, 0.62 * s, 0.15 * s)
    fill_stroke(ctx, hexc('#2b3a63'), OUTL, lw)
    ellipse(ctx, bx, by - 1.75 * s, 0.17 * s, 0.19 * s)
    fill_stroke(ctx, hexc('#f2c230'), OUTL, lw)
    tx, ty = bx, by - 0.78 * s
    ellipse(ctx, tx, ty, 0.07 * s, 0.05 * s)
    setc(ctx, RED)
    ctx.fill()
    glow(ctx, tx, ty, min(0.8 * s, 300), RED, 0.6)


# vehicles of kind 'moto' / 'ambulance' inside the engine's highway views
_orig_front, _orig_rear = engine.draw_vehicle_front, engine.draw_vehicle_rear


def _front(ctx, cam, v, t, X, D, scene_light=1.0):
    if v.kind == 'moto':
        return moto_front(ctx, cam, X, D, t)
    if v.kind == 'ambulance':
        return ambulance_front(ctx, cam, X, D, t)
    return _orig_front(ctx, cam, v, t, X, D, scene_light)


def _rear(ctx, cam, v, t, X, Z, lit):
    if v.kind == 'moto':
        return moto_rear(ctx, cam, X, Z, t)
    if v.kind == 'ambulance':
        return ambulance_rear(ctx, cam, X, Z, t)
    return _orig_rear(ctx, cam, v, t, X, Z, lit)


engine.draw_vehicle_front, engine.draw_vehicle_rear = _front, _rear
draw_vehicle_front, draw_vehicle_rear = _front, _rear


# --------------------------------------------------------- night highway POV
class Oncoming:
    def __init__(self, X, Z, col='#d8d8e0', highbeam=None, flash=None):
        self.X = X if callable(X) else const(X)
        self.Z = Z
        self.color = hexc(col)
        self.kind = 'car'
        self.highbeam = highbeam or const(0)
        self.flash = flash or const(0)


def wipers(ctx, ang):
    for px, k in ((620, 1.0), (1180, 1.0)):
        a = -math.pi + 0.15 + ang
        ex, ey = px + math.cos(a) * 640 * k, 820 + math.sin(a) * 640 * k
        ctx.move_to(px, 820)
        ctx.line_to(ex, ey)
        setc(ctx, hexc('#111116'))
        ctx.set_line_width(16)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
        ctx.move_to(px + math.cos(a) * 200, 820 + math.sin(a) * 200)
        ctx.line_to(ex, ey)
        ctx.set_line_width(26)
        ctx.stroke()


def rain_fx(ctx, t, amount=1.0, wiper=None):
    rnd = random.Random(int(t * 30))
    for _ in range(int(160 * amount)):
        x, y = rnd.uniform(-100, SW), rnd.uniform(-50, 820)
        L = rnd.uniform(30, 70)
        ctx.move_to(x, y)
        ctx.line_to(x + L * 0.25, y + L)
    setc(ctx, (0.85, 0.9, 1.0), 0.35)
    ctx.set_line_width(2.5)
    ctx.stroke()
    rnd2 = random.Random(5)
    for i in range(70):
        x, y, r = rnd2.uniform(0, SW), rnd2.uniform(0, 800), rnd2.uniform(5, 14)
        life_ = ((t * 0.7 + rnd2.random()) % 1)
        ellipse(ctx, x, y + life_ * 20, r, r * 1.15)
        setc(ctx, (0.85, 0.92, 1.0), 0.18 * (1 - life_))
        ctx.fill()
    if wiper is not None:
        wipers(ctx, wiper)


def pov2(ctx, world, t, lt, kw):
    """Night highway POV like the approved signal/distance look, plus oncoming traffic beyond the
    median, high beams, rain, rumble drift, and no dashboard mirror."""
    camx = world.camx(t)
    spd = world.speed(t)
    yaw = -world.steer(t) * 1400 + key_or(kw, 'look', lt, 0.0) * 1400 + key_or(kw, 'skid', lt, 0.0) * 900
    shake = world.shake(t)
    bob = math.sin(t * 11) * 1.2 * min(spd / 30, 1) + shake * 14 * math.sin(t * 71)
    cam = Cam(960 + shake * 10 * math.sin(t * 53), 470 + bob, 1000, camx, 1.2, yaw)
    hl = world.headlights(t)
    hb = key_or(kw, 'highbeam', lt, 0.0)
    lit = lambda Z: hl * clamp(1 - (Z - 6) / (50 + 90 * hb)) * (0.5 + 0.25 * hb)
    draw_sky(ctx, cam.hy, yaw)
    draw_road(ctx, cam, world.dist(t), hl * (1 + 0.6 * hb), 1, lit_fn=lit, dash_light=0.4 + 0.6 * hl)
    # opposite carriageway beyond the median (left)
    ground_quad(ctx, cam, -14.0, -6.2, 1.5, 420, hexc('#1c1c2c'))
    for z0 in range(int(-(world.dist(t) % 12)) + 12, 400, 12):
        ground_quad(ctx, cam, -10.2, -10.0, max(z0, 1.6), z0 + 3.5, hexc('#5a5c78'))
    items = []
    for v in world.vehicles:
        Z = v.Z(t)
        if 2.2 < Z < 400:
            items.append((Z, lambda v=v, Z=Z: draw_vehicle_rear(ctx, cam, v, t, v.X(t), Z, lit(Z))))
    glare = 0.0
    for o in kw.get('oncoming', []):
        Z = o.Z(t)
        if 2.5 < Z < 400:
            items.append((Z, lambda o=o, Z=Z: draw_vehicle_front(ctx, cam, o, t, o.X(t), Z)))
            g_ = (o.highbeam(t) + o.flash(t)) * clamp(1 - (Z - 8) / 90)
            glare = max(glare, g_)
    for zf_, lines in kw.get('signs', []):
        Z = zf_(t)
        if 3 < Z < 400:
            items.append((Z, lambda Z=Z, lines=lines: road_sign(ctx, cam, 6.4, Z, lines, lit(Z))))
    for _, fn in sorted(items, key=lambda it: -it[0]):
        fn()
    if glare > 0.01:
        setc(ctx, (1, 0.98, 0.9), min(0.85, 0.75 * glare))
        ctx.paint()
    if kw.get('rain'):
        rain_fx(ctx, t, kw['rain'], key_or(kw, 'wiper', lt, None) if 'wiper' in kw else None)
    if kw.get('eyelids') is not None:
        e = key_or(kw, 'eyelids', lt, 0.0)
        if e > 0.01:
            setc(ctx, (0, 0, 0))
            ctx.rectangle(0, 0, SW, SH / 2 * e)
            ctx.rectangle(0, SH - SH / 2 * e, SW, SH / 2 * e)
            ctx.fill()
    engine.cockpit(ctx, world, t, cam)


def road_sign(ctx, cam, x, z, lines, lit=0.0):
    """Green highway sign on two posts (right side)."""
    lw = max(1.5, min(4, 50 / z))
    x = x + 0.8
    for px in (x - 1.8, x + 1.8):
        b, tp = cam.p(px, 0, z), cam.p(px, 2.6, z)
        w = 0.12 * cam.f / z
        ctx.rectangle(b[0] - w / 2, tp[1], w, b[1] - tp[1])
        fill_stroke(ctx, hexc('#7a7f90'), OUTL, lw)
    a, b = cam.p(x - 2.9, 5.8, z), cam.p(x + 2.9, 2.5, z)
    rrect(ctx, a[0], a[1], b[0] - a[0], b[1] - a[1], (b[0] - a[0]) * 0.05)
    fill_stroke(ctx, brighten(hexc('#1f7a43'), lit * 2), (1, 1, 1), max(2, 4 * lw / 2))
    h = b[1] - a[1]
    for i, ln in enumerate(lines):
        text_center(ctx, ln, (a[0] + b[0]) / 2, a[1] + h * (0.42 + 0.38 * i), h * (0.3 if i == 0 else 0.24), (1, 1, 1))


def wiper_angle(t, period=1.1):
    u = (t % period) / period
    return math.pi * 0.62 * (0.5 - 0.5 * math.cos(2 * math.pi * u))


def shoulder_check(ctx, world, t, lt, kw):
    """Looking over the left shoulder through the rear side window (night highway)."""
    cam = Cam(1250, 520, 650, world.camx(t) - 1.0, 1.1)
    draw_sky(ctx, 520, 0)
    draw_road(ctx, cam, world.dist(t), 0, -1, zn=1.2, zf=300, dash_light=0.3)
    for v in world.vehicles:
        D = -v.Z(t)
        if 0.8 < D < 300:
            draw_vehicle_front(ctx, cam, v, t, v.X(t), max(D, 1.2))
    # interior frame: B-pillar, seat, roof, door
    setc(ctx, hexc('#20202c'))
    ctx.rectangle(-10, -10, SW + 20, 140)
    ctx.fill()
    poly(ctx, [(1560, -10), (1930, -10), (1930, SH + 10), (1700, SH + 10)])
    ctx.fill()
    rrect(ctx, 1450, 300, 520, 900, 120)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 6)
    ctx.rectangle(-10, 860, 1700, 240)
    setc(ctx, hexc('#2a2a38'))
    ctx.fill()
    ctx.rectangle(-10, 850, 1700, 18)
    setc(ctx, OUTL)
    ctx.fill()
    poly(ctx, [(-10, -10), (140, -10), (60, 870), (-10, 870)])
    setc(ctx, hexc('#20202c'))
    ctx.fill()


# ------------------------------------------------------ day-street extensions
def street_pov2(ctx, world, t, lt, kw):
    """Day street POV with extra actors: traffic light, pedestrians, cars ahead / oncoming,
    ambulance ahead, red-light camera flash."""
    yaw = key_or(kw, 'look', lt, 0.0) * 1400 - world.steer(t) * 1400 + key_or(kw, 'swerve', lt, 0.0) * 600
    spd = world.speed(t)
    shake = world.shake(t)
    bob = math.sin(t * 9) * 1.5 * min(spd / 12, 1) + shake * 12 * math.sin(t * 67)
    cam = Cam(960 + shake * 8 * math.sin(t * 51), 470 + bob, 1000, world.camx(t), 1.2, yaw)
    kw2 = dict(kw)
    ez = world.ego_z(t)
    extra = kw.get('extra', lambda t: [])

    def objects(t_):
        return extra(t_)
    street_scene_ex(ctx, world, cam, t, kw2, objects(t), ez)
    if kw.get('cam_flash') and key_or(kw, 'cam_flash', lt, 0) > 0:
        setc(ctx, (1, 1, 1), 0.85 * key_or(kw, 'cam_flash', lt, 0))
        ctx.paint()
    cockpit_day(ctx, world, t, cam)
    if kw.get('phone_down') is not None:
        f = key_or(kw, 'phone_down', lt, 0.0)
        if f > 0.01:   # driver's eyes on the phone: road view tilts down & blurs out
            setc(ctx, (0.05, 0.05, 0.1), 0.45 * f)
            ctx.paint()
    flash_overlay(ctx, world, t)


def street_scene_ex(ctx, world, cam, t, kw, objects, ez):
    """street_scene + extra depth-sorted objects given as (world_z, draw_fn(ctx, cam, rel_z))."""
    street_scene(ctx, world, cam, t, kw)
    items = []
    for zz, fn in objects:
        d = zz - ez
        if 1.6 < d < 330:
            items.append((d, fn))
    for d, fn in sorted(items, key=lambda it: -it[0]):
        fn(ctx, cam, d)


def flash_overlay(ctx, world, t):
    f = world.police_flash(t)
    if f <= 0:
        return
    ph = (t * 3.2) % 1 < 0.5
    g = cairo.LinearGradient(0, 0, SW, 0)
    col = (1, 0.15, 0.15) if ph else (0.15, 0.35, 1)
    if ph:
        g.add_color_stop_rgba(0, *col, 0.16 * f)
        g.add_color_stop_rgba(0.35, *col, 0)
    else:
        g.add_color_stop_rgba(0.65, *col, 0)
        g.add_color_stop_rgba(1, *col, 0.16 * f)
    ctx.set_source(g)
    ctx.paint()


street.flash_overlay = flash_overlay


def buckle(ctx, world, t, lt, kw):
    """Close-up: hand pulls the belt across and clicks it into the buckle."""
    setc(ctx, hexc('#2e2e40'))
    ctx.paint()
    rrect(ctx, 1150, 520, 600, 700, 120)
    fill_stroke(ctx, hexc('#3d3d50'), OUTL, 6)
    rrect(ctx, 1240, 600, 170, 230, 30)
    fill_stroke(ctx, hexc('#1c1c24'), OUTL, 6)
    rrect(ctx, 1300, 640, 50, 60, 10)
    setc(ctx, hexc('#e0393e'))
    ctx.fill()
    u = key_or(kw, 'pull', lt, 0.0)
    tx, ty = 300 + (1180 - 300) * u, 240 + (650 - 240) * u
    ctx.move_to(-50, -60)
    ctx.line_to(tx - 60, ty - 20)
    ctx.line_to(tx - 60, ty + 40)
    ctx.line_to(-50, 40)
    ctx.close_path()
    fill_stroke(ctx, hexc('#2a2a33'), OUTL, 6)
    rrect(ctx, tx - 80, ty - 30, 150, 80, 12)
    fill_stroke(ctx, hexc('#c9ccd6'), OUTL, 6)
    ellipse(ctx, tx - 120, ty + 30, 120, 90, -0.2)
    fill_stroke(ctx, SKIN, OUTL, 6)
    hose(ctx, (-100, ty + 220), (tx - 160, ty + 50), 40, 120, JACKET)
    if lt >= kw.get('click_t', 99):
        a = 1 - smooth((lt - kw['click_t']) / 0.4)
        for k in range(6):
            ang = k / 6 * 2 * math.pi
            ctx.move_to(1325 + math.cos(ang) * 150, 680 + math.sin(ang) * 150)
            ctx.line_to(1325 + math.cos(ang) * 210, 680 + math.sin(ang) * 210)
        setc(ctx, (1, 1, 1), a)
        ctx.set_line_width(10)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def phone_mount(ctx, world, t, lt, kw):
    """Phone in a dash mount showing a 'Driving Focus' moon screen; notifications stay silent."""
    setc(ctx, hexc('#2a2a38'))
    ctx.paint()
    g = cairo.LinearGradient(0, 0, 0, 500)
    g.add_color_stop_rgb(0, *hexc('#8fd0ff'))
    g.add_color_stop_rgb(1, *hexc('#d9f0ff'))
    ctx.set_source(g)
    ctx.rectangle(0, 0, SW, 420)
    ctx.fill()
    ctx.move_to(-10, 430)
    ctx.curve_to(600, 380, 1300, 380, SW + 10, 430)
    ctx.line_to(SW + 10, SH + 10)
    ctx.line_to(-10, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, hexc('#3a3a4c'), hexc('#55566e'), 5)
    px, py = 960, 600
    rrect(ctx, px - 30, py + 300, 60, 160, 10)
    fill_stroke(ctx, hexc('#1c1c24'), OUTL, 5)
    rrect(ctx, px - 230, py - 400, 460, 760, 60)
    fill_stroke(ctx, hexc('#121218'), OUTL, 7)
    rrect(ctx, px - 205, py - 375, 410, 710, 44)
    g = cairo.LinearGradient(0, py - 375, 0, py + 335)
    g.add_color_stop_rgb(0, *hexc('#2a2f6b'))
    g.add_color_stop_rgb(1, *hexc('#5b3f8f'))
    ctx.set_source(g)
    ctx.fill()
    ellipse(ctx, px, py - 120, 80, 80)
    setc(ctx, hexc('#ffe08a'))
    ctx.fill()
    ellipse(ctx, px + 40, py - 150, 70, 70)
    setc(ctx, hexc('#3a3577'))
    ctx.fill()
    text_center(ctx, 'Driving', px, py + 50, 54, (1, 1, 1))
    text_center(ctx, 'Focus ON', px, py + 115, 54, (1, 1, 1))
    for n0 in kw.get('muted', []):
        if n0 <= lt < n0 + 0.7:
            a = 1 - smooth((lt - n0) / 0.7)
            rrect(ctx, px - 180, py + 180, 360, 90, 24)
            setc(ctx, (1, 1, 1), 0.25 * a)
            ctx.fill()
            text_center(ctx, 'Message (silenced)', px, py + 238, 30, (1, 1, 1), a=a)


def pedal_floor(ctx, world, t, lt, kw):
    engine.SCENES['pedals'](ctx, world, t, lt, kw)


engine.SCENES.update(dash2=dash2, pov2=pov2, shoulder_check=shoulder_check, street_pov2=street_pov2,
                     buckle=buckle, phone_mount=phone_mount)


# --------------------------------------------------------------------- SFX
def rain_sound(d):
    t = _t(d)
    return (bp(noise(len(t)), 600, 7000) * 0.22 + lp(noise(len(t)), 300) * 0.15) * env_adsr(len(t), 0.5, 0.5)


def wiper_thunks(d, period=1.1, t0=0.0):
    out = np.zeros(int(d * SR) + SR)
    tt = 0.0
    while tt < d:
        place(out, lp(noise(int(0.25 * SR)), 900) * np.exp(-np.arange(int(0.25 * SR)) / SR / 0.06) * 0.6, tt)
        place(out, bp(noise(int(0.4 * SR)), 1500, 4000) * np.sin(np.pi * np.arange(int(0.4 * SR)) / (0.4 * SR)) * 0.12, tt + 0.1)
        tt += period / 2
    return out[:int(d * SR)]


def rumble_strip(d):
    t = _t(d)
    s = np.sign(np.sin(2 * np.pi * 38 * t)) * 0.6 + lp(noise(len(t)), 200) * 0.6
    return lp(s, 500) * env_adsr(len(t), 0.05, 0.1) * 0.8


def moto_horn(d=0.5):
    t = _t(d)
    s = np.sign(np.sin(2 * np.pi * 620 * t)) * 0.5 + np.sin(2 * np.pi * 780 * t) * 0.5
    return bp(s, 400, 4000) * env_adsr(len(t), 0.01, 0.05) * 0.45


def moto_pass(d=2.0):
    t = _t(d)
    x = (t - d * 0.5) / (d * 0.18)
    f = 160 * (1 + 0.15 * -np.tanh(x))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = lp(sum(np.sin(k * ph) / k for k in range(1, 10)), 1800) * (1 / (1 + x ** 2))
    return s * 0.6 + whoosh(d, 0.5)[:len(t)] * 0.5


def ambulance_siren(d, doppler=None):
    """Two-tone hi-lo siren."""
    t = _t(d)
    f = np.where((t % 1.0) < 0.5, 960.0, 770.0)
    if doppler is not None:
        f = f * np.interp(t, np.linspace(0, d, len(doppler)), doppler)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = lp(np.sign(np.sin(ph)) * 0.3 + np.sin(ph), 3200)
    return s * env_adsr(len(t), 0.1, 0.4) * 0.28


def seatbelt_chime(n=4):
    out = np.zeros(int(n * 0.6 * SR + SR))
    for i in range(n):
        place(out, bell(midi(81), 0.5) * 0.8, i * 0.6)
    return out


def shutter():
    out = np.zeros(int(0.3 * SR))
    place(out, click(), 0)
    place(out, bp(noise(int(0.08 * SR)), 2000, 8000) * 0.4, 0.06)
    return out


def yawn_sound():
    t = _t(1.2)
    f = 220 - 80 * (t / 1.2)
    s = bp(noise(len(t)), 300, 1500) * 0.4 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
    return s * np.sin(np.pi * t / 1.2) ** 2 * 0.6


def text_ping():
    out = np.zeros(int(0.4 * SR))
    for o, f in ((0, 1318), (0.1, 1760)):
        tt = _t(0.25)
        place(out, np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.07) * 0.4, o)
    return out


def typing_taps(d):
    return typing(d, 5) * 1.2


def car_ambience(world, dur, gain=0.55):
    return ambience(world, dur, inside=0.8) * gain


def run(video, sound, name):
    """python ep_x.py out.mp4          -> full render
       python ep_x.py out.png check    -> contact sheet of one still per shot (for review)"""
    import sys as _sys
    out = _sys.argv[1] if len(_sys.argv) > 1 else name
    if len(_sys.argv) > 2 and _sys.argv[2] == 'check':
        from PIL import Image as _Im
        tiles = []
        for s in video.shots:
            surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
            video.frame(cairo.Context(surf), s.start + s.dur * 0.6)
            buf = _np_from(surf)
            tiles.append(_Im.fromarray(buf).crop((0, int(SCENE_Y) - 160, W, int(SCENE_Y + SCENE_H))).resize((540, 384)))
        cols = 4
        rows = (len(tiles) + cols - 1) // cols
        sheet = _Im.new('RGB', (540 * cols, 384 * rows))
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % cols) * 540, (i // cols) * 384))
        sheet.save(out)
    else:
        video.render(out, sound(), out + '_work')


def _np_from(surf):
    a = np.ndarray((surf.get_height(), surf.get_width(), 4), np.uint8, surf.get_data())
    return a[..., [2, 1, 0]].copy()


def cockpit_day_nomirror(ctx, world, t, cam):
    """Street cockpit without the dashboard mirror."""
    setc(ctx, hexc('#2a2a36'))
    poly(ctx, [(250, -10), (360, -10), (175, 820), (50, 820)])
    ctx.fill()
    poly(ctx, [(1560, -10), (1670, -10), (1880, 820), (1755, 820)])
    ctx.fill()
    ctx.rectangle(-10, -10, SW + 20, 34)
    ctx.fill()
    ctx.move_to(-10, 830)
    ctx.curve_to(500, 790, 1400, 790, SW + 10, 830)
    ctx.line_to(SW + 10, SH + 10)
    ctx.line_to(-10, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, hexc('#3a3a4c'), hexc('#55566e'), 5)
    engine.cockpit_wheel(ctx, world, t)


street.cockpit_day = cockpit_day_nomirror
cockpit_day = cockpit_day_nomirror


# emergency vehicle in mirrors: street.police_car_front draws an ambulance when EMERGENCY == 'ambulance'
EMERGENCY = {'kind': 'police'}
_police_front_orig = street.police_car_front


def _emergency_front(ctx, cam, x, z, t, lights=True):
    if EMERGENCY['kind'] == 'ambulance':
        return ambulance_front(ctx, cam, x, z, t, lights)
    return _police_front_orig(ctx, cam, x, z, t, lights)


street.police_car_front = _emergency_front
