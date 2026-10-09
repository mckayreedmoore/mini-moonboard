#!/usr/bin/env node
// Executes only the actual inline UI registration, event handlers and loader
// dispatch with DOM/loader stubs. It does not render or regenerate geometry.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const zlib = require('node:zlib');
const cp = require('node:child_process');
const assert = require('node:assert/strict');
const root = cp.execFileSync('git', ['rev-parse', '--show-toplevel'], {encoding: 'utf8'}).trim();
const indexPath = 'site/index.html';
const original = cp.execFileSync('git', ['show', '29404b05:' + indexPath], {encoding: 'utf8'});
const current = fs.readFileSync(path.join(root, indexPath), 'utf8');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function slice(source, start, end) {
  const i = source.indexOf(start), j = source.indexOf(end, i);
  assert(i >= 0 && j > i, `Missing source anchors: ${start}, ${end}`);
  return source.slice(i, j);
}
class Element {
  constructor(tag, text = '', value = '') {
    this.tag = tag; this.textContent = text; this.value = value;
    this.children = []; this.listeners = {}; this.hidden = false;
  }
  add(child) { this.append(child); }
  append(...children) {
    for (const child of children) {
      if (child && typeof child === 'object') {
        if (child.parentElement) child.parentElement.children = child.parentElement.children.filter(row => row !== child);
        child.parentElement = this;
      }
      this.children.push(child);
    }
  }
  prepend(child) { this.append(child); this.children.unshift(this.children.pop()); }
  replaceChildren(...children) { this.children = []; this.append(...children); }
  after() {}
  addEventListener(name, fn) { this.listeners[name] = fn; }
  get lastChild() { return this.children.at(-1); }
  get options() { return this.children.flatMap(child => child.tag === 'option' ? [child] : child.options || []); }
}
function ui(source, requested) {
  const href = `https://example.invalid/index.html?model=${requested}&view=rear&overlay=grid#kept`;
  const nodes = new Map();
  for (const key of ['header', '#model-status']) nodes.set(key, new Element('div'));
  const dimensions = new Element('input'), parent = new Element('label');
  parent.append(dimensions, new Element('text')); nodes.set('#dimensions', dimensions);
  const location = {href, search: new URL(href).search, assign(url) { this.assigned = String(url); }};
  const context = vm.createContext({URL, URLSearchParams, location,
    Option: class extends Element { constructor(text, value) { super('option', text, value); } },
    document: {createElement: tag => new Element(tag), querySelector: query => nodes.get(query)}});
  const code = slice(source, 'const requestedModel =', "if (model !== 'plywood')");
  vm.runInContext(code + '\nglobalThis.reviewUi = {model, isWoodJoint, woodJointModels, modelSelect, updateLabel, updateToggle, updateNote};', context);
  return {state: context.reviewUi, location};
}
async function route(source, model) {
  const context = vm.createContext({model, THREE: {}, baselineText: '{"parts":[]}', sharedMeshes: {},
    resolveMeshPath: value => value, document: {querySelector: () => ({})}});
  for (const name of ['loadExtendedCleatBaseScene', 'loadExtendedCleat2026Scene', 'load2026AdjustmentsScene',
    'loadAdjustedFrameScene', 'loadEoereAlignedWireGzipScene', 'loadEoereCleatTrimScene',
    'loadEoereBottomRailScene', 'loadEoereBoltedScene', 'loadThinBoltedScene', 'loadHL35Scene', 'loadWoodJointScene']) {
    context[name] = async (three, options) => {
      context.selected = {loader: name, options: Object.fromEntries(Object.entries(options).filter(([key]) => key !== 'resolveMeshPath'))};
      return {meta: {}};
    };
  }
  await vm.runInContext('(async () => {' + slice(source, "const reviewed = model === 'wood-joints-reviewed';", 'const mass =') + '})()', context);
  return JSON.parse(JSON.stringify(context.selected));
}
async function main() {
  const oldUi = ui(original, 'eoere-adjusted-frame-development');
  const newUi = ui(current, 'eoere-extended-cleat-frame-development');
  const oldKeys = oldUi.state.woodJointModels.map(row => row[0]);
  const newKeys = newUi.state.woodJointModels.map(row => row[0]);
  assert.deepEqual(Array.from(newKeys.slice(2)), Array.from(oldKeys));
  const historical = [];
  for (const key of oldKeys) {
    const oldRoute = await route(original, key), newRoute = await route(current, key);
    assert.deepEqual(newRoute, oldRoute, key + ' loader dispatch changed');
    const state = ui(current, key).state;
    assert.equal(state.model, key); assert.equal(state.isWoodJoint, true);
    historical.push({model: key, loader: newRoute.loader, unchanged_dispatch: true});
  }
  assert.equal(ui(current, 'unknown-candidate').state.model, ui(original, 'unknown-candidate').state.model);
  const pairs = [
    ['eoere-adjusted-frame-development', 'eoere-new-2026-adjustments'],
    ['eoere-extended-cleat-frame-development', 'eoere-extended-cleat-2026-development']
  ];
  const toggles = [];
  for (const pair of pairs) for (const requested of pair) for (const checked of [false, true]) {
    const {state, location} = ui(current, requested);
    assert.equal(state.model, requested); assert.equal(state.isWoodJoint, true);
    assert.equal(state.updateLabel.hidden, false); assert.equal(state.updateNote.hidden, false);
    assert.equal(state.updateToggle.checked, requested === pair[1]);
    state.updateToggle.checked = checked; state.updateToggle.listeners.change();
    const url = new URL(location.assigned);
    assert.equal(url.searchParams.get('model'), pair[checked ? 1 : 0]);
    assert.equal(url.searchParams.get('view'), 'rear'); assert.equal(url.searchParams.get('overlay'), 'grid');
    assert.equal(url.hash, '#kept');
    toggles.push({from: requested, checked, to: url.searchParams.get('model'), other_url_state_retained: true});
  }
  const selectorTargets = [...pairs.flat(), 'eoere-bolted-aligned-wire-development', 'compact-floor-flush-development'];
  for (const key of selectorTargets) {
    const {state, location} = ui(current, pairs[1][0]);
    assert(state.modelSelect.options.some(option => option.value === key));
    state.modelSelect.value = key; state.modelSelect.listeners.change();
    const url = new URL(location.assigned);
    assert.equal(url.searchParams.get('model'), key); assert.equal(url.searchParams.get('view'), 'rear');
    assert.equal(url.searchParams.get('overlay'), 'grid'); assert.equal(url.hash, '#kept');
  }
  assert.equal(ui(current, 'eoere-bolted-aligned-wire-development').state.updateLabel.hidden, true);
  const patchFile = 'site/eoere-cleat-extension-scene.json.gz';
  const layoutFile = 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json';
  const patch = fs.readFileSync(path.join(root, patchFile));
  const decoded = zlib.gunzipSync(patch), patchData = JSON.parse(decoded);
  const currentRoutes = [];
  for (const [key, loader] of [[pairs[1][0], 'loadExtendedCleatBaseScene'], [pairs[1][1], 'loadExtendedCleat2026Scene']]) {
    const selected = await route(current, key);
    assert.equal(selected.loader, loader);
    assert.equal(selected.options.url, path.basename(patchFile));
    assert.equal(selected.options.expectedSha256, sha(patch));
    assert.equal(selected.options.decodedSha256, sha(decoded));
    assert.equal(selected.options.layoutSha256, sha(fs.readFileSync(path.join(root, layoutFile))));
    currentRoutes.push({model: key, loader, patch_binding_verified: true});
  }
  assert.equal(patchData.replacements.length, 2);
  assert.equal(patchData.analysis_pass_transferred, false);
  assert(Object.values(patchData.release).every(value => value === false));
  const sourceFiles = [indexPath, 'site/eoere-cleat-extension-overlay.mjs', patchFile, layoutFile,
    'site/eoere-2026-adjustments-overlay.mjs', 'site/eoere-adjusted-base-v3-scene.json.gz',
    'site/eoere-2026-adjustments-v3-scene.json.gz', 'scripts/check_eoere_cleat_extension_browser.cjs', 'docs/wood-joints-mvp/README.md',
    'docs/wood-joints-mvp/completion-ledger.md',
    'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-top-extension-review-v1/actual-output-review.json',
    'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-top-extension-v1/actual-mesh-check-v1.json'];
  const source_sha256 = Object.fromEntries(sourceFiles.map(file => [file, sha(fs.readFileSync(path.join(root, file)))]));
  assert.equal(source_sha256[indexPath], sha(current), 'index changed during review');
  assert.equal(source_sha256['site/eoere-cleat-extension-overlay.mjs'], '69f4887ac83af89169f56f8d1bcbae406856d6f00b6eb467fbc337cf52680bfd');
  assert.equal(source_sha256['site/eoere-adjusted-base-v3-scene.json.gz'], 'd77b9923b7d0df6b3416b2938b2d249a5406a9174fe98fba5118c341bc3df947');
  assert.equal(source_sha256['site/eoere-2026-adjustments-v3-scene.json.gz'], '8682bf9a81c0bf8e7ffb23c3f6725adc6d3c9bd4728b00e50edb696ca3305d1d');
  const result = {schema: 'independent_extended_cleat_integration_correctness_review/v1',
    status: 'PASS_SOURCE_LEVEL_UI_INTEGRATION_ONLY', baseline_commit: '29404b05',
    baseline_index_sha256: sha(original), source_sha256, review_helper_sha256: sha(fs.readFileSync(__filename)),
    historical_dispatch: historical, new_dispatch: currentRoutes, toggle_transitions: toggles,
    selector_targets_verified: selectorTargets, invalid_model_fallback_preserved: true,
    substantial_findings: [],
    manual_review: ['New keys use isWoodJoint baseline/loading/error paths.',
      'Replacement cleats retain named ownership; no integration-specific filters omit them.',
      'Both new status strings retain unevaluated strength/installation and optional positions remain unofficial.',
      'Scene-load and part-load failures retain the existing HOLD/unavailable messages.'],
    limits: ['Source-level DOM and loader stubs only; no browser, WebGL or rendering execution.',
      'Existing frozen saved-solid and real Three.js receipts reused without rerunning their methods.',
      'No CAD, native mechanics, geometry generation, installation or engineering capacity review.',
      'Parent owns browser validation and publication; this receipt grants no build or structural acceptance.'],
    mechanics_acceptance: false, physical_release: false, node_version: process.version,
    command: ['node', path.relative(root, __filename)]};
  fs.writeFileSync(path.join(__dirname, 'receipt.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({status: result.status, index_sha256: source_sha256[indexPath], historical_dispatch_count: historical.length,
    toggle_transition_count: toggles.length, substantial_findings: result.substantial_findings}));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
