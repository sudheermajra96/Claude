"""Cinematic ("Hollywood") sound-effects kit: realistic layered SFX + a mastered stereo mix. Sound effects only, no music.

  Mix2(dur)           stereo mixer with reverb sends, ducking, glue compression and a limiter on the master
                      .add(sig, t, gain, pan=0|array, verb=0.0, space='road')   sig mono or (n, 2) stereo
                      .duck(t0, t1, depth)    pull the beds down (e.g. right before an impact = "suck-out")
  beds                road_bed (tyre roar + wind, speed driven), cabin_bed (muffled interior), distant_traffic
  vehicles            engine(d, rpm_fn), passby(d, v, closest m, side) Doppler + air absorption,
                      tyre_screech(d), abs_judder(d), brake_squeal(d)
  impacts             car_crash(d) = sub thump + metal crumple + panel ring + glass + plastic debris clatter,
                      boom(d) trailer hit, sub_drop
  cinematic           whoosh2, riser2, braam2, heartbeat2, tinnitus, slowmo_in (time-stretch + low-pass),
                      relay_ticks (hazards / indicator), steam_hiss, chime2
Everything is synthesised with numpy/scipy (deterministic seeds) so renders are repeatable.
"""
import math

import numpy as np
from scipy import signal

SR = 44100
RNG = np.random.default_rng(11)


def _n(d):
    return max(1, int(d * SR))


def noise(n, seed=None):
    r = np.random.default_rng(seed) if seed is not None else RNG
    return r.standard_normal(n)


def pink(n, seed=None):
    w = np.fft.rfft(noise(n, seed))
    f = np.arange(len(w))
    f[0] = 1
    return np.fft.irfft(w / np.sqrt(f), n) * 12


def brown(n, seed=None):
    b = np.cumsum(noise(n, seed))
    b = signal.lfilter([1, -1], [1, -0.995], b)
    return b / (np.std(b) + 1e-9)


def _sos(kind, f, order=2):
    if kind == 'bp':
        lo, hi = max(10, f[0]), min(SR / 2 - 100, f[1])
        return signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
    return signal.butter(order, min(max(f, 10), SR / 2 - 100), kind, fs=SR, output='sos')


def lp(x, f, o=2):
    return signal.sosfilt(_sos('low', f, o), x)


def hp(x, f, o=2):
    return signal.sosfilt(_sos('high', f, o), x)


def bp(x, lo, hi, o=2):
    return signal.sosfilt(_sos('bp', (lo, hi), o), x)


def reson(x, f, q):
    b, a = signal.iirpeak(min(f, SR / 2 - 200), q, fs=SR)
    return signal.lfilter(b, a, x)


def tv_lp(x, cut, block=512):
    """Time-varying low-pass: cut is an array (Hz) per sample (block-wise one-pole, smooth enough)."""
    y = np.zeros_like(x)
    z = 0.0
    for i in range(0, len(x), block):
        c = float(np.mean(cut[i:i + block]))
        a = math.exp(-2 * math.pi * c / SR)
        seg, zi = signal.lfilter([1 - a], [1, -a], x[i:i + block], zi=[z * a])
        y[i:i + block] = seg
        z = seg[-1] if len(seg) else z
    return y


def env(n, a=0.01, r=0.1, hold=None):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def expdec(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def norm(x, peak=1.0):
    return x / (np.max(np.abs(x)) + 1e-9) * peak


def stretch(x, k):
    """Slow down by 1/k (k < 1 = slower + lower), works for mono or stereo."""
    n = int(len(x) / k)
    idx = np.arange(n) * k
    if x.ndim == 1:
        return np.interp(idx, np.arange(len(x)), x)
    return np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], 1)


# ------------------------------------------------------------------ reverb
_IR = {}


def _ir(space):
    if space in _IR:
        return _IR[space]
    p = {'road': (1.1, 2600, 0.012), 'cabin': (0.25, 3000, 0.002), 'hall': (2.6, 5000, 0.02), 'tail': (3.5, 3000, 0.03)}[space]
    T, cut, pre = p
    n = _n(T)
    out = []
    for s in (1, 2):
        r = noise(n, 100 + s) * np.exp(-6.9 * np.arange(n) / n)
        r = lp(r, cut)
        r[:int(pre * SR)] = 0
        if space == 'road':                         # one slap echo off buildings / barrier
            k = int(0.09 * SR)
            r[k:k + 200] += np.hanning(200) * 4.0
        out.append(r / np.sqrt(np.sum(r * r)))
    _IR[space] = out
    return out


def reverb(x, space='road'):
    L, R = _ir(space)
    m = x if x.ndim == 1 else x.mean(1)
    return np.stack([signal.fftconvolve(m, L)[:len(m)], signal.fftconvolve(m, R)[:len(m)]], 1)


# ------------------------------------------------------------------ mixer
class Mix2:
    def __init__(self, dur):
        self.dur = dur
        self.n = _n(dur) + SR * 4
        self.bus = np.zeros((self.n, 2))           # beds (ducked)
        self.fx = np.zeros((self.n, 2))            # foreground
        self.sends = {}
        self.duck_env = np.ones(self.n)

    def _place(self, buf, sig, i, gain, pan):
        if i >= self.n:
            return
        if sig.ndim == 1:
            s = sig[:self.n - i] * gain
            pan = np.full(len(s), float(pan)) if np.ndim(pan) == 0 else np.resize(np.asarray(pan, float), len(s))
            th = (pan + 1) * math.pi / 4
            buf[i:i + len(s), 0] += s * np.cos(th)
            buf[i:i + len(s), 1] += s * np.sin(th)
        else:
            s = sig[:self.n - i] * gain
            buf[i:i + len(s)] += s

    def add(self, sig, t, gain=1.0, pan=0.0, verb=0.0, space='road', bed=False):
        i = max(0, int(t * SR))
        self._place(self.bus if bed else self.fx, sig, i, gain, pan)
        if verb > 0:
            if space not in self.sends:
                self.sends[space] = np.zeros((self.n, 2))
            self._place(self.sends[space], sig, i, gain * verb, pan)

    def duck(self, t0, t1, depth=0.25, rel=0.6):
        """Beds dip to `depth` between t0 and t1, recover over rel s."""
        a, b, r = int(t0 * SR), int(t1 * SR), int(rel * SR)
        self.duck_env[a:b] = np.minimum(self.duck_env[a:b], depth)
        if b < self.n:
            m = min(r, self.n - b)
            self.duck_env[b:b + m] = np.minimum(self.duck_env[b:b + m], depth + (1 - depth) * np.linspace(0, 1, m))

    def out(self):
        de = lp(self.duck_env, 30, 1)
        mix = self.bus * de[:, None] + self.fx
        for space, s in self.sends.items():
            mix += reverb(s, space) * 0.9
        n = _n(self.dur)
        mix = mix[:n]
        # glue compressor (RMS, 3:1 above -18 dB) + soft limiter
        lvl = np.sqrt(lp(np.mean(mix ** 2, 1), 8, 1).clip(1e-12))
        lvl /= (np.max(lvl) + 1e-9)
        db = 20 * np.log10(lvl + 1e-9)
        gr = np.where(db > -10, (db + 10) * (1 - 1 / 2.0), 0.0)
        mix *= (10 ** (-gr / 20))[:, None]
        mix = hp(mix.T, 25).T
        mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.15) / math.tanh(1.15)
        fade = np.ones(n)
        fade[-int(0.3 * SR):] = np.linspace(1, 0, int(0.3 * SR))
        return mix * fade[:, None] * 0.93


# ------------------------------------------------------------------ beds
def road_bed(d, speed=lambda t: 29.0, seed=1):
    """Exterior: tyre roar on asphalt (brown/pink noise, brightness + level follow speed) + gusty wind, stereo."""
    n = _n(d)
    tt = np.arange(n) / SR
    sp = np.array([speed(t) for t in np.arange(0, d + 0.1, 0.05)])
    v = np.interp(tt, np.arange(0, d + 0.1, 0.05)[:len(sp)], sp)
    out = []
    for c in range(2):
        roar = tv_lp(brown(n, seed + c) * 0.6 + pink(n, seed + 10 + c) * 0.25, 180 + v * 22)
        hiss = bp(noise(n, seed + 20 + c), 1500, 5000) * 0.04 * (v / 30)
        gust = lp(noise(n, seed + 30 + c), 500) * (0.5 + 0.5 * np.sin(2 * np.pi * (0.13 + 0.03 * c) * tt + c) ** 2) * 0.35
        out.append((roar + hiss) * (0.25 + v / 40) + gust)
    return norm(np.stack(out, 1), 0.5)


def cabin_bed(d, speed=lambda t: 29.0, rpm=2200):
    """Interior: muffled road + engine hum + a little seat/body rumble."""
    n = _n(d)
    tt = np.arange(n) / SR
    r = lp(brown(n, 5), 160) * 0.8
    f0 = rpm / 60 * 2
    hum = sum(np.sin(2 * np.pi * f0 * k * tt + k) / k ** 1.3 for k in range(1, 6)) * 0.25
    s = norm(r + lp(hum, 400), 0.45)
    return np.stack([s, np.roll(s, 300)], 1)


def distant_traffic(d, seed=4):
    n = _n(d)
    out = lp(brown(n, seed), 400) * 0.6
    for k in range(int(d / 3)):
        i = int((k * 3 + 1.0) * SR)
        p = passby(3.0, 28, 40, (-1) ** k)
        m = min(len(p), n - i)
        if m > 0:
            out[i:i + m] += p[:m].mean(1) * 0.5
    return norm(out, 0.3)


# ------------------------------------------------------------------ vehicles
def engine(d, rpm_fn=lambda u: 2200, load=0.6, cyl=4, seed=3):
    n = _n(d)
    tt = np.arange(n) / SR
    g = np.arange(0, d + 0.05, 0.02)
    rpm = np.interp(tt, g, [rpm_fn(u) for u in g])
    fire = rpm / 60 * cyl / 2
    jitter = 1 + 0.01 * lp(noise(n, seed), 20)
    ph = 2 * np.pi * np.cumsum(fire * jitter) / SR
    s = sum(np.sin(k * ph + 0.3 * k) * (1 / k ** (1.2 - 0.5 * load)) for k in range(1, 14))
    intake = bp(noise(n, seed + 1), 300, 1800) * (0.5 + 0.5 * np.sin(ph)) ** 4 * load
    return norm(lp(np.tanh(s * (0.8 + load)), 3000) + intake * 0.4, 0.6)


def passby(d=2.0, v=29.0, closest=4.0, side=1, f0=95.0, seed=6):
    """Doppler pass-by centred at d/2: tyre roar + engine tone, 1/r level, air absorption, stereo pan."""
    n = _n(d)
    tt = np.arange(n) / SR - d / 2
    x = v * tt
    r = np.sqrt(x * x + closest ** 2)
    vr = v * x / r                                  # radial speed (+ = receding)
    dop = 343.0 / (343.0 + vr)
    ph = 2 * np.pi * np.cumsum(f0 * dop) / SR
    tone = sum(np.sin(k * ph) / k for k in range(1, 8)) * 0.35
    roar = bp(noise(n, seed), 120, 6000) * 1.0
    src = tone + roar
    amp = (closest / r) ** 1.1
    cut = 900 + 9000 * (closest / r)
    s = tv_lp(src, cut) * amp
    pan = np.clip(x / (abs(x) + closest) * side, -1, 1) * 0.9
    th = (pan + 1) * math.pi / 4
    return norm(np.stack([s * np.cos(th), s * np.sin(th)], 1), 0.8)


def tyre_screech(d=1.6, seed=8, f=900.0):
    """Rubber squeal: several narrow resonances with random pitch wobble + scrub noise, rising then dying."""
    n = _n(d)
    tt = np.arange(n) / SR
    base = noise(n, seed)
    s = np.zeros(n)
    wob = 1 + 0.05 * lp(noise(n, seed + 1), 6) / 0.3
    for k, (fr, q, a) in enumerate(((f, 25, 1.0), (f * 1.52, 30, 0.6), (f * 2.1, 35, 0.35), (f * 0.62, 20, 0.4))):
        ph = 2 * np.pi * np.cumsum(fr * wob) / SR
        s += np.sin(ph + k) * a * (0.6 + 0.4 * lp(np.abs(noise(n, seed + 3 + k)), 15) / 0.4)
    s = s * 0.5 + reson(base, f, 6) * 0.5
    scrub = bp(base, 200, 2500) * 0.35
    e = np.minimum(1, tt / 0.08) * np.minimum(1, (d - tt) / 0.25)
    return norm((s + scrub) * e, 0.85)


def abs_judder(d=1.2, seed=9):
    n = _n(d)
    tt = np.arange(n) / SR
    g = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 15 * tt))) * 0.8 + 0.2
    return norm(bp(noise(n, seed), 150, 1500) * lp(g, 60) * np.minimum(1, (d - tt) / 0.2), 0.5)


def brake_squeal(d=1.4, f=2600, seed=10):
    n = _n(d)
    tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * tt + 3 * lp(noise(n, seed), 8)) * 0.5 + reson(noise(n, seed + 1), f, 40) * 0.3
    return norm(s * np.minimum(1, tt / 0.15) * np.minimum(1, (d - tt) / 0.3), 0.4)


# ------------------------------------------------------------------ impacts
def sub_drop(d=1.2, f0=70, f1=28):
    n = _n(d)
    tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt / 0.15)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * expdec(n, 0.35)


def glass(d=1.3, seed=12, count=60):
    n = _n(d)
    out = np.zeros(n)
    r = np.random.default_rng(seed)
    out[:int(0.04 * SR)] += hp(noise(int(0.04 * SR), seed), 2000) * expdec(int(0.04 * SR), 0.008) * 3.0   # crack
    for k in range(count):
        i = int(r.exponential(0.18) * SR)
        if i >= n - 3000:
            continue
        f = r.uniform(2500, 9000)
        m = int(r.uniform(0.02, 0.09) * SR)
        tt = np.arange(m) / SR
        out[i:i + m] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / r.uniform(0.008, 0.03)) * r.uniform(0.2, 1.0)
    return out


def debris(d=1.6, seed=13, count=30):
    """Plastic / metal bits bouncing and skittering on asphalt."""
    n = _n(d)
    out = np.zeros(n)
    r = np.random.default_rng(seed)
    for k in range(count):
        i = int(r.uniform(0.05, d * 0.85) * SR)
        m = int(0.03 * SR)
        if i + m >= n:
            continue
        f = r.uniform(600, 3500)
        out[i:i + m] += reson(noise(m, seed + k), f, 8) * expdec(m, 0.006) * r.uniform(0.3, 1.0)
    return out


def car_crash(d=2.4, seed=14):
    """Layered car-into-car impact: sub thump, metal crumple bursts, panel ring, glass, debris; stereo."""
    n = _n(d)
    tt = np.arange(n) / SR
    thump = sub_drop(d, 80, 32) * 1.4 + lp(noise(n, seed), 250) * expdec(n, 0.06) * 2.0
    crunch = np.zeros(n)
    r = np.random.default_rng(seed)
    for k in range(14):                                  # crumple: many short resonant metal bursts in 0.35 s
        i = int(r.uniform(0, 0.35) * SR)
        m = int(r.uniform(0.04, 0.12) * SR)
        b = noise(m, seed + k)
        burst = sum(reson(b, f, 12) for f in r.uniform(300, 2400, 4)) * expdec(m, 0.03)
        crunch[i:i + m] += burst * r.uniform(0.5, 1.2)
    crunch = np.tanh(crunch * 0.8) * 1.1
    ring = sum(np.sin(2 * np.pi * f * tt + p) * expdec(n, tau) for f, p, tau in
               ((347, 0.1, 0.5), (521, 1.3, 0.35), (873, 2.2, 0.25), (1312, 0.7, 0.18))) * 0.12
    g = glass(d, seed + 1) * 0.55
    deb = np.zeros(n)
    db = debris(d - 0.2, seed + 2) * 0.6
    deb[int(0.2 * SR):int(0.2 * SR) + len(db)] += db
    mono = thump * 0.9 + crunch * 0.9 + ring + deb
    L = mono + g * 0.9 + np.roll(deb, 400) * 0.3
    R = mono * 0.95 + np.roll(g, 220) * 0.9 + np.roll(deb, 900) * 0.3
    return norm(np.stack([L, R], 1), 1.0)


def boom(d=3.0, seed=15):
    """Trailer-style hit: sub drop + noise burst + long tail (use verb=0.5, space='tail')."""
    n = _n(d)
    s = sub_drop(d, 60, 24) * 1.5 + lp(noise(n, seed), 1200) * expdec(n, 0.08) * 0.8
    return norm(np.tanh(s * 1.2), 1.0)


# ------------------------------------------------------------------ cinematic
def whoosh2(d=0.8, up=True, seed=16):
    n = _n(d)
    tt = np.arange(n) / SR
    u = tt / d
    cut = 300 + 5000 * (u if up else 1 - u) ** 2
    e = np.sin(np.pi * u) ** 2
    s = tv_lp(noise(n, seed), cut) * e
    pan = np.linspace(-0.8, 0.8, n)
    th = (pan + 1) * math.pi / 4
    return norm(np.stack([s * np.cos(th), s * np.sin(th)], 1), 0.7)


def riser2(d=2.5, seed=17):
    n = _n(d)
    tt = np.arange(n) / SR
    u = tt / d
    s = tv_lp(noise(n, seed), 200 + 7000 * u ** 2) * u ** 2
    tone = np.sin(2 * np.pi * np.cumsum(60 + 240 * u ** 2) / SR) * u * 0.3
    return norm(s + tone, 0.7)


def braam2(d=2.5, f0=43.65):
    n = _n(d)
    tt = np.arange(n) / SR
    s = np.zeros(n)
    for f, a in ((f0, 1.0), (f0 * 2, 0.6), (f0 * 3, 0.35), (f0 * 1.498, 0.5)):
        ph = 2 * np.pi * f * tt + 0.2 * np.sin(2 * np.pi * 5.5 * tt)
        s += (np.sign(np.sin(ph)) * 0.35 + np.sin(ph)) * a
    k = np.exp(-tt / 0.35)
    s = lp(s, 2600) * k + lp(s, 450) * (1 - k)
    s += sub_drop(d, 55, 30) * 0.8
    return norm(s * env(n, 0.015, 0.9), 0.9)


def heartbeat2(beats=4, bpm=100):
    per = 60 / bpm
    n = _n(beats * per + 0.4)
    out = np.zeros(n)
    for b in range(beats):
        for off, a in ((0.0, 1.0), (0.22, 0.7)):
            i = int((b * per + off) * SR)
            m = int(0.18 * SR)
            tt = np.arange(m) / SR
            out[i:i + m] += np.sin(2 * np.pi * (50 + 25 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.05) * a
    return lp(out, 180)


def tinnitus(d=2.5, f=3900):
    n = _n(d)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / 0.05) * np.exp(-tt / (d * 0.45)) * 0.25


def slowmo_in(d=0.9):
    """Pitch-falling 'whoomp' that sells the drop into slow motion."""
    n = _n(d)
    tt = np.arange(n) / SR
    f = 30 + 200 * np.exp(-tt / 0.2)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdec(n, 0.3)
    s += tv_lp(noise(n, 18), 2000 * np.exp(-tt / 0.15) + 100) * expdec(n, 0.25) * 0.8
    return norm(s, 0.8)


def relay_ticks(t0, t1, rate=1.5):
    """Hazard / indicator relay: tick-tock pairs, returns [(t, sig)]."""
    out = []
    m = int(0.02 * SR)
    for k, t in enumerate(np.arange(t0, t1, 1 / (2 * rate))):
        f = 2400 if k % 2 == 0 else 1900
        s = reson(noise(m, 30 + k % 2), f, 6) * expdec(m, 0.003)
        out.append((t, norm(s, 0.5)))
    return out


def steam_hiss(d=4.0, seed=19):
    n = _n(d)
    tt = np.arange(n) / SR
    s = hp(noise(n, seed), 2500) * (0.6 + 0.4 * lp(noise(n, seed + 1), 3) / 0.2)
    return s * np.minimum(1, tt / 0.3) * np.exp(-tt / (d * 0.6)) * 0.3


def engine_tick(d=3.0, seed=20):
    """Hot engine pinging after a crash."""
    n = _n(d)
    out = np.zeros(n)
    r = np.random.default_rng(seed)
    for k in range(int(d * 3)):
        i = int(r.uniform(0, d - 0.05) * SR)
        m = int(0.015 * SR)
        out[i:i + m] += reson(noise(m, seed + k), r.uniform(3000, 6000), 10) * expdec(m, 0.002)
    return norm(out, 0.3)


def chime2(f=880):
    n = _n(2.0)
    tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * h * tt) * np.exp(-tt / (0.9 / h)) / h for h in (1, 2.01, 3.02, 4.2))
    return norm(s * np.minimum(1, tt / 0.004), 0.5)


def mono_to_st(x):
    return np.stack([x, x], 1)
