import json, numpy as np, wave
m = json.load(open('meta.json'))
log = m['audioLog']; SR = 44100; N = SR * 20
ft = np.array([e['t'] for e in log]); t = np.arange(N) / SR
I = lambda k: np.interp(t, ft, np.array([float(e[k]) for e in log]))
v, drift, pol, wl, nitro = I('v'), I('drift'), I('pol'), I('wl'), I('nitro')
ts = I('ts')
rng = np.random.default_rng(3)
def lp(x, a):  # one-pole lowpass, a in (0,1)
    from scipy.signal import lfilter
    return lfilter([a], [1, a - 1], x)
try:
    import scipy
except ImportError:
    def lp(x, a):
        y = np.empty_like(x); s = 0.0
        for i in range(len(x)): s += a * (x[i] - s); y[i] = s
        return y
# engine: rpm via gears
gears = np.array([0, 18, 30, 42, 54, 66, 99])
g = np.clip(np.searchsorted(gears, v) - 1, 0, 5)
lo, hi = gears[g], gears[g + 1]
rpm = 0.35 + 0.65 * (v - lo) / (hi - lo)
f0 = 38 + rpm * 95
ph = 2 * np.pi * np.cumsum(f0) / SR
eng = sum((1 / k) * np.sin(k * ph + k * 0.3) for k in range(1, 9))
eng = eng * (0.75 + 0.25 * np.sign(np.sin(ph * 0.5)))
eng += 0.25 * lp(rng.standard_normal(N), 0.08)
eng = np.tanh(eng * 1.4) * 0.33
# screech
scr_amt = np.clip((np.abs(drift) - 0.2) * 2.5, 0, 1)
sp = 2 * np.pi * np.cumsum(1900 + 300 * np.sin(t * 13)) / SR
scr = (np.sin(sp) * 0.6 + 0.4 * (lp(rng.standard_normal(N), 0.5) - lp(rng.standard_normal(N), 0.05))) * scr_amt * 0.16
# siren (wail) when wanted
sf = 700 + 450 * (0.5 + 0.5 * np.sin(2 * np.pi * t * 0.85))
sir = np.sign(np.sin(2 * np.pi * np.cumsum(sf) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(sf) / SR) * 0.5
sir_amt = (wl > 0) * np.clip(1 - (pol - 15) / 140, 0.08, 1)
sir = lp(sir, 0.3) * sir_amt * 0.07
# nitro roar
nit = lp(rng.standard_normal(N), 0.15) * nitro * 0.35
# whooshes for popups/near misses
wh = np.zeros(N)
for p in m['popups']:
    if p['text'] != 'NEAR MISS!': continue
    # popups in sim-time; before slowmo sim==video
    s0 = int(p['t'] * SR) - int(0.25 * SR); L = int(0.6 * SR)
    if s0 < 0 or s0 + L > N: continue
    env = np.sin(np.linspace(0, np.pi, L)) ** 2
    wh[s0:s0 + L] += lp(rng.standard_normal(L), 0.25) * env * 0.5
# beat: kick + hat + bass at 128 bpm, ducks in slow-mo
bpm = 128; beat = 60 / bpm
mus = np.zeros(N)
for k in range(int(20 / beat * 2)):
    s0 = int(k * beat / 2 * SR)
    if s0 >= N: break
    if k % 2 == 0:
        L = int(0.25 * SR); tt = np.arange(L) / SR
        kick = np.sin(2 * np.pi * (50 * tt + 90 * (1 - np.exp(-tt * 30)) / 30)) * np.exp(-tt * 12)
        mus[s0:s0 + L] += kick[:N - s0] * 0.55
    L = int(0.05 * SR)
    mus[s0:s0 + L] += (rng.standard_normal(L) * np.exp(-np.arange(L) / SR * 90))[:N - s0] * 0.08
bassn = [41.2, 41.2, 49.0, 55.0]
bar = (t / (beat * 4)).astype(int)
bf = np.array(bassn)[bar % 4]
bass = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(bf) / SR)) * (0.5 + 0.5 * np.cos(2 * np.pi * t / (beat / 2)) ** 2) * 0.16
mus += bass
slow = t > 17.6
mus *= np.where(slow, np.clip(1 - (t - 17.6) / 0.3, 0.15, 1), 1)
# slow-mo: pitch engine down already via v; add impact + success chime
fx = np.zeros(N)
s0 = int(18.05 * SR); L = int(1.8 * SR); tt = np.arange(L) / SR
for i, f in enumerate([523.3, 659.3, 784.0, 1046.5]):
    a = int(i * 0.09 * SR)
    seg = np.sin(2 * np.pi * f * tt[:L - a]) * np.exp(-tt[:L - a] * 2.5) * 0.12
    fx[s0 + a:s0 + L] += seg[:N - s0 - a]
mix = eng * np.where(slow, 0.6, 1) + scr + sir + nit + wh + mus + fx
mix = np.tanh(mix * 1.1) * 0.9
fade = np.clip((20 - t) / 0.4, 0, 1) * np.clip(t / 0.05, 0, 1)
mix *= fade
st = np.stack([mix, mix], 1)
w = wave.open('audio.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st * 32767).astype('<i2').tobytes()); w.close()
print('ok', np.abs(mix).max())
