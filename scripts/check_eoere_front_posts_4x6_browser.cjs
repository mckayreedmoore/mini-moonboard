// Render both 4×6-post variants with the shared Gwen screenshot runner.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('../gwen'), runnerPath = path.join(gwen, 'scripts/agent/browser.ts');
const runner = require(runnerPath), {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const out = process.argv[2];
assert(out && !fs.existsSync(out), 'fresh ignored browser output directory required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const base = process.argv[3] || 'http://127.0.0.1:8779/index.html';
const models = ['eoere-4x6-front-posts-frame-development', 'eoere-4x6-front-posts-grid-development'];
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    page.setDefaultTimeout(90000); page.setDefaultNavigationTimeout(90000);
    const errors = [], failures = [], captures = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('requestfailed', r => failures.push(r.url()));
    page.on('response', r => {if (r.status() >= 400 && !r.url().endsWith('/favicon.ico')) failures.push(r.url());});
    const indexHash = hash(fs.readFileSync('site/index.html'));
    const url = new URL(base); url.searchParams.set('model', models[0]); url.searchParams.set('view', 'rear'); url.searchParams.set('holds', 'off');
    const response = await page.goto(url.href, {waitUntil: 'domcontentloaded'});
    assert.equal(hash(await response.body()), indexHash);
    for (const [i, model] of models.entries()) {
      if (i) {await page.locator('#update-2026').check(); await page.waitForURL(/model=eoere-4x6-front-posts-grid-development/);}
      await page.locator('#model-status').filter({hasText: /Solid 4×6 outer kicker posts/}).waitFor({timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('#update-2026').isChecked(), Boolean(i));
      assert.match(await page.locator('#model-status').textContent(), /Revised response, complete joints and installation remain unqualified/);
      assert.equal(await page.locator('canvas').count(), 1);
      await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck(); await page.locator('#show-panels').uncheck();
      const filename = path.join(out, i ? '4x6-posts-grid-rear.png' : '4x6-posts-base-rear.png');
      const steps = [{action: 'screenshot', path: filename}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      captures.push({model, url: page.url(), path: filename, sha256: hash(fs.readFileSync(filename))});
    }
    await page.locator('#update-2026').uncheck(); await page.waitForURL(/model=eoere-4x6-front-posts-frame-development/);
    await page.locator('#model-status').filter({hasText: /Solid 4×6 outer kicker posts/}).waitFor({timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    for (const [axis, count] of [['cleat_post_bolt_left_1', 7], ['rail_front_bolt_right_2', 5]]) {
      await page.locator('#bolt-view').selectOption(axis);
      await page.locator('#part').filter({hasText: 'complete '+count+'-piece bolt stack'}).waitFor();
    }
    assert.equal(await page.locator('a.support-link').filter({hasText: 'Current eoere geometry'}).getAttribute('href'), '?model='+models[0]+'&view=rear');
    for (const model of ['eoere-selected-hardware-frame-development', 'eoere-selected-hardware-grid-development',
      'eoere-kicker-clearance-frame-development', 'compact-floor-flush-development'])
      assert.equal(await page.locator('#model option[value="'+model+'"]').count(), 1);
    assert.deepEqual(errors, []); assert.deepEqual(failures, []);
    assert.equal(hash(fs.readFileSync('site/index.html')), indexHash);
    const files = ['site/index.html', 'site/eoere-front-posts-4x6-overlay.mjs', 'site/eoere-front-posts-4x6-scene.json.gz', __filename];
    fs.writeFileSync(path.join(out, 'browser-check.json'), JSON.stringify({passed: true, captures,
      grid_toggle_both_directions: true, seven_and_five_piece_stacks: true, historical_options_preserved: true,
      page_errors: errors, failed_requests: failures, page_context_code_evaluation: false,
      source_sha256: Object.fromEntries(files.map(f => [f, hash(fs.readFileSync(f))])),
      shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))},
      chromium: browser.version(), playwright: require(path.join(gwen, 'node_modules/playwright/package.json')).version,
      bun: Bun.version}, null, 2)+'\n', {flag:'wx'});
    console.log(JSON.stringify({passed: true, captures: captures.length}));
  } finally {await browser.close();}
})().catch(e => {console.error(e); process.exitCode=1;});
