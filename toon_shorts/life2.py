"""More self-improvement scenes + beat-synced music and pro-style SFX layers."""
from life import *
import engine

BPM = 120
BEAT = 60 / BPM


# ----------------------------------------------------------------- scenes
CARD_COLS = ['#ff6b6b', '#ffd166', '#06d6a0', '#118ab2', '#c77dff', '#ff9f1c', '#2ec4b6', '#e76f51']


def phone_close(ctx, world, t, lt, kw):
    setc(ctx, hexc('#0b0d20'))
    ctx.paint()
    glow(ctx, 960, 520, 900, hexc('#4a74ff'), 0.35)
    swipes = kw.get('swipes', [])
    pos = 0.0
    cur = None
    for s0 in swipes:
        if lt >= s0:
            u = clamp((lt - s0) / 0.22)
            pos += 1 - (1 - u) ** 3
            if u < 1:
                cur = u
    pos *= 340
    # palm behind phone
    ellipse(ctx, 700, 980, 260, 200, -0.4)
    fill_stroke(ctx, SKIN, OUTL, 6)
    px, py, pw, ph = 960, 600, 470, 920
    ctx.save()
    ctx.translate(px, py)
    ctx.rotate(-0.05)
    rrect(ctx, -pw / 2, -ph / 2, pw, ph, 60)
    fill_stroke(ctx, hexc('#121218'), OUTL, 7)
    rrect(ctx, -pw / 2 + 22, -ph / 2 + 22, pw - 44, ph - 44, 42)
    ctx.save()
    ctx.clip()
    setc(ctx, hexc('#f4f5fb'))
    ctx.paint()
    rnd = random.Random(11)
    top = -ph / 2 + 70
    for i in range(40):
        y = top + i * 340 - pos
        if y > ph / 2 or y + 320 < -ph / 2:
            rnd.random(); rnd.random()
            continue
        col = hexc(CARD_COLS[i % len(CARD_COLS)])
        ellipse(ctx, -pw / 2 + 70, y + 20, 22, 22)
        setc(ctx, mix(col, (0, 0, 0), 0.2))
        ctx.fill()
        rrect(ctx, -pw / 2 + 105, y + 8, 160, 18, 9)
        setc(ctx, hexc('#c9cbd8'))
        ctx.fill()
        rrect(ctx, -pw / 2 + 40, y + 55, pw - 80, 210, 18)
        setc(ctx, col)
        ctx.fill()
        kind = i % 3
        cx0, cy0 = 0, y + 160
        if kind == 0:
            ellipse(ctx, cx0, cy0, 60, 60)
            setc(ctx, (1, 1, 1), 0.85)
            ctx.fill()
        elif kind == 1:
            poly(ctx, [(cx0 - 90, cy0 + 70), (cx0 - 20, cy0 - 40), (cx0 + 30, cy0 + 20), (cx0 + 60, cy0 - 10), (cx0 + 120, cy0 + 70)])
            setc(ctx, (1, 1, 1), 0.8)
            ctx.fill()
        else:
            poly(ctx, [(cx0 - 35, cy0 - 45), (cx0 + 50, cy0), (cx0 - 35, cy0 + 45)])
            setc(ctx, (1, 1, 1), 0.9)
            ctx.fill()
        # heart
        hx, hy = -pw / 2 + 60, y + 292
        ctx.move_to(hx, hy + 12)
        ctx.curve_to(hx - 30, hy - 8, hx - 12, hy - 28, hx, hy - 12)
        ctx.curve_to(hx + 12, hy - 28, hx + 30, hy - 8, hx, hy + 12)
        setc(ctx, hexc('#ff3b5c'))
        ctx.fill()
        rrect(ctx, -pw / 2 + 100, y + 282, 120, 16, 8)
        setc(ctx, hexc('#c9cbd8'))
        ctx.fill()
    # notifications
    for n0, label, col in kw.get('notifs', []):
        if n0 <= lt < n0 + 1.0:
            a = smooth((lt - n0) / 0.15)
            out = smooth((lt - n0 - 0.8) / 0.2)
            y = -ph / 2 + 40 - 160 * (1 - a) - 160 * out
            rrect(ctx, -pw / 2 + 36, y, pw - 72, 120, 26)
            fill_stroke(ctx, (1, 1, 1), hexc('#d9dbe6'), 3)
            rrect(ctx, -pw / 2 + 56, y + 22, 76, 76, 18)
            setc(ctx, hexc(col))
            ctx.fill()
            ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(34)
            ctx.move_to(-pw / 2 + 150, y + 58)
            setc(ctx, OUTL)
            ctx.show_text(label)
            rrect(ctx, -pw / 2 + 150, y + 74, 200, 16, 8)
            setc(ctx, hexc('#c9cbd8'))
            ctx.fill()
    ctx.restore()
    ctx.restore()
    # thumb
    ty = 870 if cur is None else 870 - 380 * math.sin(math.pi * cur)
    tx = 1080 + (0 if cur is None else -20 * math.sin(math.pi * cur))
    hose(ctx, (1400, 1150), (tx, ty), -60, 110, SKIN)
    ellipse(ctx, tx, ty, 62, 74, -0.3)
    fill_stroke(ctx, SKIN, OUTL, 6)
    ellipse(ctx, tx - 8, ty - 30, 34, 26, -0.3)
    setc(ctx, hexc('#f7d6c0'))
    ctx.fill()
    # left fingers wrapping the phone edge
    for i in range(3):
        ellipse(ctx, 725 - i * 6, 520 + i * 120, 48, 52)
        fill_stroke(ctx, SKIN, OUTL, 5)


def face_scene(ctx, world, t, lt, kw):
    L = key_or(kw, 'light', lt, 1.0)
    shake = key_or(kw, 'shake', lt, 0.0)
    jx = math.sin(t * 70) * 16 * shake
    setc(ctx, light_wall(L))
    ctx.paint()
    window(ctx, 1280, 120, 460, 520, L, t)
    if L > 0.5:
        glow(ctx, 1500, 380, 700, hexc('#ffcf6b'), 0.35 * L)
    cx = 860 + jx
    ctx.move_to(cx - 470, SH + 10)
    ctx.curve_to(cx - 470, 860, cx - 300, 790, cx, 790)
    ctx.curve_to(cx + 300, 790, cx + 470, 860, cx + 470, SH + 10)
    ctx.close_path()
    fill_stroke(ctx, JACKET, OUTL, 6)
    poly(ctx, [(cx - 120, 795), (cx + 120, 795), (cx, 960)])
    fill_stroke(ctx, hexc('#f2efe6'), OUTL, 5)
    ctx.rectangle(cx - 80, 700, 160, 110)
    fill_stroke(ctx, SKIN_SH, OUTL, 5)
    look = (0, 0)
    if 'flicks' in kw:
        f = [x for x in kw['flicks'] if x <= lt]
        if f:
            u = clamp((lt - f[-1]) / 0.18)
            look = (0, 0.9 - 1.4 * (1 - u) * (u > 0))
        else:
            look = (0, 0.9)
    draw_head(ctx, cx, 500, 1.0, kw.get('expr', 'proud'), t, math.sin(t * 1.5) * 0.03, look)
    if kw.get('phone_glow'):
        setc(ctx, hexc('#05061a'), 0.55)
        ctx.paint()
        g = cairo.RadialGradient(cx, 950, 50, cx, 700, 760)
        g.add_color_stop_rgba(0, 0.45, 0.65, 1.0, 0.55)
        g.add_color_stop_rgba(1, 0.45, 0.65, 1.0, 0.0)
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ADD)
        ctx.set_source(g)
        ctx.paint()
        ctx.restore()
        rrect(ctx, cx - 170, 930, 340, 260, 30)
        fill_stroke(ctx, hexc('#121218'), OUTL, 6)
        rrect(ctx, cx - 150, 950, 300, 200, 18)
        setc(ctx, hexc('#9cc3ff'))
        ctx.fill()
        glow(ctx, cx, 960, 300, hexc('#7fb2ff'), 0.5)
    if kw.get('sparkle'):
        for i in range(4):
            ph = (t * 0.8 + i * 0.25) % 1
            x, y = cx + 340 + i * 60, 260 + i * 90
            s = math.sin(math.pi * ph) * 34
            poly(ctx, [(x, y - s), (x + s * 0.3, y - s * 0.3), (x + s, y), (x + s * 0.3, y + s * 0.3),
                       (x, y + s), (x - s * 0.3, y + s * 0.3), (x - s, y), (x - s * 0.3, y - s * 0.3)])
            setc(ctx, hexc('#ffe08a'))
            ctx.fill()
    if kw.get('expr') in ('shock', 'scream') and lt < 0.9:
        for k in range(7):
            a = -math.pi / 2 + (k - 3) * 0.33
            r0 = 360 + 20 * math.sin(lt * 30 + k)
            ctx.move_to(cx + math.cos(a) * r0, 470 + math.sin(a) * r0)
            ctx.line_to(cx + math.cos(a) * (r0 + 90), 470 + math.sin(a) * (r0 + 90))
        setc(ctx, (1, 1, 1) if L < 0.5 else OUTL, 0.95)
        ctx.set_line_width(12)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    red = key_or(kw, 'red', lt, 0.0)
    if red > 0:
        g = cairo.RadialGradient(960, 540, 300, 960, 540, 1150)
        g.add_color_stop_rgba(0, 1, 0, 0, 0)
        g.add_color_stop_rgba(1, 0.9, 0, 0.05, 0.6 * red)
        ctx.set_source(g)
        ctx.paint()


def clock_spin(ctx, world, t, lt, kw):
    mins = key_or(kw, 'mins', lt, 0.0)
    panic = key_or(kw, 'panic', lt, 0.0)
    calm = mix(hexc('#1d2b53'), hexc('#cf2b3a'), panic)
    ctx.set_source_rgb(*calm)
    ctx.paint()
    # speed lines
    rnd = random.Random(int(t * 30))
    for _ in range(int(10 + 30 * panic)):
        a = rnd.uniform(0, 2 * math.pi)
        r0 = rnd.uniform(450, 700)
        ctx.move_to(960 + math.cos(a) * r0, 540 + math.sin(a) * r0)
        ctx.line_to(960 + math.cos(a) * (r0 + rnd.uniform(80, 250)), 540 + math.sin(a) * (r0 + 200))
    setc(ctx, (1, 1, 1), 0.25)
    ctx.set_line_width(6)
    ctx.stroke()
    jx = math.sin(t * 80) * 14 * panic
    cx, cy, R = 960 + jx, 540, 400
    ellipse(ctx, cx + 12, cy + 16, R, R)
    setc(ctx, (0, 0, 0), 0.3)
    ctx.fill()
    ellipse(ctx, cx, cy, R, R)
    fill_stroke(ctx, (0.98, 0.97, 0.94), OUTL, 14)
    ellipse(ctx, cx, cy, R - 30, R - 30)
    setc(ctx, hexc('#30344f'))
    ctx.set_line_width(6)
    ctx.stroke()
    for i in range(60):
        a = i / 60 * 2 * math.pi
        r1 = R - 50 if i % 5 else R - 85
        ctx.move_to(cx + math.cos(a) * (R - 40), cy + math.sin(a) * (R - 40))
        ctx.line_to(cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        setc(ctx, OUTL)
        ctx.set_line_width(10 if i % 5 == 0 else 4)
        ctx.stroke()
    for n in (12, 3, 6, 9):
        a = (n / 12) * 2 * math.pi - math.pi / 2
        text_center(ctx, str(n), cx + math.cos(a) * (R - 140), cy + math.sin(a) * (R - 140) + 26, 76, OUTL)
    h = 7 + mins / 60
    ma = mins / 60 * 2 * math.pi - math.pi / 2
    ha = h / 12 * 2 * math.pi - math.pi / 2
    speed = abs(key_or(kw, 'mins', lt + 0.05, 0) - mins) / 0.05
    if speed > 15:
        ctx.move_to(cx, cy)
        ctx.arc_negative(cx, cy, R - 90, ma, ma - min(2.5, speed / 60))
        ctx.close_path()
        setc(ctx, hexc('#ff5a36'), 0.25)
        ctx.fill()
    for ang, ln, w, col in ((ha, R * 0.5, 26, OUTL), (ma, R * 0.78, 16, hexc('#ff5a36'))):
        ctx.move_to(cx, cy)
        ctx.line_to(cx + math.cos(ang) * ln, cy + math.sin(ang) * ln)
        setc(ctx, col)
        ctx.set_line_width(w)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()
    ellipse(ctx, cx, cy, 28, 28)
    fill_stroke(ctx, OUTL, OUTL, 2)
    text_center(ctx, f"7:{int(mins):02d}", cx, cy + R + 110, 96, (1, 1, 1))


def chaos(ctx, world, t, lt, kw):
    life_desk = engine.SCENES['desk']
    life_desk(ctx, world, t, lt, dict(action='stress', light=0.9))
    # buzzing phone on the desk
    bx = 1250 + math.sin(t * 90) * 10
    rrect(ctx, bx - 80, 760, 160, 46, 10)
    fill_stroke(ctx, hexc('#111111'), OUTL, 4)
    rrect(ctx, bx - 70, 766, 140, 34, 6)
    setc(ctx, hexc('#ff4b5c'))
    ctx.fill()
    for s in (-1, 1):
        for k in (0, 1):
            ctx.move_to(bx + s * (110 + k * 30), 740)
            ctx.line_to(bx + s * (120 + k * 30), 820)
    setc(ctx, OUTL)
    ctx.set_line_width(6)
    ctx.stroke()
    # flying papers
    rnd = random.Random(3)
    for i in range(14):
        sx, sy = rnd.uniform(500, 1300), rnd.uniform(700, 790)
        vx, vy = rnd.uniform(-900, 900), rnd.uniform(-1100, -500)
        rot = rnd.uniform(-6, 6)
        tt = (lt * 0.9 + rnd.random()) % 1.4
        x = sx + vx * tt
        y = sy + vy * tt + 900 * tt * tt
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(rot * tt)
        ctx.rectangle(-60, -80, 120, 160)
        fill_stroke(ctx, (1, 1, 1), OUTL, 4)
        for j in range(4):
            ctx.rectangle(-40, -55 + j * 30, 80, 8)
        setc(ctx, hexc('#9aa0b8'))
        ctx.fill()
        ctx.restore()
    pulse = 0.5 + 0.5 * math.sin(lt * 2 * math.pi * 2)
    g = cairo.RadialGradient(960, 540, 250, 960, 540, 1100)
    g.add_color_stop_rgba(0, 1, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.9, 0, 0.05, 0.35 + 0.3 * pulse)
    ctx.set_source(g)
    ctx.paint()


def rewind_seq(ctx, world, t, lt, kw):
    srcs = kw['srcs']
    d = kw['dur']
    n = len(srcs)
    idx = min(n - 1, int(lt / d * n))
    frac = lt / d * n - idx
    s = srcs[idx]
    ll = s.dur * (1 - frac)
    engine.SCENES[s.kind](ctx, world, s.start + ll, ll, s.kw)
    setc(ctx, (0.05, 0.05, 0.2), 0.35)
    ctx.paint()
    rnd = random.Random(int(lt * 30))
    for _ in range(10):
        y = rnd.uniform(0, SH)
        ctx.rectangle(0, y, SW, rnd.uniform(3, 16))
        setc(ctx, (1, 1, 1), rnd.uniform(0.08, 0.3))
        ctx.fill()
    for i in range(2):
        x = 820 + i * 140
        poly(ctx, [(x + 140, 400), (x, 540), (x + 140, 680)])
        setc(ctx, (1, 1, 1), 0.9)
        ctx.fill()


def split(ctx, world, t, lt, kw):
    a = smooth(lt / 0.25)
    ctx.save()
    ctx.rectangle(0, 0, 960, SH)
    ctx.clip()
    ctx.translate(-380 - (1 - a) * 300, 0)
    chaos(ctx, world, t, lt, {})
    ctx.restore()
    ctx.save()
    ctx.rectangle(960, 0, 960, SH)
    ctx.clip()
    ctx.translate(560 + (1 - a) * 300, 0)
    face_scene(ctx, world, t, lt, dict(expr='proud', light=1.0, sparkle=True))
    ctx.restore()
    ctx.rectangle(950, 0, 20, SH)
    setc(ctx, (1, 1, 1))
    ctx.fill()
    pop_ = 1 + 0.4 * (1 - smooth((lt - 0.2) / 0.25))
    if lt > 0.2:
        ellipse(ctx, 960, 540, 90 * pop_, 90 * pop_)
        fill_stroke(ctx, hexc('#ffcf3f'), OUTL, 8)
        text_center(ctx, 'VS', 960, 565, 72 * pop_, OUTL)
    for x, label, col in ((480, 'PHONE FIRST', '#e0393e'), (1440, 'PHONE LAST', '#22a356')):
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(64)
        w = ctx.text_extents(label).x_advance
        rrect(ctx, x - w / 2 - 40, 40, w + 80, 100, 50)
        fill_stroke(ctx, hexc(col), OUTL, 6)
        ctx.move_to(x - w / 2, 113)
        setc(ctx, (1, 1, 1))
        ctx.show_text(label)


engine.SCENES.update(phone_close=phone_close, face_scene=face_scene, clock_spin=clock_spin, chaos=chaos,
                     rewind_seq=rewind_seq, split=split)


# ------------------------------------------------------------------ music
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def _t(d):
    return np.arange(int(d * SR)) / SR


def saw(f, d, detune=0.0):
    t = _t(d)
    return 2 * ((t * f * (1 + detune)) % 1) - 1


def kick():
    t = _t(0.4)
    f = 45 + 120 * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2)
    s[:200] += np.linspace(0.6, 0, 200) * noise(200)
    return np.tanh(s * 1.5) * 0.9


def snare():
    t = _t(0.25)
    return (bp(noise(len(t)), 1200, 7000) * np.exp(-t / 0.09) * 0.7 +
            np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04) * 0.5)


def clap():
    t = _t(0.3)
    e = np.zeros(len(t))
    for o in (0, 0.012, 0.024):
        e += np.where(t >= o, np.exp(-np.clip(t - o, 0, None) / (0.012 if o < 0.02 else 0.12)), 0)
    return bp(noise(len(t)), 900, 5000) * e * 0.55


def hat(open_=False):
    t = _t(0.25 if open_ else 0.06)
    return hp(noise(len(t)), 7000) * np.exp(-t / (0.09 if open_ else 0.018)) * 0.28


def pluck(f, d=0.35):
    t = _t(d)
    s = saw(f, d) + 0.5 * saw(f, d, 0.004)
    return lp(s, 2800) * np.exp(-t / 0.13) * 0.22


def bass(f, d):
    t = _t(d)
    s = saw(f, d) + 0.6 * np.sin(2 * np.pi * f * t)
    return lp(s, 260, 4) * env_adsr(len(t), 0.005, 0.04) * 0.5


def pad(freqs, d, cutoff=900):
    s = np.zeros(int(d * SR))
    for f in freqs:
        for dt in (-0.006, 0.0, 0.007):
            s += saw(f, d, dt)
    s = lp(s, cutoff, 2) * 0.03
    return s * env_adsr(len(s), 0.25, 0.3)


def place(buf, sig, t0, g=1.0):
    i = int(round(t0 * SR))
    if i >= len(buf) or i < 0:
        return
    seg = sig[:len(buf) - i]
    buf[i:i + len(seg)] += seg * g


def music_tense(dur, riser_from):
    """A-minor pulse: ticking clock hats, 8th-note bass, dark pad, filter riser."""
    buf = np.zeros(int(dur * SR) + SR)
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (50, [50, 53, 57]), (52, [52, 56, 59])]
    bar = 4 * BEAT
    nb = int(dur / bar) + 1
    for b in range(nb):
        root, ch = prog[b % 4]
        t0 = b * bar
        place(buf, pad([midi(n) for n in ch], bar + 0.2, 700 + 1500 * clamp((t0 - riser_from) / 2)), t0)
        for e in range(8):
            place(buf, bass(midi(root - 24), BEAT / 2 * 0.9), t0 + e * BEAT / 2, 0.9)
        for q in range(4):
            place(buf, tick(q % 2 == 0), t0 + q * BEAT, 0.9)
            if t0 + q * BEAT >= riser_from:
                place(buf, kick(), t0 + q * BEAT, 0.8)
            if t0 >= 2 * bar:
                place(buf, hat(), t0 + q * BEAT + BEAT / 2, 0.8)
    return buf[:int(dur * SR)]


def music_happy(dur):
    """C-major four-on-the-floor: kick, clap, hats, bass, plucked arpeggio, pad."""
    buf = np.zeros(int(dur * SR) + SR)
    prog = [(48, [60, 64, 67, 72]), (43, [59, 62, 67, 71]), (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69])]
    bar = 4 * BEAT
    for b in range(int(dur / bar) + 1):
        root, ch = prog[b % 4]
        t0 = b * bar
        place(buf, pad([midi(n) for n in ch[:3]], bar + 0.2, 1400), t0, 0.8)
        for q in range(4):
            place(buf, kick(), t0 + q * BEAT)
            if q % 2 == 1:
                place(buf, clap(), t0 + q * BEAT)
            place(buf, hat(q == 3), t0 + q * BEAT + BEAT / 2)
        for e in range(8):
            place(buf, bass(midi(root - 12 if e % 2 else root - 24), BEAT / 2 * 0.8), t0 + e * BEAT / 2, 0.8)
        pattern = [0, 2, 1, 3, 2, 1, 3, 2]
        for e, k in enumerate(pattern):
            place(buf, pluck(midi(ch[k] + 12)), t0 + e * BEAT / 2, 0.9)
    # light sidechain pump
    tt = np.arange(len(buf)) / SR
    pump = 0.6 + 0.4 * np.clip((tt % BEAT) / 0.18, 0, 1)
    return (buf * pump)[:int(dur * SR)]


def tape_stop(sig, d=0.45):
    n = int(d * SR)
    head, tail = sig[:-n], sig[-n:]
    rate = np.linspace(1, 0, n) ** 1.5
    idx = np.cumsum(rate)
    idx = np.clip(idx, 0, n - 1)
    out = np.interp(idx, np.arange(n), tail) * np.linspace(1, 0.2, n)
    return np.concatenate([head, out])


# ------------------------------------------------------------------- sfx
def swipe():
    t = _t(0.16)
    s = bp(noise(len(t)), 1800, 8000) * np.sin(np.pi * t / 0.16) ** 2
    f = 900 + 3000 * t / 0.16
    s += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.16) ** 2 * 0.15
    return s * 0.5


def notif():
    out = np.zeros(int(0.35 * SR))
    for o, f in ((0, 1568), (0.09, 2093)):
        t = _t(0.25)
        place(out, (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t / 0.08), o)
    return out * 0.4


def buzz(d=0.7):
    t = _t(d)
    s = np.sign(np.sin(2 * np.pi * 170 * t)) * (np.sin(2 * np.pi * 7 * t) > -0.2)
    return lp(s, 900) * 0.3 * env_adsr(len(t), 0.01, 0.05)


def record_scratch():
    t = _t(0.45)
    f = 700 + 500 * np.sin(2 * np.pi * 3.2 * t + 1.0)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 + bp(noise(len(t)), 600, 3000) * 0.6
    return lp(s, 4000) * env_adsr(len(t), 0.005, 0.1) * 0.6


def impact():
    t = _t(1.4)
    sub = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.5)
    crack = lp(noise(len(t)), 3500) * np.exp(-t / 0.08)
    return np.tanh((sub * 1.2 + crack * 0.6) * 1.3) * 0.9


def riser(d):
    t = _t(d)
    u = t / d
    nz = noise(len(t))
    s = lp(nz, 800) * (1 - u) + bp(nz, 1500, 6000) * u
    f = 200 + 1400 * u ** 2
    s += np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return s * u ** 2 * 0.5


def reverse_cymbal(d=1.0):
    t = _t(d)
    return hp(noise(len(t)), 4000) * (t / d) ** 3 * 0.6


def drawer_slide(d=0.35):
    t = _t(d)
    return lp(noise(len(t)), 1200) * np.sin(np.pi * t / d) * 0.5


def boing():
    t = _t(0.4)
    f = 180 + 500 * (t / 0.4) + 40 * np.sin(2 * np.pi * 14 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.3) * 0.45


def sparkle():
    out = np.zeros(int(1.0 * SR))
    for i, n in enumerate((84, 88, 91, 96, 100)):
        t = _t(0.5)
        place(out, np.sin(2 * np.pi * midi(n) * t) * np.exp(-t / 0.15) * 0.25, i * 0.06)
    return out


def cut_whoosh():
    return whoosh(0.35, 0.65) * 0.5


def clock_ticks(d, accel=True):
    out = np.zeros(int(d * SR) + SR)
    tt, step = 0.0, 0.25
    hi = True
    while tt < d:
        place(out, tick(hi), tt, 0.8)
        hi = not hi
        tt += step
        if accel:
            step = max(0.035, step * 0.9)
    return out[:int(d * SR)]
