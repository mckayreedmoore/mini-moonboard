// Arguments: installed Playwright module, site URL, fresh ignored output folder.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require(process.argv[2]);
const base = new URL(process.argv[3]), out = process.argv[4];
assert(out && !fs.existsSync(out), 'fresh browser output required');fs.mkdirSync(out, {recursive: true});
const index = JSON.parse(fs.readFileSync('docs/bolted-frame-development/development-revisions.json'));
assert.equal(index.geometry.revision, 'eoere-single-spacer-cleat-stacks-v9');
const receipt = JSON.parse(fs.readFileSync(index.geometry.receipt.path));
const data = JSON.parse(fs.readFileSync(index.geometry.scene.path));
const geometry = JSON.parse(fs.readFileSync(receipt.checked_geometry.path));
const registry = new Map(geometry.changed_finished_solids.map(r => [r.id, r]));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  const report = {passed: false, revision: index.geometry.revision, models: [], captures: [],
    pageErrors: [], failedRequests: [], chromium: browser.version(),
    ignoreHTTPSErrors: process.env.VIEWER_BROWSER_IGNORE_HTTPS_ERRORS === '1'};
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: report.ignoreHTTPSErrors, viewport: {width: 1440, height: 1000}});
    page.on('pageerror', error => report.pageErrors.push(error.message));
    page.on('requestfailed', request => report.failedRequests.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) report.failedRequests.push(response.url());
    });
    await page.route(url => url.origin === base.origin && url.pathname === base.pathname, async route => {
      const response = await route.fetch(), html = await response.text(), seam = '</script>\n  </body>';
      assert(html.includes(seam));
      await route.fulfill({response, body: html.replace(seam, 'window.singleSpacerViewer={meshes,THREE,model};'+seam)});
    });
    const models = new Map();
    for (const model of ['eoere-owner-frame-v8-development', index.geometry.viewer]) {
      const current = model === index.geometry.viewer, url = new URL(base);
      url.searchParams.set('model', model);url.searchParams.set('view', 'rear');url.searchParams.set('holds', 'off');
      await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      await page.locator('#bolt-view option[value="eoere_bolt_070"]').waitFor({state: 'attached', timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('#bolt-view option:not([value=""])').count(), 96);
      const rows = await page.evaluate(() => window.singleSpacerViewer.meshes
        .filter(m => m.userData.part.name !== 'McKay').map(m => {
          m.geometry.computeBoundingBox();const b = m.geometry.boundingBox, f = m.userData.part.fabrication;
          return {name: m.userData.part.name, bounds: [b.min.x, b.max.x, b.min.y, b.max.y, b.min.z, b.max.z],
            position: m.position.toArray(), connection: f.connection_name, role: f.hardware_role,
            nut_faces: f.nut_faces, selected_product: f.selected_product, selected_spacer_SKU: f.selected_spacer_SKU};
        }));
      assert.equal(rows.length, current ? 1021 : 1037);
      const bank = new Map(rows.map(r => [r.name, r]));models.set(model, bank);
      await page.locator('#show-panels').uncheck();await page.locator('#person').uncheck();await page.locator('#dimensions').uncheck();
      await page.locator('#model').scrollIntoViewIfNeeded();
      const capture = async name => {
        const filename = path.join(out, name+'.png');await page.screenshot({path: filename});
        report.captures.push({path: filename, sha256: hash(fs.readFileSync(filename))});
      };
      await capture(current ? 'current-single-spacer-rear' : 'preserved-v8-three-spacers');
      if (current) {
        assert.match(await page.locator('#model-status').textContent(), /one 1-inch factory spacer each; 16 spacers total/);
        assert.equal(rows.filter(r => r.role?.startsWith('spacer')).length, 16);
        for (const selection of data.stack_updates) {
          const pieces = rows.filter(r => r.connection === selection.axis_id);
          assert.equal(pieces.length, 6);assert.equal(pieces.filter(r => r.role.startsWith('spacer')).length, 1);
          assert(pieces.every(r => r.selected_product === '8095' && r.selected_spacer_SKU === '13733'));
          assert(Math.abs(bank.get(selection.axis_id+'_shaft').bounds[1]-bank.get(selection.axis_id+'_shaft').bounds[0]-190.5) < .2);
          assert(Math.abs(bank.get(selection.axis_id+'_spacer').bounds[1]-bank.get(selection.axis_id+'_spacer').bounds[0]-25.4) < .2);
        }
        for (const axis of ['eoere_bolt_070', 'cleat_post_bolt_left_1', 'eoere_bolt_081']) {
          await page.locator('#bolt-view').selectOption(axis);
          await page.locator('#part').filter({hasText: axis+': complete 6-piece bolt stack'}).waitFor();
          assert.equal(await page.evaluate(() => window.singleSpacerViewer.meshes.filter(m => m.visible && m.userData.part.name !== 'McKay').length), 6);
          await capture(axis+'-complete-stack');
        }
        await page.locator('#bolt-view').selectOption('');
        await page.locator('#part').filter({hasText: 'Full assembly restored'}).waitFor();
      }
      report.models.push({model, parts: rows.length, bolt_inspection_options: 96});
    }
    const before = models.get('eoere-owner-frame-v8-development'), after = models.get(index.geometry.viewer);
    const changes = new Set(data.part_transforms.map(r => r.name)), removed = new Set(data.removals);
    for (const row of data.part_transforms) {
      const a = before.get(row.name), b = after.get(row.name), exact = registry.get(row.name);
      assert(a && b && exact);assert.deepEqual(b.position, [0, 0, 0]);
      for (let i = 0; i < 6; i++) {
        const axis = Math.floor(i/2), expected = a.bounds[i]*row.scale_xyz[axis]+row.translation_xyz_mm[axis];
        assert(Math.abs(expected-b.bounds[i]) < .002, 'rendered affine transform differs: '+row.name);
        assert(Math.abs(exact.bounds_xyz_mm[i]-b.bounds[i]) < .55, 'rendered CAD bounds differ: '+row.name);
      }
    }
    for (const [name, row] of before) {
      if (removed.has(name)) assert(!after.has(name), 'redundant spacer still visible');
      else if (!changes.has(name)) {
        assert.deepEqual(after.get(name).bounds, row.bounds, 'unrelated geometry moved: '+name);
        assert.deepEqual(after.get(name).position, row.position);
      }
    }
    let prior = index;
    while (prior.geometry.revision !== 'eoere-inward-exterior-bolts-v7') prior = prior.preceding_revision;
    const inward = JSON.parse(fs.readFileSync(prior.geometry.scene.path));
    const mid = (row, i) => (row.bounds[2*i]+row.bounds[2*i+1])/2;
    for (const row of inward.transforms) {
      const head = after.get(row.axis_id+'_head'), nut = after.get(row.axis_id+'_nut');
      assert.equal(nut.nut_faces, 'interior');
      if (row.exterior_face === 'top') assert(mid(nut, 2) < mid(head, 2));
      else assert(Math.abs(mid(nut, 0)) < Math.abs(mid(head, 0)));
    }
    report.changed_parts = changes.size;report.removed_spacers = removed.size;report.unchanged_geometries = 997;
    report.inward_stacks = 40;report.spacer_pieces = 16;
    assert.deepEqual(report.pageErrors, []);assert.deepEqual(report.failedRequests, []);report.passed = true;
  } finally {
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2)+'\n');await browser.close();
  }
  console.log(JSON.stringify(report));
})().catch(error => {console.error(error);process.exitCode = 1;});
