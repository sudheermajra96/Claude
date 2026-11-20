"""Detailed vehicles for the 2D+3D house style: ROUND 3D tyres (tread band + sidewall + rim + nuts),
a detailed conventional tractor (grille, bumper, headlights, visor, marker lights, tanks, steps, stacks,
mirrors, mud flaps) and a 53 ft trailer (skirts, reflective tape, door hardware, lights, landing gear)."""
import math

from toronto import TCam, fill_poly, lbox, L, face_rect
from kit import *

TYRE = hexc('#1d1d24')
TREAD = hexc('#2b2b33')
RIM = hexc('#d4d8e0')


def wheel3(ctx, view, c, h, r, w, rim_col=RIM, dual=False):
    """Round wheel. c = centre (world), h = vehicle heading (axle is the vehicle's left-right axis)."""
    ax = (math.cos(h), 0.0, -math.sin(h))            # axle direction (vehicle right)
    fw = (math.sin(h), 0.0, math.cos(h))
    n = 22
    ring = [(math.cos(a), math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]

    def pt(u, v, off):
        return (c[0] + fw[0] * u * r + ax[0] * off, c[1] + v * r, c[2] + fw[2] * u * r + ax[2] * off)
    cam = view.pos
    side = 1 if (cam[0] - c[0]) * ax[0] + (cam[2] - c[2]) * ax[2] > 0 else -1
    near, far = side * w / 2, -side * w / 2
    fill_poly(ctx, view, [pt(u, v, far) for u, v in ring], TYRE, OUTL, 2)
    quads = []
    for i in range(n):
        u0, v0 = ring[i]
        u1, v1 = ring[(i + 1) % n]
        q = [pt(u0, v0, far), pt(u1, v1, far), pt(u1, v1, near), pt(u0, v0, near)]
        d = view.depth(((q[0][0] + q[2][0]) / 2, (q[0][1] + q[2][1]) / 2, (q[0][2] + q[2][2]) / 2))
        quads.append((d, q, i))
    for d, q, i in sorted(quads, key=lambda it: -it[0]):
        fill_poly(ctx, view, q, TREAD if i % 2 else TYRE)
    fill_poly(ctx, view, [pt(u, v, near) for u, v in ring], TYRE, OUTL, 2)
    fill_poly(ctx, view, [pt(u * 0.62, v * 0.62, near * 1.01) for u, v in ring], rim_col, OUTL, 1.5)
    if dual:
        fill_poly(ctx, view, [pt(u * 0.5, v * 0.5, near * 1.02) for u, v in ring], mix(rim_col, (0, 0, 0), 0.25))
    fill_poly(ctx, view, [pt(u * 0.22, v * 0.22, near * 1.03) for u, v in ring], mix(rim_col, (0, 0, 0), 0.4))
    s = view.scale(c)
    if s and r * s > 14:
        for k in range(6):
            a = k / 6 * 2 * math.pi
            p = view.pt(pt(math.cos(a) * 0.36, math.sin(a) * 0.36, near * 1.04))
            if p:
                ellipse(ctx, p[0], p[1], max(1.5, r * s * 0.05), max(1.5, r * s * 0.05))
                setc(ctx, hexc('#8a8f9c'))
                ctx.fill()


def near_side(view, x, z, h):
    ax = (math.cos(h), -math.sin(h))
    return 1 if (view.pos[0] - x) * ax[0] + (view.pos[2] - z) * ax[1] > 0 else -1


def wheels_split(view, Lf, h, x, z, specs):
    """specs: [(lx, lz, r, w, dual)] -> (far_draws, near_draws)."""
    ns = near_side(view, x, z, h)
    far, near = [], []
    for lx, lz, r, w, dual in specs:
        c = Lf(lx, r, lz)
        fn = (lambda c=c, r=r, w=w, dual=dual: lambda ctx: wheel3(ctx, view, c, h, r, w, dual=dual))()
        (near if (lx > 0) == (ns > 0) else far).append(fn)
    return far, near


# ------------------------------------------------------------------ tractor
CAB_RED = '#c8312f'


def tractor_det(ctx, view, x, z, h, col=CAB_RED, haz=False, blink=None, brake=False):
    """Tractor; origin = rear drive axle (fifth wheel), +z forward."""
    Lf = L(x, z, h)
    d = view.depth((x, 1.5, z))
    lw = max(1.4, min(4, 60 / max(d, 1)))
    red = hexc(col)
    red_d = mix(red, (0, 0, 0), 0.22)
    chrome, black, glass, dark = hexc('#dfe3ea'), hexc('#1c1c22'), hexc('#2a3448'), hexc('#3a3d48')
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    far, near = wheels_split(view, Lf, h, x, z, [(sx * 0.98, wz, 0.52, 0.62, True) for wz in (-1.32, 0.0) for sx in (-1, 1)] +
                             [(sx * 1.02, 4.0, 0.52, 0.36, False) for sx in (-1, 1)])
    for f in far:
        f(ctx)
    lbox(ctx, view, Lf, h, -0.48, 0.48, 0.62, 0.98, -2.1, 5.7, allc(dark), lw)                     # frame rails
    lbox(ctx, view, Lf, h, -1.0, 1.0, 1.0, 1.12, -1.1, 0.9, allc(hexc('#2a2c33')), lw)              # fifth wheel
    for sx in (-1, 1):
        lbox(ctx, view, Lf, h, sx * 1.22 - 0.3, sx * 1.22 + 0.3, 0.55, 1.15, 0.9, 2.6, allc(chrome), lw)      # fuel tanks
        lbox(ctx, view, Lf, h, sx * 1.22 - 0.32, sx * 1.22 + 0.32, 0.5, 0.58, 1.1, 2.4, allc(dark), lw)       # step
        lbox(ctx, view, Lf, h, sx * 1.05 - 0.25, sx * 1.05 + 0.25, 1.05, 1.2, -1.95, 0.75, allc(red_d), lw)   # rear fenders
        lbox(ctx, view, Lf, h, sx * 1.0 - 0.28, sx * 1.0 + 0.28, 0.25, 0.85, -2.05, -1.98, allc(black), lw)   # mud flaps
    # sleeper + cab + hood
    lbox(ctx, view, Lf, h, -1.25, 1.25, 1.15, 3.75, 0.05, 1.65, {'front': red_d, 'back': red_d, 'left': red, 'right': red, 'top': red}, lw)
    vis = lbox(ctx, view, Lf, h, -1.25, 1.25, 1.15, 3.35, 1.65, 3.6, {'front': red, 'back': red, 'left': red, 'right': red, 'top': red}, lw)
    hv = lbox(ctx, view, Lf, h, -0.98, 0.98, 1.05, 2.3, 3.6, 5.85, {'front': chrome, 'back': red, 'left': red_d, 'right': red_d, 'top': red}, lw)
    for sx in (-1, 1):
        lbox(ctx, view, Lf, h, sx * 1.1 - 0.22, sx * 1.1 + 0.22, 1.0, 1.6, 3.9, 5.3, allc(red_d), lw)  # front fenders
    if 'front' in vis:
        face_rect(ctx, view, Lf, 'front', -1.12, 1.12, 2.4, 3.22, 3.61, glass)
        face_rect(ctx, view, Lf, 'front', -0.03, 0.03, 2.4, 3.22, 3.62, red)
        face_rect(ctx, view, Lf, 'front', -1.2, 1.2, 3.22, 3.35, 3.63, dark)                         # visor
        for k in range(5):
            face_rect(ctx, view, Lf, 'front', -0.9 + k * 0.45 - 0.07, -0.9 + k * 0.45 + 0.07, 3.36, 3.44, 3.6, AMBER,
                      AMBER, 0.25)                                                                    # cab marker lights
    for face, dx in (('left', -1.26), ('right', 1.26)):
        if face in vis:
            face_rect(ctx, view, Lf, face, 1.9, 3.4, 2.2, 3.15, dx, glass)
            face_rect(ctx, view, Lf, face, 1.85, 3.45, 1.25, 2.05, dx, mix(red, (1, 1, 1), 0.12))
    if 'front' in hv:
        for k in range(9):
            face_rect(ctx, view, Lf, 'front', -0.75 + k * 0.19 - 0.04, -0.75 + k * 0.19 + 0.04, 1.25, 2.15, 5.86, hexc('#9aa0aa'))
        for sx in (-1, 1):
            face_rect(ctx, view, Lf, 'front', sx * 0.92 - 0.2, sx * 0.92 + 0.2, 1.5, 1.75, 5.87, hexc('#fff6d8'), WHITE_L, 0.6)
            on = haz or blink == ('L' if sx < 0 else 'R')
            face_rect(ctx, view, Lf, 'front', sx * 0.92 - 0.2, sx * 0.92 + 0.2, 1.38, 1.48, 5.87,
                      AMBER if on else hexc('#7a4a00'), AMBER if on else None, 1.0)
    lbox(ctx, view, Lf, h, -1.3, 1.3, 0.75, 1.1, 5.85, 6.15, allc(chrome), lw)                     # bumper
    for sx in (-1, 1):
        lbox(ctx, view, Lf, h, sx * 1.3 - 0.09, sx * 1.3 + 0.09, 2.5, 4.55, 1.45, 1.63, allc(chrome), lw)   # stacks
        lbox(ctx, view, Lf, h, sx * 1.62 - 0.07, sx * 1.62 + 0.07, 2.15, 3.15, 3.35, 3.47, allc(black), lw)  # west-coast mirrors
        lbox(ctx, view, Lf, h, sx * 1.4 - 0.22, sx * 1.62, 2.6, 2.66, 3.4, 3.44, allc(dark), lw)
        lbox(ctx, view, Lf, h, sx * 1.2 - 0.1, sx * 1.2 + 0.1, 1.95, 2.05, 5.6, 5.75, allc(black), lw)        # hood mirrors
    for f in near:
        f(ctx)


def trailer_det(ctx, view, x, z, h, haz=False, rev=False, brake=False, col='#f4f4f6', stripe='#2f6f9f', logo='NORTHLINE'):
    """53 ft trailer; origin = kingpin, +z forward; axles at -12.3/-11.0."""
    Lf = L(x, z, h)
    d = view.depth((x - math.sin(h) * 7, 2, z - math.cos(h) * 7))
    lw = max(1.4, min(4, 80 / max(d, 1)))
    white = hexc(col)
    allc = lambda c: {k: c for k in ('front', 'back', 'left', 'right', 'top')}
    far, near = wheels_split(view, Lf, h, x, z, [(sx * 0.98, wz, 0.52, 0.62, True) for wz in (-12.3, -11.0) for sx in (-1, 1)])
    for f in far:
        f(ctx)
    for sx in (-1, 1):
        lbox(ctx, view, Lf, h, sx * 0.9 - 0.07, sx * 0.9 + 0.07, 0.25, 1.2, -2.6, -2.45, allc(hexc('#3a3d48')), lw)   # landing gear
    lbox(ctx, view, Lf, h, -1.2, 1.2, 0.45, 0.62, -15.36, -15.02, allc(hexc('#d62828')), lw)                         # ICC bar
    vis = lbox(ctx, view, Lf, h, -1.3, 1.3, 1.22, 4.1, -15.3, 0.9,
               {'front': mix(white, (0, 0, 0), 0.05), 'back': mix(white, (0, 0, 0), 0.06), 'left': mix(white, (0, 0, 0), 0.08),
                'right': mix(white, (0, 0, 0), 0.03), 'top': white}, lw)
    for face, dx in (('left', -1.31), ('right', 1.31)):
        if face in vis:
            face_rect(ctx, view, Lf, face, -9.6, -3.0, 0.6, 1.22, dx * 0.985, hexc('#c9ccd6'))                          # side skirt
            for k in range(12):                                                                                       # reflective tape
                face_rect(ctx, view, Lf, face, -15.0 + k * 1.3, -14.6 + k * 1.3, 1.3, 1.45, dx, hexc('#e0393e') if k % 2 else (1, 1, 1))
            face_rect(ctx, view, Lf, face, -14.5, 0.2, 3.85, 3.95, dx, hexc(stripe))
            face_rect(ctx, view, Lf, face, -11.6, -2.4, 2.1, 3.3, dx, hexc(stripe))
            p = view.pt(Lf(dx, 2.7, -7.0))
            s = view.scale(Lf(dx, 2.7, -7.0))
            if p and s and s * 0.7 > 9:
                ang = math.atan2(*(lambda a, b: (b[1] - a[1], b[0] - a[0]))(view.pt(Lf(dx, 2.7, -9.0)) or p, view.pt(Lf(dx, 2.7, -5.0)) or p))
                ctx.save()
                ctx.translate(*p)
                if face == 'left':
                    ang += math.pi
                ctx.rotate(ang)
                text_center(ctx, logo, 0, s * 0.25, s * 0.7, (1, 1, 1))
                ctx.restore()
    if 'back' in vis:
        face_rect(ctx, view, Lf, 'back', -0.025, 0.025, 1.3, 4.02, -15.31, OUTL)
        for s_ in (-1, 1):
            for yy in (1.6, 2.6, 3.6):
                face_rect(ctx, view, Lf, 'back', s_ * 0.55 - 0.03, s_ * 0.55 + 0.03, yy - 0.5, yy + 0.4, -15.32, hexc('#9aa0aa'))
            face_rect(ctx, view, Lf, 'back', s_ * 1.08 - 0.12, s_ * 1.08 + 0.12, 1.3, 1.6, -15.33,
                      hexc('#ff4040') if brake else hexc('#b01818'), RED if brake else None, 1.4)
            face_rect(ctx, view, Lf, 'back', s_ * 1.08 - 0.1, s_ * 1.08 + 0.1, 1.65, 1.85, -15.33,
                      AMBER if haz else hexc('#7a4a00'), AMBER if haz else None, 1.6)
            if rev:
                face_rect(ctx, view, Lf, 'back', s_ * 0.8 - 0.1, s_ * 0.8 + 0.1, 1.32, 1.5, -15.33, (1, 1, 1), WHITE_L, 1.2)
        for k in range(8):
            face_rect(ctx, view, Lf, 'back', -1.25 + k * 0.32, -1.1 + k * 0.32, 1.24, 1.32, -15.32, hexc('#e0393e') if k % 2 else (1, 1, 1))
    for f in near:
        f(ctx)


def draw_car_round(ctx, view, x, z, h, col, t, blink=None, brake=0.0, rev=False, lw=None, kind='car'):
    """Passenger car with round tyres (replacement for citykit.draw_car_g)."""
    Lf = L(x, z, h)
    body = hexc(col)
    dark = mix(body, (0, 0, 0), 0.3)
    glass = hexc('#2a3448')
    d = view.depth((x, 0.8, z))
    lw = lw or max(1.5, min(4.5, 60 / max(d, 1)))
    far, near = wheels_split(view, Lf, h, x, z, [(sx * 0.8, wz, 0.34, 0.24, False) for wz in (-1.38, 1.38) for sx in (-1, 1)])
    for f in far:
        f(ctx)
    vis = lbox(ctx, view, Lf, h, -0.92, 0.92, 0.36, 0.9, -2.2, 2.2, {'front': body, 'back': body, 'left': dark, 'right': dark, 'top': body}, lw)
    lbox(ctx, view, Lf, h, -0.78, 0.78, 0.9, 1.42, -1.25, 0.95, {'front': glass, 'back': glass, 'left': glass, 'right': glass, 'top': body}, lw)
    amb, off = AMBER, hexc('#7a4a00')
    sg = {'L': -1, 'R': 1}.get(blink)
    if 'back' in vis:
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'back', s * 0.62 - 0.2, s * 0.62 + 0.2, 0.64, 0.8, -2.21,
                      hexc('#ff4040') if brake > 0.5 else hexc('#b01818'), RED if brake > 0.5 else None, 1.2)
            face_rect(ctx, view, Lf, 'back', s * 0.8 - 0.1, s * 0.8 + 0.1, 0.62, 0.82, -2.22, amb if sg == s else off, amb if sg == s else None, 1.4)
        face_rect(ctx, view, Lf, 'back', -0.25, 0.25, 0.44, 0.58, -2.21, hexc('#e8e8ee'))
    if 'front' in vis:
        for s in (-1, 1):
            face_rect(ctx, view, Lf, 'front', s * 0.6 - 0.22, s * 0.6 + 0.22, 0.62, 0.78, 2.21, hexc('#fff6d8'), WHITE_L, 0.5)
        face_rect(ctx, view, Lf, 'front', -0.35, 0.35, 0.45, 0.58, 2.21, hexc('#2a2c33'))
    for face, s in (('left', -1), ('right', 1)):
        if face in vis:
            face_rect(ctx, view, Lf, face, -1.0, 0.85, 0.5, 0.52, s * 0.93, mix(body, (0, 0, 0), 0.45))
    for f in near:
        f(ctx)
