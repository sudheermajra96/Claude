"""Driver mistake #2: tailgating. Rural two-lane highway, Wellington County, Ontario (farms, barns, silos)."""
from mkit import *

X = 1.75
V = 25.0
# ---------- WRONG (world 3 .. 13.4): 0.78 s gap, lead brakes hard for a deer, ego reacts 0.75 s later
leadW = Track(X, Key([(0, V), (8.0, V), (11.125, 0)], 'lin'), 3.0, 23.8, '#f4f4f6')
egoW = Track(X, Key([(0, V), (8.75, V), (11.875, 0)], 'lin'), 3.0, 0.0, C_EGO)
# ---------- RIGHT (world 13.4 ..): start at 1 s, ease off to 3 s, then the same emergency
leadR = Track(X, Key([(0, V), (25.5, V), (28.625, 0)], 'lin'), 13.4, 29.4, '#f4f4f6')
egoR = Track(X, Key([(0, V), (13.4, V), (14.4, 18), (20.5, 18), (21.5, V), (26.25, V), (32.5, 0)], 'lin'), 13.4, 0.0, C_EGO)


def oncoming(seed):
    out = []
    for i, z0 in enumerate((180, 420, 700, 980)):
        p = Path([('L', (-X, 2000), (-X, -2000))])
        out.append(Mover(p, const(24), 13.4 if seed else 3.0, p.s_near(-X, z0), COLS[(i * 3 + seed) % 10], t0=-40, t1=120))
    return out


ONW, ONR = oncoming(0), oncoming(1)
DEER_W = (leadW.z(11.125) + 7.5, 9.1)          # (z, time the deer is in the middle of the road)
DEER_R = (leadR.z(28.625) + 7.5, 26.6)


def deer_xz(t):
    if t < 3.0:
        t = t + 9.6
    z, tc = DEER_W if t < 13.4 else DEER_R
    return 6.5 * (tc - t), z


def deer(ctx, view, t):
    x, z = deer_xz(t)
    if abs(x) > 40:
        return
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 0.9 * view.s, 0.4 * view.s)
        fill_stroke(ctx, hexc('#8a5a34'), OUTL, 2)
        return
    s = view.scale((x, 1.0, z))
    b = view.pt((x, 0, z))
    if not s or not b:
        return
    ph = t * 9
    dirn = -1           # running toward -x
    lw = max(1.5, s / 45)
    by = b[1] - 1.0 * s
    for k, off in enumerate((-0.45, -0.3, 0.3, 0.45)):
        lx = b[0] + off * s * dirn
        sw = math.sin(ph + k * 1.7) * 0.25 * s
        ctx.move_to(lx, by + 0.1 * s)
        ctx.line_to(lx + sw, b[1])
        setc(ctx, OUTL)
        ctx.set_line_width(0.12 * s + lw)
        ctx.stroke()
        ctx.move_to(lx, by + 0.1 * s)
        ctx.line_to(lx + sw, b[1])
        setc(ctx, hexc('#7a4a2a'))
        ctx.set_line_width(0.1 * s)
        ctx.stroke()
    ellipse(ctx, b[0], by, 0.7 * s, 0.32 * s)
    fill_stroke(ctx, hexc('#9a6a3a'), OUTL, lw)
    hx, hy = b[0] + 0.75 * s * dirn, by - 0.45 * s
    poly(ctx, [(b[0] + 0.45 * s * dirn, by - 0.1 * s), (hx, hy), (hx + 0.12 * s * dirn, hy + 0.15 * s), (b[0] + 0.5 * s * dirn, by + 0.1 * s)])
    fill_stroke(ctx, hexc('#9a6a3a'), OUTL, lw)
    ellipse(ctx, hx + 0.12 * s * dirn, hy, 0.2 * s, 0.13 * s)
    fill_stroke(ctx, hexc('#8a5a34'), OUTL, lw)
    for a in (-0.4, 0.3):
        ctx.move_to(hx, hy - 0.1 * s)
        ctx.line_to(hx + a * s, hy - 0.45 * s)
        ctx.line_to(hx + a * 1.4 * s, hy - 0.55 * s)
    setc(ctx, hexc('#d8c3a0'))
    ctx.set_line_width(max(1.5, 0.05 * s))
    ctx.stroke()
    ellipse(ctx, b[0] - 0.68 * s * dirn, by - 0.12 * s, 0.12 * s, 0.12 * s)
    setc(ctx, (1, 1, 1))
    ctx.fill()


FARMS = []
_r = random.Random(4)
for i, z in enumerate(range(-200, 1500, 95)):
    sx = 1 if i % 2 else -1
    FARMS.append((sx, z, _r.uniform(18, 34)))


def post_z():
    return leadR.z(21.6) + 2.2          # lead's front passes the post at 21.6


def farm_extras(ctx, view, t):
    out = []
    for sx, z, d in FARMS:
        bx = sx * d
        out.append(((bx, 4, z), lambda bx=bx, z=z: barn(ctx, view, *sorted((bx, bx + 12 * (1 if bx > 0 else -1))), z, z + 9)))
        sxx = bx + (14 if bx > 0 else -14)
        out.append(((sxx, 6, z + 3), lambda sxx=sxx, z=z: silo(ctx, view, sxx, z + 3)))
        for k in range(3):
            hx = bx + (6 + k * 3) * (1 if bx > 0 else -1)
            out.append(((hx, 0.7, z - 20), lambda hx=hx, z=z: hay_bale(ctx, view, hx, z - 20)))
    for sx in (-1, 1):
        out.append(((sx * 5.0, 0.6, 600), lambda sx=sx: fence(ctx, view, sx * 5.0, -300, 1500)))
    pz = post_z()
    out.append(((5.2, 1.4, pz), lambda: post_marker(ctx, view, 5.2, pz)))
    out.append(((0, 1.0, deer_xz(t)[1]), lambda: deer(ctx, view, t)))
    return out


def post_marker(ctx, view, x, z):
    if view.ortho:
        p = view.pt((x, 0, z))
        ellipse(ctx, p[0], p[1], 0.35 * view.s, 0.35 * view.s)
        fill_stroke(ctx, (1, 1, 1), OUTL, 2)
        return
    b, tp, s = view.pt((x, 0, z)), view.pt((x, 1.6, z)), view.scale((x, 0, z))
    if b and tp and s:
        ctx.rectangle(b[0] - 0.08 * s, tp[1], 0.16 * s, b[1] - tp[1])
        fill_stroke(ctx, (1, 1, 1), OUTL, max(1, s / 40))
        ctx.rectangle(b[0] - 0.08 * s, tp[1], 0.16 * s, 0.25 * s)
        setc(ctx, hexc('#e0393e'))
        ctx.fill()


def hills(ctx, view):
    far_line(ctx, view, 2600, lambda x: 60 + 40 * math.sin(x / 300) + 20 * math.sin(x / 90), col='#8fb87a')
    far_line(ctx, view, 1800, lambda x: 25 + 15 * math.sin(x / 140 + 1), col='#7aa868')


city = Street('farm', n=1, median='yellow', sidewalk=False, seed=2, skyline=hills, extras=farm_extras, ground='#9fcf7a')
world = SegWorld(35.0, [hook_seg(0, 3.0, 9.6, egoW, [leadW] + ONW), (3.0, 13.4, egoW, [leadW] + ONW, []),
                        (13.4, 99, egoR, [leadR] + ONR, [])], city, 'kmh')


def gap_s(lead, ego, t):
    return (lead.z(t) - ego.z(t) - 4.4) / max(ego.speed(t), 1.0)


def meter_at(t0, lead, ego):
    return gap_meter(lambda lt: gap_s(lead, ego, t0 + lt), 'TIME GAP', 's', 2.8, 1.8, x=1600, y=250)


def count_overlay(ctx, lt, d):
    t = 21.6 + lt - 0.0
    n = int((t - 21.6))
    if t >= 21.6:
        for k in range(1, 4):
            if t - 21.6 >= k - 1 + 0.05:
                last = (k == min(3, int(t - 21.6) + 1))
                outlined_text(ctx, str(k) + ('...' if k < 3 else '!'), 560 + (k - 1) * 400, 300, 140 if last else 100,
                              hexc('#ffd23f') if last else (1, 1, 1), lw=20)


def big_gap_post(ctx, view, t, lt):
    a = smooth(lt / 0.4)
    ez, lz = egoR.z(t), leadR.z(t)
    p0, p1 = view.pt((X + 2.4, 0, ez + 2.2)), view.pt((X + 2.4, 0, lz - 2.2))
    ctx.move_to(*p0)
    ctx.line_to(p0[0] + (p1[0] - p0[0]) * a, p1[1])
    setc(ctx, hexc('#22a356'))
    ctx.set_line_width(10)
    ctx.stroke()
    label(ctx, (p0[0] + p1[0]) / 2, p0[1] + 70, f'{lz - ez - 4.4:.0f} m to spare', '#22a356', 48)


def post_label(ctx, view, t, lt):
    p = view.pt((X + 3.4, 0, post_z()))
    ctx.move_to(p[0], p[1] - 10)
    ctx.line_to(p[0], p[1] + 40)
    setc(ctx, (1, 1, 1))
    ctx.set_line_width(5)
    ctx.stroke()
    ellipse(ctx, p[0], p[1] - 10, 12, 12)
    fill_stroke(ctx, hexc('#e0393e'), (1, 1, 1), 3)
    label(ctx, p[0], p[1] + 100, 'Fixed point', '#2f6f9f', 42)


def tight_post(ctx, view, t, lt):
    ez, lz = egoW.z(t), leadW.z(t)
    p = view.pt((X + 2.4, 0, (ez + lz) / 2))
    label(ctx, p[0], p[1] + 70, f'{max(0.0, lz - ez - 4.4):.1f} m left!', '#e0393e', 52)


HOOK_CAM = dict(cam='follow', off=(-7.0, 1.7, 1.0), look=(0.0, 0.8, 5.0), f=950)
defs = [
    (3.0, 'm_cam', HOOK_CAM),
    (6.0, 'm_cam', dict(cam='chase')),
    (8.6, 'm_cam', dict(cam='follow', off=(-3.2, 2.4, -6.5), look=(0.5, 1.0, 14), f=1000)),
    (10.4, 'm_cam', dict(cam='follow', off=(-7.5, 2.6, 8.0), look=(0.0, 0.9, 27), f=950)),
    (12.4, 'm_top', dict(scale=34.0, ahead=4.0, post=tight_post)),
    (13.4, 'rewind_seq', dict()),
    (17.4, 'm_cam', dict(cam='chase')),
    (21.4, 'm_cam', dict(cam='follow', off=(-3.2, 2.4, -6.5), look=(0.5, 1.0, 30), f=1000)),
    (25.0, 'm_top', dict(scale=13.0, ahead=40.0, post=post_label)),
    (28.6, 'm_cam', dict(cam='chase')),
    (31.6, 'm_top', dict(scale=19.0, ahead=13.0, post=big_gap_post)),
    (35.0, 'm_cam', dict(cam='follow', off=(10, 14, -26), look=(0, 0, 12), hud=False)),
]
shots = build_shots(defs)
shots[5].kw.update(srcs=list(reversed(shots[1:5])), dur=shots[5].dur)
video = Video(['Driver MISTAKE #2', 'Tailgating'], world, shots)
S = [s.start for s in shots]
E = [s.start + s.dur for s in shots]
video.overlays = [
    (0.0, 3.0, big_text('Can he stop in time?', 290, 140, hexc('#ffd23f'), 0.3, True)),
    (3.0, 6.0, mistake_title(2, 'Following too close')),
    (3.2, 5.8, location_tag('Wellington County, Ontario')),
    (S[2], E[4], badge('WRONG', '#e0393e')),
    (S[2], E[2], meter_at(S[2], leadW, egoW)),
    (S[2] + 0.1, E[2], caption('Less than 1 second behind...')),
    (S[3] + 0.1, E[3], caption('Deer! The car ahead slams the brakes')),
    (S[4] + 0.1, E[4], caption('No time to react')),
    (S[4] + 0.3, E[4], x_mark),
    (S[6], E[10], badge('RIGHT', '#22a356')),
    (S[6], E[7], meter_at(S[6], leadR, egoR)),
    (S[8], E[8], count_overlay),
    (S[11] + 0.2, E[11], end_card('Keep 3 seconds. Double it in rain.', 'How many seconds do YOU leave? Comment!')),
]
for n, (i, txt) in enumerate(((6, 'Too close? Ease off the gas'), (7, 'Build a 3-second gap'), (8, 'Count from a fixed point: 1, 2, 3'),
                              (9, 'Car brakes ahead? You have time'), (10, 'Space = time to react')), 1):
    video.overlays += [(S[i], E[i], step_badge(n)), (S[i] + 0.15, E[i], caption(txt))]
video.overlays.append((S[10] + 0.6, E[10], check_mark))


def sound():
    m = Mixer(video.dur)
    m.add(ambience(world, video.dur, inside=0.9), 0, 0.14)
    m.add(city_ambience(video.dur), 0, 0.12)
    hook_sfx(m)
    m.add(screech(1.4, 1200), 1.2, 0.7)
    m.add(screech(2.6, 1150), 8.0, 0.55, 0.2)
    m.add(screech(3.0, 1250), 8.8, 0.8)
    m.add(horn(0.6), 11.9, 0.6, 0.2)
    m.add(heartbeat(3, 130), 11.9, 1.0)
    sting_bad(m, S[4] + 0.3)
    m.add(rewind_sfx(1.0), S[5], 1.0)
    for k in range(3):
        m.add(bell(midi(76 + k * 4), 0.5), 21.6 + k, 0.8)
    m.add(screech(2.4, 1150), 25.5, 0.45, 0.2)
    m.add(brake_squeal(2.0), 26.4, 0.25)
    for i in range(6, 11):
        m.add(pop(), S[i] + 0.15, 0.7)
    sting_good(m, S[10] + 0.6)
    m.add(success_jingle(), S[11] + 0.2, 0.9)
    m.add(pop(), S[11] + 1.0, 0.8)
    return m.out(video.dur)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[2] == 'verify':
        print('wrong final gap', round(leadW.z(12.5) - egoW.z(12.5) - 4.4, 2), 'right final gap', round(leadR.z(33) - egoR.z(33) - 4.4, 1),
              'gap@21.6', round(gap_s(leadR, egoR, 21.6), 2), 'gap@8', round(gap_s(leadW, egoW, 7.9), 2))
        print('min', min_gap([egoW, leadW], 3, 13.4), min_gap([egoR, leadR], 13.4, 35))
    else:
        run(video, sound, 'm02.mp4')
