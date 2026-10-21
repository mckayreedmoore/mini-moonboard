import assert from 'node:assert/strict';
import {existsSync, readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {fileURLToPath} from 'node:url';
import {runInNewContext} from 'node:vm';
import {documentsForModel, resolveDocumentPath} from '../site/documentation-links.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const html = readFileSync(path.join(root, 'site/index.html'), 'utf8');
const index = JSON.parse(readFileSync(path.join(root, 'docs/bolted-frame-development/development-revisions.json')));
let responseIndex = index;
while (responseIndex.preceding_revision) responseIndex = responseIndex.preceding_revision;

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
  const models = [index.geometry.viewer, index.optional_grid.viewer, responseIndex.unadopted_proposal.viewer,
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
    if ([index.geometry.viewer, index.optional_grid.viewer].includes(model)) {
      if (model === index.optional_grid.viewer)
        assert.ok(rows.some(r => r.path === responseIndex.current_response.cases.path));
      else assert.ok(rows.some(r => r.path.endsWith('#single-bolt-leg-joint-review')));
      const receipt = model === index.geometry.viewer ? index.geometry.receipt : index.optional_grid.receipt;
      assert.ok(rows.some(r => r.path === receipt.path));
      assert.ok(rows.some(r => r.path === 'docs/bolted-frame-development/builder-plan.md'));
      if (model === index.optional_grid.viewer) assert.ok(rows.some(r => /extra grid off/.test(r.label)));
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
  const current = render(index.geometry.viewer), optional = render(index.optional_grid.viewer);
  assert.match(current, /Single-bolt leg joints.*24 angles.*96 bolt stacks/);
  assert.match(current, /66 Hillman axes retained/);
  assert.match(current, /strength, joint response and installation remain unqualified/);
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
