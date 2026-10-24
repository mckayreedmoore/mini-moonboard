// Check the restored upper stacks and preserve the reference and preceding views.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('../gwen'), runnerPath = path.join(gwen, 'scripts/agent/browser.ts');
const runner = require(runnerPath), {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/';
assert(out && !fs.existsSync(out), 'fresh ignored browser output required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const index = JSON.parse(fs.readFileSync('docs/bolted-frame-development/development-revisions.json'));
assert.equal(index.geometry.revision, 'eoere-reference-cleat-upper-pair-v5');

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  const report = {passed: false, revision: index.geometry.revision, captures: [], models: [],
    page_errors: [], failed_requests: [], page_context_code_evaluation: false,
    chromium: browser.version(), playwright: require(path.join(gwen, 'node_modules/playwright/package.json')).version,
    bun: Bun.version, shared_runner_sha256: hash(fs.readFileSync(runnerPath))};
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    page.on('pageerror', e => report.page_errors.push(e.message));
    page.on('requestfailed', r => report.failed_requests.push(r.url()));
    page.on('response', r => {if (r.status() >= 400 && !r.url().endsWith('/favicon.ico')) report.failed_requests.push(r.url());});
    async function capture(name) {
      const filename = path.join(out, name+'.png'), steps = [{action: 'screenshot', path: filename}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      report.captures.push({name, path: filename, sha256: hash(fs.readFileSync(filename))});
    }
    for (const [label, model, count] of [
      ['current', index.geometry.viewer, 94],
      ['previous', 'eoere-owner-frame-v4-development', 92],
      ['reference', 'eoere-narrow-channels-frame-development', 98],
    ]) {
      const url = new URL(base); url.searchParams.set('model', model); url.searchParams.set('view', 'rear');
      url.searchParams.set('holds', 'off');
      await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      await page.locator('#bolt-view option[value="eoere_bolt_071"]').waitFor({state: 'attached', timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('#bolt-view option:not([value=""])').count(), count);
      const addedCount = await page.locator('#bolt-view option[value="eoere_bolt_067"]').count();
      assert.equal(addedCount, label === 'previous' ? 0 : 1);
      await page.locator('#show-panels').uncheck();
      await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
      await capture(label+'-rear');
      if (label === 'current') {
        assert.match(await page.locator('#model-status').textContent(), /two upper and two lower cleat bolts per corner/);
        assert.match(await page.locator('#model-status').textContent(), /revised strength remain open/);
        for (const axis of ['eoere_bolt_067', 'eoere_bolt_070', 'eoere_bolt_071', 'eoere_bolt_074']) {
          await page.locator('#bolt-view').selectOption(axis);
          await page.locator('#part').filter({hasText: axis+': complete 8-piece bolt stack'}).waitFor();
          assert.equal(await page.locator('#show-holds').isDisabled(), true);
          await capture(axis+'-stack');
        }
        await page.locator('#bolt-view').selectOption('');
        await page.locator('#part').filter({hasText: 'Full assembly restored'}).waitFor();
        assert.equal(await page.locator('#show-holds').isDisabled(), false);
      }
      report.models.push({model, bolt_inspection_options: count, second_upper_axis_present: Boolean(addedCount)});
    }
    assert.deepEqual(report.page_errors, []); assert.deepEqual(report.failed_requests, []);
    report.passed = true;
  } finally {
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2)+'\n', {flag: 'wx'});
    await browser.close();
  }
  console.log(JSON.stringify({passed: report.passed, models: report.models, captures: report.captures.length}));
})().catch(error => {console.error(error); process.exitCode = 1;});
