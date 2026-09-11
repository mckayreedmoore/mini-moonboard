// Serve site/ first. Arguments: Playwright module, base URL, optional screenshot directory.
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8781/';
const artifacts = process.argv[4];
(async () => {
  const browser = await chromium.launch({headless:true, args:['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport:{width:1600,height:1100}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    let catalog = {models:{
      'angle-base-development': {mass_kg:192.73, mass_lb:424.7, basis:'audited CAD', scope:'frame and modeled hardware'},
      plywood: {mass_kg:100, mass_lb:220.46, basis:'mesh estimate', scope:'wood-only geometry'},
      'vertical-principal-development': {mass_kg:-1, mass_lb:20},
    }};
    await page.route('**/prototype-weights.json', route => catalog === null
      ? route.fulfill({status:404, body:'missing'})
      : route.fulfill({contentType:'application/json', body:JSON.stringify(catalog)}));
    // An intentionally stalled CAD manifest proves weights do not depend on mesh loading.
    let release;
    const stalled = new Promise(resolve => { release = resolve; });
    await page.route('**/hybrid/angle-base-development/parts.json', async route => {
      await stalled; await route.continue();
    });
    await page.goto(base+'?model=angle-base-development', {waitUntil:'domcontentloaded'});
    await page.waitForFunction(() => document.querySelector('#prototype-weight')?.textContent.includes('192.7 kg'));
    assert.equal(await page.locator('#design-details').count(), 0);
    assert.equal(await page.locator('#prototype-weight').innerText(), 'Estimated frame weight: 192.7 kg (424.7 lb)');
    assert.match(await page.locator('#prototype-weight-note').innerText(), /assumed material densities; excludes holds, their unmodeled T-nuts and hold bolts, lights and wiring/);
    assert.match(await page.locator('#prototype-weight-note').innerText(), /frame and modeled hardware/);
    assert.match(await page.locator('#model option[value="plywood"]').innerText(), /100.0 kg \(220.5 lb\)/);
    assert.match(await page.locator('#model option[value="vertical-principal-development"]').innerText(), /weight unavailable/);
    assert.ok((await page.locator('#model option').allTextContents()).every(label => /\d+\.\d kg \(\d+\.\d lb\)|weight unavailable/.test(label)));
    release();
    await page.unroute('**/hybrid/angle-base-development/parts.json');
    await page.goto(base+'?model=plywood', {waitUntil:'domcontentloaded'});
    await page.waitForFunction(() => document.querySelector('#prototype-weight-note')?.textContent.includes('wood-only geometry'));
    assert.match(await page.locator('#prototype-weight-note').innerText(), /Mesh volume estimate/);
    catalog = null;
    await page.goto(base+'?model=angle-base-development', {waitUntil:'domcontentloaded'});
    await page.waitForFunction(() => document.querySelector('#prototype-weight')?.textContent.endsWith('unavailable'));
    assert.ok((await page.locator('#model option').allTextContents()).every(label => label.endsWith('weight unavailable')));
    await page.waitForSelector('#design-details');
    assert.match(await page.locator('#design-details').innerText(), /NOT build-ready/);
    assert.deepEqual(errors, []);
    if (artifacts) {
      fs.mkdirSync(artifacts, {recursive:true});
      await page.screenshot({path:path.join(artifacts,'weights-unavailable.png')});
    }
    console.log('Weight units, all menu labels, limited scope, independent loading and missing-catalog fallback passed.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
