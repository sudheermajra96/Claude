"""Approaching her: WITHOUT vs WITH confidence (Toronto waterfront, multi-angle 2D, SFX only)."""
import math

from park import *

engine.DAY = True
T_REW, T_B = 17.4, 18.6


def look_at(pos, target, f=1100, cx=960, cy=540):
    dx, dy, dz = target[0] - pos[0], target[1] - pos[1], target[2] - pos[2]
    return TCam(pos, math.atan2(dx, dz), math.atan2(-dy, math.hypot(dx, dz)), f, cx, cy)


hero = Actor([(0, 9, 11), (2.5, 6, 8.5), (3.5, 6, 8.5), (4.8, 3.8, 5.5), (5.6, 5.0, 4.6), (6.6, 2.6, 3.0),
              (7.6, 1.4, 1.5), (15.4, 1.4, 1.5), (17.4, 5.5, 6.5),
              (18.59, 5.5, 6.5), (18.6, 11, -2.8), (21.6, 4.0, -2.6), (23.0, 1.5, -2.0), (23.6, 0.9, -1.7), (40, 0.9, -1.7)])


def her_expr(t):
    if t < T_B:
        return 'read' if t < 10.2 else ('startled' if t < 11.6 else 'unsure')
    return 'read' if t < 22.8 else ('smile' if t < 30.6 else 'laugh')


def her_pose(t):
    if t < T_B:
        return 'read' if t < 10.2 else ('none' if t < 15.4 else 'shrug')
    return 'read' if t < 23.2 else ('show' if 28.2 <= t < 30.6 else 'none')


def her_lean(t):
    if t < T_B:
        return -0.12 * smooth((t - 11.4) / 0.4) if 11.4 <= t < 17.4 else 0.0
    return 0.0


ST = dict(hero=hero,
          mood=lambda t: 'nervous' if t < T_B else 'confident',
          hero_expr=lambda t: 'unsure' if t < T_B else ('calm' if t < 23.6 else 'happy'),
          sweat=lambda t: t < T_B,
          her_expr=her_expr, her_pose=her_pose, her_lean=her_lean,
          wave=lambda t: 1.0 if 25.6 <= t < 26.5 else 0.0)


class W:      # minimal world object for the Video composer
    speed = staticmethod(lambda t: 0.0)


def cam_for(name, t):
    hx, hz = hero.pos(t)
    if name == 'wide':
        return look_at((2.6, 1.6, -6.0), (-0.1, 1.2, 0.8), 1250)
    if name == 'hover':
        return look_at((-1.8, 1.5, -5.5), (0.5, 1.1, 0.8), 1300)
    if name == 'two_wrong':
        return look_at((0.6, 1.5, -4.2), (0.55, 1.15, 0.9), 1450)
    if name == 'two_right':
        return look_at((-2.9, 1.5, -1.6), (0.25, 1.15, -0.65), 1250)
    if name == 'behind_him':
        f = hero.facing(t, math.atan2(HER_POS[0] - hx, HER_POS[1] - hz))
        fx, fz = math.sin(f), math.cos(f)
        rx, rz = math.cos(f), -math.sin(f)
        pos = (hx - fx * 2.8 + rx * 0.7, 1.8, hz - fz * 2.8 + rz * 0.7)
        return look_at(pos, (HER_POS[0], 1.0, HER_POS[1]), 1150)
    if name == 'over_her':
        return look_at((-0.75, 1.4, 1.15), (hx, 1.5, hz), 1150, cx=1100)
    if name == 'wide_end':
        return look_at((-4.6, 1.7, -2.8), (0.25, 1.1, -0.65), 1150)
    raise ValueError(name)


def park_cam(ctx, world, t, lt, kw):
    view = cam_for(kw['cam'], t)
    draw_park(ctx, view, t, ST, her=kw['cam'] != 'over_her')
    if kw['cam'] == 'over_her':
        her_back(ctx, 470, 980, 1.25)
    for t0, t1, who, text, italic in kw.get('bubbles', []):
        if t0 <= lt < t1:
            a = smooth((lt - t0) / 0.15)
            if who == 'him':
                hx, hz = hero.pos(t)
                p = view.pt((hx, 2.05, hz))
            elif kw['cam'] == 'over_her':
                p = (520, 330)
            else:
                p = view.pt((HER_POS[0], 1.42, HER_POS[1]))
            if p:
                x = min(max(p[0], 430), SW - 430)
                speech(ctx, x, p[1] - 10, text, 50, (0, 1), (1, 1, 1) if not italic else hexc('#e6e6ee'), a, italic)


def park_top(ctx, world, t, lt, kw):
    view = ParkTop(xc=3.0, zc=-2.3, s=62, oy=540)
    draw_park(ctx, view, t, ST)
    # her field of view
    c = view.pt((HER_POS[0], 0, HER_POS[1]))
    r = 7.0 * view.s
    ctx.move_to(*c)
    ctx.arc(c[0], c[1], r, math.pi / 2 - 0.95, math.pi / 2 + 0.95)
    ctx.close_path()
    setc(ctx, hexc('#ffd84a'), 0.28)
    ctx.fill_preserve()
    setc(ctx, hexc('#c9a400'), 0.8)
    ctx.set_line_width(4)
    ctx.set_dash([14, 10])
    ctx.stroke()
    ctx.set_dash([])
    text_center(ctx, 'her view', c[0], c[1] + r * 0.62, 40, hexc('#7a6200'))
    good = kw['good']
    col = hexc('#22a356') if good else hexc('#e0393e')
    t0 = kw['trail_from']
    pts = [view.pt((hero.X(tt), 0, hero.Z(tt))) for tt in np.arange(t0, t + 0.001, 0.05)]
    if good:
        ghost = [view.pt((hero.X(tt), 0, hero.Z(tt))) for tt in np.arange(t0, 23.6, 0.05)]
        ctx.move_to(*ghost[0])
        for p in ghost[1:]:
            ctx.line_to(*p)
        setc(ctx, col, 0.3)
        ctx.set_line_width(8)
        ctx.set_dash([16, 12])
        ctx.stroke()
        ctx.set_dash([])
        ctx.new_sub_path()
        ctx.arc(c[0], c[1], 1.4 * view.s, 0, 2 * math.pi)
        setc(ctx, hexc('#22a356'), 0.9)
        ctx.set_line_width(5)
        ctx.set_dash([10, 8])
        ctx.stroke()
        ctx.set_dash([])
    if len(pts) > 1:
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        setc(ctx, col)
        ctx.set_line_width(9)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_dash([2, 16])
        ctx.stroke()
        ctx.set_dash([])
    draw_hero(ctx, view, t, ST)
    if lt > kw.get('mark_t', 99):
        a = smooth((lt - kw['mark_t']) / 0.25)
        hx, hz = hero.pos(t)
        p = view.pt((hx, 0, hz))
        mx, my = p[0] + 70, p[1] - 70
        ellipse(ctx, mx, my, 34 * a, 34 * a)
        fill_stroke(ctx, col, OUTL, 4)
        if good:
            ctx.move_to(mx - 14, my)
            ctx.line_to(mx - 3, my + 12)
            ctx.line_to(mx + 16, my - 12)
        else:
            ctx.move_to(mx - 12, my - 12)
            ctx.line_to(mx + 12, my + 12)
            ctx.move_to(mx + 12, my - 12)
            ctx.line_to(mx - 12, my + 12)
        setc(ctx, (1, 1, 1), a)
        ctx.set_line_width(7)
        ctx.stroke()
        text_center(ctx, kw['mark_text'], mx + 10, my - 52, 40, col, a=a)


def bust_bg(ctx, look):
    if look == 'north':
        view = look_at((3.0, 1.6, -7.0), (2.0, 2.2, 10.0), 900)
    else:
        view = look_at((0.0, 1.6, 3.5), (1.0, 1.4, -10.0), 900)
    draw_park(ctx, view, 0.0, ST, her=False, hero=False)
    setc(ctx, (1, 1, 1), 0.15)
    ctx.paint()


def hero_close(ctx, world, t, lt, kw):
    bust_bg(ctx, kw.get('bg', 'north'))
    cx = 960
    ctx.move_to(cx - 470, SH + 10)
    ctx.curve_to(cx - 470, 860, cx - 300, 790, cx, 790)
    ctx.curve_to(cx + 300, 790, cx + 470, 860, cx + 470, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    poly(ctx, [(cx - 120, 795), (cx + 120, 795), (cx, 960)])
    fill_stroke(ctx, hexc('#f2efe6'), OUTL, 5)
    ctx.rectangle(cx - 80, 700, 160, 110)
    fill_stroke(ctx, SKIN_SH, OUTL, 5)
    expr = kw['expr']
    life.draw_head(ctx, cx, 500, 1.0, expr, t, kw.get('tilt', 0.0), kw.get('look', (0, 0)))
    if kw.get('sweat'):
        sx, sy = cx + 230, 330 + (lt * 50) % 60
        ctx.move_to(sx, sy - 45)
        ctx.curve_to(sx + 30, sy, sx + 30, sy + 30, sx, sy + 30)
        ctx.curve_to(sx - 30, sy + 30, sx - 30, sy, sx, sy - 45)
        fill_stroke(ctx, hexc('#8fd6ff'), OUTL, 4)
    if kw.get('sparkle'):
        for i in range(4):
            ph = (t * 0.8 + i * 0.25) % 1
            x, y = cx + 330 + i * 55, 260 + i * 80
            s = math.sin(math.pi * ph) * 34
            poly(ctx, [(x, y - s), (x + s * 0.3, y - s * 0.3), (x + s, y), (x + s * 0.3, y + s * 0.3),
                       (x, y + s), (x - s * 0.3, y + s * 0.3), (x - s, y), (x - s * 0.3, y - s * 0.3)])
            setc(ctx, hexc('#ffe08a'))
            ctx.fill()


def her_close(ctx, world, t, lt, kw):
    bust_bg(ctx, kw.get('bg', 'south'))
    cx = 960
    jx = math.sin(lt * 60) * 10 * (1 - clamp(lt / 0.6)) if kw.get('shake') else 0
    ctx.move_to(cx - 440, SH + 10)
    ctx.curve_to(cx - 440, 880, cx - 280, 820, cx, 820)
    ctx.curve_to(cx + 280, 820, cx + 440, 880, cx + 440, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, HER_JACKET, OUTL, 6)
    poly(ctx, [(cx - 90, 822), (cx + 90, 822), (cx + 70, SH + 10), (cx - 70, SH + 10)])
    fill_stroke(ctx, (0.98, 0.98, 0.96), OUTL, 5)
    ctx.rectangle(cx - 60, 730, 120, 100)
    fill_stroke(ctx, mix(HER_SKIN, (0, 0, 0), 0.12), OUTL, 5)
    her_head(ctx, cx + jx, 470, 1.05, kw['expr'], t)
    if kw['expr'] == 'startled' and lt < 1.0:
        for k_ in range(7):
            a = -math.pi / 2 + (k_ - 3) * 0.33
            r0 = 360 + 20 * math.sin(lt * 30 + k_)
            ctx.move_to(cx + math.cos(a) * r0, 430 + math.sin(a) * r0)
            ctx.line_to(cx + math.cos(a) * (r0 + 90), 430 + math.sin(a) * (r0 + 90))
        setc(ctx, OUTL, 0.9)
        ctx.set_line_width(12)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


engine.SCENES.update(park_cam=park_cam, park_top=park_top, hero_close=hero_close, her_close=her_close)

shots = [
    Shot(3.0, 'park_cam', cam='wide'),                                                              # 0
    Shot(1.6, 'hero_close', expr='unsure', sweat=True, look=(0.5, 0.6)),                            # 1
    Shot(3.0, 'park_top', good=False, trail_from=0.0, mark_t=2.9, mark_text='Out of her view'),     # 2
    Shot(2.6, 'park_cam', cam='hover'),                                                             # 3
    Shot(1.4, 'her_close', expr='startled', shake=True),                                            # 4
    Shot(2.4, 'park_cam', cam='two_wrong', bubbles=[(0.2, 2.4, 'him', 'uh... um...', True),
                                                    (1.3, 2.4, 'her', '?', False)]),               # 5
    Shot(1.4, 'hero_close', expr='unsure', sweat=True, look=(0, 1)),                                # 6
    Shot(2.0, 'park_cam', cam='wide'),                                                              # 7
    Shot(1.2, 'rewind_seq'),                                                                        # 8
    Shot(2.8, 'park_top', good=True, trail_from=T_B, mark_t=99, mark_text='In her view'),           # 9
    Shot(2.6, 'park_cam', cam='behind_him'),                                                        # 10
    Shot(1.6, 'hero_close', expr='happy', bg='south', sparkle=True),                                # 11
    Shot(2.6, 'park_cam', cam='two_right', bubbles=[(0.15, 2.6, 'him', 'Hi! Is that book any good?', False)]),  # 12
    Shot(2.4, 'park_cam', cam='over_her', bubbles=[(0.15, 2.4, 'her', "It's amazing! Have you read it?", False)]),  # 13
    Shot(2.6, 'park_cam', cam='wide_end'),                                                          # 14
]
shots[8].kw.update(srcs=list(reversed(shots[0:8])), dur=shots[8].dur)
video = Video(['Approaching her:', 'WITHOUT vs WITH confidence'], W(), shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.3, E[0] - 0.2, location_tag('Toronto Waterfront')),
    (S[1], E[7], badge('WITHOUT confidence', '#e0393e')),
    (S[2] + 0.2, E[2], caption_in_scene('Sneaking up from behind')),
    (S[3] + 0.2, E[3], caption_in_scene('Hovering too close')),
    (S[5] + 0.2, E[5], caption_in_scene('Mumbling, no eye contact')),
    (S[7] + 0.2, E[7], caption_in_scene('...awkward exit')),
    (S[9], E[14], badge('WITH confidence', '#22a356')),
    (S[9] + 0.2, E[9], caption_in_scene('1. Approach where she can see you')),
    (S[10] + 0.2, E[10], caption_in_scene('2. Walk tall & relaxed')),
    (S[11] + 0.2, E[11], caption_in_scene('3. Eye contact + a real smile')),
    (S[12] + 0.2, E[12], caption_in_scene('4. Keep it simple & friendly')),
    (S[13] + 0.2, E[13], caption_in_scene('5. Listen & be curious')),
    (S[14] + 0.2, E[14], caption_in_scene('Respect her answer, either way.')),
]


def park_ambience(d):
    t = np.arange(int(d * SR)) / SR
    waves = lp(noise(len(t)), 500) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t) ** 2) * 0.5
    wind = bp(noise(len(t)), 200, 900) * 0.06
    hum = lp(noise(len(t)), 120) * 0.25
    return waves + wind + hum


def sound():
    m = Mixer(video.dur)
    m.add(park_ambience(video.dur), 0, 0.5)
    for t0, t1, rate in ((0.0, 7.6, 1.8), (15.4, 17.4, 1.8), (18.6, 23.6, 2.6)):
        tt = t0 + 0.1
        while tt < t1:
            if hero.walking(tt):
                m.add(footsteps(0.12, 100), tt, 0.13, 0.2)
            tt += 1 / rate
    m.add(heartbeat(6, 130), S[1], 1.2)
    m.add(gulp(), S[1] + 0.6, 1.0)
    m.add(record_scratch(), S[4], 1.0)
    m.add(boing(), S[4] + 0.05, 0.6)
    m.add(pop(), S[5] + 0.2, 0.6)
    m.add(pop(), S[5] + 1.3, 0.5)
    m.add(sad_violin(), S[7] + 0.1, 1.6)
    m.add(rewind_sfx(1.2), S[8], 1.0)
    m.add(chime(), 22.9, 0.9)
    m.add(sparkle(), S[11] + 0.2, 1.4)
    m.add(pop(), S[12] + 0.15, 0.6)
    m.add(pop(), S[13] + 0.15, 0.6)
    m.add(success_jingle(), S[14] + 0.2, 0.9)
    return m.out(video.dur)


if __name__ == '__main__':
    run(video, sound, 'confidence.mp4')
