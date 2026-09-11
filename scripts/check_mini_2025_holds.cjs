// Serve site/ first. Arguments: Playwright module, base URL, optional screenshot directory.
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8781/';
const artifacts = process.argv[4];
const model = 'horizontal-service-development';
const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, '../site/mini-2025-holds.json')));
const positions = new Set(catalog.holds.map(hold => hold.position));
assert.equal(catalog.holds.length, 138);
assert.equal(positions.size, 138);
assert.equal(catalog.holds.find(hold => hold.position === 'E3').family, 'wood');
assert.equal(catalog.holds.find(hold => hold.position === 'F3').family, 'original');
assert.deepEqual(catalog.holds.reduce((counts, hold) => {
  counts[hold.family] = (counts[hold.family] || 0) + 1; return counts;
}, {}), { original: 50, 'school-f': 40, wood: 48 });
const missing = [...'ABCDEFGHIJK'].flatMap(column => Array.from({ length: 12 }, (_, i) => column + (i + 1)))
  .filter(position => !positions.has(position));
assert.deepEqual(missing, ['C1', 'D1', 'H1', 'I1']);
assert.equal(catalog.holds.filter(hold => /^KICK(?:[1-9]|10)$/.test(hold.position)).length, 10);
assert.ok(catalog.holds.every(hold => [hold.width, hold.height, hold.depth].every(value => Number.isFinite(value) && value > 0 && value < 400)
  && Number.isFinite(hold.rotation) && ['edge', 'pinch', 'sloper', 'jug', 'wedge'].includes(hold.shape)));

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route(url => url.origin === new URL(base).origin && url.pathname === new URL(base).pathname, async route => {
      const response = await route.fetch();
      const html = await response.text();
      assert.ok(html.includes('</script>\n  </body>'), 'Viewer test injection point missing');
      await route.fulfill({ response, body: html.replace('</script>\n  </body>',
        'window.holdsTest = {holdMeshes,holdGroup,meshes,camera,controls,get rowStations(){return rowStations;},scene};</script>\n  </body>') });
    });
    const url = new URL(base); url.searchParams.set('model', model);
    await page.goto(url.href, { waitUntil: 'domcontentloaded' });
    const manifest = await page.evaluate(async model => (await fetch(`hybrid/${model}/parts.json`)).json(), model);
    async function ready() {
      await page.waitForFunction(count => window.holdsTest?.meshes.filter(mesh => mesh.userData.part.name !== 'McKay').length === count,
        manifest.parts.length, { timeout: 120000 });
      await page.waitForFunction(() => window.holdsTest?.holdMeshes.length === 138);
    }
    await ready();
    assert.match(await page.locator('#hold-status').innerText(), /138 loose approximations/);
    const transforms = await page.evaluate(() => {
      const { holdMeshes, rowStations } = window.holdsTest;
      const a = 40 * Math.PI / 180;
      return holdMeshes.map(mesh => {
        const hold = mesh.userData.hold, kicker = hold.position.startsWith('KICK');
        const station = kicker ? 0 : rowStations[Number(hold.position.slice(1)) - 1];
        const expected = kicker ? [1219.2 - (100 + 248.56 * (Number(hold.position.slice(4)) - 1)), -17.5, 150]
          : [1019.2 - (hold.position.charCodeAt(0) - 65) * 200, -18 + station * Math.sin(a) + 0.5 * Math.cos(a), 225 + station * Math.cos(a) - 0.5 * Math.sin(a)];
        const normal = mesh.position.clone().set(0, 0, 1).applyQuaternion(mesh.quaternion);
        mesh.geometry.computeBoundingBox();
        return { position: hold.position, error: Math.max(...expected.map((value, i) => Math.abs(value - mesh.position.getComponent(i)))),
          normal: normal.toArray(), expectedNormal: kicker ? [0, 1, 0] : [0, Math.cos(a), -Math.sin(a)],
          back: mesh.geometry.boundingBox.min.z, depth: mesh.geometry.boundingBox.max.z, expectedDepth: hold.depth,
          finiteNormals: [...mesh.geometry.attributes.normal.array].every(Number.isFinite) };
      });
    });
    for (const row of transforms) {
      assert.ok(row.error < 1e-6, `${row.position} mounting position`);
      row.normal.forEach((value, i) => assert.ok(Math.abs(value - row.expectedNormal[i]) < 1e-6, `${row.position} front normal`));
      assert.equal(row.back, 0); assert.ok(Math.abs(row.depth - row.expectedDepth) < 1e-4);
      assert.ok(row.finiteNormals);
    }
    await page.locator('#hold-front').click();
    assert.ok(await page.evaluate(() => {
      const { camera, controls } = window.holdsTest;
      const direction = camera.position.clone().sub(controls.target).normalize(), a = 40 * Math.PI / 180;
      return Math.abs(direction.x) < 1e-6 && Math.abs(direction.y - Math.cos(a)) < 1e-6 && Math.abs(direction.z + Math.sin(a)) < 1e-6;
    }));
    if (artifacts) { fs.mkdirSync(artifacts, { recursive: true }); await page.screenshot({ path: path.join(artifacts, 'mini-2025-holds-front.png') }); }
    await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
    await page.evaluate(() => {
      const { holdMeshes, camera, controls, scene } = window.holdsTest;
      const mesh = holdMeshes.find(mesh => mesh.userData.hold.position === 'J8');
      scene.updateMatrixWorld(true);
      const target = mesh.localToWorld(mesh.position.clone().set(0, 0, 0));
      const normal = mesh.position.clone().set(0, 0, 1).applyQuaternion(mesh.getWorldQuaternion(camera.quaternion.clone()));
      controls.target.copy(target); camera.position.copy(target).addScaledVector(normal, 700);
      camera.setViewOffset(1600, 1100, -400, -300, 1600, 1100); controls.update();
    });
    await page.mouse.click(1200, 850);
    assert.match(await page.locator('#part').innerText(), /^J8: .*approximate/);
    assert.match(await page.locator('#part').innerText(), /excluded from frame weight and engineering checks/);
    if (artifacts) await page.screenshot({ path: path.join(artifacts, 'mini-2025-hold-selected.png') });
    await page.locator('#show-holds').uncheck();
    assert.equal(await page.evaluate(() => window.holdsTest.holdGroup.visible), false);
    assert.equal(new URL(page.url()).searchParams.get('holds'), 'off');
    await page.mouse.click(1200, 850);
    assert.doesNotMatch(await page.locator('#part').innerText(), /^J8: .*approximate/);
    const bolt = await page.locator('#bolt-view option:not([value=""]):not([disabled])').first().getAttribute('value');
    assert.ok(bolt, 'Actual frame bolt inspector must be available');
    for (const shown of [false, true]) {
      await page.locator('#show-holds').setChecked(shown);
      await page.selectOption('#bolt-view', bolt);
      assert.equal(await page.evaluate(() => window.holdsTest.holdGroup.visible), false);
      assert.equal(await page.locator('#show-holds').isDisabled(), true);
      assert.equal(await page.locator('#hold-front').isDisabled(), true);
      await page.selectOption('#bolt-view', '');
      assert.equal(await page.evaluate(() => window.holdsTest.holdGroup.visible), shown);
      assert.equal(await page.locator('#show-holds').isChecked(), shown);
    }
    await page.locator('#show-holds').uncheck();
    // Re-selecting the real model exercises the same URL-preserving navigation handler.
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
      page.locator('#model').evaluate(select => select.dispatchEvent(new Event('change'))),
    ]);
    await ready();
    assert.equal(new URL(page.url()).searchParams.get('holds'), 'off');
    assert.equal(await page.locator('#show-holds').isChecked(), false);
    assert.equal(await page.evaluate(() => window.holdsTest.holdGroup.visible), false);

    for (const failure of ['missing', 'invalid']) {
      await page.route('**/mini-2025-holds.json', route => failure === 'missing'
        ? route.fulfill({ status: 404, body: 'missing' })
        : route.fulfill({ contentType: 'application/json', body: JSON.stringify({ holds: catalog.holds.map((hold, i) => i === 137 ? { ...hold, width: 0 } : hold) }) }));
      await page.goto(url.href, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => document.querySelector('#hold-status')?.textContent.startsWith('Holds unavailable:'));
      await page.waitForFunction(count => window.holdsTest?.meshes.filter(mesh => mesh.userData.part.name !== 'McKay').length === count,
        manifest.parts.length, { timeout: 120000 });
      assert.equal(await page.evaluate(() => window.holdsTest.holdMeshes.length + window.holdsTest.holdGroup.children.length), 0);
      assert.equal(await page.locator('#show-holds').isDisabled(), true);
      assert.equal(await page.locator('#hold-front').isDisabled(), true);
      await page.locator('#show-panels').uncheck();
      assert.ok(await page.evaluate(() => window.holdsTest.meshes.some(mesh => !mesh.visible && mesh.userData.part.name !== 'McKay')));
      await page.locator('#show-panels').check();
      await page.selectOption('#bolt-view', bolt);
      assert.ok(await page.evaluate(() => window.holdsTest.meshes.some(mesh => mesh.visible)));
      await page.selectOption('#bolt-view', '');
      await page.unroute('**/mini-2025-holds.json');
    }
    assert.deepEqual(errors, []);
    console.log('Mini 2025 holds: catalog, placement, selection, visibility, bolt inspector, URL persistence and failure isolation passed.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
