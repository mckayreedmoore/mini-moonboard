/* Print source-bound SVG drilling references with the existing Playwright browser. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { pathToFileURL } = require('url');
const { chromium } = require(process.argv[2]);
const directory = path.resolve(process.argv[3] || 'docs/horizontal-service-drilling');
const digest = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async () => {
  const manifestPath = path.join(directory, 'manifest.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath));
  const check = () => {
    for (const [p, sha] of Object.entries(manifest.source_sha256)) {
      if (digest(p) !== sha) throw new Error(`Drawing source changed: ${p}`);
    }
    for (const [p, sha] of Object.entries(manifest.artifact_sha256)) {
      if (digest(path.join(directory, p)) !== sha) throw new Error(`Drawing artifact changed: ${p}`);
    }
  };
  check();
  const output = path.join(directory, 'drilling.pdf');
  if (fs.existsSync(output)) throw new Error('Refusing to overwrite PDF');
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(path.join(directory, 'drilling.html')).href);
    await page.evaluate(() => document.fonts.ready);
    await page.pdf({path: output, preferCSSPageSize: true, printBackground: true});
    check();
    manifest.source_sha256['scripts/print_horizontal_service_drilling.cjs'] = digest(__filename);
    manifest.artifact_sha256['drilling.pdf'] = digest(output);
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
