// Verify loose pad geometry without changing or waiting for structural CAD inventory.
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const key = process.argv[4] || 'compact-exterior-brace-development';
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport: {width: 1600, height: 1000}});
    page.setDefaultTimeout(20000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route(url => url.origin === new URL(base).origin && url.pathname === new URL(base).pathname, async route => {
      const response = await route.fetch();
      const source = await response.text();
      const marker = '</script>\n  </body>';
      assert.ok(source.includes(marker));
      await route.fulfill({response, body: source.replace(marker,
        'window.padTest={crashPadGroup,crashPadMeshes,meshes,assemblyView,THREE};'+marker)});
    });
    const url = new URL(base); url.searchParams.set('model', key);
    await page.goto(url.href, {waitUntil: 'domcontentloaded'});
    await page.waitForFunction(() => window.padTest?.crashPadMeshes.length === 2);
    assert.equal(await page.locator('#model').inputValue(), key);
    assert.equal(await page.locator('#model optgroup[label="Current design"] option').getAttribute('value'), 'compact-floor-flush-development');
    assert.equal(await page.locator('#model optgroup[label="Development candidates"] option[value="compact-floor-taper-development"]').count(), 1);
    assert.ok(await page.locator('#show-crash-pads').isChecked());
    const geometry = await page.evaluate(() => {
      const {crashPadMeshes:pads,crashPadGroup:group,meshes,THREE} = window.padTest;
      return {visible:group.visible, structuralCount:meshes.length,
        separate:pads.every(pad => !meshes.includes(pad)),
        pads:pads.map(pad => {
          pad.geometry.computeBoundingBox();
          const b=pad.geometry.boundingBox.clone().translate(pad.position);
          return {min:b.min.toArray(),max:b.max.toArray(),size:b.getSize(new THREE.Vector3()).toArray(),
            color:pad.material.color.getHex(),structural:pad.userData.crashPad.structural,mass:pad.userData.crashPad.mass_included};
        })};
    });
    assert.ok(geometry.visible && geometry.separate);
    assert.notEqual(geometry.pads[0].color,geometry.pads[1].color);
    geometry.pads.forEach((pad,index) => {
      [2438.4,914.4,127].forEach((value,axis) => assert.ok(Math.abs(pad.size[axis]-value)<.001));
      [-1219.2,index*914.4,0].forEach((value,axis) => assert.ok(Math.abs(pad.min[axis]-value)<.001));
      assert.equal(pad.structural,false); assert.equal(pad.mass,false);
    });
    assert.match(await page.locator('#crash-pad-note').innerText(),/96 × 36 × 5 in/);
    assert.match(await page.locator('#crash-pad-note').innerText(),/excluded from frame weight and structural checks/);
    await page.locator('#show-crash-pads').uncheck();
    assert.equal(await page.evaluate(() => window.padTest.crashPadGroup.visible),false);
    await page.locator('#show-crash-pads').check();
    assert.equal(await page.evaluate(() => window.padTest.crashPadGroup.visible),true);
    assert.deepEqual(errors,[]);
    console.log(key+': two exact96×36×5in floor pads, front-to-back bounds, separate inventory and toggle verified');
  } finally { await browser.close(); }
})().catch(error => { console.error(error);process.exitCode=1; });
