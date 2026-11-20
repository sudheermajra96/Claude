import json, wave, numpy as np
m = json.load(open('meta_runner.json')); log = m['audioLog']
SR = 44100; N = SR * 20; t = np.arange(N) / SR
ft = np.array([e['t'] for e in log]); I = lambda k: np.interp(t, ft, np.array([float(e[k]) for e in log]))
rng = np.random.default_rng(7)
def lp(x, a):
    # one-pole lowpass via FFT of its impulse response (fast, no scipy)
    n = len(x); h = a * (1 - a) ** np.arange(min(n, int(20 / a) + 1))
    L = 1 << int(np.ceil(np.log2(n + len(h))))
    return np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(h, L), L)[:n]
hp = lambda x, a: x - lp(x, a)
mix = np.zeros(N)
def put(sig, at, gain=1.0):
    s0 = int(at * SR)
    if s0 >= N or s0 + len(sig) <= 0: return
    a = max(0, -s0); sig = sig[a:]; s0 += a; L = min(len(sig), N - s0); mix[s0:s0 + L] += sig[:L] * gain
def env(L, dec): return np.exp(-np.arange(L) / SR * dec)
slowF = lambda tt: 0.28 if tt > 17.6 else 1.0
for e in log:
    sl = slowF(e['t'])
    if e['step']:
        L = int(0.09 * SR / sl); n = hp(rng.standard_normal(L), 0.02) * env(L, 45 * sl)
        thud = np.sin(2 * np.pi * 90 * sl * np.arange(L) / SR) * env(L, 30 * sl)
        put(n * 0.22 + thud * 0.3, e['t'])
    for k, c in enumerate(e['copSteps']):
        if c:
            L = int(0.08 * SR); put(hp(rng.standard_normal(L), 0.03) * env(L, 50) * 0.1, e['t'] + 0.01 * k)
# breathing: soft noise bursts on alternate cycles
br = lp(rng.standard_normal(N), 0.06) * (0.5 + 0.5 * np.sin(2 * np.pi * t * 2.6)) ** 4 * 0.12 * (t < 17.6)
mix += br
# jumps: whoosh + landing
prevj = False
for e in log:
    if e['jump'] and not prevj:
        sl = slowF(e['t']); L = int(0.5 * SR / sl)
        put(lp(rng.standard_normal(L), 0.2) * np.sin(np.linspace(0, np.pi, L)) ** 2 * 0.35, e['t'])
    if prevj and not e['jump']:
        L = int(0.25 * SR); put((np.sin(2 * np.pi * 70 * np.arange(L) / SR) * 0.6 + lp(rng.standard_normal(L), 0.1)) * env(L, 14) * 0.5, e['t'])
    prevj = e['jump']
# police car: engine + siren by distance, tire screech when braking
pcd, pcv = I('pcd'), I('pcv'); brake = I('brake')
near = np.clip(1 - (pcd - 6) / 90, 0, 1) ** 1.5
sf = 650 + 500 * (0.5 + 0.5 * np.sin(2 * np.pi * t * 0.9))
ph = 2 * np.pi * np.cumsum(sf) / SR
sir = lp(np.sign(np.sin(ph)) * 0.5 + np.sin(ph) * 0.5, 0.3)
mix += sir * (0.03 + 0.12 * near) * (t < 18.3)
ef = 40 + pcv * 2.5; eph = 2 * np.pi * np.cumsum(ef) / SR
eng = np.tanh(sum(np.sin(k * eph) / k for k in range(1, 7)) * 1.5) * 0.18 * near
mix += eng
scr = (np.sin(2 * np.pi * np.cumsum(1800 + 250 * np.sin(t * 15)) / SR) * 0.6 + 0.4 * hp(rng.standard_normal(N), 0.1)) * brake * 0.2
mix += scr
# whistle at start
L = int(0.7 * SR); tt = np.arange(L) / SR
put(np.sin(2 * np.pi * (2900 + 120 * np.sin(2 * np.pi * 28 * tt)) * tt) * np.minimum(1, tt * 30) * env(L, 3) * 0.16, 0.15)
put(np.sin(2 * np.pi * (2900 + 120 * np.sin(2 * np.pi * 28 * tt)) * tt) * np.minimum(1, tt * 30) * env(L, 3) * 0.16, 0.95)
# near misses: whoosh + horn
for nm in m['nearMiss']:
    if nm > 17.4: continue
    L = int(0.7 * SR); put(lp(rng.standard_normal(L), 0.3) * np.sin(np.linspace(0, np.pi, L)) ** 2 * 0.5, nm - 0.35)
    L = int(0.45 * SR); tt = np.arange(L) / SR
    horn = (np.sign(np.sin(2 * np.pi * 415 * tt)) + np.sign(np.sin(2 * np.pi * 523 * tt))) * 0.5
    put(lp(horn, 0.35) * np.minimum(1, tt * 40) * np.minimum(1, (0.45 - tt) * 20) * 0.12, nm - 0.15)
# music
bpm = 132; beat = 60 / bpm; mus = np.zeros(N)
for k in range(int(20 / beat * 2) + 1):
    s0 = int(k * beat / 2 * SR)
    if s0 >= N: break
    if k % 2 == 0:
        L = int(0.25 * SR); tt = np.arange(L) / SR
        kick = np.sin(2 * np.pi * (50 * tt + 90 * (1 - np.exp(-tt * 30)) / 30)) * np.exp(-tt * 12)
        mus[s0:s0 + L] += kick[:N - s0] * 0.45
    if k % 4 == 2:
        L = int(0.18 * SR); mus[s0:s0 + L] += (hp(rng.standard_normal(L), 0.15) * env(L, 18))[:N - s0] * 0.18
    L = int(0.04 * SR); mus[s0:s0 + L] += (rng.standard_normal(L) * env(L, 100))[:N - s0] * 0.06
bf = np.array([55.0, 55.0, 65.4, 49.0])[(t / (beat * 4)).astype(int) % 4]
mus += np.tanh(3 * np.sin(2 * np.pi * np.cumsum(bf) / SR)) * (0.5 + 0.5 * np.cos(2 * np.pi * t / (beat / 2)) ** 2) * 0.13
mus *= np.where(t > 17.6, np.clip(1 - (t - 17.6) / 0.3, 0.12, 1), 1)
mix += mus
s0 = int(18.05 * SR); L = int(1.8 * SR); tt = np.arange(L) / SR; fx = np.zeros(N)
for i, f in enumerate([523.3, 659.3, 784.0, 1046.5]):
    a = int(i * 0.09 * SR); seg = np.sin(2 * np.pi * f * tt[:L - a]) * np.exp(-tt[:L - a] * 2.5) * 0.12; fx[s0 + a:s0 + L] += seg[:N - s0 - a]
mix += fx
mix = np.tanh(mix * 1.1) * 0.9 * np.clip((20 - t) / 0.4, 0, 1)
w = wave.open('audio_runner.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.stack([mix, mix], 1) * 32767).astype('<i2').tobytes()); w.close(); print('ok')
