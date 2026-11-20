# Assembles runner.js from runner_head.js + the shared city/vehicle code in scene.js + runner_tail.js
src = open('scene.js').read()
tail = open('runner_tail.js').read()
def between(a, b):
    i = src.index(a); j = src.index(b, i); return src[i:j]
city = between('// ---------------------------------------------------------------- three scene', '// ---------------------------------------------------------------- vehicles')
veh = between('// ---------------------------------------------------------------- vehicles', 'const player = makeVehicle')
fx = between('// skid marks', '// ---------------------------------------------------------------- camera schedule')
props_start = tail.index('// ---------------------------------------------------------------- park / alley')
props_end = tail.index('// ---------------------------------------------------------------- characters')
props = tail[props_start:props_end]
tail = tail[:props_start] + tail[props_end:]
def rep(s, a, b):
    assert a in s, a
    return s.replace(a, b, 1)
city = rep(city, 'blk.position.set(cx, 0.125, cz); blk.receiveShadow = true; scene.add(blk);\n',
  "blk.position.set(cx, 0.125, cz); blk.receiveShadow = true; scene.add(blk);\n      const ov = blockOverride(cx, cz);\n      if (ov === 'park') { buildPark(cx, cz); continue; }\n      if (ov === 'alley') { buildAlley(cx, cz); continue; }\n")
city = rep(city, '  instanced(new THREE.CylinderGeometry(0.18, 0.25, 2.2, 6)',
  "  for (const arr of [trees, lamps]) for (let i = arr.length - 1; i >= 0; i--) if (nearRoute(arr[i][0], arr[i][1], 2.6)) arr.splice(i, 1);\n  for (let i = peds.length - 1; i >= 0; i--) if (nearRoute(peds[i].x, peds[i].z, 6.5)) peds.splice(i, 1);\n  instanced(new THREE.CylinderGeometry(0.18, 0.25, 2.2, 6)")
city = rep(city, '    for (const [sx, sz] of [[1, 1], [-1, -1]]) {\n      poles.push',
  '    for (const [sx, sz] of [[1, 1], [-1, -1]]) {\n      if (nearRoute(x + sx * 8.5, z + sz * 8.5, 2.6)) continue;\n      poles.push')
city = rep(city, '// blocks\n', props + '// blocks\n')
open('runner.js', 'w').write(open('runner_head.js').read() + city + veh + fx + tail)
print('ok')
