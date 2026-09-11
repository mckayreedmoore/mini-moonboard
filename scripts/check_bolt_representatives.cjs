// Lightweight regression for the viewer's representative-connection menu.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('site/index.html', 'utf8');
const start = source.indexOf('      function representativeBolts(');
const end = source.indexOf('      const manifest = model', start);
assert.ok(start >= 0 && end > start);
const group = vm.runInNewContext(source.slice(start, end) + ';representativeBolts');
const parts = JSON.parse(fs.readFileSync('site/hybrid/horizontal-service-development/parts.json')).parts;
assert.deepEqual(Array.from(group(parts), row => row.name), ['lumber_leg_bolt_left_1', 'lumber_leg_bolt_right_1']);
const changed = structuredClone(parts);
changed.find(part => part.fabrication.connection_name === 'lumber_leg_bolt_left_2' &&
  part.fabrication.hardware_role === 'shaft').fabrication.dimensions_mm[0] += 10;
const rows = group(changed);
assert.equal(rows.length, 3);
assert.equal(new Set(rows.map(row => row.label)).size, 3);
assert.equal(group(parts.filter(part => part.fabrication.hardware_role !== 'nut')).length, 0);
console.log('Representative grouping passed: mirrored locations, distinct stacks and complete hardware.');
