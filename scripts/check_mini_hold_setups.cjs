// Serve site/ first. Arguments: Playwright module, base URL, optional screenshot directory.
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8781/';
const artifacts = process.argv[4];
const model = 'round-bore-service-development';
const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, '../site/mini-2020-holds.json')));
const positions = new Set(catalog.holds.map(hold => hold.position));
assert.equal(catalog.holds.length, 130);
assert.equal(positions.size, 130);
assert.equal(catalog.holds.filter(hold => /^KICK(?:[1-9]|10)$/.test(hold.position)).length, 10);
assert.equal(catalog.holds.filter(hold => /^[A-K](?:[1-9]|1[0-2])$/.test(hold.position)).length, 120);
assert.deepEqual(catalog.holds.reduce((counts, hold) => {
  counts[hold.family] = (counts[hold.family] || 0) + 1; return counts;
}, {}), { original: 50, wood: 80 });
assert.deepEqual([...'ABCDEFGHIJK'].flatMap(column => Array.from({ length: 12 }, (_, i) => column + (i + 1)))
  .filter(position => !positions.has(position)), ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'G2', 'H1', 'I1', 'J1', 'K1']);
const yellowRows = { 12: 'AGJK', 11: 'F', 10: 'ACGI', 9: 'BEK', 8: 'CDGI', 7: 'AJ', 6: 'CEH', 5: 'BI', 4: 'DGJ', 3: 'ABGIJ', 2: 'ACDEFHIJK' };
for (const [row, columns] of Object.entries(yellowRows)) {
  assert.equal(catalog.holds.filter(hold => hold.family === 'original' && hold.position.slice(1) === row)
    .map(hold => hold.position[0]).sort().join(''), columns, `Official image yellow mask, row ${row}`);
}
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
        'window.holdsTest = {holdMeshes,holdGroup,meshes,camera,controls,scene};</script>\n  </body>') });
    });
    const url = new URL(base); url.searchParams.set('model', model); url.searchParams.set('setup', '2020');
    await page.goto(url.href, { waitUntil: 'domcontentloaded' });
    const manifest = await page.evaluate(async model => (await fetch(`hybrid/${model}/parts.json`)).json(), model);
    async function ready(setup) {
      await page.waitForFunction(count => window.holdsTest?.meshes.filter(mesh => mesh.userData.part.name !== 'McKay').length === count,
        manifest.parts.length, { timeout: 120000 });
      const count = setup === '2020' ? 130 : 138;
      await page.waitForFunction(count => window.holdsTest?.holdMeshes.length === count, count);
      assert.equal(await page.locator('#hold-setup').inputValue(), setup);
      assert.match(await page.locator('#hold-status').innerText(), new RegExp(`${count} loose approximations`));
      assert.equal(await page.evaluate(() => window.holdsTest.holdGroup.children.length), count, 'No leaked hold meshes');
      assert.equal(new URL(page.url()).searchParams.get('model'), model);
    }
    async function switchSetup(setup) {
      await Promise.all([page.waitForNavigation({ waitUntil: 'domcontentloaded' }), page.selectOption('#hold-setup', setup)]);
      await ready(setup);
    }
    async function screenshot(name) {
      if (!artifacts) return;
      fs.mkdirSync(artifacts, { recursive: true });
      await page.locator('header').evaluate(header => { header.scrollTop = 0; });
      await page.screenshot({ path: path.join(artifacts, name) });
    }
    await ready('2020');
    await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
    await page.locator('#hold-front').click();
    await screenshot('mini-2020-holds-front.png');
    await page.evaluate(() => {
      const { holdMeshes, camera, controls, scene } = window.holdsTest;
      const mesh = holdMeshes.find(mesh => mesh.userData.hold.position === 'B12');
      scene.updateMatrixWorld(true);
      const target = mesh.localToWorld(mesh.position.clone().set(0, 0, 0));
      const normal = mesh.position.clone().set(0, 0, 1).applyQuaternion(mesh.getWorldQuaternion(camera.quaternion.clone()));
      controls.target.copy(target); camera.position.copy(target).addScaledVector(normal, 700);
      camera.setViewOffset(1600, 1100, -400, -300, 1600, 1100); controls.update();
    });
    await page.mouse.click(1200, 850);
    assert.match(await page.locator('#part').innerText(), /^B12: .*Wood A\/B\/C.*approximate/);
    await page.locator('#show-holds').uncheck();
    for (const setup of ['2025', '2020']) {
      await switchSetup(setup);
      assert.equal(new URL(page.url()).searchParams.get('holds'), 'off');
      assert.equal(await page.locator('#show-holds').isChecked(), false);
      assert.equal(await page.evaluate(() => window.holdsTest.holdGroup.visible), false);
    }
    await page.locator('#show-holds').check();
    await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.locator('#hold-front').click();
    const bounds = await page.evaluate(() => {
      const { holdMeshes, scene, camera } = window.holdsTest;
      scene.updateMatrixWorld(true); camera.updateMatrixWorld(true);
      const points = holdMeshes.flatMap(mesh => {
        const vertices = mesh.geometry.attributes.position;
        return Array.from({ length: vertices.count }, (_, i) => {
          const point = mesh.position.clone().fromBufferAttribute(vertices, i).applyMatrix4(mesh.matrixWorld).project(camera);
          return [(point.x + 1) * innerWidth / 2, (1 - point.y) * innerHeight / 2];
        });
      });
      return { left: Math.min(...points.map(point => point[0])), right: Math.max(...points.map(point => point[0])),
        top: Math.min(...points.map(point => point[1])), bottom: Math.max(...points.map(point => point[1])),
        headerBottom: document.querySelector('header').getBoundingClientRect().bottom };
    });
    assert.ok(bounds.left >= 0 && bounds.right <= 768 && bounds.top >= bounds.headerBottom && bounds.bottom <= 1024,
      `Narrow front view must fit below controls: ${JSON.stringify(bounds)}`);
    await screenshot('mini-2020-holds-narrow.png');
    await page.setViewportSize({ width: 1600, height: 1100 });
    const defaultUrl = new URL(url); defaultUrl.searchParams.delete('setup');
    await page.goto(defaultUrl.href, { waitUntil: 'domcontentloaded' }); await ready('2025');
    await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
    await page.locator('#hold-front').click(); await screenshot('mini-2025-holds-front.png');
    for (const failure of ['missing', 'invalid']) {
      await page.route('**/mini-2020-holds.json', route => failure === 'missing'
        ? route.fulfill({ status: 404, body: 'missing' })
        : route.fulfill({ contentType: 'application/json', body: JSON.stringify({ holds: catalog.holds.map((hold, i) => i === 129 ? { ...hold, width: 0 } : hold) }) }));
      await page.goto(url.href, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => document.querySelector('#hold-status')?.textContent.startsWith('Holds unavailable:'));
      assert.equal(await page.evaluate(() => window.holdsTest.holdMeshes.length + window.holdsTest.holdGroup.children.length), 0);
      assert.equal(await page.locator('#show-holds').isDisabled(), true);
      assert.equal(await page.locator('#hold-setup').isDisabled(), false);
      await switchSetup('2025');
      assert.equal(await page.locator('#show-holds').isEnabled(), true);
      await page.unroute('**/mini-2020-holds.json');
    }
    assert.deepEqual(errors, []);
    console.log('Mini setups: official 2020 family layout, selection, switching, URL persistence, default 2025, narrow framing and failure recovery passed.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
