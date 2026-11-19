"""Cycling in a European city: stay in the bike lane, hand signals, changing lanes around an obstacle,
stopping for pedestrians at a zebra crossing. Multi-angle 2D house style, SFX only."""
import math

import euro
from euro import *

engine.DAY = True

speed = Key([(0, 5), (9, 5), (10, 3.5), (16.2, 3.5), (17.8, 4.5), (23.4, 5), (24.6, 5), (26.0, 0), (30.2, 0),
             (31.2, 3.5), (36, 4.5)], 'lin')
lat = Key([(0, 0), (17.8, 0), (18.8, -2.4), (21.6, -2.4), (22.6, 0), (40, 0)])


def arm(t):
    if 13.8 <= t < 17.6:
        return 'left'
    if 20.8 <= t < 22.2:
        return 'right'
    return 'bars'


cars = [
    dict(x=2.8, col='#3a7bd5', rel=Key([(0, -30), (9, -14), (11.2, -6), (12.3, 0), (13.6, 8), (16, 20), (20, 40), (40, 70)])),
    dict(x=2.8, col='#e05d5d', rel=Key([(0, -80), (16.2, -42), (17.8, -36), (21.9, -22), (26, -6), (27, -3.5), (40, -3.5)])),
    dict(x=2.8, col='#37b26c', rel=Key([(0, 25), (40, 95)], 'lin')),
]
oncoming = [dict(x=-2.8, col='#f2a541', z0=160, v=9), dict(x=-2.8, col='#c9c9d6', z0=330, v=9),
            dict(x=-2.8, col='#7a4fd0', z0=60, v=9)]
trams = [dict(x=-0.6, z0=40, v=8), dict(x=-0.6, z0=260, v=8)]
peds = [dict(x=8.2, z0=20, v=1.1, top='#56b38a'), dict(x=8.3, z0=55, v=-1.0, top='#f2c230', hair='#c7782e'),
        dict(x=8.4, z0=95, v=1.2, top='#9a6fd0', skin='#8d5a3b', hair='#1b1b1b'), dict(x=-8.0, z0=30, v=-1.1, top='#3a7bd5'),
        dict(x=-7.8, z0=80, v=1.0, top='#e05d5d', hair='#6b4a2f'), dict(x=8.0, z0=140, v=-1.1, top='#2f6f73'),
        dict(x=-8.2, z0=125, v=1.2, top='#f4f4f6', skin='#c58c6b')]
world = BikeWorld(34, speed, lat, arm, cars, peds, [], oncoming, trams)

# put the zebra crossing just ahead of where the bike stops (front wheel ~0.9 m ahead of the rider)
Z_STOP = world.ego_z(27.0)
euro.ZC0, euro.ZC1 = Z_STOP + 2.3, Z_STOP + 6.3
world.crossers = [
    dict(z=euro.ZC0 + 1.5, top='#e05d5d', x=Key([(0, 8.2), (26.0, 8.2), (33.4, -2.2)], 'lin'),
         walking=lambda t: 26.0 <= t < 33.4, wave=lambda t: 1.0 if 28.2 <= t < 29.0 else 0.0),
    dict(z=euro.ZC0 + 2.4, top='#3a7bd5', pants='#c46a3c', kid=True, x=Key([(0, 8.8), (26.3, 8.8), (33.4, -1.1)], 'lin'),
         walking=lambda t: 26.3 <= t < 33.4),
]
cars[1]['rel'] = Key([(0, -80), (16.2, -42), (17.8, -36), (21.9, -22), (26, -6), (27, Z_STOP - 0.5 - world.ego_z(27)),
                      (40, Z_STOP - 0.5 - world.ego_z(27))])
# keep car 2 stopped in front of the crossing even after we pull away
_c2 = cars[1]['rel']
cars[1]['rel'] = lambda t, f=_c2: (f(t) if t < 27 else (Z_STOP - 0.5) - world.ego_z(t))


# ------------------------------------------------------------- cameras
def cam(name, t):
    ex, ez = world.ego_xz(t)
    h = world.heading(t)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = math.cos(h), -math.sin(h)
    if name == 'chase':
        return TCam((ex - fx * 4.8, 2.5, ez - fz * 4.8), h, 0.24, 1000, cy=520)
    if name == 'close_left':
        return TCam((ex - fx * 2.7 - rx * 1.3, 1.45, ez - fz * 2.7 - rz * 1.3), h + 0.32, 0.03, 1050)
    if name == 'close_right':
        return TCam((ex - fx * 2.7 + rx * 1.3, 1.45, ez - fz * 2.7 + rz * 1.3), h - 0.32, 0.03, 1050)
    if name == 'pov':
        return TCam((ex, 1.55, ez + 0.2), h, 0.14, 950, cy=470)
    if name == 'shoulder':
        return TCam((ex - 0.1, 1.6, ez), h - 2.45, 0.1, 800, cx=980)
    if name == 'wide':
        return TCam((ex - fx * 12 - rx * 3.5, 8.0, ez - fz * 12 - rz * 3.5), h + 0.18, 0.42, 1000, cy=480)
    raise ValueError(name)


def hud(ctx, t):
    kmh = world.speed(t) * 3.6
    rrect(ctx, 1580, 900, 290, 130, 34)
    setc(ctx, (0, 0, 0), 0.5)
    ctx.fill()
    text_center(ctx, f"{int(round(kmh))}", 1680, 990, 84, (1, 1, 1))
    text_center(ctx, 'km/h', 1800, 990, 34, (0.85, 0.85, 0.9))


def handlebars(ctx, t, armstate):
    """Rider's own handlebars, hands and front wheel (POV)."""
    ctx.move_to(960, SH + 20)
    ctx.line_to(960, 960)
    setc(ctx, hexc('#2a6f97'))
    ctx.set_line_width(46)
    ctx.stroke()
    ellipse(ctx, 960, SH + 120, 70, 230)
    fill_stroke(ctx, hexc('#1c1c22'), OUTL, 5)
    ctx.move_to(420, 990)
    ctx.curve_to(620, 930, 1300, 930, 1500, 990)
    for col, w in ((OUTL, 40), (hexc('#3a3d48'), 28)):
        setc(ctx, col)
        ctx.set_line_width(w)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke_preserve()
    ctx.new_path()
    rrect(ctx, 905, 925, 110, 50, 16)
    fill_stroke(ctx, hexc('#fff6d8'), OUTL, 4)
    ellipse(ctx, 1290, 935, 34, 24)
    fill_stroke(ctx, hexc('#c9ccd6'), OUTL, 4)
    for side, gx in (('left', 470), ('right', 1450)):
        if armstate == side:
            sgn = -1 if side == 'left' else 1
            hose(ctx, (gx + sgn * 120, SH + 40), (gx + sgn * 600, 760), sgn * 40, 120, JACKET)
            continue
        rrect(ctx, gx - 60, 960, 120, 56, 20)
        setc(ctx, OUTL)
        ctx.fill()
        hose(ctx, (gx + (-150 if side == 'left' else 150), SH + 60), (gx, 1000), 30, 120, JACKET)
        ellipse(ctx, gx, 985, 80, 52)
        fill_stroke(ctx, SKIN, OUTL, 5)


def shoulder_frame(ctx):
    ctx.move_to(1350, SH + 10)
    ctx.curve_to(1420, 820, 1700, 760, SW + 10, 780)
    ctx.line_to(SW + 10, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    ctx.move_to(1560, SH + 10)
    ctx.curve_to(1600, 900, 1700, 820, 1800, 790)
    setc(ctx, C_PACK)
    ctx.set_line_width(40)
    ctx.stroke()
    ctx.move_to(-10, -10)
    ctx.curve_to(400, 40, 1500, 40, SW + 10, -10)
    ctx.line_to(SW + 10, -40)
    ctx.line_to(-10, -40)
    ctx.close_path()
    fill_stroke(ctx, C_HELMET, OUTL, 6)


def bike_cam(ctx, w, t, lt, kw):
    v = cam(kw['cam'], t)
    draw_city(ctx, v, world, t, ego=kw['cam'] not in ('pov', 'shoulder'))
    if kw['cam'] == 'pov':
        handlebars(ctx, t, world.arm(t))
    if kw['cam'] == 'shoulder':
        shoulder_frame(ctx)
    if kw.get('hud'):
        hud(ctx, t)


def plan_overlay(ctx, view):
    """Top view: planned path around the van (dashed green), drawn on the ground."""
    pts = []
    for zz in np.arange(world.ego_z(17.0), world.ego_z(23.0), 0.5):
        tt = float(np.interp(zz, world._z, world._g))
        pts.append(view.pt((BIKE_X + lat(tt), 0, zz)))
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    setc(ctx, hexc('#22c35e'))
    ctx.set_line_width(10)
    ctx.set_dash([20, 14])
    ctx.stroke()
    ctx.set_dash([])


def bike_top(ctx, w, t, lt, kw):
    view = TopView(world.ego_z(t), xc=-1.0, s=kw.get('scale', 19.0), ox=330)
    draw_city(ctx, view, world, t, top_overlay=plan_overlay if kw.get('plan') else None)
    if kw.get('plan'):
        a = smooth(lt / 0.3)
        c = view.pt((BIKE_X, 0, (euro.ZV0 + euro.ZV1) / 2))
        ellipse(ctx, c[0], c[1] - 70, 40 * a, 40 * a)
        fill_stroke(ctx, hexc('#e0393e'), OUTL, 4)
        ctx.move_to(c[0] - 15, c[1] - 85)
        ctx.line_to(c[0] + 15, c[1] - 55)
        ctx.move_to(c[0] + 15, c[1] - 85)
        ctx.line_to(c[0] - 15, c[1] - 55)
        setc(ctx, (1, 1, 1), a)
        ctx.set_line_width(7)
        ctx.stroke()
        text_center(ctx, 'Blocked', c[0], c[1] - 125, 42, hexc('#e0393e'), a=a)


engine.SCENES.update(bike_cam=bike_cam, bike_top=bike_top)

shots = [
    Shot(3.2, 'bike_cam', cam='chase', hud=True),          # 0  establishing
    Shot(2.8, 'bike_cam', cam='pov', hud=True),            # 1  STEP 1 stay in the bike lane
    Shot(3.0, 'bike_top', plan=True),                      # 2  STEP 2 blocked ahead, plan early
    Shot(2.2, 'bike_cam', cam='shoulder'),                 # 3  STEP 3 look back
    Shot(2.4, 'bike_cam', cam='chase', hud=True),          # 4  STEP 3 car coming, let it pass
    Shot(2.6, 'bike_cam', cam='close_left'),               # 5  STEP 4 signal left
    Shot(1.6, 'bike_cam', cam='shoulder'),                 # 6  STEP 5 check again: clear
    Shot(3.0, 'bike_top', plan=True),                      # 7  STEP 6 move out smoothly
    Shot(2.6, 'bike_cam', cam='close_right'),              # 8  STEP 7 signal right, back in
    Shot(2.6, 'bike_cam', cam='pov', hud=True),            # 9  STEP 8 people at the crossing
    Shot(4.4, 'bike_cam', cam='chase', hud=True),          # 10 STEP 8 stop & let them cross
    Shot(3.0, 'bike_cam', cam='wide'),                     # 11 recap
]
video = Video(['Cycling in the city:', 'signals, lanes & crossings'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.3, E[0] - 0.2, location_tag('Amsterdam, NL')),
    (S[1], E[1], step_badge(1)), (S[1] + 0.2, E[1], caption_in_scene('Stay in the bike lane')),
    (S[2], E[2], step_badge(2)), (S[2] + 0.2, E[2], caption_in_scene('Blocked ahead? Plan early')),
    (S[3], E[4], step_badge(3)), (S[3] + 0.2, E[3], caption_in_scene('Look back over your shoulder')),
    (S[4] + 0.1, E[4], caption_in_scene('Car coming? Let it pass')),
    (S[5], E[5], step_badge(4)), (S[5] + 0.2, E[5], caption_in_scene('Signal left: arm out')),
    (S[6], E[6], step_badge(5)), (S[6] + 0.2, E[6], caption_in_scene('Look again: clear')),
    (S[7], E[7], step_badge(6)), (S[7] + 0.2, E[7], caption_in_scene('Move out smoothly')),
    (S[8], E[8], step_badge(7)), (S[8] + 0.2, E[8], caption_in_scene('Signal right, back in the bike lane')),
    (S[9], E[10], step_badge(8)), (S[9] + 0.2, E[9], caption_in_scene('People at the crossing? Slow down')),
    (S[10] + 0.1, E[10], caption_in_scene('Stop & let them cross')),
    (S[11] + 0.2, E[11], caption_in_scene('Look. Signal. Move. Yield.')),
]


def city_ambience(d):
    t = np.arange(int(d * SR)) / SR
    return lp(noise(len(t)), 300) * 0.35 + bp(noise(len(t)), 400, 2000) * 0.03


def bike_bell():
    out = np.zeros(int(1.0 * SR))
    for o in (0.0, 0.18):
        tt = np.arange(int(0.6 * SR)) / SR
        s = sum(a * np.sin(2 * np.pi * f * tt) for f, a in ((2350, 1.0), (3120, 0.5), (4700, 0.25)))
        place(out, s * np.exp(-tt / 0.25) * (1 + 0.3 * np.sin(2 * np.pi * 28 * tt)) * 0.3, o)
    return out


def tram_bell():
    out = np.zeros(int(1.2 * SR))
    for o in (0.0, 0.3):
        place(out, bell(midi(76), 0.8) * 1.2, o)
    return out


def freewheel(d):
    out = np.zeros(int(d * SR) + SR)
    tt = 0.0
    while tt < d:
        n = int(0.006 * SR)
        place(out, bp(noise(n), 3000, 8000) * np.exp(-np.arange(n) / SR / 0.0015) * 0.35, tt)
        tt += 0.045
    return out[:int(d * SR)]


def bike_brake():
    t = np.arange(int(0.7 * SR)) / SR
    return np.sin(2 * np.pi * (3200 + 80 * np.sin(2 * np.pi * 9 * t)) * t) * env_adsr(len(t), 0.03, 0.2) * 0.18


def sound():
    m = Mixer(video.dur)
    m.add(city_ambience(video.dur), 0, 0.35)
    m.add(bike_bell(), 0.5, 1.0, 0.1)
    m.add(tram_bell(), 1.3, 0.8, -0.4)
    m.add(rumble(3.0), 1.6, 1.0, -0.4)
    m.add(freewheel(1.0), 9.0, 0.8)
    for i in (1, 2, 3, 5, 6, 7, 8, 9):
        m.add(pop(), S[i] + 0.2, 0.5)
    m.add(head_swish(), S[3] + 0.05, 1.0, -0.5)
    m.add(car_pass(2.4, 0.45, 105), 11.0, 1.0, np.linspace(-0.6, 0.2, int(2.4 * SR)))
    m.add(whoosh(0.4, 0.4), 13.8, 0.6, -0.4)
    m.add(head_swish(), S[6] + 0.05, 1.0, -0.5)
    m.add(bell(midi(84), 0.6), S[6] + 0.6, 0.7)
    m.add(whoosh(0.4, 0.4), 20.8, 0.6, 0.4)
    m.add(freewheel(1.4), 24.6, 0.8)
    m.add(bike_brake(), 25.0, 0.45)
    tt = 26.0
    while tt < 33.4:
        m.add(footsteps(0.12, 100), tt, 0.15, 0.3)
        tt += 0.36
    m.add(sparkle(), 28.3, 0.9, 0.3)
    m.add(success_jingle(), S[11] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'bike.mp4')
