// Street Sprint — vertical 20s on-foot chase. Deterministic, frame-indexed.
const W = 1080, H = 1920, FPS = 30, DUR = 20, NF = FPS * DUR;
const SLOWMO_AT = 17.6, SLOWMO_RATE = 0.28;
const GRID = 60, ROAD_HALF = 7;
const CITY = { x0: -150, x1: 270, z0: -330, z1: 180 };

let seed = 4242;
function rnd() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
const pick = (a) => a[Math.floor(rnd() * a.length)];
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const simTime = (t) => (t < SLOWMO_AT ? t : SLOWMO_AT + (t - SLOWMO_AT) * SLOWMO_RATE);
const wrapA = (d) => { while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; return d; };

// ---------------------------------------------------------------- route
const WP = [[10, 28], [10, -73], [28, -84], [50, -90], [66, -90], [112, -90]];
const CR = 5, DS = 0.1;
const P = { x: [], z: [], th: [], k: [], len: 0 };
(function buildPath() {
  const raw = [];
  const line = (a, b) => { const d = Math.hypot(b[0] - a[0], b[1] - a[1]); const n = Math.max(1, Math.ceil(d / 0.2)); for (let i = 0; i < n; i++) raw.push([lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)]); };
  let prev = WP[0];
  for (let i = 1; i < WP.length - 1; i++) {
    const w = WP[i], a0 = WP[i - 1], b0 = WP[i + 1];
    const d1 = [w[0] - a0[0], w[1] - a0[1]], l1 = Math.hypot(...d1), d2 = [b0[0] - w[0], b0[1] - w[1]], l2 = Math.hypot(...d2);
    const A = [w[0] - d1[0] / l1 * CR, w[1] - d1[1] / l1 * CR], B = [w[0] + d2[0] / l2 * CR, w[1] + d2[1] / l2 * CR];
    line(prev, A);
    for (let j = 0; j < 40; j++) { const t = j / 40, u = 1 - t; raw.push([u * u * A[0] + 2 * u * t * w[0] + t * t * B[0], u * u * A[1] + 2 * u * t * w[1] + t * t * B[1]]); }
    prev = B;
  }
  line(prev, WP[WP.length - 1]); raw.push(WP[WP.length - 1]);
  const cum = [0];
  for (let i = 1; i < raw.length; i++) cum.push(cum[i - 1] + Math.hypot(raw[i][0] - raw[i - 1][0], raw[i][1] - raw[i - 1][1]));
  const L = cum[cum.length - 1];
  let j = 0;
  for (let s = 0; s <= L; s += DS) { while (cum[j + 1] < s) j++; const t = (s - cum[j]) / (cum[j + 1] - cum[j] || 1); P.x.push(lerp(raw[j][0], raw[j + 1][0], t)); P.z.push(lerp(raw[j][1], raw[j + 1][1], t)); }
  const n = P.x.length;
  for (let i = 0; i < n; i++) { const a = Math.max(0, i - 2), b = Math.min(n - 1, i + 2); P.th.push(Math.atan2(P.x[b] - P.x[a], P.z[b] - P.z[a])); }
  for (let i = 0; i < n; i++) { const a = Math.max(0, i - 5), b = Math.min(n - 1, i + 5); P.k.push(wrapA(P.th[b] - P.th[a]) / ((b - a) * DS)); }
  P.len = (n - 1) * DS;
})();
function pathAt(s) {
  if (s < 0) { const th = P.th[0]; return { x: P.x[0] + Math.sin(th) * s, z: P.z[0] + Math.cos(th) * s, th, k: 0 }; }
  s = clamp(s, 0, P.len - 0.001);
  const f = s / DS, i = Math.floor(f), t = f - i;
  return { x: lerp(P.x[i], P.x[i + 1], t), z: lerp(P.z[i], P.z[i + 1], t), th: P.th[i] + wrapA(P.th[i + 1] - P.th[i]) * t, k: lerp(P.k[i], P.k[i + 1], t) };
}
function pathPos(s, lat) { const p = pathAt(s); const fx = Math.sin(p.th), fz = Math.cos(p.th); return { x: p.x - fz * lat, z: p.z + fx * lat, th: p.th, k: p.k }; }
function sAtX(x) { for (let i = P.x.length - 1; i > 0; i--) if (P.x[i] < x) return i * DS; return 0; }
function nearRoute(x, z, r) {
  for (let i = 0; i < P.x.length; i += 10) if (Math.abs(P.x[i] - x) < r && Math.abs(P.z[i] - z) < r && Math.hypot(P.x[i] - x, P.z[i] - z) < r) return true;
  return false;
}

// ---------------------------------------------------------------- runner sim
const FENCE_S = sAtX(85);
const FENCE_T = simTime(18.05);
const V = FENCE_S / FENCE_T;
const runS = (ts) => V * ts;
const JUMPS = [
  { s: runS(11.05), half: 1.7, peak: 0.75, kind: 'bench' },
  { s: runS(13.2), half: 2.2, peak: 1.25, kind: 'hedge' },
  { s: FENCE_S, half: 2.5, peak: 1.95, kind: 'fence' },
];
function jumpAt(s) {
  for (const j of JUMPS) { const d = s - j.s; if (Math.abs(d) < j.half) return { y: j.peak * (1 - (d / j.half) ** 2), f: (d + j.half) / (2 * j.half), j }; }
  return null;
}
// lateral dodge plan (negative = toward road side on first sidewalk)
const DODGES = [[3.9, -1.25], [6.6, 1.0], [10.3, 1.3], [12.0, -1.4], [16.6, 1.0]];
function latAt(ts) {
  let l = 0;
  for (const [td, a] of DODGES) l += a * Math.exp(-(((ts - td) / 0.42) ** 2));
  return l;
}
function runnerState(ts) {
  const s = runS(ts), lat = latAt(ts);
  const e = 0.02, dl = (latAt(ts + e) - latAt(ts - e)) / (2 * e) / V;
  const p = pathPos(s, lat);
  const jp = jumpAt(s);
  return { s, lat, x: p.x, z: p.z, th: p.th, k: p.k, yaw: p.th - Math.atan(dl), v: V, y: jp ? jp.y : 0, jump: jp, phase: s * Math.PI * 2 / 4.0, moving: true };
}
// cops on foot follow the runner's trail
const COPS = [
  { lag: 1.45, lat: 0.0, stopS: FENCE_S - 2.9 },
  { lag: 2.05, lat: 0.9, stopS: FENCE_S - 4.2 },
];
function copState(c, ts) {
  const lagNow = c.lag + 0.32 * Math.sin(ts * 0.9 + c.lat * 3) - 0.35 * smooth((ts - 14) / 3);
  const tq = ts - lagNow;
  let s = runS(tq), moving = true, stopT = 0;
  if (s > c.stopS) { stopT = (s - c.stopS) / V; s = c.stopS; moving = false; }
  const tl = Math.min(tq, c.stopS / V);
  const lat = latAt(tl) + c.lat;
  const p = pathPos(s, lat);
  const e = 0.02, dl = (latAt(tl + e) - latAt(tl - e)) / (2 * e) / V;
  const jp = moving ? jumpAt(s) : null;
  return { s, x: p.x, z: p.z, th: p.th, yaw: p.th - Math.atan(dl), y: jp ? jp.y : 0, jump: jp, phase: s * Math.PI * 2 / 3.9 + c.lat, moving, stopT };
}
// police car on road x=0, southbound lane x=5.25
const PC = (() => {
  const zr = (t) => runnerState(t).z;
  const tAl = 5.5, zAl = zr(tAl) + 4.0, v0 = 30;
  const tB = 8.75, brakeDur = 1.25;
  const zB = zAl - V * (tB - tAl);
  const zStop = zB - V * brakeDur / 2;
  return { tAl, zAl, v0, tB, brakeDur, zB, zStop };
})();
function policeCar(ts) {
  let z, v, drift = 0, slide = 0;
  if (ts < 3.0) { z = PC.zAl + (PC.v0 + V) / 2 * 2.5 + PC.v0 * (3.0 - ts); v = PC.v0; }
  else if (ts < PC.tAl) { const u = ts - 3.0, a = (V - PC.v0) / 2.5; z = PC.zAl + (PC.v0 + V) / 2 * 2.5 - (PC.v0 * u + a * u * u / 2); v = PC.v0 + a * u; }
  else if (ts < PC.tB) { z = PC.zAl - V * (ts - PC.tAl); v = V; }
  else { const u = Math.min(ts - PC.tB, PC.brakeDur); const a = V / PC.brakeDur; z = PC.zB - (V * u - a * u * u / 2); v = V - a * u; const f = smooth((ts - PC.tB) / PC.brakeDur); drift = 0.95 * f; slide = 1.3 * f; }
  return { x: 5.25 + slide, z, yaw: Math.PI - drift, v, drift, braking: ts > PC.tB && ts < PC.tB + PC.brakeDur };
}

// ---------------------------------------------------------------- traffic
const TYPES = { car: { len: 4.3, wid: 1.9 }, taxi: { len: 4.4, wid: 1.9 }, van: { len: 5.2, wid: 2.1 }, bus: { len: 10, wid: 2.5 } };
const CAR_COLORS = ['#2f6fdb', '#e8e8e8', '#2b2b2b', '#2fa86b', '#8a3ffc', '#f08c2e', '#5bc0eb', '#b9b9b9', '#d64f7a', '#e3262f'];
let traffic = [];
window.nearMiss = [];
function trafficPos(c, t) { const d = c.v * (t - c.t0); return { x: c.ox + c.dx * d, z: c.oz + c.dz * d, yaw: Math.atan2(c.dx, c.dz) }; }
(function genTraffic() {
  const times = []; for (let t = 0; t <= simTime(DUR) + 0.2; t += 1 / 60) times.push(t);
  const ped = (s) => ({ x: s.x, z: s.z, yaw: s.yaw, len: 0.9, wid: 0.9 });
  const rn = times.map((t) => ped(runnerState(t)));
  const cps = COPS.map((c) => times.map((t) => ped(copState(c, t))));
  const pcar = times.map((t) => { const p = policeCar(t); return { x: p.x, z: p.z, yaw: p.yaw, len: 4.8, wid: 2.1 }; });
  const test = (A, B, pad) => { const fx = Math.sin(A.yaw), fz = Math.cos(A.yaw), dx = B.x - A.x, dz = B.z - A.z; return Math.abs(dx * fx + dz * fz) < (A.len + B.len) / 2 + pad && Math.abs(-dx * fz + dz * fx) < (A.wid + B.wid) / 2 + pad; };
  const hit = (a, b, pad = 0.3) => { const dx = b.x - a.x, dz = b.z - a.z; if (dx * dx + dz * dz > 144) return false; return test(a, b, pad) && test(b, a, pad); };
  const kept = [];
  const tryAdd = (c) => {
    const T = TYPES[c.type];
    const tr = times.map((t) => ({ ...trafficPos(c, t), len: T.len, wid: T.wid }));
    let minD = 1e9, minT = 0;
    for (let i = 0; i < times.length; i++) {
      const q = tr[i];
      if (hit(rn[i], q, 0.45)) return false;
      for (const cc of cps) if (hit(cc[i], q, 0.35)) return false;
      if (hit(pcar[i], q)) return false;
      for (const k of kept) if (hit(k.tr[i], q)) return false;
      const offX = Math.abs(q.x - Math.round(q.x / GRID) * GRID) > ROAD_HALF + 1, offZ = Math.abs(q.z - Math.round(q.z / GRID) * GRID) > ROAD_HALF + 1;
      if (offX && offZ) return false;
      const d = Math.hypot(q.x - rn[i].x, q.z - rn[i].z);
      if (d < minD) { minD = d; minT = times[i]; }
    }
    c.tr = tr; c.minD = minD; c.minT = minT; kept.push(c); return true;
  };
  // timed near misses where the runner crosses a road
  const crossings = [];
  for (let i = 1; i < times.length; i++) {
    const a = rn[i - 1], b = rn[i];
    for (const ax of ['x', 'z']) { const ka = Math.floor(a[ax] / GRID), kb = Math.floor(b[ax] / GRID); if (ka !== kb) crossings.push({ t: times[i], axis: ax, line: Math.max(ka, kb) * GRID }); }
  }
  for (const cr of crossings) {
    let got = 0;
    for (let tries = 0; tries < 400 && got < 2; tries++) {
      const dir = rnd() < 0.5 ? 1 : -1, lane = pick([1.75, 5.25]), v = 15 + rnd() * 6;
      const dx = cr.axis === 'z' ? dir : 0, dz = cr.axis === 'x' ? dir : 0;
      const rx = -dz, rz = dx;
      // runner position when at this lane
      const laneX = cr.axis === 'x' ? cr.line + rx * lane : null, laneZ = cr.axis === 'z' ? cr.line + rz * lane : null;
      let tl = cr.t; for (const t of times) { const r = runnerState(t); if (cr.axis === 'x' ? Math.abs(r.x - laneX) < 0.2 : Math.abs(r.z - laneZ) < 0.2) { tl = t; break; } }
      const r = runnerState(tl);
      const tc = tl + (rnd() < 0.65 ? 0.32 + rnd() * 0.35 : -(0.32 + rnd() * 0.3));
      const ox = (cr.axis === 'x' ? laneX : r.x) - dx * v * tc, oz = (cr.axis === 'z' ? laneZ : r.z) - dz * v * tc;
      const c = { ox, oz, dx, dz, v, t0: 0, type: rnd() < 0.25 ? 'taxi' : rnd() < 0.2 ? 'van' : 'car', color: pick(CAR_COLORS) };
      if (tryAdd(c)) { if (c.minD < 3.6) { got++; window.nearMiss.push(c.minT); } else kept.pop(); }
    }
  }
  // ambient traffic
  for (let i = 0; i < 110; i++) {
    const alongX = rnd() < 0.5, dirSign = rnd() < 0.5 ? 1 : -1, lane = pick([1.75, 5.25]), v = 10 + rnd() * 10;
    const dx = alongX ? dirSign : 0, dz = alongX ? 0 : dirSign, rx = -dz, rz = dx;
    const line = Math.round(lerp(alongX ? CITY.z0 : CITY.x0, alongX ? CITY.z1 : CITY.x1, rnd()) / GRID) * GRID;
    const along = lerp(alongX ? CITY.x0 : CITY.z0, alongX ? CITY.x1 : CITY.z1, rnd());
    const ox = (alongX ? along : line) + rx * lane, oz = (alongX ? line : along) + rz * lane;
    if (!alongX && line === 0 && Math.abs(ox + 5.25) > 0.1) continue; // keep the police car's road clear for the side shot
    tryAdd({ ox, oz, dx, dz, v, t0: 0, type: rnd() < 0.1 ? 'bus' : rnd() < 0.2 ? 'taxi' : 'car', color: pick(CAR_COLORS) });
  }
  window.nearMiss.sort((a, b) => a - b);
  traffic = kept;
})();
// custom blocks along the route
function blockOverride(cx, cz) {
  if (cx === 30 && cz === -90) return 'park';
  if (cx === 90 && cz === -90) return 'alley';
  return null;
}
