// Serve site/ first. Arguments: Playwright module, base URL, optional screenshot directory.
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const artifacts = process.argv[4];
const base = process.argv[3] || 'http://127.0.0.1:8781/';
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.route(url => url.origin === new URL(base).origin && url.pathname === new URL(base).pathname, async route => {
      const response = await route.fetch();
      await route.fulfill({ response, body: (await response.text()).replace('</script>\n  </body>',
        'window.problemTest={holdMeshes,holdGroup,camera,controls,scene,meshes,problemMarks};</script>\n  </body>') });
    });
    async function ready(fullAssembly = false) {
      await page.waitForFunction(() => window.problemTest?.holdMeshes.length && !document.querySelector('#show-holds').disabled, null, { timeout: 120000 });
      if (fullAssembly) {
        const count = await page.evaluate(async () => (await (await fetch('hybrid/round-bore-service-development/parts.json')).json()).parts.length);
        await page.waitForFunction(count => window.problemTest.meshes.filter(mesh => mesh.userData.part.name !== 'McKay').length === count, count, {timeout: 120000});
      }
      await page.locator('#problem-tools').evaluate(element => { element.open = true; });
    }
    async function aim(position) {
      await page.evaluate(position => {
        const { holdMeshes, camera, controls, scene } = window.problemTest;
        const mesh = holdMeshes.find(mesh => mesh.userData.hold.position === position);
        scene.updateMatrixWorld(true);
        const target = mesh.localToWorld(mesh.position.clone().set(0, 0, 0));
        const normal = mesh.position.clone().set(0, 0, 1).applyQuaternion(mesh.getWorldQuaternion(camera.quaternion.clone()));
        controls.target.copy(target); camera.position.copy(target).addScaledVector(normal, 700);
        camera.setViewOffset(1600, 1100, -400, -300, 1600, 1100); controls.update();
      }, position);
    }
    const url = new URL(base); url.searchParams.set('setup', '2020');
    await page.goto(url.href, {waitUntil: 'domcontentloaded'}); await ready(true); await aim('B12');
    await page.mouse.click(1200, 850);
    assert.match(await page.locator('#part').innerText(), /^B12:/);
    assert.equal(await page.evaluate(() => window.problemTest.problemMarks.size), 0, 'Inspection does not mark holds');
    await page.locator('#problem-edit').check();
    for (const role of ['s', 'h', 'f', 't']) {
      await page.selectOption('#problem-role', role); await page.mouse.click(1200, 850);
      await page.waitForFunction(role => window.problemTest.problemMarks.get('B12') === role, role);
      assert.equal(new URL(page.url()).searchParams.get('problem'), `2020:B12.${role}`);
      assert.equal(await page.evaluate(() => {
        const marker = window.problemTest.holdMeshes.find(mesh => mesh.userData.hold.position === 'B12').userData.problemMarker;
        return marker.visible && marker.material.depthWrite;
      }), true, 'Opaque rings write depth so later frame meshes cannot overwrite them');
    }
    await page.selectOption('#problem-role', 'erase'); await page.mouse.click(1200, 850);
    await page.waitForFunction(() => window.problemTest.problemMarks.size === 0);
    assert.equal(new URL(page.url()).searchParams.has('problem'), false);
    await page.selectOption('#problem-role', 's');
    await page.mouse.move(1200, 850); await page.mouse.down(); await page.mouse.move(1260, 850, {steps: 5}); await page.mouse.up();
    assert.equal(await page.evaluate(() => window.problemTest.problemMarks.size), 0, 'Orbit does not paint');
    await aim('B12');
    const touch = await page.context().newCDPSession(page);
    await touch.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: [{x: 1200, y: 850, id: 1}]});
    await touch.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: [{x: 1200, y: 850, id: 1}, {x: 1250, y: 850, id: 2}]});
    await touch.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: [{x: 1250, y: 850, id: 2}]});
    await touch.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: []});
    assert.equal(await page.evaluate(() => window.problemTest.problemMarks.size), 0, 'Two-finger gestures do not paint');
    await touch.detach();
    await aim('B12'); await page.mouse.click(1200, 850);
    await page.waitForFunction(() => window.problemTest.problemMarks.get('B12') === 's');
    console.log('Problem click roles, erase, orbit and two-finger gestures passed.');
    await page.reload({waitUntil: 'domcontentloaded'}); await ready();
    assert.equal(await page.evaluate(() => window.problemTest.problemMarks.get('B12')), 's');
    assert.equal(await page.locator('#problem-edit').isChecked(), false, 'Shared links start in inspect mode');
    await page.locator('#show-holds').uncheck();
    assert.equal(await page.locator('#problem-clear').isDisabled(), true);
    await page.locator('#show-holds').check();
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { value: { writeText: async () => { throw new Error('denied'); } }, configurable: true }));
    await page.locator('#problem-share').click();
    const shared = new URL(await page.locator('#problem-link').inputValue());
    assert.equal(shared.searchParams.get('problem'), '2020:B12.s'); assert.equal(shared.searchParams.get('setup'), '2020');
    assert.equal(await page.locator('#problem-link').isVisible(), true);
    await page.locator('#problem-clear').click();
    await page.locator('#problem-edit').check();
    await page.selectOption('#problem-position', 'KICK1'); await page.selectOption('#problem-role', 'f');
    await page.locator('#problem-apply').click();
    assert.equal(await page.evaluate(() => window.problemTest.problemMarks.get('KICK1')), 'f', 'Keyboard controls mark holds');
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { value: { writeText: async text => { window.copiedProblem = text; } }, configurable: true }));
    await page.locator('#problem-share').click();
    assert.equal(new URL(await page.evaluate(() => window.copiedProblem)).searchParams.get('problem'), '2020:KICK1.f');
    await page.locator('#problem-clear').click();
    assert.equal(await page.evaluate(() => window.problemTest.problemMarks.size), 0);
    console.log('Problem reload, keyboard, visibility and clipboard checks passed.');
    // URL validation exercises real catalog loading without repeatedly loading the unrelated CAD meshes.
    await page.route('**/hybrid/round-bore-service-development/parts.json', async route => {
      const response = await route.fetch(); const manifest = await response.json();
      await route.fulfill({response, json: {...manifest, parts: []}});
    });
    for (const invalid of ['2025:B12.s', '2020:A1.s', '2020:B12.s,B12.h', '2020:B12.x', '2020:<script>.s']) {
      url.searchParams.set('problem', invalid); await page.goto(url.href, {waitUntil: 'domcontentloaded'}); await ready();
      assert.equal(await page.evaluate(() => window.problemTest.problemMarks.size), 0);
      assert.match(await page.locator('#problem-status').innerText(), /ignored/);
      assert.equal(new URL(page.url()).searchParams.has('problem'), false);
    }
    await page.unroute('**/hybrid/round-bore-service-development/parts.json');
    url.searchParams.set('problem', '2020:B12.s,KICK1.f'); await page.goto(url.href, {waitUntil: 'domcontentloaded'}); await ready();
    assert.equal(await page.evaluate(() => window.problemTest.problemMarks.size), 2);
    if (artifacts) {
      await ready(true);
      fs.mkdirSync(artifacts, {recursive: true});
      for (const [name, viewport] of [['desktop', {width: 1600, height: 1100}], ['mobile', {width: 390, height: 844}]]) {
        await page.setViewportSize(viewport);
        await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
        await page.locator('#hold-front').click();
        await page.locator('#problem-tools').evaluate(tools => { tools.scrollIntoView({block: 'start'}); });
        await page.screenshot({path: path.join(artifacts, `problem-highlights-${name}.png`)});
      }
      await page.setViewportSize({width: 1600, height: 1100});
    }
    await Promise.all([page.waitForNavigation(), page.selectOption('#hold-setup', '2025')]); await ready();
    assert.equal(await page.evaluate(() => window.problemTest.problemMarks.size), 0, 'Setup switching clears previous problem');
    assert.equal(new URL(page.url()).searchParams.has('problem'), false);
    assert.deepEqual(errors, []);
    console.log('Problem highlights: inspect/edit, roles, erase, orbit, URL reload/validation, setup isolation, hidden controls and share fallback passed.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
