
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
