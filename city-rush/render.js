const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
(async () => {
  const [, , outFile, fStart = '0', fEnd = '600', step = '1'] = process.argv;
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', (m) => console.log('[page]', m.text()));
  page.on('pageerror', (e) => console.log('[err]', e.message));
  await page.goto('file://' + path.resolve('index.html'));
  await page.addScriptTag({ path: 'node_modules/three/build/three.min.js' });
  await page.evaluate(() => document.fonts.load('900 40px Inter'));
  await page.addScriptTag({ path: process.env.SCENE || 'scene.js' });
  await page.waitForFunction(() => window.ready);
  console.log(JSON.stringify(await page.evaluate(() => { const m = getMeta(); delete m.audioLog; return m; })));
  const a = +fStart, b = +fEnd, st = +step;
  let ff = null;
  if (outFile.endsWith('.mp4')) {
    ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', '30', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', outFile], { stdio: ['pipe', 'ignore', 'inherit'] });
  }
  const t0 = Date.now();
  for (let f = 0; f < b; f++) {
    // must render every frame sequentially (stateful skids/smoke); only output selected
    const url = await page.evaluate((i) => renderFrame(i), f);
    if (f < a || (f - a) % st) continue;
    const buf = Buffer.from(url.split(',')[1], 'base64');
    if (ff) { if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r)); }
    else fs.writeFileSync(`${outFile}_${String(f).padStart(3, '0')}.jpg`, buf);
    if (f % 30 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(1) + 's');
  }
  fs.writeFileSync(process.env.META || 'meta.json', JSON.stringify(await page.evaluate(() => getMeta())));
  if (ff) { ff.stdin.end(); await new Promise((r) => ff.on('close', r)); }
  await browser.close();
})();
