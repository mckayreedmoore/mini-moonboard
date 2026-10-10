// Exercise the current hardware variants with the shared Gwen screenshot runner.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('..', 'gwen'), runnerPath = path.join(gwen, 'scripts/agent/browser.ts');
const runner = require(runnerPath), {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/index.html';
assert(out && !fs.existsSync(out), 'fresh ignored browser output directory required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const models = ['eoere-selected-hardware-frame-development', 'eoere-selected-hardware-grid-development'];
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    const errors = [], failures = [], captures = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failures.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failures.push(response.url());
    });
    const indexHash = hash(fs.readFileSync('site/index.html'));
    const url = new URL(base); url.searchParams.set('model', models[0]); url.searchParams.set('view', 'rear');
    const response = await page.goto(url.href, {waitUntil: 'domcontentloaded'});
    assert.equal(hash(await response.body()), indexHash);
    for (const [i, model] of models.entries()) {
      if (i) await page.locator('#update-2026').check();
      await page.locator('#model-status').filter({hasText: /Selected hardware.*eight factory spacers/}).waitFor({timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('#update-2026').isChecked(), Boolean(i));
      assert.match(await page.locator('#model-status').textContent(), i ? /264 main positions/ : /Extra grid off/);
      assert.equal(await page.locator('canvas').count(), 1);
      for (const bolt of ['cleat_post_bolt_left_1', 'cleat_post_bolt_right_2', 'eoere_bolt_065'])
        assert.equal(await page.locator('#bolt-view option[value="' + bolt + '"]').isDisabled(), false);
      await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
      await page.locator('#show-panels').uncheck();
      const screenshot = path.join(out, i ? 'selected-grid-rear.png' : 'selected-base-rear.png');
      const steps = [{action: 'screenshot', path: screenshot}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      captures.push({model, url: page.url(), path: screenshot, sha256: hash(fs.readFileSync(screenshot))});
    }
    await page.locator('#update-2026').uncheck();
    await page.locator('#model-status').filter({hasText: /Selected hardware.*Extra grid off/}).waitFor({timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    assert.equal(await page.locator('#model').inputValue(), models[0]);
    assert.equal(await page.locator('a.support-link').filter({hasText: 'Current eoere geometry'}).getAttribute('href'),
      '?model=' + models[0] + '&view=rear');
    for (const [connection, filename] of [['eoere_bolt_065', 'selected-header-stack.png'],
      ['cleat_post_bolt_left_1', 'selected-post-stack.png']]) {
      await page.locator('#bolt-view').selectOption(connection);
      await page.locator('#part').filter({hasText: /complete 6-piece bolt stack/}).waitFor({timeout: 30000});
      await page.locator('#part').scrollIntoViewIfNeeded();
      const stackPath = path.join(out, filename), stackSteps = [{action: 'screenshot', path: stackPath}];
      runner.assertEvalStepsAllowed(stackSteps, false); await runner.runSteps(page, stackSteps);
      captures.push({model: models[0], connection, path: stackPath, sha256: hash(fs.readFileSync(stackPath))});
    }
    for (const model of ['eoere-kicker-clearance-frame-development', 'eoere-kicker-clearance-2026-development',
      'eoere-expanded-right-column-development', 'compact-floor-flush-development'])
      assert.equal(await page.locator('#model option[value="' + model + '"]').count(), 1);
    assert.deepEqual(errors, []); assert.deepEqual(failures, []);
    assert.equal(hash(fs.readFileSync('site/index.html')), indexHash);
    const files = ['site/index.html', 'site/eoere-selected-hardware-overlay.mjs', 'site/eoere-selected-hardware-scene.json.gz',
      'scripts/check_eoere_selected_hardware_browser.cjs'];
    const result = {schema: 'eoere_selected_hardware_browser_check/v1', passed: true, captures,
      both_toggle_directions: true, historical_options_preserved: true, page_errors: errors, failed_requests: failures,
      source_sha256: Object.fromEntries(files.map(name => [name, hash(fs.readFileSync(name))])),
      shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))}, chromium_version: browser.version(),
      playwright_version: require(path.join(gwen, 'node_modules/playwright/package.json')).version, bun_version: Bun.version,
      page_context_code_evaluation: false, mechanics_or_physical_release: false};
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify({passed: true, out, captures: captures.length}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
