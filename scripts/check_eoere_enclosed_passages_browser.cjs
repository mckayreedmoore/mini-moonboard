// Reuse the shared Bun/Playwright browser runner; no page-context evaluation.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('..', 'gwen');
const {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const runner = require(path.join(gwen, 'scripts/agent/browser.ts'));
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8771/index.html';
assert(out && !fs.existsSync(out), 'fresh ignored browser output required');
fs.mkdirSync(out, {recursive: true});
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    page.setDefaultTimeout(120000);
    const errors = [], failures = [], checks = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => failures.push(request.url()));
    page.on('response', response => {if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failures.push(response.url());});
    for (const [model, ready, label] of [
      ['eoere-enclosed-passages-frame-development', /Enclosed LED passages/, 'enclosed-rear'],
      ['eoere-narrow-channels-frame-development', /Narrower front openings/, 'preserved-notches-rear'],
    ]) {
      const url = new URL(base); url.searchParams.set('model', model); url.searchParams.set('view', 'rear');
      const response = await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      assert.equal(hash(await response.body()), hash(fs.readFileSync('site/index.html')));
      await page.locator('#model-status').filter({hasText: ready}).waitFor();
      await page.waitForLoadState('networkidle');
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('canvas').count(), 1);
      assert.ok(await page.locator('#bolt-view option').count() >= 99);
      const steps = [{action: 'screenshot', path: path.join(out, label+'.png')}];
      runner.assertEvalStepsAllowed(steps, false); await runner.runSteps(page, steps);
      checks.push({model, status: await page.locator('#model-status').textContent(),
        screenshot: {path: steps[0].path, sha256: hash(fs.readFileSync(steps[0].path))}});
    }
    assert.deepEqual(errors, []); assert.deepEqual(failures, []);
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify({passed: true, checks,
      page_errors: errors, failed_requests: failures, chromium: browser.version(), page_context_evaluation: false,
      source_sha256: Object.fromEntries(['site/index.html', 'site/eoere-enclosed-passages-overlay.mjs',
        'site/eoere-enclosed-passages-scene.json.gz', 'scripts/check_eoere_enclosed_passages_browser.cjs']
        .map(name => [name, hash(fs.readFileSync(name))]))}, null, 2)+'\n');
    console.log(JSON.stringify({passed: true, out}));
  } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
