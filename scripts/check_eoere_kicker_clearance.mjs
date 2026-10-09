// Verify the assembled Three.js geometry and complete 100/66 source records.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {loadUniformChannelBaseScene, loadUniformChannel2026Scene} from '../site/eoere-uniform-channels-overlay.mjs';
import {loadKickerClearanceBaseScene, loadKickerClearance2026Scene, validateKickerClearance} from '../site/eoere-kicker-clearance-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const output = process.argv[2]; assert.ok(output, 'fresh output path required');
const assetPath = 'site/eoere-kicker-clearance-scene.json.gz';
const asset = await readFile(path.join(root, assetPath)), decoded = gunzipSync(asset), patch = JSON.parse(decoded);
const layoutBytes = await readFile(path.join(root, patch.layout_report.path)), layout = JSON.parse(layoutBytes);
assert.equal(sha(layoutBytes), patch.layout_report.sha256);
const parentBytes = await readFile(path.join(root, layout.parent_geometry.path)), original = JSON.parse(parentBytes);
assert.equal(sha(parentBytes), layout.parent_geometry.sha256);
assert.deepEqual(layout.axes, original.axes); assert.equal(layout.axes.length, 100);
assert.equal(layout.screw_axes.length, 66); assert.equal(layout.moved_screw_axes.length, 2);
const moved = new Set(['round_kicker_left_rim_2', 'round_kicker_right_rim_2']);
let movedCount = 0;
for (let i = 0; i < original.screw_axes.length; i++) {
  const old = original.screw_axes[i], now = layout.screw_axes[i];
  const expected = moved.has(old.axis_id) ? {...old, origin_xyz_mm: [...old.origin_xyz_mm.slice(0, 2), 212]} : old;
  assert.deepEqual(now, expected, old.axis_id);
  movedCount += moved.has(old.axis_id);
}
assert.equal(movedCount, 2);
assert.ok(Math.abs(layout.maximum_bore_clearance.capsule_separation_lower_bound_mm - 3.94375) < 1e-9);
assert.equal(layout.known_answer_fixtures, 4);
for (const row of layout.screw_support) {
  assert.ok(row.modeled_body_backing_fraction > 0.999999);
  assert.ok(Math.abs(row.post_top_axis_distance_mm - 26.9) < 1e-8);
  assert.ok(Math.abs(row.panel_top_axis_distance_mm - 65) < 1e-8);
  assert.equal(row.actual, null); assert.equal(row.edge_distance_strength_qualification, false);
}
for (const row of patch.replacements) {
  const source = layout.changed_finished_solids.find(value => value.id === row.name);
  const bytes = await readFile(path.join(root, source.path));
  assert.equal(bytes.length, source.bytes); assert.equal(sha(bytes), source.sha256);
  assert.deepEqual(row.mesh.bounds_xyz_mm, source.bounds_xyz_mm);
}
const bundlePath = '.venv/lib/python3.12/site-packages/ocp_vscode/static/js/three-cad-viewer.esm.js';
const bundle = await readFile(path.join(root, bundlePath));
const THREE = await import('data:text/javascript;base64,' + Buffer.concat([bundle,
  Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64'));
const nativeFetch = globalThis.fetch;
globalThis.fetch = async url => {
  if (typeof url === 'string' && url.startsWith('blob:')) return nativeFetch(url);
  assert.equal(typeof url, 'string');
  assert.ok(!url.startsWith('/') && !url.includes('..') && !url.includes(':'), 'site-local asset expected');
  return new Response(await readFile(path.join(site, url)), {status: 200});
};
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const options = {baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: value => aliases[value] || value};
const proposedOptions = {...options, url: path.basename(assetPath), expectedSha256: sha(asset),
  decodedSha256: sha(decoded), layoutSha256: sha(layoutBytes)};
const variants = [];
for (const [variant, parentLoader, newLoader] of [
  ['base', loadUniformChannelBaseScene, loadKickerClearanceBaseScene],
  ['extra', loadUniformChannel2026Scene, loadKickerClearance2026Scene]]) {
  const binding = patch.parent_scene;
  const parent = await parentLoader(THREE, {...options, url: binding.url, expectedSha256: binding.sha256,
    decodedSha256: binding.decoded_sha256, layoutSha256: binding.layout_sha256});
  const current = await newLoader(THREE, proposedOptions), count = variant === 'base' ? 1021 : 1380;
  const byName = new Map(current.parts.map(row => [row.name, row]));
  assert.equal(parent.parts.length, count); assert.equal(current.parts.length, count); assert.equal(byName.size, count);
  const changed = new Set(patch.replacements.map(row => row.name));
  let unchanged = 0;
  for (const old of parent.parts) {
    const now = byName.get(old.name); assert.ok(now, old.name);
    const before = old.geometry?.getAttribute('position').array, after = now.geometry?.getAttribute('position').array;
    if (changed.has(old.name)) {
      assert.notDeepEqual(after, before, old.name);
      assert.equal(now.fabrication.kicker_clearance_revision, layout.revision);
      old.geometry.computeBoundingBox(); now.geometry.computeBoundingBox();
      // Native STL parents and 0.1-mm quantized patches have different display
      // precision. Exact CAD bounds are checked against the saved BREP records.
      const margin = patch.replacements.find(row => row.name === old.name).mesh.vertex_quantization_mm + 0.0002;
      for (const key of ['min', 'max']) for (const axis of ['x', 'y', 'z']) {
        const delta = old.fabrication.kind === 'screw' && axis === 'z' ? 20 : 0;
        assert.ok(Math.abs(now.geometry.boundingBox[key][axis] - old.geometry.boundingBox[key][axis] - delta) < margin,
          `${old.name}:${key}:${axis}: ${old.geometry.boundingBox[key][axis]} -> ${now.geometry.boundingBox[key][axis]}`);
      }
    } else {
      assert.deepEqual(now.fabrication, old.fabrication, old.name);
      if (before) assert.deepEqual(after, before, old.name);
      else assert.deepEqual(now, old, old.name);
      unchanged++;
    }
  }
  assert.equal(unchanged, count - 4);
  for (const [kind, expected] of [['timber', 22], ['panel', 6], ['bracket', 22], ['bolt', 500], ['screw', 66],
    ['light', variant === 'base' ? 132 : 252], ['tnut', variant === 'base' ? 142 : 262], ['wire', variant === 'base' ? 131 : 250]])
    assert.equal(current.parts.filter(row => row.fabrication.kind === kind).length, expected, kind);
  assert.equal(new Set(current.parts.filter(row => row.fabrication.kind === 'bolt').map(row => row.fabrication.connection_name)).size, 100);
  assert.equal(current.meta.analysis_pass_transferred, false); assert.equal(current.meta.physical_release, false);
  assert.equal(current.design.qualified_for_design, false);
  variants.push({variant, count, unchanged, changed: 4, bolts: 100, screws: 66});
  for (const part of [...parent.parts, ...current.parts]) part.geometry?.dispose();
}
const controls = [
  ['response transfer', p => {p.analysis_pass_transferred = true;}],
  ['release', p => {p.release.physical_release = true;}],
  ['missing panel', p => {p.replacements.pop();}],
  ['duplicate replacement', p => {p.replacements[1] = p.replacements[0];}],
  ['screw count', p => {p.counts.base.screw = 67;}],
  ['bolt count', p => {p.counts.extra.physical_bolt_axes = 99;}],
  ['wrong height', p => {p.moved_screw_axes[0].new_origin_xyz_mm[2] = 211;}],
  ['horizontal move', p => {p.moved_screw_axes[0].new_origin_xyz_mm[0] += 1;}],
];
for (const [label, change] of controls) {
  const control = structuredClone(patch); change(control);
  assert.throws(() => validateKickerClearance(control, sha(layoutBytes)), undefined, label);
}
for (const key of ['expectedSha256', 'decodedSha256', 'layoutSha256'])
  await assert.rejects(() => loadKickerClearanceBaseScene(THREE, {...proposedOptions, [key]: '0'.repeat(64)}));
const sourcePaths = [assetPath, patch.layout_report.path, layout.parent_geometry.path,
  'site/eoere-kicker-clearance-overlay.mjs', 'scripts/check_eoere_kicker_clearance.mjs', bundlePath];
const result = {schema: 'eoere_kicker_screw_clearance_actual_mesh_check/v1', passed: true, variants,
  moved_screw_axes: [...moved], unchanged_bolt_axes: 100, full_source_records_checked: true,
  rejected_controls: controls.map(([label]) => label), rejected_hash_options: 3,
  source_sha256: Object.fromEntries(await Promise.all(sourcePaths.map(async name => [name, sha(await readFile(path.join(root, name)))]))),
  mechanics_or_physical_release: false};
await writeFile(output, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({passed: true, variants, output}));
