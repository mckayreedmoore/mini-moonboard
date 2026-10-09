// Reuse Gwen's Bun/Playwright runner and selectors; no page-context evaluation.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('..', 'gwen');
const {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const runnerPath = path.join(gwen, 'scripts/agent/browser.ts'), runner = require(runnerPath);
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/index.html';
assert(out && !fs.existsSync(out), 'fresh ignored output directory required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const models = {base: 'eoere-uniform-channels-frame-development', extra: 'eoere-uniform-channels-2026-development'};
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}}); page.setDefaultTimeout(120000);
    const indexHash = hash(fs.readFileSync('site/index.html')), errors = [], failed = [], captures = [], navigation = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failed.push(request.url()));
    page.on('response', response => {if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failed.push(response.url());});
    async function ready(model) {
      await page.locator('#model-status').filter({hasText: /Smaller cable channels/}).waitFor();
      await page.waitForLoadState('networkidle');
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('canvas').count(), 1);
      assert.equal(await page.locator('#bolt-view option').count(), 99);
      assert.equal(await page.locator('#update-2026').isChecked(), model === models.extra);
      assert.match(await page.locator('#update-2026-note').textContent(), /Unofficial, provisional.*exact midpoints are assumed/);
      navigation.push({model, url: page.url(), status: await page.locator('#model-status').textContent()});
    }
    async function capture(label) {
      const steps = [{action: 'screenshot', path: path.join(out, label + '.png')}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      captures.push({label, url: page.url(), path: steps[0].path, sha256: hash(fs.readFileSync(steps[0].path))});
    }
    const url = new URL(base); url.searchParams.set('model', models.base); url.searchParams.set('view', 'rear');
    const response = await page.goto(url.href, {waitUntil: 'domcontentloaded'});
    assert.equal(hash(await response.body()), indexHash); await ready(models.base); await capture('base-rear');
    assert.equal(await page.locator('a.support-link').filter({hasText: 'Current eoere geometry'}).getAttribute('href'), `?model=${models.base}&view=rear`);
    for (const model of ['eoere-extended-cleat-frame-development', 'eoere-extended-cleat-2026-development',
      'eoere-lower-cleat-z180-development', 'eoere-adjusted-frame-development', 'compact-floor-flush-development'])
      assert.equal(await page.locator(`#model option[value="${model}"]`).count(), 1);
    await page.locator('#update-2026').check(); await ready(models.extra); await capture('extra-rear');
    await page.locator('#update-2026').uncheck(); await ready(models.base);
    await page.locator('#update-2026').check(); await ready(models.extra);
    const front = new URL(base); front.searchParams.set('model', models.extra);
    await page.goto(front.href, {waitUntil: 'domcontentloaded'}); await ready(models.extra); await capture('extra-front');
    assert.deepEqual(errors, []); assert.deepEqual(failed, []); assert.equal(hash(fs.readFileSync('site/index.html')), indexHash);
    const files = ['site/index.html', 'site/eoere-uniform-channels-overlay.mjs', 'site/eoere-uniform-channels-scene.json.gz',
      'scripts/check_eoere_uniform_channels_browser.cjs'];
    const result = {schema: 'eoere_uniform_channels_browser_check/v1', passed: true, navigation, captures,
      off_on_off_on_cycle: true, preserved_model_choices_present: true, page_errors: errors, failed_requests_or_responses: failed,
      source_sha256: Object.fromEntries(files.map(name => [name, hash(fs.readFileSync(name))])),
      shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))},
      chromium_version: browser.version(), playwright_version: require(path.join(gwen, 'node_modules/playwright/package.json')).version,
      bun_version: Bun.version, page_context_code_evaluation: false, mechanics_or_physical_release: false};
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify({passed: true, out}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
