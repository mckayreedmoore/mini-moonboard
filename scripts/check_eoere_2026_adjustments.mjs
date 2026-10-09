// Exercise real Three.js meshes and preserve every previous viewer choice.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {load2026AdjustmentsScene, loadAdjustedFrameScene, validate2026Adjustments, validateAdjustedBase} from '../site/eoere-2026-adjustments-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const sha = data => createHash('sha256').update(data).digest('hex');
const output = process.argv[2]; assert.ok(output, 'fresh ignored output path required');
const reportPath = 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-2026-adjustments-v3.json';
const reportBytes = await readFile(path.join(root, reportPath)), report = JSON.parse(reportBytes);
const asset = await readFile(path.join(site, 'eoere-2026-adjustments-v3-scene.json.gz'));
const decoded = gunzipSync(asset), patch = JSON.parse(decoded);
assert.equal(patch.layout_report.sha256, sha(reportBytes));
assert.equal(report.grid.length, 120); assert.equal(report.new_wire_routes.length, 119);
assert.equal(report.rerouted_original_wire_links.length, 10);
assert.equal(report.second_cable_plane_N_mm, 14);
assert.ok(Object.values(report.collisions).every(rows => rows.length === 0));
assert.equal(report.panel_drilling.reduce((n, row) => n + row.added_hold_bores, 0), 120);
assert.equal(report.panel_drilling.reduce((n, row) => n + row.added_LED_bores, 0), 120);
assert.ok(report.panel_drilling.every(row => Math.abs(row.removed_volume_mm3 - row.expected_volume_mm3) < .01));
assert.equal(report.principal_move_adopted, true);
assert.equal(report.unofficial_2026_positions, true);
assert.equal(report.all_midpoints_are_assumed_not_confirmed, true);
for (const [name, digest] of Object.entries(report.source_sha256))
  assert.equal(sha(await readFile(path.resolve(root, name))), digest, `frozen source ${name}`);
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
const options = {baselineParts: JSON.parse(baselineText).parts, baselineText,
  resolveMeshPath: value => aliases[value] || value};
const parent = await loadAdjustedFrameScene(THREE, {...options, url: patch.parent_scene.url,
  expectedSha256: patch.parent_scene.sha256, decodedSha256: patch.parent_scene.decoded_sha256,
  layoutSha256: patch.parent_scene.layout_sha256});
const current = await load2026AdjustmentsScene(THREE, {...options, url: 'eoere-2026-adjustments-v3-scene.json.gz',
  expectedSha256: sha(asset), decodedSha256: sha(decoded), layoutSha256: sha(reportBytes)});
const byName = new Map(current.parts.map(row => [row.name, row]));
assert.equal(byName.size, 1380);
for (const [kind, count] of [['light', 252], ['tnut', 262], ['wire', 250], ['screw', 66]])
  assert.equal(current.parts.filter(row => row.fabrication.kind === kind).length, count, kind);
assert.equal(new Set(current.parts.filter(row => row.fabrication.kind === 'bolt').map(row => row.fabrication.connection_name)).size, 100);
const replaced = new Set(patch.replacements.map(row => row.name));
let unchanged = 0;
for (const old of parent.parts) {
  const now = byName.get(old.name); assert.ok(now, old.name);
  if (!replaced.has(old.name)) {
    assert.deepEqual(now.fabrication, old.fabrication, old.name);
    if (old.geometry) assert.deepEqual(now.geometry.getAttribute('position').array, old.geometry.getAttribute('position').array, old.name);
    else assert.deepEqual(now, old, old.name);
    unchanged++;
  } else assert.notDeepEqual(now.geometry.getAttribute('position').array, old.geometry?.getAttribute('position').array, old.name);
}
assert.equal(unchanged, 1021 - patch.replacements.length);
for (const row of patch.additions) {
  const part = byName.get(row.name); assert.ok(part.geometry, row.name);
  assert.ok(part.geometry.getAttribute('position').array.every(Number.isFinite), row.name);
  assert.equal(part.fabrication.clearance_status, row.fabrication.clearance_status);
}
const red = current.parts.filter(row => row.fabrication.clearance_status?.startsWith('FAIL'));
assert.ok(!report.collisions.new_services_vs_timber.some(row => row.first.startsWith('hold_tnut_2026_FG')), 'relocated principal must clear midpoint T-nuts');
const principal = parent.parts.find(row => row.name === 'base_principal_center_right');
assert.ok(Math.abs(principal.geometry.boundingBox.min.x - 11.75) < .11);
assert.ok(Math.abs(principal.geometry.boundingBox.max.x - 49.85) < .11);
assert.equal(parent.parts.length, 1021);
assert.equal(parent.parts.filter(row => row.name.startsWith('light_2026_')).length, 0);
assert.equal(current.design.qualified_for_design, false); assert.equal(current.meta.analysis_pass_transferred, false);
const baseBytes = await readFile(path.join(root, 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-adjusted-base-v3.json'));
const baseReport = JSON.parse(baseBytes);
assert.equal(baseReport.moved_bolt_axes.length, 22); assert.equal(baseReport.moved_panel_screw_axes.length, 10);
assert.equal(baseReport.extended_rails.length, 3);
assert.ok(Object.values(baseReport.collisions).every(rows => rows.length === 0));
assert.ok(baseReport.affected_duties.includes("clip_split_header_center_right"));
assert.equal(baseReport.retained_service_bodies_audited, 405);
assert.equal(report.retained_service_bodies_audited, 405);
assert.equal(baseReport.canonical_interval_checks.length, 12);
for (const row of baseReport.canonical_interval_checks) {
  assert.ok(row.canonical_interval_mm.every((value, i) => Math.abs(value - row.saved_receiver_x_bounds_mm[i]) < 1e-6));
  assert.ok(Math.abs(row.canonical_interval_mm[0] - 11.75) < 1e-6);
  assert.ok(Math.abs(row.canonical_interval_mm[1] - 49.85) < 1e-6);
}
const sourceAxes = JSON.parse(await readFile(path.join(root, 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-aligned-wire-v1.json'))).axes;
for (const axis of baseReport.axes.filter(row => baseReport.moved_bolt_axes.includes(row.id))) {
  const original = sourceAxes.find(row => row.id === axis.id);
  for (let i = 0; i < axis.attachments.length; i++) {
    const direction = original.attachments[i].direction;
    const sign = direction.find(value => Math.abs(value) > 1e-8) > 0 ? 1 : -1;
    const delta = -39.2 * direction[0] * sign / Math.hypot(...direction);
    assert.ok(axis.attachments[i].interval_mm.every((value, j) => Math.abs(value - original.attachments[i].interval_mm[j] - delta) < 1e-8));
  }
}
assert.ok(baseReport.restored_contacts.every(row => row.distance_mm < 1e-5 && row.intersection_mm3 < .01));
assert.ok(baseReport.screw_support.every(row => row.full_body_fraction > .999999));
const baseAsset = await readFile(path.join(site, 'eoere-adjusted-base-v3-scene.json.gz'));
const basePatch = JSON.parse(gunzipSync(baseAsset));
validateAdjustedBase(basePatch, sha(baseBytes));
const baseControl = structuredClone(basePatch); baseControl.replacements.pop();
assert.throws(() => validateAdjustedBase(baseControl, sha(baseBytes)));
const controls = [
  ['missing added light', p => {p.additions.splice(p.additions.findIndex(r => r.fabrication.kind === 'light'), 1);}],
  ['changed parent', p => {p.parent_scene.sha256 = '0'.repeat(64);}],
  ['missing relocation', p => {p.principal_move_adopted = false;}],
  ['official grid claim', p => {p.unofficial_2026_positions = false;}],
  ['fabrication release', p => {p.release.fabrication_released = true;}],
  ['wrong report', p => {p.layout_report.sha256 = '0'.repeat(64);}],
  ['wrong screw count', p => {p.counts.screw = 67;}],
];
for (const [label, change] of controls) {
  const copy = structuredClone(patch); change(copy);
  assert.throws(() => validate2026Adjustments(copy, sha(reportBytes)), undefined, label);
}
const result = {schema: 'eoere_2026_actual_mesh_check/v1', passed: true, visible_parts: 1380,
  unchanged_parts: unchanged, replacements: patch.replacements.length, added_parts: 359,
  retained_bolt_axes: 100, retained_Hillman_screws: 66, lights: 252, tnuts: 262, wires: 250,
  red_revision_parts: red.map(row => row.name), rejected_controls: controls.map(([label]) => label),
  source_sha256: {[reportPath]: sha(reportBytes), 'site/eoere-2026-adjustments-v3-scene.json.gz': sha(asset),
    'site/eoere-2026-adjustments-overlay.mjs': sha(await readFile(path.join(site, 'eoere-2026-adjustments-overlay.mjs'))),
    'scripts/check_eoere_2026_adjustments.mjs': sha(await readFile(fileURLToPath(import.meta.url)))},
  mechanics_or_physical_release: false};
await writeFile(output, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
for (const part of [...parent.parts, ...current.parts]) part.geometry?.dispose();
console.log(JSON.stringify({passed: true, unchanged, visible_parts: 1380, red_parts: red.length, output}));
