// Bounded smoke checks for separately exported clear-space development models.
// Usage: node scripts/check_clear_space_viewer.cjs PLAYWRIGHT_PATH BASE_URL
const {chromium} = require(process.argv[2] || 'playwright');
const assert = require('node:assert/strict');
const base = process.argv[3] || 'http://127.0.0.1:8767/';
const candidates = [
  {key: 'compact-floor-rail-development', meshes: 725, bolts: 12, knees: 0, rails: 2, accepted: true, documents: 'clear-space'},
  {key: 'compact-floor-taper-development', meshes: 725, bolts: 12, knees: 0, rails: 2, accepted: true, documents: 'floor-runner-taper'},
  {key: 'compact-floor-recess-development', meshes: 725, bolts: 12, knees: 0, rails: 2, accepted: null, documents: 'floor-runner-recess'},
  {key: 'compact-floor-rail-2x4-development', meshes: 735, bolts: 14, knees: 0, rails: 2, accepted: false, documents: 'floor-rail-2x4'},
  {key: 'compact-exterior-brace-development', meshes: 767, bolts: 20, knees: 4, rails: 0, accepted: true, documents: 'clear-space'},
];

(async () => {
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  try {
    for (const expected of candidates) {
      const page = await browser.newPage({viewport: {width: 1400, height: 1000}});
      page.setDefaultTimeout(15000);
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route(url => url.origin === new URL(base).origin && url.pathname === new URL(base).pathname,
        async route => {
          const response = await route.fetch();
          const body = await response.text();
          const marker = '</script>\n  </body>';
          assert.ok(body.includes(marker), 'Viewer test hook insertion remains valid');
          await route.fulfill({response, body: body.replace(marker,
            'window.cadTest = {meshes, THREE};'+marker)});
        });
      const url = new URL(base);
      if (expected.key !== 'compact-exterior-brace-development') url.searchParams.set('model', expected.key);
      else url.searchParams.delete('model');
      url.searchParams.set('view', 'rear');
      console.log('Loading', expected.key);
      await page.goto(url.href, {waitUntil: 'domcontentloaded', timeout: 30000});
      const manifest = await page.evaluate(async key => {
        const response = await fetch('hybrid/'+key+'/parts.json');
        if (!response.ok) throw new Error('Missing candidate manifest: '+response.status);
        return response.json();
      }, expected.key);
      assert.equal(manifest.parts.length, expected.meshes);
      await page.waitForFunction(n => window.cadTest?.meshes.filter(m => m.userData.part.name !== 'McKay').length === n,
        expected.meshes, {timeout: 120000});
      assert.equal(await page.locator('#model').inputValue(), expected.key);
      assert.equal(await page.locator('#model optgroup[label="Current design"] option').count(), 1);
      assert.equal(await page.locator('#model optgroup[label="Current design"] option').getAttribute('value'),
        'compact-exterior-brace-development');
      for (const candidate of candidates.filter(row => row.key !== 'compact-exterior-brace-development')) {
        assert.equal(await page.locator('#model optgroup[label="Development candidates"] option[value="'+candidate.key+'"]').count(), 1);
      }
      for (const document of [expected.documents+'-study.md', expected.documents+'-hardware.md']) {
        assert.equal(await page.locator('#model-documents a[href$="'+document+'"]').count(), 1);
      }
      assert.equal(manifest.design.main_face_height_mm, 277);
      assert.ok(Math.abs(manifest.design.upper_bolt_pitch_mm-(expected.key === 'compact-exterior-brace-development' ? 64 : 56)) < 1.e-6);
      if (expected.key === 'compact-exterior-brace-development') {
        assert.equal(manifest.design.floor_friction_assumption.kind, 'per_cell_coulomb');
        assert.equal(manifest.design.floor_friction_assumption.mu_assumed, .4);
        assert.equal(manifest.design.floor_friction_assumption.measured_floor, false);
      }
      if (expected.accepted === null) assert.match(manifest.design.status, /^(Development|NOT ACCEPTED)/);
      else assert.ok(manifest.design.status.startsWith(expected.accepted ? 'Conditional listed checks met' : 'NOT ACCEPTED'));
      assert.equal(manifest.parts.filter(p => /^base_knee_(left|right)_(rim|leg)$/.test(p.name)).length, expected.knees);
      assert.equal(manifest.parts.filter(p => /^base_floor_(left|right)$/.test(p.name)).length, expected.rails);
      assert.ok(manifest.parts.every(p => p.path.startsWith('hybrid/'+expected.key+'/models/')));
      assert.ok(manifest.parts.every(p => !p.translation_mm));
      const stacks = new Map();
      for (const part of manifest.parts.filter(p => p.fabrication.kind === 'bolt')) {
        const {connection_name: name, hardware_role: role} = part.fabrication;
        if (!stacks.has(name)) stacks.set(name, []);
        stacks.get(name).push(role);
      }
      assert.equal(stacks.size, expected.bolts);
      for (const roles of stacks.values()) {
        assert.deepEqual(roles.sort(), ['far_washer', 'head', 'near_washer', 'nut', 'shaft']);
      }
      const geometry = await page.evaluate(() => {
        const stacks = new Map();
        const knees = [], rails = [], lowerKicker = [], outerKickerX = [], baseClips = [], rims = [];
        let header;
        for (const mesh of window.cadTest.meshes) {
          const part = mesh.userData.part;
          mesh.geometry.computeBoundingBox();
          const box = mesh.geometry.boundingBox.clone().translate(mesh.position);
          if (part.name === 'base_header') header = {minY: box.min.y, maxY: box.max.y};
          if (/^clip_angle_base_(left|right)$/.test(part.name)) baseClips.push({minY: box.min.y, maxY: box.max.y});
          if (/^base_side_(left|right)$/.test(part.name)) rims.push({minY: box.min.y});
          const f = part.fabrication;
          if (f?.kind === 'bolt' && ['head', 'nut'].includes(f.hardware_role)) {
            const row = stacks.get(f.connection_name) || {};
            row[f.hardware_role] = Math.abs(box.getCenter(new window.cadTest.THREE.Vector3()).x);
            stacks.set(f.connection_name, row);
          }
          if (/^base_knee_(left|right)_(rim|leg)$/.test(part.name)) knees.push({name: part.name, minX: box.min.x, maxX: box.max.x});
          if (/^base_floor_(left|right)$/.test(part.name)) rails.push({name: part.name, minZ: box.min.z, minX: box.min.x, maxX: box.max.x});
          if (/^fastener_round_kicker_(left|right)_(rim|center)_1$/.test(part.name)) lowerKicker.push((box.min.z+box.max.z)/2);
          if (/^fastener_round_kicker_(left|right)_rim_1$/.test(part.name)) outerKickerX.push(Math.abs((box.min.x+box.max.x)/2));
        }
        return {stacks: [...stacks.values()], knees, rails, lowerKicker, outerKickerX, baseClips, header, rims};
      });
      assert.equal(geometry.baseClips.length, 2);
      assert.ok(geometry.baseClips.every(c => c.minY >= geometry.header.minY+19.04 && c.maxY <= geometry.header.maxY-19.04));
      assert.equal(geometry.rims.length, 2);
      assert.ok(geometry.rims.every(r => Math.abs(geometry.header.minY-r.minY-7) < .01));
      assert.equal(geometry.stacks.length, expected.bolts);
      assert.ok(geometry.stacks.every(row => row.nut > row.head), 'Every bolt tip faces outward');
      assert.equal(geometry.knees.length, expected.knees);
      assert.ok(geometry.knees.every(row => row.name.includes('_left_') ? row.maxX <= -1219.19 : row.minX >= 1219.19),
        'All exterior knee wood stays outside panel edges');
      assert.equal(geometry.rails.length, expected.rails);
      assert.ok(geometry.rails.every(row => Math.abs(row.minZ) < .01), 'Rails reach floor');
      if (['compact-floor-recess-development', 'compact-floor-taper-development'].includes(expected.key)) {
        assert.ok(geometry.rails.every(row => row.name.endsWith('left') ? row.maxX <= -1219.19 : row.minX >= 1219.19), 'Recess runners remain outboard');
        assert.equal(geometry.outerKickerX.length, 2);
        assert.ok(geometry.outerKickerX.every(x => Math.abs(x-1200.15) < .01), 'Original outer kicker attachment positions retained');
      }
      assert.equal(geometry.lowerKicker.length, 4);
      assert.ok(geometry.lowerKicker.every(z => Math.abs(z-60) < .01));
      assert.deepEqual(errors, []);
      console.log(expected.key+': '+expected.meshes+' meshes, '+expected.bolts+' outward bolt stacks, '+expected.knees+' exterior knee pieces, '+expected.rails+' floor rails verified');
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
