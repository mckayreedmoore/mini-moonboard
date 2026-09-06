// Optional browser regression: serve site/ on localhost:8766 and run with
// node scripts/check_development_viewer.cjs [path-to-installed-playwright] [model]
const { chromium } = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const model = process.argv[3] || 'independent-leg-development';
assert.ok(['independent-leg-development', 'screw-spacing-development'].includes(model));
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('requestfailed', request => errors.push(request.url() + ': ' + request.failure().errorText));
  // Expose existing renderer state only in this served test response so real
  // pointer events can exercise the application's raycaster from both sides.
  await page.route('http://127.0.0.1:8766/', async route => {
    const response = await route.fetch();
    await route.fulfill({response, body: (await response.text()).replace('</script>\n  </body>',
      'window.cadTest = {meshes, camera, controls, climberView};</script>\n  </body>')});
  });
  await page.route('http://127.0.0.1:8766/?*', async route => {
    const response = await route.fetch();
    await route.fulfill({response, body: (await response.text()).replace('</script>\n  </body>',
      'window.cadTest = {meshes, camera, controls, climberView};</script>\n  </body>')});
  });
  await page.goto('http://127.0.0.1:8766/?model='+model);
  const manifest = await page.evaluate(async model => (await fetch('hybrid/'+model+'/parts.json')).json(), model);
  await page.waitForFunction(count => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === count,
    manifest.parts.length, {timeout: 120000});
  assert.equal(await page.locator('#model').inputValue(), model);
  const details = await page.locator('#design-details').innerText();
  assert.match(details, /PROVISIONAL/);
  assert.match(details, /candidate FEA not run/);
  assert.match(details, model === 'independent-leg-development' ?
    /No adhesive, interface-friction or external-bracing credit/ : /Mixed-product spacing approval, head seating, materials and resistance unresolved/);
  const plies = manifest.parts.filter(p => /^leg_(left|right)_(inner|outer)$/.test(p.name));
  const stitches = manifest.parts.filter(p => p.name.startsWith('fastener_leg_stitch_'));
  assert.equal(plies.length, 4);
  assert.equal(stitches.length, 6);
  await page.screenshot({path:'/tmp/mini-moonboard-'+model+'-front.png'});
  await page.evaluate(() => {
    const {camera, controls} = window.cadTest;
    camera.position.set(2076.35,321.033374,1134.344356);
    controls.target.set(1276.35,21.033374,1134.344356); controls.update();
  });
  await page.waitForTimeout(150);
  await page.mouse.click(720,500);
  assert.match(await page.locator('#part').innerText(), /^McKay:/);
  await page.locator('#person').uncheck();
  await page.mouse.click(720,500);
  assert.match(await page.locator('#part').innerText(), /^fastener_leg_stitch_left_1:/);
  await page.locator('#dimensions').uncheck();
  const clicked = [];
  async function clickAt(name, x, y, z, side) {
    await page.evaluate(({x,y,z,side}) => {
      const {camera, controls} = window.cadTest;
      camera.position.set(x+side*800, y-500, z);
      controls.target.set(x,y,z); controls.update();
    }, {x,y,z,side});
    await page.waitForTimeout(150);
    await page.mouse.click(720,500);
    const text = await page.locator('#part').innerText();
    assert.ok(text.startsWith(name+':'), name+' got '+text);
    assert.match(text, /NOT structural approval/);
    clicked.push(name);
  }
  // World view mirrors CAD X and offsets assembly Y by -950 mm.
  for (const ply of plies) {
    const sign = ply.name.includes('right') ? 1 : -1;
    const inner = ply.name.endsWith('inner');
    const x = -sign * (inner ? 1266.825 : 1285.875);
    await clickAt(ply.name,x,862.792120+.55*(1403.998388-862.792120)-950,1417.930445*.45,
      inner ? sign : -sign);
    assert.match(await page.locator('#part').innerText(), /19.05/);
  }
  for (const stitch of stitches) {
    const sign = stitch.name.includes('right') ? 1 : -1;
    const index = Number(stitch.name.at(-1))-1, q = [.2,.5,.8][index];
    await clickAt(stitch.name,-sign*1276.35,862.792120+q*(1403.998388-862.792120)-950,
      1417.930445*(1-q),-sign);
    assert.match(await page.locator('#part').innerText(), /capacity unvalidated/);
  }
  await page.screenshot({path:'/tmp/mini-moonboard-'+model+'-stitch.png'});
  await page.goto('http://127.0.0.1:8766/');
  await page.waitForSelector('#model');
  assert.equal(await page.locator('#model').inputValue(),'plywood');
  await page.selectOption('#model',model);
  await page.waitForURL('**/?model='+model);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({loadedParts:manifest.parts.length,clicked,defaultModel:'plywood',selectorNavigation:true,errors}));
  await browser.close();
})().catch(error => {console.error(error);process.exit(1)});
