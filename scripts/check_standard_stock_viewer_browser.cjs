// One current-stock model, two selections. DOM only; no injected page evaluation.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
assert(typeof Bun !== 'undefined', 'Run with Bun and the existing Playwright installation');
const {chromium} = require(process.argv[2]), url = new URL(process.argv[3]), out = process.argv[4];
assert.equal(url.searchParams.get('model'), 'eoere-standard-4x6-top-and-sides-preview');
assert(out && !fs.existsSync(out), 'fresh ignored browser output required');
fs.mkdirSync(out, {recursive: true});
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  const report = {passed: false, model: url.searchParams.get('model'), url: url.href, chromium: browser.version(),
    scope: 'one portable model, DOM/status/document routes and two stack selections; no measured geometry or structural acceptance',
    expected_parts_from_loader_contract: 1151, pageErrors: [], failedRequests: [], ignoredRequests: [],
    actual_Cg_adopted: null, complete_connection_capacity: null, custom_packers_approved: false, current_alias_promoted: false};
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    page.on('pageerror', error => report.pageErrors.push(error.message));
    page.on('requestfailed', request => report.failedRequests.push(request.url()));
    page.on('request', request => {if (new URL(request.url()).pathname.includes('/fea/')) report.ignoredRequests.push(request.url());});
    page.on('response', response => {if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) report.failedRequests.push(response.url());});
    await page.goto(url.href, {waitUntil: 'domcontentloaded'});
    await page.locator('#bolt-view option[value="eoere_bolt_006"]').waitFor({state: 'attached', timeout: 120000});
    await page.waitForLoadState('networkidle', {timeout: 120000});
    assert.equal(await page.locator('#model').inputValue(), report.model);
    assert.equal(await page.locator('#bolt-view option:not([value=""])').count(), 116);
    assert.equal(await page.locator('#bolt-view option:not([value=""]):disabled').count(), 0);
    const status = await page.locator('#model-status').textContent();
    assert.match(status, /Own six 250 lb cases/); assert.match(status, /declared conditional vector section reference reaches 0\.998500/);
    assert.match(status, /Fifteen bearing diagnostic rows/); assert.match(status, /Actual Cg and complete joint capacity remain unqualified/);
    assert.match(status, /Custom packers remain unapproved/); assert.doesNotMatch(status, /pending|safety margin/i); report.status = status;
    const labels = await page.locator('#model option').allTextContents();
    assert(labels.some(label => label.startsWith('Current standard 4×6 top and sides')));
    for (const alias of ['eoere-current-frame-development', 'eoere-owner-frame-v10-development'])
      assert.match(await page.locator('#model option[value="'+alias+'"]').textContent(), /Preserved V10 Candidate 13/);
    assert(await page.locator('canvas').first().isVisible());
    for (const id of ['eoere_bolt_006', 'rail_rear_bolt_left_1']) {
      await page.locator('#bolt-view').selectOption(id); await page.locator('#part').filter({hasText: id+': complete '}).waitFor();
    }
    await page.locator('#bolt-view').selectOption(''); await page.locator('#part').filter({hasText: 'Full assembly restored'}).waitFor();
    // Read individual DOM attributes without evaluating page code.
    const hrefs = [], anchors = page.locator('#shop-docs a');
    for (let i=0;i<await anchors.count();i++) hrefs.push(await anchors.nth(i).getAttribute('href'));
    assert(hrefs.some(href => href?.endsWith('/standard-side-stock/connection-method-evaluation.json')));
    assert(hrefs.some(href => href?.endsWith('/standard-side-stock/response-bank.json')));
    await page.locator('#show-panels').uncheck(); await page.locator('#person').uncheck(); await page.locator('#dimensions').uncheck();
    await page.screenshot({path: path.join(out, 'portable-standard-stock-rear.png')});
    assert.deepEqual(report.pageErrors, []); assert.deepEqual(report.failedRequests, []); assert.deepEqual(report.ignoredRequests, []);
    report.passed = true; report.bolt_options = 116; report.stack_selections_checked = 2; report.document_hrefs = hrefs;
  } finally {
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2)+'\n'); await browser.close();
  }
  console.log(JSON.stringify(report));
})().catch(error => {console.error(error); process.exitCode = 1;});
