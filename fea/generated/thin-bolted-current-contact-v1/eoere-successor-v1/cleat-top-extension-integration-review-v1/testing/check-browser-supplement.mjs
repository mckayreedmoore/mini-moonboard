// Bounded source/receipt review only. Does not launch a browser or alter evidence.
import assert from 'node:assert/strict';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const root = 'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1';
const review = `${root}/cleat-top-extension-integration-review-v1/testing`;
const self = `${review}/check-browser-supplement.mjs`;
const browserPath = `${root}/cleat-top-extension-v1/browser-v3/result.json`;
const output = process.argv[2]; assert.ok(output, 'new receipt path required');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const priorBytes = await readFile(`${review}/result-v2.json`), prior = JSON.parse(priorBytes);
const stableFiles = ['site/index.html', 'site/eoere-cleat-extension-overlay.mjs', 'site/eoere-cleat-extension-scene.json.gz',
  'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json'];
const files = [...stableFiles, 'scripts/check_eoere_cleat_extension_browser.cjs', self];
const bytes = Object.fromEntries(await Promise.all(files.map(async file => [file, await readFile(file)])));
const source_sha256 = Object.fromEntries(files.map(file => [file, sha(bytes[file])]));
for (const file of stableFiles) assert.equal(source_sha256[file], prior.source_sha256[file], file);
const source = bytes['scripts/check_eoere_cleat_extension_browser.cjs'].toString();
for (const token of ["page.setDefaultTimeout(120000)", "url.searchParams.set('model', baseModel)",
  "url.searchParams.set('view', 'rear')", "await page.locator('#update-2026').check(); await ready(extraModel",
  "await page.locator('#update-2026').uncheck(); await ready(baseModel", "new_pair_toggle_off_on_off: true",
  "preserved_v3_options_present: true", "unofficial_label_verified: true", "assert.deepEqual(errors, [])",
  "assert.deepEqual(failed, [])", "page_context_code_evaluation: false", "mechanics_or_physical_release: false"])
  assert.ok(source.includes(token), token);
for (const unsupportedClaim of ['new_pair_toggle_on_off_on:', 'preserved_v3_pair_toggle:']) assert.ok(!source.includes(unsupportedClaim));
assert.ok(!source.includes("page.locator('#person')") && !source.includes("page.locator('#dimensions')"));
assert.ok(!source.includes("page.locator('#model').selectOption"));
let actual_browser = {path: browserPath, completed: false};
try {
  const resultBytes = await readFile(browserPath), result = JSON.parse(resultBytes);
  assert.equal(result.passed, true);
  assert.equal(result.new_pair_toggle_off_on_off, true);
  assert.equal(result.preserved_v3_options_present, true);
  assert.equal(result.unofficial_label_verified, true);
  assert.equal(result.page_context_code_evaluation, false);
  assert.equal(result.mechanics_or_physical_release, false);
  assert.deepEqual(result.page_errors, []); assert.deepEqual(result.failed_requests_or_responses, []);
  assert.deepEqual(result.navigation.map(row => row.model), ['eoere-extended-cleat-frame-development',
    'eoere-extended-cleat-2026-development', 'eoere-extended-cleat-frame-development']);
  assert.deepEqual(result.captures.map(row => [row.model, row.view]), [
    ['eoere-extended-cleat-frame-development', 'rear'], ['eoere-extended-cleat-2026-development', 'rear']]);
  for (const [file, expected] of Object.entries(result.source_sha256)) assert.equal(source_sha256[file], expected, file);
  for (const capture of result.captures) assert.equal(sha(await readFile(capture.screenshot.path)), capture.screenshot.sha256);
  assert.equal(sha(await readFile(result.shared_runner.path)), result.shared_runner.sha256);
  actual_browser = {path: browserPath, completed: true, sha256: sha(resultBytes),
    captures: result.captures.map(row => ({model: row.model, view: row.view, screenshot: row.screenshot})),
    navigation_models: result.navigation.map(row => row.model)};
} catch (error) {if (error.code !== 'ENOENT') throw error;}
for (const file of files) assert.equal(sha(await readFile(file)), source_sha256[file], file);
const receipt = {schema: 'eoere_cleat_extension_bounded_browser_testing_supplement/v1',
  status: actual_browser.completed ? 'PASS_SOURCE_COVERAGE_AND_COMPLETED_BROWSER_BINDINGS' : 'PASS_SOURCE_COVERAGE_BROWSER_RESULT_PENDING',
  findings: [], source_sha256, production_sources_unchanged_from_independent_testing_review: true,
  prior_testing_receipt: {path: `${review}/result-v2.json`, sha256: sha(priorBytes), retained_coverage: 'Eight pair-routing cases, twelve historical dispatch routes, forty rejected controls and source-bound saved/v3 proofs.'},
  reviewed_runtime_coverage: ['New base rear load', 'Checkbox ON loads new extra mode', 'Rear captures of both new modes',
    'Checkbox OFF returns to new base', 'Current link, unofficial label and four preserved model options',
    'One canvas and ninety-nine representative bolt options on each loaded mode', 'No page errors or failed non-favicon responses'],
  boundaries: ['No front capture, person/dimension interaction, historical runtime navigation or old-pair runtime toggle claimed by this bounded helper.',
    'Initial served index response is hashed; subsequent capture index hashes reuse that digest and the unchanged local index check.',
    'No new browser/CAD/native run performed by this review; no mechanics or physical release.'], actual_browser,
  node_version: process.version, command: process.argv};
await writeFile(output, JSON.stringify(receipt, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({receipt: output, sha256: sha(await readFile(output)), status: receipt.status, findings: []}));
