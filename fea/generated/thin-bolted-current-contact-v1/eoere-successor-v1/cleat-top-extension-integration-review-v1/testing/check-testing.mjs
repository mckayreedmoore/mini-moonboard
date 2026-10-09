// Cheap independent integration review: no CAD, Three construction, or browser run.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {createHash, webcrypto} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import vm from 'node:vm';
import {validateCleatExtension, loadExtendedCleatBaseScene} from '../../../../../../site/eoere-cleat-extension-overlay.mjs';

globalThis.crypto ??= webcrypto;
const ROOT = 'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1';
const DRAFT = `${ROOT}/cleat-top-extension-v1`;
const DOC = 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json';
const self = `${ROOT}/cleat-top-extension-integration-review-v1/testing/check-testing.mjs`;
const receiptPath = process.argv[2];
assert.ok(receiptPath, 'fresh receipt path required');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const files = [self, 'site/index.html', 'site/eoere-cleat-extension-overlay.mjs', 'site/eoere-cleat-extension-scene.json.gz',
  'site/eoere-2026-adjustments-overlay.mjs', 'site/wood-joints-overlay.mjs',
  'site/eoere-adjusted-base-v3-scene.json.gz', 'site/eoere-2026-adjustments-v3-scene.json.gz', DOC,
  'scripts/check_eoere_cleat_extension_browser.cjs', `${DRAFT}/eoere-cleat-extension-overlay.mjs`,
  `${DRAFT}/cad-v1/geometry.json`, `${DRAFT}/cad-v1/scene.json.gz`, `${DRAFT}/check-viewer.mjs`,
  `${DRAFT}/actual-mesh-check-v1.json`, `${ROOT}/cleat-top-extension-review-v1/actual-output-review.json`,
  `${ROOT}/2026-adjustments-v10/actual-mesh-check-v1.json`, `${ROOT}/2026-adjustments-v10/browser-v1/result.json`];
const bytes = Object.fromEntries(await Promise.all(files.map(async file => [file, await readFile(file)])));
const source_sha256 = Object.fromEntries(files.map(file => [file, hash(bytes[file])]));
assert.deepEqual(bytes['site/eoere-cleat-extension-overlay.mjs'], bytes[`${DRAFT}/eoere-cleat-extension-overlay.mjs`]);
assert.deepEqual(bytes['site/eoere-cleat-extension-scene.json.gz'], bytes[`${DRAFT}/cad-v1/scene.json.gz`]);
assert.deepEqual(bytes[DOC], bytes[`${DRAFT}/cad-v1/geometry.json`]);
const decoded = gunzipSync(bytes['site/eoere-cleat-extension-scene.json.gz']);
const patch = JSON.parse(decoded), geometry = JSON.parse(bytes[DOC]);
assert.equal(hash(decoded), '6c39b4a240f8033491bbd43c437d60dc888c524e90b350e53351eaf28ddc5db6');
assert.equal(hash(bytes['site/eoere-cleat-extension-scene.json.gz']), 'ae6315463f0482597075a769ad3ee55630b4c8b430c2ae93137c5232cc6dbb54');
assert.equal(hash(bytes[DOC]), '01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d');
validateCleatExtension(patch, hash(bytes[DOC]));
assert.deepEqual(geometry.release, patch.release);
assert.deepEqual(Object.keys(patch.release).sort(), ['candidate_accepted', 'capacity_established', 'climbing_released',
  'complete_joint_acceptance', 'fabrication_released', 'structural_released'].sort());
assert.ok(Object.values(patch.release).every(value => value === false));

const meshProof = JSON.parse(bytes[`${DRAFT}/actual-mesh-check-v1.json`]);
const solidProof = JSON.parse(bytes[`${ROOT}/cleat-top-extension-review-v1/actual-output-review.json`]);
assert.equal(meshProof.status, 'PASS_DISPLAY_AND_FROZEN_PARENT_BINDINGS_ONLY');
assert.deepEqual(meshProof.variants, [
  {variant: 'base', total: 1021, unchanged_parts: 1019, replacement_cleats: 2},
  {variant: 'extra', total: 1380, unchanged_parts: 1378, replacement_cleats: 2}]);
assert.equal(meshProof.rejected_guards.length, 10);
for (const file of [`${DRAFT}/eoere-cleat-extension-overlay.mjs`, `${DRAFT}/cad-v1/geometry.json`,
  `${DRAFT}/cad-v1/scene.json.gz`, `${DRAFT}/check-viewer.mjs`]) assert.equal(meshProof.source_sha256[file], source_sha256[file]);
assert.equal(solidProof.status, 'PASS_NOMINAL_SAVED_GEOMETRY_ONLY');
assert.equal(solidProof.producer_source_pin_count_verified, 581);
assert.equal(solidProof.saved_solids_imported, 6);
assert.equal(solidProof.body_checks.length, 2);
assert.equal(solidProof.bore_and_land_checks.length, 8);
assert.equal(solidProof.viewer_mesh_checks.length, 2);
assert.ok(solidProof.sole_two_cleat_replacements && solidProof.both_parent_variant_bindings_verified);
assert.equal(solidProof.current_v3_axes_canonical_sha256, geometry.base_100_axis_records_canonical_sha256);
assert.equal(solidProof.current_v3_screw_axes_canonical_sha256, geometry.base_66_screw_records_canonical_sha256);
assert.equal(geometry.axes.length, 100);
assert.equal(geometry.screw_axes.length, 66);
assert.equal(meshProof.physical_release, false);
assert.equal(meshProof.mechanics_acceptance, false);
assert.equal(solidProof.analysis_pass_transferred, false);
assert.equal(solidProof.physical_release, false);
assert.equal(solidProof.mechanics_or_global_rebuild_run, false);

const html = bytes['site/index.html'].toString();
const prior = execFileSync('git', ['show', '29404b05:site/index.html'], {encoding: 'utf8'});
const v3MeshProof = JSON.parse(bytes[`${ROOT}/2026-adjustments-v10/actual-mesh-check-v1.json`]);
const v3BrowserProof = JSON.parse(bytes[`${ROOT}/2026-adjustments-v10/browser-v1/result.json`]);
assert.equal(v3MeshProof.passed, true);
assert.equal(v3MeshProof.retained_bolt_axes, 100);
assert.equal(v3MeshProof.retained_Hillman_screws, 66);
assert.equal(v3MeshProof.visible_parts, 1380);
assert.equal(v3BrowserProof.passed, true);
assert.deepEqual(v3BrowserProof.page_errors, []);
assert.deepEqual(v3BrowserProof.failed_requests_or_responses, []);
assert.equal(v3BrowserProof.source_sha256['site/index.html'], hash(Buffer.from(prior)));
assert.notEqual(v3BrowserProof.source_sha256['site/index.html'], source_sha256['site/index.html']);
for (const proof of [v3MeshProof, v3BrowserProof]) {
  for (const file of ['site/eoere-2026-adjustments-overlay.mjs', 'site/eoere-2026-adjustments-v3-scene.json.gz'])
    assert.equal(proof.source_sha256[file], source_sha256[file]);
  assert.equal(proof.mechanics_or_physical_release, false);
}
assert.equal(v3BrowserProof.source_sha256['site/eoere-adjusted-base-v3-scene.json.gz'], source_sha256['site/eoere-adjusted-base-v3-scene.json.gz']);
const choiceArray = text => vm.runInNewContext(text.match(/const woodJointModels = (\[[\s\S]*?\n\s*\]);/)[1]);
const choices = choiceArray(html), historicalChoices = choiceArray(prior);
const newKeys = ['eoere-extended-cleat-frame-development', 'eoere-extended-cleat-2026-development'];
assert.deepEqual(Array.from(choices, row => row[0]).slice(0, 2), newKeys);
assert.deepEqual(Array.from(choices, row => row[0]).slice(2), Array.from(historicalChoices, row => row[0]));
assert.equal(new Set(choices.map(row => row[0])).size, choices.length);
const routing = text => text.slice(text.indexOf("const reviewed = model === 'wood-joints-reviewed';"),
  text.indexOf("document.querySelector('#model-status').textContent =", text.indexOf("const reviewed = model === 'wood-joints-reviewed';")));
const loaderNames = ['loadExtendedCleat2026Scene', 'loadExtendedCleatBaseScene', 'load2026AdjustmentsScene',
  'loadAdjustedFrameScene', 'loadEoereAlignedWireGzipScene', 'loadEoereCleatTrimScene', 'loadEoereBottomRailScene',
  'loadEoereBoltedScene', 'loadThinBoltedScene', 'loadHL35Scene', 'loadWoodJointScene'];
async function resolveRoute(text, model) {
  const context = {model, THREE: {}, baselineText: '{"parts":[]}', sharedMeshes: {}, resolveMeshPath: value => value};
  for (const name of loaderNames) context[name] = async (_, options) => ({loader: name, options});
  return vm.runInNewContext(`(async () => {${routing(text)} return data;})()`, context);
}
const routes = [];
for (const model of newKeys) {
  const route = await resolveRoute(html, model);
  assert.equal(route.loader, model === newKeys[0] ? 'loadExtendedCleatBaseScene' : 'loadExtendedCleat2026Scene');
  assert.equal(route.options.url, 'eoere-cleat-extension-scene.json.gz');
  assert.equal(route.options.expectedSha256, source_sha256['site/eoere-cleat-extension-scene.json.gz']);
  assert.equal(route.options.decodedSha256, hash(decoded));
  assert.equal(route.options.layoutSha256, source_sha256[DOC]);
  routes.push({model, loader: route.loader, url: route.options.url});
}
for (const [model] of historicalChoices) {
  const current = await resolveRoute(html, model), old = await resolveRoute(prior, model);
  assert.equal(current.loader, old.loader, model);
  for (const key of ['url', 'expectedSha256', 'decodedSha256', 'layoutSha256']) assert.equal(current.options[key], old.options[key], `${model}/${key}`);
}

const extensionModelsDeclaration = html.match(/const extendedCleatModels = \[[^;]+;/)[0];
const toggleHandler = html.slice(html.indexOf("updateToggle.addEventListener('change', () => {"), html.indexOf("      if (model !== 'plywood')"));
const toggle_routes = [];
for (const model of [...newKeys, 'eoere-adjusted-frame-development', 'eoere-new-2026-adjustments']) {
  for (const checked of [false, true]) {
    let callback, target;
    const initial = `https://example.test/index.html?model=${model}&view=rear&overlay=grid-high`;
    vm.runInNewContext(`${extensionModelsDeclaration}\n${toggleHandler}`, {model, URL,
      updateToggle: {checked, addEventListener: (_, fn) => {callback = fn;}},
      location: {href: initial, assign: value => {target = new URL(value);}}});
    callback();
    const expectedPair = newKeys.includes(model) ? newKeys : ['eoere-adjusted-frame-development', 'eoere-new-2026-adjustments'];
    assert.equal(target.searchParams.get('model'), expectedPair[checked ? 1 : 0]);
    assert.equal(target.searchParams.get('view'), 'rear');
    assert.equal(target.searchParams.get('overlay'), 'grid-high');
    toggle_routes.push({from: model, checked, to: target.searchParams.get('model')});
  }
}

const rejected_guards = [];
const controls = [
  ['candidate', data => {data.candidate = 'other';}], ['revision', data => {data.revision = 'other';}],
  ['status', data => {data.status = 'PASS';}], ['layout path', data => {data.layout_report.path = 'other';}],
  ['layout hash', data => {data.layout_report.sha256 = '0'.repeat(64);}],
  ['missing cleat', data => {data.replacements.pop();}], ['duplicate cleat', data => {data.replacements[1] = data.replacements[0];}],
  ['non-cleat owner', data => {data.replacements[0].name = 'base_side_left';}],
  ['indirect mesh', data => {data.replacements[0].transform = Array(16).fill(0);}],
  ['template mesh', data => {data.replacements[0].template_id = 'template';}],
  ['mechanics ready', data => {data.mechanics_ready = true;}], ['analysis pass transfer', data => {data.analysis_pass_transferred = true;}],
  ['body restriction', data => {data.only_two_cleat_bodies_changed = false;}],
  ['retained harness', data => {data.base_and_extra_harness_retained = false;}]
];
for (const variant of ['base', 'extra']) {
  for (const key of ['url', 'sha256', 'decoded_sha256', 'layout_sha256']) controls.push([`${variant} parent ${key}`, data => {data.parent_scenes[variant][key] = 'other';}]);
  for (const key of ['physical_bolt_axes', 'screw', 'wire', 'total_visible_parts']) controls.push([`${variant} census ${key}`, data => {data.counts[variant][key]--; }]);
}
for (const key of Object.keys(patch.release)) controls.push([`release ${key}`, data => {data.release[key] = true;}]);
for (const [name, mutate] of controls) {
  const data = structuredClone(patch); mutate(data);
  assert.throws(() => validateCleatExtension(data, source_sha256[DOC]), undefined, name);
  rejected_guards.push(name);
}
const options = {url: 'isolated-fixture', expectedSha256: source_sha256['site/eoere-cleat-extension-scene.json.gz'],
  decodedSha256: hash(decoded), layoutSha256: source_sha256[DOC]};
const originalFetch = globalThis.fetch;
try {
  globalThis.fetch = async () => new Response('missing', {status: 404});
  await assert.rejects(loadExtendedCleatBaseScene({}, options), /scene request failed/);
  rejected_guards.push('failed HTTP response');
  globalThis.fetch = async () => new Response(new Uint8Array([1, 2, 3]), {status: 200});
  await assert.rejects(loadExtendedCleatBaseScene({}, options), /compressed bytes differ/);
  rejected_guards.push('compressed bytes mismatch');
  globalThis.fetch = async () => new Response(bytes['site/eoere-cleat-extension-scene.json.gz'], {status: 200});
  await assert.rejects(loadExtendedCleatBaseScene({}, {...options, decodedSha256: '0'.repeat(64)}), /decoded bytes differ/);
  rejected_guards.push('decoded bytes mismatch');
  await assert.rejects(loadExtendedCleatBaseScene({}, {...options, layoutSha256: '0'.repeat(64)}), /geometry binding required/);
  rejected_guards.push('supplied layout binding mismatch');
} finally {globalThis.fetch = originalFetch;}
for (const file of files) assert.equal(hash(await readFile(file)), source_sha256[file], `source changed during review: ${file}`);
const receipt = {schema: 'eoere_cleat_extension_integration_testing_review/v1', status: 'PASS_ISOLATED_BINDING_AND_ROUTING_CHECKS',
  findings: [], source_sha256, source_base_commit: '29404b05', site_copies_byte_identical_to_frozen_reviewed_inputs: true,
  loader_routes: routes, all_12_historical_wood_joint_loader_routes_retained: true, toggle_routes,
  rejected_guards, reused_proofs: {saved_solids: solidProof.status, real_three: meshProof.status,
    variants: meshProof.variants, prior_guard_count: meshProof.rejected_guards.length,
    v3_actual_mesh_still_binds_unchanged_parent_sources: true,
    v3_browser_binds_only_pre_extension_index_at_base_commit: true},
  checks_not_rerun: ['CAD/BRep', 'Three construction', 'browser captures', 'native/global mechanics', 'install', 'full suite'],
  limits: ['Parent owns complete source-bank reauthentication and final browser/publication validation.',
    'Isolated route assertions execute site source with stub loaders; mesh and geometry claims use the byte-bound existing proofs.',
    'No capacity, fabrication, structural, climbing or physical release established.'],
  node_version: process.version, command: process.argv};
await writeFile(receiptPath, JSON.stringify(receipt, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({receipt: receiptPath, sha256: hash(await readFile(receiptPath)), rejected_guards: rejected_guards.length, findings: []}));
