// Serve site/ on a dedicated port, then run:
// node scripts/check_lumber_leg_viewer.cjs [playwright-path] [base-url] [artifact-dir]
// Test-response instrumentation exposes existing state only; selection uses real pointer events.
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const artifacts = process.argv[4] || 'fea/generated/lumber-leg-viewer';
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
          'window.cadTest = {meshes, camera, controls};</script>\n  </body>') });
      });
    async function loaded(count) {
      await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
        count, { timeout: 120000 });
    }
    await page.goto(base + '?model=wide-principal-development&view=rear');
    await loaded(291);
    assert.equal(await page.locator('#model').inputValue(), 'wide-principal-development');
    const variants = ['2x6', '2x8', '2x10', '2x12'].flatMap(s => [0, 150, 300].map(e => `lumber-leg-${s}-e${e}`));
    const checked = process.env.CAPTURE_ONLY ? [] : variants;
    for (const model of checked) {
      await page.selectOption('#model', model);
      await page.waitForURL(url => url.searchParams.get('model') === model);
      await loaded(283);
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.match(await page.locator('#design-details').innerText(), /NOT build-ready/);
    }
    const model = 'lumber-leg-2x8-e150';
    await page.selectOption('#model', model);
    await page.waitForURL(url => url.searchParams.get('model') === model);
    await loaded(283);
    await page.locator('#person').uncheck();
    const point = await page.evaluate(() => {
      const { meshes, camera, controls } = window.cadTest;
      const mesh = meshes.find(m => m.userData.part.name === 'lumber_leg_left');
      mesh.geometry.computeBoundingBox(); mesh.updateWorldMatrix(true, false);
      const p = mesh.geometry.boundingBox.getCenter(camera.position.clone()).applyMatrix4(mesh.matrixWorld);
      camera.position.set(p.x + 3500, p.y, p.z + 400);
      controls.target.copy(p); controls.update(); camera.updateMatrixWorld();
      p.project(camera);
      return { x: (p.x + 1) * innerWidth / 2, y: (1 - p.y) * innerHeight / 2 };
    });
    await page.waitForTimeout(250);
    await page.mouse.click(point.x, point.y);
    const card = await page.locator('#part').innerText();
    assert.match(card, /^lumber_leg_left:/);
    assert.match(card, /184.15/);
    assert.match(card, /mm \(.* ft .* in/);
    assert.match(card, /NOT build-ready/);
    await page.locator('#part').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(artifacts, '2x8-e150-selected-leg.png') });
    await page.goto(base);
    await page.waitForSelector('#model');
    assert.equal(await page.locator('#model').inputValue(), 'plywood');
    await page.waitForLoadState('networkidle');
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ variants: checked.length, meshes_per_variant: 283,
      selected: card, screenshot: path.join(artifacts, '2x8-e150-selected-leg.png'), errors }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
