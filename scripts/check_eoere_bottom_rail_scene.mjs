// Default: changed-partition fixtures on genuine existing Three.js geometry.
// --fixtures [--bundle /existing/viewer-bundle.js] [--actual-mesh] [--out ignored/review.json]
// [--bundle] /existing/three.js --scene site-local.json.gz
//   --encoded-sha SHA --decoded-sha SHA --layout-sha SHA [--out ignored/review.json]
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash, webcrypto} from 'node:crypto';
import {gzipSync, gunzipSync} from 'node:zlib';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';
import {loadEoereBottomRailScene, validateEoereBottomRailScene, EOERE_BOTTOM_RAIL_BASE,
  EOERE_BOTTOM_RAIL_REVISION, EOERE_BOTTOM_RAIL_COUNTS, EOERE_BOTTOM_RAIL_REPLACED_SHARED} from '../site/eoere-bottom-rail-overlay.mjs';

const root = fileURLToPath(new URL('../', import.meta.url)), site = path.join(root, 'site');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const defaultBundle = '.venv/lib/python3.12/site-packages/ocp_vscode/static/js/three-cad-viewer.esm.js';
const actualMeshFixture = {url: 'eoere-bottom-rail-scene.json.gz',
  sha256: '28269c01354dd901ad87604fe80475fcbb19cf71ad6cebec29194e7fe94cf536',
  decoded_sha256: '7e01f4d4cf96c7ab5f2a4ccfb8e0404a7b460a50e23b308138bdd1a0d38d1087'};
const oldPins = {'site/eoere-bolted-overlay.mjs': 'f6aa64bc76df378800289fbb6846455d581f2f5d5d447f2e3079dbb67b780341',
  'scripts/check_eoere_bolted_scene.mjs': '0a99aa51bb0a0026544d2a7af74f0c99276a0db771c1ab185e99dac246702ad9',
  'site/eoere-review-scene.json.gz': EOERE_BOTTOM_RAIL_BASE.sha256};
globalThis.crypto ??= webcrypto;

function localPath(value) {
  return typeof value === 'string' && !value.startsWith('/') && !value.includes('\\') && !value.includes(':') &&
    !value.split('/').some(part => !part || part === '.' || part === '..');
}

async function verify(pins) {
  for (const [name, hash] of Object.entries(pins)) assert.equal(digest(await readFile(path.join(root, name))), hash, name);
}

async function pinsFor(names) {
  return Object.fromEntries(await Promise.all(names.map(async name => [name, digest(await readFile(path.join(root, name)))])));
}

function fileFetch(memory = new Map()) {
  return async url => {
    assert.ok(localPath(url), 'site-local source fetch required');
    return new Response(memory.has(url) ? memory.get(url) : await readFile(path.join(site, url)), {status: 200});
  };
}

async function geometryModule(modulePath, bundle) {
  const source = await readFile(modulePath);
  const THREE = bundle ? await import('data:text/javascript;base64,'+Buffer.concat([source,
    Buffer.from('\nexport {BufferGeometry, BufferAttribute, Matrix4};\n')]).toString('base64')) :
    await import(pathToFileURL(path.resolve(modulePath)).href);
  assert.equal(typeof THREE.BufferGeometry, 'function');
  return {THREE, module_sha256: digest(source), module_path: modulePath, bundled: bundle};
}

function checkLoaded(loaded) {
  const census = {timber: 22, panel: 6, bracket: 22, bolt: 500, screw: 66, wire: 131, light: 132, tnut: 142};
  assert.equal(loaded.parts.length, 1021);
  assert.equal(new Set(loaded.parts.map(part => part.name)).size, 1021);
  assert.deepEqual(Object.fromEntries(Object.keys(census).map(kind => [kind,
    loaded.parts.filter(part => part.fabrication.kind === kind).length])), census);
  assert.equal(new Set(loaded.parts.filter(part => part.fabrication.kind === 'bolt')
    .map(part => part.fabrication.connection_name)).size, 100);
  assert.equal(loaded.meta.shared_parts_reused, 471); assert.equal(loaded.meta.own_new_solids, 550);
  assert.equal(loaded.meta.physical_release, false); assert.equal(loaded.meta.planning_mass_kg, null);
  assert.equal(loaded.design.qualified_for_design, false);
  assert.equal(loaded.meta.revision, EOERE_BOTTOM_RAIL_REVISION);
  for (const part of loaded.parts) {
    assert.ok(part.fabrication.dimensions_mm.length === 3 && part.fabrication.dimensions_mm.every(v => Number.isFinite(v) && v >= 0));
    if (part.geometry) assert.ok([...part.geometry.getAttribute('position').array].every(Number.isFinite));
  }
  assert.ok(loaded.bounds_mm.flat().every(Number.isFinite));
  return census;
}

function fixtureScene(old, thin) {
  const vertices = Buffer.alloc(24), triangles = Buffer.alloc(24);
  [0, 0, 0, 10, 0, 0, 0, 10, 0, 0, 0, 10].forEach((v, i) => vertices.writeInt16LE(v, i*2));
  [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3].forEach((v, i) => triangles.writeUInt16LE(v, i*2));
  const topology = digest(triangles), mesh = {encoding: 'base64_typed_arrays_le_v1', bounds_xyz_mm: [0, 1, 0, 1, 0, 1],
    vertex_component_type: 'int16', triangle_component_type: 'uint16', vertex_count: 4, triangle_count: 4,
    vertex_quantization_mm: .1, vertex_max_euclidean_error_mm: 0, vertices_base64: vertices.toString('base64'),
    triangle_topology_sha256: topology};
  const replaced = new Set(EOERE_BOTTOM_RAIL_REPLACED_SHARED);
  const rows = [...old.solids, ...thin.solids.filter(row => replaced.has(row.name))];
  assert.equal(rows.length, 550);
  const solids = rows.map((row, i) => ({id: row.id, name: row.name, template_id: 'tiny',
    transform: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 5000+i*2, 0, 0, 1],
    fabrication: structuredClone(row.fabrication)}));
  // Exercise inline meshes alongside shared template clones.
  solids[0] = {...solids[0], mesh: structuredClone(mesh)};
  delete solids[0].template_id; delete solids[0].transform;
  return {schema: 'eoere_bolted_review_scene/v1', candidate: old.candidate, revision: EOERE_BOTTOM_RAIL_REVISION,
    status: 'REVISE_UNQUALIFIED_PROPOSAL', base_scene: {...EOERE_BOTTOM_RAIL_BASE}, shared_scene: {...old.shared_scene},
    layout_report: {path: 'synthetic/bottom-rail-layout.json', sha256: '1'.repeat(64)},
    baseline_manifest_sha256: old.baseline_manifest_sha256, counts: {...EOERE_BOTTOM_RAIL_COUNTS},
    retained_shared_part_names: old.retained_shared_part_names.filter(name => !replaced.has(name)),
    retained_parent_service_names: [...old.retained_parent_service_names], solids,
    factory_angle_holes: structuredClone(old.factory_angle_holes), mesh_templates: {tiny: {id: 'tiny', mesh}},
    triangle_topologies: {[topology]: {triangle_count: 4, triangle_component_type: 'uint16', index_count: 12,
      triangle_indices_base64: triangles.toString('base64')}}, release: {...old.release}, mechanics_ready: false,
    design: {key: 'eoere-bolted-bottom-rail-development', qualified_for_design: false,
      description: 'Synthetic changed-mesh fixture; no new candidate CAD or mechanics'}};
}

async function runFixtures(THREE, baselineOptions, actualData) {
  const old = JSON.parse(gunzipSync(await readFile(path.join(site, EOERE_BOTTOM_RAIL_BASE.url))));
  const thin = JSON.parse(gunzipSync(await readFile(path.join(site, old.shared_scene.url))));
  const scene = fixtureScene(old, thin), priorFetch = globalThis.fetch, tracked = new Set(), disposal = new Map();
  class TrackedGeometry extends THREE.BufferGeometry {
    constructor() { super(); tracked.add(this); }
    dispose() { disposal.set(this, (disposal.get(this) || 0)+1); return super.dispose(); }
  }
  const realThree = {...THREE, BufferGeometry: TrackedGeometry};
  const disposeLoaded = loaded => { for (const geometry of new Set(loaded.parts.map(part => part.geometry).filter(Boolean))) geometry.dispose(); };
  const assertClean = () => {
    assert.ok(tracked.size > 0);
    for (const geometry of tracked) assert.equal(disposal.get(geometry), 1, 'every allocated real geometry disposed exactly once');
    tracked.clear(); disposal.clear();
  };
  const optionsFor = (data, gzip = false) => {
    const raw = Buffer.from(JSON.stringify(data)), encoded = gzip ? gzipSync(raw) : raw;
    const url = gzip ? 'bottom-rail-fixture.json.gz' : 'bottom-rail-fixture.json';
    globalThis.fetch = fileFetch(new Map([[url, encoded]]));
    return {...baselineOptions, url, expectedSha256: digest(encoded), decodedSha256: digest(raw), layoutSha256: '1'.repeat(64)};
  };
  const rejected = [];
  try {
    assert.equal(validateEoereBottomRailScene(scene, '1'.repeat(64)), 100);
    for (const gzip of [false, true]) {
      const loaded = await loadEoereBottomRailScene(realThree, optionsFor(scene, gzip));
      checkLoaded(loaded);
      assert.ok(loaded.bounds_mm[1][0] >= 6099, 'new geometry expands conservative display bounds');
      const changed = new Set(EOERE_BOTTOM_RAIL_REPLACED_SHARED);
      assert.equal(loaded.parts.filter(part => changed.has(part.name)).length, 6);
      assert.equal(loaded.parts.filter(part => part.fabrication.layer === 'eoere_bottom_rail_candidate').length, 550);
      disposeLoaded(loaded); assertClean();
    }
    for (const [name, mutate, message] of [
      ['changed-preserved-partition', data => { data.retained_shared_part_names[0] = old.solids[0].name; }, /exact preserved 471/],
      ['missing-new-panel', data => { data.solids.splice(data.solids.findIndex(row => row.name === 'main_lower_left'), 1); }, /owned mesh inventory/],
      ['released', data => { data.release.fabrication_released = true; }, /qualification flags/],
      ['bad-new-mesh-only', data => { data.solids[0].mesh.vertices_base64 = 'AA=='; }, /encoded component length/],
    ]) {
      const invalid = structuredClone(scene); mutate(invalid);
      await assert.rejects(loadEoereBottomRailScene(realThree, optionsFor(invalid)), message);
      if (tracked.size) assertClean(); rejected.push(name);
    }
    const options = optionsFor(scene, true);
    await assert.rejects(loadEoereBottomRailScene(realThree, {...options, expectedSha256: '0'.repeat(64)}), /new scene bytes differ/);
    await assert.rejects(loadEoereBottomRailScene(realThree, {...options, decodedSha256: '0'.repeat(64)}), /new decoded scene bytes differ/);
    assert.equal(tracked.size, 0);
    if (actualData) {
      const actual = structuredClone(scene), changed = new Set(EOERE_BOTTOM_RAIL_REPLACED_SHARED);
      const rows = actualData.solids.filter(row => changed.has(row.name));
      assert.equal(rows.length, 6);
      for (const row of rows) {
        const fixture = actual.solids.find(part => part.name === row.name);
        fixture.mesh = structuredClone(row.mesh); delete fixture.template_id; delete fixture.transform;
        assert.equal(actualData.triangle_topologies[row.mesh.triangle_topology_sha256], undefined,
          'regression uses the six actual inline meshes absent from the topology table');
        assert.ok(row.mesh.triangle_indices_base64);
      }
      const loaded = await loadEoereBottomRailScene(realThree, optionsFor(actual));
      checkLoaded(loaded); disposeLoaded(loaded); assertClean();
      for (const [name, mutate, message] of [
        ['actual-inline-topology-corrupted', mesh => {
          const bytes = Buffer.from(mesh.triangle_indices_base64, 'base64'); bytes[0] ^= 1;
          mesh.triangle_indices_base64 = bytes.toString('base64');
        }, /inline topology bytes differ/],
        ['actual-inline-topology-missing', mesh => { delete mesh.triangle_indices_base64; }, /missing or mismatched topology/],
      ]) {
        const invalid = structuredClone(actual);
        mutate(invalid.solids.find(row => row.name === 'main_lower_left').mesh);
        await assert.rejects(loadEoereBottomRailScene(realThree, optionsFor(invalid)), message);
        assertClean(); rejected.push(name);
      }
    }
  } finally { globalThis.fetch = priorFetch; }
  return {fixture_changed_partition_validated: true, plain_and_gzip_verified: true, rejected,
    encoded_and_decoded_hash_rejections: true, all_allocated_geometry_disposed_once_on_success_and_error: true,
    actual_six_inline_meshes_and_missing_table_regression_verified: Boolean(actualData),
    new_geometry_expands_conservative_bounds: true, preserved_parts: 471, new_owned_solids: 550, visible_parts: 1021,
    complete_physical_shafts: 100, Hillman_screws: 66, factory_holes: 176};
}

const args = process.argv.slice(2), fixtures = !args.length || args[0] === '--fixtures';
if (args[0] === '--fixtures') args.shift();
let modulePath = fixtures ? defaultBundle : args.shift(), bundle = fixtures;
if (args[0] === '--bundle' && fixtures) { args.shift(); modulePath = args.shift(); }
else if (modulePath === '--bundle') { bundle = true; modulePath = args.shift(); }
assert.ok(modulePath, 'existing Three.js module or viewer bundle required');
const options = {};
while (args.length) {
  const key = args.shift();
  if (fixtures && key === '--actual-mesh') {
    assert.ok(!Object.hasOwn(options, key), 'duplicate actual-mesh fixture option'); options[key] = true; continue;
  }
  assert.ok((fixtures ? ['--out'] : ['--scene', '--encoded-sha', '--decoded-sha', '--layout-sha', '--out']).includes(key) && args.length,
    'unknown or incomplete checker option');
  assert.ok(!Object.hasOwn(options, key), 'duplicate checker option'); options[key] = args.shift();
}
await verify(oldPins);
const baselineText = await readFile(path.join(site, 'hybrid/compact-floor-flush-kerf-right/parts.json'), 'utf8');
const aliases = JSON.parse(await readFile(path.join(site, 'mesh-aliases.json'), 'utf8')).aliases;
const baselineOptions = {baselineParts: JSON.parse(baselineText).parts, baselineText, resolveMeshPath: value => aliases[value] || value};
const module = await geometryModule(modulePath, bundle);
const sourceNames = ['site/eoere-bottom-rail-overlay.mjs', 'scripts/check_eoere_bottom_rail_scene.mjs', ...Object.keys(oldPins),
  'site/wood-joints-overlay.mjs', 'site/thin-bolted-overlay.mjs', 'site/thin-bolted-scene.json.gz',
  'site/owner-wood-joints-wj24-scene.json', 'site/hybrid/compact-floor-flush-kerf-right/parts.json', 'site/mesh-aliases.json'];
let report;
if (fixtures) {
  let actualData;
  if (options['--actual-mesh']) {
    const encoded = await readFile(path.join(site, actualMeshFixture.url)), raw = gunzipSync(encoded);
    assert.equal(digest(encoded), actualMeshFixture.sha256); assert.equal(digest(raw), actualMeshFixture.decoded_sha256);
    actualData = JSON.parse(raw);
    sourceNames.push(`site/${actualMeshFixture.url}`);
  }
  const before = await pinsFor(sourceNames);
  report = {schema: 'eoere_bottom_rail_loader_method_fixture/v1', passed: true,
    ...await runFixtures(module.THREE, baselineOptions, actualData), source_sha256: before};
  await verify(before);
} else {
  assert.ok(localPath(options['--scene']), 'site-local new scene required');
  for (const key of ['--encoded-sha', '--layout-sha']) assert.match(options[key] || '', /^[0-9a-f]{64}$/);
  const encoded = await readFile(path.join(site, options['--scene'])), compressed = options['--scene'].endsWith('.gz');
  const raw = compressed ? gunzipSync(encoded) : encoded, scene = JSON.parse(raw);
  assert.equal(digest(encoded), options['--encoded-sha']);
  if (compressed || options['--decoded-sha']) assert.equal(digest(raw), options['--decoded-sha']);
  assert.equal(validateEoereBottomRailScene(scene, options['--layout-sha']), 100);
  assert.equal(digest(await readFile(path.join(root, scene.layout_report.path))), options['--layout-sha']);
  const before = await pinsFor([...sourceNames, `site/${options['--scene']}`, scene.layout_report.path]);
  const priorFetch = globalThis.fetch;
  globalThis.fetch = fileFetch();
  let loaded;
  try {
    loaded = await loadEoereBottomRailScene(module.THREE, {...baselineOptions, url: options['--scene'],
      expectedSha256: options['--encoded-sha'], ...(compressed || options['--decoded-sha'] ? {decodedSha256: options['--decoded-sha']} : {}),
      layoutSha256: options['--layout-sha']});
    const kinds = checkLoaded(loaded);
    let authenticatedSharedAssets = 0;
    for (const part of loaded.parts) if (part.path) {
      assert.equal(digest(await readFile(path.join(site, part.path))), part.expected_sha256); authenticatedSharedAssets++;
    }
    await verify(before);
    report = {schema: 'eoere_bottom_rail_scene_cpu_validation/v1', candidate: scene.candidate, revision: scene.revision,
      passed: true, kinds, visible_parts: loaded.parts.length, preserved_parts: 471, new_owned_solids: 550,
      complete_physical_shafts: 100, Hillman_screws: 66, factory_holes: 176, installed_hole_joins: 88,
      authenticated_shared_assets: authenticatedSharedAssets, source_sha256: before};
  } finally {
    globalThis.fetch = priorFetch;
    if (loaded) for (const geometry of new Set(loaded.parts.map(part => part.geometry).filter(Boolean))) geometry.dispose();
  }
}
await verify(oldPins);
report.execution = {actual_argv: process.argv, geometry_module_sha256: module.module_sha256,
  geometry_module_path: module.module_path, bundled: module.bundled, node: process.version};
report.real_Three_cpu_geometry_tested = true;
report.browser_or_WebGL_render_tested = false;
report.candidate_CAD_query_q_K_mechanics_or_native = false;
report.physical_release = false;
report.limits = 'Source-bound display partition, mesh/hash/transform and CPU Three.js checks only; no new geometry adoption, lower-gap remedy, mechanical qualification or release.';
if (options['--out']) await writeFile(options['--out'], JSON.stringify(report, null, 2)+'\n', {flag: 'wx'});
console.log(JSON.stringify(report));
