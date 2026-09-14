// Check the current spliced-knee package and preserved development designs.
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const screenshots = process.env.CAD_VIEWER_SCREENSHOTS !== '0';
const output = process.argv[4] || 'fea/generated/no-shoes-viewer';
fs.mkdirSync(output, {recursive: true});
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport: {width: 1600, height: 1100}});
    const errors = [];
    page.on('pageerror', e => { errors.push(e.message); console.error('Viewer error:', e.message); });
    await page.route(url => url.origin === new URL(base).origin && url.pathname === new URL(base).pathname,
      async route => {
        const response = await route.fetch();
        await route.fulfill({response, body: (await response.text()).replace('</script>\n  </body>',
          'window.cadTest = {meshes, camera, controls, THREE};</script>\n  </body>')});
      });
    for (const key of ['compact-spliced-knee-development']) {
      console.log('Loading current candidate');
      await page.goto(base+'?view=rear');
      console.log('Page loaded');
      const manifest = await page.evaluate(async key => (await fetch('hybrid/'+key+'/parts.json')).json(), key);
      await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
        manifest.parts.length, {timeout: 120000});
      console.log('All current meshes loaded:', manifest.parts.length);
      assert.equal(await page.locator('#model').inputValue(), key);
      assert.deepEqual(await page.locator('#model optgroup').evaluateAll(groups => groups.map(g => g.label)), ['Current design', 'Development candidates', 'Historical / archive designs']);
      assert.equal(await page.locator('#model optgroup').first().locator('option').count(), 1);
      assert.match(await page.locator('#design-details').innerText(), /conditional/i);
      assert.ok(await page.locator('#model-documents a').count() >= 2);
      if (screenshots) {
      const panel = page.locator('header');
      const before = await panel.boundingBox();
      await page.mouse.move(before.x + before.width - 3, before.y + before.height - 3);
      await page.mouse.down();
      await page.mouse.move(before.x + before.width + 180, before.y + before.height + 180, {steps: 12});
      await page.mouse.up();
      const after = await panel.boundingBox();
      assert.ok(after.width > before.width + 100, 'Information panel grows horizontally');
      assert.ok(after.height > before.height + 100, 'Information panel grows vertically');
      await page.screenshot({path: path.join(output, key+'-resized-panel.png'), timeout: 10000});
      await page.setViewportSize({width: 390, height: 700});
      const mobile = await panel.boundingBox();
      assert.ok(mobile.width <= 390 && mobile.height <= 700, 'Panel stays inside smaller viewport');
      await page.setViewportSize({width: 1600, height: 1100});
      await page.screenshot({path: path.join(output, key+'-rear.png'), timeout: 10000});
      }
      assert.equal(manifest.design.main_face_height_mm, 277);
      assert.equal(manifest.design.leg_bolt_count, 4);
      assert.equal(manifest.design.bolts_per_leg, 2);
      assert.equal(manifest.parts.filter(p => p.fabrication.kind === 'bolt').length, 100);
      assert.match(await page.locator('#design-details').innerText(), /two independent unnotched members/i);
      const stacks = new Map();
      for (const part of manifest.parts.filter(p => p.fabrication.kind === 'bolt')) {
        const name = part.fabrication.connection_name;
        if (!stacks.has(name)) stacks.set(name, []);
        stacks.get(name).push(part.fabrication.hardware_role);
      }
      assert.equal(stacks.size, 20);
      for (const roles of stacks.values()) {
        assert.deepEqual(roles.sort(), ['far_washer', 'head', 'near_washer', 'nut', 'shaft']);
      }
      assert.equal(manifest.design.total_bolt_count, 20);
      assert.equal(manifest.design.knee_piece_count, 4);
      assert.equal(manifest.design.upper_bolt_pitch_mm, 56);
      assert.equal(manifest.parts.filter(p => /^base_knee_(left|right)_(rim|leg)$/.test(p.name)).length, 4);
      for (const document of ['compact-spliced-build-package.md', 'compact-splice-study.md']) {
        assert.equal(await page.locator('#model-documents a[href$="'+document+'"]').count(), 1);
      }
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
    assert.equal(await page.locator('#model optgroup').nth(1).locator('option[value="thick-leg-centered-pivot-development"]').count(), 1);
    for (const key of ['compact-thick-development', 'round-reinforcement-development']) {
      assert.equal(await page.locator('#model optgroup').nth(2).locator('option[value="'+key+'"]').count(), 1);
    }
    assert.deepEqual(errors, []);
    console.log('Spliced-knee candidate loaded; twenty complete bolts, four knee pieces, 277mm datum, standalone meshes and floor contact verified');
  } catch (error) {
    console.error(error);
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
