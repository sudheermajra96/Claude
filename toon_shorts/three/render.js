// Render merge.html frames headlessly: node render.js <out_dir> [first] [last] [step]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const out = process.argv[2];
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await page.goto('file://' + path.join(__dirname, 'merge.html'));
  await page.waitForFunction(() => window.ready === true);
  const dur = await page.evaluate(() => window.DUR);
  const n = Math.round(dur * 30);
  const first = +(process.argv[3] || 0), last = +(process.argv[4] || n - 1), step = +(process.argv[5] || 1);
  for (let i = first; i <= last; i += step) {
    const url = await page.evaluate(i => window.renderAt(i / 30, window.frameSrc(i)), i);
    fs.writeFileSync(path.join(out, String(i).padStart(5, '0') + '.jpg'), Buffer.from(url.split(',')[1], 'base64'));
  }
  await browser.close();
})();
