// Genuine Three.js check of the compact two-cleat replacement and its ancestry.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {loadEoereCleatTrimScene, validateEoereCleatTrimPatch, EOERE_CLEAT_TRIM_PARENT} from '../site/eoere-cleat-trim-overlay.mjs';
import {loadEoereBottomRailScene} from '../site/eoere-bottom-rail-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const out = process.argv[2];
assert.ok(out, 'supply a new ignored receipt path');
const geometryPath = 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-cleat-trim-v1.json';
const reportBytes = await readFile(path.join(root, geometryPath)), report = JSON.parse(reportBytes);
assert.equal(digest(reportBytes), '4223b78f85418b37832861d8eedc936381188e4e091750bbc8c112646d7f1056');
const patchBytes = await readFile(path.join(site, 'eoere-cleat-trim-scene.json')), patch = JSON.parse(patchBytes);
assert.equal(digest(patchBytes), 'e49ed92875c8de3dfafbab10755fb49175662c0c4a3eaf5affe247da04535c57');
const bundlePath = '.venv/lib/python3.12/site-packages/ocp_vscode/static/js/three-cad-viewer.esm.js';
const bundle = await readFile(path.join(root, bundlePath));
const THREE = await import('data:text/javascript;base64,'+Buffer.concat([bundle,
  Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64'));
assert.equal(typeof THREE.BufferGeometry, 'function');
globalThis.fetch = async url => {
  assert.equal(typeof url, 'string');
  assert.ok(!url.startsWith('/') && !url.includes('..') && !url.includes(':'), 'site-local asset required');
  return new Response(await readFile(path.join(site, url)), {status: 200});
};
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const shared = {baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: value => aliases[value] || value};
const parent = await loadEoereBottomRailScene(THREE, {...shared, url: EOERE_CLEAT_TRIM_PARENT.url,
  expectedSha256: EOERE_CLEAT_TRIM_PARENT.sha256, decodedSha256: EOERE_CLEAT_TRIM_PARENT.decoded_sha256,
  layoutSha256: EOERE_CLEAT_TRIM_PARENT.layout_sha256});
const current = await loadEoereCleatTrimScene(THREE, {...shared, url: 'eoere-cleat-trim-scene.json',
  expectedSha256: digest(patchBytes), layoutSha256: digest(reportBytes)});
assert.equal(current.parts.length, 1021);
assert.equal(new Set(current.parts.map(part => part.name)).size, 1021);
assert.equal(new Set(current.parts.filter(part => part.fabrication.kind === 'bolt')
  .map(part => part.fabrication.connection_name)).size, 100);
assert.equal(current.parts.filter(part => part.fabrication.kind === 'screw').length, 66);
assert.equal(current.meta.analysis_pass_transferred, false);
assert.equal(current.meta.physical_release, false);
assert.equal(current.design.qualified_for_design, false);
const oldParts = new Map(parent.parts.map(part => [part.name, part]));
const changed = new Set(['eoere_cleat_left', 'eoere_cleat_right']);
let unchanged = 0, maxPlaneResidual = -Infinity;
const [[ya, za], [yb, zb]] = report.rear_profile_edge_YZ_mm;
const slope = (zb-za)/(yb-ya), normalScale = Math.sqrt(1+slope*slope);
for (const part of current.parts) {
  const previous = oldParts.get(part.name); assert.ok(previous);
  if (!changed.has(part.name)) {
    assert.deepEqual(part.fabrication, previous.fabrication, part.name);
    if (part.geometry) assert.deepEqual(part.geometry.getAttribute('position').array,
      previous.geometry.getAttribute('position').array, part.name);
    else assert.deepEqual(part, previous, part.name);
    unchanged++;
  } else {
    const positions = part.geometry.getAttribute('position').array;
    assert.notDeepEqual(positions, previous.geometry.getAttribute('position').array);
    for (let i = 0; i < positions.length; i += 3) {
      const residual = (positions[i+2]-za-slope*(positions[i+1]-ya))/normalScale;
      maxPlaneResidual = Math.max(maxPlaneResidual, residual);
      assert.ok(residual <= 0.0877, 'display exceeds source cut beyond its quantization allowance');
    }
  }
}
assert.equal(unchanged, 1019);
const negatives = [
  ['wrong revision', data => {data.revision = 'eoere-bottom-rail-tnut-clearance-v1';}],
  ['wrong parent', data => {data.parent_scene.sha256 = '0'.repeat(64);}],
  ['third changed body', data => {data.solids[0].id = data.solids[0].name = 'base_side_left';}],
  ['transferred mechanics', data => {data.mechanics_ready = true;}],
  ['physical release', data => {data.release.climbing_released = true;}],
  ['wrong complete census', data => {data.counts.physical_bolt_axes = 99;}],
  ['moved replacement', data => {data.solids[0].transform = Array(16).fill(0);}]
];
for (const [name, mutate] of negatives) {
  const data = structuredClone(patch); mutate(data);
  assert.throws(() => validateEoereCleatTrimPatch(data, digest(reportBytes)), undefined, name);
}
const result = {schema: 'eoere_cleat_trim_actual_mesh_check/v1', passed: true,
  visible_parts: 1021, unchanged_actual_parts: unchanged, changed_cleats: 2,
  unchanged_physical_bolt_axes: 100, unchanged_Hillman_screws: 66,
  max_display_cut_plane_residual_mm: maxPlaneResidual, display_quantization_check_limit_mm: 0.0877,
  negative_guards_rejected: negatives.map(([name]) => name),
  source_sha256: Object.fromEntries(await Promise.all([geometryPath, 'site/eoere-cleat-trim-scene.json',
    'site/eoere-cleat-trim-overlay.mjs', 'site/eoere-bottom-rail-overlay.mjs', 'site/eoere-bottom-rail-scene.json.gz',
    'site/wood-joints-overlay.mjs', 'scripts/check_eoere_cleat_trim_scene.mjs', bundlePath,
    'site/hybrid/compact-floor-flush-kerf-right/parts.json', 'site/mesh-aliases.json'].map(async name =>
      [name, digest(await readFile(path.join(root, name)))]))),
  command: process.argv, complete_joint_acceptance: false, physical_release: false};
await writeFile(out, JSON.stringify(result, null, 2)+'\n', {flag: 'wx'});
for (const part of [...parent.parts, ...current.parts]) part.geometry?.dispose();
console.log(JSON.stringify({passed: true, unchanged_parts: unchanged, negative_guards: negatives.length, out}));
