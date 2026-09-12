// Load both assessed leg variants and inspect the complete wider-leg bolt stack.
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const output = process.argv[4] || 'fea/generated/wider-leg-viewer';
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
    for (const key of ['round-reinforcement-development', 'wider-leg-development']) {
      await page.goto(base+'?model='+key+'&view=rear');
      const manifest = await page.evaluate(async key => (await fetch('hybrid/'+key+'/parts.json')).json(), key);
      await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
        manifest.parts.length, {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), key);
      assert.match(await page.locator('#design-details').innerText(), /NOT build-ready/);
      assert.ok(await page.locator('#model-documents a').count() >= 3);
      await page.screenshot({path: path.join(output, key+'-rear.png')});
      if (key === 'wider-leg-development') {
        assert.equal(manifest.design.leg_bolt_count, 12);
        const stacks = manifest.parts.filter(p => p.fabrication.connection_name?.startsWith('lumber_leg_bolt_'));
        assert.equal(stacks.length, 96);
        assert.equal(new Set(stacks.map(p => p.fabrication.connection_name)).size, 12);
        const select = page.locator('#bolt-view');
        await select.selectOption('lumber_leg_bolt_left_1');
        const visible = await page.evaluate(() => window.cadTest.meshes.filter(m => m.visible).map(m => m.userData.part));
        assert.equal(visible.length, 8);
        assert.deepEqual(visible.map(p => p.fabrication.hardware_role).sort(),
          ['shaft', 'head_plate', 'nut_plate', 'spacer_1', 'spacer_2', 'spacer_3', 'head', 'nut'].sort());
        await page.screenshot({path: path.join(output, 'complete-eight-piece-leg-stack.png')});
      }
    }
    assert.deepEqual(errors, []);
    console.log('Both leg variants loaded; 12 complete eight-piece wider stacks; comparison documents and representative inspection passed');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
