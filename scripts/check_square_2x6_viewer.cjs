// Serve site/ first. Arguments: Playwright module path, base URL, screenshot directory.
// Response instrumentation exposes existing viewer state; clicks exercise the actual UI.
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const artifacts = process.argv[4] || 'fea/generated/square-2x6-viewer';
const variants = process.argv[5] ? [process.argv[5]] : ['angle-base-development'];
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
          'window.cadTest = {meshes, camera, controls, overlay, colorFor};</script>\n  </body>') });
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
      assert.match(await page.locator('header p:nth-of-type(2)').innerText(), /bolts steel gray/);
      assert.match(await page.locator('header p:nth-of-type(2)').innerText(), /red marks an explicit clearance failure, not a strength rating/);
      const colors = await page.evaluate(() => window.cadTest.meshes
        .filter(mesh => mesh.userData.part.fabrication?.kind === 'bolt')
        .map(mesh => ({color: mesh.material.color.getHex(),
          failed: mesh.userData.part.fabrication.clearance_status?.startsWith('FAIL')})));
      assert.ok(colors.length > 0 && colors.every(({color, failed}) => color === (failed ? 0xef5350 : 0x9aa5b1)));
      assert.deepEqual(await page.evaluate(() => [
        window.cadTest.colorFor({fabrication: {kind: 'bolt', clearance_status: 'FAIL: insufficient edge distance'}}),
        window.cadTest.colorFor({fabrication: {kind: 'bolt', clearance_status: 'Unqualified'}}),
      ]), [0xef5350, 0x9aa5b1]);
      return manifest;
    }
    await page.goto(base);
    await loaded();
    assert.equal(await page.locator('#model').inputValue(), 'angle-base-development');
    assert.deepEqual(await page.locator('#model option').evaluateAll(options =>
      options.slice(0, 9).map(option => option.value)), [
        'angle-base-development', 'infill-panel-development', 'split-center-development', 'vertical-principal-development', 'paired-rail-base-development', 'selective-2x6-development', 'single-2x6-development',
        'square-2x6-revised-development', 'square-2x6-development']);
    assert.equal(await page.locator('#model option').last().getAttribute('value'), 'plywood');
    for (const model of variants) {
      await page.goto(base+'?model='+model);
      await loaded();
      assert.equal(await page.locator('#model').inputValue(), model);
      await page.screenshot({ path: path.join(artifacts, model+'-front.png') });
      await page.goto(base+'?model='+model+'&view=rear');
      const manifest = await loaded();
      if (['vertical-principal-development', 'split-center-development', 'infill-panel-development', 'angle-base-development'].includes(model)) {
        const names = ['left_1', 'left_2', 'right_1', 'right_2'];
        const principals = manifest.parts.filter(p => /^base_principal_(left|right)_[12]$/.test(p.name));
        assert.equal(principals.length, 4);
        assert.ok(principals.every(p => p.fabrication.dimensions_mm[1] === 139.7 && p.fabrication.dimensions_mm[2] === 38.1));
        assert.ok(!manifest.parts.some(p => p.name.startsWith('base_rail_mid_')));
        for (const suffix of names) {
          assert.ok(manifest.parts.some(p => p.name === 'base_post_'+suffix));
          assert.ok(manifest.parts.some(p => p.name === 'clip_vertical_base_'+suffix));
          assert.ok(manifest.parts.some(p => p.name === 'clip_vertical_header_'+suffix));
        }
        assert.equal(manifest.design.qualified_for_design, false);
        assert.match(manifest.design.description, /seam (?:is|remains) unsupported between principals/);
      }
      if (model === 'paired-rail-base-development') {
        const rails = manifest.parts.filter(p => p.name.startsWith('base_rail_mid_'));
        assert.equal(rails.length, 4);
        assert.ok(rails.every(p => p.fabrication.dimensions_mm[1] === 139.7 && p.fabrication.dimensions_mm[2] === 38.1));
        assert.ok(manifest.parts.some(p => p.name === 'clip_paired_base_center'));
        assert.equal(manifest.design.qualified_for_design, false);
      }
      assert.ok(await page.evaluate(() => window.cadTest.camera.position.y < window.cadTest.controls.target.y));
      await page.locator('#person').uncheck();
      await page.locator('#dimensions').uncheck();
      await page.screenshot({ path: path.join(artifacts, model+'-rear.png') });
      if (['split-center-development', 'infill-panel-development', 'angle-base-development'].includes(model)) {
        assert.ok(!manifest.parts.some(p => p.name === 'base_principal_center'));
        for (const suffix of ['left', 'right']) {
          assert.ok(manifest.parts.some(p => p.name === 'base_principal_center_'+suffix));
          assert.ok(manifest.parts.some(p => p.name === 'base_post_center_'+suffix));
        }
        const bolts = manifest.parts.filter(p => p.fabrication.kind === 'bolt');
        const connections = new Set(bolts.map(p => p.fabrication.connection_name));
        assert.equal(connections.size, model === 'angle-base-development' ? 8 : 16);
        for (const connection of connections) {
          assert.deepEqual(bolts.filter(p => p.fabrication.connection_name === connection)
            .map(p => p.fabrication.hardware_role).sort(), ['far_washer', 'head', 'near_washer', 'nut', 'shaft']);
        }
        // Orbit to each physical end; select its exposed surface with a real click.
        for (const role of ['head', 'nut']) {
          const name = 'fastener_lumber_leg_bolt_right_1_'+role;
          await page.evaluate(({name, role}) => {
            const {meshes, camera, controls} = window.cadTest;
            const mesh = meshes.find(m => m.userData.part.name === name);
            mesh.geometry.computeBoundingBox(); mesh.updateWorldMatrix(true, false);
            const target = mesh.geometry.boundingBox.getCenter(camera.position.clone()).applyMatrix4(mesh.matrixWorld);
            target.y += 6.1; // Outside the shaft radius, inside the hex nut flats.
            camera.clearViewOffset();
            camera.position.set(target.x+(role === 'head' ? 60 : -60), target.y, target.z);
            controls.target.copy(target); controls.update(); camera.updateMatrixWorld();
          }, {name, role});
          await page.waitForTimeout(250);
          await page.mouse.click(800, 550);
          assert.ok((await page.locator('#part').innerText()).startsWith(name+':'));
          await page.screenshot({path: path.join(artifacts, model+'-bolt-'+role+'.png')});
        }
      }
      if (['infill-panel-development', 'angle-base-development'].includes(model)) {
        const infill = manifest.parts.filter(p => p.name.startsWith('fastener_infill_'));
        assert.equal(infill.length, manifest.design.infill_screw_count);
        assert.ok(infill.length > 0);
        assert.ok(infill.every(p => p.fabrication.kind === 'screw'));
        assert.ok(manifest.design.panel_kicker_screw_count > infill.length);
        assert.equal(manifest.design.maximum_infill_interval_mm, 150);
      }
      if (model === 'angle-base-development') {
        assert.ok(!manifest.parts.some(p => p.name.includes('gusset') || p.name.startsWith('fastener_timber_base_')));
        for (const side of ['left', 'right']) {
          assert.ok(manifest.parts.some(p => p.name === 'clip_angle_base_'+side));
          assert.equal(manifest.parts.filter(p => p.name.startsWith('fastener_clip_angle_base_'+side+'_')).length, 6);
        }
      }
      // Target the rear surface of the left principal at mid-height, away from rails.
      await page.evaluate(model => {
        const a = 40*Math.PI/180, x = ['split-center-development', 'infill-panel-development', 'angle-base-development'].includes(model) ? -70 : ['single-2x6-development', 'selective-2x6-development', 'paired-rail-base-development', 'vertical-principal-development'].includes(model) ? 0 : -57.15, s = 700, n = 139.7;
        const y = -18*(1+Math.cos(a))+s*Math.sin(a)-n*Math.cos(a)-950;
        const z = 225+18*Math.sin(a)+s*Math.cos(a)+n*Math.sin(a);
        const {camera, controls} = window.cadTest;
        camera.setViewOffset(1600,1100,-380,-300,1600,1100);
        camera.position.set(-x, y-800*Math.cos(a), z+800*Math.sin(a));
        controls.target.set(-x,y,z); controls.update();
      }, model);
      await page.waitForTimeout(250);
      await page.mouse.click(1180, 850);
      assert.match(await page.locator('#part').innerText(), ['split-center-development', 'infill-panel-development', 'angle-base-development'].includes(model) ? /^base_principal_center_left:/ : ['single-2x6-development', 'selective-2x6-development', 'paired-rail-base-development', 'vertical-principal-development'].includes(model) ? /^base_principal_center:/ : /^base_principal_left:/);
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
