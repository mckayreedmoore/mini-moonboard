// Actual viewer loading, category controls and T-nut selection.
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const output = process.argv[4] || 'fea/generated/reinforcement-viewer';
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
    await page.goto(base+'?model=round-reinforcement-development&view=rear');
    const manifest = await page.evaluate(async () => (await fetch('hybrid/round-reinforcement-development/parts.json')).json());
    await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
      manifest.parts.length, {timeout: 120000}).catch(async error => {
      const state = await page.evaluate(() => ({instrumented: Boolean(window.cadTest),
        count: window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length,
        card: document.querySelector('#part')?.textContent}));
      throw new Error(JSON.stringify({error: error.message, state, expected: manifest.parts.length, errors}));
    });
    assert.equal(manifest.design.hold_tnut_count, 142);
    assert.equal(manifest.design.hold_bolt_count, 0);
    assert.equal(manifest.design.panel_kicker_screw_count, 66);
    const nuts = manifest.parts.filter(p => p.fabrication.kind === 'tnut');
    assert.equal(nuts.length, 142);
    assert.equal(new Set(nuts.map(p => p.name)).size, 142);
    assert.match(await page.locator('#design-details').innerText(), /NOT build-ready/);
    assert.equal(await page.locator('#model').inputValue(), 'round-reinforcement-development');
    await page.screenshot({path: path.join(output, 'assembly-rear.png')});
    await page.locator('#show-t-nuts').uncheck();
    assert.equal(await page.evaluate(() => window.cadTest.meshes.filter(m => m.userData.part.fabrication.kind === 'tnut' && m.visible).length), 0);
    await page.locator('#show-t-nuts').check();
    for (const kind of ['panels', 'timber', 'brackets', 'bolts', 'screws', 'inserts', 'lights', 'wiring']) {
      await page.locator('#show-'+kind).uncheck();
    }
    const click = await page.evaluate(() => {
      const {meshes, camera, controls, THREE} = window.cadTest;
      const mesh = meshes.find(m => m.userData.part.name === 'hold_tnut_main_F6');
      mesh.geometry.computeBoundingSphere();
      mesh.updateMatrixWorld(true);
      const center = mesh.geometry.boundingSphere.center.clone().applyMatrix4(mesh.matrixWorld);
      camera.position.copy(center.clone().add(new THREE.Vector3(45, 60, 35)));
      controls.target.copy(center); controls.update(); camera.updateMatrixWorld(true);
      const positions = mesh.geometry.attributes.position;
      const ray = new THREE.Raycaster();
      for (let i = 0; i < positions.count; i += 3) {
        const point = new THREE.Vector3();
        for (let j = 0; j < 3; j++) point.add(new THREE.Vector3().fromBufferAttribute(positions, i+j));
        point.divideScalar(3).applyMatrix4(mesh.matrixWorld).project(camera);
        ray.setFromCamera(new THREE.Vector2(point.x, point.y), camera);
        if (ray.intersectObjects(meshes.filter(m => m.visible))[0]?.object !== mesh) continue;
        const rect = document.querySelector('canvas').getBoundingClientRect();
        return {x: rect.left+(point.x+1)*rect.width/2, y: rect.top+(1-point.y)*rect.height/2};
      }
      throw new Error('No visible T-nut surface');
    });
    await page.mouse.click(click.x, click.y);
    assert.match(await page.locator('#part').innerText(), /^hold_tnut_main_F6:/);
    assert.match(await page.locator('#part').innerText(), /Escape|T-nut/);
    await page.screenshot({path: path.join(output, 'selected-t-nut.png')});
    assert.deepEqual(errors, []);
    console.log(`${manifest.parts.length} meshes; 142 selectable T-nuts; category controls and actual selection passed`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
