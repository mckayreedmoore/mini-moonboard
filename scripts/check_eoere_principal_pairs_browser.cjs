// Verify both paired connection families and capture the straight cleat perimeter.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const gwen = path.resolve('../gwen'), runner = require(path.join(gwen, 'scripts/agent/browser.ts'));
const {chromium} = require(path.join(gwen, 'node_modules/playwright'));
const out = process.argv[2], base = process.argv[3] || 'http://127.0.0.1:8767/';
assert(out && !fs.existsSync(out), 'fresh browser output required');fs.mkdirSync(out, {recursive: true});
const hash = b => createHash('sha256').update(b).digest('hex');
const index = JSON.parse(fs.readFileSync('docs/bolted-frame-development/development-revisions.json'));
assert.equal(index.geometry.revision, 'eoere-flat-cleats-principal-upper-pairs-v6');
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  const report = {passed: false, revision: index.geometry.revision, captures: [], models: [],
    errors: [], failed_requests: [], page_context_code_evaluation: false,
    chromium: browser.version(), playwright: require(path.join(gwen, 'node_modules/playwright/package.json')).version};
  try {
    const page = await browser.newPage({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    page.on('pageerror', e => report.errors.push(e.message));
    page.on('requestfailed', r => report.failed_requests.push(r.url()));
    page.on('response', r => {if (r.status() >= 400 && !r.url().endsWith('/favicon.ico')) report.failed_requests.push(r.url());});
    const capture = async name => {
      const filename = path.join(out, name+'.png'), steps = [{action: 'screenshot', path: filename}];
      runner.assertEvalStepsAllowed(steps, false);await runner.runSteps(page, steps);
      report.captures.push({name, path: filename, sha256: hash(fs.readFileSync(filename))});
    };
    for (const [model, count] of [[index.geometry.viewer, 96], ['eoere-owner-frame-v5-development', 94]]) {
      const current = model === index.geometry.viewer;
      const url = new URL(base);url.searchParams.set('model', model);url.searchParams.set('view', 'rear');
      url.searchParams.set('revision', index.geometry.revision);url.searchParams.set('holds', 'off');
      await page.goto(url.href, {waitUntil: 'domcontentloaded'});
      await page.locator('#bolt-view option[value="eoere_bolt_071"]').waitFor({state: 'attached', timeout: 120000});
      await page.waitForLoadState('networkidle', {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), model);
      assert.equal(await page.locator('#bolt-view option:not([value=""])').count(), count);
      for (const axis of ['eoere_bolt_068', 'eoere_bolt_069'])
        assert.equal(await page.locator('#bolt-view option[value="'+axis+'"]').count(), current ? 1 : 0);
      await page.locator('#show-panels').uncheck();await page.locator('#person').uncheck();await page.locator('#dimensions').uncheck();
      await page.locator('#model').scrollIntoViewIfNeeded();await capture(current ? 'current-rear' : 'preserved-v5-rear');
      if (current) {
        assert.match(await page.locator('#model-status').textContent(), /flat cleat sides without tabs or steps/);
        assert.match(await page.locator('#model-status').textContent(), /Two upper bolts at each cleat and each center principal\/header connection/);
        for (const axis of ['eoere_bolt_067', 'eoere_bolt_070', 'eoere_bolt_071', 'eoere_bolt_074',
          'eoere_bolt_068', 'eoere_bolt_069', 'eoere_bolt_072', 'eoere_bolt_073']) {
          const pieces = ['eoere_bolt_068', 'eoere_bolt_069', 'eoere_bolt_072', 'eoere_bolt_073'].includes(axis) ? 5 : 8;
          await page.locator('#bolt-view').selectOption(axis);
          await page.locator('#part').filter({hasText: axis+': complete '+pieces+'-piece bolt stack'}).waitFor();
          if (['eoere_bolt_068', 'eoere_bolt_069'].includes(axis)) await capture(axis+'-stack');
        }
        await page.locator('#bolt-view').selectOption('');
        await page.locator('#part').filter({hasText: 'Full assembly restored'}).waitFor();
        await page.mouse.move(848, 820);await page.mouse.down({button: 'right'});
        await page.mouse.move(720, 500, {steps: 12});await page.mouse.up({button: 'right'});
        await page.mouse.wheel(0, -600);await page.waitForTimeout(350);
        await capture('current-cleat-closeup');
        console.log('Current 96-bolt view and all eight upper-stack inspections pass');
      }
      report.models.push({model, bolt_inspection_options: count});
    }
    assert.deepEqual(report.errors, []);assert.deepEqual(report.failed_requests, []);report.passed = true;
  } finally {
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2)+'\n', {flag: 'wx'});
    await browser.close();
  }
  console.log(JSON.stringify({passed: report.passed, captures: report.captures.length, models: report.models}));
})().catch(e => {console.error(e);process.exitCode = 1;});
