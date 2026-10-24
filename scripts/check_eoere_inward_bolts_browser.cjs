// Arguments: installed Playwright module, site URL, fresh ignored output folder.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require(process.argv[2]);
const base = new URL(process.argv[3]), out = process.argv[4];
assert(out && !fs.existsSync(out), 'fresh browser output required');
fs.mkdirSync(out, {recursive: true});
const index = JSON.parse(fs.readFileSync('docs/bolted-frame-development/development-revisions.json'));
const cumulative = index.geometry.revision === 'eoere-inward-bolts-and-angles-v8';
assert(cumulative || index.geometry.revision === 'eoere-inward-exterior-bolts-v7');
const sceneBytes = fs.readFileSync(index.geometry.scene.path);
const scene = JSON.parse(cumulative ? require('node:zlib').gunzipSync(sceneBytes) : sceneBytes);
const receipt = JSON.parse(fs.readFileSync(index.geometry.receipt.path));
const checkedGeometry = cumulative ? JSON.parse(fs.readFileSync(receipt.checked_geometry.path)) : null;
const checkedClearance = cumulative ? JSON.parse(fs.readFileSync(receipt.checked_clearance.path)) : null;
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  const report = {passed: false, revision: index.geometry.revision, models: [], captures: [],
    pageErrors: [], failedRequests: [], chromium: browser.version()};
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: process.env.VIEWER_BROWSER_IGNORE_HTTPS_ERRORS === '1',
      viewport: {width: 1440, height: 1000}});
    report.ignoreHTTPSErrors = process.env.VIEWER_BROWSER_IGNORE_HTTPS_ERRORS === '1';
    page.on('pageerror', error => report.pageErrors.push(error.message));
    page.on('requestfailed', request => report.failedRequests.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) report.failedRequests.push(response.url());
    });
    await page.route(url => url.origin === base.origin && url.pathname === base.pathname, async route => {
      const response = await route.fetch(), html = await response.text(), seam = '</script>\n  </body>';
      assert(html.includes(seam));
      await route.fulfill({response, body: html.replace(seam,
        'window.boltPoseViewer={meshes,THREE,model,renderer};'+seam)});
    });
    const snapshots = new Map();
    for (const model of cumulative ? [index.geometry.viewer] : ['eoere-owner-frame-v6-development', index.geometry.viewer]) {
      const current = model === index.geometry.viewer, url = new URL(base);
      url.searchParams.set('model', model);url.searchParams.set('view', 'rear');url.searchParams.set('holds', 'off');
      await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      await page.locator('#bolt-view option[value="eoere_bolt_070"]').waitFor({state: 'attached', timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('#bolt-view option:not([value=""])').count(), 96);
      const snapshot = await page.evaluate(async replaced => {
        const v = window.boltPoseViewer;
        return Promise.all(v.meshes.filter(m => m.userData.part.name !== 'McKay').map(async m => {
          m.geometry.computeBoundingBox();const b = m.geometry.boundingBox;
          const positions = m.geometry.attributes.position.array;
          const digest = replaced.includes(m.userData.part.name) ? Array.from(new Uint8Array(
            await crypto.subtle.digest('SHA-256', positions.buffer))).map(n => n.toString(16).padStart(2, '0')).join('') : null;
          return {name: m.userData.part.name, bounds: [b.min.x, b.max.x, b.min.y, b.max.y, b.min.z, b.max.z],
            connection: m.userData.part.fabrication.connection_name, role: m.userData.part.fabrication.hardware_role,
            nut_faces: m.userData.part.fabrication.nut_faces, position: m.position.toArray(), position_sha256: digest};
        }));
      }, cumulative ? scene.replacements.map(r => r.name) : []);
      assert.equal(snapshot.length, 1037);snapshots.set(model, new Map(snapshot.map(r => [r.name, r])));
      await page.locator('#show-panels').uncheck();await page.locator('#person').uncheck();await page.locator('#dimensions').uncheck();
      await page.locator('#model').scrollIntoViewIfNeeded();
      const capture = async name => {
        const filename = path.join(out, name+'.png');await page.screenshot({path: filename});
        report.captures.push({path: filename, sha256: hash(fs.readFileSync(filename))});
      };
      await capture(current ? cumulative ? 'current-inward-angles-rear' : 'current-inward-rear' : 'preserved-v6-outward-rear');
      if (current) {
        assert.match(await page.locator('#model-status').textContent(), /Heads outside and nuts inside on 40 side\/top stacks/);
        for (const [axis, pieces] of [['eoere_bolt_070', 8], ['eoere_bolt_001', 5], ['rail_rear_bolt_right_1', 5]]) {
          await page.locator('#bolt-view').selectOption(axis);
          await page.locator('#part').filter({hasText: axis+': complete '+pieces+'-piece bolt stack'}).waitFor();
          assert.equal(await page.evaluate(() => window.boltPoseViewer.meshes.filter(m => m.visible && m.userData.part.name !== 'McKay').length), pieces);
          await capture(axis+'-inward-stack');
        }
        await page.locator('#bolt-view').selectOption('');
        await page.locator('#part').filter({hasText: 'Full assembly restored'}).waitFor();
      }
      report.models.push({model, parts: snapshot.length, bolt_inspection_options: 96});
    }
    const after = snapshots.get(index.geometry.viewer);
    if (cumulative) {
      const registry = new Map(checkedGeometry.changed_finished_solids.map(r => [r.id, r]));
      for (const name of checkedClearance.newly_checked_part_ids) {
        const actual = after.get(name), expected = registry.get(name);
        assert(actual && expected);assert.deepEqual(actual.position, [0, 0, 0]);
        assert(actual.bounds.every((v, i) => Math.abs(v-expected.bounds_xyz_mm[i]) < .55), 'rendered CAD bounds differ: '+name);
      }
      const {meshGeometry, decodeTypedArray} = await import('../site/wood-joints-overlay.mjs');
      class Geometry {setAttribute(key, value) {(this.attributes ||= {})[key] = value;}computeVertexNormals() {}}
      class Attribute {constructor(array, itemSize) {this.array = array;this.itemSize = itemSize;}}
      const topologies = new Map(Object.entries(scene.triangle_topologies).map(([digest, row]) =>
        [digest, {...row, indices: decodeTypedArray(row.triangle_indices_base64, row.triangle_component_type, row.index_count).values}]));
      for (const row of scene.replacements) {
        const geometry = meshGeometry({BufferGeometry: Geometry, BufferAttribute: Attribute}, row.mesh, topologies);
        assert.equal(after.get(row.name).position_sha256, hash(Buffer.from(geometry.attributes.position.array.buffer)),
          'rendered drilled receiver differs from current mesh: '+row.name);
      }
      const parentScene = JSON.parse(fs.readFileSync(scene.parent_scene.path));
      for (const transform of parentScene.transforms) {
        const head = after.get(transform.axis_id+'_head'), nut = after.get(transform.axis_id+'_nut');
        const midpoint = (row, i) => (row.bounds[2*i]+row.bounds[2*i+1])/2;
        assert.equal(nut.nut_faces, 'interior');
        if (transform.exterior_face === 'top') assert(midpoint(nut, 2) < midpoint(head, 2));
        else assert(Math.abs(midpoint(nut, 0)) < Math.abs(midpoint(head, 0)));
      }
      report.reversed_stacks = 40;report.changed_parts_checked_against_CAD = checkedClearance.newly_checked_part_ids.length;
      report.drilled_receiver_meshes_matched = scene.replacements.length;report.inset_angles = 8;
    } else {
    const before = snapshots.get('eoere-owner-frame-v6-development');
    const moved = new Set();
    for (const transform of scene.transforms) {
      for (const role of transform.roles) {
        const name = transform.axis_id+'_'+role, a = before.get(name), b = after.get(name);
        assert(a && b);moved.add(name);assert.equal(b.nut_faces, 'interior');
        for (let i = 0; i < 3; i++) {
          const sign = transform.rotation_matrix_row_major[i][i], offset = transform.translation_xyz_mm[i];
          const endpoints = [a.bounds[2*i]*sign+offset, a.bounds[2*i+1]*sign+offset].sort((x, y) => x-y);
          for (let end = 0; end < 2; end++) assert(Math.abs(endpoints[end]-b.bounds[2*i+end]) < .001,
            'rendered hardware differs from checked CAD transform: '+name);
        }
      }
      const head = after.get(transform.axis_id+'_head'), nut = after.get(transform.axis_id+'_nut');
      const midpoint = (row, i) => (row.bounds[2*i]+row.bounds[2*i+1])/2;
      if (transform.exterior_face === 'top') assert(midpoint(nut, 2) < midpoint(head, 2));
      else assert(Math.abs(midpoint(nut, 0)) < Math.abs(midpoint(head, 0)));
    }
    assert.equal(moved.size, 224);
    for (const [name, row] of before) if (!moved.has(name)) assert.deepEqual(after.get(name), row, 'unrelated part moved: '+name);
    report.reversed_stacks = 40;report.checked_hardware_parts = moved.size;report.unchanged_parts = 1037-moved.size;
    }
    assert.deepEqual(report.pageErrors, []);assert.deepEqual(report.failedRequests, []);report.passed = true;
  } finally {
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2)+'\n');
    await browser.close();
  }
  console.log(JSON.stringify(report));
})().catch(error => {console.error(error);process.exitCode = 1;});
