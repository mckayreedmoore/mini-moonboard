// Frozen source/JSON and synthetic ownership controls only; no real Three/CAD/browser.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {gunzipSync} from 'node:zlib';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const own = fileURLToPath(import.meta.url), folder = path.dirname(own);
const root = process.cwd(), packet = path.resolve(folder, '../..');
const rel = value => path.relative(root, value);
const sha = value => createHash('sha256').update(value).digest('hex');
const read = async value => JSON.parse(await readFile(value));
const manifestPath = path.join(packet, 'review-target-v1.json');
const manifestBytes = await readFile(manifestPath), manifest = JSON.parse(manifestBytes);
assert.equal(sha(manifestBytes), '9bd09c57b337c7176d3965e79d620341d2d63b4aeec1b5afbd36d191786f7310');
const pins = {...manifest.files, [rel(manifestPath)]: sha(manifestBytes)};
async function verify() {
  for (const [name, digest] of Object.entries(pins)) assert.equal(sha(await readFile(path.join(root, name))), digest, name);
}
await verify();
const input = await read(path.join(packet, 'inputs.json'));
const exported = await read(path.join(packet, 'runs-v1/export01/export-result.json'));
const layout = await read(path.join(packet, 'runs-v1/export01/layout.json'));
const encoded = await readFile(path.join(root, 'site/eoere-lower-cleat-z180-scene.json.gz'));
const decoded = gunzipSync(encoded), patchData = JSON.parse(decoded);
for (const [name, digest] of Object.entries(exported.source_sha256)) {
  assert.ok(!pins[name] || pins[name] === digest, name); pins[name] = digest;
}
for (const row of Object.values(exported.output)) {
  const bytes = await readFile(path.join(root, row.path));
  assert.equal(bytes.length, row.bytes); assert.equal(sha(bytes), row.sha256);
  pins[row.path] = row.sha256;
}
assert.deepEqual(await readFile(path.join(root, exported.output['scene.json.gz'].path)), encoded);
assert.equal(sha(decoded), exported.scene_decoded_sha256);
assert.equal(patchData.layout_report.sha256, exported.output['layout.json'].sha256);
assert.equal(patchData.layout_report.path, exported.output['layout.json'].path);

// Run only the authenticated exporter's stdlib prepare(), never main/native display.
const python = `import hashlib,importlib.util,json,sys
from pathlib import Path
p=Path(${JSON.stringify(path.join(packet, 'export.py'))})
s=importlib.util.spec_from_file_location('z180_source_only_export_review',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
i,pins,runtime,descriptor,bodies,audit=m.prepare()
b=json.dumps(descriptor,indent=2,sort_keys=True,allow_nan=False).encode()+b'\\n'
assert not any(n=='cadquery' or n=='OCP' or n.startswith('OCP.') for n in sys.modules)
print(json.dumps({'layout_sha256':hashlib.sha256(b).hexdigest(),'pins':pins,'audit':audit,'no_native_imports':True}))
`;
const prepared = JSON.parse(execFileSync(path.join(root, '.venv/bin/python'), ['-B', '-c', python], {
  cwd: root, env: {...process.env, PYTHONDONTWRITEBYTECODE: '1'}, encoding: 'utf8', maxBuffer: 1024*1024,
}));
assert.equal(prepared.layout_sha256, exported.output['layout.json'].sha256);
assert.deepEqual(prepared.pins, exported.source_sha256);
assert.deepEqual(prepared.audit, exported.saved_receiver_audit);
assert.equal(prepared.no_native_imports, true);
assert.equal(layout.axis_changes.length, 4); assert.equal(layout.receiver_datums.length, 8);
assert.deepEqual(layout.release, patchData.release);
assert.ok(Object.values(layout.release).every(value => value === false));
assert.equal(layout.complete_joint_resistance, null); assert.equal(layout.saved_response_transferred, false);
for (const row of patchData.replacements) {
  assert.equal(row.source_brep_sha256, layout.finished_receivers[row.name].sha256);
  assert.deepEqual(row.mesh.bounds_xyz_mm, layout.finished_receivers[row.name].bounds_xyz_mm.flat());
}

const checker = await read(path.join(packet, 'mesh-check-v1.json'));
assert.equal(checker.passed, true);
assert.deepEqual([checker.unchanged_parts, checker.replaced_receivers, checker.translated_bolt_components,
  checker.retained_bolt_axes, checker.retained_Hillman_screws], [997, 4, 20, 100, 66]);
assert.equal(checker.rejected_controls.length, 13); assert.equal(checker.rejected_hash_options, 3);
for (const [name, digest] of Object.entries(checker.source_sha256)) {
  assert.ok(!pins[name] || pins[name] === digest); pins[name] = digest;
}

const loaderPath = path.join(root, 'site/eoere-lower-cleat-z180-overlay.mjs');
const loaderSource = await readFile(loaderPath, 'utf8');
const hosts = patchData.replacements.map(row => row.name);
const axes = patchData.bolt_translations.map(row => row.axis_id), roles = ['shaft', 'head', 'head_washer', 'nut_washer', 'nut'];
let state;
class FakeGeometry {
  constructor(bounds = [0, 38.1, 0, 100, 0, 100]) {
    this.boundingBox = {min: {x: bounds[0], y: bounds[2], z: bounds[4]}, max: {x: bounds[1], y: bounds[3], z: bounds[5]}};
    this.disposals = 0; state.created.push(this);
  }
  computeBoundingBox() {}
  clone() {
    if (++state.clones === state.failClone) throw new Error('synthetic clone failure');
    const b = this.boundingBox;
    return new FakeGeometry([b.min.x, b.max.x, b.min.y, b.max.y, b.min.z, b.max.z]);
  }
  translate(x, y, z) {
    for (const end of ['min', 'max']) for (const [key, value] of Object.entries({x, y, z})) this.boundingBox[end][key] += value;
    this.translation = [x, y, z]; return this;
  }
  dispose() { this.disposals++; }
}
const stubs = {
  sha256: async bytes => sha(Buffer.from(bytes)),
  decodeTypedArray: (base64, type, count) => {
    const bytes = Buffer.from(base64, 'base64'), width = type === 'uint16' ? 2 : 4;
    assert.equal(bytes.length, width*count);
    return {bytes, values: Array.from({length: count}, (_, i) => width === 2 ? bytes.readUInt16LE(i*width) : bytes.readUInt32LE(i*width))};
  },
  meshGeometry: (_three, mesh) => {
    if (++state.meshes === state.failMesh) throw new Error('synthetic mesh failure');
    return new FakeGeometry(mesh.bounds_xyz_mm);
  },
  loadExtendedCleatBaseScene: async (_three, options) => {
    assert.equal(options.url, input.parent_scene.url); assert.equal(options.expectedSha256, input.parent_scene.sha256);
    const parts = hosts.map(name => ({name, path: 'old-path', geometry: new FakeGeometry(), fabrication: {kind: 'timber', description: 'parent'}}));
    for (const axis of axes) for (const role of roles) parts.push({name: `${axis}_${role}`, geometry: new FakeGeometry(),
      fabrication: {kind: 'bolt', connection_name: axis, hardware_role: role, dimensions_mm: [10, 10, 10]}});
    for (let i = parts.length; i < 1021; i++) parts.push({name: `unchanged_${i}`, geometry: new FakeGeometry(), fabrication: {kind: 'context'}});
    state.parent = {parts, design: {key: 'current'}, meta: {planning_mass_kg: 99}};
    return state.parent;
  },
};
globalThis.__z180ReviewStubs = stubs;
const adapted = loaderSource.replace(/^import .*;\n/gm, '')
  + '\nconst {meshGeometry,sha256,decodeTypedArray,loadExtendedCleatBaseScene}=globalThis.__z180ReviewStubs;\n';
const loader = await import('data:text/javascript;base64,' + Buffer.from(adapted).toString('base64'));
globalThis.fetch = async () => new Response(encoded, {status: 200});
const options = {url: 'eoere-lower-cleat-z180-scene.json.gz', expectedSha256: sha(encoded),
  decodedSha256: sha(decoded), layoutSha256: patchData.layout_report.sha256};
state = {created: [], clones: 0, meshes: 0};
const composed = await loader.loadLowerCleatPreviewScene({}, options);
const old = new Map(state.parent.parts.map(part => [part.name, part]));
let retained = 0, replaced = 0, translated = 0;
for (const part of composed.parts) {
  const before = old.get(part.name);
  if (hosts.includes(part.name)) {
    assert.notEqual(part, before); assert.equal(part.path, undefined);
    assert.equal(part.fabrication.lower_cleat_revision, layout.revision);
    assert.equal(before.geometry.disposals, 1); assert.equal(part.geometry.disposals, 0); replaced++;
  } else if (axes.includes(part.fabrication.connection_name)) {
    assert.notEqual(part.geometry, before.geometry); assert.deepEqual(part.geometry.translation, [0, 0, -20]);
    assert.deepEqual(part.fabrication.world_translation_from_Z200_mm, [0, 0, -20]);
    assert.equal(before.geometry.disposals, 1); assert.equal(part.geometry.disposals, 0); translated++;
  } else {
    assert.equal(part, before); assert.equal(part.geometry.disposals, 0); retained++;
  }
}
assert.deepEqual([retained, replaced, translated], [997, 4, 20]);
assert.equal(composed.design.qualified_for_design, false); assert.equal(composed.meta.geometry_adopted, false);
assert.equal(composed.meta.analysis_pass_transferred, false); assert.equal(composed.meta.planning_mass_kg, null);
const ownershipControls = [];
for (const [field, value, error] of [['failMesh', 3, /synthetic mesh failure/], ['failClone', 7, /synthetic clone failure/]]) {
  state = {created: [], clones: 0, meshes: 0, [field]: value};
  await assert.rejects(() => loader.loadLowerCleatPreviewScene({}, options), error);
  assert.ok(state.created.every(g => g.disposals === 1));
  ownershipControls.push({injected_failure: field, all_created_geometries_disposed_once: state.created.length});
}

// Execute only actual routing expressions with inert loaders; compare all old choices to HEAD.
const indexSource = await readFile(path.join(root, 'site/index.html'), 'utf8');
const headIndex = execFileSync('git', ['show', 'HEAD:site/index.html'], {cwd: root, encoding: 'utf8'});
const loaderNames = [...loaderSource.matchAll(/never-match/g)].map(row => row[0]);
const names = ['loadLowerCleatPreviewScene', 'loadExtendedCleat2026Scene', 'loadExtendedCleatBaseScene', 'load2026AdjustmentsScene',
  'loadAdjustedFrameScene', 'loadEoereAlignedWireGzipScene', 'loadEoereCleatTrimScene', 'loadEoereBottomRailScene',
  'loadEoereBoltedScene', 'loadThinBoltedScene', 'loadHL35Scene', 'loadWoodJointScene'];
async function routing(source, model) {
  const start = source.indexOf("        const reviewed = model === 'wood-joints-reviewed';");
  const end = source.indexOf("        document.querySelector('#model-status').textContent", start);
  assert.ok(start >= 0 && end > start);
  const run = new Function('model', 'THREE', 'baselineText', 'sharedMeshes', 'resolveMeshPath', ...names,
    'return (async()=>{' + source.slice(start, end) + '\nreturn data;})()');
  const value = await run(model, {}, '{"parts":[]}', {}, v => v,
    ...names.map(name => async (_three, supplied) => ({loader: name, ...supplied})));
  return Object.fromEntries(['loader', 'url', 'expectedSha256', 'decodedSha256', 'layoutSha256'].map(k => [k, value[k]]));
}
const choices = new Function('return ' + indexSource.match(/const woodJointModels = (\[[\s\S]*?\n      \]);/)[1])();
const route = await routing(indexSource, 'eoere-lower-cleat-z180-development');
assert.equal(route.loader, 'loadLowerCleatPreviewScene'); assert.equal(route.expectedSha256, sha(encoded));
assert.equal(route.decodedSha256, sha(decoded)); assert.equal(route.layoutSha256, patchData.layout_report.sha256);
let oldRoutes = 0;
for (const [model] of choices.filter(([model]) => model !== 'eoere-lower-cleat-z180-development')) {
  assert.deepEqual(await routing(indexSource, model), await routing(headIndex, model), model); oldRoutes++;
}
assert.equal(oldRoutes, 14); assert.equal(loaderNames.length, 0);
assert.ok(indexSource.includes('Current six-case results remain bound to Z200'));
assert.ok(indexSource.includes("const adjustmentModels = ['eoere-adjusted-frame-development', 'eoere-new-2026-adjustments', ...extendedCleatModels];"));
assert.equal(manifest.browser_check_status, 'pending; no browser requested from reviewers');
await verify();
const receipt = {
  schema: 'eoere_lower_cleat_z180_independent_correctness_source_review/v1', findings: [],
  status: 'NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_AND_SYNTHETIC_SCOPE', review_helper_sha256: sha(await readFile(own)),
  target_manifest: {path: rel(manifestPath), sha256: sha(manifestBytes)}, source_sha256: pins,
  sources_unchanged_before_after: true, files_rehashed_before_after: Object.keys(pins).length,
  checks: {exact_source_only_descriptor_replay: true, translated_axes: 4, moved_receiver_bores: 8,
    current_bolt_axes: 100, current_screws: 66, saved_BREP_display_source_bindings: 4,
    reused_actual_Three_mesh_proof: {sha256: manifest.files[rel(path.join(packet, 'mesh-check-v1.json'))], unchanged: 997, receivers: 4, hardware: 20},
    synthetic_composition: {retained, replaced, translated}, synthetic_failure_ownership: ownershipControls,
    actual_source_routing: {new_proposal: route, old_routes_equal_HEAD: oldRoutes, HEAD_index_sha256: sha(headIndex)},
    claim_flags_false: true, current_response_transfer_false: true},
  limits: ['No CAD/OCP/BREP import, tessellation, geometry rebuild, native/FEA/global mechanics or browser run. Python prepare() and the reused saved-result consumer execute stdlib only.',
    'Real Three composition/13 claim mutations/3 hash rejects are authenticated existing evidence; synthetic geometry controls independently check loader ownership, translation dispatch and failure cleanup, without actual mesh regeneration.',
    'Four saved proposed modeled-hole receivers are displayed; uniform maximum-hole results remain separate. Nominal display meshes do not qualify physical fit, drilling, delivered hardware, strength, geometry adoption or climbing.',
    'Current Z200 geometry, 100 axes/66 screws, selected authority and six-case forces retain their source meanings. The separate preview has no transferred response, complete resistance, mass claim or extra grid.',
    'Browser acceptance remains parent-owned and pending in the frozen review target. No browser result is claimed here.'],
};
const out = path.join(folder, 'receipt.json');
await writeFile(out, JSON.stringify(receipt, null, 2) + '\n', {flag: 'wx'});
await verify();
console.log(JSON.stringify({receipt: rel(out), sha256: sha(await readFile(out)), helper_sha256: receipt.review_helper_sha256,
  files: Object.keys(pins).length, findings: 0, oldRoutes, ownershipControls}));
