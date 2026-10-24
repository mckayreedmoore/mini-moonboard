import assert from 'node:assert/strict';
import {existsSync, readFileSync} from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import {fileURLToPath} from 'node:url';
import {runInNewContext} from 'node:vm';
import {gunzipSync} from 'node:zlib';

let root = path.dirname(fileURLToPath(import.meta.url));
while (!existsSync(path.join(root, 'site/eoere-v10-overlay.mjs'))) {
  const parent = path.dirname(root);
  assert.notEqual(parent, root, 'V10 repository root missing');
  root = parent;
}
const html = readFileSync(path.join(root, 'site/index.html'), 'utf8');
const scene = JSON.parse(gunzipSync(readFileSync(path.join(root, 'site/eoere-v10-scene-13.json.gz'))));

// Execute the real selector helper and its real menu-building call site.
function optionsFor(model, parts) {
  const helperStart = html.indexOf('function representativeBolts(');
  const helperEnd = html.indexOf('const manifestKey', helperStart);
  const menuStart = html.indexOf('for (const {name, label} of representativeBolts(displayParts');
  const menuEnd = html.indexOf('boltLabel.hidden', menuStart);
  assert.ok(helperStart >= 0 && helperEnd > helperStart && menuStart >= 0 && menuEnd > menuStart);
  const options = [];
  class Option {constructor(label, value) {this.label = label; this.value = value;}}
  runInNewContext(html.slice(helperStart, helperEnd) + html.slice(menuStart, menuEnd), {
    model, displayParts: parts, Option, boltSelect: {add(option) {options.push(option);}},
  });
  return options;
}

const roles = ['head', 'head_washer', 'nut', 'nut_washer', 'shaft'];
const dimensions = {head: [9, 22.225, 25.663], head_washer: [3.175, 34.925, 34.925],
  nut: [11.532, 22.225, 25.663], nut_washer: [3.175, 34.925, 34.925], shaft: [215.9, 12.7, 12.7]};
function stack(axis, stackRoles = roles) {
  return stackRoles.map(role => ({name: axis+'_'+role, fabrication: {
    kind: 'bolt', connection_name: axis, hardware_role: role, stack_roles: stackRoles,
    dimensions_mm: [...(dimensions[role] || [25.4, 19.05, 19.05])],
  }}));
}
const matchingLegs = ['left', 'right'].flatMap(side => [1, 2].flatMap(number =>
  stack(`lumber_leg_bolt_${side}_${number}`)));

for (const model of ['eoere-owner-frame-v10-development', 'eoere-current-frame-development']) {
  test(model+' retains both individually selectable leg bolts on each side', () => {
    assert.deepEqual(optionsFor(model, matchingLegs).map(row => row.value).sort(), [
      'lumber_leg_bolt_left_1', 'lumber_leg_bolt_left_2',
      'lumber_leg_bolt_right_1', 'lumber_leg_bolt_right_2',
    ]);
  });
  test(model+' exposes every complete declared Candidate 13 stack', () => {
    const parts = scene.stack_updates.flatMap(selection => stack(selection.axis_id, selection.stack_roles));
    const actual = optionsFor(model, parts).map(row => row.value).sort();
    assert.equal(actual.length, 116);
    assert.deepEqual(actual, scene.stack_updates.map(row => row.axis_id).sort());
  });
}
test('historical menus retain one example only while every role dimension matches', () => {
  const grouped = optionsFor('eoere-owner-frame-v9-development', matchingLegs);
  assert.deepEqual(grouped.map(row => row.value), ['lumber_leg_bolt_left_1', 'lumber_leg_bolt_right_1']);
  assert.ok(grouped.every(row => row.label.endsWith('joint · example')));
  const changed = structuredClone(matchingLegs);
  changed.find(row => row.name === 'lumber_leg_bolt_left_2_nut_washer').fabrication.dimensions_mm[0] += 1;
  assert.deepEqual(optionsFor('eoere-owner-frame-v9-development', changed).map(row => row.value), [
    'lumber_leg_bolt_left_1', 'lumber_leg_bolt_left_2', 'lumber_leg_bolt_right_1',
  ]);
});
test('individual current menu still excludes an incomplete declared stack', () => {
  const incomplete = matchingLegs.filter(row => row.name !== 'lumber_leg_bolt_left_2_nut');
  assert.deepEqual(optionsFor('eoere-owner-frame-v10-development', incomplete).map(row => row.value).sort(), [
    'lumber_leg_bolt_left_1', 'lumber_leg_bolt_right_1', 'lumber_leg_bolt_right_2',
  ]);
});
