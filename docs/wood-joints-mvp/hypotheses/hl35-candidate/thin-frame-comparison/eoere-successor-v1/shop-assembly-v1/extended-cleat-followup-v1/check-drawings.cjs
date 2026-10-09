// Render saved SVGs using the existing shared browser dependencies; no page evaluation.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');

let root = __dirname;
while (!fs.existsSync(path.join(root, 'AGENTS.md'))) {
  const parent = path.dirname(root);
  assert.notEqual(root, parent, 'repository root not found');
  root = parent;
}
const shared = process.env.GWEN_BROWSER_ROOT || path.resolve(root, '..', 'gwen');
const {chromium} = require(path.join(shared, 'node_modules/playwright'));
const runnerPath = path.join(shared, 'scripts/agent/browser.ts');
const runner = require(runnerPath);
const sourceDir = path.resolve(process.argv[2] || __dirname);
const out = process.argv[3];
assert(out && !fs.existsSync(out), 'fresh ignored capture directory required');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

(async () => {
  const files = fs.readdirSync(sourceDir).filter(name => name.endsWith('.svg')).sort();
  assert.equal(files.length, 9, 'expected four member, two panel and three operation drawings');
  fs.mkdirSync(out, {recursive: true});
  const browser = await chromium.launch({headless: true});
  const captures = [], errors = [], overflow = [];
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1550}});
    page.on('pageerror', error => errors.push(error.message));
    for (const name of files) {
      const file = path.join(sourceDir, name);
      const before = hash(fs.readFileSync(file));
      await page.setContent('<!doctype html><html><body style="margin:8px">' +
        fs.readFileSync(file, 'utf8') + '</body></html>', {waitUntil: 'load'});
      const svg = page.locator('svg');
      assert.equal(await svg.count(), 1);
      assert.equal(await page.locator('parsererror').count(), 0);
      const box = await svg.boundingBox();
      assert(box);
      for (const text of await svg.locator('text').all()) {
        const bounds = await text.boundingBox();
        if (bounds && (bounds.x < box.x - .5 || bounds.y < box.y - .5 ||
            bounds.x + bounds.width > box.x + box.width + .5 ||
            bounds.y + bounds.height > box.y + box.height + .5)) {
          overflow.push({file: name, text: await text.textContent(), bounds, svg: box});
        }
      }
      const screenshot = path.join(out, name.replace(/\.svg$/, '.png'));
      const steps = [{action: 'screenshot', path: screenshot, fullPage: false}];
      runner.assertEvalStepsAllowed(steps, false);
      await runner.runSteps(page, steps);
      assert.equal(hash(fs.readFileSync(file)), before);
      captures.push({file: name, sha256: before, text_count: await svg.locator('text').count(),
        screenshot: {path: screenshot, sha256: hash(fs.readFileSync(screenshot))}});
    }
    const result = {schema: 'eoere_current_shop_drawing_browser_check/v1',
      passed: errors.length === 0 && overflow.length === 0, captures, errors, overflow,
      checker_sha256: hash(fs.readFileSync(__filename)), chromium: browser.version(),
      playwright: require(path.join(shared, 'node_modules/playwright/package.json')).version,
      shared_runner: {path: runnerPath, sha256: hash(fs.readFileSync(runnerPath))},
      rendering: 'exact saved SVG embedded in a static HTML document; 1440x1550 viewport',
      browser_page_code_evaluation: false, geometry_or_mechanics_acceptance: false};
    fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    console.log(JSON.stringify({passed: result.passed, drawings: files.length, errors, overflow}));
    assert(result.passed, 'browser drawing check failed; retain failure output');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
