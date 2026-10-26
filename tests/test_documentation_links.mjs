import assert from 'node:assert/strict';
import {existsSync, readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {fileURLToPath} from 'node:url';
import {runInNewContext} from 'node:vm';
import {documentsForModel, resolveDocumentPath} from '../site/documentation-links.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const html = readFileSync(path.join(root, 'site/index.html'), 'utf8');
const currentIndex = JSON.parse(readFileSync(path.join(root, 'docs/bolted-frame-development/development-revisions.json')));
// Preserve Candidate13's own document contract through later development revisions.
let index = currentIndex;
while (index && index.geometry.revision !== 'eoere-candidate13-side-depth-v10') index = index.preceding_revision;
assert.ok(index, 'preserved Candidate13 document authority required');
let responseIndex = index;
while (responseIndex.preceding_revision) responseIndex = responseIndex.preceding_revision;
let optionalIndex = index;
while (!optionalIndex.optional_grid) optionalIndex = optionalIndex.preceding_revision;

function slice(first, last) {
  const start = html.indexOf(first), end = html.indexOf(last, start);
  assert.ok(start >= 0 && end > start, `viewer seam: ${first}`);
  return html.slice(start, end);
}

function checkTarget(target) {
  const url = new URL(target, 'https://repository.invalid/');
  if (url.origin !== 'https://repository.invalid') return;
  const file = path.join(root, decodeURIComponent(url.pathname));
  assert.ok(existsSync(file), `missing document: ${target}`);
  if (url.hash && file.endsWith('.md')) {
    const text = readFileSync(file, 'utf8');
    const ids = [...text.matchAll(/\bid=["']([^"']+)["']/g)].map(m => m[1]);
    const counts = new Map();
    for (const match of text.matchAll(/^#{1,6}\s+(.+?)\s*#*$/gm)) {
      const slug = match[1].replace(/<[^>]*>/g, '').toLowerCase()
        .replace(/[^\p{L}\p{N}\p{M}_ -]/gu, '').replace(/ /g, '-');
      const count = counts.get(slug) || 0;
      ids.push(slug + (count ? `-${count}` : '')); counts.set(slug, count + 1);
    }
    assert.ok(ids.includes(decodeURIComponent(url.hash.slice(1))), `missing fragment: ${target}`);
  }
}

test('historical routing preserves fragments, queries and unrelated document identities', () => {
  assert.equal(resolveDocumentPath('docs/compact-splice-study.md#results'), 'docs/history/compact-splice-study.md#results');
  assert.equal(resolveDocumentPath('docs/round-service-build-plan.md?plain=1#stock'), 'docs/history/round-service-build-plan.md?plain=1#stock');
  for (const target of ['docs/material-costs.md', 'docs/history/compact-splice-study.md',
    'docs/bolted-frame-development/README.md', 'https://example.com/docs/compact-splice-study.md'])
    assert.equal(resolveDocumentPath(target), target);
});

test('preserved packer-free menu binds its own geometry, bank, evaluation and method summary', () => {
  let evaluated = currentIndex;
  while (evaluated.geometry.revision !== 'v10-packer-free-flush-return-far-row-only-v1')
    evaluated = evaluated.preceding_revision;
  const rows = documentsForModel(evaluated.geometry.viewer);
  for (const ref of [evaluated.geometry.receipt, evaluated.response_bank,
    evaluated.engineering_review, evaluated.connection_method_evaluation]) {
    assert.ok(rows.some(row => row.path === ref.path), `missing current packer-free record: ${ref.path}`);
    checkTarget(ref.path);
  }
});

test('current V9 restoration menu exposes its fixed geometry and own conditional analysis', () => {
  assert.equal(currentIndex.geometry.viewer, 'eoere-v11-v9-eight-bolt-preview');
  assert.equal(currentIndex.response_bank.path,
    'docs/bolted-frame-development/owner-frame-v11/response-bank.json');
  const rows = documentsForModel(currentIndex.geometry.viewer);
  for (const target of [currentIndex.owner_request.path, currentIndex.response_bank.path,
    'docs/bolted-frame-development/owner-frame-v11/reference-review.json',
    'docs/bolted-frame-development/owner-frame-v11/connection-capacity-followthrough.json',
    'docs/bolted-frame-development/owner-frame-v11/grade5-property-comparison.json',
    'docs/bolted-frame-development/owner-frame-v11/geometry-applicability.json',
    'docs/bolted-frame-development/owner-frame-v11/component-reference-summary.json',
    'docs/bolted-frame-development/README.md',
    'docs/bolted-frame-development/builder-plan.md']) {
    assert.ok(rows.some(row => row.path === target));
    checkTarget(target);
  }
  assert.ok(rows.some(row => /geometry-only/.test(row.label)));
  assert.ok(rows.every(row => !/analysis pending/i.test(row.label)));
});

test('rendered historical model menus resolve their actual document paths', () => {
  const menu = slice('const woodJointModels =', 'const modelLabel =');
  const navigation = slice("if (['horizontal-service-development'", '// Loose padding');
  const models = runInNewContext(menu + '\n[...squareModels, ...woodJointModels].map(r => r[0]);', {requestedModel: null});
  let links = 0;
  for (const model of models) {
    const anchors = [];
    const document = {
      createElement(tag) {
        const node = {style: {}, setAttribute() {}, append() {}};
        if (tag === 'a') anchors.push(node);
        return node;
      },
      querySelector() { return {after() {}}; },
    };
    runInNewContext(menu + navigation, {requestedModel: model, document, resolveDocumentPath});
    for (const anchor of anchors) {
      const prefix = 'https://github.com/mckayreedmoore/mini-moonboard/blob/master/';
      assert.ok(anchor.href.startsWith(prefix));
      checkTarget(anchor.href.slice(prefix.length)); links++;
    }
  }
  assert.ok(links >= 50, 'historical document menus must be exercised');
});

test('current and unadopted menus expose their own shop records and response bindings', () => {
  const documents = slice('const v4Documents =', 'const first =');
  const models = [index.geometry.viewer, optionalIndex.optional_grid.viewer, responseIndex.unadopted_proposal.viewer,
    'wood-joints-reviewed', 'wood-joints-working-proposal', 'bolted-v4-development',
    'owner-corner-layout', 'owner-barrel-layout',
    ...runInNewContext(slice('const woodJointModels =', 'const modelLabel =') + '\nwoodJointModels.map(r => r[0]);', {requestedModel: null})];
  assert.match(html, /from '\.\/documentation-links\.mjs'/);
  assert.match(documents, /documentsForModel\(model, design\.documents\)/);
  for (const model of new Set(models)) {
    const scenes = {'hl35-development': 'hl35-candidate-scene.json',
      'hl35-fit-development': 'hl35-final-scene.json', 'hl35-counterbore-development': 'hl35-counterbore-scene.json'};
    const recorded = scenes[model]
      ? JSON.parse(readFileSync(path.join(root, 'site', scenes[model]))).design.documents
      : [{label: 'Historical source', path: 'docs/history/README.md'}];
    const rows = runInNewContext(documents + '\ndocuments;', {model, design: {documents: recorded}, documentsForModel});
    assert.ok(rows.length >= (scenes[model] ? 2 : 3), `missing menu: ${model}`);
    for (const row of rows) checkTarget(resolveDocumentPath(row.path));
    assert.ok(rows.every(r => r.label !== 'Current development ledger'));
    if ([index.geometry.viewer, optionalIndex.optional_grid.viewer].includes(model)) {
      if (model === optionalIndex.optional_grid.viewer)
        assert.ok(rows.some(r => r.path === responseIndex.current_response.cases.path));
      else assert.ok(rows.some(r => r.path.endsWith('#current-v10-candidate13')));
      const receipt = model === index.geometry.viewer ? index.geometry.receipt : optionalIndex.optional_grid.receipt;
      assert.ok(rows.some(r => r.path === receipt.path));
      assert.ok(rows.some(r => r.path === 'docs/bolted-frame-development/builder-plan.md'));
      if (model === optionalIndex.optional_grid.viewer) assert.ok(rows.some(r => /extra grid off/.test(r.label)));
    }
  }
  const recorded = [{label: 'Earlier own record', path: 'docs/history/README.md'}];
  assert.equal(documentsForModel('unlisted-historical-model', recorded), recorded);
  for (const model of ['eoere-bolted-development', 'eoere-bolted-bottom-rail-development', 'eoere-bolted-aligned-wire-development']) {
    const rows = documentsForModel(model, [{label: 'Current joint evidence', path: 'docs/wood-joints-mvp/completion-ledger.md#build-package-completion'}]);
    assert.ok(rows.some(r => r.path.endsWith('.json')));
    assert.ok(rows.every(r => !r.path.endsWith('#build-package-completion')));
  }
});

test('loaded viewer status distinguishes completed current cases, optional grid and proposal', () => {
  const flags = slice("const reviewed = model ===", 'const sceneLoader =');
  const status = slice("document.querySelector('#model-status').textContent = narrowChannels", 'const mass = data.meta');
  function render(model) {
    const node = {};
    runInNewContext(flags + status, {model, document: {querySelector() { return node; }}});
    return node.textContent;
  }
  const current = render(index.geometry.viewer), optional = render(optionalIndex.optional_grid.viewer);
  const v9 = render('eoere-owner-frame-v9-development');
  assert.match(current, /V10 Candidate 13.*116 bolt stacks.*66 Hillman screws/);
  assert.match(current, /Two glued nominal ½-inch leaves per cleat/);
  assert.match(current, /Own six 250 lb cases and independent replays recorded/);
  assert.match(current, /Twenty-six trial bearing flags remain across 13 components/);
  assert.match(current, /No fabrication or climbing release/);
  assert.equal(render('eoere-owner-frame-v10-development'), current);
  assert.match(v9, /Preserved V9 96-bolt frame.*flat cleat sides without tabs or steps/);
  assert.match(v9, /Own six 250 lb cases replayed; exceeded bolt and top-rail references are deferred/);
  assert.match(v9, /Two upper bolts at each cleat and each center principal\/header connection/);
  assert.match(v9, /Heads outside and nuts inside on 40 side\/top stacks/);
  assert.match(v9, /Eight cleat stacks now use 7½-inch A574 bolts and one 1-inch factory spacer each; 16 spacers total/);
  assert.match(v9, /Inset angles, timber holes and 66 screws remain/);
  assert.match(v9, /actual fit and complete joint strength remain unqualified/);
  assert.match(render('eoere-owner-frame-v8-development'), /Preserved 96-bolt frame.*Eight connected base\/header angles and their 24 shared bolt axes are inset 6 mm/);
  assert.match(v9, /No fabrication or climbing release/);
  assert.match(render('eoere-owner-frame-v6-development'), /Preserved 96-bolt frame.*Six 250 lb cases evaluated/);
  assert.match(render('eoere-owner-frame-v4-development'), /Preserved 92-bolt frame.*24 angles.*66 Hillman/);
  assert.match(render('eoere-owner-frame-v3-development'), /Preserved 92-bolt frame before the lower-front-hole move/);
  const previous = render('eoere-leg-header-frame-development');
  assert.match(previous, /Single-bolt leg joints.*24 angles.*96 bolt stacks/);
  assert.match(previous, /66 Hillman axes retained/);
  assert.match(render('eoere-enclosed-passages-frame-development'), /Solid 4×6 outer kicker posts/);
  assert.match(optional, /Optional expanded grid on/);
  const proposal = render(responseIndex.unadopted_proposal.viewer);
  assert.match(proposal, /Six separate own-case first-order results and component references are complete/);
  assert.match(proposal, /do not select this proposal or transfer to current Z200/);
  assert.match(render('hl35-counterbore-development'), /Preserved HL35/);
});

test('unavailable exports replace geometry-preview claims with an explicit load status', () => {
  const failure = slice('rejectOwnerConceptBaseline?.(error);', "if (model === 'bolted-v4-development')").replace(/\}\);\s*$/, '');
  for (const [model, isWoodJoint, expected] of [
    ['2x10', false, /Historical export unavailable.*original exports need recovery/],
    ['compact-floor-flush-development', false, /Model compact-floor-flush-development unavailable/],
    [index.geometry.viewer, true, /Wood-joint scene unavailable.*source identity must match/],
  ]) {
    const status = {}, weightLine = {};
    runInNewContext(failure, {model, isWoodJoint, error: new Error('HTTP 404'),
      rejectOwnerConceptBaseline: null, partCard: {}, holdStatus: {}, weightLine,
      document: {querySelector() { return status; }}});
    assert.match(status.textContent, expected);
    assert.equal(weightLine.textContent, 'Planning mass: unavailable');
  }
});

for (const failureFirst of [false, true]) for (const weightsAvailable of [false, true])
test(`weight response ${failureFirst ? 'after' : 'before'} a failed model (${weightsAvailable ? 'available' : 'unavailable'} metadata) retains the load error`, async () => {
  const weights = slice('const designLabels = ', 'const categoryLabels = ');
  const failure = slice('rejectOwnerConceptBaseline?.(error);', "if (model === 'bolted-v4-development')").replace(/\}\);\s*$/, '');
  let resolveResponse;
  const response = new Promise(resolve => {resolveResponse = resolve;});
  const weightLine = {}, status = {};
  const model = 'compact-floor-flush-development';
  const context = {model, isWoodJoint: false, woodJointModels: [],
    modelSelect: {options: [{value: model, text: 'Selected baseline'}]},
    weightLine, weightNote: {}, excludedMass: 'visual accessories',
    fetch: () => response, error: new Error('HTTP 404'),
    rejectOwnerConceptBaseline: null, partCard: {}, holdStatus: {},
    document: {querySelector() {return status;}}};
  runInNewContext(weights + `\nglobalThis.failModel = () => {${failure}};`, context);
  if (failureFirst) context.failModel();
  const catalog = JSON.parse(readFileSync(path.join(root, 'site/prototype-weights.json')));
  resolveResponse({ok: weightsAvailable, status: 404, json: async () => catalog});
  // Let the actual fetch/json/then/catch chain settle, with no timing delay.
  await new Promise(setImmediate);
  if (!failureFirst) {
    assert.match(weightLine.textContent, /^Estimated frame weight:/, 'weight callback ran');
    context.failModel();
  }
  assert.match(context.modelSelect.options[0].text, /kg|weight unavailable/, 'menu metadata still loads');
  assert.match(status.textContent, /Model compact-floor-flush-development unavailable/);
  assert.equal(weightLine.textContent, 'Planning mass: unavailable');
});

test('historical post comparison initializes beside browser globals and responds to its controls', () => {
  const page = readFileSync(path.join(root, 'site/post-connection-options.html'), 'utf8');
  const script = page.match(/<script>([\s\S]*?)<\/script>/)?.[1];
  assert.ok(script, 'historical comparison script');
  const nodes = new Map();
  for (const id of ['current', 'move', 'block', 'bearing', 'shift', 'duration',
    'bound', 'shift-label', 'depth', 'allowance', 'ratio', 'result-note']) {
    nodes.set(id, {value: id === 'shift' ? '40.7' : id === 'duration' ? '1.25' : '',
      listeners: {}, addEventListener(event, callback) { this.listeners[event] = callback; }});
  }
  // Represent window.top's existing global binding; VM contexts alone allow
  // lexical names that a browser's nonconfigurable Window properties reject.
  runInNewContext('var top;\n' + script, {document: {getElementById(id) {
    assert.ok(nodes.has(id), `unknown chart element: ${id}`); return nodes.get(id);
  }}});
  for (const id of ['current', 'move', 'block', 'bearing'])
    assert.match(nodes.get(id).innerHTML, /<circle /, `${id} diagram initialized`);
  const metric = id => parseFloat(nodes.get(id).textContent);
  const moved = nodes.get('move').innerHTML;
  nodes.get('shift').value = '0'; nodes.get('shift').listeners.input();
  assert.ok(metric('ratio') > 1, 'original position exceeds the saved scalar reference');
  assert.notEqual(nodes.get('move').innerHTML, moved, 'slider redraws the moved pair');
  const shortDuration = metric('ratio');
  nodes.get('duration').value = '1'; nodes.get('duration').listeners.change();
  assert.ok(metric('ratio') > shortDuration, 'duration changes the displayed comparison');
  nodes.get('bound').listeners.click();
  assert.ok(Number(nodes.get('shift').value) > 0, 'bound control moves the slider');
  assert.ok(metric('ratio') <= 1, 'bound control reaches the saved scalar reference');
  assert.match(nodes.get('result-note').textContent, /Whole-joint feasibility and acceptance remain open/);
});
