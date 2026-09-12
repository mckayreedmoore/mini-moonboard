// Check the raised shoe-free candidate and its displayed transforms.
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
      await page.goto(base+'?model='+key+'&view=rear');
      const manifest = await page.evaluate(async key => (await fetch('hybrid/'+key+'/parts.json')).json(), key);
      await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
        manifest.parts.length, {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), key);
      assert.match(await page.locator('#design-details').innerText(), /NOT build-ready/);
      assert.ok(await page.locator('#model-documents a').count() >= 2);
      await page.screenshot({path: path.join(output, key+'-rear.png')});
      assert.equal(manifest.design.main_face_height_mm, 277);
      assert.ok(!manifest.parts.some(p => p.name.includes('steel_shoe')));
      const transformed = await page.evaluate(() => window.cadTest.meshes
        .filter(m => m.userData.part.translation_mm)
        .every(m => m.position.toArray().every((v, i) => v === m.userData.part.translation_mm[i])));
      assert.ok(transformed);
      const floor = await page.evaluate(() => window.cadTest.meshes
        .filter(m => /^(lumber_leg_|base_post_)/.test(m.userData.part.name))
        .map(m => { m.geometry.computeBoundingBox(); return m.geometry.boundingBox.min.z + m.position.z; }));
      assert.ok(floor.length >= 2);
      assert.ok(floor.every(z => Math.abs(z) < .01));

    }
    assert.deepEqual(errors, []);
    console.log('Shoe-free candidate loaded; 277mm datum, inherited transforms and floor contact verified');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
