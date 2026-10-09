// Use the installed Gwen browser runner; no dependency install or page evaluation.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('..', 'gwen'), {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const runnerPath = path.join(gwen, 'scripts/agent/browser.ts'), runner = require(runnerPath);
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/index.html';
assert(out && !fs.existsSync(out), 'fresh ignored output directory required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    const errors = [], failed = [], results = [], indexHash = hash(fs.readFileSync('site/index.html'));
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failed.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failed.push(response.url());
    });
    for (const view of ['front', 'rear']) {
      const url = new URL(base); url.searchParams.set('model', 'eoere-expanded-right-column-development');
      url.searchParams.set('view', view);
      const response = await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      assert.equal(hash(await response.body()), indexHash);
      await page.locator('#model-status').filter({hasText: /264 main-face/}).waitFor({timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), 'eoere-expanded-right-column-development');
      assert.equal(await page.locator('#update-2026').isChecked(), true);
      assert.match(await page.locator('#update-2026-note').textContent(), /Unofficial, provisional/);
      assert.match(await page.locator('#model-status').textContent(), /10 kicker/);
      assert.equal(await page.locator('canvas').count(), 1);
      for (const model of ['eoere-kicker-clearance-2026-development', 'eoere-kicker-clearance-frame-development',
        'eoere-bolted-aligned-wire-development', 'compact-floor-flush-development'])
        assert.equal(await page.locator(`#model option[value="${model}"]`).count(), 1);
      await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
      if (view === 'rear') await page.locator('#show-panels').uncheck();
      const steps = [{action: 'screenshot', path: path.join(out, `right-column-${view}.png`)}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      results.push({view, url: url.href, status: await page.locator('#model-status').textContent(),
        screenshot: {path: steps[0].path, sha256: hash(fs.readFileSync(steps[0].path))}});
    }
    await page.locator('#update-2026').uncheck();
    await page.locator('#model-status').filter({hasText: /Extra grid off/}).waitFor({timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    assert.equal(await page.locator('#model').inputValue(), 'eoere-kicker-clearance-frame-development');
    assert.equal(await page.locator('#update-2026').isChecked(), false);
    await page.locator('#update-2026').check();
    await page.locator('#model-status').filter({hasText: /264 main-face/}).waitFor({timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    assert.equal(await page.locator('#model').inputValue(), 'eoere-expanded-right-column-development');
    await page.locator('#model').selectOption('eoere-kicker-clearance-2026-development');
    await page.locator('#model-status').filter({hasText: /120 added T-nuts and 120 lights/}).waitFor({timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    assert.equal(await page.locator('#model').inputValue(), 'eoere-kicker-clearance-2026-development');
    assert.equal(await page.locator('#update-2026').isChecked(), true);
    assert.deepEqual(errors, []); assert.deepEqual(failed, []);
    assert.equal(hash(fs.readFileSync('site/index.html')), indexHash);
    const result = {schema: 'eoere_right_column_browser_check/v1', passed: true, results,
      preserved_252_option_navigation: true, toggle_on_off_on: true, page_errors: errors, failed_requests_or_responses: failed,
      chromium_version: browser.version(), playwright_version: require(path.join(gwen, 'node_modules/playwright/package.json')).version,
      bun_version: Bun.version, shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))},
      source_sha256: Object.fromEntries(['site/index.html', 'site/eoere-right-column-overlay.mjs',
        'site/eoere-right-column-scene.json.gz', 'scripts/check_eoere_right_column_browser.cjs']
        .map(name => [name, hash(fs.readFileSync(name))])), page_context_code_evaluation: false, mechanics_or_physical_release: false};
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify({passed: true, out, errors, failed}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
