"""Daylight suburban street POV (2D, signal/distance house style): intersection with a STOP sign,
houses, trees, cross traffic, police car, officer, ticket. Plus siren / paper / whistle SFX."""
from psych import *          # engine + life + psych SFX (sad_violin, success_jingle, ...)
from psych import _t
import engine

TICKET_TEXT = 'Ran a STOP sign'
ZL = 200.0                 # world z of the stop line
ZI = ZL + 10.5             # intersection centre
DRIVER_X = 1.3             # driver position in the right lane
GRASS = hexc('#7cc46a')
ASPH = hexc('#5d6170')
SIDEWALK = hexc('#d9d4c8')
CURB = hexc('#b9b3a6')
HOUSE_COLS = ['#f2d0a4', '#cfe3f2', '#f4b6a6', '#e9e3b8', '#c9e4c5', '#e6c7e8', '#fde7b0']
ROOF_COLS = ['#a8473a', '#5a6378', '#7b4b3a', '#3f6f8a']


class StreetWorld(World):
    """Ego driving along a street; positions come from piecewise-linear speed keys with resets."""

    def __init__(self, dur, parts, camx, look=None, police_flash=None):
        # parts: list of (t_start, start_line_dist, speed Key)
        self.parts = parts
        self._grid = np.arange(0, dur + 1, 1 / 120)
        ld = np.zeros(len(self._grid))
        for i, t in enumerate(self._grid):
            p = [q for q in parts if q[0] <= t][-1]
            if i == 0 or self._grid[i - 1] < p[0]:
                ld[i] = p[1]
            else:
                ld[i] = ld[i - 1] - p[2](t) / 120
        self._ld = ld
        sp = lambda t: [q for q in parts if q[0] <= t][-1][2](t)
        super().__init__(dur, sp, camx)
        self.look = look or const(0)
        self.police_flash = police_flash or (lambda t: 0.0)

    def line_dist(self, t):
        return float(np.interp(t, self._grid, self._ld))

    def ego_z(self, t):
        return ZL - self.line_dist(t)


# ------------------------------------------------------------------ drawing
def quad(ctx, cam, pts, col, lw=3, stroke=True):
    poly(ctx, [cam.p(*p) for p in pts])
    if stroke:
        fill_stroke(ctx, col, OUTL, lw)
    else:
        setc(ctx, col)
        ctx.fill()


def ground_quad(ctx, cam, x0, x1, z0, z1, col, zn=1.2):
    z0, z1 = max(z0, zn), z1
    if z1 <= z0:
        return
    quad(ctx, cam, [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1)], col, stroke=False)


def house(ctx, cam, x0, x1, z0, z1, h, col, roof, seed):
    lw = max(1.5, min(4, 60 / z0))
    wall = hexc(col)
    box(ctx, cam, x0, x1, 0, h, z0, z1, wall, mix(wall, (0, 0, 0), 0.18), None, lw)
    xm = (x0 + x1) / 2
    rh = h + 2.2
    rc = hexc(roof)
    # gable on the front face + the roof slope that faces the road
    quad(ctx, cam, [(x0 - .3, h, z0 - .3), (x1 + .3, h, z0 - .3), (xm, rh, z0 - .3)], wall, lw)
    if x0 > cam.camx:
        quad(ctx, cam, [(x0 - .3, h, z0 - .3), (xm, rh, z0 - .3), (xm, rh, z1 + .3), (x0 - .3, h, z1 + .3)], rc, lw)
        fx = x0
    else:
        quad(ctx, cam, [(x1 + .3, h, z0 - .3), (xm, rh, z0 - .3), (xm, rh, z1 + .3), (x1 + .3, h, z1 + .3)], rc, lw)
        fx = x1
    # windows + door on the side facing the road
    for zz in (z0 + 1.5, z1 - 3.0):
        quad(ctx, cam, [(fx, 1.4, zz), (fx, 1.4, zz + 1.5), (fx, 2.6, zz + 1.5), (fx, 2.6, zz)], hexc('#8fc6ee'), lw * 0.7)
    zd = (z0 + z1) / 2 - 0.6
    quad(ctx, cam, [(fx, 0, zd), (fx, 0, zd + 1.1), (fx, 2.1, zd + 1.1), (fx, 2.1, zd)], hexc('#7b4b3a'), lw * 0.7)


def tree(ctx, cam, x, z, s=1.0, seed=0):
    bx, by = cam.p(x, 0, z)
    tx, ty = cam.p(x, 3.2 * s, z)
    w = 0.35 * cam.f / z
    ctx.rectangle(bx - w / 2, ty, w, by - ty)
    fill_stroke(ctx, hexc('#7b5434'), OUTL, max(1, 40 / z))
    r = 1.9 * s * cam.f / z
    cols = [hexc('#3f9a4c'), hexc('#58b05a'), hexc('#2f8a45')]
    for i, (dx, dy) in enumerate(((-0.45, 0.1), (0.45, 0.15), (0, -0.4))):
        ellipse(ctx, tx + dx * r, ty + dy * r, r * 0.75, r * 0.7)
        fill_stroke(ctx, cols[(seed + i) % 3], OUTL, max(1, 40 / z))


def stop_sign(ctx, cam, x, z):
    if z < 1.6:
        return
    bx, by = cam.p(x, 0, z)
    sx, sy = cam.p(x, 2.3, z)
    w = 0.08 * cam.f / z
    ctx.rectangle(bx - w / 2, sy, w, by - sy)
    fill_stroke(ctx, hexc('#9aa0aa'), OUTL, max(1, 30 / z))
    r = 0.42 * cam.f / z
    pts = [(sx + math.cos(math.pi / 8 + i * math.pi / 4) * r, sy + math.sin(math.pi / 8 + i * math.pi / 4) * r) for i in range(8)]
    poly(ctx, pts)
    fill_stroke(ctx, (1, 1, 1), OUTL, max(1, 30 / z))
    pts2 = [(sx + math.cos(math.pi / 8 + i * math.pi / 4) * r * 0.86, sy + math.sin(math.pi / 8 + i * math.pi / 4) * r * 0.86) for i in range(8)]
    poly(ctx, pts2)
    setc(ctx, hexc('#d62828'))
    ctx.fill()
    if r > 6:
        text_center(ctx, 'STOP', sx, sy + r * 0.2, r * 0.62, (1, 1, 1))


def car_side(ctx, cam, x, z, col, length=4.4, dirn=1):
    """Car driving along the cross street (we see its side)."""
    lw = max(1.5, min(4, 50 / z))
    body = hexc(col)
    box(ctx, cam, x - length / 2, x + length / 2, 0.3, 0.9, z - 0.9, z + 0.9, body, mix(body, (0, 0, 0), 0.25), body, lw)
    box(ctx, cam, x - length / 2 + 0.9, x + length / 2 - 1.1, 0.9, 1.45, z - 0.8, z + 0.8,
        hexc('#2a3448'), hexc('#2a3448'), body, lw)
    for wx in (x - length / 2 + 0.8, x + length / 2 - 0.8):
        cx_, cy_ = cam.p(wx, 0.33, z - 0.92)
        r = 0.34 * cam.f / z
        ellipse(ctx, cx_, cy_, r, r)
        fill_stroke(ctx, hexc('#1c1c22'), OUTL, lw)


def police_lightbar(ctx, cam, x, y, z, t, w=1.2, bright=1.0):
    ph = (t * 4) % 1 < 0.5
    for s, col in ((-1, hexc('#ff2a2a')), (1, hexc('#2a6bff'))):
        on = ph if s < 0 else not ph
        cx_, cy_ = cam.p(x + s * w * 0.3, y, z)
        r = 0.22 * cam.f / z
        rrect(ctx, cx_ - r, cy_ - r * 0.5, r * 2, r, r * 0.3)
        fill_stroke(ctx, col if on else mix(col, (0, 0, 0), 0.5), OUTL, max(1, 30 / z))
        if on:
            glow(ctx, cx_, cy_, min(2.4 * cam.f / z, 900) * bright, col, 0.8 * bright)


def police_car_front(ctx, cam, x, z, t, lights=True):
    lw = max(1.5, min(4, 50 / z))
    white, black = hexc('#f4f4f6'), hexc('#1c1d26')
    box(ctx, cam, x - 0.92, x + 0.92, 0.22, 0.86, z, z + 4.6, black, black, white, lw)
    box(ctx, cam, x - 0.92, x + 0.92, 0.56, 0.86, z - 0.02, z + 4.6, white, white, white, lw)
    box(ctx, cam, x - 0.76, x + 0.76, 0.86, 1.42, z + 1.2, z + 3.1, hexc('#2a3448'), hexc('#2a3448'), white, lw)
    for s in (-1, 1):
        cx_, cy_ = cam.p(x + s * 0.62, 0.66, z - 0.03)
        rr = 0.14 * cam.f / z
        ellipse(ctx, cx_, cy_, rr * 1.3, rr * 0.8)
        setc(ctx, (1, 1, 0.92))
        ctx.fill()
    if lights:
        police_lightbar(ctx, cam, x, 1.55, z + 1.6, t)


def officer(ctx, x, y, k, t, pose='write', lt=0.0, expr='flat'):
    """Original police officer: navy uniform, cap, aviators, moustache. (x, y) = chest centre."""
    navy, navy_d = hexc('#1f3a6b'), hexc('#16294d')
    skin = hexc('#c98d63')
    # torso
    ctx.move_to(x - 230 * k, y + 400 * k)
    ctx.curve_to(x - 240 * k, y - 60 * k, x - 170 * k, y - 140 * k, x, y - 145 * k)
    ctx.curve_to(x + 170 * k, y - 140 * k, x + 240 * k, y - 60 * k, x + 230 * k, y + 400 * k)
    ctx.close_path()
    fill_stroke(ctx, navy, OUTL, 6)
    poly(ctx, [(x - 55 * k, y - 145 * k), (x + 55 * k, y - 145 * k), (x, y - 70 * k)])
    fill_stroke(ctx, hexc('#e8e8ee'), OUTL, 4)
    ctx.move_to(x, y - 70 * k)
    ctx.line_to(x, y + 400 * k)
    setc(ctx, navy_d)
    ctx.set_line_width(5)
    ctx.stroke()
    # star badge
    bx, by, r = x - 110 * k, y - 20 * k, 34 * k
    poly(ctx, [(bx + math.cos(-math.pi / 2 + i * math.pi / 5) * (r if i % 2 == 0 else r * 0.45),
                by + math.sin(-math.pi / 2 + i * math.pi / 5) * (r if i % 2 == 0 else r * 0.45)) for i in range(10)])
    fill_stroke(ctx, hexc('#f2c230'), OUTL, 3)
    rrect(ctx, x + 70 * k, y - 40 * k, 90 * k, 22 * k, 6)
    fill_stroke(ctx, hexc('#c9ccd6'), OUTL, 3)
    # neck + head
    ctx.rectangle(x - 45 * k, y - 210 * k, 90 * k, 80 * k)
    fill_stroke(ctx, mix(skin, (0, 0, 0), 0.15), OUTL, 5)
    hy = y - 330 * k
    for s in (-1, 1):
        ellipse(ctx, x + s * 118 * k, hy + 20 * k, 26 * k, 34 * k)
        fill_stroke(ctx, skin, OUTL, 5)
    ellipse(ctx, x, hy, 125 * k, 140 * k)
    fill_stroke(ctx, skin, OUTL, 6)
    # cap
    ctx.move_to(x - 135 * k, hy - 40 * k)
    ctx.curve_to(x - 140 * k, hy - 190 * k, x + 140 * k, hy - 190 * k, x + 135 * k, hy - 40 * k)
    ctx.close_path()
    fill_stroke(ctx, navy, OUTL, 6)
    ctx.move_to(x - 140 * k, hy - 40 * k)
    ctx.curve_to(x - 60 * k, hy - 5 * k, x + 60 * k, hy - 5 * k, x + 140 * k, hy - 40 * k)
    ctx.curve_to(x + 60 * k, hy - 30 * k, x - 60 * k, hy - 30 * k, x - 140 * k, hy - 40 * k)
    fill_stroke(ctx, hexc('#111118'), OUTL, 5)
    poly(ctx, [(x, hy - 140 * k), (x + 22 * k, hy - 110 * k), (x, hy - 80 * k), (x - 22 * k, hy - 110 * k)])
    fill_stroke(ctx, hexc('#f2c230'), OUTL, 3)
    # aviators
    for s in (-1, 1):
        ctx.move_to(x + s * 12 * k, hy + 5 * k)
        ctx.curve_to(x + s * 20 * k, hy - 10 * k, x + s * 95 * k, hy - 12 * k, x + s * 100 * k, hy + 2 * k)
        ctx.curve_to(x + s * 100 * k, hy + 45 * k, x + s * 30 * k, hy + 55 * k, x + s * 12 * k, hy + 5 * k)
        fill_stroke(ctx, hexc('#1b2030'), OUTL, 4)
        ctx.move_to(x + s * 70 * k, hy + 2 * k)
        ctx.line_to(x + s * 86 * k, hy + 14 * k)
        setc(ctx, (1, 1, 1), 0.6)
        ctx.set_line_width(4)
        ctx.stroke()
    # nose, moustache, mouth
    ctx.move_to(x - 4 * k, hy + 40 * k)
    ctx.curve_to(x - 16 * k, hy + 70 * k, x + 4 * k, hy + 76 * k, x + 14 * k, hy + 66 * k)
    setc(ctx, mix(skin, (0, 0, 0), 0.25))
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.move_to(x - 60 * k, hy + 92 * k)
    ctx.curve_to(x - 30 * k, hy + 70 * k, x + 30 * k, hy + 70 * k, x + 60 * k, hy + 92 * k)
    ctx.curve_to(x + 30 * k, hy + 84 * k, x - 30 * k, hy + 84 * k, x - 60 * k, hy + 92 * k)
    fill_stroke(ctx, hexc('#3a2316'), OUTL, 3)
    if expr == 'smile':
        ctx.arc(x, hy + 80 * k, 38 * k, 0.2 * math.pi, 0.8 * math.pi)
    else:
        ctx.move_to(x - 30 * k, hy + 108 * k)
        ctx.line_to(x + 30 * k, hy + 106 * k)
    setc(ctx, OUTL)
    ctx.set_line_width(6)
    ctx.stroke()
    # arms / props
    if pose == 'write':
        pad = (x - 40 * k, y + 120 * k)
        hose(ctx, (x - 180 * k, y - 80 * k), (pad[0] - 60 * k, pad[1] + 40 * k), 60 * k, 70 * k, navy)
        ctx.save()
        ctx.translate(*pad)
        ctx.rotate(-0.15)
        rrect(ctx, -120 * k, -90 * k, 240 * k, 180 * k, 10)
        fill_stroke(ctx, (1, 1, 1), OUTL, 5)
        ctx.rectangle(-120 * k, -90 * k, 240 * k, 26 * k)
        setc(ctx, hexc('#e0393e'))
        ctx.fill()
        for i in range(4):
            wln = min(1, max(0, (lt - 0.3 - i * 0.35) / 0.35))
            if wln > 0:
                ctx.move_to(-95 * k, (-40 + i * 34) * k)
                for j in range(int(18 * wln)):
                    ctx.line_to((-95 + j * 10) * k, (-40 + i * 34 + (6 if j % 2 else -6)) * k)
                setc(ctx, hexc('#30508a'))
                ctx.set_line_width(3)
                ctx.stroke()
        ctx.restore()
        ellipse(ctx, pad[0] - 70 * k, pad[1] + 40 * k, 34 * k, 30 * k)
        fill_stroke(ctx, skin, OUTL, 4)
        px_ = pad[0] + (-60 + ((lt * 140) % 200)) * k
        py_ = pad[1] + (-30 + 34 * min(3, int(lt / 0.35))) * k + math.sin(lt * 30) * 5 * k
        hose(ctx, (x + 180 * k, y - 80 * k), (px_ + 30 * k, py_ + 30 * k), -60 * k, 70 * k, navy)
        ctx.move_to(px_, py_)
        ctx.line_to(px_ + 50 * k, py_ - 70 * k)
        setc(ctx, hexc('#30508a'))
        ctx.set_line_width(10 * k)
        ctx.stroke()
        ellipse(ctx, px_ + 30 * k, py_ + 30 * k, 34 * k, 30 * k)
        fill_stroke(ctx, skin, OUTL, 4)
    elif pose == 'thumbs':
        up = smooth(lt / 0.35)
        hx_, hy_ = x + 250 * k, y + 80 * k - 260 * k * up
        hose(ctx, (x + 180 * k, y - 80 * k), (hx_, hy_ + 30 * k), -40 * k, 70 * k, navy)
        rrect(ctx, hx_ - 45 * k, hy_ - 10 * k, 90 * k, 80 * k, 20 * k)
        fill_stroke(ctx, skin, OUTL, 5)
        rrect(ctx, hx_ - 18 * k, hy_ - 80 * k, 36 * k, 80 * k, 16 * k)
        fill_stroke(ctx, skin, OUTL, 5)
        hose(ctx, (x - 180 * k, y - 80 * k), (x - 200 * k, y + 300 * k), 20 * k, 70 * k, navy)


def ticket_paper(ctx, cx, cy, s, rot, lt, stamp_t=0.6):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(s, s)
    rrect(ctx, -260, -330, 520, 660, 14)
    fill_stroke(ctx, hexc('#fffdf3'), OUTL, 6)
    ctx.rectangle(-260, -330, 520, 90)
    setc(ctx, hexc('#e0393e'))
    ctx.fill()
    text_center(ctx, 'TRAFFIC TICKET', 0, -268, 52, (1, 1, 1))
    for i in range(3):
        ctx.rectangle(-210, -190 + i * 48, 420 - i * 90, 14)
        setc(ctx, hexc('#c9cbd8'))
        ctx.fill()
    rrect(ctx, -210, -30, 40, 40, 6)
    fill_stroke(ctx, (1, 1, 1), OUTL, 4)
    ctx.move_to(-202, -12)
    ctx.line_to(-190, 2)
    ctx.line_to(-170, -26)
    setc(ctx, hexc('#30508a'))
    ctx.set_line_width(7)
    ctx.stroke()
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(34)
    ctx.move_to(-150, 2)
    setc(ctx, OUTL)
    ctx.show_text(TICKET_TEXT)
    text_center(ctx, 'FINE', -90, 120, 56, OUTL)
    if lt >= stamp_t:
        a = smooth((lt - stamp_t) / 0.12)
        sc = 1 + 0.8 * (1 - a)
        ctx.save()
        ctx.translate(80, 125)
        ctx.rotate(-0.18)
        ctx.scale(sc, sc)
        rrect(ctx, -110, -60, 220, 110, 16)
        setc(ctx, hexc('#d62828'), a)
        ctx.set_line_width(10)
        ctx.stroke()
        text_center(ctx, '$$$', 0, 22, 74, hexc('#d62828'), a=a)
        ctx.restore()
    ctx.move_to(-200, 260)
    for j in range(30):
        ctx.line_to(-200 + j * 9, 260 + (10 if j % 3 == 0 else -6))
    setc(ctx, hexc('#30508a'))
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.restore()


# ------------------------------------------------------------------ scenes
def street_scene(ctx, world, cam, t, kw, rear=False):
    """Everything outside the car. rear=True draws the view behind (for mirrors)."""
    ez = world.ego_z(t)
    sign = -1 if rear else 1
    rel = lambda z: (z - ez) * sign
    draw_sky(ctx, cam.hy, cam.yaw)
    setc(ctx, GRASS)
    ctx.rectangle(-400, cam.hy, SW + 800, SH)
    ctx.fill()
    zn, zf = 1.4, 320
    zi = rel(ZI)
    # cross street band
    za, zb = sorted((zi - 6, zi + 6))
    if zb > zn and za < zf:
        ground_quad(ctx, cam, -400, 400, za, zb, ASPH)
        for zz in (za - 1.6, zb):
            ground_quad(ctx, cam, -400, -3.5 - 2.5, zz, zz + 1.6, SIDEWALK)
            ground_quad(ctx, cam, 3.5 + 2.5, 400, zz, zz + 1.6, SIDEWALK)
        for xx in range(-80, 81, 8):
            if abs(xx) > 5:
                ground_quad(ctx, cam, xx, xx + 3, zi - 0.08, zi + 0.08, hexc('#f2c230'))
    # our road + sidewalks, split around the intersection
    segs = [(zn, za - 1.6), (zb + 1.6, zf)] if zb > zn else [(zn, zf)]
    for z0, z1 in segs:
        if z1 <= max(z0, zn):
            continue
        ground_quad(ctx, cam, -3.5, 3.5, z0, z1, ASPH)
        ground_quad(ctx, cam, 3.5, 6.0, z0, z1, SIDEWALK)
        ground_quad(ctx, cam, -6.0, -3.5, z0, z1, SIDEWALK)
        ground_quad(ctx, cam, 3.5, 3.75, z0, z1, CURB)
        ground_quad(ctx, cam, -3.75, -3.5, z0, z1, CURB)
        ground_quad(ctx, cam, -0.18, -0.06, z0, z1, hexc('#f2c230'))
        ground_quad(ctx, cam, 0.06, 0.18, z0, z1, hexc('#f2c230'))
    ground_quad(ctx, cam, -3.5, 3.5, za - 1.6, za, ASPH)
    ground_quad(ctx, cam, -3.5, 3.5, zb, zb + 1.6, ASPH)
    if not rear:
        # crosswalk + STOP line on our side
        for i in range(7):
            x0 = -3.3 + i * 1.0
            ground_quad(ctx, cam, x0, x0 + 0.55, zi - 9.6, zi - 6.6, (0.97, 0.97, 0.97))
        ground_quad(ctx, cam, 0.15, 3.5, rel(ZL) - 0.3, rel(ZL) + 0.3, (1, 1, 1))
        if rel(ZL) - 0.3 > zn:
            pass
    # depth-sorted objects
    items = []
    for side in (-1, 1):
        for i, zz in enumerate(np.arange(-160, 1600, 17)):
            if abs(zz - ZI) < 16:
                continue
            z0 = rel(zz)
            if rear:
                z0 = rel(zz + 10)
            if 2.0 < z0 < zf:
                col = HOUSE_COLS[(i + (side > 0) * 3) % len(HOUSE_COLS)]
                roof = ROOF_COLS[(i * 3 + (side > 0)) % len(ROOF_COLS)]
                x0, x1 = (9, 17) if side > 0 else (-17, -9)
                items.append((z0, lambda z0=z0, x0=x0, x1=x1, col=col, roof=roof, i=i:
                              house(ctx, cam, x0, x1, z0, z0 + 10, 4.2 + (i % 3) * 0.6, col, roof, i)))
        for i, zz in enumerate(np.arange(-150, 1600, 13)):
            if abs(zz - ZI) < 9:
                continue
            z0 = rel(zz)
            if 1.8 < z0 < zf:
                items.append((z0, lambda z0=z0, side=side, i=i: tree(ctx, cam, side * 6.6, z0, 0.9 + (i % 3) * 0.15, i)))
    if not rear and rel(ZL) > 1.6 and not kw.get('no_stop'):
        items.append((rel(ZL), lambda: stop_sign(ctx, cam, 4.7, rel(ZL))))
    for x, zz, col in kw.get('cross_cars', lambda t: [])(t):
        if 2 < rel(zz) < zf:
            items.append((rel(zz), lambda x=x, zz=zz, col=col: car_side(ctx, cam, x, rel(zz), col)))
    for zz, x, lights in kw.get('police', lambda t: [])(t):
        d = rel(zz)
        if 2 < d < zf:
            items.append((d, lambda d=d, x=x, lights=lights: police_car_front(ctx, cam, x, d, t, lights)))
    for zz, x in kw.get('officer_at', lambda t: [])(t):
        d = rel(zz)
        if 2 < d < zf:
            def draw_off(d=d, x=x):
                px, py = cam.p(x, 1.25, d)
                officer(ctx, px, py, 0.62 * cam.f / d / 100, t, 'thumbs', 1.0, 'smile')
            items.append((d - 0.1, draw_off))
    for _, fn in sorted(items, key=lambda it: -it[0]):
        fn()


def cockpit_day(ctx, world, t, cam):
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
    mx, my = 120, 850
    ellipse(ctx, mx, my, 205, 128, -0.08)
    fill_stroke(ctx, hexc('#c23b3b'), OUTL, 5)
    ctx.save()
    ellipse(ctx, mx + 10, my, 170, 100, -0.08)
    ctx.clip()
    street_scene(ctx, world, Cam(mx + 70, my - 22, 260, world.camx(t) - 0.9, 1.0), t, {}, rear=True)
    ctx.restore()
    ellipse(ctx, mx + 10, my, 170, 100, -0.08)
    setc(ctx, OUTL)
    ctx.set_line_width(5)
    ctx.stroke()
    ang = clamp(world.steer(t) * 3.5, -0.3, 0.3)
    ctx.save()
    ctx.translate(960, 1230)
    ctx.rotate(ang)
    ellipse(ctx, 0, 0, 470, 360)
    ellipse(ctx, 0, 0, 405, 300)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#1b1b24'), OUTL, 5)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for s in (-1, 1):
        hx, hy = s * 360, -240
        poly(ctx, [(hx + s * 40, hy + 30), (hx + s * 210, hy + 520), (hx - s * 120, hy + 560), (hx - s * 60, hy + 60)])
        fill_stroke(ctx, JACKET, OUTL, 5)
        ellipse(ctx, hx, hy, 85, 62, s * 0.5)
        fill_stroke(ctx, SKIN, OUTL, 5)
        ellipse(ctx, hx - s * 20, hy - 30, 50, 26, s * 0.3)
        fill_stroke(ctx, SKIN, OUTL, 4)
    ctx.restore()


def flash_overlay(ctx, world, t):
    f = world.police_flash(t)
    if f <= 0:
        return
    ph = (t * 4) % 1 < 0.5
    for x, col, on in ((0, hexc('#ff2a2a'), ph), (SW, hexc('#2a6bff'), not ph)):
        if on:
            glow(ctx, x, SH * 0.45, 900, col, 0.45 * f)


def street_pov(ctx, world, t, lt, kw):
    yaw = key_or(kw, 'look', lt, 0.0) * 1400 - world.steer(t) * 1400
    spd = world.speed(t)
    bob = math.sin(t * 9) * 1.5 * min(spd / 12, 1)
    cam = Cam(960, 470 + bob, 1000, world.camx(t), 1.2, yaw)
    street_scene(ctx, world, cam, t, kw)
    cockpit_day(ctx, world, t, cam)
    flash_overlay(ctx, world, t)


def rear_mirror_day(ctx, world, t, lt, kw):
    draw_sky(ctx, 900, 0)
    setc(ctx, hexc('#2a2a36'))
    ctx.move_to(-10, -10)
    ctx.line_to(SW + 10, -10)
    ctx.line_to(SW + 10, 120)
    ctx.curve_to(1300, 170, 600, 170, -10, 120)
    ctx.close_path()
    ctx.fill()
    ctx.rectangle(920, 100, 80, 120)
    fill_stroke(ctx, hexc('#24243a'), OUTL, 5)
    mx, my = 960, 560
    rrect(ctx, mx - 800, my - 340, 1600, 680, 120)
    fill_stroke(ctx, hexc('#222230'), OUTL, 7)
    ctx.save()
    rrect(ctx, mx - 760, my - 300, 1520, 600, 90)
    ctx.clip()
    street_scene(ctx, world, Cam(mx, my - 20, 1100, world.camx(t), 1.25), t, kw, rear=True)
    setc(ctx, hexc('#2c2c38'))
    ctx.rectangle(mx - 800, my - 340, 1600, 680)
    rrect(ctx, mx - 560, my - 230, 1120, 380, 70)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for hx in (mx - 360, mx + 360):
        rrect(ctx, hx - 130, my + 60, 260, 200, 60)
        fill_stroke(ctx, hexc('#44445a'), OUTL, 4)
    g = cairo.LinearGradient(mx - 760, my - 300, mx, my + 300)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.12)
    g.add_color_stop_rgba(0.6, 1, 1, 1, 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    flash_overlay(ctx, world, t)


def window_ticket(ctx, world, t, lt, kw):
    """Looking out of the driver's window: officer writes the ticket and hands it over."""
    cam = Cam(1300, 520, 700, 0, 1.4, 0)
    draw_sky(ctx, 520, 0)
    setc(ctx, GRASS)
    ctx.rectangle(0, 520, SW, SH)
    ctx.fill()
    ground_quad(ctx, cam, -40, 40, 6, 400, SIDEWALK)
    for i, zz in enumerate(range(14, 200, 17)):
        house(ctx, cam, -16, -8, zz, zz + 10, 4.4, HOUSE_COLS[i % 7], ROOF_COLS[i % 4], i)
    police_car_front(ctx, Cam(1500, 560, 900, 0, 1.3, 0), 0, 9, t)
    give = key_or(kw, 'give', lt, 0.0)
    pose = 'write' if give < 0.01 else 'hand'
    officer(ctx, 900 + math.sin(t * 1.3) * 6, 640, 1.25, t, 'write' if pose == 'write' else 'none', lt, 'flat')
    if pose == 'hand':
        # arm reaching to the camera with the ticket
        sx, sy = 900 + 220, 560
        hx, hy = sx + 260 * give, sy + 160 * give
        hose(ctx, (sx, sy), (hx, hy), -60, 90, hexc('#1f3a6b'))
        ticket_paper(ctx, hx + 80 * give, hy + 60 * give, 0.45 + 0.5 * give, -0.2 + 0.15 * give, 0, 99)
        ellipse(ctx, hx, hy, 46, 40)
        fill_stroke(ctx, hexc('#c98d63'), OUTL, 5)
    # car window frame (door, pillar, roof) around the view
    setc(ctx, hexc('#c23b3b'))
    ctx.rectangle(-10, 900, SW + 20, 200)
    ctx.fill()
    ctx.rectangle(-10, 880, SW + 20, 30)
    setc(ctx, hexc('#1b1b24'))
    ctx.fill()
    poly(ctx, [(-10, -10), (180, -10), (60, 900), (-10, 900)])
    setc(ctx, hexc('#2a2a36'))
    ctx.fill()
    ctx.rectangle(-10, -10, SW + 20, 60)
    ctx.fill()
    flash_overlay(ctx, world, t)


def ticket_close(ctx, world, t, lt, kw):
    setc(ctx, hexc('#3a3a4c'))
    ctx.paint()
    ellipse(ctx, 960, SH + 260, 640, 330)
    ellipse(ctx, 960, SH + 260, 570, 270)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill_stroke(ctx, hexc('#1b1b24'), OUTL, 6)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    shake = math.sin(t * 40) * 3
    ticket_paper(ctx, 960 + shake, 540, 1.35, -0.04, lt, 0.5)
    for s in (-1, 1):
        ellipse(ctx, 960 + s * 360, 860, 80, 70, s * 0.3)
        fill_stroke(ctx, SKIN, OUTL, 6)
    flash_overlay(ctx, world, t)


def officer_ok(ctx, world, t, lt, kw):
    draw_sky(ctx, 600, 0)
    setc(ctx, GRASS)
    ctx.rectangle(0, 600, SW, SH)
    ctx.fill()
    cam = Cam(960, 600, 800, 0, 1.4, 0)
    ground_quad(ctx, cam, -40, 40, 8, 400, SIDEWALK)
    for i, zz in enumerate(range(16, 200, 17)):
        house(ctx, cam, 9, 17, zz, zz + 10, 4.4, HOUSE_COLS[(i + 2) % 7], ROOF_COLS[i % 4], i)
        tree(ctx, cam, -7, zz + 5, 1.0, i)
    police_car_front(ctx, Cam(1400, 620, 900, 0, 1.3, 0), 0, 8, t, lights=False)
    officer(ctx, 780, 700, 1.3, t, 'thumbs', lt, 'smile')
    for i in range(4):
        ph = (t * 0.8 + i * 0.25) % 1
        x, y = 1100 + i * 50, 250 + i * 70
        s = math.sin(math.pi * ph) * 34
        poly(ctx, [(x, y - s), (x + s * 0.3, y - s * 0.3), (x + s, y), (x + s * 0.3, y + s * 0.3),
                   (x, y + s), (x - s * 0.3, y + s * 0.3), (x - s, y), (x - s * 0.3, y - s * 0.3)])
        setc(ctx, hexc('#ffe08a'))
        ctx.fill()


def face_day(ctx, world, t, lt, kw):
    engine.SCENES['face'](ctx, world, t, lt, kw)
    flash_overlay(ctx, world, t)


engine.SCENES.update(street_pov=street_pov, rear_mirror_day=rear_mirror_day, window_ticket=window_ticket,
                     ticket_close=ticket_close, officer_ok=officer_ok, face_day=face_day)


# --------------------------------------------------------------------- SFX
def siren_whoop(n=2):
    out = np.zeros(int((0.42 * n + 0.2) * SR))
    for i in range(n):
        t = _t(0.38)
        f = 380 + 1100 * (t / 0.38) ** 0.7
        s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + np.sin(2 * np.pi * np.cumsum(f) / SR)
        place(out, lp(s, 3500) * env_adsr(len(t), 0.01, 0.08) * 0.35, i * 0.42)
    return out


def siren_wail(d):
    t = _t(d)
    f = 750 + 450 * np.sin(2 * np.pi * t / 2.2 - math.pi / 2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = lp(np.sign(np.sin(ph)) * 0.35 + np.sin(ph), 3000)
    return s * env_adsr(len(t), 0.3, 0.6) * 0.25


def paper_rip():
    t = _t(0.45)
    crack = (np.random.default_rng(4).random(len(t)) > 0.985).astype(float)
    crack = lp(crack, 3000) * 8
    s = bp(noise(len(t)), 1200, 7000) * (0.4 + crack) * np.sin(np.pi * t / 0.45)
    return s * 0.5


def paper_rustle(d=0.5):
    t = _t(d)
    am = np.abs(lp(noise(len(t)), 25)) * 5
    return bp(noise(len(t)), 1500, 8000) * am * np.sin(np.pi * t / d) * 0.3


def window_motor(d=1.0):
    t = _t(d)
    s = np.sin(2 * np.pi * (180 + 20 * t) * t) * 0.3 + lp(noise(len(t)), 600) * 0.2
    return s * env_adsr(len(t), 0.05, 0.1) * 0.6


def knock():
    out = np.zeros(int(0.5 * SR))
    for o in (0, 0.16):
        place(out, thud() * 0.6, o)
        place(out, click() * 0.4, o)
    return out


def whistle_tune():
    """Short carefree whistle (original 5-note motif)."""
    out = np.zeros(int(1.6 * SR))
    for i, (n, d) in enumerate(((79, 0.18), (83, 0.18), (86, 0.3), (84, 0.18), (86, 0.5))):
        t = _t(d)
        f = midi(n) * (1 + 0.01 * np.sin(2 * np.pi * 6 * t))
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) + bp(noise(len(t)), 1500, 4000) * 0.05
        place(out, s * env_adsr(len(t), 0.03, 0.05) * 0.25, sum(x[1] for x in ((79, 0.18), (83, 0.18), (86, 0.3), (84, 0.18), (86, 0.5))[:i]))
    return out
