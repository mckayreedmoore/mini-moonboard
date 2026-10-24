// Run with Bun from the repository root.
// Arguments: installed Playwright module, site URL, fresh ignored output folder.
// DOM surface checks only: no page evaluation, script injection or measured mesh claims.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto'), {gunzipSync} = require('node:zlib');
assert(typeof Bun !== 'undefined', 'Run this check with Bun');
const {chromium} = require(process.argv[2]);
const base = new URL(process.argv[3]), out = process.argv[4];
assert(out && !fs.existsSync(out), 'fresh browser output required');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const provenanceBytes = fs.readFileSync('site/eoere-v10-candidate13-provenance.json');
assert.equal(hash(provenanceBytes), 'de8a8b3581e2bd808d866a10b8e7cf63e0815d21ca2b98d7244eaa2c931418e4');
const provenance = JSON.parse(provenanceBytes), raw = fs.readFileSync(provenance.artifacts.viewer_scene.integrated.path);
assert.equal(hash(raw), provenance.artifacts.viewer_scene.original.sha256);
const decoded = gunzipSync(raw), scene = JSON.parse(decoded);
assert.equal(hash(decoded), provenance.scene_decoded_sha256);
fs.mkdirSync(out, {recursive: true});

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  const report = {passed: false, revision: scene.revision, verification_scope: 'DOM controls, text, links and captures only',
    provenance_sha256: hash(provenanceBytes), scene_sha256: hash(raw), chromium: browser.version(),
    pageErrors: [], failedRequests: [], models: [], captures: [], local_asset_fetches: [],
    measured_mesh_bounds: false, measured_part_inventory: false, raw_mechanics_recovered: false,
    structural_acceptance: false, fabrication_released: false, climbing_released: false};
  try {
    for (const [name, expected] of [['eoere-v10-candidate13-provenance.json', hash(provenanceBytes)],
      ['eoere-v10-scene-13.json.gz', hash(raw)]]) {
      const response = await fetch(new URL(name, base));
      assert(response.ok, 'local source asset unavailable: '+name);
      assert.equal(hash(Buffer.from(await response.arrayBuffer())), expected, 'local source asset differs: '+name);
      report.local_asset_fetches.push({path: name, status: response.status, sha256: expected});
    }
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    page.on('pageerror', error => report.pageErrors.push(error.message));
    page.on('requestfailed', request => report.failedRequests.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) report.failedRequests.push(response.url());
    });
    const selections = new Map();
    for (const model of ['eoere-owner-frame-v9-development', 'eoere-owner-frame-v10-development', 'eoere-current-frame-development']) {
      const v10 = model !== 'eoere-owner-frame-v9-development', url = new URL(base);
      url.searchParams.set('model', model);url.searchParams.set('view', 'rear');url.searchParams.set('holds', 'off');
      await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      await page.locator('#bolt-view option[value="eoere_bolt_070"]').waitFor({state: 'attached', timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert(await page.locator('canvas').first().isVisible(), 'viewer canvas is not visible');
      const options = page.locator('#bolt-view option:not([value=""])'), ids = [];
      for (let i = 0; i < await options.count(); i++) ids.push(await options.nth(i).getAttribute('value'));
      assert.equal(ids.length, v10 ? 116 : 96);
      assert.equal(new Set(ids).size, ids.length, 'duplicate bolt option');
      const status = await page.locator('#model-status').textContent();
      assert.match(status, /no\b.*fabrication.*climbing release/i);
      if (v10) {
        assert.match(status, /(?:V10|Candidate\s*13|candidate\s*13)/);
        assert.match(status, /116\b/);assert.match(status, /66\b.*(?:Hillman|screws)/i);
        assert.deepEqual(new Set(ids), new Set(scene.stack_updates.map(row => row.axis_id)));
        const links = page.locator('#shop-docs-primary a, #model-documents a'), hrefs = [];
        for (let i = 0; i < await links.count(); i++) hrefs.push(await links.nth(i).getAttribute('href'));
        for (const document of provenance.documents) {
          assert(fs.existsSync(document.path), 'portable document missing: '+document.path);
          assert(hrefs.some(href => href?.endsWith('/'+document.path)), 'portable document route missing: '+document.path);
        }
        const descriptions = [];
        for (const selection of scene.stack_updates) {
          await page.locator('#bolt-view').selectOption(selection.axis_id);
          const expected = selection.axis_id+': complete '+selection.stack_roles.length+'-piece bolt stack';
          await page.locator('#part').filter({hasText: expected}).waitFor();
          descriptions.push({axis: selection.axis_id, pieces: selection.stack_roles.length});
        }
        selections.set(model, descriptions);
        await page.locator('#bolt-view').selectOption('');
        await page.locator('#part').filter({hasText: 'Full assembly restored'}).waitFor();
      } else {
        assert.match(status, /(?:V9|96-bolt|96 bolt)/);
        await page.locator('#bolt-view').selectOption('eoere_bolt_070');
        await page.locator('#part').filter({hasText: 'eoere_bolt_070: complete 6-piece bolt stack'}).waitFor();
        await page.locator('#bolt-view').selectOption('');
      }
      await page.locator('#show-panels').uncheck();await page.locator('#person').uncheck();await page.locator('#dimensions').uncheck();
      const file = path.join(out, model+'-rear.png');await page.screenshot({path: file});
      report.captures.push({path: file, sha256: hash(fs.readFileSync(file))});
      report.models.push({model, bolt_options: ids.length, complete_stack_descriptions_checked: v10 ? 116 : 1,
        status, local_document_routes_checked: v10 ? provenance.documents.length : 0});
      console.log(JSON.stringify({model, surface_check: 'passed'}));
    }
    assert.deepEqual(selections.get('eoere-current-frame-development'), selections.get('eoere-owner-frame-v10-development'),
      'current alias stack controls differ from explicit V10');
    assert.deepEqual(report.pageErrors, []);assert.deepEqual(report.failedRequests, []);
    report.remote_document_http_check = 'Deferred until publication; rendered hrefs and local source files checked';
    report.passed = true;
  } finally {
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2)+'\n');await browser.close();
  }
  console.log(JSON.stringify(report));
})().catch(error => {console.error(error);process.exitCode = 1;});
