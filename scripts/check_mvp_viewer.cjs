// Serve site/ on localhost:8766; pass an installed Playwright module path.
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const models = process.argv.slice(3);
if (!models.length) models.push('wood-first-mvp', 'commercial-bracket-mvp');
assert.ok(models.every(model => ['wood-first-mvp', 'commercial-bracket-mvp',
  'square-cut-bracket', 'square-cut-wood-blocks', 'bolted-clip-frame', 'bolted-block-frame', 'lean-38mm-frame', 'continuous-lean-frame', 'bearing-lean-frame', 'base-bearing-concept', 'timber-base-development', 'panel-insert-development', 'wide-principal-development'].includes(model)));

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => errors.push(request.url()));
    await page.route('http://127.0.0.1:8766/?*', async route => {
      const response = await route.fetch();
      await route.fulfill({response, body: (await response.text()).replace('</script>\n  </body>',
        'window.cadTest = {meshes, camera, controls, overlay};</script>\n  </body>')});
    });
    for (const model of models) {
      await page.goto('http://127.0.0.1:8766/?model='+model);
      const manifest = await page.evaluate(async model =>
        (await fetch('hybrid/'+model+'/parts.json')).json(), model);
      await page.waitForFunction(count => window.cadTest?.meshes.filter(m =>
        m.userData.part.name !== 'McKay').length === count, manifest.parts.length, {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.match(await page.locator('#design-details').innerText(), /NOT build-ready/);
      await page.screenshot({path: '/tmp/mini-moonboard-'+model+'-front.png'});
      await page.locator('#person').uncheck();
      await page.locator('#dimensions').uncheck();
      // Aim at an unobstructed rear face of the new continuous central support.
      await page.evaluate(model => {
        const lean = ['lean-38mm-frame', 'continuous-lean-frame', 'bearing-lean-frame', 'base-bearing-concept', 'timber-base-development', 'panel-insert-development', 'wide-principal-development'].includes(model);
        const a = 40*Math.PI/180, x = lean ? -57.15 : -76.35, s = 700, n = lean ? 139.7 : 177.8;
        const y = -18*(1+Math.cos(a))+s*Math.sin(a)-n*Math.cos(a)-950;
        const z = 225+18*Math.sin(a)+s*Math.cos(a)+n*Math.sin(a);
        const {camera, controls} = window.cadTest;
        camera.setViewOffset(1440,1000,-380,-300,1440,1000);
        camera.position.set(-x, y-800*Math.cos(a), z+800*Math.sin(a));
        controls.target.set(-x,y,z); controls.update();
      }, model);
      await page.waitForTimeout(150);
      await page.mouse.click(1100, 800);
      assert.match(await page.locator('#part').innerText(), /wood_principal_left|lean_principal_left|base_principal_left|fastener_wood_principal_ledge_left/);
      assert.match(await page.locator('#part').innerText(), /mm.*ft.*in/);
      if (model === 'lean-38mm-frame') assert.match(await page.locator('#part').innerText(), /2298\.7 × 139\.7 × 38\.1 mm/);
      if (['continuous-lean-frame', 'bearing-lean-frame'].includes(model)) assert.match(await page.locator('#part').innerText(), /2260\.6 × 139\.7 × 38\.1 mm/);
      await page.screenshot({path: '/tmp/mini-moonboard-'+model+'-selection.png'});
      await page.goto('http://127.0.0.1:8766/?model='+model+'&view=rear');
      await page.waitForFunction(count => window.cadTest?.meshes.filter(m =>
        m.userData.part.name !== 'McKay').length === count, manifest.parts.length, {timeout: 120000});
      assert.ok(await page.evaluate(() => window.cadTest.camera.position.y < window.cadTest.controls.target.y));
      await page.screenshot({path: '/tmp/mini-moonboard-'+model+'-rear.png'});
      if (['base-bearing-concept', 'timber-base-development', 'panel-insert-development', 'wide-principal-development'].includes(model)) {
        // Select labels before the model metadata arrives: they must refresh
        // to the corrected stations, not retain the historical uniform grid.
        let release;
        const pending = new Promise(resolve => { release = resolve; });
        const pattern = '**/hybrid/'+model+'/parts.json';
        await page.route(pattern, async route => { await pending; await route.continue(); });
        await page.goto('http://127.0.0.1:8766/?model='+model, {waitUntil: 'domcontentloaded'});
        await page.locator('#overlay').selectOption('grid');
        release();
        await page.waitForFunction(() => window.cadTest?.overlay.children.length === 23 &&
          Math.abs(window.cadTest.overlay.children[11].position.z -
            (225-.5*Math.sin(40*Math.PI/180)+99.2*Math.cos(40*Math.PI/180))) < 1e-6);
        const stations = await page.evaluate(() => window.cadTest.overlay.children.slice(11).map(label =>
          (label.position.z-225+.5*Math.sin(40*Math.PI/180))/Math.cos(40*Math.PI/180)));
        manifest.design.tnut_row_stations_mm.forEach((station, i) => assert.ok(Math.abs(stations[i]-station)<1e-6));
        await page.waitForFunction(count => window.cadTest.meshes.filter(m =>
          m.userData.part.name !== 'McKay').length === count, manifest.parts.length);
        await page.screenshot({path: '/tmp/mini-moonboard-'+model+'-grid.png'});
        await page.unroute(pattern);
      }
      if (model === 'bearing-lean-frame') {
        await page.locator('#person').uncheck();
        await page.locator('#dimensions').uncheck();
        await page.evaluate(() => {
          const a = 40*Math.PI/180, x = -509.2, s = 75, n = 40.8;
          const y = -18*(1+Math.cos(a))+s*Math.sin(a)-n*Math.cos(a)-950;
          const z = 225+18*Math.sin(a)+s*Math.cos(a)+n*Math.sin(a);
          const {camera, controls} = window.cadTest;
          camera.setViewOffset(1440,1000,-380,-300,1440,1000);
          camera.position.set(-x,y-500*Math.cos(a),z+500*Math.sin(a));
          controls.target.set(-x,y,z); controls.update();
        });
        await page.waitForTimeout(150);
        await page.mouse.click(1100, 800);
        assert.match(await page.locator('#part').innerText(), /^clip_mvp_ledge_2:/);
        assert.match(await page.locator('#part').innerText(), /101\.6 × 50\.8 × 50\.8 mm/);
        assert.match(await page.locator('#part').innerText(), /PROVISIONAL/);
        await page.screenshot({path: '/tmp/mini-moonboard-'+model+'-lower-angle.png'});
      }
      console.log(model+': loaded '+manifest.parts.length+' meshes; rear selection and dual units passed');
    }
    assert.deepEqual(errors, []);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
