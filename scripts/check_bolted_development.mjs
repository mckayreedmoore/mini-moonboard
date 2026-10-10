// Fast Git-only identity checks. Full source recovery and mechanics stay separate.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {runInNewContext} from 'node:vm';
import {gunzipSync} from 'node:zlib';
import {validateKickerClearance} from '../site/eoere-kicker-clearance-overlay.mjs';
import {validateUniformChannels} from '../site/eoere-uniform-channels-overlay.mjs';
import {validateSelectedHardware} from '../site/eoere-selected-hardware-overlay.mjs';

export const ROOT = fileURLToPath(new URL('../', import.meta.url));
export const INDEX_PATH = 'docs/bolted-frame-development/development-revisions.json';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const read = name => readFileSync(path.join(ROOT, name));
export const readIndex = () => JSON.parse(read(INDEX_PATH));

function bound(ref) {
  assert.ok(ref && typeof ref.path === 'string' && !path.isAbsolute(ref.path) &&
    !ref.path.split(/[\\/]/).includes('..'), 'repository-relative binding required');
  const bytes = read(ref.path);
  assert.equal(sha(bytes), ref.sha256, `source binding: ${ref.path}`);
  return bytes;
}

export function viewerModel(html, requestedModel) {
  const start = html.indexOf('const woodJointModels =');
  const end = html.indexOf('const modelLabel =', start);
  assert.ok(start >= 0 && end > start, 'viewer model-selection seam missing');
  return runInNewContext(html.slice(start, end) + '\nmodel;', {requestedModel}, {timeout: 1000});
}

export function validateEntry(text, index) {
  assert.equal(text.match(/The current geometry is \*\*`([^`]+)`\*\*/)?.[1],
    index.geometry.revision, 'incoming current geometry differs');
  assert.ok(text.includes(`?model=${index.geometry.viewer}&view=rear`), 'incoming viewer differs');
}

export function validateStructuralAssessment(report, index) {
  assert.equal(report.schema, 'eoere_current_structural_assessment/v1');
  assert.equal(report.geometry_revision, index.geometry.revision);
  assert.equal(report.hardware_revision, index.hardware_model.revision);
  assert.equal(report.assessment_status, 'BOUNDED_ASSESSMENT_COMPLETE_ACCEPTANCE_UNRESOLVED');
  for (const key of ['extra_grid', 'current_response_computed', 'historical_pass_transferred',
    'native_solve_performed', 'cad_rebuilt', 'remedies_attempted', 'geometry_or_hardware_changed',
    'structural_acceptance', 'fabrication_released', 'climbing_released'])
    assert.equal(report[key], false, `assessment boundary: ${key}`);
  assert.equal(report.actual_build_fit_work_excluded_by_owner, true);
  assert.equal(report.actual_observations, null);
  assert.equal(report.thread_method.threshold, .25);
  for (const ref of [index.hardware_model.receipt, index.shop.result, index.shop.overrides[0], index.response.components])
    assert.equal(report.source_sha256[ref.path], ref.sha256, `assessment source: ${ref.path}`);
  bound({path: 'scripts/eoere_structural_assessment.py',
    sha256: report.source_sha256['scripts/eoere_structural_assessment.py']});
  assert.deepEqual(report.preceding_reference_comparisons.recorded_geometry.report, index.response.geometry);
  assert.equal(report.preceding_reference_comparisons.applies_to_current_model, false);
  assert.equal(report.preceding_reference_comparisons.complete_joint_resistance, null);
  assert.ok(report.preceding_reference_comparisons.governing_own_case_witnesses.length > 0);
  assert.ok(report.preceding_reference_comparisons.saved_reference_exceedances.length > 0);
  assert.equal(report.preceding_reference_comparisons.other_saved_exceedance_and_sensitivity_disclosures.length, 6);
  assert.equal(report.thread_stacks.length, 100);
  assert.equal(report.thread_stacks.reduce((n, row) => n + row.members.length, 0), 120);
  assert.ok(report.thread_stacks.every(row => row.actual_thread_fraction === null && row.current_capacity === null));
  const counts = {};
  for (const row of report.thread_stacks)
    counts[row.catalog_envelope_disposition] = (counts[row.catalog_envelope_disposition] || 0) + 1;
  assert.deepEqual(report.thread_catalog_envelope_counts, counts);
  const previousPath = path.posix.join(path.posix.dirname(index.structural_assessment.path), 'mechanics-review.json');
  const previous = JSON.parse(bound({path: previousPath, sha256: report.source_sha256[previousPath]}));
  assert.deepEqual(report.current_unresolved_modes, previous.unresolved);
  assert.ok(report.current_unresolved_modes.every(row => row.current_resistance === null));
  const contact = report.spacer_contact;
  assert.equal(contact.current_resistance, null);
  assert.equal(contact.current_axial_actions, null);
  assert.deepEqual(contact.nominal_projection_areas_mm2, previous.nominal_projection_areas_mm2);
  const pressures = contact.mean_pressure_mpa_per_1000n_centered_axial_force;
  assert.deepEqual(Object.keys(pressures).sort(), Object.keys(contact.nominal_projection_areas_mm2).sort());
  for (const [name, area] of Object.entries(contact.nominal_projection_areas_mm2)) {
    assert.ok(Number.isFinite(area) && area > 0);
    assert.equal(pressures[name], 1000 / area);
  }
}

export function checkDevelopment(index = readIndex()) {
  assert.equal(index.schema, 'bolted_frame_development_revisions/v1');
  assert.equal(index.fabrication_released, false);
  assert.equal(index.climbing_released, false);
  const geometry = JSON.parse(bound(index.geometry.receipt));
  assert.equal(index.candidate, 'compact-bolted-frame-development');
  assert.equal(index.evidence_candidate, geometry.candidate);
  assert.equal(index.geometry.revision, geometry.revision);
  assert.equal(index.optional_grid.default_enabled, false);
  assert.equal(index.optional_grid.official, false);
  assert.equal(JSON.parse(bound(index.optional_grid.receipt)).revision, index.optional_grid.revision);

  const encoded = bound(index.geometry.scene), decoded = gunzipSync(encoded);
  assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
  const scene = validateKickerClearance(JSON.parse(decoded), index.geometry.receipt.sha256);
  assert.deepEqual(scene.layout_report, index.geometry.receipt);
  assert.equal(scene.revision, index.geometry.revision);
  const parentBytes = bound(geometry.parent_geometry), parentGeometry = JSON.parse(parentBytes);
  const parentEncoded = bound({path: `site/${scene.parent_scene.url}`, sha256: scene.parent_scene.sha256});
  const parentDecoded = gunzipSync(parentEncoded);
  assert.equal(sha(parentDecoded), scene.parent_scene.decoded_sha256);
  assert.equal(sha(parentBytes), scene.parent_scene.layout_sha256);
  validateUniformChannels(JSON.parse(parentDecoded), sha(parentBytes));
  assert.deepEqual(geometry.axes, parentGeometry.axes);
  assert.equal(geometry.axes.length, 100);
  assert.equal(geometry.screw_axes.length, 66);
  assert.deepEqual(geometry.moved_screw_axes, scene.moved_screw_axes);
  assert.equal(geometry.analysis_pass_transferred, false);
  assert.ok(Object.values(geometry.release).every(value => value === false));

  const shopGeometry = JSON.parse(bound(index.shop.geometry));
  assert.equal(index.shop.revision, shopGeometry.revision);
  assert.deepEqual(index.shop.geometry, index.geometry.receipt);
  assert.ok(read(index.shop.packet).toString().includes(index.shop.revision), 'shop packet revision differs');
  assert.equal(index.shop.current_channel_drawings_complete, true);
  assert.equal(index.shop.shop_planning_only, true);
  assert.equal(index.shop.hardware_model_updated, true);
  assert.deepEqual(index.shop.screw_datums, geometry.panel_screw_datums);
  bound(index.shop.screw_datums);
  const shop = JSON.parse(bound(index.shop.result));
  assert.equal(shop.schema, 'eoere_current_shop_followup/v1');
  assert.equal(shop.revision, index.geometry.revision);
  assert.deepEqual(shop.current_screw_datums, index.shop.screw_datums);
  assert.deepEqual(shop.counts, {timbers: 22, panels: 6, angles: 22, bolts: 100,
    nuts: 100, washers: 200, Hillman_screws: 66, selected_spacers: 8,
    receiver_occurrences: 120, machining_envelopes: 340, access_sides: 200,
    base_wire_channel_occurrences: 32, changed_bolt_lengths_from_viewer: 32});
  assert.ok(Object.values(shop.release).every(value => value === false));
  const shopDirectory = path.posix.dirname(index.shop.result.path);
  const hardware = shop.files['hardware-selection.csv'];
  assert.deepEqual(index.shop.overrides, [{path: `${shopDirectory}/hardware-selection.csv`, sha256: hardware.sha256}]);
  index.shop.overrides.forEach(bound);
  const hardwareModel = index.hardware_model;
  assert.ok(hardwareModel, 'explicit applied hardware binding required');
  const hardwareGeometry = JSON.parse(bound(hardwareModel.receipt));
  assert.equal(hardwareGeometry.revision, hardwareModel.revision);
  assert.deepEqual(hardwareGeometry.retained_axis_geometry, index.geometry.receipt);
  assert.deepEqual(hardwareModel.wood_screw_geometry, index.geometry.receipt);
  assert.deepEqual(hardwareModel.optional_grid_geometry, index.optional_grid.receipt);
  assert.deepEqual(hardwareModel.shop_override, index.shop.overrides[0]);
  assert.deepEqual(hardwareGeometry.hardware_selection, hardwareModel.shop_override);
  assert.deepEqual(hardwareGeometry.shop_result, index.shop.result);
  assert.equal(hardwareGeometry.selected_hardware_overrides_parent_lengths, true);
  assert.equal(hardwareModel.analysis_pass_transferred, false);
  assert.equal(hardwareModel.actual_parts_verified, false);
  const hardwareEncoded = bound(hardwareModel.scene), hardwareDecoded = gunzipSync(hardwareEncoded);
  assert.equal(sha(hardwareDecoded), hardwareModel.scene.decoded_sha256);
  const hardwareScene = validateSelectedHardware(JSON.parse(hardwareDecoded), hardwareModel.receipt.sha256);
  assert.deepEqual(hardwareScene.selected_stacks, hardwareGeometry.selected_stacks);
  assert.deepEqual(hardwareModel.viewers, hardwareScene.keys);
  assert.equal(hardwareModel.viewers.base, index.geometry.viewer);
  assert.equal(hardwareModel.viewers.extra, index.optional_grid.viewer);
  assert.equal(hardwareScene.parents.base.layout_sha256, index.geometry.receipt.sha256);
  assert.equal(hardwareScene.parents.extra.layout_sha256, index.optional_grid.receipt.sha256);
  for (const [name, record] of Object.entries(shop.files)) {
    assert.equal(path.posix.basename(name), name, 'shop companion must be a filename');
    const bytes = bound({path: `${shopDirectory}/${name}`, sha256: record.sha256});
    assert.equal(bytes.length, record.bytes, `shop size: ${name}`);
  }
  const envelope = JSON.parse(read(`${shopDirectory}/hardware-envelope-review.json`));
  assert.equal(envelope.changed_envelope_count, 48);
  assert.equal(envelope.refined_query_count, 12);
  assert.equal(envelope.all_changed_envelopes_nominally_clear, true);
  assert.equal(envelope.physical_fit_observed, false);
  assert.equal(envelope.hardware_model_updated, false);
  const responseGeometry = JSON.parse(bound(index.response.geometry));
  assert.equal(index.response.revision, responseGeometry.revision);
  assert.notEqual(index.response.revision, index.geometry.revision);
  assert.equal(index.response.applies_to_current_geometry, false);
  const cases = JSON.parse(bound(index.response.cases));
  const components = JSON.parse(bound(index.response.components));
  assert.equal(cases.candidate_geometry_sha256, index.response.geometry.sha256);
  assert.deepEqual(components.current_geometry.report, index.response.geometry);
  validateStructuralAssessment(JSON.parse(bound(index.structural_assessment)), index);
  for (const record of [cases, components, JSON.parse(bound(index.unadopted_proposal.cases))])
    assert.ok(Object.values(record.release).every(value => value === false));
  assert.equal(index.unadopted_proposal.adopted, false);
  const proposal = JSON.parse(bound(index.unadopted_proposal.receipt));
  assert.equal(index.unadopted_proposal.revision, proposal.revision);
  assert.equal(index.evidence_candidate, proposal.candidate);
  assert.notEqual(index.unadopted_proposal.revision, index.geometry.revision);
  read(index.unadopted_proposal.shop_packet);

  const html = read('site/index.html').toString();
  const variants = html.match(/const selectedHardwareModels = (\[[^;]+\]);/)?.[1];
  assert.ok(variants, 'current viewer variant seam missing');
  assert.deepEqual(Array.from(runInNewContext(variants)), [index.geometry.viewer, index.optional_grid.viewer]);
  const baseline = JSON.parse(read(index.selected_baseline.authority));
  assert.equal(index.selected_baseline.authority, 'current-candidate.json');
  assert.equal(index.selected_baseline.candidate, baseline.candidate);
  assert.equal(viewerModel(html, null), baseline.candidate);
  for (const model of [index.geometry.viewer, index.optional_grid.viewer, index.unadopted_proposal.viewer])
    assert.equal(viewerModel(html, model), model, `unknown viewer model: ${model}`);
  assert.ok(html.includes(`href="?model=${index.geometry.viewer}&view=rear">Current eoere geometry`));
  for (const [key, expected] of Object.entries({url: path.basename(hardwareModel.scene.path),
    expectedSha256: hardwareModel.scene.sha256, decodedSha256: hardwareModel.scene.decoded_sha256,
    layoutSha256: hardwareModel.receipt.sha256})) {
    const expression = html.match(new RegExp(`\\b${key}: (selectedHardware \\? .+),\\r?\\n`))?.[1];
    assert.ok(expression, `viewer ${key} binding missing`);
    assert.equal(runInNewContext(`(${expression})`, {selectedHardware: true}, {timeout: 1000}), expected);
  }
  const entries = ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'];
  for (const name of entries) validateEntry(read(name).toString(), index);
  assert.ok(read(entries[2]).toString().trimEnd().split('\n').length <= 150,
    'keep the development entry within 150 lines; link details from the ledger');
  return {passed: true, revision: geometry.revision, shop_revision: shop.revision, response_revision: index.response.revision,
    bolt_axes: geometry.axes.length, screw_axes: geometry.screw_axes.length,
    full_ignored_input_closure_checked: false, mechanics_executed: false};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url))
  console.log(JSON.stringify(checkDevelopment()));
