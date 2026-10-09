// Check real composed meshes against the frozen source bodies and preserved models.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {loadExtendedCleatBaseScene, loadExtendedCleat2026Scene} from '../site/eoere-cleat-extension-overlay.mjs';
import {loadUniformChannelBaseScene, loadUniformChannel2026Scene, validateUniformChannels} from '../site/eoere-uniform-channels-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const output = process.argv[2]; assert.ok(output, 'fresh output path required');
const assetPath = 'site/eoere-uniform-channels-scene.json.gz';
const encoded = await readFile(path.join(root, assetPath)), decoded = gunzipSync(encoded), patch = JSON.parse(decoded);
const layoutBytes = await readFile(path.join(root, patch.layout_report.path)), layout = JSON.parse(layoutBytes);
assert.equal(sha(layoutBytes), patch.layout_report.sha256);
const originalBytes = await readFile(path.join(root, layout.parent_geometry.path)), original = JSON.parse(originalBytes);
assert.equal(sha(originalBytes), layout.parent_geometry.sha256);
assert.deepEqual(layout.axes, original.axes); assert.deepEqual(layout.screw_axes, original.screw_axes);
assert.equal(layout.axes.length, 100); assert.equal(layout.screw_axes.length, 66);
assert.equal(layout.principal_arc_cuts.removed_F_column_arc_cut_links.length, 11);
assert.ok(layout.principal_arc_cuts.base_restored_volume_mm3 > 90000);
assert.equal(layout.principal_arc_cuts.existing_base_channel_retained, true);
assert.equal(layout.flexible_routes.length, 140);
for (const row of layout.flexible_routes) {
  assert.equal(row.endpoints_retained, true);
  assert.deepEqual([row.route_local_mm[0], row.route_local_mm.at(-1)], row.source_LED_endpoints_local_mm);
  assert.ok(row.rounded_length_mm <= row.approximate_budget_mm);
  assert.equal(row.machining_route_local_mm.length, 2);
  assert.ok(row.machining_route_local_mm.every(point => point[2] === 8));
  if (row.family === 'original_F_column') assert.equal(row.route_local_mm.length, 2);
}
for (const hits of Object.values(layout.collisions)) assert.deepEqual(hits, []);
assert.ok(layout.service_cuts.every(row => row.receiver !== 'base_header'));
for (const [name, digest] of Object.entries(layout.source_sha256))
  assert.equal(sha(await readFile(path.resolve(root, name))), digest, name);
const bodySources = new Map(layout.changed_finished_solids.map(row => [`${row.variant}:${row.id}`, row]));
for (const variant of ['common', 'base', 'extra']) for (const row of patch[`${variant}_replacements`]) {
  const source = bodySources.get(`${variant}:${row.name}`); assert.ok(source, row.name);
  const bytes = await readFile(path.resolve(root, source.path));
  assert.equal(bytes.length, source.bytes); assert.equal(sha(bytes), source.sha256);
  assert.equal(row.source_brep_sha256, source.sha256); assert.deepEqual(row.mesh.bounds_xyz_mm, source.bounds_xyz_mm);
}
const bundlePath = '.venv/lib/python3.12/site-packages/ocp_vscode/static/js/three-cad-viewer.esm.js';
const bundle = await readFile(path.join(root, bundlePath));
const THREE = await import('data:text/javascript;base64,' + Buffer.concat([bundle,
  Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64'));
const nativeFetch = globalThis.fetch;
globalThis.fetch = async url => {
  if (typeof url === 'string' && url.startsWith('blob:')) return nativeFetch(url);
  assert.equal(typeof url, 'string'); assert.ok(!url.startsWith('/') && !url.includes('..') && !url.includes(':'));
  return new Response(await readFile(path.join(site, url)), {status: 200});
};
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const options = {baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: value => aliases[value] || value};
const newOptions = {...options, url: path.basename(assetPath), expectedSha256: sha(encoded), decodedSha256: sha(decoded), layoutSha256: sha(layoutBytes)};
const results = [];
for (const [variant, oldLoader, newLoader, total, changed] of [
  ['base', loadExtendedCleatBaseScene, loadUniformChannelBaseScene, 1021, 12],
  ['extra', loadExtendedCleat2026Scene, loadUniformChannel2026Scene, 1380, 149]]) {
  const parent = await oldLoader(THREE, {...options, url: patch.parent_scene.url, expectedSha256: patch.parent_scene.sha256,
    decodedSha256: patch.parent_scene.decoded_sha256, layoutSha256: patch.parent_scene.layout_sha256});
  const current = await newLoader(THREE, newOptions);
  assert.equal(current.parts.length, total); assert.equal(parent.parts.length, total);
  const byName = new Map(current.parts.map(row => [row.name, row])); assert.equal(byName.size, total);
  const replacements = new Set([...patch.common_replacements, ...patch[`${variant}_replacements`]].map(row => row.name));
  let unchanged = 0;
  for (const old of parent.parts) {
    const now = byName.get(old.name); assert.ok(now, old.name);
    const before = old.geometry?.getAttribute('position').array, after = now.geometry?.getAttribute('position').array;
    if (replacements.has(old.name)) {
      assert.equal(now.fabrication.uniform_channel_revision, layout.revision);
      assert.ok(after.length > 0); assert.notDeepEqual(after, before, old.name);
    } else {
      assert.deepEqual(now.fabrication, old.fabrication, old.name);
      if (before) assert.deepEqual(after, before, old.name); else assert.deepEqual(now, old, old.name);
      unchanged++;
    }
  }
  assert.equal(unchanged, total - changed); assert.equal(current.meta.changed_visible_parts, changed);
  for (const [kind, count] of [['timber', 22], ['panel', 6], ['bracket', 22], ['bolt', 500], ['screw', 66],
    ['light', variant === 'base' ? 132 : 252], ['tnut', variant === 'base' ? 142 : 262], ['wire', variant === 'base' ? 131 : 250]])
    assert.equal(current.parts.filter(row => row.fabrication.kind === kind).length, count, kind);
  assert.equal(current.meta.analysis_pass_transferred, false); assert.equal(current.meta.physical_release, false);
  assert.equal(current.design.qualified_for_design, false);
  results.push({variant, total, changed, unchanged});
  for (const part of [...parent.parts, ...current.parts]) part.geometry?.dispose();
}
const controls = [
  ['release', p => {p.release.fabrication_released = true;}],
  ['response transfer', p => {p.analysis_pass_transferred = true;}],
  ['official grid', p => {p.optional_grid_unofficial = false;}],
  ['larger depth', p => {p.smaller_profile.rear_depth_mm = 20.35;}],
  ['missing F link', p => {p.common_replacements.pop();}],
  ['duplicate replacement', p => {p.extra_replacements[1] = p.extra_replacements[0];}],
  ['moved screw count', p => {p.counts.base.screw = 65;}],
  ['parent hash', p => {p.parent_scene.sha256 = '0'.repeat(64);}],
];
for (const [label, change] of controls) {
  const control = structuredClone(patch); change(control);
  assert.throws(() => validateUniformChannels(control, sha(layoutBytes)), undefined, label);
}
for (const key of ['expectedSha256', 'decodedSha256', 'layoutSha256'])
  await assert.rejects(() => loadUniformChannelBaseScene(THREE, {...newOptions, [key]: '0'.repeat(64)}));
const sourcePaths = [assetPath, patch.layout_report.path, 'site/index.html', 'site/eoere-uniform-channels-overlay.mjs',
  'scripts/check_eoere_uniform_channels.mjs', bundlePath];
const result = {schema: 'eoere_uniform_channels_actual_mesh_check/v1', passed: true, results,
  rejected_controls: controls.map(([label]) => label), rejected_hash_options: 3,
  unchanged_axes: 100, unchanged_screws: 66, source_bindings_verified: Object.keys(layout.source_sha256).length,
  source_sha256: Object.fromEntries(await Promise.all(sourcePaths.map(async name => [name, sha(await readFile(path.join(root, name)))]))),
  mechanics_or_physical_release: false};
await writeFile(output, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({passed: true, results, output}));
