"""Shared skeleton for the 'frustrated by another driver' series (cinematic square, built on cinetemplate.py).

Every episode = 8 beats (~22 s): hook flash-forward, establishing heli + location, the annoying move, hero's angry
face (dash cam), STEP 1, STEP 2, STEP 3 / fact badge, end card.  An episode supplies the traffic plan, the shot list,
the texts and optional extra SFX; frustkit builds the overlays, the base sound and the checks.
"""
from cinetemplate import *

HERO_COL = '#e23b3b'


def hero_car(x_key, s_key, expr_fn, blink=None, za=0.0, **kw):
    return Veh(x_key, s_key, 0.0, za, HERO_COL, occ=occ_of('hero', expr_fn), blink=blink, **kw)


def lane_key(*pts):
    """lane_key((t, lane), ...) -> x Key; lane index or float x."""
    return Key([(t, LANES[l] if isinstance(l, int) else l) for t, l in pts])


def spd(*pts):
    return Key(list(pts), 'lin')


def blinks(*spans):
    """blinks((t0, t1, 'L'|'R'), ...)."""
    def f(t):
        for a, b, sd in spans:
            if a <= t < b and ((t - a) * 1.6) % 1 < 0.5:
                return sd
        return None
    return f


def filler(lanes_z, speed=V, cols=None):
    cols = cols or COLS
    return [Veh(LANES[l], speed if callable(speed) else const(speed), 0.0, z, cols[i % len(cols)]) for i, (l, z) in enumerate(lanes_z)]


def oncoming(n=40, z0=-300):
    return [Rev(-5.0 if i % 2 else -11.0, z0 + 47 * i, COLS[(i * 3) % 10]) for i in range(n)]


class Episode:
    """defs: list of 8 (end, kind, kw). texts: dict with keys hook, loc, c (list of 8 captions or None),
    steps {shot: n}, badge (shot, text, color), end (line1, line2)."""

    def __init__(self, name, title, city, hero, agents, defs, texts, dur, tm=None, sfx=None, extra_overlays=()):
        EP.hero = hero
        EP.shadows = [a for a in [hero] + agents if hasattr(a, 'ext')]
        if tm:
            EP.tm = tm
        self.name, self.hero, self.agents, self.dur, self.sfx = name, hero, agents, dur, sfx
        self.world = make_world(city, hero, agents)
        self.video = make_video(title, self.world, defs, dur)
        v = self.video
        S, E = v.S, v.E
        ov = [(0.0, E[0], big_text(texts['hook'], 300, texts.get('hook_size', 112), hexc('#ffd23f'), 0.15, True)),
              (S[1], E[1], location_tag(texts['loc']))]
        for i, c in enumerate(texts['c']):
            if c:
                txt, size = (c, 74) if isinstance(c, str) else c
                ov.append((S[i] + 0.2, E[i], sq_caption(txt, size)))
        for i, n in texts.get('steps', {}).items():
            ov.append((S[i], E[i], step_badge(n)))
        if texts.get('badge'):
            i, txt, col = texts['badge']
            ov.append((S[i], E[i], badge(txt, col)))
        ov.append((S[-1] + 0.2, E[-1], end_card(*texts['end'])))
        v.overlays = ov + list(extra_overlays)

    def sound(self):
        v = self.video
        S, E = v.S, v.E
        m = Mixer(self.dur)
        highway_bed(m, self.dur)
        m.add(braam(2.2, 49), 0.05, 0.7)
        m.add(heartbeat(3, 118), 0.2, 0.5)
        m.add(heartbeat(3, 125), S[3] + 0.1, 0.55)
        for i in (4, 5, 6):
            m.add(pop(), S[i] + 0.15, 0.55)
        m.add(whoosh(0.5, 0.4), S[6] - 0.1, 0.4)
        m.add(success_jingle(), S[-1] + 0.3, 0.8)
        if self.sfx:
            self.sfx(m, S, E)
        return m.out(self.dur)

    def verify(self, extra=None):
        names = [('HERO', self.hero)] + [(f'A{i}', a) for i, a in enumerate(self.agents) if isinstance(a, Track)]
        verify_gaps(names, 0.0, self.dur + 2)
        if extra:
            extra()
        v = self.video
        for i, s in enumerate(v.shots):
            print(i, s.kind, s.kw.get('cam', ''), round(v.S[i], 2), '-', round(v.E[i], 2), 'world', round(EP.tm.wt(v.S[i]), 2))

    def run(self, extra_verify=None):
        run(self.video, self.sound, lambda: self.verify(extra_verify), self.name + '.mp4')
