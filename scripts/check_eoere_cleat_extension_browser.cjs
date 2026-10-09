// Use the existing Gwen browser runner; the frozen v3 check remains unchanged.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('..', 'gwen');
const {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const runnerPath = path.join(gwen, 'scripts/agent/browser.ts'), runner = require(runnerPath);
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/index.html';
assert(out && !fs.existsSync(out), 'fresh ignored output directory required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const baseModel = 'eoere-extended-cleat-frame-development', extraModel = 'eoere-extended-cleat-2026-development';

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    // Software rendering of this complete scene can delay ordinary control clicks.
    page.setDefaultTimeout(120000);
    const errors = [], failed = [], captures = [], navigation = [];
    const indexHash = hash(fs.readFileSync('site/index.html'));
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failed.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failed.push(response.url());
    });
    async function ready(model, text) {
      await page.locator('#model-status').filter({hasText: text}).waitFor({timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('canvas').count(), 1);
      assert.equal(await page.locator('#bolt-view option').count(), 99);
      navigation.push({model, status: await page.locator('#model-status').textContent()});
    }
    const url = new URL(base); url.searchParams.set('model', baseModel); url.searchParams.set('view', 'rear');
    const response = await page.goto(url.href, {waitUntil: 'domcontentloaded'});
    assert.equal(hash(await response.body()), indexHash);
    await ready(baseModel, /Maximum cleat blank 361.186 mm/);
    assert.equal(await page.locator('a.support-link').filter({hasText: 'Current eoere geometry'}).getAttribute('href'), `?model=${baseModel}&view=rear`);
    assert.equal(await page.locator('#update-2026').isChecked(), false);
    assert.match(await page.locator('#update-2026-note').textContent(), /Unofficial, provisional.*exact midpoints are assumed/);
    for (const model of ['eoere-adjusted-frame-development', 'eoere-new-2026-adjustments', 'eoere-bolted-aligned-wire-development', 'compact-floor-flush-development'])
      assert.equal(await page.locator(`#model option[value="${model}"]`).count(), 1);
    for (const [model, label] of [[baseModel, 'base'], [extraModel, 'extra']]) {
      if (model === extraModel) {
        await page.locator('#update-2026').check(); await ready(extraModel, /120 added T-nuts and 120 lights/);
        assert.equal(await page.locator('#update-2026').isChecked(), true);
      }
      const steps = [{action: 'screenshot', path: path.join(out, `extended-cleats-${label}-rear.png`)}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      captures.push({model, view: 'rear', url: page.url(), screenshot: {path: steps[0].path, sha256: hash(fs.readFileSync(steps[0].path))}, index_html_sha256: indexHash});
    }
    await page.locator('#update-2026').uncheck(); await ready(baseModel, /Maximum cleat blank 361.186 mm/);
    assert.equal(await page.locator('#update-2026').isChecked(), false);
    assert.deepEqual(errors, []); assert.deepEqual(failed, []);
    assert.equal(hash(fs.readFileSync('site/index.html')), indexHash);
    const files = ['site/index.html', 'site/eoere-cleat-extension-overlay.mjs', 'site/eoere-cleat-extension-scene.json.gz', 'scripts/check_eoere_cleat_extension_browser.cjs'];
    const result = {schema: 'eoere_extended_cleats_browser_check/v1', passed: true, captures, navigation,
      new_pair_toggle_off_on_off: true, preserved_v3_options_present: true, unofficial_label_verified: true, page_errors: errors, failed_requests_or_responses: failed,
      source_sha256: Object.fromEntries(files.map(name => [name, hash(fs.readFileSync(name))])),
      shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))},
      chromium_version: browser.version(), playwright_version: require(path.join(gwen, 'node_modules/playwright/package.json')).version, bun_version: Bun.version,
      page_context_code_evaluation: false, mechanics_or_physical_release: false};
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify({passed: true, out, errors, failed}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
