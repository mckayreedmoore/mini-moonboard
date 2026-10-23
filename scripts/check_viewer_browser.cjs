// Serve site/ first. Arguments: installed Playwright, base URL, optional JSON receipt and baseline receipt.
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {createHash} = require('node:crypto');
const sha = value => createHash('sha256').update(value).digest('hex');
const base = new URL(process.argv[3] || 'http://127.0.0.1:8767/');
const output = process.argv[4];
const ignoreHTTPSErrors = process.env.VIEWER_BROWSER_IGNORE_HTTPS_ERRORS === '1';
const index = JSON.parse(fs.readFileSync('docs/bolted-frame-development/development-revisions.json'));
const currentGeometry = JSON.parse(fs.readFileSync(index.geometry.receipt.path));
const models = [index.geometry.viewer, 'compact-floor-flush-development',
  'compact-floor-flush-kerf-right', 'eoere-retained-2x6-frame-development', 'plywood'];

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader']});
  const report = {passed: false, revision: index.geometry.revision, models: [], pageErrors: [], consoleErrors: [], failedRequests: [], controlledFailures: [],
    playwright: require(require.resolve(`${process.argv[2] || 'playwright'}/package.json`)).version,
    chromium: browser.version(), ignoreHTTPSErrors};
  const expectedFailures = new Set();
  try {
    const page = await browser.newPage({ignoreHTTPSErrors, viewport: {width: 1024, height: 768}});
    page.on('pageerror', error => report.pageErrors.push(error.message));
    page.on('console', message => {
      if (message.type() === 'error' && !expectedFailures.has(message.location().url))
        report.consoleErrors.push(message.text());
    });
    page.on('requestfailed', request => report.failedRequests.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico'))
        (expectedFailures.has(response.url()) ? report.controlledFailures : report.failedRequests).push(response.url());
    });
    await page.route(url => url.origin === base.origin && url.pathname === base.pathname, async route => {
      const response = await route.fetch();
      const text = await response.text();
      assert.ok(text.includes('</script>\n  </body>'), 'existing browser-test seam');
      await route.fulfill({response, body: text.replace('</script>\n  </body>',
        'window.cleanupViewer={THREE,renderer,meshes,camera,controls,scene,grid,overlay,holdMeshes,holdGroup,problemMarks,person,dimensions,climberView,crashPadGroup,categoryFor,model};</script>\n  </body>')});
    });
    async function ready(model) {
      await page.waitForFunction(model => window.cleanupViewer?.model === model &&
        window.cleanupViewer.holdMeshes.length > 0 && document.querySelector('#model').value === model &&
        !document.querySelector('#show-holds').disabled, model, {timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
    }
    async function checkRendering(model) {
      assert.equal(await page.locator('canvas').isVisible(), true);
      await page.evaluate(() => {
        const v = window.cleanupViewer, renderer = v.renderer, render = renderer.render;
        const frame = renderer.info.render.frame, drawn = new Set();
        const hooks = v.meshes.map(mesh => [mesh, mesh.onAfterRender]);
        for (const [mesh, after] of hooks) mesh.onAfterRender = function (...args) {
          after.apply(this, args);
          if (this.userData.part.name !== 'McKay') drawn.add(this.userData.part.name);
        };
        // Observe a normal app frame; never render on behalf of the app.
        renderer.render = function (...args) {
          try {
            const result = render.apply(this, args), gl = this.getContext();
            const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
            gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
            v.rendering = {frames: this.info.render.frame - frame, calls: this.info.render.calls,
              triangles: this.info.render.triangles, cadParts: drawn.size,
              nonuniformPixels: pixels.some((byte, i) => i % 4 < 3 && byte !== pixels[i % 4])};
            return result;
          } finally {
            this.render = render;
            for (const [mesh, after] of hooks) mesh.onAfterRender = after;
          }
        };
      });
      await page.waitForFunction(() => window.cleanupViewer.rendering);
      const rendering = await page.evaluate(() => window.cleanupViewer.rendering);
      assert.ok(rendering.frames > 0 && rendering.calls > 0 && rendering.triangles > 0, 'app submits triangle draws');
      assert.ok(rendering.cadParts > 10, 'CAD parts participate in the draw');
      assert.equal(rendering.nonuniformPixels, true, 'canvas contains visible content');
      (report.rendering ||= []).push({model, ...rendering});
    }
    async function inspectionState() {
      return page.evaluate(() => {
        const v = window.cleanupViewer;
        return {parts: v.meshes.filter(m => m.visible).map(m => m.userData.part.name).sort(),
          accessories: ['person', 'dimensions', 'grid', 'overlay', 'holdGroup', 'crashPadGroup']
            .map(key => v[key].visible),
          camera: v.camera.position.toArray(), target: v.controls.target.toArray()};
      });
    }
    for (const model of models) {
      console.log(`Checking ${model}`);
      const url = new URL(base); url.searchParams.set('model', model); url.searchParams.set('view', 'rear');
      const requested = []; const track = request => requested.push(request.url()); page.on('request', track);
      await page.goto(url.href, {waitUntil: 'domcontentloaded'}); await ready(model); console.log(`  Loaded ${model}`);
      await checkRendering(model);
      const snapshot = await page.evaluate(() => {
        const v = window.cleanupViewer;
        return {parts: v.meshes.map(m => m.userData.part).filter(p => p.name !== 'McKay')
          .map(p => ({name: p.name, path: p.path, fabrication: p.fabrication}))
          .sort((a, b) => a.name.localeCompare(b.name)),
          holds: v.holdMeshes.map(m => ({hold: m.userData.hold, position: m.position.toArray(), rotation: m.quaternion.toArray()})),
          camera: v.camera.position.toArray(), target: v.controls.target.toArray()};
      });
      assert.ok(snapshot.parts.length > 10, 'CAD part metadata loaded');
      if (model === index.geometry.viewer) assert.equal(snapshot.parts.length, currentGeometry.counts.occupied_parts);
      console.log(`  Read metadata ${model}`);
      const beforeOrbit = await page.evaluate(() => window.cleanupViewer.camera.position.toArray());
      await page.mouse.move(780, 550); await page.mouse.down();
      await page.mouse.move(880, 610, {steps: 8}); await page.mouse.up(); await page.waitForTimeout(200);
      assert.notDeepEqual(await page.evaluate(() => window.cleanupViewer.camera.position.toArray()), beforeOrbit);
      assert.ok(await page.evaluate(() => window.cleanupViewer.meshes.some(m =>
        m.userData.part.name !== 'McKay' && window.cleanupViewer.categoryFor(m.userData.part) === 'timber')));
      await page.locator('#show-timber').uncheck();
      assert.equal(await page.locator('#show-timber').isChecked(), false);
      assert.equal(await page.evaluate(() => window.cleanupViewer.meshes
        .filter(m => m.userData.part.name !== 'McKay' && window.cleanupViewer.categoryFor(m.userData.part) === 'timber')
        .every(m => !m.visible)), true);
      await page.locator('#show-timber').check();
      assert.equal(await page.evaluate(() => window.cleanupViewer.meshes
        .filter(m => m.userData.part.name !== 'McKay' && window.cleanupViewer.categoryFor(m.userData.part) === 'timber')
        .every(m => m.visible)), true);
      await page.locator('#dimensions').uncheck(); await page.locator('#person').uncheck();
      assert.equal(await page.evaluate(() => window.cleanupViewer.dimensions.visible || window.cleanupViewer.person.visible), false);
      await page.locator('#dimensions').check(); await page.locator('#person').check();
      console.log(`  Visibility and orbit ${model}`);
      const bolts = page.locator('#bolt-view option:not([value=""])');
      const boltCount = await bolts.count();
      if (model === 'plywood') assert.equal(boltCount, 0, 'plywood has no complete bolt stacks');
      else assert.ok(boltCount > 0, `${model} has inspectable bolt stacks`);
      if (boltCount) {
        const bolt = await bolts.first().getAttribute('value');
        // Settle the earlier orbit's damping before comparing saved/restored views.
        await page.evaluate(() => {for (let i = 0; i < 1000; i++) window.cleanupViewer.controls.update();});
        const assembly = await inspectionState();
        const stack = await page.evaluate(bolt => window.cleanupViewer.meshes
          .filter(m => m.userData.part.fabrication?.connection_name === bolt)
          .map(m => m.userData.part.name).sort(), bolt);
        assert.ok(stack.length >= 5, 'complete selected bolt stack');
        await page.locator('#bolt-view').selectOption(bolt);
        await page.locator('#part').filter({hasText: /complete \d+-piece bolt stack/}).waitFor();
        assert.equal(await page.locator('#show-holds').isDisabled(), true);
        const inspecting = await inspectionState();
        assert.deepEqual(inspecting.parts, stack, 'only the selected stack remains visible');
        assert.ok(inspecting.accessories.every(visible => !visible), 'inspection hides accessories');
        assert.notDeepEqual(inspecting.camera, assembly.camera, 'inspection focuses the stack');
        await page.locator('#bolt-view').selectOption('');
        const restored = await inspectionState();
        assert.deepEqual(restored.parts, assembly.parts, 'assembly visibility restored');
        assert.deepEqual(restored.accessories, assembly.accessories, 'accessory visibility restored');
        for (const key of ['camera', 'target']) assert.ok(restored[key].every((v, i) =>
          Math.abs(v - assembly[key][i]) < 1e-8), `${key} restored within floating-point roundoff (mm)`);
        (report.boltInspectionModels ||= []).push(model);
      }
      console.log(`  Bolt inspection ${model}`);
      const padsAvailable = await page.locator('#show-crash-pads').isVisible();
      if (padsAvailable) {
        await page.locator('#show-crash-pads').uncheck();
        assert.equal(await page.evaluate(() => window.cleanupViewer.crashPadGroup.visible), false);
        await page.locator('#show-crash-pads').check();
        assert.equal(await page.evaluate(() => window.cleanupViewer.crashPadGroup.visible), true);
      }
      assert.equal(padsAvailable, ['compact-floor-flush-development', 'compact-floor-flush-kerf-right'].includes(model));
      page.off('request', track);
      if (model === index.geometry.viewer) {
        assert.ok(!requested.some(url => /owner-(wood-joints|barrel)-layout-scene\.json$/.test(url)), 'large historical scenes stay lazy');
      }
      report.models.push({model, partCount: snapshot.parts.length, partMetadataSha256: sha(JSON.stringify(snapshot.parts)),
        holdGeometrySha256: sha(JSON.stringify(snapshot.holds)), camera: snapshot.camera, target: snapshot.target,
        status: await page.locator('#model-status').innerText(), requests: requested.length});
    }
    // Select a rendered physical part and a hold through the real pointer handlers.
    async function aimAt(name, hold = false) {
      return page.evaluate(({name, hold}) => {
        const {THREE, meshes, holdMeshes, camera, controls, scene} = window.cleanupViewer;
        scene.updateMatrixWorld(true);
        const mesh = (hold ? holdMeshes : meshes).find(m => hold
          ? m.userData.hold.position === name : m.userData.part.name === name);
        const center = new THREE.Box3().setFromObject(mesh).getCenter(new THREE.Vector3());
        const normal = new THREE.Vector3(0, Math.cos(Math.PI * 40 / 180), -Math.sin(Math.PI * 40 / 180));
        controls.target.copy(center); camera.position.copy(center).addScaledVector(normal, 700);
        camera.setViewOffset(innerWidth, innerHeight, -180, -100, innerWidth, innerHeight);
        controls.update(); camera.updateMatrixWorld(true);
        const pixel = center.project(camera);
        return {x: (pixel.x + 1) * innerWidth / 2, y: (1 - pixel.y) * innerHeight / 2};
      }, {name, hold});
    }
    await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
    await page.locator('#show-holds').uncheck();
    let pixel = await aimAt('main_lower_left'); await page.mouse.click(pixel.x, pixel.y);
    assert.match(await page.locator('#part').innerText(), /^main_lower_left:/);
    await page.locator('#show-holds').check();
    pixel = await aimAt('B12', true); await page.mouse.click(pixel.x, pixel.y);
    assert.match(await page.locator('#part').innerText(), /^B12: .*approximate/);
    // Keyboard marking, reload persistence, clipboard fallback, and setup isolation.
    await page.locator('#problem-tools').evaluate(node => {node.open = true;});
    await page.locator('#problem-edit').check();
    const position = await page.locator('#problem-position option').first().getAttribute('value');
    await page.locator('#problem-position').selectOption(position); await page.locator('#problem-apply').click();
    assert.equal(new URL(page.url()).searchParams.get('problem'), `2025:${position}.s`);
    await page.reload({waitUntil: 'domcontentloaded'}); await ready('plywood');
    assert.equal(await page.evaluate(() => window.cleanupViewer.problemMarks.size), 1);
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {configurable: true,
      value: {writeText: async () => {throw new Error('denied for regression');}}}));
    await page.locator('#problem-share').click(); assert.equal(await page.locator('#problem-link').isVisible(), true);
    await page.locator('#model').selectOption('compact-floor-flush-development'); await ready('compact-floor-flush-development');
    await page.goBack({waitUntil: 'domcontentloaded'}); await ready('plywood');
    await page.goForward({waitUntil: 'domcontentloaded'}); await ready('compact-floor-flush-development');
    await page.locator('#hold-setup').selectOption('2020');
    await page.waitForURL(/setup=2020/); await ready('compact-floor-flush-development');
    assert.equal(await page.evaluate(() => window.cleanupViewer.holdMeshes.length), 130);
    assert.equal(new URL(page.url()).searchParams.has('problem'), false);
    await page.goBack({waitUntil: 'domcontentloaded'}); await ready('compact-floor-flush-development');
    await page.waitForFunction(() => document.querySelector('#hold-setup').value === '2025');
    assert.equal(await page.evaluate(() => window.cleanupViewer.holdMeshes.length), 138);
    await page.goForward({waitUntil: 'domcontentloaded'}); await ready('compact-floor-flush-development');
    await page.waitForFunction(() => document.querySelector('#hold-setup').value === '2020');
    assert.equal(await page.evaluate(() => window.cleanupViewer.holdMeshes.length), 130);
    // Both no-query and unrecognized model routes retain the selected baseline.
    await page.goto(base.href, {waitUntil: 'domcontentloaded'}); await ready('compact-floor-flush-development');
    const frontCamera = await page.evaluate(() => window.cleanupViewer.camera.position.toArray());
    // OrbitControls recomputes coordinates; tolerate only floating-point roundoff (in mm).
    assert.ok(frontCamera.every((v, i) => Math.abs(v - [4300, 4700, 1600][i]) < 1e-8));
    const unknown = new URL(base); unknown.searchParams.set('model', 'unknown-cleanup-regression');
    await page.goto(unknown.href, {waitUntil: 'domcontentloaded'}); await ready('compact-floor-flush-development');
    // An explicit unavailable-manifest control must retain its visible error.
    const missing = new URL('hybrid/compact-floor-flush-development/parts.json', base).href;
    expectedFailures.add(missing);
    await page.route(missing, route => route.fulfill({status: 404, body: 'intentional regression control'}));
    const weightsURL = new URL('prototype-weights.json', base).href;
    let releaseWeights;
    const weightsGate = new Promise(resolve => {releaseWeights = resolve;});
    await page.route(weightsURL, async route => {await weightsGate; await route.continue();});
    try {
      await page.reload({waitUntil: 'domcontentloaded'});
      await page.locator('#model-status').filter({hasText: /Model compact-floor-flush-development unavailable/}).waitFor();
      const weightsResponse = page.waitForResponse(weightsURL);
      releaseWeights(); await weightsResponse;
      await page.waitForLoadState('networkidle');
      assert.equal(await page.locator('#prototype-weight').innerText(), 'Planning mass: unavailable');
      report.lateWeightMetadataPreservesLoadError = true;
    } finally {releaseWeights();}
    assert.deepEqual(report.pageErrors, []); assert.deepEqual(report.consoleErrors, []); assert.deepEqual(report.failedRequests, []);
    assert.equal(report.controlledFailures.length, 1);
    if (process.argv[5]) {
      const baseline = JSON.parse(fs.readFileSync(process.argv[5]));
      // Completed model snapshots remain useful when a later baseline interaction failed.
      // Retain that failure flag rather than representing the baseline as a full pass.
      report.baselinePassed = baseline.passed;
      assert.deepEqual(report.models.map(({requests, ...stable}) => stable),
        baseline.models.map(({requests, ...stable}) => stable), 'model metadata, holds, cameras and scope labels remain equivalent');
      report.modelSnapshotsEquivalent = true;
    }
    report.passed = true;
    console.log(JSON.stringify({passed: true, baselinePassed: report.baselinePassed,
      modelSnapshotsEquivalent: report.modelSnapshotsEquivalent, models: report.models.map(m => [m.model, m.partCount]),
      controls: 'orbit, part/hold picking, visibility, crash pads, bolt inspection, problem links, reload, back/forward, hold setup, default/unknown routes, unavailable-export error'}));
  } finally {
    await browser.close();
    if (output) fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
