// Real browser navigation/screenshots through the shared Gwen runner; no eval.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('..', 'gwen');
const {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const runnerPath = path.join(gwen, 'scripts/agent/browser.ts'), runner = require(runnerPath);
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/index.html';
assert(out && !fs.existsSync(out), 'fresh ignored screenshot directory required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const model = 'eoere-lower-cleat-z180-development', original = 'eoere-extended-cleat-frame-development';

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    page.setDefaultTimeout(120000);
    const errors = [], failed = [], captures = [], navigation = [];
    const indexHash = hash(fs.readFileSync('site/index.html'));
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failed.push(request.url()));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failed.push(response.url());
    });
    async function ready(expected, text) {
      await page.locator('#model-status').filter({hasText: text}).waitFor({timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), expected);
      assert.equal(await page.locator('canvas').count(), 1);
      assert.equal(await page.locator('#bolt-view option').count(), 99);
      assert.equal(await page.locator('#bolt-view option[value="cleat_post_bolt_left_1"]').isDisabled(), false);
      assert.equal(await page.locator('a.support-link').filter({hasText: 'Current eoere geometry'}).getAttribute('href'), `?model=${original}&view=rear`);
      navigation.push({model: expected, status: await page.locator('#model-status').textContent()});
    }
    async function capture(name) {
      const steps = [{action: 'screenshot', path: path.join(out, name)}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      captures.push({url: page.url(), selected_bolt: await page.locator('#bolt-view').inputValue(),
        screenshot: {path: steps[0].path, sha256: hash(fs.readFileSync(steps[0].path))}, index_html_sha256: indexHash});
    }
    const url = new URL(base); url.searchParams.set('model', model); url.searchParams.set('view', 'rear');
    const response = await page.goto(url.href, {waitUntil: 'domcontentloaded'});
    assert.equal(hash(await response.body()), indexHash);
    await ready(model, /Unadopted Z180 proposal.*Current six-case results remain bound to Z200/);
    assert.equal(await page.locator('#update-2026').isVisible(), false);
    await capture('z180-rear.png');
    for (const side of ['left', 'right']) {
      const bolt = `cleat_post_bolt_${side}_1`;
      await page.locator('#bolt-view').selectOption(bolt);
      await page.locator('#part').filter({hasText: `${bolt}: complete 5-piece bolt stack`}).waitFor();
      assert.equal(await page.locator('#part-visibility').isDisabled(), true);
      await capture(`z180-${side}-bolt.png`);
    }
    await page.locator('#bolt-view').selectOption('');
    await page.locator('#part').filter({hasText: 'Full assembly restored'}).waitFor();
    await page.locator('#model').selectOption(original);
    await ready(original, /Maximum cleat blank 361.186 mm/);
    assert.equal(await page.locator('#update-2026').isChecked(), false);
    for (const key of [model, 'eoere-extended-cleat-2026-development', 'eoere-adjusted-frame-development',
      'eoere-bolted-aligned-wire-development', 'compact-floor-flush-development'])
      assert.equal(await page.locator(`#model option[value="${key}"]`).count(), 1);
    assert.deepEqual(errors, []); assert.deepEqual(failed, []);
    assert.equal(hash(fs.readFileSync('site/index.html')), indexHash);
    const files = ['site/index.html', 'site/eoere-lower-cleat-z180-overlay.mjs',
      'site/eoere-lower-cleat-z180-scene.json.gz', 'scripts/check_eoere_lower_cleat_z180_browser.cjs'];
    const result = {schema: 'eoere_lower_cleat_z180_browser_check/v1', passed: true, captures, navigation,
      unadopted_label_verified: true, old_current_link_preserved: true, old_options_preserved: true,
      new_model_extra_grid_disabled: true, left_and_right_complete_stack_inspection: true,
      page_errors: errors, failed_requests_or_responses: failed,
      source_sha256: Object.fromEntries(files.map(name => [name, hash(fs.readFileSync(name))])),
      shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))},
      chromium_version: browser.version(), playwright_version: require(path.join(gwen, 'node_modules/playwright/package.json')).version,
      bun_version: Bun.version, page_context_code_evaluation: false, mechanics_or_physical_release: false};
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify({passed: true, out, captures: captures.length, errors, failed}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
