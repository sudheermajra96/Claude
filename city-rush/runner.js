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
// ---------------------------------------------------------------- three scene
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
renderer.domElement.style.display = 'none';
const scene = new THREE.Scene();
const SKY = new THREE.Color('#bfe6ff');
scene.background = SKY;
scene.fog = new THREE.Fog('#cfe9f7', 110, 300);
const camera = new THREE.PerspectiveCamera(70, W / H, 0.3, 700);

const hemi = new THREE.HemisphereLight('#e8f6ff', '#6b6f5a', 1.25);
scene.add(hemi);
const sun = new THREE.DirectionalLight('#fff3dc', 2.1);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
const sc = sun.shadow.camera; sc.left = -70; sc.right = 70; sc.top = 70; sc.bottom = -70; sc.near = 1; sc.far = 300;
sun.shadow.bias = -0.0008;
scene.add(sun); scene.add(sun.target);

// sky dome gradient
{
  const g = new THREE.SphereGeometry(600, 32, 16);
  const cols = [];
  const pos = g.attributes.position;
  const top = new THREE.Color('#5aa9e6'), hor = new THREE.Color('#d9f0ff');
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i) / 600;
    const c = hor.clone().lerp(top, clamp(y * 1.6, 0, 1));
    cols.push(c.r, c.g, c.b);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
  const m = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false });
  const dome = new THREE.Mesh(g, m);
  dome.renderOrder = -1;
  scene.add(dome);
  window.dome = dome;
}

const lam = (c, extra = {}) => new THREE.MeshLambertMaterial({ color: c, ...extra });

// ground / asphalt
{
  const g = new THREE.PlaneGeometry(CITY.x1 - CITY.x0 + 600, CITY.z1 - CITY.z0 + 600);
  const m = new THREE.Mesh(g, lam('#3d4148'));
  m.rotation.x = -Math.PI / 2;
  m.position.set((CITY.x0 + CITY.x1) / 2, 0, (CITY.z0 + CITY.z1) / 2);
  m.receiveShadow = true;
  scene.add(m);
}

const dummy = new THREE.Object3D();
function instanced(geo, mat, list, shadow = false) {
  const im = new THREE.InstancedMesh(geo, mat, list.length);
  list.forEach((f, i) => { dummy.position.set(0, 0, 0); dummy.rotation.set(0, 0, 0); dummy.scale.set(1, 1, 1); f(dummy); dummy.updateMatrix(); im.setMatrixAt(i, dummy.matrix); });
  im.castShadow = shadow; im.receiveShadow = true;
  scene.add(im);
  return im;
}

// road markings
{
  const dashes = [], yell = [], walks = [];
  const xs = [], zs = [];
  for (let x = Math.ceil(CITY.x0 / GRID) * GRID; x <= CITY.x1; x += GRID) xs.push(x);
  for (let z = Math.ceil(CITY.z0 / GRID) * GRID; z <= CITY.z1; z += GRID) zs.push(z);
  const seg = (alongX, line, a, b) => {
    const len = b - a;
    for (const off of [-3.5, 3.5]) {
      for (let d = a + 2; d < b - 2; d += 6) dashes.push((o) => { o.rotation.x = -Math.PI / 2; if (alongX) { o.position.set(d + 1.5, 0.02, line + off); o.rotation.z = Math.PI / 2; } else o.position.set(line + off, 0.02, d + 1.5); });
    }
    for (const off of [-0.18, 0.18]) yell.push((o) => { o.rotation.x = -Math.PI / 2; o.scale.set(1, len, 1); if (alongX) { o.position.set((a + b) / 2, 0.02, line + off); o.rotation.z = Math.PI / 2; } else o.position.set(line + off, 0.02, (a + b) / 2); });
  };
  for (const x of xs) for (let i = 0; i < zs.length - 1; i++) seg(false, x, zs[i] + ROAD_HALF + 3, zs[i + 1] - ROAD_HALF - 3);
  for (const z of zs) for (let i = 0; i < xs.length - 1; i++) seg(true, z, xs[i] + ROAD_HALF + 3, xs[i + 1] - ROAD_HALF - 3);
  for (const x of xs) for (const z of zs) {
    for (let k = -6; k <= 6; k += 1.5) {
      walks.push((o) => { o.rotation.x = -Math.PI / 2; o.position.set(x + k, 0.021, z + ROAD_HALF + 1.5); });
      walks.push((o) => { o.rotation.x = -Math.PI / 2; o.position.set(x + k, 0.021, z - ROAD_HALF - 1.5); });
      walks.push((o) => { o.rotation.x = -Math.PI / 2; o.rotation.z = Math.PI / 2; o.position.set(x + ROAD_HALF + 1.5, 0.021, z + k); });
      walks.push((o) => { o.rotation.x = -Math.PI / 2; o.rotation.z = Math.PI / 2; o.position.set(x - ROAD_HALF - 1.5, 0.021, z + k); });
    }
  }
  const white = new THREE.MeshLambertMaterial({ color: '#f2f2f2' });
  instanced(new THREE.PlaneGeometry(0.22, 3), white, dashes);
  instanced(new THREE.PlaneGeometry(0.16, 1), new THREE.MeshLambertMaterial({ color: '#f5c400' }), yell);
  instanced(new THREE.PlaneGeometry(0.8, 2.6), white, walks);
}

// window texture
function windowTex() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 128, 128);
  g.fillStyle = '#e9e9e9'; g.fillRect(0, 118, 128, 10);
  for (let i = 0; i < 2; i++) {
    g.fillStyle = '#3b5a78'; g.fillRect(10 + i * 64, 22, 44, 70);
    g.fillStyle = '#7fb3dd'; g.fillRect(10 + i * 64, 22, 44, 22);
    g.fillStyle = '#ffffff'; g.fillRect(30 + i * 64, 22, 4, 70);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}
const WIN = windowTex();
const BCOLS = ['#f2c14e', '#f78154', '#4d9078', '#e9e3d5', '#b4436c', '#9ad1d4', '#ffb3c1', '#c3b299', '#6c91c2', '#f4a259', '#bdd9bf', '#e07a5f', '#81b29a', '#f2cc8f'];
const roofMats = {};
function building(cx, cz, w, d, h, col) {
  const g = new THREE.BoxGeometry(w, h, d);
  const uv = g.attributes.uv;
  const faceDims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let v = 0; v < 4; v++) {
    const i = f * 4 + v;
    uv.setXY(i, uv.getX(i) * Math.max(1, Math.round(faceDims[f][0] / 4)), uv.getY(i) * Math.max(1, Math.round(faceDims[f][1] / 3.6)));
  }
  const side = lam(col, { map: WIN });
  const roof = roofMats[col] || (roofMats[col] = lam(new THREE.Color(col).multiplyScalar(0.72)));
  const m = new THREE.Mesh(g, [side, side, roof, roof, side, side]);
  m.position.set(cx, h / 2 + 0.25, cz);
  m.castShadow = true; m.receiveShadow = true;
  scene.add(m);
  // roof details
  if (rnd() < 0.5) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(w * 0.3, 2, d * 0.3), lam('#9aa0a6'));
    b.position.set(cx + (rnd() - 0.5) * w * 0.4, h + 1.25, cz + (rnd() - 0.5) * d * 0.4);
    b.castShadow = true; scene.add(b);
  }
}
// ---------------------------------------------------------------- park / alley / route props
const parkMat = lam('#7cc36b'), dirtMat = lam('#d9c49a'), hedgeMat = lam('#2f8a3e', { flatShading: true });
const woodMat = lam('#9b6a3c'), ironMat = lam('#3b3f46'), brickMat = lam('#a8553a'), stoneMat = lam('#b9b4ab');
function addBox(w, h, d, mat, x, y, z, ry = 0, shadow = true) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.rotation.y = ry; m.castShadow = shadow; m.receiveShadow = true; scene.add(m); return m;
}
function bench(x, z, ry) {
  const g = new THREE.Group(); g.position.set(x, 0.3, z); g.rotation.y = ry; scene.add(g);
  const b = (w, h, d, m, px, py, pz) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(px, py, pz); o.castShadow = true; g.add(o); };
  b(2.2, 0.1, 0.6, woodMat, 0, 0.45, 0); b(2.2, 0.45, 0.08, woodMat, 0, 0.75, -0.28);
  b(0.1, 0.45, 0.6, ironMat, -0.95, 0.22, 0); b(0.1, 0.45, 0.6, ironMat, 0.95, 0.22, 0);
}
function buildPark(cx, cz) {
  addBox(40, 0.1, 40, parkMat, cx, 0.3, cz, 0, false);
  // dirt trail along the route inside the park
  for (let s = 0; s < P.len; s += 1.2) {
    const p = pathAt(s);
    if (Math.abs(p.x - cx) < 19.5 && Math.abs(p.z - cz) < 19.5) addBox(2.6, 0.04, 1.4, dirtMat, p.x, 0.37, p.z, p.th, false);
  }
  // fountain
  const f = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.4, 0.7, 20), stoneMat); f.position.set(cx + 3, 0.65, cz - 7); f.castShadow = true; scene.add(f);
  const w = new THREE.Mesh(new THREE.CylinderGeometry(2.8, 2.8, 0.1, 20), lam('#5bb8e8')); w.position.set(cx + 3, 0.98, cz - 7); scene.add(w);
  const c = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.5, 2.2, 10), stoneMat); c.position.set(cx + 3, 1.6, cz - 7); c.castShadow = true; scene.add(c);
  for (let i = 0; i < 26; i++) { const x = cx + (rnd() - 0.5) * 36, z = cz + (rnd() - 0.5) * 36; if (!nearRoute(x, z, 4) && Math.hypot(x - cx - 3, z - cz + 7) > 5) trees.push([x, z, 0.8 + rnd() * 0.6]); }
  // hedges: decorative rows + the jump hedge across the trail
  const jh = pathAt(JUMPS[1].s);
  addBox(0.9, 1.0, 6, hedgeMat, jh.x, 0.85, jh.z, jh.th + Math.PI / 2);
  for (const [x, z, l, r] of [[cx - 12, cz + 14, 12, Math.PI / 2], [cx + 14, cz + 2, 10, 0], [cx - 6, cz - 16, 14, Math.PI / 2]]) if (!nearRoute(x, z, 5)) addBox(0.9, 1.0, l, hedgeMat, x, 0.85, z, r);
  // benches: the jump bench sits across the trail
  const jb = pathAt(JUMPS[0].s);
  bench(jb.x, jb.z, jb.th);
  bench(cx + 3 + 4.3, cz - 7, Math.PI / 2); bench(cx - 1.5, cz - 7 + 3.6, Math.PI);
}
function buildAlley(cx, cz) {
  // two long buildings with a 7m alley between them along z = cz
  building(cx, cz - 13, 44, 19, 24, '#c98b5a');
  building(cx, cz + 13, 44, 19, 32, '#7b8fa6');
  addBox(44, 0.05, 7, lam('#5a5d63'), cx, 0.27, cz, 0, false);
  // wall to hop
  const fp = pathAt(FENCE_S);
  addBox(0.5, 1.6, 7, brickMat, fp.x, 1.05, fp.z);
  addBox(0.62, 0.12, 7.1, stoneMat, fp.x, 1.9, fp.z);
  // dumpster at the dodge point and clutter
  const dd = pathPos(runS(16.6), -1.7);
  addBox(1.8, 1.3, 1.2, lam('#2e7d4f'), dd.x, 0.9, dd.z);
  addBox(1.9, 0.12, 1.3, lam('#1f5c39'), dd.x, 1.6, dd.z);
  for (let i = 0; i < 6; i++) { const x = cx - 18 + rnd() * 36, z = cz + (rnd() < 0.5 ? -3 : 3); if (!nearRoute(x, z, 1.6)) addBox(0.7, 0.7, 0.7, lam('#b98c55'), x, 0.6, z, rnd()); }
  // fire escapes
  for (const x of [cx - 12, cx + 6]) for (let fl = 1; fl < 5; fl++) addBox(3, 0.12, 1.0, ironMat, x, fl * 4.2, cz - 3.0);
}

// blocks
const trees = [], lamps = [], peds = [];
{
  const sideMat = lam('#c9c4bb');
  const curbGeo = new THREE.BoxGeometry(46, 0.25, 46);
  const grassMat = lam('#7cc36b');
  const plazaMat = lam('#e3d9c6');
  for (let x = Math.floor(CITY.x0 / GRID) * GRID; x < CITY.x1; x += GRID) {
    for (let z = Math.floor(CITY.z0 / GRID) * GRID; z < CITY.z1; z += GRID) {
      const cx = x + GRID / 2, cz = z + GRID / 2;
      const blk = new THREE.Mesh(curbGeo, sideMat);
      blk.position.set(cx, 0.125, cz); blk.receiveShadow = true; scene.add(blk);
      const ov = blockOverride(cx, cz);
      if (ov === 'park') { buildPark(cx, cz); continue; }
      if (ov === 'alley') { buildAlley(cx, cz); continue; }
      const r = rnd();
      if (r < 0.1) {
        // park
        const g = new THREE.Mesh(new THREE.BoxGeometry(40, 0.1, 40), grassMat);
        g.position.set(cx, 0.3, cz); g.receiveShadow = true; scene.add(g);
        for (let i = 0; i < 14; i++) trees.push([cx + (rnd() - 0.5) * 34, cz + (rnd() - 0.5) * 34, 0.8 + rnd() * 0.6]);
      } else {
        const big = rnd() < 0.3;
        const lots = big ? [[0, 0, 38]] : [[-10, -10, 18], [10, -10, 18], [-10, 10, 18], [10, 10, 18]];
        for (const [ox, oz, sz] of lots) {
          if (!big && rnd() < 0.12) {
            const g = new THREE.Mesh(new THREE.BoxGeometry(sz, 0.1, sz), rnd() < 0.5 ? grassMat : plazaMat);
            g.position.set(cx + ox, 0.3, cz + oz); g.receiveShadow = true; scene.add(g);
            trees.push([cx + ox, cz + oz, 1.2]);
            continue;
          }
          const h = big ? 30 + rnd() * 50 : 9 + rnd() * 28;
          const w = sz - 1 - rnd() * 3, d = sz - 1 - rnd() * 3;
          building(cx + ox, cz + oz, w, d, h, pick(BCOLS));
        }
      }
      // sidewalk trees + lamps
      for (const [sx, sz] of [[-21.5, 0], [21.5, 0], [0, -21.5], [0, 21.5]]) {
        for (let k = -16; k <= 16; k += 16) {
          const px = cx + (sx ? sx : k), pz = cz + (sz ? sz : k);
          if (rnd() < 0.55) trees.push([px, pz, 0.7 + rnd() * 0.3]);
          else lamps.push([px, pz, sx ? (sx > 0 ? Math.PI / 2 : -Math.PI / 2) : (sz > 0 ? 0 : Math.PI)]);
        }
        // pedestrians
        for (let k = 0; k < 2; k++) if (rnd() < 0.7) peds.push({ x: cx + (sx ? sx * 1.04 : (rnd() - 0.5) * 40), z: cz + (sz ? sz * 1.04 : (rnd() - 0.5) * 40), alongX: !sx, sp: (rnd() < 0.5 ? -1 : 1) * (1 + rnd() * 0.8), col: pick(['#e63946', '#457b9d', '#f1c40f', '#2ecc71', '#9b59b6', '#ffffff', '#ff8c42', '#222']) });
      }
    }
  }
  for (const arr of [trees, lamps]) for (let i = arr.length - 1; i >= 0; i--) if (nearRoute(arr[i][0], arr[i][1], 2.6)) arr.splice(i, 1);
  for (let i = peds.length - 1; i >= 0; i--) if (nearRoute(peds[i].x, peds[i].z, 6.5)) peds.splice(i, 1);
  instanced(new THREE.CylinderGeometry(0.18, 0.25, 2.2, 6), lam('#7a5230'), trees.map(([x, z, s]) => (o) => { o.position.set(x, 1.35, z); o.scale.setScalar(s); }), true);
  instanced(new THREE.IcosahedronGeometry(1.7, 0), lam('#3f9e4d', { flatShading: true }), trees.map(([x, z, s]) => (o) => { o.position.set(x, 1.25 + 2.6 * s, z); o.scale.setScalar(s); }), true);
  instanced(new THREE.CylinderGeometry(0.1, 0.12, 6, 6), lam('#555b63'), lamps.map(([x, z]) => (o) => { o.position.set(x, 3.25, z); }), true);
  instanced(new THREE.BoxGeometry(0.4, 0.2, 2), lam('#555b63'), lamps.map(([x, z, r]) => (o) => { o.rotation.y = r; o.position.set(x, 6.2, z); o.translateZ(-0.9); }));
}
// traffic lights at intersections
{
  const poles = [], heads = [];
  for (let x = Math.ceil(CITY.x0 / GRID) * GRID; x <= CITY.x1; x += GRID) for (let z = Math.ceil(CITY.z0 / GRID) * GRID; z <= CITY.z1; z += GRID) {
    for (const [sx, sz] of [[1, 1], [-1, -1]]) {
      if (nearRoute(x + sx * 8.5, z + sz * 8.5, 2.6)) continue;
      poles.push((o) => o.position.set(x + sx * 8.5, 2.5, z + sz * 8.5));
      heads.push((o) => o.position.set(x + sx * 8.5, 5.2, z + sz * 8.5));
    }
  }
  instanced(new THREE.CylinderGeometry(0.12, 0.12, 5, 6), lam('#333'), poles, true);
  instanced(new THREE.BoxGeometry(0.6, 1.6, 0.6), lam('#222'), heads, true);
}
// pedestrians (instanced, animated)
const pedMesh = new THREE.InstancedMesh(new THREE.CapsuleGeometry(0.28, 0.9, 3, 6), lam('#ffffff'), peds.length);
pedMesh.castShadow = true;
peds.forEach((p, i) => pedMesh.setColorAt(i, new THREE.Color(p.col)));
scene.add(pedMesh);
const headMesh = new THREE.InstancedMesh(new THREE.SphereGeometry(0.24, 8, 6), lam('#f1c27d'), peds.length);
scene.add(headMesh);
function updatePeds(t) {
  peds.forEach((p, i) => {
    const d = ((p.sp * t * 1.4 + 100) % 8) - 4;
    const x = p.x + (p.alongX ? d : 0), z = p.z + (p.alongX ? 0 : d);
    const bob = Math.abs(Math.sin(t * 9 + i)) * 0.08;
    dummy.position.set(x, 1.0 + bob, z); dummy.rotation.set(0, 0, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix();
    pedMesh.setMatrixAt(i, dummy.matrix);
    dummy.position.y = 1.85 + bob; dummy.updateMatrix(); headMesh.setMatrixAt(i, dummy.matrix);
  });
  pedMesh.instanceMatrix.needsUpdate = true; headMesh.instanceMatrix.needsUpdate = true;
}

// ---------------------------------------------------------------- vehicles
const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.32, 14);
wheelGeo.rotateZ(Math.PI / 2);
const wheelMat = lam('#1b1b1b');
const rimMat = lam('#cfd3d6');
const rimGeo = new THREE.CylinderGeometry(0.22, 0.22, 0.34, 8); rimGeo.rotateZ(Math.PI / 2);
const glassMat = lam('#22323f');
const headMat = new THREE.MeshBasicMaterial({ color: '#fffbe0' });
const tailMat = new THREE.MeshBasicMaterial({ color: '#ff2a2a' });
function box(w, h, d, mat, x, y, z, parent, shadow = true) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = shadow; parent.add(m); return m;
}
function makeVehicle(kind, color) {
  const g = new THREE.Group();
  const body = new THREE.Group(); g.add(body);
  const bm = lam(color);
  const wheels = [];
  let L = 4.3, Wd = 1.9;
  if (kind === 'bus') {
    L = 10; Wd = 2.5;
    box(2.5, 2.6, 10, bm, 0, 1.75, 0, body);
    box(2.55, 0.9, 9.4, glassMat, 0, 2.3, -0.1, body);
    box(2.3, 0.9, 0.08, glassMat, 0, 2.2, 5.0, body);
  } else if (kind === 'van') {
    L = 5.2; Wd = 2.1;
    box(2.1, 2.0, 5.2, bm, 0, 1.45, 0, body);
    box(2.0, 0.7, 0.1, glassMat, 0, 1.95, 2.58, body);
    box(2.12, 0.6, 1.2, glassMat, 0, 1.95, 1.7, body);
  } else {
    const sporty = kind === 'player';
    const hBody = sporty ? 0.62 : 0.75;
    box(Wd, hBody, L, bm, 0, 0.42 + hBody / 2, 0, body);
    const cabH = sporty ? 0.5 : 0.62, cabL = sporty ? 2.0 : 2.3;
    box(Wd - 0.22, cabH, cabL, glassMat, 0, 0.42 + hBody + cabH / 2, sporty ? -0.35 : -0.2, body);
    box(Wd - 0.3, 0.08, cabL - 0.5, bm, 0, 0.42 + hBody + cabH + 0.03, sporty ? -0.45 : -0.3, body);
    if (sporty) {
      box(Wd, 0.08, 0.5, lam('#111'), 0, 1.45, -2.0, body);
      box(0.1, 0.36, 0.1, lam('#111'), 0.7, 1.24, -2.0, body);
      box(0.1, 0.36, 0.1, lam('#111'), -0.7, 1.24, -2.0, body);
      box(0.5, 0.02, L - 0.2, lam('#ffffff'), 0.32, 0.42 + hBody + 0.01, 0.05, body, false);
      box(0.5, 0.02, L - 0.2, lam('#ffffff'), -0.32, 0.42 + hBody + 0.01, 0.05, body, false);
    }
    if (kind === 'taxi') box(0.8, 0.25, 0.35, lam('#ffffff'), 0, 0.42 + hBody + cabH + 0.2, -0.3, body);
    if (kind === 'police') {
      box(Wd + 0.01, 0.5, 1.9, lam('#1a2a6c'), 0, 0.42 + hBody / 2, 0.0, body, false);
      const bar = new THREE.Group(); bar.position.set(0, 0.42 + hBody + cabH + 0.16, -0.3); body.add(bar);
      const red = new THREE.MeshBasicMaterial({ color: '#ff1a1a' });
      const blue = new THREE.MeshBasicMaterial({ color: '#1a4dff' });
      const r = box(0.6, 0.18, 0.32, red, -0.36, 0, 0, bar, false);
      const b = box(0.6, 0.18, 0.32, blue, 0.36, 0, 0, bar, false);
      g.userData.bar = { r, b, red, blue };
      const glowR = makeGlow('#ff2020'), glowB = makeGlow('#2a5bff');
      glowR.position.set(-0.5, 0.2, 0); glowB.position.set(0.5, 0.2, 0);
      bar.add(glowR); bar.add(glowB);
      g.userData.glow = { glowR, glowB };
    }
  }
  box(0.42, 0.18, 0.06, headMat, Wd / 2 - 0.35, 0.85, L / 2 + 0.01, body, false);
  box(0.42, 0.18, 0.06, headMat, -Wd / 2 + 0.35, 0.85, L / 2 + 0.01, body, false);
  box(0.42, 0.16, 0.06, tailMat, Wd / 2 - 0.35, 0.9, -L / 2 - 0.01, body, false);
  box(0.42, 0.16, 0.06, tailMat, -Wd / 2 + 0.35, 0.9, -L / 2 - 0.01, body, false);
  const wz = kind === 'bus' ? 3.4 : L / 2 - 0.85;
  for (const [sx, sz] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) {
    const piv = new THREE.Group(); piv.position.set(sx * (Wd / 2 - 0.1), 0.4, sz * wz); g.add(piv);
    const w = new THREE.Mesh(wheelGeo, wheelMat); w.castShadow = true; piv.add(w);
    const r = new THREE.Mesh(rimGeo, rimMat); w.add(r);
    wheels.push({ piv, w, front: sz > 0 });
  }
  g.userData.body = body; g.userData.wheels = wheels; g.userData.L = L;
  scene.add(g);
  return g;
}
const glowTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.6)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
})();
function makeGlow(col) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: col, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  s.scale.set(3.2, 3.2, 1);
  return s;
}

// skid marks
const SKID_MAX = 6000;
const skidPos = new Float32Array(SKID_MAX * 6 * 3);
const skidGeo = new THREE.BufferGeometry();
skidGeo.setAttribute('position', new THREE.BufferAttribute(skidPos, 3));
skidGeo.setDrawRange(0, 0);
const skidMesh = new THREE.Mesh(skidGeo, new THREE.MeshBasicMaterial({ color: '#111', transparent: true, opacity: 0.5, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
skidMesh.frustumCulled = false;
scene.add(skidMesh);
let skidN = 0;
const lastWheel = {};
function addSkid(key, x, z, wdx, wdz, on) {
  const prev = lastWheel[key];
  lastWheel[key] = { x, z, on };
  if (!prev || !prev.on || !on || skidN >= SKID_MAX) return;
  const w = 0.16;
  const dx = x - prev.x, dz = z - prev.z, l = Math.hypot(dx, dz) || 1;
  const nx = -dz / l * w, nz = dx / l * w;
  const y = 0.03;
  const q = [prev.x + nx, y, prev.z + nz, prev.x - nx, y, prev.z - nz, x + nx, y, z + nz, prev.x - nx, y, prev.z - nz, x - nx, y, z - nz, x + nx, y, z + nz];
  skidPos.set(q, skidN * 18); skidN++;
  skidGeo.setDrawRange(0, skidN * 6);
  skidGeo.attributes.position.needsUpdate = true;
}
// smoke
const smokeTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
})();
const smoke = [];
for (let i = 0; i < 160; i++) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: smokeTex, color: '#eeeeee', transparent: true, depthWrite: false, opacity: 0 }));
  s.visible = false; scene.add(s); smoke.push({ s, life: 0, max: 1, vx: 0, vz: 0 });
}
let smokeIdx = 0;
function spawnSmoke(x, z, amt) {
  const p = smoke[smokeIdx++ % smoke.length];
  p.s.position.set(x + (rnd() - 0.5) * 0.4, 0.5, z + (rnd() - 0.5) * 0.4);
  p.life = 0; p.max = 0.9 + rnd() * 0.7; p.vx = (rnd() - 0.5) * 1.5; p.vz = (rnd() - 0.5) * 1.5; p.amt = amt;
  p.s.visible = true;
}
function updateSmoke(dt) {
  for (const p of smoke) {
    if (!p.s.visible) continue;
    p.life += dt;
    const f = p.life / p.max;
    if (f >= 1) { p.s.visible = false; continue; }
    p.s.position.x += p.vx * dt; p.s.position.z += p.vz * dt; p.s.position.y += dt * 1.2;
    const sc = 1 + f * 4.5; p.s.scale.set(sc, sc, 1);
    p.s.material.opacity = (1 - f) * 0.55 * p.amt;
  }
}

function placeVehicle(obj, x, z, yaw, opts = {}) {
  obj.position.set(x, 0, z);
  obj.rotation.y = yaw;
  const body = obj.userData.body;
  body.rotation.z = opts.roll || 0;
  body.rotation.x = opts.pitch || 0;
  for (const w of obj.userData.wheels) {
    w.w.rotation.x = opts.spin || 0;
    if (w.front) w.piv.rotation.y = opts.steer || 0;
  }
}


// ---------------------------------------------------------------- characters
function makeChar(o) {
  const g = new THREE.Group(); scene.add(g);
  const M = (c) => lam(c);
  const skin = M(o.skin || '#e0ac69'), shirt = M(o.shirt), pants = M(o.pants), shoe = M(o.shoes || '#f4f4f4'), hair = M(o.hair || '#2b1d14');
  const part = (w, h, d, m, x, y, z, parent) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); b.position.set(x, y, z); b.castShadow = true; parent.add(b); return b; };
  const hips = new THREE.Group(); hips.position.y = 0.95; g.add(hips);
  const torso = new THREE.Group(); hips.add(torso);
  part(0.56, 0.62, 0.32, shirt, 0, 0.33, 0, torso);
  part(0.5, 0.16, 0.3, pants, 0, -0.02, 0, hips);
  const head = new THREE.Group(); head.position.y = 0.74; torso.add(head);
  part(0.34, 0.36, 0.34, skin, 0, 0.18, 0, head);
  part(0.36, 0.12, 0.36, hair, 0, 0.38, -0.01, head);
  part(0.06, 0.06, 0.02, M('#111'), 0.08, 0.22, 0.175, head); part(0.06, 0.06, 0.02, M('#111'), -0.08, 0.22, 0.175, head);
  if (o.hat === 'police') { part(0.4, 0.14, 0.4, M('#141c3a'), 0, 0.42, 0, head); part(0.4, 0.04, 0.2, M('#0c1024'), 0, 0.36, 0.22, head); part(0.08, 0.08, 0.02, M('#ffd23f'), 0, 0.44, 0.21, head); }
  if (o.hood) part(0.4, 0.3, 0.12, shirt, 0, 0.2, -0.22, head);
  if (o.badge) { part(0.08, 0.1, 0.02, M('#ffd23f'), -0.14, 0.48, 0.17, torso); part(0.58, 0.08, 0.34, M('#111'), 0, 0.05, 0, torso); }
  const limb = (x, y, parentObj, m1, m2, l1, l2, w, footM) => {
    const a = new THREE.Group(); a.position.set(x, y, 0); parentObj.add(a);
    part(w, l1, w, m1, 0, -l1 / 2, 0, a);
    const b = new THREE.Group(); b.position.y = -l1; a.add(b);
    part(w * 0.92, l2, w * 0.92, m2, 0, -l2 / 2, 0, b);
    if (footM) part(w * 1.05, 0.1, 0.3, footM, 0, -l2 - 0.02, 0.07, b);
    else part(w * 0.9, 0.11, w * 0.9, skin, 0, -l2 - 0.05, 0, b);
    return { a, b };
  };
  const legL = limb(0.14, 0, hips, pants, pants, 0.46, 0.44, 0.2, shoe), legR = limb(-0.14, 0, hips, pants, pants, 0.46, 0.44, 0.2, shoe);
  const armL = limb(0.36, 0.6, torso, shirt, o.sleeves ? shirt : skin, 0.32, 0.3, 0.15), armR = limb(-0.36, 0.6, torso, shirt, o.sleeves ? shirt : skin, 0.32, 0.3, 0.15);
  g.userData = { hips, torso, head, legL, legR, armL, armR };
  return g;
}
function poseChar(ch, st) {
  const u = ch.userData;
  if (st.mode === 'run') {
    const ph = st.phase, A = 0.95;
    const sl = Math.sin(ph), cl = Math.cos(ph);
    u.legL.a.rotation.x = -sl * A; u.legR.a.rotation.x = sl * A;
    u.legL.b.rotation.x = 0.25 + 1.15 * Math.max(0, cl) + 0.3 * Math.max(0, -sl);
    u.legR.b.rotation.x = 0.25 + 1.15 * Math.max(0, -cl) + 0.3 * Math.max(0, sl);
    u.armL.a.rotation.x = sl * 0.95; u.armR.a.rotation.x = -sl * 0.95;
    u.armL.b.rotation.x = -1.35; u.armR.b.rotation.x = -1.35;
    u.armL.a.rotation.z = 0.12; u.armR.a.rotation.z = -0.12;
    u.torso.rotation.x = 0.28; u.head.rotation.x = -0.2;
    u.hips.position.y = 0.92 + Math.abs(Math.cos(ph)) * 0.09;
    u.torso.rotation.y = sl * 0.18;
  } else if (st.mode === 'jump') {
    const f = st.f;
    const tuck = Math.sin(f * Math.PI);
    u.legL.a.rotation.x = -1.3 * tuck - 0.2; u.legR.a.rotation.x = -0.4 * tuck + 0.5 * (1 - tuck);
    u.legL.b.rotation.x = 0.4 + 1.2 * tuck; u.legR.b.rotation.x = 0.4 + 1.5 * tuck;
    u.armL.a.rotation.x = -2.2 * tuck - 0.4; u.armR.a.rotation.x = 1.0 * tuck - 0.4;
    u.armL.b.rotation.x = -0.4; u.armR.b.rotation.x = -0.8;
    u.armL.a.rotation.z = 0.35; u.armR.a.rotation.z = -0.35;
    u.torso.rotation.x = 0.35; u.head.rotation.x = -0.25; u.hips.position.y = 0.92; u.torso.rotation.y = 0;
  } else if (st.mode === 'tired') {
    const b = Math.sin(st.t * 7) * 0.04;
    u.legL.a.rotation.x = -0.25; u.legR.a.rotation.x = -0.25; u.legL.b.rotation.x = 0.45; u.legR.b.rotation.x = 0.45;
    u.torso.rotation.x = 0.85 + b; u.head.rotation.x = -0.7;
    u.armL.a.rotation.x = -0.9; u.armR.a.rotation.x = -0.9; u.armL.b.rotation.x = -0.2; u.armR.b.rotation.x = -0.2;
    u.armL.a.rotation.z = 0.1; u.armR.a.rotation.z = -0.1;
    u.hips.position.y = 0.82; u.torso.rotation.y = 0;
  } else if (st.mode === 'stand' || st.mode === 'startled') {
    const sc = st.mode === 'startled' ? st.amt : 0;
    const w = Math.sin(st.t * 2) * 0.03;
    u.legL.a.rotation.x = 0.05 * sc; u.legR.a.rotation.x = -0.3 * sc; u.legL.b.rotation.x = 0.05; u.legR.b.rotation.x = 0.2 * sc;
    u.armL.a.rotation.x = -2.5 * sc + w; u.armR.a.rotation.x = -2.5 * sc - w; u.armL.b.rotation.x = -0.3 * sc - 0.1; u.armR.b.rotation.x = -0.3 * sc - 0.1;
    u.armL.a.rotation.z = 0.1 + 0.4 * sc; u.armR.a.rotation.z = -0.1 - 0.4 * sc;
    u.torso.rotation.x = -0.25 * sc; u.head.rotation.x = 0; u.hips.position.y = 0.95; u.torso.rotation.y = 0;
  }
}

// ---------------------------------------------------------------- actors
const runner = makeChar({ shirt: '#22c55e', pants: '#2b3a55', shoes: '#ffffff', skin: '#c68642', hair: '#1a120d', hood: true, sleeves: true });
const cops = COPS.map((c, i) => makeChar({ shirt: '#22356e', pants: '#141c3a', shoes: '#111', skin: i ? '#f1c27d' : '#8d5524', hat: 'police', badge: true, sleeves: false }));
const pcar = makeVehicle('police', '#f4f4f4');
traffic.forEach((c) => { c.obj = makeVehicle(c.type, c.type === 'taxi' ? '#ffc61a' : c.type === 'bus' ? pick(['#2a9d8f', '#e76f51']) : c.color); c.obj.visible = false; });
const bystanders = DODGES.slice(0, 4).map(([td, a], i) => {
  const s = runS(td), p = pathPos(s, -Math.sign(a) * 0.65);
  const ch = makeChar({ shirt: ['#9b59b6', '#e63946', '#2ecc71', '#f1c40f'][i], pants: ['#333', '#556', '#3a2a1a', '#223'][i], skin: ['#f1c27d', '#e0ac69', '#8d5524', '#ffdbac'][i], hair: ['#5a3825', '#111', '#111', '#c99a55'][i], sleeves: i % 2 === 0 });
  ch.position.set(p.x, 0.25, p.z); ch.rotation.y = p.th + Math.PI;
  return { ch, td, s };
});

// ---------------------------------------------------------------- camera
const SHOTS = [
  ['intro', -1, 2.3],
  ['chase', 2.3, 5.4, 0.55, 0.04],
  ['side', 5.4, 8.4, 0.04, 0.04],
  ['chase', 8.4, 12.0, 0.04],
  ['top', 12.0, 14.8],
  ['chaseLow', 14.8, 17.55],
  ['orbit', 17.55, 21],
];
const BLEND = 0.6;
const camState = { th: null };
function camFor(mode, st, t) {
  const fx = Math.sin(camState.th), fz = Math.cos(camState.th), rx = -fz, rz = fx;
  const p = new THREE.Vector3(st.x, 0.25, st.z);
  const V3 = (f, r, u) => new THREE.Vector3(fx * f + rx * r, u, fz * f + rz * r);
  switch (mode) {
    case 'intro': { const pull = t * 0.6; return { pos: p.clone().add(V3(5.2 + pull, 0.9, 1.1)), tgt: p.clone().add(V3(-4, 0, 1.0)), fov: 62 }; }
    case 'chase': return { pos: p.clone().add(V3(-5.4, 0.3, 2.4)), tgt: p.clone().add(V3(4.5, 0, 1.15)), fov: 68 };
    case 'chaseLow': return { pos: p.clone().add(V3(-4.2, -0.4, 1.35)), tgt: p.clone().add(V3(5, 0, 1.35)), fov: 72 };
    case 'side': return { pos: p.clone().add(V3(0.2, -11.5, 3.3)), tgt: p.clone().add(V3(-0.6, -2.5, 0.9)), fov: 58 };
    case 'top': return { pos: p.clone().add(V3(-7, 0, 24)), tgt: p.clone().add(V3(3.5, 0, 0)), fov: 58 };
    case 'orbit': {
      const fp = pathAt(FENCE_S), u = t - 17.55;
      return { pos: new THREE.Vector3(fp.x + 6.2 + u * 2.4, 2.3, fp.z + 2.4), tgt: new THREE.Vector3(st.x - 0.5, 0.25 + st.y * 0.6 + 1.0, st.z), fov: 62 };
    }
  }
}
function shotWeights(t) {
  const ws = SHOTS.map(([m, a, b, bi = BLEND, bo]) => { bo = bo ?? (bi < 0.1 ? bi : BLEND); return smooth((t - a + bi / 2) / bi) * (1 - smooth((t - b + bo / 2) / bo)); });
  const sum = ws.reduce((x, y) => x + y, 0) || 1;
  return ws.map((w) => w / sum);
}

// ---------------------------------------------------------------- HUD
const out = document.createElement('canvas'); out.width = W; out.height = H;
const ctx = out.getContext('2d');
const FONT = '"Inter", "DejaVu Sans", sans-serif';
function txt(s, x, y, size, fill, opts = {}) {
  ctx.save();
  ctx.font = `${opts.italic ? 'italic ' : ''}${opts.weight || 900} ${size}px ${FONT}`;
  ctx.textAlign = opts.align || 'center'; ctx.textBaseline = 'middle';
  if (opts.stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = opts.sw || size * 0.16; ctx.strokeStyle = opts.stroke; ctx.strokeText(s, x, y); }
  ctx.fillStyle = fill; ctx.fillText(s, x, y);
  ctx.restore();
}
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function star(cx, cy, r, filled, col) {
  ctx.beginPath();
  for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, q = i % 2 ? r * 0.45 : r; ctx.lineTo(cx + Math.cos(a) * q, cy + Math.sin(a) * q); }
  ctx.closePath(); ctx.lineWidth = 6; ctx.strokeStyle = '#000'; ctx.stroke();
  ctx.fillStyle = filled ? col : 'rgba(255,255,255,0.18)'; ctx.fill();
  ctx.lineWidth = 2.5; ctx.strokeStyle = filled ? '#fff' : 'rgba(255,255,255,0.6)'; ctx.stroke();
}
function wantedLevel(ts) { if (ts > 18.0) return Math.max(0, 3 - Math.floor((ts - 18.0) / 0.08)); if (ts < 5.3) return 2; return 3; }
const popups = [];
for (const t of window.nearMiss) if (t > 2.2 && t < 17.3) popups.push({ t, text: 'CLOSE CALL!', sub: '+$150', col: '#ffd23f', val: 150 });
popups.push({ t: runS(11.05) / V - 0.05, text: 'PARKOUR!', sub: '+$200', col: '#3ee6ff', val: 200 });
popups.push({ t: runS(13.2) / V, text: 'HEDGE HOP!', sub: '+$300', col: '#3ee6ff', val: 300 });
popups.push({ t: 5.3, text: 'BACKUP!', sub: 'POLICE CAR INCOMING', col: '#ff3b3b', val: 0, big: true });
popups.sort((a, b) => a.t - b.t);
for (let i = 1; i < popups.length; i++) if (popups[i].t - popups[i - 1].t < 1.0) popups[i].t = popups[i - 1].t + 1.0;
function cashAt(ts) { let c = 480; for (const p of popups) if (p.t <= ts) c += p.val; if (ts > 18.05) c += Math.round(2500 * smooth((ts - 18.05) / 0.35)); return c; }

function drawMinimap(st, ts, dots) {
  const cx = 175, cy = 300, R = 135, S = 2.2;
  ctx.save();
  ctx.beginPath(); ctx.arc(cx, cy, R + 10, 0, Math.PI * 2); ctx.fillStyle = 'rgba(0,0,0,0.75)'; ctx.fill();
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = '#6b7a68'; ctx.fillRect(cx - R, cy - R, R * 2, R * 2);
  ctx.translate(cx, cy); const th = camState.th; ctx.rotate(th + Math.PI); ctx.scale(-S, S); ctx.translate(-st.x, -st.z);
  ctx.fillStyle = '#7cc36b'; ctx.fillRect(10, -110, 40, 40);
  ctx.strokeStyle = '#d4d4d4'; ctx.lineWidth = 14; const r0 = 90;
  for (let x = Math.floor((st.x - r0) / GRID) * GRID; x <= st.x + r0; x += GRID) { ctx.beginPath(); ctx.moveTo(x, st.z - r0); ctx.lineTo(x, st.z + r0); ctx.stroke(); }
  for (let z = Math.floor((st.z - r0) / GRID) * GRID; z <= st.z + r0; z += GRID) { ctx.beginPath(); ctx.moveTo(st.x - r0, z); ctx.lineTo(st.x + r0, z); ctx.stroke(); }
  ctx.strokeStyle = '#c04dff'; ctx.lineWidth = 3; ctx.lineJoin = 'round'; ctx.beginPath();
  for (let s = st.s; s < Math.min(P.len, st.s + 120); s += 1) { const p = pathAt(s); ctx.lineTo(p.x, p.z); } ctx.stroke();
  ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.clip();
  const fx = Math.sin(th), fz = Math.cos(th);
  for (const d of dots) {
    const dx = d.x - st.x, dz = d.z - st.z, x = cx + (dx * -fz + dz * fx) * S, y = cy - (dx * fx + dz * fz) * S;
    const on = Math.floor(ts * 6) % 2;
    ctx.beginPath(); ctx.arc(x, y, d.car ? 10 : 7, 0, Math.PI * 2); ctx.fillStyle = on ? '#ff2a2a' : '#2f6bff'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
  }
  ctx.restore();
  ctx.save(); ctx.translate(cx, cy);
  ctx.beginPath(); ctx.moveTo(0, -16); ctx.lineTo(11, 12); ctx.lineTo(0, 6); ctx.lineTo(-11, 12); ctx.closePath();
  ctx.fillStyle = '#fff'; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = '#000'; ctx.stroke(); ctx.restore();
  ctx.beginPath(); ctx.arc(cx, cy, R + 4, 0, Math.PI * 2); ctx.lineWidth = 8;
  ctx.strokeStyle = wantedLevel(ts) > 0 ? (Math.floor(ts * 4) % 2 ? '#ff3030' : '#3060ff') : '#ffffff'; ctx.stroke();
  // health / armor / stamina
  const bar = (y, f, col) => { rr(40, y, 270, 16, 8); ctx.fillStyle = 'rgba(0,0,0,0.65)'; ctx.fill(); rr(43, y + 3, 264 * f, 10, 5); ctx.fillStyle = col; ctx.fill(); };
  bar(462, 0.86, '#4fd15a'); bar(486, 0.45, '#4aa3ff');
  const stam = ts > 18 ? 0.25 + (ts - 18) * 0.5 : clamp(1 - ts / 26 - (ts > 14.8 ? 0.05 : 0), 0, 1);
  bar(510, stam, '#ffd23f');
}
function drawJoystick(dx, dy) {
  const cx = 230, cy = H - 270;
  ctx.save();
  ctx.beginPath(); ctx.arc(cx, cy, 165, 0, Math.PI * 2); ctx.fillStyle = 'rgba(20,22,28,0.55)'; ctx.fill();
  ctx.lineWidth = 6; ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.45)';
  for (const a of [0, Math.PI / 2, Math.PI, -Math.PI / 2]) { ctx.save(); ctx.translate(cx, cy); ctx.rotate(a); ctx.beginPath(); ctx.moveTo(0, -140); ctx.lineTo(16, -118); ctx.lineTo(-16, -118); ctx.closePath(); ctx.fill(); ctx.restore(); }
  const kx = cx + dx * 95, ky = cy + dy * 95;
  ctx.beginPath(); ctx.arc(kx, ky, 72, 0, Math.PI * 2);
  const g = ctx.createRadialGradient(kx - 20, ky - 20, 10, kx, ky, 72); g.addColorStop(0, '#5a5f6b'); g.addColorStop(1, '#25282f');
  ctx.fillStyle = g; ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = '#22c55e'; ctx.stroke();
  ctx.restore();
}
function drawButton(x, y, r, label, pressed, col, size = 34) {
  ctx.save(); ctx.translate(x, y); const sc = pressed ? 0.9 : 1; ctx.scale(sc, sc);
  ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fillStyle = pressed ? col : 'rgba(40,42,48,0.85)'; ctx.fill();
  ctx.lineWidth = 6; ctx.strokeStyle = pressed ? '#fff' : 'rgba(255,255,255,0.5)'; ctx.stroke(); ctx.restore();
  txt(label, x, y, size, pressed ? '#111' : '#fff');
}
function drawHUD(t, ts, st, dots, lead) {
  const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.72);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.45)'); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  const wl = wantedLevel(ts);
  if (wl > 0 && ts < 18) {
    const on = Math.floor(ts * 6) % 2;
    const gr = ctx.createLinearGradient(on ? 0 : W, 0, on ? 240 : W - 240, 0);
    gr.addColorStop(0, on ? 'rgba(255,30,30,0.28)' : 'rgba(40,80,255,0.28)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
  }
  const tg = ctx.createLinearGradient(0, 0, 0, 560); tg.addColorStop(0, 'rgba(0,0,0,0.45)'); tg.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 560);
  const bg = ctx.createLinearGradient(0, H - 560, 0, H); bg.addColorStop(0, 'rgba(0,0,0,0)'); bg.addColorStop(1, 'rgba(0,0,0,0.5)'); ctx.fillStyle = bg; ctx.fillRect(0, H - 560, W, 560);
  drawMinimap(st, ts, dots);
  for (let i = 0; i < 5; i++) { const filled = i < wl; const flash = filled && i === wl - 1 && Math.floor(ts * 5) % 2 === 0 && ts < 18; star(W - 70 - (4 - i) * 78, 232, 32, filled, flash ? '#fff' : '#ffd23f'); }
  txt('$' + String(cashAt(ts)).padStart(8, '0'), W - 40, 155, 64, '#5fe36a', { align: 'right', stroke: '#000', sw: 12 });
  txt('21:08', W - 40, 88, 40, '#ffffff', { align: 'right', stroke: '#000', sw: 8, weight: 800 });
  // lead meter (top-center)
  {
    const cx = W / 2 + 60, cy = 470;
    ctx.save(); ctx.translate(cx, cy); rr(-190, -78, 380, 156, 30); ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fill(); ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.stroke();
    const f = clamp(lead / 25, 0, 1);
    rr(-160, 46, 320, 14, 7); ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.fill();
    rr(-160, 46, 320 * f, 14, 7); ctx.fillStyle = f < 0.5 ? '#ff3b3b' : f < 0.8 ? '#ffd23f' : '#5fe36a'; ctx.fill(); ctx.restore();
    txt(lead > 99 ? '---' : String(Math.round(lead)).padStart(2, '0'), cx - 40, cy - 12, 92, '#fff', { italic: true });
    txt('M', cx + 40, cy + 6, 40, '#fff', { weight: 800 });
    txt('LEAD', cx + 125, cy - 8, 26, '#ffd23f', { weight: 800 });
  }
  // subtitles / mission
  const SUBS = [[0.4, 2.1, 'COP: ', 'Stop! Police!', '#6fa8ff'], [2.5, 4.9, 'Lose the ', 'cops!', '#ff4d4d'], [5.9, 8.2, 'COP: ', 'Get on the ground!', '#6fa8ff'], [9.4, 11.8, 'Cut through the ', 'park!', '#5fe36a'], [14.6, 17.2, 'Hop the ', 'wall!', '#ffd23f']];
  for (const [a, b, p1, p2, col] of SUBS) if (ts > a && ts < b) {
    ctx.save(); ctx.font = `800 46px ${FONT}`; const w1 = ctx.measureText(p1).width, w2 = ctx.measureText(p2).width;
    const x0 = W / 2 - (w1 + w2) / 2, y = H - 500; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round'; ctx.lineWidth = 9; ctx.strokeStyle = '#000';
    ctx.strokeText(p1, x0, y); ctx.strokeText(p2, x0 + w1, y); ctx.fillStyle = p1.startsWith('COP') ? '#6fa8ff' : '#fff'; ctx.fillText(p1, x0, y); ctx.fillStyle = col; ctx.fillText(p2, x0 + w1, y); ctx.restore();
  }
  // controls
  if (t < 17.8) {
    ctx.save(); ctx.globalAlpha = 1 - smooth((t - 17.5) / 0.3);
    const steer = clamp(-st.k * 6 + (st.yaw - st.th) * -1.2, -0.8, 0.8);
    drawJoystick(steer, -0.75);
    const jumping = !!st.jump;
    drawButton(W - 160, H - 220, 110, 'JUMP', jumping, '#3ee6ff', 38);
    drawButton(W - 340, H - 380, 85, 'SPRINT', !jumping, '#ffd23f', 28);
    drawButton(W - 140, H - 440, 62, 'HIDE', false, '#fff', 24);
    ctx.restore();
  }
  for (const p of popups) {
    const age = ts - p.t; if (age < 0 || age > 0.95 || p.t > 16.7) continue;
    const pop = age < 0.15 ? 0.4 + 0.8 * (age / 0.15) : age < 0.25 ? 1.2 - (age - 0.15) * 2 : 1;
    const alpha = age > 0.75 ? 1 - (age - 0.75) / 0.2 : 1;
    ctx.save(); ctx.globalAlpha = clamp(alpha, 0, 1); ctx.translate(W / 2, (p.big ? 760 : 820) - age * 60); ctx.scale(pop, pop); ctx.rotate(-0.05);
    txt(p.text, 0, 0, p.big ? 120 : 96, p.col, { italic: true, stroke: '#000', sw: 16 });
    txt(p.sub, 0, p.big ? 86 : 80, p.big ? 44 : 54, '#fff', { italic: true, stroke: '#000', sw: 10 }); ctx.restore();
  }
  if (t < 2.1) {
    const a = t < 0.15 ? t / 0.15 : t > 1.75 ? 1 - (t - 1.75) / 0.35 : 1, sl = 1 - smooth(t / 0.35);
    ctx.save(); ctx.globalAlpha = clamp(a, 0, 1); ctx.translate(W / 2 - sl * 600, 800); ctx.rotate(-0.06);
    rr(-480, -150, 960, 300, 30); ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fill();
    txt('STREET', 0, -52, 145, '#ffd23f', { italic: true, stroke: '#000', sw: 18 });
    txt('SPRINT', 0, 78, 145, '#22e06b', { italic: true, stroke: '#000', sw: 18 }); ctx.restore();
  }
  if (ts > 18.0) {
    const pop = smooth((t - 17.95) / 0.35);
    ctx.save(); ctx.fillStyle = `rgba(0,0,0,${0.35 * pop})`; ctx.fillRect(0, 1180, W, 400);
    ctx.globalAlpha = pop; ctx.translate(W / 2, 1330); ctx.scale(0.6 + 0.4 * pop, 0.6 + 0.4 * pop);
    txt('ESCAPED!', 0, 0, 150, '#ffd23f', { italic: true, stroke: '#000', sw: 18 });
    txt('COPS LOST YOU', 0, 120, 52, '#fff', { stroke: '#000', sw: 10 });
    txt('+$2500', 0, 190, 64, '#5fe36a', { italic: true, stroke: '#000', sw: 12 }); ctx.restore();
  }
}

// ---------------------------------------------------------------- frame render
let prevTs = 0, prevPhase = 0, prevCopPhase = [0, 0];
const audioLog = [];
function renderFrame(fi) {
  const t = fi / FPS, ts = simTime(t), dt = Math.max(1e-4, ts - prevTs);
  const st = runnerState(ts);
  if (camState.th === null) camState.th = st.th;
  camState.th += wrapA(st.th - camState.th) * (1 - Math.exp(-dt * 3.5));

  runner.position.set(st.x, 0.25 + st.y, st.z); runner.rotation.y = st.yaw; runner.rotation.z = clamp(st.k * V * 0.12, -0.25, 0.25);
  poseChar(runner, st.jump ? { mode: 'jump', f: st.jump.f } : { mode: 'run', phase: st.phase });
  const copSt = COPS.map((c, i) => {
    const cs = copState(c, ts), ch = cops[i];
    ch.position.set(cs.x, 0.25 + cs.y, cs.z); ch.rotation.y = cs.yaw;
    if (cs.moving) poseChar(ch, cs.jump ? { mode: 'jump', f: cs.jump.f } : { mode: 'run', phase: cs.phase });
    else { poseChar(ch, { mode: 'tired', t: ts + i }); ch.rotation.y = cs.yaw + (i ? 0.5 : -0.3); }
    return cs;
  });
  const pc = policeCar(ts);
  placeVehicle(pcar, pc.x, pc.z, pc.yaw, { spin: -pc.z / 0.4, roll: -pc.drift * 0.08, steer: -pc.drift * 0.5 });
  {
    const on = Math.floor(ts * 7) % 2 === 0, { glowR, glowB } = pcar.userData.glow;
    glowR.visible = on; glowB.visible = !on;
    pcar.userData.bar.r.material.color.set(on ? '#ff2a2a' : '#551111'); pcar.userData.bar.b.material.color.set(!on ? '#2a5bff' : '#111a55');
    const fx = Math.sin(pc.yaw), fz = Math.cos(pc.yaw);
    [[0.85, -1.3], [-0.85, -1.3], [0.85, 1.3], [-0.85, 1.3]].forEach(([lx, lz], k) => {
      const ax = pc.x + Math.cos(pc.yaw) * lx + fx * lz, az = pc.z - Math.sin(pc.yaw) * lx + fz * lz;
      addSkid('pc' + k, ax, az, 0, 0, pc.braking);
      if (pc.braking && k < 2) spawnSmoke(ax, az, 0.8);
    });
  }
  for (const b of bystanders) {
    const d = st.s - b.s;
    poseChar(b.ch, { mode: 'startled', t: ts, amt: smooth((d + 4) / 2) * (1 - smooth((d - 10) / 4)) });
  }
  // landing dust
  if (st.jump && st.jump.f > 0.93) for (let k = 0; k < 2; k++) spawnSmoke(st.x, st.z, 0.35);
  updateSmoke(dt);
  for (const c of traffic) {
    const q = trafficPos(c, ts);
    if (Math.hypot(q.x - st.x, q.z - st.z) > 230) { c.obj.visible = false; continue; }
    c.obj.visible = true; placeVehicle(c.obj, q.x, q.z, q.yaw, { spin: -c.v * ts / 0.4 });
  }
  updatePeds(ts);

  const ws = shotWeights(t);
  const pos = new THREE.Vector3(), tgt = new THREE.Vector3(); let fov = 0;
  SHOTS.forEach(([m], i) => { if (ws[i] < 1e-4) return; const c = camFor(m, st, t); pos.addScaledVector(c.pos, ws[i]); tgt.addScaledVector(c.tgt, ws[i]); fov += c.fov * ws[i]; });
  const shake = t < 17.5 ? 0.035 : 0;
  pos.x += Math.sin(fi * 1.7) * shake; pos.y += Math.abs(Math.sin(st.phase)) * 0.06 * (t < 17.5 ? 1 : 0) + Math.sin(fi * 2.3) * shake; pos.z += Math.cos(fi * 1.9) * shake;
  camera.position.copy(pos); camera.fov = fov; camera.updateProjectionMatrix(); camera.lookAt(tgt);
  sun.position.set(st.x + 45, 100, st.z - 55); sun.target.position.set(st.x, 0, st.z);
  window.dome.position.copy(camera.position);
  renderer.render(scene, camera);
  ctx.drawImage(renderer.domElement, 0, 0);
  const lead = Math.min(...copSt.map((c) => Math.hypot(c.x - st.x, c.z - st.z)));
  const dots = copSt.map((c) => ({ x: c.x, z: c.z })).concat([{ x: pc.x, z: pc.z, car: true }]);
  drawHUD(t, ts, st, dots, ts > 18.0 ? 999 : lead);

  // audio events
  const steps = Math.floor(st.phase / Math.PI) !== Math.floor(prevPhase / Math.PI) && !st.jump;
  const copSteps = copSt.map((c, i) => { const r = c.moving && !c.jump && Math.floor(c.phase / Math.PI) !== Math.floor(prevCopPhase[i] / Math.PI); prevCopPhase[i] = c.phase; return r; });
  prevPhase = st.phase;
  audioLog.push({ t, ts, step: steps, copSteps, jump: !!st.jump, jf: st.jump ? st.jump.f : 0, jk: st.jump ? st.jump.j.kind : '', pcd: Math.hypot(pc.x - st.x, pc.z - st.z), pcv: pc.v, brake: pc.braking, lead });
  prevTs = ts;
  return out.toDataURL('image/jpeg', 0.93);
}
window.renderFrame = renderFrame;
window.getMeta = () => ({ audioLog, nearMiss: window.nearMiss, popups: popups.map((p) => ({ t: p.t, text: p.text })), traffic: traffic.length, V, FENCE_S, fence: pathAt(FENCE_S), jumps: JUMPS.map((j) => ({ s: j.s, p: pathAt(j.s) })) });
window.ready = true;
