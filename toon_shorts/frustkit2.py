"""Series v2 'frustrated by another driver': situation -> what you WANT to do -> consequence (red X) -> REWIND ->
the right way (green tick) -> end card.  Two worlds per episode (WRONG / RIGHT timelines share everything before the
branch).  Shots are dicts:  dict(end=, kind=, world='w'|'r', cam kw..., cap=, x=, ok=, step=, hook=, loc=, badge=,
rewind=(a, b), end_card=(l1, l2), sfx=[(local t, fn)])
"""
from frustkit import *


class Story:
    def __init__(self, name, title, city, hero_w, hero_r, others_w, others_r, shots, dur, tm=None, sfx=None, unit='mph'):
        EP.unit = unit
        if tm:
            EP.tm = tm
        EP.hero = hero_r
        self.name, self.dur, self.sfx_fn = name, dur, sfx
        self.hw, self.hr = hero_w, hero_r
        self.ow, self.orr = others_w, others_r
        allag = [hero_w, hero_r] + others_w + others_r
        EP.shadows = []
        self.ww = make_world(city, hero_w, others_w)
        self.wr = make_world(city, hero_r, others_r)
        self._sh_w = [a for a in [hero_w] + others_w if hasattr(a, 'ext')]
        self._sh_r = [a for a in [hero_r] + others_r if hasattr(a, 'ext')]
        defs = []
        for sh in shots:
            kw = {k: v for k, v in sh.items() if k not in ('end', 'kind', 'world', 'cap', 'x', 'ok', 'step', 'hook', 'loc', 'badge',
                                                           'end_card', 'sfx', 'capsize')}
            w = sh.get('world', 'r')
            kw['world'] = self.ww if w == 'w' else self.wr
            kw['_w'] = w
            if sh['kind'] in ('interior_mirror', 'dash_face') and 'car' not in kw:
                kw['car'] = hero_w if w == 'w' else hero_r
            defs.append((sh['end'], sh['kind'], kw))
        self.video = make_video(title, self.wr, defs, dur)
        v = self.video
        S, E = v.S, v.E
        ov = []
        for i, sh in enumerate(shots):
            if sh.get('hook'):
                ov.append((S[i], E[i], big_text(sh['hook'], 300, sh.get('hook_size', 110), hexc('#ffd23f'), 0.1, True)))
            if sh.get('loc'):
                ov.append((S[i], E[i], location_tag(sh['loc'])))
            if sh.get('cap'):
                ov.append((S[i] + 0.15, E[i], sq_caption(sh['cap'], sh.get('capsize', 74))))
            if sh.get('x'):
                ov.append((S[i] + sh.get('vdelay', 0.2), E[i], verdict('x', sh['x'])))
            if sh.get('ok'):
                ov.append((S[i] + 0.15, E[i], verdict('ok', sh['ok'])))
            if sh.get('step'):
                ov.append((S[i], E[i], step_badge(sh['step'])))
            if sh.get('badge'):
                ov.append((S[i], E[i], badge(*sh['badge'])))
            if sh.get('end_card'):
                ov.append((S[i] + 0.2, E[i], end_card(*sh['end_card'])))
        v.overlays = ov
        self.shots = shots
        # shadows follow the world of the shot being drawn
        orig = v.frame

        def frame(ctx, t, _o=orig):
            s_ = v.shot_at(t)
            EP.shadows = self._sh_w if s_.kw.get('_w') == 'w' else self._sh_r
            return _o(ctx, t)
        v.frame = frame

    def sound(self):
        v = self.video
        S, E = v.S, v.E
        m = Mixer(self.dur)
        highway_bed(m, self.dur)
        m.add(braam(2.2, 49), 0.05, 0.7)
        for i, sh in enumerate(self.shots):
            if sh.get('rewind'):
                m.add(rewind_sfx(E[i] - S[i]), S[i], 0.8)
            if sh.get('x'):
                m.add(impact(), S[i] + 0.2, 0.25)
            if sh.get('ok'):
                m.add(chime(), S[i] + 0.2, 0.35)
            if sh.get('step'):
                m.add(pop(), S[i] + 0.1, 0.5)
            if sh.get('end_card'):
                m.add(success_jingle(), S[i] + 0.3, 0.8)
            if sh['kind'] == 'dash_face':
                m.add(heartbeat(2, 120), S[i] + 0.1, 0.5)
            if sh['kind'] == 'pedal_close':
                m.add(whoosh(0.4, 0.3), S[i] + sh.get('hit', 0.6) - 0.3, 0.6)
                m.add(impact(), S[i] + sh.get('hit', 0.6), 0.45)
        if self.sfx_fn:
            self.sfx_fn(m, S, E)
        return m.out(self.dur)

    def verify(self, extra=None):
        for label, hero, others in (('WRONG', self.hw, self.ow), ('RIGHT', self.hr, self.orr)):
            print('---', label)
            names = [('HERO', hero)] + [(f'A{i}', a) for i, a in enumerate(others) if isinstance(a, Track)]
            verify_gaps(names, 0.0, self.dur + 2, top=6)
        if extra:
            extra()
        v = self.video
        for i, s in enumerate(v.shots):
            print(i, s.kind, s.kw.get('cam', ''), s.kw.get('_w'), round(v.S[i], 2), '-', round(v.E[i], 2), 'world', round(EP.tm.wt(v.S[i]), 2))

    def run(self, extra=None):
        run(self.video, self.sound, lambda: self.verify(extra), self.name + '.mp4')


def layout(seq):
    """seq: [(duration, shot dict)] -> shot dicts with absolute 'end'."""
    out, t = [], 0.0
    for d, sh in seq:
        t += d
        sh = dict(sh)
        sh['end'] = round(t, 3)
        out.append(sh)
    return out
