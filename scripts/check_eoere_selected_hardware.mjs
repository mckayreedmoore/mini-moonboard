// Verify both assembled scenes using the installed Three.js implementation.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {loadKickerClearanceBaseScene} from '../site/eoere-kicker-clearance-overlay.mjs';
import {loadRightColumnScene} from '../site/eoere-right-column-overlay.mjs';
import {loadSelectedHardwareBaseScene, loadSelectedHardwareGridScene,
  validateSelectedHardware} from '../site/eoere-selected-hardware-overlay.mjs';

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const canonical = value => {
  const ordered = x => Array.isArray(x) ? x.map(ordered) : x && typeof x === 'object' ?
    Object.fromEntries(Object.keys(x).sort().map(k => [k, ordered(x[k])])) : x;
  return sha(JSON.stringify(ordered(value)));
};
const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0);
function verifyStations(data, retainedAxes) {
  const axes = new Map(retainedAxes.map(row => [row.id, row]));
  const selected = new Map(data.selected_stacks.map(row => [row.axis_id, row]));
  const close = (actual, expected, label) => assert.ok(actual.every((value, i) =>
    Math.abs(value - expected[i]) < 1e-8), label);
  for (const row of [...data.replacements, ...data.additions, ...data.translations]) {
    const axis = axes.get(row.fabrication.connection_name); assert.ok(axis, row.name);
    const norm = Math.hypot(...axis.direction_xyz), direction = axis.direction_xyz.map(value => value / norm);
    if (row.translation_xyz_mm) {
      close(row.translation_xyz_mm, direction.map(value => value * selected.get(axis.id).nut_side_spacer_mm),
        row.name + ' signed retained-axis nut travel');
    } else {
      const washer = axis.hardware_scenario.washer_thickness_mm;
      const station = row.fabrication.hardware_role === 'shaft' ? -(axis.before_plate_mm + washer) :
        axis.grip_mm + axis.after_plate_mm + washer;
      close(row.transform.slice(8, 11), direction, row.name + ' retained-axis direction');
      close(row.transform.slice(12, 15), axis.point_xyz_mm.map((value, i) => value + direction[i] * station),
        row.name + ' retained-axis origin');
    }
  }
}
function segmentRadius(a, b) {
  const d = [b[0] - a[0], b[1] - a[1]], denominator = dot(d, d);
  const fraction = denominator ? Math.max(0, Math.min(1, -dot(a.slice(0, 2), d) / denominator)) : 0;
  return Math.hypot(a[0] + fraction * d[0], a[1] + fraction * d[1]);
}
function triangleRadius(a, b, c) {
  const cross2 = (p, q) => p[0] * q[1] - p[1] * q[0];
  const area = cross2([b[0] - a[0], b[1] - a[1]], [c[0] - a[0], c[1] - a[1]]);
  const signs = [cross2(a, b), cross2(b, c), cross2(c, a)];
  if (Math.abs(area) > 1e-10 && (signs.every(value => value >= 0) || signs.every(value => value <= 0))) return 0;
  return Math.min(segmentRadius(a, b), segmentRadius(b, c), segmentRadius(c, a));
}
function verifySpacerMesh(geometry, transform, quantization) {
  const origin = transform.slice(12, 15), basis = [0, 4, 8].map(i => transform.slice(i, i + 3));
  const raw = geometry.getAttribute('position').array, vertices = [];
  const inner = 10.31875 / 2, outer = 19.05 / 2, length = 12.7;
  // Quantization plus a stricter 0.05-mm facet allowance is an acceptance limit,
  // independent of the source export's looser maximum tessellation tolerance.
  const tolerance = Math.sqrt(3) * quantization / 2 + 0.05;
  for (let i = 0; i < raw.length; i += 3) {
    const delta = origin.map((value, j) => raw[i + j] - value), point = basis.map(axis => dot(delta, axis));
    const radius = Math.hypot(point[0], point[1]);
    assert.ok(Math.min(Math.abs(radius - inner), Math.abs(radius - outer)) <= tolerance, 'spacer surface radii');
    assert.ok(Math.min(Math.abs(point[2]), Math.abs(point[2] - length)) <= tolerance, 'spacer axial endpoints');
    vertices.push(point);
  }
  let volume = 0, boreRadius = Infinity;
  for (let i = 0; i < vertices.length; i += 3) {
    const [a, b, c] = vertices.slice(i, i + 3);
    const cross = [b[1] * c[2] - b[2] * c[1], b[2] * c[0] - b[0] * c[2], b[0] * c[1] - b[1] * c[0]];
    volume += dot(a, cross) / 6;
    boreRadius = Math.min(boreRadius, triangleRadius(a, b, c));
  }
  assert.ok(boreRadius >= inner - tolerance, 'spacer triangles must preserve through bore');
  const nominal = Math.PI * (outer ** 2 - inner ** 2) * length;
  const lower = Math.PI * ((outer - tolerance) ** 2 - (inner + tolerance) ** 2) * (length - 2 * tolerance);
  const upper = Math.PI * ((outer + tolerance) ** 2 - (inner - tolerance) ** 2) * (length + 2 * tolerance);
  assert.ok(volume >= lower && volume <= upper, 'signed spacer mesh volume');
  return {volume_mm3: volume, nominal_volume_mm3: nominal, volume_acceptance_mm3: [lower, upper],
    minimum_projected_bore_radius_mm: boreRadius, surface_tolerance_mm: tolerance};
}
const output = process.argv[2]; assert.ok(output, 'fresh output path required');
const assetPath = 'site/eoere-selected-hardware-scene.json.gz';
const asset = await readFile(path.join(root, assetPath)), decoded = gunzipSync(asset), patch = JSON.parse(decoded);
const layoutBytes = await readFile(path.join(root, patch.layout_report.path)), layout = JSON.parse(layoutBytes);
assert.equal(sha(layoutBytes), patch.layout_report.sha256);
const axisBytes = await readFile(path.join(root, layout.retained_axis_geometry.path)), axisLayout = JSON.parse(axisBytes);
assert.equal(sha(axisBytes), layout.retained_axis_geometry.sha256);
const extraAxisBytes = await readFile(path.join(root, layout.parents.extra.path));
assert.equal(sha(extraAxisBytes), layout.parents.extra.sha256);
assert.deepEqual(JSON.parse(extraAxisBytes).axes, axisLayout.axes);
assert.deepEqual(JSON.parse(extraAxisBytes).screw_axes, axisLayout.screw_axes);
assert.equal(axisLayout.axes.length, 100); assert.equal(axisLayout.screw_axes.length, 66);
assert.deepEqual(layout.selected_stacks, patch.selected_stacks);
verifyStations(patch, axisLayout.axes);
const sourceBytes = await readFile(path.join(root, layout.source_map.path)), sources = JSON.parse(sourceBytes);
assert.equal(sha(sourceBytes), layout.source_map.sha256);
assert.equal(canonical(sources), layout.source_map_canonical_sha256);
assert.equal(Object.keys(sources).length, layout.source_pin_count);
for (const [name, digest] of Object.entries(sources)) assert.equal(sha(await readFile(path.resolve(root, name))), digest, name);
for (const row of [...patch.replacements, ...patch.translations, ...patch.additions, ...patch.templates]) {
  const source = [...layout.changed_finished_solids, ...layout.template_solids].find(value => value.id === (row.name || row.id));
  assert.ok(source); assert.equal(row.source_brep_sha256, source.sha256);
  const bytes = await readFile(path.join(root, source.path));
  assert.equal(bytes.length, source.bytes); assert.equal(sha(bytes), source.sha256);
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
const outcomes = [], spacerChecks = [];
for (const [variant, parentLoader, loader] of [['base', loadKickerClearanceBaseScene, loadSelectedHardwareBaseScene],
  ['extra', loadRightColumnScene, loadSelectedHardwareGridScene]]) {
  const binding = patch.parents[variant];
  const parent = await parentLoader(THREE, {...options, url: binding.url, expectedSha256: binding.sha256,
    decodedSha256: binding.decoded_sha256, layoutSha256: binding.layout_sha256});
  const current = await loader(THREE, proposedOptions);
  const byName = new Map(current.parts.map(row => [row.name, row]));
  assert.equal(byName.size, patch.counts[variant]);
  const changed = new Map([...patch.replacements, ...patch.translations].map(row => [row.name, row]));
  let unchanged = 0;
  for (const old of parent.parts) {
    const now = byName.get(old.name); assert.ok(now, old.name);
    const before = old.geometry?.getAttribute('position').array, after = now.geometry?.getAttribute('position').array;
    const row = changed.get(old.name);
    if (row) {
      assert.notDeepEqual(after, before, old.name);
      if (row.translation_xyz_mm) {
        assert.equal(after.length, before.length);
        for (let i = 0; i < after.length; i++)
          assert.ok(Math.abs(after[i] - before[i] - row.translation_xyz_mm[i % 3]) < 0.0003, old.name);
      }
    } else {
      if (before) assert.deepEqual(after, before, old.name);
      else assert.deepEqual(now, old, old.name);
      if (old.fabrication.kind !== 'bolt') assert.deepEqual(now.fabrication, old.fabrication, old.name);
      unchanged++;
    }
  }
  assert.equal(unchanged, parent.parts.length - 40);
  for (const source of layout.changed_finished_solids) {
    const part = byName.get(source.id); assert.ok(part, source.id);
    part.geometry.computeBoundingBox();
    const bb = part.geometry.boundingBox;
    const bounds = [bb.min.x, bb.max.x, bb.min.y, bb.max.y, bb.min.z, bb.max.z];
    bounds.forEach((value, i) => assert.ok(Math.abs(value - source.bounds_xyz_mm[i]) < 0.15, source.id));
    for (let i = 0; i < 3; i++) {
      assert.ok(current.bounds_mm[0][i] <= bounds[i * 2]);
      assert.ok(current.bounds_mm[1][i] >= bounds[i * 2 + 1]);
    }
  }
  for (const row of patch.additions) spacerChecks.push({variant, name: row.name,
    ...verifySpacerMesh(byName.get(row.name).geometry, row.transform, 0.1)});
  if (variant === 'base') {
    const row = patch.additions[0], reversed = byName.get(row.name).geometry.clone();
    const positions = reversed.getAttribute('position').array;
    for (let i = 0; i < positions.length; i += 9) for (let j = 0; j < 3; j++)
      [positions[i + 3 + j], positions[i + 6 + j]] = [positions[i + 6 + j], positions[i + 3 + j]];
    assert.throws(() => verifySpacerMesh(reversed, row.transform, 0.1), /signed spacer mesh volume/);
    reversed.dispose();
  }
  const axes = new Map(axisLayout.axes.map(row => [row.id, row]));
  for (const selection of patch.selected_stacks) {
    const parts = current.parts.filter(part => part.fabrication.connection_name === selection.axis_id);
    assert.equal(parts.length, selection.nut_side_spacer_mm ? 6 : 5, selection.axis_id);
    for (const part of parts) {
      assert.equal(part.fabrication.selected_underhead_length_mm, selection.selected_underhead_length_mm);
      assert.equal(part.fabrication.delivered_part_verified, false);
      assert.deepEqual([...part.fabrication.stack_roles].sort(), parts.map(p => p.fabrication.hardware_role).sort());
    }
    const row = patch.replacements.find(part => part.fabrication.connection_name === selection.axis_id);
    if (!row) continue;
    const axis = axes.get(selection.axis_id), length = selection.selected_underhead_length_mm;
    const positions = byName.get(row.name).geometry.getAttribute('position').array;
    const direction = row.transform.slice(8, 11), origin = row.transform.slice(12, 15), projections = [];
    assert.ok(direction.every((v, i) => Math.abs(v - axis.direction_xyz[i]) < 1e-9));
    for (let i = 0; i < positions.length; i += 3)
      projections.push(direction.reduce((s, v, j) => s + v * (positions[i + j] - origin[j]), 0));
    assert.ok(Math.abs(Math.min(...projections)) < 0.15, row.name);
    assert.ok(Math.abs(Math.max(...projections) - length) < 0.15, row.name);
  }
  for (const [kind, expected] of [['timber', 22], ['panel', 6], ['bracket', 22], ['bolt', 508], ['screw', 66]])
    assert.equal(current.parts.filter(row => row.fabrication.kind === kind).length, expected, kind);
  assert.equal(new Set(current.parts.filter(row => row.fabrication.kind === 'bolt').map(row => row.fabrication.connection_name)).size, 100);
  assert.equal(current.meta.hardware_model_updated, true);
  assert.equal(current.meta.analysis_pass_transferred, false); assert.equal(current.meta.physical_release, false);
  assert.equal(current.design.qualified_for_design, false);
  outcomes.push({variant, count: current.parts.length, unchanged_geometry: unchanged, replaced: 40, added: 8});
  for (const part of [...parent.parts, ...current.parts]) part.geometry?.dispose();
}
const controls = [
  ['response transfer', p => {p.analysis_pass_transferred = true;}],
  ['release', p => {p.release.fabrication = true;}],
  ['missing shaft', p => {p.replacements.pop();}],
  ['duplicate spacer', p => {p.additions[1] = p.additions[0];}],
  ['invalid catalog margin', p => {p.selected_stacks[0].minimum_two_pitch_margin_mm = 0;}],
  ['full thread substitution', p => {p.selected_stacks[0].selected_bolt_grade = 'full thread';}],
  ['scaled instance', p => {p.replacements[0].transform[0] = 2;}],
  ['missing nut', p => {p.translations.pop();}],
  ['wrong nut travel', p => {p.translations[0].translation_xyz_mm = [0, 0, 13];}],
  ['bolt count', p => {p.counts.physical_bolt_axes = 99;}],
  ['parent binding', p => {p.parents.base.sha256 = '0'.repeat(64);}],
];
for (const [label, change] of controls) {
  const control = structuredClone(patch); change(control);
  assert.throws(() => validateSelectedHardware(control, sha(layoutBytes)), undefined, label);
}
const stationControls = [
  ['shifted shaft origin', p => {p.replacements[0].transform[12] += 25;}],
  ['shifted spacer station', p => {p.additions[0].transform[12] += 25;}],
  ['reversed nut travel', p => {p.translations[0].translation_xyz_mm = p.translations[0].translation_xyz_mm.map(value => -value);}],
];
for (const [label, change] of stationControls) {
  const control = structuredClone(patch); change(control);
  validateSelectedHardware(control, sha(layoutBytes));
  assert.throws(() => verifyStations(control, axisLayout.axes), undefined, label);
}
// A filled cylinder has the same rendered outer bounds and length as the spacer.
const filled = [], radius = 9.5, length = 12.7;
for (let i = 0; i < 64; i++) {
  const point = (angle, z) => [radius * Math.cos(angle), radius * Math.sin(angle), z];
  const a = point(2 * Math.PI * i / 64, 0), b = point(2 * Math.PI * (i + 1) / 64, 0);
  const c = [b[0], b[1], length], d = [a[0], a[1], length];
  filled.push(...a, ...b, ...c, ...a, ...c, ...d, 0, 0, 0, ...b, ...a, 0, 0, length, ...d, ...c);
}
const filledGeometry = new THREE.BufferGeometry();
filledGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(filled), 3));
const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
assert.throws(() => verifySpacerMesh(filledGeometry, identity, 0.1), /spacer surface radii/, 'filled spacer bore');
filledGeometry.dispose();
// A cap with every vertex on the inner circumference still closes the bore.
const cap = Array.from({length: 3}, (_, i) => [10.31875 / 2 * Math.cos(i * 2 * Math.PI / 3),
  10.31875 / 2 * Math.sin(i * 2 * Math.PI / 3), 0]).flat();
const capGeometry = new THREE.BufferGeometry();
capGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(cap), 3));
assert.throws(() => verifySpacerMesh(capGeometry, identity, 0.1), /spacer triangles must preserve through bore/);
capGeometry.dispose();
for (const key of ['expectedSha256', 'decodedSha256', 'layoutSha256'])
  await assert.rejects(() => loadSelectedHardwareBaseScene(THREE, {...proposedOptions, [key]: '0'.repeat(64)}));
const sourcePaths = [assetPath, patch.layout_report.path, layout.retained_axis_geometry.path,
  'site/eoere-selected-hardware-overlay.mjs', 'scripts/check_eoere_selected_hardware.mjs', bundlePath];
const result = {schema: 'eoere_selected_hardware_actual_mesh_check/v1', passed: true, outcomes,
  unchanged_bolt_axes: 100, unchanged_screw_axes: 66, source_pins_checked: layout.source_pin_count,
  world_BREP_bytes_checked: 48, source_bounds_tolerance_mm: 0.15, rejected_controls: controls.map(([label]) => label),
  retained_axis_stations_checked: 48, rejected_station_controls: stationControls.map(([label]) => label),
  rendered_spacer_checks: spacerChecks, rejected_spacer_controls: ['filled spacer bore', 'capped bore', 'reversed winding'],
  rejected_hash_options: 3,
  source_sha256: Object.fromEntries(await Promise.all(sourcePaths.map(async name => [name, sha(await readFile(path.join(root, name)))]))),
  mechanics_or_physical_release: false};
await writeFile(output, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({passed: true, outcomes, output}));
