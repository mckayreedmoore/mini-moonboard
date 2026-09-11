// Real viewer controls; optional missing-category fixtures are test-only and never exported.
// Arguments: Playwright module, base URL, model key (default angle-base-development).
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[3] || 'http://127.0.0.1:8781/';
const model = process.argv[4] || 'angle-base-development';
const actual = process.argv.includes('--actual');
const artifacts = process.argv[5] && process.argv[5] !== '--actual' ? process.argv[5] : null;
if (artifacts) assert.ok(actual, 'Screenshots require actual assets, never synthetic fixtures');
(async () => {
  const browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport:{width:1600,height:1100}});
    const errors=[]; page.on('pageerror', e=>errors.push(e.message));
    await page.route(url=>url.origin===new URL(base).origin&&url.pathname===new URL(base).pathname,async route=>{
      const response=await route.fetch();
      await route.fulfill({response,body:(await response.text()).replace('</script>\n  </body>',
        'window.visibilityTest={meshes,categoryFor,camera,controls,scene};</script>\n  </body>')});
    });
    let count;
    await page.route('**/hybrid/'+model+'/parts.json',async route=>{
      const response=await route.fetch(); const data=await response.json();
      // Reuse a tiny real hardware mesh solely to exercise absent kind classifications.
      // These synthetic fixtures do not claim real light/wire/insert geometry or placement.
      for(const kind of actual ? [] : ['light','wire','insert']) if(!data.parts.some(p=>p.fabrication.kind===kind)) {
        const part=data.parts.find(p=>p.fabrication.kind==='screw');
        data.parts.push({...part,name:'test_fixture_'+kind,fabrication:{...part.fabrication,kind}});
      }
      count=data.parts.length; await route.fulfill({response,json:data});
    });
    await page.goto(base+'?model='+model);
    await page.waitForFunction(()=>window.visibilityTest?.meshes.filter(m=>m.userData.part.name!=='McKay').length>=1);
    await page.waitForFunction(n=>window.visibilityTest.meshes.filter(m=>m.userData.part.name!=='McKay').length===n,count,{timeout:120000});
    assert.equal(await page.locator('#part-visibility input').count(),8);
    console.log('Loaded '+count+' actual/fixture meshes; checking category controls.');
    if (actual && model === 'horizontal-service-development') {
      const counts = await page.evaluate(() => ['light','wire'].map(kind => window.visibilityTest.meshes.filter(m => m.userData.part.fabrication?.kind === kind).length));
      assert.deepEqual(counts, [132,131]);
    }
    if (artifacts) {
      fs.mkdirSync(artifacts,{recursive:true});
      await page.waitForTimeout(250);
      await page.screenshot({path:path.join(artifacts,model+'-lights-front.png')});
    }
    for(const category of ['panels','timber','brackets','bolts','screws','inserts','lights','wiring']) {
      console.log('Checking '+category);
      const before=await page.evaluate(category=>window.visibilityTest.meshes.filter(m=>
        m.userData.part.name!=='McKay'&&window.visibilityTest.categoryFor(m.userData.part)===category).length,category);
      if (!actual) assert.ok(before>0,category);
      await page.locator('#show-'+category).evaluate(input=>{ if(input.checked) input.click(); });
      assert.equal(await page.evaluate(category=>window.visibilityTest.meshes.filter(m=>m.visible&&
        m.userData.part.name!=='McKay'&&window.visibilityTest.categoryFor(m.userData.part)===category).length,category),0);
      await page.locator('#show-'+category).evaluate(input=>{ if(!input.checked) input.click(); });
    }
    console.log('All category toggles checked.');
    const lights=await page.evaluate(()=>window.visibilityTest.meshes.filter(m=>m.userData.part.fabrication?.kind==='light')
      .map(m=>({color:m.material.emissive.getHex(),intensity:m.material.emissiveIntensity})));
    assert.ok(lights.every(l=>l.color===0x00ff35&&l.intensity>0));
    assert.equal(await page.evaluate(()=>{let n=0;window.visibilityTest.scene.traverse(o=>{if(o.isPointLight)n++;});return n;}),0);
    await page.locator('#show-panels').evaluate(input=>{ if(input.checked) input.click(); });
    if (artifacts) {
      await page.locator('#person').evaluate(input=>{ if(input.checked) input.click(); }); await page.locator('#dimensions').evaluate(input=>{ if(input.checked) input.click(); });
      await page.evaluate(() => {
        const {camera,controls}=window.visibilityTest;
        camera.position.set(3700,-4300,2500); controls.target.set(0,-250,1100); controls.update();
      });
      await page.waitForTimeout(250);
      await page.screenshot({path:path.join(artifacts,model+'-wiring-rails.png')});
      await page.setViewportSize({width:390,height:844}); await page.waitForTimeout(250);
      await page.screenshot({path:path.join(artifacts,model+'-categories-narrow.png')});
      await page.setViewportSize({width:1600,height:1100});
    }
    await page.locator('#show-bolts').evaluate(input=>{ if(input.checked) input.click(); });
    const value=await page.locator('#bolt-view option').nth(1).getAttribute('value');
    await page.selectOption('#bolt-view',value);
    assert.equal(await page.evaluate(()=>window.visibilityTest.meshes.filter(m=>m.visible).length),5);
    assert.equal(await page.locator('#show-panels').isDisabled(),true);
    await page.selectOption('#bolt-view','');
    assert.equal(await page.locator('#show-panels').isChecked(),false);
    assert.equal(await page.locator('#show-bolts').isChecked(),false);
    assert.equal(await page.locator('#show-panels').isDisabled(),false);
    assert.equal(await page.evaluate(()=>window.visibilityTest.meshes.filter(m=>m.visible&&
      ['panels','bolts'].includes(window.visibilityTest.categoryFor(m.userData.part))).length),0);
    assert.deepEqual(errors,[]);
    console.log('Eight category toggles, green emissive lights without PointLights, and inspector category restoration passed. '+(actual ? 'Actual exported assets only.' : 'Missing kinds used explicitly synthetic test fixtures.'));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
