// Reuse the neighboring Gwen browser runner and its installed Playwright.
// No page-context evaluation or dependency installation.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('..', 'gwen');
const {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const runnerPath = path.join(gwen, 'scripts/agent/browser.ts'), runner = require(runnerPath);
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/index.html';
assert(out && !fs.existsSync(out), 'fresh ignored output directory required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    const errors = [], failed = [], results = [];
    const indexHash = hash(fs.readFileSync('site/index.html'));
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failed.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failed.push(response.url());
    });
    for (const view of ['front', 'rear']) {
      const url = new URL(base); url.searchParams.set('model', 'eoere-new-2026-adjustments');
      url.searchParams.set('view', view);
      const response = await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      assert.equal(hash(await response.body()), indexHash);
      assert.equal(await page.locator('a.support-link').filter({hasText: 'Current eoere geometry'}).getAttribute('href'), '?model=eoere-adjusted-frame-development&view=rear');
      assert.match(await page.locator('#model option[value="eoere-bolted-aligned-wire-development"]').textContent(), /^Preserved/);
      await page.locator('#model-status').filter({hasText: /120 added T-nuts and 120 lights/}).waitFor({timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), 'eoere-new-2026-adjustments');
      assert.match(await page.locator('#model option:checked').textContent(), /^New 2026 adjustments/);
      assert.equal(await page.locator('canvas').count(), 1);
      assert.equal(await page.locator('#update-2026').isChecked(), true);
      assert.match(await page.locator('#update-2026-note').textContent(), /Unofficial, provisional.*exact midpoints are assumed/);
      assert.equal(await page.locator('#bolt-view option').count(), 99);
      for (const model of ['eoere-bolted-aligned-wire-development', 'eoere-bolted-trimmed-cleats-development',
        'eoere-bolted-bottom-rail-development', 'compact-floor-flush-development'])
        assert.equal(await page.locator(`#model option[value="${model}"]`).count(), 1);
      await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
      if (view === 'rear') await page.locator('#show-panels').uncheck();
      const steps = [{action: 'screenshot', path: path.join(out, `2026-${view}.png`)}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      results.push({view, url: url.href, status: await page.locator('#model-status').textContent(),
        screenshot: {path: steps[0].path, sha256: hash(fs.readFileSync(steps[0].path))},
        index_html_sha256: hash(await response.body())});
    }
    await page.locator('#update-2026').uncheck();
    await page.locator('#model-status').filter({hasText: /Extra unofficial 2026 holes and lights are off/}).waitFor({timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    assert.equal(await page.locator('#model').inputValue(), 'eoere-adjusted-frame-development');
    assert.equal(await page.locator('#update-2026').isChecked(), false);
    await page.screenshot({path: path.join(out, 'adjusted-base-2026-off.png')});
    await page.locator('#update-2026').check();
    await page.locator('#model-status').filter({hasText: /120 added T-nuts and 120 lights/}).waitFor({timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    assert.equal(await page.locator('#model').inputValue(), 'eoere-new-2026-adjustments');
    await page.locator('#model').selectOption('eoere-bolted-aligned-wire-development');
    await page.locator('#model-status').filter({hasText: /All 132 LED endpoints/}).waitFor({timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    assert.equal(await page.locator('#model').inputValue(), 'eoere-bolted-aligned-wire-development');
    assert.deepEqual(errors, []); assert.deepEqual(failed, []);
    assert.equal(hash(fs.readFileSync('site/index.html')), indexHash);
    const result = {schema: 'eoere_2026_browser_check/v1', passed: true, results,
      preserved_option_navigation: true, update_toggle_on_off_on: true, unofficial_positions_label_verified: true, page_errors: errors, failed_requests_or_responses: failed,
      chromium_version: browser.version(), playwright_version: require(path.join(gwen, 'node_modules/playwright/package.json')).version,
      bun_version: Bun.version, shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))},
      source_sha256: Object.fromEntries(['site/index.html', 'site/eoere-2026-adjustments-overlay.mjs',
        'site/eoere-2026-adjustments-v3-scene.json.gz', 'site/eoere-adjusted-base-v3-scene.json.gz', 'scripts/check_eoere_2026_browser.cjs']
        .map(name => [name, hash(fs.readFileSync(name))])), page_context_code_evaluation: false,
      mechanics_or_physical_release: false};
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify({passed: true, out, errors, failed}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
