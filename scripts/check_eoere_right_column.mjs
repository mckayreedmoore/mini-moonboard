// Check the assembled Three.js scene against its unchanged parent and CAD receipt.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {loadKickerClearance2026Scene} from '../site/eoere-kicker-clearance-overlay.mjs';
import {loadRightColumnScene, validateRightColumn} from '../site/eoere-right-column-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const output = process.argv[2]; assert.ok(output, 'fresh output path required');
const assetPath = 'site/eoere-right-column-scene.json.gz';
const asset = await readFile(path.join(root, assetPath)), decoded = gunzipSync(asset), patch = JSON.parse(decoded);
const layoutBytes = await readFile(path.join(root, patch.layout_report.path)), layout = JSON.parse(layoutBytes);
assert.equal(sha(layoutBytes), patch.layout_report.sha256);
const parentBytes = await readFile(path.join(root, layout.parent_geometry.path)), original = JSON.parse(parentBytes);
assert.equal(sha(parentBytes), layout.parent_geometry.sha256);
assert.deepEqual(layout.axes, original.axes); assert.equal(layout.axes.length, 100);
assert.deepEqual(layout.screw_axes, original.screw_axes); assert.equal(layout.screw_axes.length, 66);
assert.equal(layout.clearance.passed, true); assert.deepEqual(layout.clearance.collisions, []);
assert.equal(layout.clearance.known_answer_fixtures, 2);
assert.equal(layout.unchanged_timber_count, 19);
assert.equal(layout.service_cuts.length, 3);
assert.equal(layout.panel_bores.reduce((sum, row) => sum + row.holes.tnut, 0), 12);
assert.equal(layout.panel_bores.reduce((sum, row) => sum + row.holes.LED, 0), 12);
for (const row of layout.panel_bores) {
  assert.ok(Math.abs(row.removed_volume_mm3 - row.expected_removed_volume_mm3) < 0.01);
  assert.equal(row.bounds_unchanged, true);
}
assert.ok(Math.abs(layout.right_4x6_gaps_mm.tnut_flange - 33.625) < 1e-5);
assert.ok(layout.right_4x6_gaps_mm.cable > 14);
assert.equal(layout.routes.length, 12);
for (const row of layout.routes) assert.ok(row.rounded_length_mm <= 304.8);
for (const row of [...patch.replacements, ...patch.additions.filter(row => row.mesh)]) {
  const source = layout.changed_finished_solids.find(value => value.id === row.name);
  const bytes = await readFile(path.join(root, source.path));
  assert.equal(bytes.length, source.bytes); assert.equal(sha(bytes), source.sha256);
  assert.equal(row.source_brep_sha256, source.sha256);
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
const binding = patch.parent_scene;
const parent = await loadKickerClearance2026Scene(THREE, {...options, url: binding.url, expectedSha256: binding.sha256,
  decodedSha256: binding.decoded_sha256, layoutSha256: binding.layout_sha256});
const proposedOptions = {...options, url: path.basename(assetPath), expectedSha256: sha(asset),
  decodedSha256: sha(decoded), layoutSha256: sha(layoutBytes)};
const current = await loadRightColumnScene(THREE, proposedOptions);
assert.equal(parent.parts.length, 1380); assert.equal(current.parts.length, 1416);
const byName = new Map(current.parts.map(row => [row.name, row])); assert.equal(byName.size, 1416);
const changed = new Set(patch.replacements.map(row => row.name));
let unchanged = 0;
for (const old of parent.parts) {
  const now = byName.get(old.name); assert.ok(now, old.name);
  const before = old.geometry?.getAttribute('position').array, after = now.geometry?.getAttribute('position').array;
  if (changed.has(old.name)) {
    assert.notDeepEqual(after, before, old.name);
    assert.equal(now.fabrication.right_column_revision, layout.revision);
    old.geometry.computeBoundingBox(); now.geometry.computeBoundingBox();
    const margin = patch.replacements.find(row => row.name === old.name).mesh.vertex_quantization_mm + 0.0002;
    for (const key of ['min', 'max']) for (const axis of ['x', 'y', 'z'])
      assert.ok(Math.abs(now.geometry.boundingBox[key][axis] - old.geometry.boundingBox[key][axis]) < margin,
        `${old.name}:${key}:${axis}`);
  } else {
    assert.deepEqual(now.fabrication, old.fabrication, old.name);
    if (before) assert.deepEqual(after, before, old.name);
    else assert.deepEqual(now, old, old.name);
    unchanged++;
  }
}
assert.equal(unchanged, 1375);
for (const [kind, expected] of [['timber', 22], ['panel', 6], ['bracket', 22], ['bolt', 500], ['screw', 66],
  ['light', 264], ['tnut', 274], ['wire', 262]])
  assert.equal(current.parts.filter(row => row.fabrication.kind === kind).length, expected, kind);
assert.equal(new Set(current.parts.filter(row => row.fabrication.kind === 'bolt').map(row => row.fabrication.connection_name)).size, 100);
const normal = [0, -Math.cos(40 * Math.PI / 180), Math.sin(40 * Math.PI / 180)];
const along = [0, Math.sin(40 * Math.PI / 180), Math.cos(40 * Math.PI / 180)];
const origin = [0, -18 * (1 + Math.cos(40 * Math.PI / 180)), 277 + 18 * Math.sin(40 * Math.PI / 180)];
for (const row of patch.additions.filter(row => row.template_id)) {
  // Independently check the instance frame against panel X/S/N coordinates.
  const grid = layout.grid.find(site => site.id === row.fabrication.grid_position);
  const kind = row.fabrication.kind, [x, s] = kind === 'tnut' ? grid.tnut_x_s_mm : grid.LED_x_s_mm;
  const n = kind === 'tnut' ? 0 : -18.25625;
  assert.ok(Math.abs(row.transform[12] - (x - 1219.2)) < 1e-8);
  // Frame origin retains the historical 18-mm support-face offset at the
  // 277-mm climbing-face/kicker seam; finished panel thickness is 18.25625.
  assert.ok(Math.abs(row.transform[13] - (origin[1] + s * along[1] + n * normal[1])) < 1e-8);
  assert.ok(Math.abs(row.transform[14] - (origin[2] + s * along[2] + n * normal[2])) < 1e-8);
}
assert.equal(current.meta.analysis_pass_transferred, false); assert.equal(current.meta.physical_release, false);
assert.equal(current.design.qualified_for_design, false); assert.equal(current.meta.main_face_positions, 264);
for (const part of [...parent.parts, ...current.parts]) part.geometry?.dispose();
const controls = [
  ['response transfer', p => {p.analysis_pass_transferred = true;}],
  ['release', p => {p.release.fabrication_released = true;}],
  ['missing rail', p => {p.replacements.pop();}],
  ['duplicate addition', p => {p.additions[1] = p.additions[0];}],
  ['wrong column', p => {p.grid[0].tnut_x_s_mm[0] = 2400;}],
  ['missing LED', p => {p.additions.splice(12, 1);}],
  ['bolt count', p => {p.counts.physical_bolt_axes = 99;}],
  ['parent binding', p => {p.parent_scene.sha256 = '0'.repeat(64);}],
];
for (const [label, change] of controls) {
  const control = structuredClone(patch); change(control);
  assert.throws(() => validateRightColumn(control, sha(layoutBytes)), undefined, label);
}
for (const key of ['expectedSha256', 'decodedSha256', 'layoutSha256'])
  await assert.rejects(() => loadRightColumnScene(THREE, {...proposedOptions, [key]: '0'.repeat(64)}));
const sourcePaths = [assetPath, patch.layout_report.path, layout.parent_geometry.path,
  'site/eoere-right-column-overlay.mjs', 'scripts/check_eoere_right_column.mjs', bundlePath];
const result = {schema: 'eoere_right_column_actual_mesh_check/v1', passed: true, count: 1416,
  unchanged: 1375, replaced: 5, added: 36, main_positions: 264, kicker_positions: 10,
  unchanged_bolt_axes: 100, unchanged_screw_axes: 66, full_source_records_checked: true,
  rejected_controls: controls.map(([label]) => label), rejected_hash_options: 3,
  source_sha256: Object.fromEntries(await Promise.all(sourcePaths.map(async name => [name, sha(await readFile(path.join(root, name)))]))),
  mechanics_or_physical_release: false};
await writeFile(output, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({passed: true, count: 1416, unchanged, output}));
