// City Rush — vertical 20s driving clip. Deterministic, frame-indexed.
const W = 1080, H = 1920, FPS = 30, DUR = 20, NF = FPS * DUR;
const SLOWMO_AT = 17.6, SLOWMO_RATE = 0.28;
const GRID = 60, ROAD_HALF = 7;
const CITY = { x0: -180, x1: 360, z0: -960, z1: 180 };

let seed = 1337;
function rnd() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
const pick = (a) => a[Math.floor(rnd() * a.length)];
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const simTime = (t) => (t < SLOWMO_AT ? t : SLOWMO_AT + (t - SLOWMO_AT) * SLOWMO_RATE);

// ---------------------------------------------------------------- path
const WP = [[0, 110], [0, -180], [180, -180], [180, -420], [60, -420], [60, -1000]];
const CR = 15;
const DS = 0.25;
let P = { x: [], z: [], th: [], k: [], len: 0 };
(function buildPath() {
  const raw = [];
  const line = (a, b) => {
    const d = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const n = Math.max(1, Math.ceil(d / 0.5));
    for (let i = 0; i < n; i++) raw.push([lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)]);
  };
  let prev = WP[0];
  for (let i = 1; i < WP.length - 1; i++) {
    const w = WP[i], a0 = WP[i - 1], b0 = WP[i + 1];
    const d1 = [w[0] - a0[0], w[1] - a0[1]], l1 = Math.hypot(...d1);
    const d2 = [b0[0] - w[0], b0[1] - w[1]], l2 = Math.hypot(...d2);
    const A = [w[0] - d1[0] / l1 * CR, w[1] - d1[1] / l1 * CR];
    const B = [w[0] + d2[0] / l2 * CR, w[1] + d2[1] / l2 * CR];
    line(prev, A);
    for (let j = 0; j < 60; j++) {
      const t = j / 60, u = 1 - t;
      raw.push([u * u * A[0] + 2 * u * t * w[0] + t * t * B[0], u * u * A[1] + 2 * u * t * w[1] + t * t * B[1]]);
    }
    prev = B;
  }
  line(prev, WP[WP.length - 1]);
  raw.push(WP[WP.length - 1]);
  const cum = [0];
  for (let i = 1; i < raw.length; i++) cum.push(cum[i - 1] + Math.hypot(raw[i][0] - raw[i - 1][0], raw[i][1] - raw[i - 1][1]));
  const L = cum[cum.length - 1];
  let j = 0;
  for (let s = 0; s <= L; s += DS) {
    while (cum[j + 1] < s) j++;
    const t = (s - cum[j]) / (cum[j + 1] - cum[j] || 1);
    P.x.push(lerp(raw[j][0], raw[j + 1][0], t));
    P.z.push(lerp(raw[j][1], raw[j + 1][1], t));
  }
  const n = P.x.length;
  for (let i = 0; i < n; i++) {
    const a = Math.max(0, i - 1), b = Math.min(n - 1, i + 1);
    P.th.push(Math.atan2(P.x[b] - P.x[a], P.z[b] - P.z[a]));
  }
  for (let i = 0; i < n; i++) {
    const a = Math.max(0, i - 2), b = Math.min(n - 1, i + 2);
    let d = P.th[b] - P.th[a];
    while (d > Math.PI) d -= 2 * Math.PI;
    while (d < -Math.PI) d += 2 * Math.PI;
    P.k.push(d / ((b - a) * DS));
  }
  P.len = (n - 1) * DS;
})();
function pathAt(s) {
  s = clamp(s, 0, P.len - 0.001);
  const f = s / DS, i = Math.floor(f), t = f - i;
  const x = lerp(P.x[i], P.x[i + 1], t), z = lerp(P.z[i], P.z[i + 1], t);
  let d = P.th[i + 1] - P.th[i];
  while (d > Math.PI) d -= 2 * Math.PI;
  while (d < -Math.PI) d += 2 * Math.PI;
  const th = P.th[i] + d * t;
  return { x, z, th, k: lerp(P.k[i], P.k[i + 1], t) };
}
function pathPos(s, lat) {
  const p = pathAt(s);
  const fx = Math.sin(p.th), fz = Math.cos(p.th);
  return { x: p.x - fz * lat, z: p.z + fx * lat, th: p.th, k: p.k };
}
// right vector of heading th (fwd = (sin, cos)) is (-cos, sin)?  fwd(0,-1) -> right(+1,0): (-fz, fx) = (1,0) ok

// ---------------------------------------------------------------- player sim
const SIM_HZ = 240, SIM_END = simTime(DUR) + 0.2;
const sim = { t: [], s: [], v: [], lat: [], drift: [], th: [], yaw: [], k: [], acc: [] };
(function runSim() {
  const n = P.x.length;
  const vlim = new Float32Array(n);
  const ALAT = 62, VMAX = 64, BRAKE = 40;
  for (let i = 0; i < n; i++) {
    let m = 0;
    for (let j = Math.max(0, i - 4); j <= Math.min(n - 1, i + 4); j++) m = Math.max(m, Math.abs(P.k[j]));
    vlim[i] = Math.min(VMAX, Math.sqrt(ALAT / Math.max(m, 1e-4)));
  }
  for (let i = n - 2; i >= 0; i--) vlim[i] = Math.min(vlim[i], Math.sqrt(vlim[i + 1] ** 2 + 2 * BRAKE * DS));
  // lane plan (lateral offset) keyed by time
  const lanePlan = [[0, 5.25], [1.6, 5.25], [2.3, 1.75], [3.5, 1.75], [4.1, -1.75], [5.1, -1.75], [5.7, 1.75], [7.6, 1.75], [8.2, 5.25], [9.3, 5.25], [9.9, 1.75], [10.9, 1.75], [11.5, -1.75], [12.4, -1.75], [13.0, 1.75], [14.4, 1.75], [15.0, 5.25], [15.9, 5.25], [16.5, 1.75], [30, 1.75]];
  const latAt = (t) => {
    for (let i = 0; i < lanePlan.length - 1; i++) {
      const [ta, la] = lanePlan[i], [tb, lb] = lanePlan[i + 1];
      if (t >= ta && t < tb) return lerp(la, lb, smooth((t - ta) / (tb - ta)));
    }
    return lanePlan[lanePlan.length - 1][1];
  };
  let s = 0, v = 34, drift = 0, prevLat = latAt(0);
  const dt = 1 / SIM_HZ;
  for (let step = 0; step * dt <= SIM_END; step++) {
    const t = step * dt;
    const i = Math.min(n - 1, Math.round(s / DS));
    const nitro = t > 14.6 && t < 17.6;
    const vmaxNow = nitro ? 76 : 64;
    const acc = (nitro ? 30 : 15) * (1 - v / 90) + 4;
    let target = Math.min(vlim[i] * (nitro ? 1.15 : 1), vmaxNow);
    let nv = v < target ? Math.min(target, v + acc * dt) : Math.max(target, v - 55 * dt);
    const a = (nv - v) / dt;
    v = nv;
    s += v * dt;
    const p = pathAt(s);
    const lat = latAt(t);
    const dlat = (lat - prevLat) / Math.max(v * dt, 1e-4);
    prevLat = lat;
    const dTarget = clamp(p.k * v * v * 0.0105, -0.75, 0.75);
    drift += (dTarget - drift) * (1 - Math.exp(-dt * (Math.abs(dTarget) > Math.abs(drift) ? 6 : 2.6)));
    const yaw = p.th - Math.atan(dlat) + drift;
    sim.t.push(t); sim.s.push(s); sim.v.push(v); sim.lat.push(lat); sim.drift.push(drift);
    sim.th.push(p.th); sim.yaw.push(yaw); sim.k.push(p.k); sim.acc.push(a);
  }
})();
function simAt(t) {
  const i = clamp(Math.round(t * SIM_HZ), 0, sim.t.length - 1);
  return { t, s: sim.s[i], v: sim.v[i], lat: sim.lat[i], drift: sim.drift[i], th: sim.th[i], yaw: sim.yaw[i], k: sim.k[i], acc: sim.acc[i] };
}
function playerState(t) {
  const st = simAt(t);
  const pp = pathPos(st.s, st.lat);
  return { ...st, x: pp.x, z: pp.z };
}
// corner times (for camera schedule)
const cornerTimes = [];
{
  let inC = false;
  for (let i = 0; i < sim.t.length; i++) {
    const c = Math.abs(sim.k[i]) > 0.03;
    if (c && !inC) cornerTimes.push(sim.t[i]);
    inC = c;
  }
}

// ---------------------------------------------------------------- police
const police = [
  { start: 4.2, lag0: 2.6, lag1: 0.45, rampEnd: 7.4, latOff: 0, color: 'police' },
  { start: 9.0, lag0: 2.4, lag1: 1.05, rampEnd: 11.5, latOff: 0, color: 'police' },
];
function policeLag(pc, t) {
  let lag = lerp(pc.lag0, pc.lag1, smooth((t - pc.start) / (pc.rampEnd - pc.start)));
  if (t > 14.8) lag += (t - 14.8) * 0.55; // player nitros away
  if (pc === police[0]) lag += 0.55 * smooth((t - 8.97) / 0.12);
  return lag;
}
function policeState(pc, t) {
  if (t < pc.start) return null;
  const lag = policeLag(pc, t);
  const st = simAt(Math.max(0, t - lag));
  const pp = pathPos(st.s, st.lat + pc.latOff);
  return { x: pp.x, z: pp.z, yaw: st.yaw, v: st.v, drift: st.drift, s: st.s };
}

// ---------------------------------------------------------------- traffic
const TYPES = {
  car: { len: 4.3, wid: 1.9 }, taxi: { len: 4.4, wid: 1.9 }, van: { len: 5.2, wid: 2.1 }, bus: { len: 10, wid: 2.5 },
};
const CAR_COLORS = ['#2f6fdb', '#e8e8e8', '#2b2b2b', '#2fa86b', '#8a3ffc', '#f08c2e', '#5bc0eb', '#b9b9b9', '#d64f7a'];
let traffic = [];
function trafficPos(c, t) {
  if (c.mode === 'path') {
    const s = c.s0 + c.dir * c.v * (t - c.t0);
    if (s < 1 || s > P.len - 1) return null;
    const pp = pathPos(s, c.lane);
    return { x: pp.x, z: pp.z, yaw: c.dir > 0 ? pp.th : pp.th + Math.PI, s };
  } else {
    const d = c.v * (t - c.t0);
    return { x: c.ox + c.dx * d, z: c.oz + c.dz * d, yaw: Math.atan2(c.dx, c.dz) };
  }
}
(function genTraffic() {
  const cands = [];
  const nearCorner = (s) => { for (let d = -26; d <= 26; d += 2) if (Math.abs(pathAt(s + d).k) > 0.01) return true; return false; };
  // timed near-miss traffic on player's route
  for (let tp = 1.1; tp < 17.4; tp += 0.42 + rnd() * 0.35) {
    const st = playerState(tp);
    if (nearCorner(st.s)) continue;
    const lanes = [-5.25, -1.75, 1.75, 5.25].filter((l) => Math.abs(l - st.lat) >= 3.3);
    const lane = pick(lanes);
    const dir = lane > 0 ? 1 : -1;
    const v = dir > 0 ? 9 + rnd() * 9 : 11 + rnd() * 8;
    const type = rnd() < 0.08 ? 'bus' : rnd() < 0.15 ? 'van' : rnd() < 0.25 ? 'taxi' : 'car';
    cands.push({ mode: 'path', s0: st.s, t0: tp, dir, v, lane, type, color: pick(CAR_COLORS), nm: Math.abs(lane - st.lat) < 3.6 });
  }
  // cross traffic at intersections the player passes straight through
  for (let t = 0.5; t < 17.2; t += 1 / 60) {
    const a = playerState(t), b = playerState(t + 1 / 60);
    for (const axis of ['x', 'z']) {
      const ka = Math.floor(a[axis] / GRID), kb = Math.floor(b[axis] / GRID);
      if (ka !== kb && Math.abs(a.k) < 0.005 && rnd() < 0.75) {
        const gx = Math.max(ka, kb) * GRID;
        // player crossing a road line perpendicular to its travel
        const fx = Math.sin(a.th), fz = Math.cos(a.th);
        // cross road runs along the other axis
        const dirSign = rnd() < 0.5 ? 1 : -1;
        const lane = pick([1.75, 5.25]);
        const v = 14 + rnd() * 6;
        const tc = t + (rnd() < 0.5 ? 0.42 : -0.38) + rnd() * 0.15;
        // cross road direction vector
        let dx, dz, ox, oz;
        if (axis === 'z') { dx = dirSign; dz = 0; }
        else { dx = 0; dz = dirSign; }
        // right of travel dir
        const rx = -dz, rz = dx;
        // position at tc: on the player's road center line crossing point
        const cx = axis === 'x' ? gx : a.x, cz = axis === 'z' ? gx : a.z;
        const px = axis === 'x' ? cx : a.x, pz = axis === 'z' ? cz : a.z;
        // car passes the player's lateral position at tc
        ox = (axis === 'z' ? a.x : gx) + rx * lane - dx * v * tc;
        oz = (axis === 'x' ? a.z : gx) + rz * lane - dz * v * tc;
        if (axis === 'x') { ox = gx + rx * lane - dx * v * tc; oz = a.z - dz * v * tc + (a.z - a.z); }
        if (axis === 'z') { oz = gx + rz * lane - dz * v * tc; ox = a.x - dx * v * tc; }
        cands.push({ mode: 'line', ox, oz, dx, dz, v, t0: 0, type: rnd() < 0.2 ? 'van' : 'car', color: pick(CAR_COLORS) });
      }
    }
  }
  // ambient traffic on all roads
  for (let i = 0; i < 90; i++) {
    const alongX = rnd() < 0.5;
    const dirSign = rnd() < 0.5 ? 1 : -1;
    const lane = pick([1.75, 5.25]);
    const v = 10 + rnd() * 10;
    let dx = alongX ? dirSign : 0, dz = alongX ? 0 : dirSign;
    const rx = -dz, rz = dx;
    const line = Math.round(lerp(alongX ? CITY.z0 : CITY.x0, alongX ? CITY.z1 : CITY.x1, rnd()) / GRID) * GRID;
    const along = lerp(alongX ? CITY.x0 : CITY.z0, alongX ? CITY.x1 : CITY.z1, rnd());
    const ox = (alongX ? along : line) + rx * lane, oz = (alongX ? line : along) + rz * lane;
    cands.push({ mode: 'line', ox, oz, dx, dz, v, t0: 0, type: rnd() < 0.1 ? 'bus' : rnd() < 0.2 ? 'taxi' : 'car', color: pick(CAR_COLORS) });
  }
  // collision filtering
  const times = [];
  for (let t = 0; t <= SIM_END; t += 1 / 60) times.push(t);
  const pl = times.map((t) => { const p = playerState(t); return { x: p.x, z: p.z, yaw: p.yaw, len: 4.6, wid: 2.1 }; });
  const pol = police.map((pc) => times.map((t) => { const p = policeState(pc, t); return p && { x: p.x, z: p.z, yaw: p.yaw, len: 4.8, wid: 2.1 }; }));
  const hit = (a, b) => {
    const dx = b.x - a.x, dz = b.z - a.z;
    if (dx * dx + dz * dz > 144) return false;
    // OBB-ish: check b center in a frame and a in b frame with summed half sizes
    const test = (A, B) => {
      const fx = Math.sin(A.yaw), fz = Math.cos(A.yaw);
      const ddx = B.x - A.x, ddz = B.z - A.z;
      const lo = Math.abs(ddx * fx + ddz * fz), la = Math.abs(-ddx * fz + ddz * fx);
      return lo < (A.len + B.len) / 2 + 0.3 && la < (A.wid + B.wid) / 2 + 0.25;
    };
    return test(a, b) && test(b, a);
  };
  const kept = [];
  for (const c of cands) {
    const T = TYPES[c.type];
    const tr = times.map((t) => { const p = trafficPos(c, t); return p && { ...p, len: T.len, wid: T.wid }; });
    let bad = false;
    for (let i = 0; i < times.length && !bad; i++) {
      const q = tr[i]; if (!q) continue;
      if (hit(pl[i], q)) bad = true;
      for (const pp of pol) if (pp[i] && hit(pp[i], q)) bad = true;
      for (const k of kept) if (k.tr[i] && hit(k.tr[i], q)) { bad = true; break; }
      // keep off-road check for line cars
      if (c.mode === 'line') {
        const offX = Math.abs(q.x - Math.round(q.x / GRID) * GRID) > ROAD_HALF + 1;
        const offZ = Math.abs(q.z - Math.round(q.z / GRID) * GRID) > ROAD_HALF + 1;
        if (offX && offZ) bad = true;
      }
    }
    if (!bad) { c.tr = tr; kept.push(c); }
  }
  // near miss events
  const events = [];
  for (const c of kept) {
    let best = 1e9, bt = 0;
    for (let i = 0; i < times.length; i++) {
      const q = c.tr[i]; if (!q) continue;
      const a = pl[i];
      const fx = Math.sin(a.yaw), fz = Math.cos(a.yaw);
      const ddx = q.x - a.x, ddz = q.z - a.z;
      const lo = Math.abs(ddx * fx + ddz * fz), la = Math.abs(-ddx * fz + ddz * fx);
      if (lo < 3 && la < best) { best = la; bt = times[i]; }
    }
    if (best < 4.1) events.push(bt);
  }
  events.sort((a, b) => a - b);
  window.nearMiss = [];
  for (const e of events) if (!window.nearMiss.length || e - window.nearMiss[window.nearMiss.length - 1] > 0.9) window.nearMiss.push(e);
  traffic = kept;
})();

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

const player = makeVehicle('player', '#e3262f');
const flames = [];
for (const sx of [0.45, -0.45]) {
  const f = new THREE.Mesh(new THREE.ConeGeometry(0.16, 1.2, 8), new THREE.MeshBasicMaterial({ color: '#66ccff', transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false }));
  f.rotation.x = -Math.PI / 2; f.position.set(sx, 0.55, -2.75);
  const gl = makeGlow('#5fbfff'); gl.scale.set(1.6, 1.6, 1); f.add(gl);
  player.add(f); flames.push(f);
}
const policeCars = police.map((pc) => makeVehicle('police', '#f4f4f4'));
traffic.forEach((c) => { c.obj = makeVehicle(c.type === 'car' ? 'car' : c.type, c.type === 'taxi' ? '#ffc61a' : c.type === 'bus' ? pick(['#2a9d8f', '#e76f51', '#f4a261']) : c.color); c.obj.visible = false; });

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

// ---------------------------------------------------------------- camera schedule
const C = cornerTimes;
window.cornerTimes = C;
// camera mode weights by video time
const SHOTS = [
  // [mode, start, end]
  ['intro', -1, 1.75],
  ['chase', 1.75, 6.3, 0.55, 0.04],
  ['front', 6.3, 9.0, 0.04],
  ['chase', 9.0, 12.3, 0.04],
  ['top', 12.3, 14.9],
  ['chaseLow', 14.9, 17.5],
  ['orbit', 17.5, 21],
];
const BLEND = 0.55;
let camSmooth = null;
const camState = { th: null };
function camFor(mode, st, t, ts) {
  const fx = Math.sin(camState.th), fz = Math.cos(camState.th);
  const rx = -fz, rz = fx;
  const p = new THREE.Vector3(st.x, 0, st.z);
  const v = st.v;
  switch (mode) {
    case 'intro': {
      // fixed roadside camera ahead of start
      const a = pathPos(80, 0.2);
      const pos = new THREE.Vector3(a.x, 1.3, a.z);
      const tgt = p.clone().add(new THREE.Vector3(0, 1.0, 0));
      return { pos, tgt, fov: 58 };
    }
    case 'chase': {
      const back = 10.5 + v * 0.03, hgt = 4.4;
      return { pos: p.clone().add(new THREE.Vector3(-fx * back, hgt, -fz * back)), tgt: p.clone().add(new THREE.Vector3(fx * 7, 1.3, fz * 7)), fov: 66 + v * 0.16 };
    }
    case 'chaseLow': {
      const back = 8.5 + v * 0.02, hgt = 2.6;
      return { pos: p.clone().add(new THREE.Vector3(-fx * back, hgt, -fz * back)), tgt: p.clone().add(new THREE.Vector3(fx * 8, 1.2, fz * 8)), fov: 68 + v * 0.2 };
    }
    case 'front': {
      const ahead = 11, side = 2.2;
      return { pos: p.clone().add(new THREE.Vector3(fx * ahead + rx * side, 2.4, fz * ahead + rz * side)), tgt: p.clone().add(new THREE.Vector3(-fx * 14, 1.3, -fz * 14)), fov: 62 };
    }
    case 'top': {
      return { pos: p.clone().add(new THREE.Vector3(-fx * 9, 46, -fz * 9)), tgt: p.clone().add(new THREE.Vector3(fx * 7, 0, fz * 7)), fov: 52 };
    }
    case 'orbit': {
      const a = camState.th + Math.PI * 0.75 + (t - 17.5) * 0.9;
      return { pos: p.clone().add(new THREE.Vector3(Math.sin(a) * 9, 2.2, Math.cos(a) * 9)), tgt: p.clone().add(new THREE.Vector3(0, 0.9, 0)), fov: 56 };
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
document.body.appendChild(out);
const FONT = '"Inter", "DejaVu Sans", sans-serif';
function txt(s, x, y, size, fill, opts = {}) {
  ctx.save();
  ctx.font = `${opts.italic ? 'italic ' : ''}${opts.weight || 900} ${size}px ${FONT}`;
  ctx.textAlign = opts.align || 'center'; ctx.textBaseline = 'middle';
  if (opts.stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = opts.sw || size * 0.16; ctx.strokeStyle = opts.stroke; ctx.strokeText(s, x, y); }
  if (opts.shadow) { ctx.shadowColor = opts.shadow; ctx.shadowBlur = opts.blur || 12; }
  ctx.fillStyle = fill; ctx.fillText(s, x, y);
  ctx.restore();
}
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function star(cx, cy, r, filled, col) {
  ctx.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + i * Math.PI / 5, rr2 = i % 2 ? r * 0.45 : r;
    ctx.lineTo(cx + Math.cos(a) * rr2, cy + Math.sin(a) * rr2);
  }
  ctx.closePath();
  ctx.lineWidth = 6; ctx.strokeStyle = '#000'; ctx.stroke();
  ctx.fillStyle = filled ? col : 'rgba(255,255,255,0.18)'; ctx.fill();
  ctx.lineWidth = 2.5; ctx.strokeStyle = filled ? '#fff' : 'rgba(255,255,255,0.6)'; ctx.stroke();
}
function wantedLevel(ts) {
  if (ts > 18.0) return 0;
  if (ts < 4.9) return 0; if (ts < 7.0) return 1; if (ts < 9.4) return 2; if (ts < 12.5) return 3; return 4;
}
const popups = [];
(function buildPopups() {
  let cash = 0;
  for (const t of window.nearMiss) if (t > 2.0 && t < 17.4) popups.push({ t, text: 'NEAR MISS!', sub: '+$250', col: '#ffd23f', val: 250 });
  // drifts
  let inD = false, dStart = 0;
  for (let i = 0; i < sim.t.length; i++) {
    const d = Math.abs(sim.drift[i]) > 0.3;
    if (d && !inD) dStart = sim.t[i];
    if (!d && inD && sim.t[i] - dStart > 0.4 && sim.t[i] < 17.6) popups.push({ t: sim.t[i] - 0.25, text: 'DRIFT!', sub: '+$' + Math.round((sim.t[i] - dStart) * 900), col: '#3ee6ff', val: Math.round((sim.t[i] - dStart) * 900) });
    inD = d;
  }
  popups.push({ t: 4.95, text: 'WANTED!', sub: 'COPS ARE COMING', col: '#ff3b3b', val: 0, big: true });
  popups.sort((a, b) => a.t - b.t);
  // de-overlap
  for (let i = 1; i < popups.length; i++) if (popups[i].t - popups[i - 1].t < 1.0) popups[i].t = popups[i - 1].t + 1.0;
})();
function cashAt(ts) {
  let c = 1250;
  for (const p of popups) if (p.t <= ts) c += p.val;
  if (ts > 18.05) c += Math.round(5000 * smooth((ts - 18.05) / 0.35));
  return c;
}
let shownCash = 1250;

function drawMinimap(st, ts, polStates) {
  const cx = 175, cy = 300, R = 135, S = 1.15;
  ctx.save();
  ctx.beginPath(); ctx.arc(cx, cy, R + 10, 0, Math.PI * 2); ctx.fillStyle = 'rgba(0,0,0,0.75)'; ctx.fill();
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = '#5e7d58'; ctx.fillRect(cx - R, cy - R, R * 2, R * 2);
  ctx.translate(cx, cy);
  const th = camState.th;
  // map world (x,z) -> screen, heading up. world forward f=(sin th, cos th) maps to (0,-1)
  ctx.rotate(th + Math.PI);
  ctx.scale(-S, S);
  ctx.translate(-st.x, -st.z);
  // roads
  ctx.strokeStyle = '#d4d4d4'; ctx.lineWidth = 14; ctx.lineCap = 'butt';
  const r0 = 160;
  for (let x = Math.floor((st.x - r0) / GRID) * GRID; x <= st.x + r0; x += GRID) { ctx.beginPath(); ctx.moveTo(x, st.z - r0); ctx.lineTo(x, st.z + r0); ctx.stroke(); }
  for (let z = Math.floor((st.z - r0) / GRID) * GRID; z <= st.z + r0; z += GRID) { ctx.beginPath(); ctx.moveTo(st.x - r0, z); ctx.lineTo(st.x + r0, z); ctx.stroke(); }
  // GPS route ahead
  ctx.strokeStyle = '#c04dff'; ctx.lineWidth = 6; ctx.lineJoin = 'round';
  ctx.beginPath();
  for (let s = st.s; s < st.s + 260; s += 4) { const p = pathAt(s); ctx.lineTo(p.x, p.z); }
  ctx.stroke();
  // traffic dots
  ctx.restore();
  ctx.save();
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.clip();
  const toScreen = (x, z) => {
    const dx = x - st.x, dz = z - st.z;
    const fx = Math.sin(th), fz = Math.cos(th);
    const fwd = dx * fx + dz * fz, right = dx * -fz + dz * fx;
    return [cx + right * S, cy - fwd * S];
  };
  for (const ps of polStates) if (ps) {
    const [x, y] = toScreen(ps.x, ps.z);
    const on = Math.floor(ts * 6) % 2;
    ctx.beginPath(); ctx.arc(x, y, 9, 0, Math.PI * 2); ctx.fillStyle = on ? '#ff2a2a' : '#2f6bff'; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
  }
  ctx.restore();
  // player arrow
  ctx.save(); ctx.translate(cx, cy);
  ctx.beginPath(); ctx.moveTo(0, -16); ctx.lineTo(11, 12); ctx.lineTo(0, 6); ctx.lineTo(-11, 12); ctx.closePath();
  ctx.fillStyle = '#fff'; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = '#000'; ctx.stroke();
  ctx.restore();
  // ring + N
  ctx.beginPath(); ctx.arc(cx, cy, R + 4, 0, Math.PI * 2); ctx.lineWidth = 8;
  const wl = wantedLevel(ts);
  ctx.strokeStyle = wl > 0 ? (Math.floor(ts * 4) % 2 ? '#ff3030' : '#3060ff') : '#ffffff'; ctx.stroke();
}
function drawWheel(steer, cx, cy, r) {
  ctx.save(); ctx.translate(cx, cy);
  ctx.globalAlpha = 0.92;
  ctx.beginPath(); ctx.arc(0, 0, r + 14, 0, Math.PI * 2); ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fill();
  ctx.rotate(steer);
  ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.lineWidth = 30; ctx.strokeStyle = '#1d1f24'; ctx.stroke();
  ctx.lineWidth = 6; ctx.strokeStyle = '#4a4e57'; ctx.beginPath(); ctx.arc(0, 0, r + 9, 0, Math.PI * 2); ctx.stroke();
  ctx.fillStyle = '#2b2e35';
  for (const a of [0, Math.PI / 2, -Math.PI / 2]) {
    ctx.save(); ctx.rotate(a); rr(-14, 0, 28, r - 6, 8); ctx.fill(); ctx.restore();
  }
  ctx.beginPath(); ctx.arc(0, 0, 42, 0, Math.PI * 2); ctx.fillStyle = '#31353d'; ctx.fill();
  ctx.lineWidth = 4; ctx.strokeStyle = '#e3262f'; ctx.stroke();
  // top marker
  ctx.fillStyle = '#e3262f'; rr(-10, -r - 16, 20, 30, 5); ctx.fill();
  ctx.restore();
}
function drawPedal(x, y, w, h, label, pressed, col) {
  ctx.save();
  const sc = pressed ? 0.92 : 1;
  ctx.translate(x + w / 2, y + h);
  ctx.scale(sc, pressed ? 0.88 : 1);
  ctx.translate(-w / 2, -h);
  rr(0, 0, w, h, 18); ctx.fillStyle = pressed ? col : 'rgba(40,42,48,0.85)'; ctx.fill();
  ctx.lineWidth = 6; ctx.strokeStyle = pressed ? '#fff' : 'rgba(255,255,255,0.45)'; ctx.stroke();
  ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 6;
  for (let yy = 30; yy < h - 30; yy += 26) { ctx.beginPath(); ctx.moveTo(18, yy); ctx.lineTo(w - 18, yy); ctx.stroke(); }
  ctx.restore();
  txt(label, x + w / 2, y + h + 34, 26, '#fff', { stroke: '#000', sw: 6 });
}
function drawSpeedo(kmh, cx, cy, nitro) {
  ctx.save();
  ctx.translate(cx, cy);
  rr(-190, -78, 380, 156, 30); ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fill();
  ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.stroke();
  const f = clamp(kmh / 300, 0, 1);
  rr(-160, 46, 320, 14, 7); ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.fill();
  const g = ctx.createLinearGradient(-160, 0, 160, 0); g.addColorStop(0, '#3ee6ff'); g.addColorStop(0.6, '#ffd23f'); g.addColorStop(1, '#ff3b3b');
  rr(-160, 46, 320 * f, 14, 7); ctx.fillStyle = g; ctx.fill();
  ctx.restore();
  txt(String(Math.round(kmh)).padStart(3, '0'), cx - 20, cy - 12, 92, '#ffffff', { italic: true, shadow: nitro ? '#3ee6ff' : 'rgba(0,0,0,0)', blur: 24 });
  txt('KM/H', cx + 130, cy + 4, 26, '#ffd23f', { weight: 800 });
}
function drawHUD(t, ts, st, polStates, steer, gas, brake) {
  // vignette
  const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.72);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.45)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  // police flash tint
  const wl = wantedLevel(ts);
  const nearPol = polStates.some((p) => p && Math.hypot(p.x - st.x, p.z - st.z) < 70);
  if (wl > 0 && nearPol) {
    const on = Math.floor(ts * 6) % 2;
    const gr = ctx.createLinearGradient(on ? 0 : W, 0, on ? 260 : W - 260, 0);
    gr.addColorStop(0, on ? 'rgba(255,30,30,0.35)' : 'rgba(40,80,255,0.35)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
  }
  // speed lines
  const kmh = st.v * 3.6;
  if (kmh > 170 && t < 17.6) {
    const a = clamp((kmh - 170) / 80, 0, 1) * 0.5;
    ctx.save(); ctx.strokeStyle = `rgba(255,255,255,${a})`;
    let sd = Math.floor(t * 30) * 7919;
    const r2 = () => { sd = (sd * 16807) % 2147483647; return sd / 2147483647; };
    for (let i = 0; i < 26; i++) {
      const ang = r2() * Math.PI * 2, r0 = 520 + r2() * 300, len = 120 + r2() * 260;
      ctx.lineWidth = 2 + r2() * 4;
      ctx.beginPath(); ctx.moveTo(W / 2 + Math.cos(ang) * r0, H * 0.46 + Math.sin(ang) * r0 * 1.4); ctx.lineTo(W / 2 + Math.cos(ang) * (r0 + len), H * 0.46 + Math.sin(ang) * (r0 + len) * 1.4); ctx.stroke();
    }
    ctx.restore();
  }
  // top gradient for readability
  const tg = ctx.createLinearGradient(0, 0, 0, 480); tg.addColorStop(0, 'rgba(0,0,0,0.45)'); tg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = tg; ctx.fillRect(0, 0, W, 480);
  const bg = ctx.createLinearGradient(0, H - 560, 0, H); bg.addColorStop(0, 'rgba(0,0,0,0)'); bg.addColorStop(1, 'rgba(0,0,0,0.5)');
  ctx.fillStyle = bg; ctx.fillRect(0, H - 560, W, 560);

  drawMinimap(st, ts, polStates);
  // stars
  for (let i = 0; i < 5; i++) {
    const filled = i < wl;
    const flash = filled && i === wl - 1 && Math.floor(ts * 5) % 2 === 0 && ts < 18;
    star(W - 70 - (4 - i) * 78, 232, 32, filled, flash ? '#ffffff' : '#ffd23f');
  }
  // cash
  shownCash = cashAt(ts);
  txt('$' + String(shownCash).padStart(8, '0'), W - 40, 155, 64, '#5fe36a', { align: 'right', stroke: '#000', sw: 12 });
  // clock
  txt('12:47', W - 40, 88, 40, '#ffffff', { align: 'right', stroke: '#000', sw: 8, weight: 800 });
  // speedo top-center below minimap row
  drawSpeedo(kmh, W / 2, 470, ts > 14.6 && ts < 17.6);
  // mission text
  let mission = null;
  if (ts > 1.9 && ts < 4.7) mission = ['Deliver the car to the ', 'docks', '#3ee6ff'];
  if (ts > 6.0 && ts < 9.6) mission = ['Lose the ', 'cops!', '#ff4d4d'];
  if (ts > 14.4 && ts < 16.6) mission = ['NITRO ', 'BOOST!', '#3ee6ff'];
  if (mission) {
    ctx.save(); ctx.font = `800 44px ${FONT}`;
    const w1 = ctx.measureText(mission[0]).width, w2 = ctx.measureText(mission[1]).width;
    const x0 = W / 2 - (w1 + w2) / 2, y = H - 470;
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    ctx.lineWidth = 9; ctx.strokeStyle = '#000';
    ctx.strokeText(mission[0], x0, y); ctx.strokeText(mission[1], x0 + w1, y);
    ctx.fillStyle = '#fff'; ctx.fillText(mission[0], x0, y);
    ctx.fillStyle = mission[2]; ctx.fillText(mission[1], x0 + w1, y);
    ctx.restore();
  }
  // controls (mobile driving-game style)
  if (t < 17.8) {
    const ca = 1 - smooth((t - 17.5) / 0.3);
    ctx.save(); ctx.globalAlpha = ca;
    drawWheel(steer, 245, H - 260, 165);
    drawPedal(W - 330, H - 330, 110, 170, 'BRAKE', brake, '#ff4d4d');
    drawPedal(W - 185, H - 400, 130, 240, 'GAS', gas, '#2fd36b');
    // nitro button
    const nOn = ts > 14.6 && ts < 17.6;
    ctx.beginPath(); ctx.arc(W - 120, H - 560, 62, 0, Math.PI * 2);
    ctx.fillStyle = nOn ? '#3ee6ff' : 'rgba(40,42,48,0.85)'; ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = '#fff'; ctx.stroke();
    txt('N₂O', W - 120, H - 560, 34, nOn ? '#002a33' : '#3ee6ff');
    ctx.restore();
  }
  // popups
  for (const p of popups) {
    const age = ts - p.t;
    if (age < 0 || age > 0.95 || p.t > 17.7) continue;
    const pop = age < 0.15 ? 0.4 + 0.8 * (age / 0.15) : age < 0.25 ? 1.2 - (age - 0.15) * 2 : 1;
    const alpha = age > 0.75 ? 1 - (age - 0.75) / 0.2 : 1;
    const y = (p.big ? 760 : 820) - age * 60;
    ctx.save(); ctx.globalAlpha = clamp(alpha, 0, 1);
    ctx.translate(W / 2, y); ctx.scale(pop, pop); ctx.rotate(-0.05);
    txt(p.text, 0, 0, p.big ? 120 : 92, p.col, { italic: true, stroke: '#000', sw: 16 });
    txt(p.sub, 0, p.big ? 86 : 78, p.big ? 44 : 54, '#ffffff', { italic: true, stroke: '#000', sw: 10 });
    ctx.restore();
  }
  // intro title
  if (t < 2.1) {
    const a = t < 0.15 ? t / 0.15 : t > 1.75 ? 1 - (t - 1.75) / 0.35 : 1;
    const sl = 1 - smooth(t / 0.35);
    ctx.save(); ctx.globalAlpha = clamp(a, 0, 1);
    ctx.translate(W / 2 - sl * 600, 820); ctx.rotate(-0.06);
    rr(-470, -150, 940, 300, 30); ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fill();
    txt('CITY', 0, -52, 150, '#ffd23f', { italic: true, stroke: '#000', sw: 18 });
    txt('RUSH', 0, 78, 150, '#ff3b3b', { italic: true, stroke: '#000', sw: 18 });
    ctx.restore();
  }
  // ending
  if (ts > 18.0) {
    const age = (t - 17.95) / 1.0;
    const pop = smooth(age / 0.35);
    ctx.save();
    ctx.fillStyle = `rgba(0,0,0,${0.35 * pop})`; ctx.fillRect(0, 640, W, 400);
    ctx.globalAlpha = pop;
    ctx.translate(W / 2, 790); ctx.scale(0.6 + 0.4 * pop, 0.6 + 0.4 * pop);
    txt('ESCAPED!', 0, 0, 150, '#ffd23f', { italic: true, stroke: '#000', sw: 18 });
    txt('MISSION COMPLETE', 0, 120, 52, '#ffffff', { stroke: '#000', sw: 10 });
    txt('+$5000', 0, 190, 64, '#5fe36a', { italic: true, stroke: '#000', sw: 12 });
    ctx.restore();
  }
}

// ---------------------------------------------------------------- frame render
let prevTs = 0, prevSteer = 0;
const audioLog = [];
function renderFrame(fi) {
  const t = fi / FPS, ts = simTime(t);
  const dt = Math.max(1e-4, ts - prevTs);
  const st = playerState(ts);
  // camera heading smoothing (sim time)
  if (camState.th === null) camState.th = st.th;
  let dth = st.th - camState.th; while (dth > Math.PI) dth -= 2 * Math.PI; while (dth < -Math.PI) dth += 2 * Math.PI;
  camState.th += dth * (1 - Math.exp(-dt * 4.2));

  // player
  const spin = -st.s / 0.4;
  const roll = clamp(-st.drift * 0.12 + st.k * st.v * 0.02, -0.12, 0.12);
  const pitch = clamp(-st.acc * 0.0022, -0.05, 0.05);
  const steerAng = clamp(-st.drift * 0.9 + st.k * 6, -0.55, 0.55);
  placeVehicle(player, st.x, st.z, st.yaw, { spin, roll, pitch, steer: steerAng });
  const nitro = ts > 14.6 && ts < 17.6;
  flames.forEach((f, i) => { f.visible = nitro; f.scale.set(1, 0.7 + 0.5 * Math.abs(Math.sin(fi * 2.3 + i)), 1); });

  // skids + smoke
  const fx = Math.sin(st.yaw), fz = Math.cos(st.yaw);
  const drifting = Math.abs(st.drift) > 0.22;
  [[0.85, -1.3], [-0.85, -1.3], [0.85, 1.3], [-0.85, 1.3]].forEach(([lx, lz], i) => {
    const wx = st.x + -fz * -lx + fx * lz, wz = st.z + fx * -lx + fz * lz;
    // careful: right vector = (-fz, fx); local +x on car is left? three: rotation.y yaw maps local +x to (cos yaw, -sin yaw)
    const ax = st.x + Math.cos(st.yaw) * lx + fx * lz, az = st.z - Math.sin(st.yaw) * lx + fz * lz;
    addSkid('p' + i, ax, az, 0, 0, drifting && (i < 2 || Math.abs(st.drift) > 0.4));
    if (drifting && i < 2 && fi % 1 === 0) { spawnSmoke(ax, az, clamp((Math.abs(st.drift) - 0.2) * 2.5, 0.3, 1)); }
  });
  if (nitro && fi % 2 === 0) spawnSmoke(st.x - fx * 2.8, st.z - fz * 2.8, 0.25);
  updateSmoke(dt);

  // police
  const polStates = police.map((pc, i) => {
    const ps = policeState(pc, ts);
    const car = policeCars[i];
    car.visible = !!ps;
    if (ps) {
      placeVehicle(car, ps.x, ps.z, ps.yaw, { spin: -ps.s / 0.4, roll: clamp(-ps.drift * 0.1, -0.1, 0.1), steer: clamp(-ps.drift * 0.9, -0.5, 0.5) });
      const on = Math.floor(ts * 7 + i) % 2 === 0;
      const { glowR, glowB } = car.userData.glow;
      glowR.visible = on; glowB.visible = !on;
      car.userData.bar.r.material.color.set(on ? '#ff2a2a' : '#551111');
      car.userData.bar.b.material.color.set(!on ? '#2a5bff' : '#111a55');
      if (Math.abs(ps.drift) > 0.25) {
        const pfx = Math.sin(ps.yaw), pfz = Math.cos(ps.yaw);
        [[0.85, -1.3], [-0.85, -1.3]].forEach(([lx, lz], k) => {
          const ax = ps.x + Math.cos(ps.yaw) * lx + pfx * lz, az = ps.z - Math.sin(ps.yaw) * lx + pfz * lz;
          addSkid('c' + i + k, ax, az, 0, 0, true);
          if (fi % 2 === 0) spawnSmoke(ax, az, 0.5);
        });
      } else { addSkid('c' + i + '0', 0, 0, 0, 0, false); addSkid('c' + i + '1', 0, 0, 0, 0, false); }
    }
    return ps;
  });
  // traffic
  for (const c of traffic) {
    const q = trafficPos(c, ts);
    if (!q || Math.hypot(q.x - st.x, q.z - st.z) > 260) { c.obj.visible = false; continue; }
    c.obj.visible = true;
    placeVehicle(c.obj, q.x, q.z, q.yaw, { spin: -c.v * ts / 0.4 });
  }
  updatePeds(ts);

  // camera
  const ws = shotWeights(t);
  const pos = new THREE.Vector3(), tgt = new THREE.Vector3(); let fov = 0;
  SHOTS.forEach(([m], i) => {
    if (ws[i] < 1e-4) return;
    const c = camFor(m, st, t, ts);
    pos.addScaledVector(c.pos, ws[i]); tgt.addScaledVector(c.tgt, ws[i]); fov += c.fov * ws[i];
  });
  // shake
  const shake = clamp((st.v - 40) / 40, 0, 1) * (t < 17.5 ? 0.09 : 0) + (nitro ? 0.08 : 0);
  pos.x += Math.sin(fi * 1.7) * shake; pos.y += Math.sin(fi * 2.3 + 1) * shake; pos.z += Math.cos(fi * 1.9) * shake;
  camera.position.copy(pos); camera.fov = fov; camera.updateProjectionMatrix();
  camera.lookAt(tgt);
  // shadow follows player
  sun.position.set(st.x + 60, 110, st.z + 40); sun.target.position.set(st.x, 0, st.z);
  window.dome.position.copy(camera.position);

  renderer.render(scene, camera);
  ctx.drawImage(renderer.domElement, 0, 0);
  const steerHUD = clamp(-st.drift * 2.2 - st.k * 18, -2.2, 2.2) * -1;
  const sm = prevSteer + (steerHUD - prevSteer) * 0.35; prevSteer = sm;
  const gas = st.acc > 0.5 || (st.acc > -0.5 && st.v > 60);
  const brake = st.acc < -3;
  drawHUD(t, ts, st, polStates, sm, gas, brake);
  // white flash at nitro start
  if (ts > 14.6 && ts < 14.8) { ctx.fillStyle = `rgba(200,240,255,${0.45 * (1 - (ts - 14.6) / 0.2)})`; ctx.fillRect(0, 0, W, H); }

  const nearestPol = Math.min(...polStates.filter(Boolean).map((p) => Math.hypot(p.x - st.x, p.z - st.z)), 999);
  audioLog.push({ t, ts, v: st.v, drift: st.drift, acc: st.acc, nitro, pol: nearestPol, wl: wantedLevel(ts) });
  prevTs = ts;
  return out.toDataURL('image/jpeg', 0.93);
}
window.renderFrame = renderFrame;
window.getMeta = () => ({ audioLog, nearMiss: window.nearMiss, popups: popups.map((p) => ({ t: p.t, text: p.text })), corners: cornerTimes, traffic: traffic.length, simEndS: simAt(simTime(DUR)).s, pathLen: P.len });
window.ready = true;
