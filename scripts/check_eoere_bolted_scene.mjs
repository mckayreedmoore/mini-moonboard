// Pure fixtures by default. Actual exported-file mode uses an existing Three.js module.
// --fixtures
// [--bundle] /existing/three.js --scene eoere-review-scene.json.gz
//   --encoded-sha SHA --decoded-sha SHA --layout-sha SHA [--out ignored/result.json]
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {webcrypto, createHash} from 'node:crypto';
import {gzipSync, gunzipSync} from 'node:zlib';
import {pathToFileURL, fileURLToPath} from 'node:url';
import path from 'node:path';
import {EOERE_COUNTS, EOERE_MAIN_ANGLE_IDS, EOERE_PARENT_SHA256, EOERE_SHARED_SCENE,
  validateEoereBoltedScene, loadEoereBoltedScene} from '../site/eoere-bolted-overlay.mjs';

const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
globalThis.crypto ??= webcrypto;
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const baselineOptions = {baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: p => aliases[p] || p};

function localPath(value) {
  return typeof value === 'string' && !value.startsWith('/') && !value.includes('\\') && !value.includes(':') &&
    !value.split('/').some(part => !part || part === '.' || part === '..');
}

function fileFetch(memory = new Map()) {
  return async url => {
    assert.ok(localPath(url), 'fetch remains within the site');
    return new Response(memory.get(url) || await readFile(path.join(site, url)), {status: 200});
  };
}

// Tiny CPU geometry stand-in checks array decoding, proper transforms and bounds.
// It neither computes display normals nor exercises WebGL/Three.js rendering.
class FixtureGeometry {
  attributes = {};
  setAttribute(key, value) { this.attributes[key] = value; return this; }
  getAttribute(key) { return this.attributes[key]; }
  computeVertexNormals() {}
  clone() { const result = new FixtureGeometry(); result.setAttribute('position', {array: this.getAttribute('position').array.slice()}); return result; }
  applyMatrix4(matrix) {
    const values = this.getAttribute('position').array, m = matrix.elements;
    for (let i = 0; i < values.length; i += 3) {
      const [x, y, z] = values.slice(i, i+3);
      values.set([m[0]*x+m[4]*y+m[8]*z+m[12], m[1]*x+m[5]*y+m[9]*z+m[13], m[2]*x+m[6]*y+m[10]*z+m[14]], i);
    }
    return this;
  }
  computeBoundingBox() {
    const values = this.getAttribute('position').array;
    this.boundingBox = {min: {x: Infinity, y: Infinity, z: Infinity}, max: {x: -Infinity, y: -Infinity, z: -Infinity}};
    for (let i = 0; i < values.length; i++) {
      const axis = ['x', 'y', 'z'][i%3];
      this.boundingBox.min[axis] = Math.min(this.boundingBox.min[axis], values[i]);
      this.boundingBox.max[axis] = Math.max(this.boundingBox.max[axis], values[i]);
    }
  }
  dispose() { this.disposed = true; }
}
const FixtureTHREE = {BufferGeometry: FixtureGeometry,
  BufferAttribute: class { constructor(array, itemSize) { this.array = array; this.itemSize = itemSize; } },
  Matrix4: class { fromArray(values) { this.elements = values; return this; } }};

function fixtureScene(retained, services) {
  const vertices = Buffer.alloc(24), vertexValues = [0, 0, 0, 10, 0, 0, 0, 10, 0, 0, 0, 10];
  vertexValues.forEach((value, index) => vertices.writeInt16LE(value, index*2));
  const indices = Buffer.alloc(24), indexValues = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3];
  indexValues.forEach((value, index) => indices.writeUInt16LE(value, index*2));
  const topology = digest(indices), solids = [], angleIds = [...EOERE_MAIN_ANGLE_IDS, ...Array.from({length: 6}, (_, i) => `eoere_fixture_remaining_${i}`)];
  const add = (name, kind, extra = {}) => solids.push({id: name, name, template_id: 'tiny',
    transform: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, solids.length*2, 0, 0, 1],
    fabrication: {kind, description: 'Synthetic display fixture only; no source CAD or mechanics claim', ...extra}});
  for (let i = 0; i < EOERE_COUNTS.timber; i++) add(`fixture_timber_${i}`, 'timber');
  for (const name of angleIds) add(name, 'bracket', {duty_id: name.slice(6)});
  const roles = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'];
  for (let i = 0; i < EOERE_COUNTS.physical_bolt_axes; i++) for (const role of roles) add(`fixture_axis_${i}_${role}`, 'bolt',
    {connection_name: `fixture_axis_${i}`, hardware_role: role, stack_roles: roles});
  const holes = angleIds.map((angle_id, i) => ({angle_id, holes: ['beam', 'post'].flatMap((flange, j) =>
    ['near', 'far'].flatMap(row => [-1, 1].map((transverse, k) => ({id: `${angle_id}/${flange}/${row}/${transverse}`,
      flange, row, transverse, point_xyz_mm: [i, j, transverse], direction_xyz: [0, 0, 1],
      installed_bolt_axis_id: row === 'far' ? `fixture_axis_${[17, 19].includes(i) && j === 1 ? (i-1)*4+j*2+k : i*4+j*2+k}` : null}))))}));
  return {schema: 'eoere_bolted_review_scene/v1', candidate: 'compact-floor-flush-eoere-bolted-development',
    revision: 'eoere-far-pairs-cleat-corners-v1', status: 'REVISE_UNQUALIFIED_PROPOSAL',
    parent_scene: {url: 'owner-wood-joints-wj24-scene.json', sha256: EOERE_PARENT_SHA256},
    shared_scene: {...EOERE_SHARED_SCENE},
    layout_report: {path: 'synthetic/eoere-layout.json', sha256: '1'.repeat(64)},
    baseline_manifest_sha256: digest(baselineText), counts: {...EOERE_COUNTS},
    retained_shared_part_names: retained, retained_parent_service_names: services,
    solids, factory_angle_holes: holes,
    mesh_templates: {tiny: {id: 'tiny', mesh: {encoding: 'base64_typed_arrays_le_v1', bounds_xyz_mm: [0, 1, 0, 1, 0, 1],
      vertex_component_type: 'int16', triangle_component_type: 'uint16', vertex_count: 4, triangle_count: 4,
      vertex_quantization_mm: .1, vertex_max_euclidean_error_mm: 0, vertices_base64: vertices.toString('base64'), triangle_topology_sha256: topology}}},
    triangle_topologies: {[topology]: {triangle_count: 4, triangle_component_type: 'uint16', index_count: 12, triangle_indices_base64: indices.toString('base64')}},
    release: Object.fromEntries(['candidate_accepted', 'complete_joint_acceptance', 'capacity_established', 'fabrication_released',
      'structural_released', 'climbing_released'].map(key => [key, false])), mechanics_ready: false,
    design: {key: 'eoere-development', qualified_for_design: false}};
}

const mutations = [
  ['release', d => { d.release.climbing_released = true; }],
  ['extra-release', d => { d.release.unlisted_acceptance = true; }],
  ['mechanics-ready', d => { d.mechanics_ready = true; }],
  ['design-qualified', d => { d.design.qualified_for_design = true; }],
  ['unknown-revision', d => { d.revision = 'unknown'; }],
  ['changed-parent', d => { d.parent_scene = {url: 'owner-wood-joints-wj24-scene.json', sha256: '0'.repeat(64)}; }],
  ['changed-shared-encoded-source', d => { d.shared_scene.sha256 = '0'.repeat(64); }],
  ['changed-shared-decoded-source', d => { d.shared_scene.decoded_sha256 = '0'.repeat(64); }],
  ['changed-layout', d => { d.layout_report.sha256 = '0'.repeat(64); }],
  ['changed-census', d => { d.counts.physical_bolt_axes++; }],
  ['duplicate-part', d => { d.solids.push(d.solids[0]); }],
  ['scale-transform', d => { d.solids.find(row => row.template_id).transform[0] *= 2; }],
  ['reflect-transform', d => { const m = d.solids.find(row => row.template_id).transform; m[0] *= -1; m[1] *= -1; m[2] *= -1; }],
  ['unknown-role', d => { d.solids.find(row => row.fabrication.kind === 'bolt').fabrication.hardware_role = 'unknown'; }],
  ['missing-role', d => { d.solids.splice(d.solids.findIndex(row => row.fabrication.kind === 'bolt'), 1); }],
  ['duplicate-role', d => { const rows = d.solids.filter(row => row.fabrication.kind === 'bolt'); rows[1].fabrication.hardware_role = rows[0].fabrication.hardware_role; }],
  ['unknown-main-angle', d => { const row = d.solids.find(row => row.name === EOERE_MAIN_ANGLE_IDS[0]); row.id = row.name = 'unknown_angle'; }],
  ['missing-factory-hole', d => { d.factory_angle_holes[0].holes.pop(); }],
  ['duplicate-factory-hole', d => { d.factory_angle_holes[0].holes[1] = d.factory_angle_holes[0].holes[0]; }],
  ['unused-hole-installed', d => { d.factory_angle_holes[0].holes.find(hole => hole.row === 'near').installed_bolt_axis_id = 'wrong'; }],
  ['installed-hole-unbound', d => { d.factory_angle_holes[0].holes.find(hole => hole.row === 'far').installed_bolt_axis_id = 'missing'; }],
  ['lost-shared-shaft', d => { d.factory_angle_holes[17].holes.find(hole => hole.row === 'far' && hole.flange === 'post').installed_bolt_axis_id = 'fixture_axis_99'; }],
  ['alien-hole-owner', d => { d.factory_angle_holes[0].angle_id = 'unknown'; }],
  ['hole-direction-scale', d => { d.factory_angle_holes[0].holes[0].direction_xyz = [0, 0, 2]; }],
  ['old-wire-service', d => { d.retained_parent_service_names[0] = 'wire_old'; }],
  ['duplicate-shared-part', d => { d.retained_shared_part_names[0] = d.retained_shared_part_names[1]; }],
  ['missing-shared-part', d => { d.retained_shared_part_names.pop(); }],
];

function checkRejected(data, layout) {
  const rejected = [];
  for (const [name, mutate] of mutations) {
    const invalid = structuredClone(data); mutate(invalid);
    assert.throws(() => validateEoereBoltedScene(invalid, layout)); rejected.push(name);
  }
  return rejected;
}

function verifyLoaded(loaded) {
  const kinds = Object.fromEntries(['timber', 'panel', 'bracket', 'bolt', 'screw', 'wire', 'light', 'tnut']
    .map(kind => [kind, loaded.parts.filter(part => part.fabrication.kind === kind).length]));
  assert.deepEqual(kinds, {timber: EOERE_COUNTS.timber, panel: EOERE_COUNTS.panel, bracket: EOERE_COUNTS.bracket,
    bolt: EOERE_COUNTS.bolt, screw: EOERE_COUNTS.screw, wire: EOERE_COUNTS.wire, light: EOERE_COUNTS.lights, tnut: EOERE_COUNTS.tnuts});
  assert.equal(loaded.parts.length, EOERE_COUNTS.total_visible_parts);
  assert.equal(new Set(loaded.parts.filter(part => part.fabrication.kind === 'bolt').map(part => part.fabrication.connection_name)).size, EOERE_COUNTS.physical_bolt_axes);
  assert.equal(loaded.meta.physical_release, false); assert.equal(loaded.design.qualified_for_design, false);
  for (const part of loaded.parts) {
    assert.ok(Array.isArray(part.fabrication.dimensions_mm) && part.fabrication.dimensions_mm.length === 3 &&
      part.fabrication.dimensions_mm.every(value => Number.isFinite(value) && value >= 0), 'all visible parts have display dimensions');
    if (part.geometry) assert.ok([...part.geometry.getAttribute('position').array].every(Number.isFinite));
  }
  assert.ok(loaded.bounds_mm.flat().every(Number.isFinite));
  return kinds;
}

const args = process.argv.slice(2), fixtures = !args.length || args[0] === '--fixtures';
if (fixtures) {
  const thin = JSON.parse(gunzipSync(await readFile(path.join(site, 'thin-bolted-scene.json.gz'))));
  const shared = [...thin.solids.filter(row => ['panel', 'screw', 'wire'].includes(row.fabrication.kind)).map(row => row.name),
    ...thin.retained_parent_service_names];
  assert.equal(shared.length, 477);
  const scene = fixtureScene(shared, thin.retained_parent_service_names);
  // Match the exporter: parent is reached through shared_scene, and timbers
  // may carry global inline meshes before the first transformed template.
  delete scene.parent_scene;
  scene.solids[0].mesh = structuredClone(scene.mesh_templates.tiny.mesh);
  delete scene.solids[0].template_id;
  delete scene.solids[0].transform;
  assert.equal(validateEoereBoltedScene(scene, '1'.repeat(64)), EOERE_COUNTS.physical_bolt_axes);
  const rejected = checkRejected(scene, '1'.repeat(64)), raw = Buffer.from(JSON.stringify(scene)), encoded = gzipSync(raw);
  globalThis.fetch = fileFetch(new Map([['eoere-fixture.json', raw], ['eoere-fixture.json.gz', encoded]]));
  for (const [url, bytes] of [['eoere-fixture.json', raw], ['eoere-fixture.json.gz', encoded]]) {
    const options = {...baselineOptions, url, expectedSha256: digest(bytes), decodedSha256: digest(raw), layoutSha256: '1'.repeat(64)};
    await assert.rejects(loadEoereBoltedScene(FixtureTHREE, {...options, expectedSha256: '0'.repeat(64)}), /scene bytes differ/);
    if (url.endsWith('.gz')) await assert.rejects(loadEoereBoltedScene(FixtureTHREE, {...options, decodedSha256: '0'.repeat(64)}), /decoded scene bytes differ/);
    const loaded = await loadEoereBoltedScene(FixtureTHREE, options); verifyLoaded(loaded);
    for (const part of loaded.parts) part.geometry?.dispose();
  }
  console.log(JSON.stringify({schema: 'eoere_bolted_scene_loader_fixture/v1', passed: true, rejected,
    visible_parts: EOERE_COUNTS.total_visible_parts, owned_solids: 544, shared_parts: 477,
    physical_shafts: EOERE_COUNTS.physical_bolt_axes, factory_angle_holes: EOERE_COUNTS.bracket*8,
    plain_and_gzip_verified: true, candidate_CAD_query_or_mechanics: false,
    real_Three_or_browser_render_tested: false, physical_release: false}));
} else {
  let modulePath = args.shift(), bundle = false;
  if (modulePath === '--bundle') { bundle = true; modulePath = args.shift(); }
  assert.ok(modulePath, 'supply an existing Three.js module or viewer bundle');
  const options = {};
  while (args.length) {
    const key = args.shift(); assert.ok(['--scene', '--encoded-sha', '--decoded-sha', '--layout-sha', '--out'].includes(key) && args.length, 'unknown/incomplete checker option');
    assert.ok(!Object.hasOwn(options, key), 'duplicate checker option'); options[key] = args.shift();
  }
  assert.ok(localPath(options['--scene']), 'supply site-local --scene');
  for (const key of ['--encoded-sha', '--layout-sha']) assert.match(options[key] || '', /^[0-9a-f]{64}$/);
  const encoded = await readFile(path.join(site, options['--scene'])), compressed = options['--scene'].endsWith('.gz');
  const raw = compressed ? gunzipSync(encoded) : encoded, scene = JSON.parse(raw);
  assert.equal(digest(encoded), options['--encoded-sha']);
  if (compressed || options['--decoded-sha']) assert.equal(digest(raw), options['--decoded-sha']);
  assert.equal(digest(await readFile(path.join(root, scene.layout_report.path))), options['--layout-sha']);
  assert.equal(validateEoereBoltedScene(scene, options['--layout-sha']), EOERE_COUNTS.physical_bolt_axes);
  const rejected = checkRejected(scene, options['--layout-sha']);
  const moduleSource = await readFile(modulePath);
  const THREE = bundle ? await import('data:text/javascript;base64,'+Buffer.concat([moduleSource,
    Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64')) : await import(pathToFileURL(path.resolve(modulePath)).href);
  globalThis.fetch = fileFetch();
  const loaderOptions = {...baselineOptions, url: options['--scene'], expectedSha256: options['--encoded-sha'],
    ...(compressed || options['--decoded-sha'] ? {decodedSha256: options['--decoded-sha']} : {}), layoutSha256: options['--layout-sha']};
  await assert.rejects(loadEoereBoltedScene(THREE, {...loaderOptions, expectedSha256: '0'.repeat(64)}), /scene bytes differ/);
  if (compressed) await assert.rejects(loadEoereBoltedScene(THREE, {...loaderOptions, decodedSha256: '0'.repeat(64)}), /decoded scene bytes differ/);
  const loaded = await loadEoereBoltedScene(THREE, loaderOptions), kinds = verifyLoaded(loaded);
  let authenticatedSharedAssets = 0;
  for (const part of loaded.parts) if (part.path) {
    assert.equal(digest(await readFile(path.join(site, part.path))), part.expected_sha256); authenticatedSharedAssets++;
  }
  const report = {schema: 'eoere_bolted_viewer_validation/v1', candidate: scene.candidate, revision: scene.revision,
    passed: true, loaded_visible_parts: loaded.parts.length, kinds, complete_bolt_axes: EOERE_COUNTS.physical_bolt_axes, factory_holes: EOERE_COUNTS.bracket*8,
    installed_hole_joins: EOERE_COUNTS.bracket*4, authenticated_shared_assets: authenticatedSharedAssets, rejected_invalid_scenes: rejected,
    rejected_encoded_and_decoded_hash_mismatches: true, native_browser_or_webgl_render_tested: false, physical_release: false,
    execution: {actual_argv: process.argv, geometry_module_sha256: digest(moduleSource), bundled: bundle},
    source_sha256: Object.fromEntries(await Promise.all(['site/eoere-bolted-overlay.mjs', 'site/wood-joints-overlay.mjs',
      'site/thin-bolted-overlay.mjs', 'scripts/check_eoere_bolted_scene.mjs', `site/${options['--scene']}`,
      'site/thin-bolted-scene.json.gz', 'site/owner-wood-joints-wj24-scene.json', scene.layout_report.path]
      .map(async p => [p, digest(await readFile(path.join(root, p)))]))),
    limits: 'Source-bound display inventory/transforms and real Three.js geometry; no browser render, mechanics, hardware qualification or physical release.'};
  if (options['--out']) await writeFile(options['--out'], JSON.stringify(report, null, 2)+'\n', {flag: 'wx'});
  console.log(JSON.stringify(report));
  for (const part of loaded.parts) part.geometry?.dispose();
}
