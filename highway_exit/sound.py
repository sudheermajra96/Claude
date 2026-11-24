"""Synthesize a natural-sounding highway soundtrack from events.json (written by rec.js)."""
import json, sys, numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR = 44100
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'events.json'))
T = d['T']; N = int(T * SR); t = np.arange(N) / SR
rng = np.random.default_rng(3)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def noise(n=N): return rng.standard_normal(n)
def norm(x): return x / (np.sqrt(np.mean(x ** 2)) + 1e-9)
v = np.interp(t, np.arange(len(d['v'])) / 100, d['v']); vn = v / 27.8
L = np.zeros(N); R = np.zeros(N)
def add(sig, gain, pan=0.0, start=0):
    end = min(N, start + len(sig)); sig = sig[:end - start] * gain
    L[start:end] += sig * np.sqrt((1 - pan) / 2); R[start:end] += sig * np.sqrt((1 + pan) / 2)

# 1) tyre roar on asphalt (low/mid rumble) — scales with speed, slight L/R decorrelation
slow = 1 + 0.12 * lp(noise(), 1.5, 1) / 0.02 * 0.02
for side, pan in ((noise(), -0.6), (noise(), 0.6)):
    roar = norm(bp(side, 70, 900)) * 0.55 + norm(bp(side, 900, 2600)) * 0.12
    add(roar * vn ** 1.4 * slow, 0.055, pan)
# 2) tyre hiss / road texture
add(norm(bp(noise(), 2500, 7000)) * vn ** 1.8, 0.012)
# 3) wind buffeting — low noise with slow gusts, ~v^2
gust = 0.7 + 0.3 * norm(lp(noise(), 0.6, 1)) * 0.5
add(norm(lp(noise(), 350)) * vn ** 2 * np.clip(gust, 0.3, 1.3), 0.028)
# 4) engine — harmonic hum following speed, softer while braking
f0 = 26 + v * 1.9
ph = 2 * np.pi * np.cumsum(f0) / SR
eng = sum(a * np.sin(k * ph + rng.random() * 6) for k, a in ((1, 1), (2, .6), (3, .35), (4, .2), (6, .1)))
eng *= 1 + 0.15 * norm(lp(noise(), 20)) * 0.3
load = np.where(np.diff(np.r_[v[0], v]) < -1e-5, 0.55, 1.0); load = lp(load, 2, 1)
add(lp(eng, 400) * load, 0.03)

# 5) passing vehicles — whoosh with 1/r level, doppler engine tone for trucks
C = 343.0
for e in d['passes']:
    if e['t'] < 0.15 or e['d'] > 40: continue
    span = 3.0; s0 = max(0, int((e['t'] - span) * SR)); s1 = min(N, int((e['t'] + span) * SR))
    tt = t[s0:s1] - e['t']; rv = max(e['rv'], 3.0); dist = max(e['d'], 3.5)
    r = np.sqrt(dist ** 2 + (rv * tt) ** 2)
    env = (dist / r) ** 1.3 * (6 / dist) ** 0.9
    big = e['type'] in ('semi', 'truck')
    n = noise(s1 - s0)
    w = bp(n, 60, 900) * 1.2 + bp(n, 900, 3500) * 0.35 if big else bp(n, 150, 1800) + bp(n, 1800, 5000) * 0.25
    w = norm(w) * env
    if big:  # diesel drone with doppler shift
        vrad = rv * rv * tt / r
        f = (48 if e['type'] == 'semi' else 62) * C / (C + vrad)
        tone = sum(a * np.sin(2 * np.pi * np.cumsum(f * k) / SR) for k, a in ((1, 1), (2, .5), (3, .3)))
        w += tone * env * 0.35
    g = 0.2 if big else 0.14
    if e['onc']: w = lp(w, 1500); g *= 0.55          # other side of the concrete barrier
    pan = float(np.clip(e['side'] * 0.75, -0.85, 0.85))
    add(w, g, pan, s0)

# 6) turn signal tick-tock in sync with the indicator
def click(freq, n=int(0.018 * SR)):
    k = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * k) + 0.5 * np.sin(2 * np.pi * freq * 2.3 * k)) * np.exp(-k * 320) + noise(n) * 0.25 * np.exp(-k * 600)
for a, b in d['signals']:
    k = 0; x = a
    while x < b:
        add(click(2300 if k % 2 == 0 else 1700), 0.10 if k % 2 == 0 else 0.075, 0.0, int(x * SR)); k += 1; x += d['flash']

# 7) passing under the overpass — rush of reflected road noise + low boom
to = d['overpass']; s0 = int((to - 0.6) * SR); n = int(1.2 * SR); k = np.arange(n) / SR
envo = np.exp(-((k - 0.6) / 0.17) ** 2)
add(norm(bp(noise(n), 200, 3000)) * envo + np.sin(2 * np.pi * 55 * k) * envo * 0.6, 0.06, 0, s0)
# 8) pavement seams — two quick thumps (front + rear axle)
for tj in d['joints']:
    i = int(np.argmin(abs(t - tj))); gap = 2.6 / max(v[i], 5)
    for dt in (0, gap):
        n = int(0.09 * SR); k = np.arange(n) / SR
        th = np.sin(2 * np.pi * 70 * k) * np.exp(-k * 45) + lp(noise(n), 400) * 2 * np.exp(-k * 80)
        add(th, 0.07, 0, int((tj + dt) * SR))
# 9) countryside birds once we slow down on the ramp (open window feel)
for tb in np.arange(11.2, T - 0.3, 0.55) + rng.random(len(np.arange(11.2, T - 0.3, 0.55))) * 0.4:
    n = int(rng.uniform(0.06, 0.13) * SR); k = np.arange(n) / SR
    f = rng.uniform(3200, 4600) + rng.uniform(-1500, 1500) * k / k[-1]
    ch = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * k / k[-1]) ** 2
    add(ch, 0.012 * min(1, (tb - 11) / 1.5), rng.uniform(-0.8, 0.8), int(tb * SR))
# 10) soft chime at each new step (tutorial cue)
for ts in d['steps'][1:]:
    n = int(0.7 * SR); k = np.arange(n) / SR
    ch = (np.sin(2 * np.pi * 880 * k) + 0.6 * np.sin(2 * np.pi * 1318.5 * k)) * np.exp(-k * 6) * np.minimum(1, k * 200)
    add(ch, 0.035, 0, int(ts * SR))

mix = np.stack([L, R], 1)
mix = hp(mix.T, 35).T
fade = np.ones(N); fi = int(0.4 * SR); fade[:fi] = np.linspace(0, 1, fi); fade[-fi:] = np.linspace(1, 0, fi)
mix *= fade[:, None]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.6) * 0.89
wavfile.write('sound.wav', SR, (mix * 32767).astype(np.int16))
print('ok', mix.shape, 'peak', np.abs(mix).max().round(3))
