// Real navigation and screenshots using the existing shared runner; no eval.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('..', 'gwen'), runnerPath = path.join(gwen, 'scripts/agent/browser.ts');
const {chromium} = require(path.join(gwen, 'node_modules/playwright')), runner = require(runnerPath);
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/index.html';
assert(out && !fs.existsSync(out), 'fresh ignored screenshot directory required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const models = ['eoere-kicker-clearance-frame-development', 'eoere-kicker-clearance-2026-development'];

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    const errors = [], failed = [], captures = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failed.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failed.push(response.url());
    });
    async function ready(model) {
      await page.locator('#model-status').filter({hasText: /Kicker screw clearance.*Z212/}).waitFor({timeout: 60000});
      await page.waitForLoadState('networkidle', {timeout: 60000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('canvas').count(), 1);
      assert.equal(await page.locator('#update-2026').isChecked(), model === models[1]);
      for (const side of ['left', 'right'])
        assert.equal(await page.locator(`#bolt-view option[value="cleat_post_bolt_${side}_2"]`).isDisabled(), false);
    }
    for (const [i, model] of models.entries()) {
      if (i === 0) {
        const url = new URL(base); url.searchParams.set('model', model); url.searchParams.set('view', 'rear');
        await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      } else await page.locator('#update-2026').click();
      await ready(model);
      const steps = [{action: 'screenshot', path: path.join(out, i ? 'extra-rear.png' : 'base-rear.png')}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      captures.push({model, url: page.url(), status: await page.locator('#model-status').textContent(),
        path: steps[0].path, sha256: hash(fs.readFileSync(steps[0].path))});
    }
    await page.locator('#update-2026').click(); await ready(models[0]);
    assert.equal(await page.locator('a.support-link').filter({hasText: 'Current eoere geometry'}).getAttribute('href'), `?model=${models[0]}&view=rear`);
    for (const model of ['eoere-uniform-channels-frame-development', 'eoere-extended-cleat-frame-development',
      'eoere-lower-cleat-z180-development', 'compact-floor-flush-development'])
      assert.equal(await page.locator(`#model option[value="${model}"]`).count(), 1);
    assert.deepEqual(errors, []); assert.deepEqual(failed, []);
    const files = ['site/index.html', 'site/eoere-kicker-clearance-overlay.mjs', 'site/eoere-kicker-clearance-scene.json.gz',
      'scripts/check_eoere_kicker_clearance_browser.cjs'];
    const result = {schema: 'eoere_kicker_clearance_browser_check/v1', passed: true, captures,
      both_toggle_directions: true, prior_options_retained: true, page_errors: errors, failed_requests: failed,
      source_sha256: Object.fromEntries(files.map(name => [name, hash(fs.readFileSync(name))])),
      shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))},
      chromium_version: browser.version(), playwright_version: require(path.join(gwen, 'node_modules/playwright/package.json')).version,
      bun_version: Bun.version, page_context_code_evaluation: false, mechanics_or_physical_release: false};
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify({passed: true, out, captures: captures.length}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
