// Serve site/ first. Arguments: Playwright module path, base URL, screenshot directory.
// Response instrumentation exposes existing viewer state; clicks exercise the actual UI.
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const artifacts = process.argv[4] || 'fea/generated/square-2x6-viewer';
const variants = process.argv[5] ? [process.argv[5]] : ['square-2x6-development', 'square-2x6-revised-development'];
fs.mkdirSync(artifacts, { recursive: true });
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('requestfailed', r => errors.push(r.url() + ': ' + r.failure().errorText));
    page.on('response', r => { if (r.status() >= 400) errors.push(r.status() + ': ' + r.url()); });
    await page.route(url => url.origin === new URL(base).origin && url.pathname === new URL(base).pathname,
      async route => {
        const response = await route.fetch();
        await route.fulfill({ response, body: (await response.text()).replace('</script>\n  </body>',
          'window.cadTest = {meshes, camera, controls, overlay};</script>\n  </body>') });
      });
    async function loaded() {
      const manifest = await page.evaluate(async () => {
        const model = document.querySelector('#model').value;
        return (await fetch('hybrid/'+model+'/parts.json')).json();
      });
      await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
        manifest.parts.length, { timeout: 120000 });
      assert.ok(manifest.parts.some(p => p.fabrication.kind === 'screw'));
      assert.ok(manifest.parts.some(p => p.fabrication.kind === 'bolt'));
      assert.ok(!manifest.parts.some(p => p.fabrication.kind === 'insert' || p.name.startsWith('insert_')));
      assert.match(await page.locator('#design-details').innerText(), /NOT build-ready/);
      return manifest;
    }
    await page.goto(base);
    await loaded();
    assert.equal(await page.locator('#model').inputValue(), 'single-2x6-development');
    for (const model of variants) {
      await page.goto(base+'?model='+model);
      await loaded();
      assert.equal(await page.locator('#model').inputValue(), model);
      await page.screenshot({ path: path.join(artifacts, model+'-front.png') });
      await page.goto(base+'?model='+model+'&view=rear');
      const manifest = await loaded();
      assert.ok(await page.evaluate(() => window.cadTest.camera.position.y < window.cadTest.controls.target.y));
      await page.locator('#person').uncheck();
      await page.locator('#dimensions').uncheck();
      await page.screenshot({ path: path.join(artifacts, model+'-rear.png') });
      // Target the rear surface of the left principal at mid-height, away from rails.
      await page.evaluate(model => {
        const a = 40*Math.PI/180, x = model === 'single-2x6-development' ? 0 : -57.15, s = 700, n = 139.7;
        const y = -18*(1+Math.cos(a))+s*Math.sin(a)-n*Math.cos(a)-950;
        const z = 225+18*Math.sin(a)+s*Math.cos(a)+n*Math.sin(a);
        const {camera, controls} = window.cadTest;
        camera.setViewOffset(1600,1100,-380,-300,1600,1100);
        camera.position.set(-x, y-800*Math.cos(a), z+800*Math.sin(a));
        controls.target.set(-x,y,z); controls.update();
      }, model);
      await page.waitForTimeout(250);
      await page.mouse.click(1180, 850);
      assert.match(await page.locator('#part').innerText(), model === 'single-2x6-development' ? /^base_principal_center:/ : /^base_principal_left:/);
      assert.match(await page.locator('#part').innerText(), /mm.*ft.*in/);
      await page.screenshot({ path: path.join(artifacts, model+'-principal.png') });
      await page.goto(base+'?model='+model+'&view=rear');
      await loaded();
      await page.locator('#overlay').selectOption('grid');
      await page.waitForFunction(() => window.cadTest.overlay.children.length === 23);
      const stations = await page.evaluate(() => window.cadTest.overlay.children.slice(11).map(label =>
        (label.position.z-225+.5*Math.sin(40*Math.PI/180))/Math.cos(40*Math.PI/180)));
      manifest.design.tnut_row_stations_mm.forEach((station, i) => assert.ok(Math.abs(stations[i]-station)<1e-6));
      await page.setViewportSize({ width: 390, height: 844 });
      await page.screenshot({ path: path.join(artifacts, model+'-narrow.png') });
      await page.setViewportSize({ width: 1600, height: 1100 });
      console.log(model+': '+manifest.parts.length+' meshes, full hardware, selection and corrected grid passed');
    }
    // Dropdown navigation must preserve the requested candidate through a real reload.
    if (variants.length === 1) {
      await page.goto(base+'?model=square-2x6-revised-development');
      await loaded();
    }
    await page.selectOption('#model', variants[0]);
    await page.waitForURL(url => url.searchParams.get('model') === variants[0]);
    await loaded();
    assert.deepEqual(errors, []);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
