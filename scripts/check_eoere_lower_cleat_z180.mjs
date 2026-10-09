// Actual Three.js composition and source-descriptor checks; no CAD regeneration.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {loadExtendedCleatBaseScene} from '../site/eoere-cleat-extension-overlay.mjs';
import {loadLowerCleatPreviewScene, validateLowerCleatPreview} from '../site/eoere-lower-cleat-z180-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const output = process.argv[2]; assert.ok(output, 'fresh output path required');
const assetPath = 'site/eoere-lower-cleat-z180-scene.json.gz';
const asset = await readFile(path.join(root, assetPath)), decoded = gunzipSync(asset), patch = JSON.parse(decoded);
const layoutBytes = await readFile(path.join(root, patch.layout_report.path)), layout = JSON.parse(layoutBytes);
assert.equal(sha(layoutBytes), patch.layout_report.sha256);
const originalBytes = await readFile(path.join(root, layout.parent_geometry.path)), original = JSON.parse(originalBytes);
assert.equal(sha(originalBytes), layout.parent_geometry.sha256);
const placementBytes = await readFile(path.join(root, layout.placement.path)), placement = JSON.parse(placementBytes);
assert.equal(sha(placementBytes), layout.placement.sha256);
assert.deepEqual(layout.proposed_axes, placement.proposed_axes);
assert.equal(original.axes.length, 100); assert.equal(original.screw_axes.length, 66);
const movedAxes = new Map(layout.proposed_axes.map(row => [row.id, row]));
assert.equal(movedAxes.size, 4);
const reconstructed = original.axes.map(row => movedAxes.get(row.id) || row);
// Python's frozen canonical form distinguishes 200.0 from 200; JavaScript does
// not. Check the pinned digest declarations and the complete semantic records.
assert.equal(layout.proposed_100_axes_canonical_sha256, placement.proposed_100_axes_canonical_sha256);
assert.equal(layout.current_100_axes_canonical_sha256, placement.current_100_axes_canonical_sha256);
assert.equal(layout.unchanged_66_screws_canonical_sha256, placement.current_66_screws_canonical_sha256);
for (let i = 0; i < original.axes.length; i++) {
  const old = original.axes[i], now = reconstructed[i];
  const expected = movedAxes.has(old.id) ? {...old, point_xyz_mm: [...old.point_xyz_mm.slice(0, 2), 180]} : old;
  assert.deepEqual(now, expected, old.id);
}
for (const row of layout.receiver_datums) {
  assert.equal(row.world_axis_point_xyz_mm[2], 180);
  assert.ok([44.45, 95.25].includes(row.from_Ymin_mm));
  if (row.receiver.startsWith('eoere_cleat')) assert.equal(row.from_Zmin_mm, 40.3);
  else assert.equal(row.from_Zmax_mm, 58.9);
  assert.equal(row.bit_instruction, null); assert.equal(row.actual, null);
}
assert.equal(layout.receiver_datums.length, 8);
for (const row of patch.replacements) {
  const source = layout.finished_receivers[row.name];
  const bytes = await readFile(path.join(root, source.path));
  assert.equal(bytes.length, source.bytes); assert.equal(sha(bytes), source.sha256);
  assert.equal(row.source_brep_sha256, source.sha256);
  assert.deepEqual(row.mesh.bounds_xyz_mm, source.bounds_xyz_mm.flat());
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
const parent = await loadExtendedCleatBaseScene(THREE, {...options, url: patch.parent_scene.url,
  expectedSha256: patch.parent_scene.sha256, decodedSha256: patch.parent_scene.decoded_sha256,
  layoutSha256: patch.parent_scene.layout_sha256});
const proposedOptions = {...options, url: path.basename(assetPath), expectedSha256: sha(asset),
  decodedSha256: sha(decoded), layoutSha256: sha(layoutBytes)};
const current = await loadLowerCleatPreviewScene(THREE, proposedOptions);
assert.equal(parent.parts.length, 1021); assert.equal(current.parts.length, 1021);
const byName = new Map(current.parts.map(row => [row.name, row])); assert.equal(byName.size, 1021);
const hosts = new Set(patch.replacements.map(row => row.name));
let unchanged = 0, translated = 0, changedReceivers = 0;
for (const old of parent.parts) {
  const now = byName.get(old.name); assert.ok(now, old.name);
  const before = old.geometry?.getAttribute('position').array, after = now.geometry?.getAttribute('position').array;
  if (hosts.has(old.name)) {
    assert.notDeepEqual(after, before, old.name);
    assert.equal(now.fabrication.lower_cleat_revision, layout.revision);
    changedReceivers++;
  } else if (old.fabrication.kind === 'bolt' && movedAxes.has(old.fabrication.connection_name)) {
    assert.equal(before.length, after.length, old.name);
    for (let i = 0; i < before.length; i++)
      assert.equal(after[i], i % 3 === 2 ? Math.fround(before[i] - 20) : before[i], `${old.name}:${i}`);
    assert.deepEqual(now.fabrication.world_translation_from_Z200_mm, [0, 0, -20]); translated++;
  } else {
    assert.deepEqual(now.fabrication, old.fabrication, old.name);
    if (before) assert.deepEqual(after, before, old.name);
    else assert.deepEqual(now, old, old.name);
    unchanged++;
  }
}
assert.equal(unchanged, 997); assert.equal(translated, 20); assert.equal(changedReceivers, 4);
for (const [kind, count] of [['timber', 22], ['panel', 6], ['bracket', 22], ['bolt', 500], ['screw', 66],
  ['light', 132], ['tnut', 142], ['wire', 131]])
  assert.equal(current.parts.filter(row => row.fabrication.kind === kind).length, count, kind);
assert.equal(new Set(current.parts.filter(row => row.fabrication.kind === 'bolt').map(row => row.fabrication.connection_name)).size, 100);
assert.equal(current.meta.geometry_adopted, false); assert.equal(current.meta.analysis_pass_transferred, false);
assert.equal(current.meta.physical_release, false); assert.equal(current.design.qualified_for_design, false);
const controls = [
  ['adopted status', p => {p.status = 'ADOPTED';}],
  ['geometry adoption', p => {p.release.geometry_adopted = true;}],
  ['response transfer', p => {p.saved_response_transferred = true;}],
  ['complete resistance', p => {p.complete_joint_resistance = 1;}],
  ['extra grid', p => {p.optional_2026_extra = true;}],
  ['parent hash', p => {p.parent_scene.sha256 = '0'.repeat(64);}],
  ['descriptor hash', p => {p.layout_report.sha256 = '0'.repeat(64);}],
  ['screw count', p => {p.counts.screw = 67;}],
  ['missing receiver', p => {p.replacements.pop();}],
  ['duplicate receiver', p => {p.replacements[1] = p.replacements[0];}],
  ['missing stack', p => {p.bolt_translations.pop();}],
  ['duplicate stack', p => {p.bolt_translations[1] = p.bolt_translations[0];}],
  ['wrong bolt translation', p => {p.bolt_translations[0].translation_xyz_mm[2] = -19;}],
];
for (const [label, change] of controls) {
  const control = structuredClone(patch); change(control);
  assert.throws(() => validateLowerCleatPreview(control, sha(layoutBytes)), undefined, label);
}
for (const key of ['expectedSha256', 'decodedSha256', 'layoutSha256'])
  await assert.rejects(() => loadLowerCleatPreviewScene(THREE, {...proposedOptions, [key]: '0'.repeat(64)}));
const sourcePaths = [assetPath, patch.layout_report.path, layout.parent_geometry.path, layout.placement.path,
  'site/index.html', 'site/eoere-lower-cleat-z180-overlay.mjs', 'scripts/check_eoere_lower_cleat_z180.mjs', bundlePath];
const result = {schema: 'eoere_lower_cleat_z180_actual_mesh_check/v1', passed: true,
  visible_parts: 1021, replaced_receivers: changedReceivers, translated_bolt_components: translated,
  unchanged_parts: unchanged, retained_bolt_axes: 100, retained_Hillman_screws: 66,
  proposed_descriptor_source_and_semantics_checked: true, datum_occurrences: 8,
  rejected_controls: controls.map(([label]) => label), rejected_hash_options: 3,
  source_sha256: Object.fromEntries(await Promise.all(sourcePaths.map(async name => [name, sha(await readFile(path.join(root, name)))]))),
  mechanics_or_physical_release: false};
await writeFile(output, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
for (const part of [...parent.parts, ...current.parts]) part.geometry?.dispose();
console.log(JSON.stringify({passed: true, unchanged, translated, changedReceivers, output}));
