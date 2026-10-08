// Run with Bun from the repo root and an existing Playwright module path.
// No injected page code or page-context evaluation is used.
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const base = process.argv[3] || 'http://127.0.0.1:8767/index.html';
const output = process.argv[4] || 'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/browser-v2';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
assert(!fs.existsSync(output), 'preserve earlier browser evidence; choose a new output');
fs.mkdirSync(output, {recursive: true});

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--enable-unsafe-swiftshader']});
  try {
    const context = await browser.newContext({ignoreHTTPSErrors: true, viewport: {width: 1440, height: 1000}});
    const page = await context.newPage(), results = [], errors = [], failedResponses = [], failedRequests = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => {
      if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) failedResponses.push([response.status(), response.url()]);
    });
    page.on('requestfailed', request => failedRequests.push([request.url(), request.failure()?.errorText]));
    for (const view of ['front', 'rear']) {
      const url = new URL(base);
      url.searchParams.set('model', 'eoere-bolted-development');
      if (view === 'rear') url.searchParams.set('view', 'rear');
      const response = await page.goto(url.href, {waitUntil: 'domcontentloaded', timeout: 60000});
      const status = page.locator('#model-status');
      await status.filter({hasText: /Latest eoere proposal/}).waitFor({state: 'visible', timeout: 60000});
      await page.waitForLoadState('networkidle', {timeout: 60000});
      assert.equal(await page.locator('#model').inputValue(), 'eoere-bolted-development');
      assert.equal(await page.locator('canvas').count(), 1);
      // Two unchanged leg pairs have one representative example per side.
      // The genuine Three/file-backed check verifies all 100 physical stacks.
      assert.equal(await page.locator('#bolt-view option').count(), 99);
      assert.equal(await page.locator('#bolt-view option:disabled').count(), 0);
      for (const retained of ['thin-bolted-development', 'wood-joints-reviewed', 'compact-floor-flush-development']) {
        assert.equal(await page.locator(`#model option[value="${retained}"]`).count(), 1);
      }
      assert.match(await status.textContent(), /strength.*pending/i);
      await page.locator('#person').uncheck();
      await page.locator('#dimensions').uncheck();
      if (view === 'rear') await page.locator('#show-panels').uncheck();
      const screenshot = path.join(output, `eoere-${view}.png`);
      await page.screenshot({path: screenshot, timeout: 10000});
      results.push({view, url: url.href, status: await status.textContent(), connection_examples: 98,
        screenshot: {path: screenshot, bytes: fs.statSync(screenshot).size, sha256: hash(fs.readFileSync(screenshot))},
        index_html_sha256: hash(await response.body())});
      console.log(JSON.stringify(results.at(-1)));
    }
    await page.locator('#bolt-view').selectOption('cleat_post_bolt_left_2');
    await page.locator('#bolt-view-note').waitFor({state: 'visible'});
    await page.screenshot({path: path.join(output, 'cleat-bolt-inspection.png'), timeout: 10000});
    await page.locator('#bolt-view').selectOption('');
    assert.equal(await page.locator('#show-panels').isChecked(), false);
    assert.deepEqual(errors, []);
    assert.deepEqual(failedResponses, []);
    assert.deepEqual(failedRequests, []);
    const receipt = {schema: 'eoere_bolted_browser_check/v1', passed: true,
      command: process.argv, cwd: process.cwd(), playwright_version: require(path.join(process.argv[2], 'package.json')).version,
      browser_version: browser.version(), results, connection_inspection_checked: true,
      page_errors: errors, failed_responses: failedResponses, failed_requests: failedRequests,
      page_context_evaluation: false, geometry_strength_or_physical_release: false};
    fs.writeFileSync(path.join(output, 'browser-check.json'), JSON.stringify(receipt, null, 2) + '\n');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
