// Check the raised shoe-free candidate and standalone world-coordinate meshes.
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const output = process.argv[4] || 'fea/generated/no-shoes-viewer';
fs.mkdirSync(output, {recursive: true});
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport: {width: 1600, height: 1100}});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route(url => url.origin === new URL(base).origin && url.pathname === new URL(base).pathname,
      async route => {
        const response = await route.fetch();
        await route.fulfill({response, body: (await response.text()).replace('</script>\n  </body>',
          'window.cadTest = {meshes, camera, controls, THREE};</script>\n  </body>')});
      });
    for (const key of ['no-shoes-development']) {
      await page.goto(base+'?view=rear');
      const manifest = await page.evaluate(async key => (await fetch('hybrid/'+key+'/parts.json')).json(), key);
      await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
        manifest.parts.length, {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), key);
      assert.deepEqual(await page.locator('#model optgroup').evaluateAll(groups => groups.map(g => g.label)), ['Current design', 'Development candidates', 'Historical / archive designs']);
      assert.equal(await page.locator('#model optgroup').first().locator('option').count(), 1);
      assert.match(await page.locator('#design-details').innerText(), /NOT build-ready/);
      assert.ok(await page.locator('#model-documents a').count() >= 2);
      const panel = page.locator('header');
      const before = await panel.boundingBox();
      await page.mouse.move(before.x + before.width - 3, before.y + before.height - 3);
      await page.mouse.down();
      await page.mouse.move(before.x + before.width + 180, before.y + before.height + 180, {steps: 12});
      await page.mouse.up();
      const after = await panel.boundingBox();
      assert.ok(after.width > before.width + 100, 'Information panel grows horizontally');
      assert.ok(after.height > before.height + 100, 'Information panel grows vertically');
      await page.screenshot({path: path.join(output, key+'-resized-panel.png')});
      await page.setViewportSize({width: 390, height: 700});
      const mobile = await panel.boundingBox();
      assert.ok(mobile.width <= 390 && mobile.height <= 700, 'Panel stays inside smaller viewport');
      await page.setViewportSize({width: 1600, height: 1100});
      await page.screenshot({path: path.join(output, key+'-rear.png')});
      assert.equal(manifest.design.main_face_height_mm, 277);
      assert.ok(!manifest.parts.some(p => p.name.includes('steel_shoe')));
      assert.ok(manifest.parts.every(p => p.path.startsWith('hybrid/'+key+'/models/')),
        'Current meshes do not depend on historical assets');
      assert.ok(manifest.parts.every(p => !p.translation_mm), 'Meshes use world coordinates');
      const positioned = await page.evaluate(() => window.cadTest.meshes
        .filter(m => m.userData.part.name !== 'McKay')
        .every(m => m.position.toArray().every(v => v === 0)));
      assert.ok(positioned);
      const floor = await page.evaluate(() => window.cadTest.meshes
        .filter(m => /^(lumber_leg_|base_post_)/.test(m.userData.part.name))
        .map(m => { m.geometry.computeBoundingBox(); return m.geometry.boundingBox.min.z + m.position.z; }));
      assert.ok(floor.length >= 2);
      assert.ok(floor.every(z => Math.abs(z) < .01));

    }
    const pivot = 'thick-leg-centered-pivot-development';
    await page.locator('#model').selectOption(pivot);
    await page.waitForURL('**model='+pivot+'*');
    const pivotManifest = await page.evaluate(async key => (await fetch('hybrid/'+key+'/parts.json')).json(), pivot);
    await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
      pivotManifest.parts.length, {timeout:120000});
    assert.equal(pivotManifest.design.leg_stock, '4x6');
    assert.equal(pivotManifest.design.leg_bolt_count, 2);
    assert.equal(pivotManifest.parts.filter(p => p.fabrication.kind === 'bolt').length, 10);
    assert.match(await page.locator('#design-details').innerText(), /Free relative rotation is an analysis assumption/);
    assert.equal(await page.locator('#model optgroup').nth(1).locator('option:checked').count(), 1);
    await page.screenshot({path:path.join(output, pivot+'-rear.png')});
    await page.locator('#model').selectOption('round-reinforcement-development');
    await page.waitForURL('**model=round-reinforcement-development*');
    await page.waitForFunction(() => document.querySelector('#model')?.value === 'round-reinforcement-development');
    assert.equal(await page.locator('#model optgroup').nth(2).locator('option:checked').count(), 1);
    assert.deepEqual(errors, []);
    console.log('Shoe-free candidate loaded; 277mm datum, standalone meshes and floor contact verified');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
