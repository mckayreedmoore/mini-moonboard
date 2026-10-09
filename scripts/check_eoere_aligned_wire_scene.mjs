// Actual Three.js geometry and ancestry checks, using existing viewer helpers.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {loadEoereAlignedWireScene, validateEoereAlignedWirePatch, EOERE_ALIGNED_WIRE_PARENT,
  EOERE_ALIGNED_RAIL_IDS, EOERE_ALIGNED_WIRE_IDS} from '../site/eoere-aligned-wire-overlay.mjs';
import {loadEoereCleatTrimScene} from '../site/eoere-cleat-trim-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const out = process.argv[2]; assert.ok(out, 'new ignored output path required');
const reportPath = 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-aligned-wire-v1.json';
const patchPath = 'site/eoere-aligned-wire-scene.json';
const reportBytes = await readFile(path.join(root, reportPath)), report = JSON.parse(reportBytes);
const patchBytes = await readFile(path.join(root, patchPath)), patch = JSON.parse(patchBytes);
assert.equal(patch.layout_report.sha256, sha(reportBytes));
assert.equal(report.changed_rails, 6); assert.equal(report.changed_wire_links, 30);
assert.equal(report.principal_move_adopted, false); assert.equal(report.mechanics_ready, false);
const bundlePath = '.venv/lib/python3.12/site-packages/ocp_vscode/static/js/three-cad-viewer.esm.js';
const bundle = await readFile(path.join(root, bundlePath));
const THREE = await import('data:text/javascript;base64,'+Buffer.concat([bundle,
  Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64'));
assert.equal(typeof THREE.BufferGeometry, 'function');
globalThis.fetch = async url => {
  assert.equal(typeof url, 'string');
  assert.ok(!url.startsWith('/') && !url.includes('..') && !url.includes(':'), 'site-local assets only');
  return new Response(await readFile(path.join(site, url)), {status: 200});
};
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const options = {baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: value => aliases[value] || value};
const parent = await loadEoereCleatTrimScene(THREE, {...options, url: EOERE_ALIGNED_WIRE_PARENT.url,
  expectedSha256: EOERE_ALIGNED_WIRE_PARENT.sha256, layoutSha256: EOERE_ALIGNED_WIRE_PARENT.layout_sha256});
const current = await loadEoereAlignedWireScene(THREE, {...options, url: 'eoere-aligned-wire-scene.json',
  expectedSha256: sha(patchBytes), layoutSha256: sha(reportBytes)});
assert.equal(current.parts.length, 1021); assert.equal(new Set(current.parts.map(p => p.name)).size, 1021);
assert.equal(new Set(current.parts.filter(p => p.fabrication.kind === 'bolt').map(p => p.fabrication.connection_name)).size, 100);
assert.equal(current.parts.filter(p => p.fabrication.kind === 'screw').length, 66);
assert.equal(current.parts.filter(p => p.fabrication.kind === 'wire').length, 131);
assert.equal(current.parts.filter(p => p.fabrication.kind === 'light').length, 132);
assert.equal(current.design.qualified_for_design, false); assert.equal(current.meta.analysis_pass_transferred, false);
const old = new Map(parent.parts.map(p => [p.name, p]));
const changed = new Set([...EOERE_ALIGNED_RAIL_IDS, ...EOERE_ALIGNED_WIRE_IDS]);
let unchanged = 0;
for (const part of current.parts) {
  const previous = old.get(part.name); assert.ok(previous);
  if (!changed.has(part.name)) {
    assert.deepEqual(part.fabrication, previous.fabrication, part.name);
    if (part.geometry) assert.deepEqual(part.geometry.getAttribute('position').array,
      previous.geometry.getAttribute('position').array, part.name);
    else assert.deepEqual(part, previous, part.name);
    unchanged++;
  } else {
    assert.ok(part.geometry); assert.equal(part.path, undefined);
    if (previous.geometry) assert.notDeepEqual(part.geometry.getAttribute('position').array,
      previous.geometry.getAttribute('position').array, part.name);
    const positions = part.geometry.getAttribute('position').array;
    assert.ok(positions.length > 0 && positions.every(Number.isFinite), part.name);
  }
}
assert.equal(unchanged, 985);
const controls = [
  ['old revision', p => {p.revision = 'eoere-rear-trimmed-cleats-v1';}],
  ['wrong parent', p => {p.parent_scene.sha256 = '0'.repeat(64);}],
  ['moved principal', p => {p.changed_rail_ids[0] = 'base_principal_center_right';}],
  ['connector replacement', p => {p.changed_wire_ids[0] = 'wire_050_E2_E3';}],
  ['moved transform', p => {p.solids[0].transform = Array(16).fill(0);}],
  ['wrong inventory', p => {p.counts.physical_bolt_axes = 99;}],
  ['mechanics transfer', p => {p.mechanics_ready = true;}],
  ['physical release', p => {p.release.climbing_released = true;}],
  ['wrong layout', p => {p.layout_report.sha256 = '0'.repeat(64);}]
];
for (const [label, mutate] of controls) {
  const copy = structuredClone(patch); mutate(copy);
  assert.throws(() => validateEoereAlignedWirePatch(copy, sha(reportBytes)), undefined, label);
}
const inputs = [reportPath, patchPath, 'site/eoere-aligned-wire-overlay.mjs', 'site/eoere-cleat-trim-overlay.mjs',
  'site/eoere-cleat-trim-scene.json', 'site/eoere-bottom-rail-overlay.mjs', 'site/eoere-bottom-rail-scene.json.gz',
  'site/wood-joints-overlay.mjs', 'scripts/check_eoere_aligned_wire_scene.mjs', bundlePath,
  'site/hybrid/compact-floor-flush-kerf-right/parts.json', 'site/mesh-aliases.json'];
const result = {schema: 'eoere_aligned_wire_actual_mesh_check/v1', passed: true,
  visible_parts: 1021, unchanged_actual_parts: unchanged, changed_rails: 6, changed_wire_links: 30,
  unchanged_physical_bolt_axes: 100, unchanged_Hillman_screws: 66, retained_LED_endpoints: 132, retained_wire_links: 131,
  negative_guards_rejected: controls.map(([label]) => label),
  source_sha256: Object.fromEntries(await Promise.all(inputs.map(async name => [name, sha(await readFile(path.join(root, name)))]))),
  command: process.argv, complete_joint_acceptance: false, physical_release: false};
await writeFile(out, JSON.stringify(result, null, 2)+'\n', {flag: 'wx'});
for (const part of [...parent.parts, ...current.parts]) part.geometry?.dispose();
console.log(JSON.stringify({passed: true, unchanged_parts: unchanged, negative_guards: controls.length, out}));
