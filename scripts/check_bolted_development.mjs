// Fast Git-only identity checks. Full source recovery and mechanics stay separate.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {runInNewContext} from 'node:vm';
import {isDeepStrictEqual} from 'node:util';
import {gunzipSync} from 'node:zlib';
import {validatePackerFreeProvenance, validatePackerFreeDelta, PACKER_FREE_MODEL,
  PACKER_FREE_REVISION} from '../site/eoere-packer-free-overlay.mjs';
import {validatePackerFreeResults, PACKER_FREE_RESULTS_ASSET} from '../site/eoere-packer-free-results.mjs';
import {validateCenterFarRowScene, validateCenterFarRowProvenance, CENTER_FAR_ROW_MODEL,
  CENTER_FAR_ROW_REVISION, CENTER_FAR_ROW_ASSETS} from '../site/eoere-center-far-row-overlay.mjs';
import {validateKickerClearance} from '../site/eoere-kicker-clearance-overlay.mjs';
import {validateUniformChannels} from '../site/eoere-uniform-channels-overlay.mjs';
import {validateSelectedHardware} from '../site/eoere-selected-hardware-overlay.mjs';
import {validateFrontPosts} from '../site/eoere-front-posts-4x6-overlay.mjs';
import {validateNarrowChannels} from '../site/eoere-narrow-channels-overlay.mjs';
import {validateEnclosedPassages} from '../site/eoere-enclosed-passages-overlay.mjs';
import {validateLegHeader} from '../site/eoere-leg-header-overlay.mjs';
import {validatePairedFrame} from '../site/eoere-paired-frame-overlay.mjs';
import {validateRetainedFrame} from '../site/eoere-retained-frame-overlay.mjs';
import {validateOwnerFrame} from '../site/eoere-owner-frame-overlay.mjs';
import {validateReferenceCleats} from '../site/eoere-reference-cleat-overlay.mjs';
import {validatePrincipalPairs} from '../site/eoere-principal-pair-overlay.mjs';
import {validateInwardBolts} from '../site/eoere-inward-bolts-overlay.mjs';
import {validateInwardAngles} from '../site/eoere-inward-angles-overlay.mjs';
import {validateSingleSpacers} from '../site/eoere-single-spacer-overlay.mjs';
import {validateStandardStockProvenance, validateStandardStockScene} from '../site/eoere-standard-stock-overlay.mjs';
import {validateV10Provenance, resolveV10SourceRef, validateV10SceneProvenance, V10_PROVENANCE_SHA256,
  V10_SCENE, V10_REVISION as V10_CANDIDATE13_REVISION, V10_COUNTS as V10_CANDIDATE13_COUNTS} from '../site/eoere-v10-provenance.mjs';

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
  const selection = index.development_selection;
  assert.equal(text.match(/The current geometry is \*\*`([^`]+)`\*\*/)?.[1],
    selection?.revision ?? index.geometry.revision, 'incoming current geometry differs');
  assert.ok(text.includes(`?model=${selection?.viewer?.model ?? index.geometry.viewer}&view=rear`), 'incoming viewer differs');
}

export function validateCurrent96Review(report, index) {
  assert.equal(report.schema, 'eoere_current96_exceedance_review/v1');
  assert.equal(report.geometry_revision, index.geometry.revision);
  assert.deepEqual(report.physical_geometry, index.geometry.receipt);
  assert.equal(report.case_count, 6);
  assert.deepEqual([...report.case_ids].sort(),
    ['a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'].sort());
  assert.ok(report.analysis_geometry.path.includes('/owner-principal-pairs-v6/analysis-v1/'));
  assert.match(report.analysis_geometry.sha256, /^[a-f0-9]{64}$/);
  assert.equal(report.current_response_computed, true);
  assert.deepEqual(report.load_contract, {input_weight: 250, input_unit: 'lb',
    downward_multiplier: 2, horizontal_force_n: 300, duration_factor_CD: 1});
  for (const [key, count] of Object.entries({current_bolts: 96, ordinary_bolts: 84,
    dedicated_bolts: 12, sawn_timber_members: 20, bonded_plywood_hosts: 2,
    physical_plywood_leaves: 4, physical_bodies: 148, wood_bearing_walls: 112,
    four_port_fittings: 24, panel_screws_deferred: 66}))
    assert.equal(report.inventory[key], count, `current96 inventory: ${key}`);
  assert.equal(report.qualification.panel_Hillman_resolution_deferred, true);
  for (const key of ['complete_conditional_frame_evaluation', 'physical_demand_bounds_established',
    'structural_acceptance', 'fabrication_released', 'climbing_released'])
    assert.equal(report.qualification[key], false, `current96 claim boundary: ${key}`);
  assert.ok(report.geometry_eligibility && report.metric_maxima && report.exceedances);
  assert.equal(report.geometry_eligibility.no_pass_when_geometry_ineligible, true);
  assert.equal(report.geometry_eligibility.all_geometry_eligible, false);
  assert.equal(report.source_map_limits.active_field_source_pins_reverified, true);
  for (const name of ['analysis_producer', 'worksheet_adapter', 'report_producer'])
    bound(report.source_bindings[name]);
}

export function validateCurrentBoltGeometryReview(report, index) {
  const target = {
    'eoere-inward-bolts-and-angles-v8': ['eoere-v8-perfect-bond-four-host-analysis-v1', 'owner-inward-angles-v8'],
    'eoere-single-spacer-cleat-stacks-v9': ['eoere-v9-perfect-bond-four-host-analysis-v1', 'owner-single-spacer-stacks-v9'],
  }[index.geometry.revision];
  assert.ok(target, 'supported own-bank geometry required');
  const physical = JSON.parse(bound(index.geometry.receipt));
  assert.equal(report.schema, 'eoere_current_bolt_geometry_review/v1');
  assert.equal(report.geometry_revision, index.geometry.revision);
  assert.deepEqual(report.physical_geometry, index.geometry.receipt);
  assert.equal(report.analysis_revision, target[0]);
  assert.deepEqual(report.physical_geometry_raw, physical.checked_geometry);
  assert.equal(report.status, 'CURRENT_COMPONENT_REVIEW_COMPLETE_JOINT_UNRESOLVED');
  assert.deepEqual(report.load_contract, {input_weight: 250, input_unit: 'lb',
    downward_multiplier: 2, horizontal_force_n: 300, duration_factor_CD: 1, accessory_mass_kg: 25});
  assert.equal(report.all_six_fields_share_geometry_and_material_intake, true);
  assert.ok(report.analysis_geometry.path.includes(`/${target[1]}/analysis-v1/geometry/`));
  assert.match(report.analysis_geometry.sha256, /^[a-f0-9]{64}$/);
  assert.equal(report.formal_geometry_Cdelta, null);
  for (const key of ['complete_joint_qualified', 'complete_joint_acceptance', 'candidate_accepted',
    'capacity_established', 'structural_acceptance', 'structural_released',
    'physical_demand_bounds_established', 'fabrication_released', 'climbing_released',
    'historical_pass_transferred', 'new_force_response_computed_by_this_review'])
    assert.equal(report[key], false, `current geometry claim boundary: ${key}`);
  assert.deepEqual(report.base_input_manifest.legacy_screen_adjusted_indices, {});
  assert.deepEqual(report.inventory, {shafts: 96, wood_occurrences_per_case: 112,
    timber_rows: 22, fitting_ports: 96, analytical_plywood_bodies: 2,
    physical_plywood_leaves: 4, cases: 6, panels: 6, screws: 66});
  for (const key of ['producer', 'occurrence_producer', 'rules_producer',
    'outer_geometry_producer', 'pair_census_producer', 'pair_upgrade_producer']) bound(report[key]);
  const cases = ['a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'];
  assert.deepEqual(report.case_summaries.map(r => r.case_id).sort(), [...cases].sort());
  assert.deepEqual(Object.keys(report.source_bindings.fields_and_replays).sort(), [...cases].sort());
  for (const row of report.case_summaries) {
    assert.deepEqual(row.field, report.source_bindings.fields_and_replays[row.case_id].field);
    assert.equal(Object.values(row.axis_status_counts).reduce((a, b) => a+b, 0), 96);
    assert.equal(Object.values(row.load_class_counts).reduce((a, b) => a+b, 0), 112);
    assert.deepEqual(row.pair_census_counts, {same_host_pairs: 326, existing_connection_group_pairs: 52,
      additional_pairs_with_unresolved_applicability: 274});
    for (const ref of Object.values(report.source_bindings.fields_and_replays[row.case_id])) {
      assert.ok(ref.path.includes(`/${target[1]}/analysis-v1/four-hosts/${row.case_id}/`));
      assert.match(ref.sha256, /^[a-f0-9]{64}$/);
    }
  }
  assert.equal(report.additional_same_host_pairs.length, 274);
  const pairs = new Set();
  for (const row of report.additional_same_host_pairs) {
    assert.equal(row.axes.length, 2); assert.ok(row.axes[0] < row.axes[1]);
    pairs.add(`${row.host}/${row.axes.join('/')}`);
    assert.equal(row.status, 'UNRESOLVED'); assert.equal(row.complete_Cdelta, null);
    assert.equal(row.complete_joint_qualified, false);
    assert.deepEqual([...row.case_ids].sort(), [...cases].sort());
  }
  assert.equal(pairs.size, 274);
  if (report.method_blueprint) {
    for (const key of ['analysis_module', 'frozen_geometry_reader', 'latest_wrapper'])
      bound(report.method_blueprint[key]);
    assert.equal(report.method_blueprint.analysis_revision, report.analysis_revision);
    assert.equal(report.method_blueprint.physical_geometry_revision, report.geometry_revision);
  }
}

export function validateOwnResponseBank(report, index) {
  const target = {
    'eoere-inward-bolts-and-angles-v8': ['eoere-v8-perfect-bond-four-host-analysis-v1', 'owner-inward-angles-v8'],
    'eoere-single-spacer-cleat-stacks-v9': ['eoere-v9-perfect-bond-four-host-analysis-v1', 'owner-single-spacer-stacks-v9'],
  }[index.geometry.revision];
  assert.ok(target, 'own response-bank geometry required');
  assert.equal(report.schema, 'eoere_own_response_bank/v1');
  assert.equal(report.geometry_revision, index.geometry.revision);
  assert.deepEqual(report.physical_geometry, index.geometry.receipt);
  assert.deepEqual(report.physical_geometry_raw, JSON.parse(bound(index.geometry.receipt)).checked_geometry);
  assert.equal(report.analysis_revision, target[0]);
  assert.ok(report.analysis_geometry.path.includes(`/${target[1]}/analysis-v1/geometry/`));
  assert.equal(report.all_six_cases_admitted, true);
  assert.equal(report.admission_gate_N, 1e-5);
  assert.ok(Number.isFinite(report.maximum_gradient_inf_N) && report.maximum_gradient_inf_N >= 0 && report.maximum_gradient_inf_N < 1e-5);
  assert.deepEqual(report.load_contract, {weight_lb: 250, downward_multiplier: 2,
    horizontal_force_N: 300, accessory_mass_kg: 25, duration_factor_CD: 1});
  for (const key of ['historical_force_pass_transferred', 'physical_force_bounds_established',
    'complete_joint_or_frame_qualified', 'structural_acceptance', 'fabrication_released', 'climbing_released'])
    assert.equal(report[key], false, `own-bank boundary: ${key}`);
  bound(report.producer);
  const cases = ['a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'];
  assert.deepEqual(report.cases.map(r => r.case_id).sort(), [...cases].sort());
  const base = report.analysis_geometry.path.replace(/\/geometry\/geometry\.json$/, '/four-hosts/');
  for (const row of report.cases) {
    assert.equal(row.both_independent_replays_admitted, true);
    assert.equal(row.physical_bodies, 148);assert.equal(row.shafts, 96);
    assert.equal(row.panels, 6);assert.equal(row.Hillman_axes, 66);
    assert.ok(Number.isFinite(row.gradient_inf_N) && row.gradient_inf_N >= 0 && row.gradient_inf_N < 1e-5);
    for (const key of ['field', 'independent_replay', 'independent_plywood_replay']) {
      assert.ok(row[key].path.startsWith(base+row.case_id+'/'));
      assert.match(row[key].sha256, /^[a-f0-9]{64}$/);
    }
  }
  assert.equal(report.maximum_gradient_inf_N, Math.max(...report.cases.map(r => r.gradient_inf_N)));
}

const CURRENT_CASES = ['a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'];
const SHAFT_REFERENCE_METRICS = ['maximum_bearing_index_before_Cdelta',
  'maximum_N_M_index_before_Cdelta', 'maximum_N_M_V_index_before_Cdelta'];
const TIMBER_REFERENCE_METRICS = ['maximum_normal_reference_upper',
  'maximum_shear_torsion_reference_upper', 'maximum_declared_restraint_normal_reference_upper'];
const CURRENT_SAWN_MEMBERS = ['base_header', 'base_rail_top', ...['left', 'right'].flatMap(side =>
  ['base_floor', 'base_post_center', 'base_post_outer', 'base_principal_center',
    'base_rail_bottom', 'base_rail_service_lower', 'base_rail_service_upper', 'base_side', 'lumber_leg']
    .map(name => `${name}_${side}`))];
const BRACING_MODES = ['top_grain_compression', 'side_grain_compression', 'panel_normal_translation',
  'top_grain_torsion', 'side_grain_torsion', 'in_plane_corner_rotation'];
const BRACING_FITTINGS = {left: 'eoere_clip_single_top_left_1', right: 'eoere_clip_single_top_right_2'};
const BRACING_AXIS_TOLERANCE = 1e-8; // Tracked factory directions are rounded to nine decimal places.

function referenceKeys(value, expected, label) {
  assert.ok(value && typeof value === 'object' && !Array.isArray(value), `${label}: object required`);
  assert.deepEqual(Object.keys(value).sort(), [...expected].sort(), `${label}: keys differ`);
}

function referenceBinding(binding, expectedPath) {
  referenceKeys(binding, ['path', 'sha256'], 'source binding');
  assert.ok(typeof binding.path === 'string' && binding.path.split('/').every(part =>
    part && part !== '.' && part !== '..') && !binding.path.includes('\\') && !path.isAbsolute(binding.path),
  'source binding must use a repository-relative path');
  assert.match(binding.sha256, /^[a-f0-9]{64}$/);
  if (expectedPath !== undefined) assert.equal(binding.path, expectedPath, 'own source path differs');
}

function referenceIndex(value, label) {
  assert.ok(Number.isFinite(value) && value >= 0, `${label}: finite nonnegative index required`);
}

function referenceClose(actual, expected, label) {
  assert.ok(Number.isFinite(actual) && Number.isFinite(expected) &&
    Math.abs(actual-expected) <= 1e-12*Math.max(1, Math.abs(expected)), `${label}: values differ`);
}

function parallelProbeAxes(first, second) {
  return Math.min(Math.hypot(...first.map((value, i) => value-second[i])),
    Math.hypot(...first.map((value, i) => value+second[i]))) <= BRACING_AXIS_TOLERANCE;
}

export function currentFittingProbeGeometry(axisMap, fitting) {
  assert.ok(Object.values(BRACING_FITTINGS).includes(fitting), 'known bracing fitting required');
  const holes = [];
  for (const [axisID, axis] of axisMap) {
    assert.ok(Array.isArray(axis.attachments), 'axis attachment list required');
    const attachments = axis.attachments.filter(row => row?.angle_id === fitting);
    assert.ok(attachments.length <= 1, 'one fitting hole center per bolt axis required');
    if (!attachments.length) continue;
    const {point, receiver, direction} = attachments[0];
    assert.ok(Array.isArray(point) && point.length === 3 && point.every(Number.isFinite),
      'finite physical fitting hole center required');
    holes.push({axisID, point, receiver, direction});
  }
  assert.equal(holes.length, 4, 'four physical fitting hole centers required');
  assert.equal(new Set(holes.map(row => JSON.stringify(row.point))).size, 4,
    'four distinct physical fitting hole centers required');
  const corner = Object.keys(BRACING_FITTINGS).find(side => BRACING_FITTINGS[side] === fitting);
  const beam = holes.filter(row => row.receiver === 'base_rail_top');
  const post = holes.filter(row => row.receiver === `base_side_${corner}`);
  assert.equal(beam.length, 2, 'current corner needs two top-rail attachments');
  assert.equal(post.length, 2, 'current corner needs two side-member attachments');
  const receiverAxis = rows => {
    const axes = rows.map(({direction}) => {
      assert.ok(Array.isArray(direction) && direction.length === 3 && direction.every(Number.isFinite),
        'finite fitting attachment direction required');
      const norm = Math.hypot(...direction);
      assert.ok(Math.abs(norm-1) <= BRACING_AXIS_TOLERANCE, 'unit fitting attachment direction required');
      return direction.map(value => value/norm);
    });
    assert.ok(parallelProbeAxes(...axes), 'two receiver attachments must define one consistent axis');
    return axes[0];
  };
  // This frozen corner layout uses post bores along top grain and beam bores
  // along side grain. Require its recorded 2+2 receiver arrangement; this is
  // not a general rule for other fitting layouts or timber profiles.
  const top = receiverAxis(post), side = receiverAxis(beam);
  assert.ok(Math.abs(top.reduce((total, value, i) => total+value*side[i], 0)) <= BRACING_AXIS_TOLERANCE,
    'current corner grain axes must remain orthogonal');
  const cross = [top[1]*side[2]-top[2]*side[1], top[2]*side[0]-top[0]*side[2],
    top[0]*side[1]-top[1]*side[0]];
  const normal = cross.map(value => value/Math.hypot(...cross));
  return {axes: holes.map(row => row.axisID).sort(),
    point: [0, 1, 2].map(i => holes.reduce((total, row) => total+row.point[i], 0)/4),
    directions: {top, side, normal}};
}

function currentPublicReview(report, index) {
  assert.equal(report.geometry_revision, index.geometry.revision);
  referenceBinding(report.physical_geometry);
  assert.deepEqual(report.physical_geometry, index.geometry.receipt);
  const bank = JSON.parse(bound(index.response_bank));
  validateOwnResponseBank(bank, index);
  referenceBinding(report.analysis_geometry);
  assert.deepEqual(report.analysis_geometry, bank.analysis_geometry);
  assert.deepEqual([...report.case_ids].sort(), [...CURRENT_CASES].sort());
  const base = bank.analysis_geometry.path.replace(/geometry\/geometry\.json$/, '');
  assert.notEqual(base, bank.analysis_geometry.path, 'own analysis geometry filename required');
  referenceBinding(report.producer, 'scripts/eoere_current_reference_review.py');
  bound(report.producer);
  for (const key of ['structural_acceptance', 'fabrication_released', 'climbing_released'])
    assert.equal(report[key], false, `current review claim boundary: ${key}`);
  // Recover receiver/attachment records from tracked axis rows.
  // Recent packets contain updates, so retain the preceding complete census.
  const axisSources = [];
  for (let revision = index; revision; revision = revision.preceding_revision) {
    const receipt = JSON.parse(bound(revision.geometry.receipt));
    for (const name of ['axes.json', 'axes-additions.json', 'axis-updates.json'])
      if (receipt.files[name]) axisSources.push(JSON.parse(bound(receipt.files[name])).axes);
    if (receipt.files['candidate-parameters.json']) axisSources.push(
      JSON.parse(bound(receipt.files['candidate-parameters.json'])).axis_updates.map(row => row.after_axis));
    if (receipt.files['axes.json']) break;
  }
  const axisMap = new Map(axisSources.reverse().flat().map(axis => [axis.id, axis]));
  assert.equal(axisMap.size, 96);
  return {bank, base, axisMap};
}

export function validateCurrentConventionalReferenceReview(report, index) {
  assert.equal(report.schema, 'eoere_current_conventional_reference_review/v1');
  const {bank, base, axisMap} = currentPublicReview(report, index);
  referenceBinding(report.physical_source_geometry);
  assert.deepEqual(report.physical_source_geometry, bank.physical_geometry_raw);
  referenceBinding(report.prepared_readiness, base+'adapter-readiness.json');
  assert.deepEqual(report.prepared_readiness, bank.readiness);
  assert.deepEqual(report.load_contract, {...bank.load_contract, self_weight: true});
  assert.equal(report.complete_joint_Cdelta_established, false);
  assert.equal(report.physical_failure_inferred, false);
  assert.equal(report.physical_geometry_loads_screws_resistances_unchanged_by_review, true);
  assert.equal(report.fields.length, CURRENT_CASES.length);
  for (const [i, caseID] of report.case_ids.entries())
    assert.deepEqual(report.fields[i], bank.cases.find(row => row.case_id === caseID).field,
      'reference field must join its own admitted bank');
  const sources = {
    shaft_Cg_only: 'reference-review-v1/complete-v1/shaft-bearing-blocks-v1.json',
    timber_scalar: 'reference-review-v1/complete-v1/timber-sections-v1.json',
    timber_vector: 'reference-review-v1/vector-bound-v2/timber-sections-v1.json',
    cleat_nominal: 'reference-review-v1/nominal38p1-rows-v1.json',
    cleat_wall_allowance: 'reference-review-v1/bonded-rows-v1.json',
    timber_cores: 'reference-review-v1/complete-v1/timber-net-geometry-v1.json',
    thread_windows: 'reference-review-v1/head-to-nut-windows.json',
  };
  referenceKeys(report.source_bindings, [...Object.keys(sources), 'vector_method'], 'reference sources');
  for (const [name, suffix] of Object.entries(sources)) referenceBinding(report.source_bindings[name], base+suffix);
  referenceBinding(report.source_bindings.vector_method, 'scripts/timber_vector_shear_bound.py');
  bound(report.source_bindings.vector_method);
  assert.ok(Number.isSafeInteger(report.interval_count) && report.interval_count >= 6*20,
    'whole-interval reference census required');

  const caseWitness = row => {
    assert.ok(CURRENT_CASES.includes(row.case_id), 'current case witness required');
    referenceIndex(row.index, 'reference witness');
  };
  const shaftWitness = row => {
    caseWitness(row);
    assert.ok(axisMap.has(row.axis), 'current shaft identity required');
    assert.ok(SHAFT_REFERENCE_METRICS.includes(row.metric), 'known shaft reference metric required');
    assert.ok(Number.isFinite(row.Cg) && row.Cg > 0 && row.Cg <= 1, 'bounded Cg required');
    assert.equal(row.complete_joint_Cdelta, null);
  };
  referenceKeys(report.shaft_Cg_only_maxima, SHAFT_REFERENCE_METRICS, 'shaft maxima');
  for (const [metric, row] of Object.entries(report.shaft_Cg_only_maxima)) {
    shaftWitness(row);
    assert.equal(row.metric, metric);
  }
  const timberWitness = row => {
    caseWitness(row);
    assert.ok(CURRENT_SAWN_MEMBERS.includes(row.member), 'current sawn member required');
    assert.ok(Number.isSafeInteger(row.section_interval_count) && row.section_interval_count > 0,
      'section interval count required');
  };
  referenceKeys(report.timber_maxima, ['timber_scalar', 'timber_vector'], 'timber constructions');
  for (const [construction, metrics] of Object.entries(report.timber_maxima)) {
    referenceKeys(metrics, TIMBER_REFERENCE_METRICS, 'timber metrics');
    for (const [metric, summary] of Object.entries(metrics)) {
      assert.equal(summary.source_field_name, metric);
      assert.equal(summary.unit, 'reference upper index');
      referenceKeys(summary.by_case, CURRENT_CASES, 'timber case maxima');
      for (const [caseID, row] of Object.entries(summary.by_case)) {
        timberWitness(row);
        assert.equal(row.case_id, caseID);
      }
      timberWitness(summary.overall);
      assert.deepEqual(summary.overall, summary.by_case[summary.overall.case_id], 'whole maximum witness differs');
      assert.equal(summary.overall.index, Math.max(...Object.values(summary.by_case).map(row => row.index)));
      if (construction === 'timber_vector') {
        const scalar = report.timber_maxima.timber_scalar[metric];
        if (metric === 'maximum_shear_torsion_reference_upper') {
          for (const caseID of CURRENT_CASES) assert.ok(summary.by_case[caseID].index <= scalar.by_case[caseID].index+1e-7,
            'vector bound exceeds scalar beyond the issued series-tail allowance');
        } else assert.deepEqual(summary, scalar, 'vector refinement changed another reference');
      }
    }
  }
  referenceKeys(report.vector_timber_member_maxima, CURRENT_SAWN_MEMBERS, 'vector member maxima');
  for (const [member, metrics] of Object.entries(report.vector_timber_member_maxima)) {
    referenceKeys(metrics, TIMBER_REFERENCE_METRICS, 'member metrics');
    for (const [metric, row] of Object.entries(metrics)) {
      caseWitness(row);
      const interval = row.worst_interval;
      for (const name of TIMBER_REFERENCE_METRICS) referenceIndex(interval[name.replace('maximum_', '')], 'interval reference');
      assert.equal(row.index, interval[metric.replace('maximum_', '')], 'member maximum and interval disagree');
      for (const name of ['world_grain_interval_mm', 'net_core_interval_local_L_mm'])
        assert.ok(interval[name].length === 2 && interval[name].every(Number.isFinite) && interval[name][1] > interval[name][0],
          'finite increasing interval required');
      const byCase = report.timber_maxima.timber_vector[metric].by_case[row.case_id];
      assert.ok(row.index <= byCase.index, 'member witness exceeds its case maximum');
      for (const witness of Object.values(report.timber_maxima.timber_vector[metric].by_case))
        if (witness.member === member) assert.ok(witness.index <= row.index, 'case witness exceeds its member maximum');
    }
  }
  for (const metric of TIMBER_REFERENCE_METRICS) assert.equal(
    report.timber_maxima.timber_vector[metric].overall.index,
    Math.max(...Object.values(report.vector_timber_member_maxima).map(row => row[metric].index)),
    'whole and member maxima disagree');

  const cleatWitness = row => {
    caseWitness(row);
    assert.ok(['eoere_cleat_left', 'eoere_cleat_right'].includes(row.host), 'current bonded cleat required');
    assert.ok(Array.isArray(row.axes) && row.axes.length > 0 && row.axes.length <= 4 &&
      new Set(row.axes).size === row.axes.length && row.axes.every(axis => axisMap.get(axis)?.receivers.includes(row.host)),
    'unique cleat subset axes required');
  };
  referenceKeys(report.cleat_maxima, ['cleat_nominal', 'cleat_wall_allowance'], 'cleat maxima');
  for (const row of Object.values(report.cleat_maxima)) cleatWitness(row);
  referenceKeys(report.reference_exceedances,
    ['shaft_Cg_only', 'timber_scalar', 'timber_vector', 'cleat_nominal', 'cleat_wall_allowance'], 'exceedance groups');
  for (const [group, rows] of Object.entries(report.reference_exceedances)) {
    assert.ok(Array.isArray(rows), 'exceedance array required');
    const identities = new Set();
    for (const row of rows) {
      caseWitness(row);
      assert.ok(row.index > 1, 'strict reference exceedance required');
      let identity;
      if (group === 'shaft_Cg_only') {
        shaftWitness(row);
        assert.ok(row.index <= report.shaft_Cg_only_maxima[row.metric].index, 'shaft exceedance exceeds maximum');
        identity = `${row.case_id}/${row.axis}/${row.metric}`;
      } else if (group.startsWith('timber_')) {
        assert.ok(CURRENT_SAWN_MEMBERS.includes(row.member) && TIMBER_REFERENCE_METRICS.includes(row.metric));
        assert.equal(row.geometry_status, 'section_reference_only');
        const summary = report.timber_maxima[group][row.metric].by_case[row.case_id];
        assert.ok(row.index <= summary.index, 'timber exceedance exceeds case maximum');
        if (row.member === summary.member) assert.equal(row.index, summary.index);
        if (group === 'timber_vector') assert.ok(row.index <= report.vector_timber_member_maxima[row.member][row.metric].index,
          'timber exceedance exceeds member maximum');
        identity = `${row.case_id}/${row.member}/${row.metric}`;
      } else {
        cleatWitness(row);
        assert.ok(row.index <= report.cleat_maxima[group].index, 'cleat exceedance exceeds maximum');
        identity = `${row.case_id}/${row.host}/${[...row.axes].sort().join('/')}`;
      }
      assert.ok(!identities.has(identity), 'duplicate reference exceedance');
      identities.add(identity);
    }
  }
  // The compact report exposes maxima, not every shaft/member comparison.
  // Require every disclosed maximum above one; raw nonworst completeness is
  // checked only by the separate recovered-evidence audit.
  const requireDisclosed = (rows, expected) => assert.ok(rows.some(row => isDeepStrictEqual(row, expected)),
    'exceeded published maximum is not disclosed');
  for (const row of Object.values(report.shaft_Cg_only_maxima))
    if (row.index > 1) requireDisclosed(report.reference_exceedances.shaft_Cg_only, row);
  for (const [construction, metrics] of Object.entries(report.timber_maxima))
    for (const [metric, summary] of Object.entries(metrics))
      for (const row of Object.values(summary.by_case)) if (row.index > 1)
        requireDisclosed(report.reference_exceedances[construction], {case_id: row.case_id, member: row.member,
          metric, index: row.index, geometry_status: 'section_reference_only'});
  for (const [member, metrics] of Object.entries(report.vector_timber_member_maxima))
    for (const [metric, row] of Object.entries(metrics)) if (row.index > 1)
      requireDisclosed(report.reference_exceedances.timber_vector, {case_id: row.case_id, member,
        metric, index: row.index, geometry_status: 'section_reference_only'});
  for (const [group, row] of Object.entries(report.cleat_maxima))
    if (row.index > 1) requireDisclosed(report.reference_exceedances[group], row);
}

export function validateCurrentPanelBracingSummary(report, index) {
  assert.equal(report.schema, 'eoere_current_panel_bracing_summary/v1');
  const {base, axisMap} = currentPublicReview(report, index);
  assert.equal(report.case_count, 6);
  assert.equal(report.stiffness_comparison_only, true);
  assert.equal(report.strength_gain_factor, null);
  for (const name of ['new_unbraced_climber_load_equilibrium', 'double_strength_credit_applied',
    'compression_capacity_or_buckling_gain_established']) assert.equal(report[name], false, `bracing boundary: ${name}`);
  assert.deepEqual(report.inventory, {corners: 2, probe_comparisons: 72, factorizations: 12,
    balanced_rhs_solves: 144, panels_removed: 6, screw_springs_removed: 66});
  assert.deepEqual(report.controls, {floating_panel_gain: 1, known_answer_controls_passed: true, series_parallel_gain: 1.4});
  assert.deepEqual(report.model_assumptions, {Hillman_axial_N_per_mm: 1000, Hillman_lateral_N_per_mm: 1000,
    panel_contact_N_per_mm3: 2, physical_Hillman_law_qualified: false, contact_branches_frozen_at_braced_state: true});
  referenceKeys(report.source_bindings, ['raw_result', 'candidate_intake', 'reference_review', 'method'], 'bracing sources');
  referenceBinding(report.source_bindings.raw_result, base+'panel-bracing-review-v2/result.json');
  referenceBinding(report.source_bindings.candidate_intake, base+'panel-bracing-review-v2/candidate-intake.json');
  referenceBinding(report.source_bindings.reference_review);
  assert.deepEqual(report.source_bindings.reference_review, index.engineering_review);
  referenceBinding(report.source_bindings.method, 'scripts/eoere_panel_bracing_review.py');
  bound(report.source_bindings.method);
  referenceBinding(report.literature_review);
  referenceKeys(report.numerical_checks, ['maximum_relative_equilibrium_error',
    'maximum_relative_binary64_equilibrium_error', 'maximum_normalized_reciprocity_error'], 'bracing numerical checks');
  for (const value of Object.values(report.numerical_checks)) referenceIndex(value, 'bracing numerical check');
  assert.ok(report.numerical_checks.maximum_relative_equilibrium_error < 1e-7);
  assert.ok(report.numerical_checks.maximum_normalized_reciprocity_error < 1e-6);

  assert.equal(report.probes.length, 72);
  const corners = Object.fromEntries(Object.entries(BRACING_FITTINGS).map(([corner, fitting]) =>
    [corner, currentFittingProbeGeometry(axisMap, fitting)]));
  const identities = new Set();
  for (const row of report.probes) {
    assert.ok(CURRENT_CASES.includes(row.case_id) && ['left', 'right'].includes(row.corner) &&
      BRACING_MODES.includes(row.mode), 'current case/corner/mode probe required');
    const identity = `${row.case_id}/${row.corner}/${row.mode}`;
    assert.ok(!identities.has(identity), 'duplicate bracing probe'); identities.add(identity);
    assert.equal(row.first, 'base_rail_top'); assert.equal(row.second, `base_side_${row.corner}`);
    assert.equal(row.stiffness_unit, BRACING_MODES.indexOf(row.mode) < 3 ? 'N/mm' : 'Nmm/rad');
    for (const key of ['point_xyz_mm', 'direction_xyz'])
      assert.ok(row[key].length === 3 && row[key].every(Number.isFinite), 'finite probe geometry required');
    referenceClose(Math.hypot(...row.direction_xyz), 1, 'unit probe direction');
    assert.ok(row.joint_axis_ids.length === 4 && new Set(row.joint_axis_ids).size === 4 &&
      row.joint_axis_ids.every(axis => typeof axis === 'string' && axis), 'four unique corner axes required');
    assert.deepEqual([...row.joint_axis_ids].sort(), corners[row.corner].axes, 'probe must use its own corner axes');
    // Match the V2 flange_probe_points datum: physical hole centers, not head origins.
    for (const [i, coordinate] of row.point_xyz_mm.entries())
      assert.ok(Math.abs(coordinate-corners[row.corner].point[i]) <= 1e-7,
        'probe point must be the centroid of its four physical fitting holes');
    const axis = row.mode.startsWith('top_grain') ? 'top' : row.mode.startsWith('side_grain') ? 'side' : 'normal';
    assert.ok(parallelProbeAxes(row.direction_xyz, corners[row.corner].directions[axis]),
      'probe direction must follow its recorded corner mode axis, allowing either parallel sign');
    for (const key of ['with_panels_stiffness', 'without_panels_stiffness', 'modeled_stiffness_ratio'])
      assert.ok(Number.isFinite(row[key]) && row[key] > 0, 'finite positive probe stiffness/ratio required');
    referenceClose(row.modeled_stiffness_ratio, row.with_panels_stiffness/row.without_panels_stiffness, 'probe ratio');
    assert.ok(row.modeled_stiffness_ratio >= 1-1e-6, 'removing positive restraint cannot stiffen the comparator');
  }
  referenceKeys(report.all_six_case_ranges, BRACING_MODES, 'bracing mode ranges');
  for (const [mode, ranges] of Object.entries(report.all_six_case_ranges)) {
    referenceKeys(ranges, ['minimum', 'maximum'], 'bracing range');
    const candidates = report.probes.filter(row => row.mode === mode);
    for (const [kind, witness] of Object.entries(ranges)) {
      const own = candidates.find(row => row.case_id === witness.case_id && row.corner === witness.corner);
      assert.deepEqual(witness, own, 'range must retain its complete own probe witness');
      assert.equal(witness.modeled_stiffness_ratio,
        Math[kind === 'minimum' ? 'min' : 'max'](...candidates.map(row => row.modeled_stiffness_ratio)));
    }
  }
}

export function validateBoltGeometryReview(report, index) {
  const base = JSON.parse(bound(index.engineering_review));
  assert.ok(['eoere_current96_bolt_geometry_review/v1', 'eoere_current96_bolt_geometry_review/v2'].includes(report.schema));
  assert.equal(report.geometry_revision, index.geometry.revision);
  assert.deepEqual(report.physical_geometry, index.geometry.receipt);
  assert.deepEqual(report.base_review, index.engineering_review);
  assert.deepEqual(report.analysis_geometry, base.analysis_geometry);
  assert.deepEqual(report.load_contract, base.load_contract);
  assert.deepEqual(report.legacy_screen_adjusted_indices_unchanged, base.metric_maxima.shafts_Cdelta_adjusted);
  assert.equal(report.status, 'RULE_APPLICABILITY_CORRECTED_COMPLETE_JOINT_UNRESOLVED');
  assert.deepEqual(report.inventory, {shafts: 96, wood_occurrences_per_case: 112,
    cases: 6, panels: 6, screws: 66});
  assert.equal(report.formal_geometry_Cdelta, null);
  assert.equal(report.all_complete_geometry_factors_unresolved, true);
  for (const key of ['complete_joint_qualified', 'structural_acceptance',
    'fabrication_released', 'climbing_released', 'frame_CAD_or_mechanics_recomputed',
    'historical_pass_transferred']) assert.equal(report[key], false, `geometry review boundary: ${key}`);
  bound(report.producer); bound(report.rules_producer);
  assert.equal(report.case_summaries.length, 6);
  assert.deepEqual(report.case_summaries.map(c => c.case_id).sort(), [...base.case_ids].sort());
  for (const row of report.case_summaries) {
    assert.deepEqual(row.field, base.source_bindings.fields_and_replays[row.case_id].field);
    assert.equal(Object.values(row.axis_status_counts).reduce((a, b) => a+b, 0), 96);
    assert.equal(Object.values(row.load_class_counts).reduce((a, b) => a+b, 0), 112);
  }
  assert.equal(report.upper_pair_statuses.length, 48);
  const upperAxes = Array.from({length: 8}, (_, i) => `eoere_bolt_${String(i+67).padStart(3, '0')}`);
  const expectedUpper = base.case_ids.flatMap(c => upperAxes.map(a => `${c}/${a}`)).sort();
  assert.deepEqual(report.upper_pair_statuses.map(r => `${r.case_id}/${r.axis_id}`).sort(), expectedUpper);
  for (const row of report.upper_pair_statuses) {
    assert.equal(row.component_status, 'UNRESOLVED');
    assert.equal(row.complete_Cdelta, null);
    assert.equal(row.complete_joint_qualified, false);
  }
  assert.equal(report.affected_pair_measurements.length, 6);
  for (const pair of report.affected_pair_measurements) {
    assert.ok(Math.abs(pair.rule.actual_spacing_mm-50.8) < 1e-6);
    assert.equal(pair.rule.status, 'unresolved');
    assert.equal(pair.rule.required_mm, null);
    assert.equal(pair.complete_Cdelta, null);
  }
  if (report.schema.endsWith('/v2')) {
    bound(report.occurrence_producer); bound(report.census_producer);
    const preceding = JSON.parse(bound(report.preceding_geometry_review));
    assert.equal(preceding.schema, 'eoere_current96_bolt_geometry_review/v1');
    assert.deepEqual(preceding.physical_geometry, report.physical_geometry);
    assert.equal(report.same_host_pair_census_complete, true);
    for (const row of report.case_summaries)
      assert.deepEqual(row.pair_census_counts, {same_host_pairs: 326, existing_connection_group_pairs: 52,
        additional_pairs_with_unresolved_applicability: 274});
    assert.equal(report.additional_same_host_pairs.length, 274);
    const pairs = new Set();
    for (const row of report.additional_same_host_pairs) {
      assert.equal(row.axes.length, 2);
      assert.ok(row.axes[0] < row.axes[1], 'same-host pair must be canonical');
      pairs.add(`${row.host}/${row.axes.join('/')}`);
      assert.equal(row.component_status, 'UNRESOLVED');
      assert.equal(row.complete_Cdelta, null);
      assert.equal(row.complete_joint_qualified, false);
      assert.equal(row.parallel_bore_axes, true);
      assert.ok(Number.isFinite(row.actual_spacing_mm) && row.actual_spacing_mm > 0);
    }
    assert.equal(pairs.size, 274, 'same-host pairs must not be duplicated');
    for (const pair of report.affected_pair_measurements) assert.equal(pair.case_id, 'a12-forward');
  }
}

export function validateCurrent96TestingReview(report, index) {
  const base = JSON.parse(bound(index.engineering_review));
  assert.equal(report.schema, 'eoere_current96_testing_method_review/v1');
  assert.equal(report.geometry_revision, index.geometry.revision);
  assert.deepEqual(report.physical_geometry, index.geometry.receipt);
  assert.deepEqual(report.base_review, index.engineering_review);
  for (const key of ['analysis_geometry', 'case_ids', 'case_count', 'load_contract', 'qualification'])
    assert.deepEqual(report[key], base[key], `testing review changed ${key}`);
  for (const key of ['current_bolts', 'sawn_timber_members', 'physical_plywood_leaves', 'panel_screws_deferred'])
    assert.equal(report.inventory[key], base.inventory[key]);
  bound(report.source_bindings.producer);
  for (const name of ['original_core', 'original_sections', 'prior_method_audit',
    'corrected_core', 'corrected_sections', 'worksheet_intake']) {
    const binding = report.source_bindings[name];
    assert.ok(binding.path.startsWith('fea/generated/'));
    assert.match(binding.sha256, /^[a-f0-9]{64}$/);
  }
  assert.deepEqual(report.source_bindings.original_sections, base.source_bindings.worksheets.timber_sections);
  for (const key of ['side_core_breadth_correction_applied',
    'current_six_case_all_interval_timber_references_recomputed',
    'original_bolt_and_cleat_references_retained', 'all_force_couples_and_hole_deductions_retained'])
    assert.equal(report.testing_disposition[key], true, `missing audit correction: ${key}`);
  for (const key of ['midface_probe_or_force_only_row_used_as_pass',
    'reduced_bolt_interaction_replaced_by_elastic_index', 'geometry_ineligibility_waived',
    'physical_failure_inferred_from_reference_exceedance', 'new_frame_or_native_solve',
    'cad_rebuilt', 'physical_geometry_or_loads_changed'])
    assert.equal(report.testing_disposition[key], false, `unsupported testing claim: ${key}`);
  assert.equal(report.release, false);
  for (const [group, metrics] of Object.entries(report.unchanged_reference_maxima))
    for (const [metric, value] of Object.entries(metrics))
      assert.deepEqual(value, base.metric_maxima[group][metric][group === 'shafts_Cdelta_adjusted' ? 'all_96' : 'overall'],
        'unchanged reference differs');
  assert.deepEqual(Object.keys(report.unchanged_reference_maxima).sort(),
    ['plywood_credited_36p5', 'plywood_nominal_38p1', 'shafts_Cdelta_adjusted']);
  for (const group of Object.keys(report.unchanged_reference_maxima))
    assert.deepEqual(Object.keys(report.unchanged_reference_maxima[group]).sort(),
      Object.keys(base.metric_maxima[group]).sort());
  for (const [key, value] of Object.entries(report.geometry_eligibility))
    assert.deepEqual(value, base.geometry_eligibility[key]);
  assert.equal(report.geometry_eligibility.no_pass_when_geometry_ineligible, true);
  assert.equal(report.geometry_eligibility.all_geometry_eligible, false);
  assert.deepEqual(report.side_core_changes.map(r => r.member).sort(), ['base_side_left', 'base_side_right']);
  for (const change of report.side_core_changes) {
    assert.equal(change.restored_breadth_mm, 9.525);
    assert.ok(Math.abs(change.current_bounds_U_mm[1]-change.current_bounds_U_mm[0]-88.898) < 1e-6);
    assert.ok(change.whole_interval_prisms_queried > 0);
    for (const key of ['projected_holes_unchanged', 'grain_intervals_unchanged', 'cached_solid_unchanged'])
      assert.equal(change[key], true);
  }
  const metrics = Object.keys(base.metric_maxima.timber_sections).sort();
  assert.deepEqual(Object.keys(report.timber_reference_maxima).sort(), metrics);
  for (const value of Object.values(report.timber_reference_maxima)) {
    assert.ok(Number.isFinite(value.overall.index) && value.overall.index >= 0);
    assert.deepEqual(Object.keys(value.by_case).sort(), [...base.case_ids].sort());
  }
  assert.deepEqual(report.member_comparisons.map(r => r.member).sort(),
    ['base_header', 'base_rail_top', 'base_side_left', 'base_side_right']);
  for (const member of report.member_comparisons) {
    assert.deepEqual(Object.keys(member.current).sort(), metrics);
    if (!member.member.startsWith('base_side_')) assert.deepEqual(member.current, member.original);
  }
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

export function validateCurrentResponse(report, index) {
  const response = index.current_response;
  assert.ok(response, 'explicit current response binding required');
  assert.equal(response.revision, index.geometry.revision);
  assert.equal(response.hardware_revision, index.hardware_model.revision);
  assert.deepEqual(response.geometry, index.geometry.receipt);
  assert.deepEqual(response.hardware_model, index.hardware_model.receipt);
  assert.equal(response.applies_to_current_geometry, true);
  assert.equal(response.applies_to_current_hardware, true);
  assert.ok(response.components, 'separate current component references required');
  assert.equal(report.schema, 'eoere_selected_hardware_six_case_response/v1');
  assert.equal(report.status, 'CURRENT_CONDITIONAL_FIRST_ORDER_CASES_ADMITTED');
  assert.equal(report.candidate, index.evidence_candidate);
  assert.equal(report.geometry_revision, response.revision);
  assert.equal(report.hardware_revision, response.hardware_revision);
  assert.deepEqual(report.geometry, response.geometry);
  assert.deepEqual(report.hardware_model, response.hardware_model);
  for (const key of ['extra_grid', 'native_solve_performed', 'historical_q_forces_or_passes_transferred',
    'remedies_attempted', 'actual_build_fit_work_performed', 'structural_acceptance',
    'physical_demand_bounds_established']) assert.equal(report[key], false, `response boundary: ${key}`);
  assert.equal(report.conditional_first_order_solve_performed, true);
  assert.equal(report.all_six_saved_field_admissions_pass, true);
  assert.equal(report.complete_joint_resistance, null);
  assert.equal(report.finished_member_capacity, null);
  assert.deepEqual(report.release, Object.fromEntries(['candidate_accepted', 'complete_joint_acceptance',
    'capacity_established', 'fabrication_released', 'structural_released', 'climbing_released'].map(k => [k, false])));
  assert.equal(report.source_manifest.path, path.posix.join(path.posix.dirname(response.cases.path), 'inputs.json'));
  const manifest = JSON.parse(bound(report.source_manifest));
  assert.equal(manifest.schema, 'eoere_selected_hardware_current_response_sources/v1');
  assert.deepEqual(manifest.references.geometry, response.geometry);
  assert.deepEqual(manifest.references.hardware, response.hardware_model);
  assert.equal(manifest.optional_extra_grid, false);
  for (const [key, name] of Object.entries({summary_producer: 'summarize_eoere_current_response',
    force_producer: 'eoere_current_response', input_checker: 'check_eoere_current_inputs'})) {
    assert.equal(report[key].path, `scripts/${name}.py`);
    bound(report[key]);
  }
  const sequence = ['a12-forward', 'a12-rear', 'a12-left', 'k12-right', 'k12-rear', 'a1-rear'];
  assert.deepEqual(report.case_sequence, sequence);
  assert.deepEqual(report.cases.map(row => row.case_id), sequence);
  assert.equal(new Set(report.cases.map(row => row.state_id)).size, 6);
  const raw = 'fea/generated/selected-hardware-followup-v1/current-response-v1/';
  for (const row of report.cases) {
    const directory = `${raw}cases-v1/${row.case_id}/attempt01/`;
    for (const [key, name] of [['field', 'field.json'], ['admission', 'admission.json']]) {
      assert.equal(row[key].path, directory + name);
      assert.match(row[key].sha256, /^[a-f0-9]{64}$/);
    }
    assert.equal(row.current_equilibrium_and_recovery_pass, true);
    assert.equal(row.physical_demand_bounds_established, false);
    assert.equal(row.first_order_physical_applicability_established, false);
    assert.ok(Number.isFinite(row.gradient_inf_n) && row.gradient_inf_n >= 0 && row.gradient_inf_n <= 1e-5);
    for (const [key, value] of Object.entries({physical_bodies: 150, timber: 22, fitting: 22,
      panel: 6, shaft: 100, floor_normals: 32, floor_xy_components: 16, end_captures: 200}))
      assert.equal(row.counts[key], value, `response census: ${key}`);
    assert.equal(row.applied_load_checks.physical_load_count, 835);
    assert.equal(row.applied_load_checks.complete_six_component_applied_load_work_replayed, true);
    assert.equal(row.applied_load_checks.distributed_panel_rhs_independently_regenerated, false);
    assert.equal(row.applied_load_checks.distributed_panel_rhs_is_exact_source_authenticated_capture, true);
    assert.equal(row.equilibrium_verification.all_body_and_global_checks_pass, true);
    assert.equal(row.equilibrium_verification.all_bodies, 150);
    for (const leg of ['lumber_leg_left', 'lumber_leg_right'])
      assert.ok(Number.isFinite(row.normal_force_n_by_host[leg]) && row.normal_force_n_by_host[leg] > 1e-7);
    assert.equal(row.floor_support_summary.normal_reactions_nonnegative, true);
    assert.equal(row.floor_support_summary.friction_or_anchor_capacity_established, false);
    assert.equal(row.floor_support_summary.centroid_xy_penalty_is_exact_distributed_no_slip, false);
    assert.equal(row.motion_diagnostics.first_order_applicability_established, false);
    assert.equal(row.motion_diagnostics.adopted_small_motion_threshold, null);
    for (const key of ['maximum_owned_interaction_point_linear_displacement_norm_mm',
      'maximum_relative_timber_or_fitting_strip_rotation_norm_rad'])
      assert.ok(Number.isFinite(row.motion_diagnostics[key]) && row.motion_diagnostics[key] >= 0);
    assert.equal(row.spacer_nut_capture_actions.length, 8);
    assert.equal(new Set(row.spacer_nut_capture_actions.map(r => r.axis_id)).size, 8);
    assert.ok(row.spacer_nut_capture_actions.every(r => Number.isFinite(r.compression_n) && r.compression_n >= 0));
  }
  assert.equal(report.maximum_full_gradient_residual_n, Math.max(...report.cases.map(r => r.gradient_inf_n)));
  assert.equal(report.maximum_owned_interaction_motion_mm,
    Math.max(...report.cases.map(r => r.motion_diagnostics.maximum_owned_interaction_point_linear_displacement_norm_mm)));
  assert.equal(report.maximum_relative_timber_or_fitting_rotation_rad,
    Math.max(...report.cases.map(r => r.motion_diagnostics.maximum_relative_timber_or_fitting_strip_rotation_norm_rad)));
  assert.ok(Number.isInteger(report.source_union.count) && report.source_union.count > 1450);
  assert.match(report.source_union.canonical_sha256, /^[a-f0-9]{64}$/);
  assert.equal(report.source_union.record.path, raw + 'summary-source-map-v1.json');
}

export function validateCurrentComponents(report, index) {
  const response = index.current_response, forces = JSON.parse(bound(response.cases));
  assert.equal(report.schema, 'eoere_current_six_case_structural_references/v1');
  assert.equal(report.status, 'BOUNDED_CURRENT_REFERENCES_COMPLETE_RESISTANCE_UNKNOWN');
  assert.equal(response.components.path, path.posix.join(path.posix.dirname(response.cases.path), 'components.json'));
  assert.deepEqual(report.current_response, response.cases);
  assert.equal(report.geometry_revision, response.revision);
  assert.equal(report.hardware_revision, response.hardware_revision);
  assert.deepEqual(report.geometry, response.geometry);
  assert.deepEqual(report.hardware_model, response.hardware_model);
  assert.deepEqual(report.release, forces.release);
  for (const key of ['extra_grid', 'structural_acceptance', 'native_solve_performed', 'CAD_rebuilt',
    'actual_build_fit_work_performed', 'remedies_attempted', 'physical_demand_bounds_established'])
    assert.equal(report[key], false, `component boundary: ${key}`);
  for (const key of ['complete_joint_resistance', 'finished_member_capacity', 'Hillman_product_capacity'])
    assert.equal(report[key], null, `unknown current resistance: ${key}`);
  const input = JSON.parse(bound(report.component_inputs));
  assert.equal(input.schema, 'eoere_current_component_inputs/v1');
  assert.deepEqual(input.current_response, response.cases);
  assert.deepEqual(input.release, report.release);
  for (const [key, name] of Object.entries({component_producer: 'eoere_current_components',
    section_producer: 'eoere_current_sections', summary_producer: 'summarize_eoere_current_components'})) {
    assert.equal(report[key].path, `scripts/${name}.py`);
    bound(report[key]);
  }
  assert.deepEqual(report.case_sequence, forces.case_sequence);
  assert.deepEqual(report.cases.map(r => r.case_id), forces.case_sequence);
  const screwAxes = JSON.parse(bound(response.geometry)).screw_axes.map(r => r.axis_id).sort();
  const timberMembers = [...new Set(report.targeted_finished_sections.planes.map(r => r.member))].sort();
  const raw = 'fea/generated/selected-hardware-followup-v1/current-components-v1/';
  for (const [i, row] of report.cases.entries()) {
    const force = forces.cases[i];
    for (const key of ['state_id', 'field', 'admission', 'release']) assert.deepEqual(row[key], force[key] ?? forces[key]);
    for (const [key, name] of [['raw_components', 'components.json'], ['producer_process', 'process.json']]) {
      assert.equal(row[key].path, `${raw}cases-v1/${row.case_id}/attempt02/${name}`);
      assert.match(row[key].sha256, /^[a-f0-9]{64}$/);
    }
    assert.equal(row.coarse.complete24_joint_resistances, null);
    assert.equal(row.coarse.generic_screw_references.all66_own_axes, true);
    assert.equal(row.coarse.generic_screw_references.Hillman_product_capacity_or_complete_end_interaction, null);
    const screws = row.coarse.generic_screw_references;
    const headIDs = screws.generic_CD1_head_exceedance_axis_ids;
    const scalars = screws.all_screw_reference_scalars;
    const threadRows = screws.all_effective_thread_length_reference_exceedances;
    assert.deepEqual(screws.reference_counts, {axes: 66, generic_CD1_head_exceedances: headIDs.length,
      effective_thread_length_exceedances: threadRows.length});
    assert.equal(new Set(headIDs).size, headIDs.length);
    assert.equal(scalars.length, 66);
    assert.deepEqual(scalars.map(r => r.axis_id).sort(), screwAxes);
    for (const scalar of scalars) {
      assert.ok(Number.isFinite(scalar.generic_head_ratio_CD1) && scalar.generic_head_ratio_CD1 >= 0);
      assert.ok(Number.isFinite(scalar.generic_withdrawal_required_effective_thread_mm_CD1)
        && scalar.generic_withdrawal_required_effective_thread_mm_CD1 >= 0);
      assert.ok(Number.isFinite(scalar.gross_nominal_length_after_panel_mm) && scalar.gross_nominal_length_after_panel_mm > 0);
      if (scalar.generic_withdrawal_required_effective_thread_mm_CD1 > scalar.gross_nominal_length_after_panel_mm)
        assert.ok(scalar.effective_thread_exceedance_witness, 'whole effective-thread witness binding required');
      else assert.equal(scalar.effective_thread_exceedance_witness, null);
    }
    assert.deepEqual(headIDs, scalars.filter(r => r.generic_head_ratio_CD1 > 1).map(r => r.axis_id));
    assert.deepEqual(threadRows.map(r => r.axis_id), scalars.filter(r =>
      r.generic_withdrawal_required_effective_thread_mm_CD1 > r.gross_nominal_length_after_panel_mm).map(r => r.axis_id));
    assert.equal(new Set(threadRows.map(r => r.axis_id)).size, threadRows.length);
    assert.deepEqual(threadRows, scalars.filter(r => r.effective_thread_exceedance_witness !== null)
      .map(r => r.effective_thread_exceedance_witness));
    const headWorst = screws.generic_head_ratio_CD1;
    assert.ok(Number.isFinite(headWorst.generic_head_ratio_CD1));
    assert.equal(headWorst.generic_head_ratio_CD1, Math.max(...scalars.map(r => r.generic_head_ratio_CD1)));
    assert.equal(scalars.find(r => r.axis_id === headWorst.axis_id)?.generic_head_ratio_CD1, headWorst.generic_head_ratio_CD1);
    if (headWorst.generic_head_ratio_CD1 > 1) assert.ok(headIDs.includes(headWorst.axis_id));
    else assert.equal(headIDs.length, 0);
    for (const witness of threadRows) {
      const scalar = scalars.find(r => r.axis_id === witness.axis_id);
      for (const key of ['axis_id', 'generic_head_ratio_CD1', 'generic_withdrawal_required_effective_thread_mm_CD1',
        'gross_nominal_length_after_panel_mm']) assert.deepEqual(witness[key], scalar[key]);
      assert.equal(witness.case_id, row.case_id);
      assert.equal(witness.state_id, row.state_id);
      assert.ok(Number.isFinite(witness.generic_withdrawal_required_effective_thread_mm_CD1));
      assert.ok(Number.isFinite(witness.gross_nominal_length_after_panel_mm));
      assert.ok(witness.generic_withdrawal_required_effective_thread_mm_CD1 > witness.gross_nominal_length_after_panel_mm);
    }
    const threadWorst = screws.generic_withdrawal_required_effective_thread_mm_CD1;
    if (threadWorst.generic_withdrawal_required_effective_thread_mm_CD1 > threadWorst.gross_nominal_length_after_panel_mm) {
      const saved = threadRows.find(r => r.axis_id === threadWorst.axis_id);
      assert.ok(saved, 'largest effective-thread exceedance witness must be retained');
      for (const [key, value] of Object.entries(threadWorst)) assert.deepEqual(saved[key], value);
    }
    assert.equal(row.coarse.panels.per_panel.length, 6);
    const panelExceedances = row.coarse.panels.per_panel.flatMap(p => Object.entries(p.section_components).flatMap(([component, value]) => {
      assert.ok(Number.isFinite(value.sampled_ratio_CD1));
      return value.sampled_ratio_CD1 > 1 ? [{panel: p.panel, component, ...value}] : [];
    }));
    assert.deepEqual(row.coarse.panels.sampled_section_exceedances_CD1, panelExceedances);
    assert.deepEqual(row.rich.steel_scenarios.map(r => r.comparison), [
      {id: 't6_r6', inside_radius_scenario_mm: 6, thickness_mm: 6, yield_factor: 1.67, rupture_factor: 2},
      {id: 't6p35_r6p35', inside_radius_scenario_mm: 6.35, thickness_mm: 6.35, yield_factor: 1.67, rupture_factor: 2},
    ]);
    const steelCategories = {
      physical_cut_nominal_combined: 'conditional_combined_yield_reference_ratio',
      near_hole_nominal_combined: 'conditional_combined_yield_reference_ratio',
      far_hole_nominal_combined: 'conditional_combined_yield_reference_ratio',
      radius_conditioned_heel_component_with_gravity: 'conditional_combined_yield_reference_ratio',
      separate_whole_flange_torsion_warping: 'conditional_combined_yield_reference_ratio',
      used_hole_bearing: 'bearing_reference_ratio', used_hole_tearout: 'tearout_reference_ratio',
      unused_near_hole_net_shear: 'net_shear_rupture_reference_ratio',
    };
    for (const scenario of row.rich.steel_scenarios) {
      assert.equal(scenario.fixed_actions_only, true);
      assert.equal(scenario.product_strength, null);
      assert.deepEqual(Object.keys(scenario.summary).sort(), Object.keys(steelCategories).sort());
      for (const [name, metric] of Object.entries(steelCategories)) {
        const category = scenario.summary[name], values = category.all_reference_values;
        assert.equal(category.comparison_count, name === 'separate_whole_flange_torsion_warping' ? 44 : 88);
        assert.equal(values.length, category.comparison_count);
        assert.ok(values.every(v => Number.isFinite(v) && v >= 0));
        assert.equal(category.worst.saved_metric, metric);
        assert.equal(category.worst[metric], Math.max(...values));
        assert.equal(category.exceedance_count, category.exceedances.length);
        assert.deepEqual(category.exceedances, category.whole_exceedance_witness_bindings);
        assert.deepEqual(category.exceedances.map(w => w[metric]), values.filter(v => v > 1));
        for (const witness of [category.worst, ...category.exceedances]) {
          assert.equal(witness.saved_metric, metric);
          assert.equal(typeof witness.body, 'string');
          if (name === 'unused_near_hole_net_shear') assert.equal(typeof witness.port_id, 'string');
          else assert.equal(typeof witness.flange, 'string');
          if (name === 'radius_conditioned_heel_component_with_gravity')
            assert.equal(witness.inside_radius_scenario_mm, scenario.comparison.inside_radius_scenario_mm);
        }
        if (category.worst[metric] > 1) assert.deepEqual(category.exceedances.find(w =>
          w.body === category.worst.body && w.flange === category.worst.flange && w.port_id === category.worst.port_id
          && w.axis_id === category.worst.axis_id && w[metric] === category.worst[metric]), category.worst);
      }
    }
    assert.equal(row.rich.timber.summary.physical_shafts, 100);
    assert.equal(row.rich.timber.summary.wood_surfaces, 120);
    assert.equal(row.rich.timber.summary.supported_component_reference_count, 92);
    assert.equal(row.rich.timber.all24_complete_joint_resistances, null);
    assert.equal(row.rich.timber.mixed_stacks.length, 8);
    assert.equal(row.rich.shaft.complete_bolt_resistance, null);
    assert.equal(row.rich.washers.census.physical_end_captures, 200);
    assert.equal(row.rich.washers.census.full_source_nominal_wood_ring_landing, 0);
    assert.equal(row.rich.washers.nominal_seat_geometry.nominal_wood_seats, 112);
    assert.equal(row.rich.washers.nominal_seat_geometry.all_current_finished_wood_lands_qualified, false);
    assert.equal(row.mixed_stack_statics.compatible_threaded_contact_or_yield_capacity, null);
    assert.equal(row.mixed_stack_statics.mixed_axis_ids.length, 8);
    assert.equal(row.mixed_stack_statics.own_surface_count, 24);
    const stability = row.gross_member_stability, members = stability.all_member_witness_records;
    assert.equal(stability.member_count, 22);
    assert.equal(stability.saved_sampled_witness_count, 44);
    assert.equal(members.length, 22);
    assert.deepEqual(members.map(r => r.member).sort(), timberMembers);
    const stabilityWitnesses = [];
    for (const member of members) {
      for (const key of ['span_mm', 'weak_column_domain_limit_mm', 'full_length_over_weak_column_domain_limit'])
        assert.ok(Number.isFinite(member[key]) && member[key] > 0);
      assert.equal(member.full_length_over_weak_column_domain_limit, member.span_mm/member.weak_column_domain_limit_mm);
      assert.equal(member.actual_restraint_or_complete_resistance, null);
      assert.deepEqual(member.two_saved_witness_sensitivities.map(w => w.witness),
        ['fully_braced_normal', 'sufficient_shear_torsion']);
      for (const witness of member.two_saved_witness_sensitivities) {
        assert.ok(Number.isFinite(witness.station_global_grain_projection_mm));
        assert.ok(Number.isFinite(witness.interaction_ratio) && witness.interaction_ratio >= 0);
        assert.equal(witness.ratio_exceeds_one, witness.interaction_ratio > 1);
        assert.equal(typeof witness.within_slenderness_limits, 'boolean');
        assert.equal(typeof witness.Euler_denominators_positive, 'boolean');
        assert.equal(witness.ratio_qualified_inside_declared_stability_domain,
          witness.within_slenderness_limits && witness.Euler_denominators_positive);
        stabilityWitnesses.push({member: member.member, ...witness});
      }
    }
    const domainKeys = ['member', 'span_mm', 'weak_column_domain_limit_mm', 'full_length_over_weak_column_domain_limit'];
    assert.deepEqual(stability.full_length_domain_exceedances, members
      .filter(r => r.full_length_over_weak_column_domain_limit > 1)
      .map(r => Object.fromEntries(domainKeys.map(k => [k, r[k]]))));
    assert.deepEqual(stability.saved_witness_reference_exceedances, stabilityWitnesses.filter(w => w.interaction_ratio > 1));
    assert.deepEqual(stability.largest_saved_K1_normal_sensitivity, stabilityWitnesses.find(w =>
      w.interaction_ratio === Math.max(...stabilityWitnesses.map(v => v.interaction_ratio))));
    assert.equal(row.spacer_nuts.length, 8);
    assert.deepEqual(row.spacer_nuts.map(r => ({axis_id: r.axis_id, compression_n: r.N_n})).sort((a,b) => a.axis_id.localeCompare(b.axis_id)),
      [...force.spacer_nut_capture_actions].sort((a,b) => a.axis_id.localeCompare(b.axis_id)));
    for (const spacer of row.spacer_nuts) {
      assert.equal(spacer.nominal_washer_ring_reference.uniform_load_ring_outer_radius_mm, 19.05/2);
      assert.equal(spacer.spacer_strength_nut_contact_or_compatible_pressure_bound, null);
      assert.equal(spacer.ideal_projection_is_not_actual_contact_or_pressure_bound, true);
    }
    assert.equal(row.support_screen.actual_no_slip_or_overturning_qualified, false);
    assert.equal(row.support_screen.floor_friction_or_contact_pressure_capacity, null);
  }
  const finished = report.targeted_finished_sections;
  assert.deepEqual(finished.producer, report.section_producer);
  assert.equal(finished.selected_unique_planes, 38);
  assert.equal(finished.same_plane_case_comparisons, 228);
  assert.equal(finished.members, 22);
  assert.equal(finished.planes.length, 38);
  assert.equal(new Set(finished.planes.map(r => `${r.member}/${r.station_global_grain_projection_mm}`)).size, 38);
  assert.equal(new Set(finished.planes.map(r => r.member)).size, 22);
  assert.equal(finished.continuous_finished_member_resistance, null);
  assert.deepEqual(finished.per_case_worst_witnesses.map(r => r.case_id), forces.case_sequence);
  function validateFinishedWitness(witness, expectedCase = witness.case_id) {
    const binding = forces.cases.find(r => r.case_id === expectedCase);
    const plane = finished.planes.find(r => r.member === witness.member
      && r.station_global_grain_projection_mm === witness.station_global_grain_projection_mm);
    assert.ok(binding && plane, 'own case and selected finished plane required');
    assert.equal(witness.case_id, expectedCase);
    assert.equal(witness.state_id, binding.state_id);
    assert.equal(witness.finished_area_mm2, plane.finished_area_mm2);
    assert.equal(witness.finished_shear_torsion_fracture_or_stability_resistance, null);
    for (const value of [witness.normal_reference.fully_braced_linear_normal_CD1_reference_index,
      witness.necessary_mean_shear_over_CD1_Fv]) assert.ok(Number.isFinite(value) && value >= 0);
  }
  const finishedScalars = finished.all_selected_plane_reference_scalars;
  const planeCaseID = w => JSON.stringify([w.case_id, w.member, w.station_global_grain_projection_mm]);
  assert.equal(finishedScalars.length, 228);
  assert.deepEqual(finishedScalars.map(planeCaseID).sort(), finished.planes.flatMap(p =>
    forces.case_sequence.map(case_id => planeCaseID({...p, case_id}))).sort());
  for (const scalar of finishedScalars) {
    assert.equal(scalar.state_id, forces.cases.find(r => r.case_id === scalar.case_id).state_id);
    for (const value of [scalar.fully_braced_linear_normal_CD1_reference_index,
      scalar.necessary_mean_shear_over_CD1_Fv]) assert.ok(Number.isFinite(value) && value >= 0);
    if (scalar.fully_braced_linear_normal_CD1_reference_index > 1 || scalar.necessary_mean_shear_over_CD1_Fv > 1) {
      validateFinishedWitness(scalar.exceedance_witness, scalar.case_id);
      assert.equal(planeCaseID(scalar.exceedance_witness), planeCaseID(scalar));
      assert.equal(scalar.exceedance_witness.normal_reference.fully_braced_linear_normal_CD1_reference_index,
        scalar.fully_braced_linear_normal_CD1_reference_index);
      assert.equal(scalar.exceedance_witness.necessary_mean_shear_over_CD1_Fv, scalar.necessary_mean_shear_over_CD1_Fv);
    } else assert.equal(scalar.exceedance_witness, null);
  }
  for (const [i, row] of finished.per_case_worst_witnesses.entries())
    for (const key of ['normal_worst', 'necessary_shear_worst']) {
      validateFinishedWitness(row[key], row.case_id);
      assert.equal(row[key].state_id, forces.cases[i].state_id);
      const scalar = finishedScalars.find(r => planeCaseID(r) === planeCaseID(row[key]));
      assert.equal(row[key].normal_reference.fully_braced_linear_normal_CD1_reference_index,
        scalar.fully_braced_linear_normal_CD1_reference_index);
      assert.equal(row[key].necessary_mean_shear_over_CD1_Fv, scalar.necessary_mean_shear_over_CD1_Fv);
      const metric = key === 'normal_worst' ? 'fully_braced_linear_normal_CD1_reference_index' : 'necessary_mean_shear_over_CD1_Fv';
      assert.equal(scalar[metric], Math.max(...finishedScalars.filter(r => r.case_id === row.case_id).map(r => r[metric])));
    }
  for (const [globalKey, worstKey, exceedanceKey, scalarKey, metric] of [
    ['maximum_normal_reference', 'normal_worst', 'all_selected_plane_normal_reference_exceedances',
      'fully_braced_linear_normal_CD1_reference_index',
      w => w.normal_reference.fully_braced_linear_normal_CD1_reference_index],
    ['maximum_necessary_mean_shear', 'necessary_shear_worst', 'all_selected_plane_necessary_shear_reference_exceedances',
      'necessary_mean_shear_over_CD1_Fv',
      w => w.necessary_mean_shear_over_CD1_Fv],
  ]) {
    const global = finished[globalKey], exceedances = finished[exceedanceKey];
    validateFinishedWitness(global);
    const owner = finished.per_case_worst_witnesses.find(r => r.case_id === global.case_id);
    assert.deepEqual(global, owner[worstKey]);
    assert.equal(metric(global), Math.max(...finished.per_case_worst_witnesses.map(r => metric(r[worstKey]))));
    assert.ok(Array.isArray(exceedances), 'finished exceedance disclosure required');
    assert.deepEqual(exceedances, finishedScalars.filter(r => r[scalarKey] > 1).map(r => r.exceedance_witness));
    assert.equal(new Set(exceedances.map(w => `${w.case_id}/${w.member}/${w.station_global_grain_projection_mm}`)).size, exceedances.length);
    for (const witness of exceedances) {
      validateFinishedWitness(witness);
      const own = finished.per_case_worst_witnesses.find(r => r.case_id === witness.case_id)[worstKey];
      assert.ok(metric(witness) > 1 && metric(witness) <= metric(own), 'strict own-case finished exceedance required');
    }
    for (const row of finished.per_case_worst_witnesses) {
      const worst = row[worstKey];
      if (metric(worst) > 1) assert.deepEqual(exceedances.find(w => w.case_id === row.case_id
        && w.member === worst.member && w.station_global_grain_projection_mm === worst.station_global_grain_projection_mm), worst);
    }
  }
  assert.equal(report.static_geometry_only_reused.historical_actions_ratios_or_passes_transferred, false);
  assert.deepEqual(report.static_geometry_only_reused.source, index.structural_assessment);
  assert.ok(Object.keys(report.missing_inputs).length >= 8);
  assert.ok(Number.isInteger(report.source_union.count) && report.source_union.count > 1524);
  assert.equal(report.source_union.all_sources_unchanged, true);
  assert.match(report.source_union.canonical_sha256, /^[a-f0-9]{64}$/);
  assert.ok(report.source_union.record.path.startsWith(raw + 'summary-source-map-'));
}

export function validateEngineeringAssessment(report, index) {
  const forces = JSON.parse(bound(index.current_response.cases));
  const components = JSON.parse(bound(index.current_response.components));
  assert.equal(report.schema, 'eoere_current_engineering_assessment/v1');
  assert.equal(report.status, 'ENGINEERING_ASSESSMENT_COMPLETE_ACCEPTANCE_NOT_ESTABLISHED');
  assert.deepEqual(report.geometry, index.geometry.receipt);
  assert.deepEqual(report.hardware_model, index.hardware_model.receipt);
  assert.equal(report.geometry_revision, index.geometry.revision);
  assert.equal(report.hardware_revision, index.hardware_model.revision);
  assert.deepEqual(report.current_response, index.current_response.cases);
  assert.deepEqual(report.current_components, index.current_response.components);
  assert.equal(report.producer.path, 'scripts/eoere_engineering_assessment.py');
  bound(report.producer);
  assert.equal(report.screw_panel_exceedance_resolution_deferred_by_owner, true);
  for (const key of ['screw_panel_load_path_removed_or_capacity_accepted', 'physical_demand_bounds_established',
    'structural_acceptance', 'native_solve_CAD_rebuild_or_remedy_performed']) assert.equal(report[key], false);
  for (const key of ['small_motion_threshold_adopted', 'complete_joint_resistance', 'finished_member_capacity'])
    assert.equal(report[key], null);
  assert.deepEqual(report.release, forces.release);
  assert.equal(report.all_input_sources_unchanged, true);
  assert.deepEqual(report.verified_input_unions, [forces.source_union, components.source_union]);
  assert.deepEqual(report.recorded_load_basis, {climber_lb: 250, downward_multiplier: 2,
    horizontal_force_n: 300, accessory_mass_kg: 25,
    dynamic_spectrum_or_all_hold_direction_envelope_verified: false});
  assert.deepEqual(report.equilibrium_wrench_reference_xyz_mm, [0, 750, 1100]);
  assert.deepEqual(Object.keys(report.recorded_hold_geometry).sort(), ['A1', 'A12', 'K12']);
  const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  assert.deepEqual(report.case_sequence, forces.case_sequence);
  assert.deepEqual(report.cases, forces.cases.map(r => Object.fromEntries(
    ['case_id', 'state_id', 'field', 'admission', 'operator_bundle'].map(k => [k, r[k]]))));
  assert.deepEqual(report.load_checks.map(r => r.case_id), forces.case_sequence);
  assert.deepEqual(report.active_action_load_path_screen.map(r => r.case_id), forces.case_sequence);
  const probe = report.finite_arm_contact_probe;
  assert.equal(probe.fixed_original_directors, true);
  assert.equal(probe.evaluated_at_saved_linear_state, true);
  assert.equal(probe.finite_equilibrium_contact_law_or_error_bound, false);
  assert.equal(probe.classification_tolerance_mm, 1e-8);
  assert.deepEqual(probe.cases.map(r => r.case_id), forces.case_sequence);
  assert.deepEqual(probe.contact_scalar_columns,
    ['linear_gap_mm', 'fixed_director_finite_arm_gap_mm', 'relative_linear_rotation_rad']);
  assert.equal(probe.contact_identities.length, 684);
  assert.equal(new Set(probe.contact_identities.map(r => r.contact_id)).size, 684);
  for (const identity of probe.contact_identities) {
    assert.ok(typeof identity.contact_id === 'string' && identity.contact_id.length > 0);
    assert.ok(['timber_face_contact', 'flange_contact'].includes(identity.kind));
    assert.ok(typeof identity.first === 'string' && typeof identity.second === 'string' && identity.first !== identity.second);
    assert.equal(identity.point_xyz_mm.length, 3);
    assert.ok(identity.point_xyz_mm.every(Number.isFinite));
  }
  const classification = g => g > probe.classification_tolerance_mm ? 1 : g < -probe.classification_tolerance_mm ? -1 : 0;
  const maximum = (rows, metric) => rows.reduce((best, row) => best === null || metric(row) > metric(best) ? row : best, null);
  for (const [i, c] of probe.cases.entries()) {
    const force = forces.cases[i], load = report.load_checks[i], routing = report.active_action_load_path_screen[i];
    assert.equal(c.state_id, force.state_id);
    assert.equal(c.physical_error_bound_or_response, false);
    assert.equal(c.contacts, 684);
    assert.equal(c.all_contact_scalars.length, c.contacts);
    const rows = c.all_contact_scalars.map((values, j) => {
      assert.equal(values.length, probe.contact_scalar_columns.length);
      assert.ok(values.every(Number.isFinite) && values[2] >= 0, 'finite own contact scalar census required');
      return {...probe.contact_identities[j], ...Object.fromEntries(probe.contact_scalar_columns.map((key, k) => [key, values[k]])),
        gap_change_mm: values[1]-values[0], linear_class: classification(values[0]), surrogate_class: classification(values[1])};
    });
    for (const [key, kind, expected] of [['timber_face_contacts', 'timber_face_contact', 332], ['flange_contacts', 'flange_contact', 352]]) {
      assert.equal(c[key], rows.filter(r => r.kind === kind).length);
      assert.equal(c[key], expected);
    }
    const changes = rows.filter(r => r.linear_class*r.surrogate_class === -1);
    for (const key of ['open_to_compressed', 'compressed_to_open', 'strict_open_compressed_class_changes'])
      assert.ok(Number.isInteger(c[key]) && c[key] >= 0 && c[key] <= c.contacts);
    assert.equal(c.strict_open_compressed_class_changes, changes.length);
    assert.equal(c.open_to_compressed, changes.filter(r => r.linear_class === -1).length);
    assert.equal(c.compressed_to_open, changes.filter(r => r.linear_class === 1).length);
    assert.deepEqual(c.maximum_absolute_gap_change, maximum(rows, r => Math.abs(r.gap_change_mm)));
    assert.deepEqual(c.maximum_relative_linear_rotation, maximum(rows, r => r.relative_linear_rotation_rad));
    assert.deepEqual(c.largest_gap_change_class_switch, maximum(changes, r => Math.abs(r.gap_change_mm)));
    assert.ok(Math.abs(c.maximum_relative_linear_rotation.relative_linear_rotation_rad-
      force.motion_diagnostics.maximum_relative_timber_or_fitting_strip_rotation_norm_rad) <= 1e-12);
    assert.equal(load.physical_load_rows, 835);
    assert.equal(load.numerical_load_basis_verified, true);
    for (const key of ['whole_force_xyz_n', 'whole_moment_about_origin_xyz_nmm', 'midplane_couple_xyz_nmm', 'load_point_xyz_mm']) {
      assert.equal(load[key].length, 3);
      assert.ok(load[key].every(Number.isFinite), `complete load vector required: ${key}`);
    }
    const horizontal = {'a12-forward': [0,-300], 'a12-rear': [0,300], 'a12-left': [-300,0],
      'k12-right': [300,0], 'k12-rear': [0,300], 'a1-rear': [0,300]}[c.case_id];
    assert.deepEqual(load.climber_force_xyz_n, [...horizontal, -250*2*4.4482216152605]);
    const sourceWrench = force.applied_load_checks.applied_wrench_about_reference_n_nmm;
    const referenceCouple = cross(report.equilibrium_wrench_reference_xyz_mm, sourceWrench.slice(0, 3));
    for (let j = 0; j < 3; j++) {
      assert.ok(Math.abs(load.whole_force_xyz_n[j]-sourceWrench[j]) < 1e-7);
      assert.ok(Math.abs(load.whole_moment_about_origin_xyz_nmm[j]-sourceWrench[j+3]-referenceCouple[j]) < 1e-5);
    }
    assert.equal(load.hold, c.case_id.split('-')[0].toUpperCase());
    const hold = report.recorded_hold_geometry[load.hold];
    assert.equal(load.panel, hold.panel);
    assert.deepEqual(load.load_point_xyz_mm, hold.load_point_xyz_mm);
    assert.equal(hold.panel_midplane_xyz_mm.length, 3);
    assert.ok(hold.panel_midplane_xyz_mm.every(Number.isFinite));
    const holdCouple = cross(hold.load_point_xyz_mm.map((x, j) => x-hold.panel_midplane_xyz_mm[j]), load.climber_force_xyz_n);
    for (let j = 0; j < 3; j++) assert.ok(Math.abs(load.midplane_couple_xyz_nmm[j]-holdCouple[j]) < 1e-5);
    assert.ok(Math.abs(load.permanent_and_accessory_weight_n-
      (forces.modeled_gravity.known_modeled_mass_kg+25)*9.80665) < 1e-7);
    assert.equal(routing.state_id, force.state_id);
    assert.equal(routing.physical_owners, 150);
    assert.equal(routing.physical_owner_ids.length, routing.physical_owners);
    assert.equal(new Set(routing.physical_owner_ids).size, routing.physical_owners);
    assert.ok(routing.physical_owner_ids.every(id => typeof id === 'string' && id.length > 0 && id !== 'floor'));
    assert.ok(routing.physical_owner_ids.includes(load.panel));
    assert.ok(Number.isInteger(routing.active_action_rows) && routing.active_action_rows >= 0);
    const floor = routing.physical_owners, graph = Array.from({length: floor+1}, () => new Set()), edgeKeys = new Set();
    let activeRows = 0;
    for (const edge of routing.active_edge_census) {
      assert.equal(edge.length, 3);
      const [first, second, count] = edge;
      assert.ok(Number.isInteger(first) && Number.isInteger(second) && first >= 0 && first < second && second <= floor);
      assert.ok(Number.isInteger(count) && count > 0);
      const key = `${first}/${second}`;
      assert.ok(!edgeKeys.has(key), 'unique active edge required'); edgeKeys.add(key);
      graph[first].add(second); graph[second].add(first); activeRows += count;
    }
    assert.equal(routing.active_action_rows, activeRows);
    const reached = new Set([floor]), pending = [floor];
    while (pending.length) for (const next of graph[pending.pop()]) if (!reached.has(next)) {reached.add(next); pending.push(next);}
    assert.deepEqual(routing.owners_without_active_action_path_to_floor,
      routing.physical_owner_ids.filter((id, j) => !reached.has(j)).sort());
    assert.equal(routing.force_threshold_n, 1e-6);
    assert.equal(routing.moment_threshold_nmm, 1e-5);
    assert.equal(routing.directional_restraint_capacity_or_complete_joint_behavior_qualified, false);
    assert.equal(routing.all_owners_have_active_action_path_to_floor, routing.owners_without_active_action_path_to_floor.length === 0);
  }
  const domains = components.cases[0].gross_member_stability.all_member_witness_records;
  assert.deepEqual(report.member_effective_length_domain, domains.map(r => ({member: r.member, full_span_mm: r.span_mm,
    maximum_effective_length_for_l_over_d_50_mm: r.weak_column_domain_limit_mm,
    maximum_effective_length_factor_for_full_span: r.weak_column_domain_limit_mm/r.span_mm,
    full_span_K1_outside_domain: r.span_mm > r.weak_column_domain_limit_mm,
    actual_effective_length_factor: null, bracing_or_member_strength_qualified: false})));
  assert.ok(report.contact_probe_rows.path.startsWith('fea/generated/selected-hardware-followup-v1/engineering-acceptance-v1/'));
  assert.match(report.contact_probe_rows.sha256, /^[a-f0-9]{64}$/);
}

function checkFrontPostRevision(index, entryChecks) {
  assert.equal(index.schema, 'bolted_frame_development_revisions/v2');
  const previous = index.preceding_revision;
  assert.ok(previous, 'preserved preceding revision required');
  checkDevelopment(previous, {entryChecks: false});
  for (const key of ['candidate', 'evidence_candidate', 'selected_baseline'])
    assert.deepEqual(index[key], previous[key], `preserved authority: ${key}`);
  for (const key of ['fabrication_released', 'climbing_released']) assert.equal(index[key], false);
  for (const key of ['current_response', 'structural_assessment', 'engineering_assessment'])
    assert.equal(index[key], null, `new response/acceptance cannot be inherited: ${key}`);
  const geometry = JSON.parse(bound(index.geometry.receipt));
  assert.equal(geometry.schema, 'eoere_front_posts_4x6_geometry/v1');
  assert.equal(index.geometry.revision, geometry.revision);
  assert.equal(geometry.revision, 'eoere-4x6-front-posts-v1');
  assert.equal(geometry.candidate, index.evidence_candidate);
  bound({path: 'scripts/eoere_front_posts_4x6.py', sha256: geometry.source_sha256['scripts/eoere_front_posts_4x6.py']});
  assert.deepEqual(geometry.parent_geometry, previous.geometry.receipt);
  assert.deepEqual(geometry.parent_hardware, previous.hardware_model.receipt);
  assert.deepEqual(geometry.parent_shop, previous.shop.result);
  const parent = JSON.parse(bound(geometry.parent_geometry));
  const axes = parent.axes.map(a => geometry.axis_overrides[a.id] || a);
  assert.equal(axes.length, 100);
  assert.equal(Object.keys(geometry.axis_overrides).length, 8);
  for (const [i, a] of axes.entries()) {
    const old = parent.axes[i];
    assert.deepEqual(a.direction_xyz, old.direction_xyz);
    assert.equal(a.diameter_mm, old.diameter_mm);
    assert.equal(a.bore_diameter_mm, old.bore_diameter_mm);
    const delta = a.point_xyz_mm.map((v, j) => v-old.point_xyz_mm[j]);
    const along = delta.reduce((sum, v, j) => sum+v*a.direction_xyz[j], 0);
    assert.ok(Math.hypot(...delta.map((v, j) => v-along*a.direction_xyz[j])) < 1e-8, `moved bolt line: ${a.id}`);
    assert.deepEqual(a.receivers, old.receivers);
  }
  assert.equal(geometry.unchanged_bolt_axis_lines, 100);
  assert.equal(geometry.unchanged_screw_axes, 66);
  const posts = ['base_post_outer_left', 'base_post_outer_right'];
  assert.deepEqual(Object.keys(geometry.profile_overrides).sort(), posts);
  for (const p of Object.values(geometry.profile_overrides)) {
    assert.deepEqual(p.blank_mm, [238.9, 139.7, 88.9]);
    assert.equal(p.inner_kicker_facing_longitudinal_bevel_mm, 9.525);
  }
  assert.equal(geometry.selected_stack_overrides.length, 8);
  for (const r of geometry.selected_stack_overrides) {
    const cleat = r.axis_id.startsWith('cleat_post_bolt_');
    assert.ok(Object.hasOwn(geometry.axis_overrides, r.axis_id));
    assert.equal(r.selected_underhead_length_mm, cleat ? 177.8 : 152.4);
    assert.equal(r.nut_side_spacer_mm, cleat ? 25.4 : 0);
    assert.equal(r.spacer_piece_count, cleat ? 2 : 0);
    for (const key of ['minimum_body_to_nominated_target_margin_mm', 'minimum_nut_seating_margin_mm', 'minimum_two_pitch_margin_mm'])
      assert.ok(Number.isFinite(r[key]) && r[key] > 0, `stack window: ${r.axis_id}/${key}`);
    assert.equal(r.Actual, ''); assert.equal(r.Disposition, '');
  }
  assert.equal(geometry.fixed_original_action_post_shear_screens.length, 12);
  assert.equal(geometry.maximum_fixed_action_post_shear_ratio,
    Math.max(...geometry.fixed_original_action_post_shear_screens.map(r => r.ratio_upper)));
  assert.ok(geometry.maximum_fixed_action_post_shear_ratio < .724);
  assert.equal(geometry.inner_kicker_facing_longitudinal_bevel_mm, 9.525);
  assert.equal(geometry.minimum_full_depth_rectangular_core_width_mm, 79.375);
  assert.equal(geometry.service_census.parts, 405);
  assert.equal(geometry.service_census.post_service_comparisons, 810);
  assert.equal(geometry.service_census.all_clear, true);
  assert.equal(geometry.service_census.unbeveled_stock_failures.length, 2);
  assert.deepEqual(geometry.service_census.refined_queries.map(r => r.service).sort(), ['hold_tnut_kicker_1', 'hold_tnut_kicker_10']);
  assert.ok(geometry.service_census.refined_queries.every(r => r.intersection_volume_mm3 < 1e-7 && r.minimum_distance_mm > 2));
  assert.equal(geometry.new_response_computed, false);
  assert.equal(geometry.analysis_pass_transferred, false);
  assert.ok(Object.values(geometry.release).every(v => v === false));
  const decoded = gunzipSync(bound(index.geometry.scene));
  assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
  const scene = validateFrontPosts(JSON.parse(decoded), index.geometry.receipt.sha256);
  assert.deepEqual(scene.layout_report, index.geometry.receipt);
  assert.equal(index.geometry.viewer, scene.keys.base);
  assert.equal(index.optional_grid.viewer, scene.keys.extra);
  assert.equal(index.optional_grid.default_enabled, false); assert.equal(index.optional_grid.official, false);
  assert.deepEqual(index.optional_grid.receipt, index.geometry.receipt);
  assert.deepEqual(index.optional_grid.inherited_grid_receipt, previous.optional_grid.receipt);
  assert.equal(index.hardware_model.revision, geometry.revision);
  assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
  assert.deepEqual(index.hardware_model.scene, index.geometry.scene);
  assert.deepEqual(index.hardware_model.viewers, scene.keys);
  assert.equal(index.hardware_model.analysis_pass_transferred, false);
  assert.equal(index.hardware_model.actual_parts_verified, false);
  assert.deepEqual(index.shop.geometry, index.geometry.receipt);
  assert.deepEqual(index.shop.result, index.geometry.receipt);
  assert.equal(index.shop.revision, geometry.revision);
  assert.equal(index.shop.shop_planning_only, true);
  assert.equal(index.shop.affected_installation_qualified, false);
  assert.equal(index.shop.overrides.length, 3);
  for (const ref of index.shop.overrides) {
    bound(ref);
    assert.equal(ref.sha256, geometry.shop_overrides[path.posix.basename(ref.path)].sha256);
  }
  assert.deepEqual(index.hardware_model.shop_override, index.shop.overrides[0]);
  assert.ok(read(index.shop.packet).toString().includes(geometry.revision));
  const html = read('site/index.html').toString();
  for (const model of Object.values(scene.keys)) assert.equal(viewerModel(html, model), model);
  assert.equal(viewerModel(html, null), index.selected_baseline.candidate);
  if (entryChecks) assert.ok(html.includes(`href="?model=${index.geometry.viewer}&view=rear">Current eoere geometry`));
  for (const [key, value] of Object.entries({url: path.basename(index.geometry.scene.path),
    expectedSha256: index.geometry.scene.sha256, decodedSha256: index.geometry.scene.decoded_sha256,
    layoutSha256: index.geometry.receipt.sha256})) {
    assert.ok(html.includes(`${key}: frontPosts ? '${value}'`), `current scene binding: ${key}`);
  }
  if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
    validateEntry(read(name).toString(), index);
  assert.ok(read('docs/bolted-frame-development/README.md').toString().trimEnd().split('\n').length <= 150);
  return {passed: true, revision: geometry.revision, bolt_axes: 100, screw_axes: 66,
    maximum_fixed_original_action_post_shear_ratio: geometry.maximum_fixed_action_post_shear_ratio,
    current_response_revision: null, previous_response_revision: previous.current_response.revision,
    mechanics_executed: false, full_ignored_input_closure_checked: false};
}

// Proposal insertion before checkDevelopment in scripts/check_bolted_development.mjs.
// Uses that file's assert, sha, bound, gunzipSync, referenceKeys,
// referenceBinding, referenceIndex, referenceClose, CURRENT_CASES and isDeepStrictEqual.
const V10_CANDIDATE13_ORIGIN = '/mnt/c/Users/mckay/Documents/Codex/2026-10-23/task-3/v10-isolated/';
const V10_CANDIDATE13_ROOT = 'docs/bolted-frame-development/owner-frame-v10/candidate13/';
const V10_CANDIDATE13_LOAD = {weight_lb: 250, downward_multiplier: 2,
  horizontal_force_N: 300, accessory_mass_kg: 25, duration_factor_CD: 1};
const V10_CANDIDATE13_GEOMETRY_SHA = V10_SCENE.layoutSha256;
const V10_CANDIDATE13_SCENE_SHA = V10_SCENE.expectedSha256;
const V10_CANDIDATE13_SCENE_DECODED_SHA = V10_SCENE.decodedSha256;
const V10_CANDIDATE13_FAMILIES = ['cleat_actual_perimeter_rows', 'direct_elastic_steel',
  'reduced_connection_axial_bending', 'timber_net_shear_torsion',
  'timber_normal_and_stability', 'wood_bearing_whole_affine'];

function v10FrozenReference(ref, expectedPath) {
  assert.ok(ref && typeof ref.path === 'string' && ref.path.startsWith(V10_CANDIDATE13_ORIGIN),
    'Candidate13 original reference must stay in its frozen source package');
  assert.ok(ref.path.slice(V10_CANDIDATE13_ORIGIN.length).split('/').every(part =>
    part && part !== '.' && part !== '..'), 'unambiguous original source path required');
  assert.match(ref.sha256, /^[a-f0-9]{64}$/);
  if (expectedPath !== undefined) assert.equal(ref.path, V10_CANDIDATE13_ORIGIN+expectedPath);
}

export function candidate13SourceResolver(manifest, readIntegrated = bound) {
  validateV10Provenance(manifest);
  const rows = [...Object.values(manifest.artifacts), ...manifest.support_files];
  const originals = new Map(), integrated = new Map();
  for (const row of rows) {
    const encoded = readIntegrated(row.integrated);
    assert.equal(encoded.length, row.integrated.bytes, 'integrated file length changed');
    assert.equal(sha(encoded), row.integrated.sha256, 'integrated encoded bytes changed');
    const decoded = row.encoding === 'gzip' ? gunzipSync(encoded) : encoded;
    assert.equal(decoded.length, row.original.bytes, 'frozen original file length changed');
    assert.equal(sha(decoded), row.original.sha256, 'frozen original bytes changed during integration');
    originals.set(row.original.path, decoded);
    integrated.set(row.integrated.path, row);
  }
  return {
    sourceBound(ref) {
      resolveV10SourceRef(ref, manifest);
      return originals.get(ref.path);
    },
    originalFor(ref, relative) {
      referenceBinding(ref, V10_CANDIDATE13_ROOT+relative);
      const row = integrated.get(ref.path);
      assert.ok(row && row.encoding === 'identity' && row.integrated.sha256 === ref.sha256,
        'index roots must name the byte-identical small copied record');
      assert.equal(row.original.path, V10_CANDIDATE13_ORIGIN+relative);
      return {path: row.original.path, sha256: row.original.sha256};
    },
  };
}

export function readV10Candidate13Authority(index, readIntegrated = bound) {
  referenceBinding(index.integration_manifest, 'site/eoere-v10-candidate13-provenance.json');
  const manifestBytes = readIntegrated(index.integration_manifest);
  assert.equal(sha(manifestBytes), V10_PROVENANCE_SHA256);
  assert.equal(index.integration_manifest.sha256, V10_PROVENANCE_SHA256);
  const manifest = JSON.parse(manifestBytes);
  const resolver = candidate13SourceResolver(manifest, readIntegrated);
  const refs = {}, data = {manifest};
  for (const [key, ref, relative] of [
    ['geometry', index.geometry.receipt, 'geometry-receipt-13.json'],
    ['delivery', index.delivery_bundle, 'delivery-bundle-13.json'],
    ['validation', index.delivery_validation, 'delivery-validation-13.json'],
    ['bank', index.response_bank, 'response-bank-13.json'],
    ['review', index.engineering_review, 'reference-review-13.json'],
    ['inventory', index.exceedance_inventory, 'analysis-attempt-08/reference-attempt-01/complete-exceedance-inventory.json'],
    ['joint', index.joint_applicability, 'joint-applicability-13-canonical-wsl.json'],
    ['paper', index.paper_audit, 'paper-audit/paper-audit-bundle-v1.json'],
    ['edgeCorrection', index.center_principal_correction, 'paper-audit/center-principal-correction-13-v1.json'],
    ['correctedCompletion', index.corrected_completion_index, 'paper-audit/completion-index-v3.json'],
    ['readiness', index.shop.readiness, 'packet-13-complete/readiness.json'],
  ]) {
    refs[key] = resolver.originalFor(ref, relative);
    data[key] = JSON.parse(resolver.sourceBound(refs[key]));
  }
  assert.equal(refs.geometry.sha256, V10_CANDIDATE13_GEOMETRY_SHA);
  refs.groupHandoff = resolver.originalFor(index.group_replacement_handoff,
    'paper-audit/wsl-group-and-relocation-handoff-v1.txt');
  resolver.sourceBound(refs.groupHandoff);
  // Authenticate every mapped delivery/paper artifact, but never follow raw
  // field references or inherited source paths outside that explicit mapping.
  for (const ref of [...Object.values(data.delivery.artifacts), ...data.paper.artifacts]) resolver.sourceBound(ref);
  for (const [key, name] of Object.entries({clearance: 'clearance', rawGeometry: 'geometry_raw',
    geometryJoin: 'geometry_viewer_join', jointBank: 'joint_bank_scope'}))
    data[key] = JSON.parse(resolver.sourceBound(data.delivery.artifacts[name]));
  for (const [key, relative] of Object.entries({group: 'paper-audit/group-action-overlap-review-13-v2.json',
    groupSeal: 'paper-audit/group-paper-final-binding-13.json',
    method: 'paper-audit/candidate13-group-factor-method-audit-v2.json'})) {
    const ref = data.paper.artifacts.find(row => row.path === V10_CANDIDATE13_ORIGIN+relative);
    assert.ok(ref, 'current paper audit record required');
    data[key] = JSON.parse(resolver.sourceBound(ref));
  }
  const sceneRef = data.delivery.artifacts.viewer_scene;
  v10FrozenReference(sceneRef, 'site/eoere-v10-scene-13.json.gz');
  assert.equal(sceneRef.sha256, V10_CANDIDATE13_SCENE_SHA);
  referenceKeys(index.geometry.scene, ['path', 'sha256', 'decoded_sha256'], 'current scene binding');
  assert.equal(index.geometry.scene.path, 'site/eoere-v10-scene-13.json.gz');
  assert.equal(index.geometry.scene.sha256, V10_CANDIDATE13_SCENE_SHA);
  assert.equal(index.geometry.scene.decoded_sha256, V10_CANDIDATE13_SCENE_DECODED_SHA);
  const sceneBytes = gunzipSync(resolver.sourceBound(sceneRef));
  assert.equal(sha(sceneBytes), index.geometry.scene.decoded_sha256);
  const scene = JSON.parse(sceneBytes);
  validateV10SceneProvenance(scene, manifest);
  referenceBinding(index.continuation_evaluation,
    'docs/bolted-frame-development/owner-frame-v10/continuation-evaluation.json');
  const continuationBytes = readIntegrated(index.continuation_evaluation);
  assert.equal(sha(continuationBytes), index.continuation_evaluation.sha256);
  data.continuation = JSON.parse(continuationBytes);
  referenceBinding(index.standard_top_stock_evaluation.evidence,
    'docs/bolted-frame-development/owner-frame-v10/standard-top-stock-evaluation.json');
  const stockBytes = readIntegrated(index.standard_top_stock_evaluation.evidence);
  assert.equal(sha(stockBytes), index.standard_top_stock_evaluation.evidence.sha256);
  data.standardTopStock = JSON.parse(stockBytes);
  const groupCriteria = data.standardTopStock.fallback.physical_row_group_criteria;
  for (const [key, ref, filename] of [
    ['activeConnectionCriteria', groupCriteria.active_criteria, 'active-connection-criteria.json'],
    ['groupRowComparison', groupCriteria.comparison, 'group-row-comparison-v1.json'],
  ]) {
    referenceBinding(ref, 'docs/bolted-frame-development/owner-frame-v10/standard-top-stock/'+filename);
    data[key] = JSON.parse(bound(ref));
  }
  referenceBinding(groupCriteria.producer,
    'docs/bolted-frame-development/owner-frame-v10/standard-top-stock/group_row_comparison_v1.py');
  bound(groupCriteria.producer);
  referenceBinding(index.development_selection.owner_decision,
    'docs/bolted-frame-development/owner-frame-v10/owner-selected-standard-4x6-top-v1.json');
  data.ownerDecision = JSON.parse(bound(index.development_selection.owner_decision));
  referenceBinding(index.development_selection.readable_owner_decision,
    'docs/bolted-frame-development/owner-frame-v10/owner-selected-standard-4x6-top-v1.txt');
  bound(index.development_selection.readable_owner_decision);
  data.stockRecords = {};
  for (const [key, role, filename] of [
    ['bank', 'response_bank', '4x6-v2-response-bank.json'],
    ['review', 'reference_review', '4x6-v2-reference-review.json'],
    ['inventory', 'trial_inventory', '4x6-v2-trial-inventory.json'],
    ['receipt', 'geometry_receipt', '4x6-v2-geometry-receipt.json'],
  ]) {
    const ref = data.standardTopStock.fallback.matched_results[role];
    referenceBinding(ref, 'docs/bolted-frame-development/owner-frame-v10/standard-top-stock/'+filename);
    const bytes = readIntegrated(ref);
    assert.equal(sha(bytes), ref.sha256);
    data.stockRecords[key] = JSON.parse(bytes);
  }
  return {...data, refs, scene};
}

export function validateV10Candidate13Authority(index, data) {
  const {geometry, delivery, validation, bank, review, inventory, joint, paper,
    readiness, clearance, rawGeometry, geometryJoin, jointBank, group, groupSeal, method,
    edgeCorrection, correctedCompletion, continuation, scene, refs} = data;
  assert.equal(index.schema, 'bolted_frame_development_revisions/v15');
  assert.equal(index.candidate, 'compact-bolted-frame-development');
  assert.equal(index.evidence_candidate, 'compact-floor-flush-eoere-bolted-development');
  assert.equal(index.geometry.revision, V10_CANDIDATE13_REVISION);
  assert.equal(index.geometry.viewer, 'eoere-current-frame-development');
  assert.equal(index.preceding_revision.schema, 'bolted_frame_development_revisions/v14');
  assert.equal(index.preceding_revision.geometry.revision, 'eoere-single-spacer-cleat-stacks-v9');
  assert.equal(index.preceding_revision.geometry.receipt.sha256, '29db14a7cb6aaf37e5f65ab23f6c9362b1429456a29d4ca02c0e1d5266af00ef');
  assert.equal(index.preserved_owner_v9_viewer, 'eoere-owner-frame-v9-development');
  assert.deepEqual(index.selected_baseline, {authority: 'current-candidate.json', candidate: 'compact-floor-flush-development'});
  assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
  assert.equal(index.conditional_frame_evaluation, null);
  assert.equal(index.panel_Hillman_resolution_deferred, true);
  assert.equal(index.shop.shop_planning_only, true);
  assert.equal(index.shop.instructions_current_for_fabrication, false);
  assert.equal(index.shop.packet, V10_CANDIDATE13_ROOT+'packet-13-complete/builder-plan.md');
  for (const row of [index.hardware_model, index.shop]) {
    assert.equal(row.revision, index.geometry.revision);
    assert.deepEqual(row.receipt ?? row.geometry, index.geometry.receipt);
  }
  for (const key of ['selected_for_build', 'actual_parts_verified', 'analysis_pass_transferred'])
    assert.equal(index.hardware_model[key], false);
  const falseClaims = (row, keys = ['structural_acceptance', 'fabrication_released', 'climbing_released']) => {
    for (const key of keys) assert.equal(row[key], false, `Candidate13 claim boundary: ${key}`);
  };
  falseClaims(index, ['structural_acceptance', 'complete_joint_qualified', 'physical_operations_authorized',
    'fabrication_released', 'climbing_released']);
  for (const row of [geometry, delivery, validation, bank, review, joint, paper, readiness, group, groupSeal, method, inventory]) {
    if ('geometry_revision' in row) assert.equal(row.geometry_revision, index.geometry.revision);
    if ('physical_geometry' in row) assert.deepEqual(row.physical_geometry, refs.geometry);
    for (const [key, value] of Object.entries(row))
      if (/(?:^structural_acceptance$|^fabrication_released$|^climbing_released$|_qualified$|_adopted$|^physical_operations_authorized$|^physical_force_bounds_established$)/.test(key))
        assert.ok(value === false || value === null, `Candidate13 must retain unresolved ${key}`);
  }
  for (const row of [delivery, bank, review, paper, readiness, group, groupSeal, method, inventory]) falseClaims(row);
  falseClaims(geometry, ['fabrication_released', 'climbing_released']);
  falseClaims(delivery, ['complete_joint_qualified', 'physical_force_bounds_established', 'physical_operations_authorized']);
  assert.equal(delivery.schema, 'eoere_v10_delivery_bundle/v1');
  assert.equal(geometry.schema, 'eoere_v10_geometry_revision/v1');
  assert.equal(geometry.revision, index.geometry.revision);
  assert.equal(geometry.iteration, '13');
  assert.deepEqual(geometry.counts, V10_CANDIDATE13_COUNTS);
  assert.deepEqual(geometry.parent_geometry, {path: '/home/mckay-linux/repos/mini-moonboard/'+index.preceding_revision.geometry.receipt.path,
    sha256: index.preceding_revision.geometry.receipt.sha256});
  assert.equal(geometry.geometry_adopted, false);
  assert.equal(geometry.complete_joint_qualified, false);
  assert.equal(geometry.complete_conditional_frame_evaluation, false);
  assert.equal(geometry.catalog_delivery_or_strength_qualified, false);
  assert.equal(geometry.actual_observations, null);
  assert.equal(geometry.nominal_geometry_clear, true);
  assert.equal(rawGeometry.revision, index.geometry.revision);
  assert.equal(rawGeometry.axes.length, 116);
  const axes = new Set(rawGeometry.axes.map(row => row.id)); assert.equal(axes.size, 116);
  assert.equal(Object.keys(rawGeometry.profiles).length, 32);
  assert.equal(rawGeometry.fitting_poses.length, 24); assert.equal(rawGeometry.screw_axes.length, 66);
  assert.deepEqual(geometry.checked_geometry, delivery.artifacts.geometry_raw);
  assert.deepEqual(geometry.checked_clearance, delivery.artifacts.clearance);
  assert.deepEqual(clearance.geometry, geometry.checked_geometry);
  assert.equal(clearance.nominal_geometry_clear, true); assert.equal(clearance.occupied_part_count, 1167);
  assert.deepEqual(clearance.collisions, []); assert.deepEqual(clearance.missing_candidates, []);
  for (const key of ['release', 'strength_qualified', 'actual_tools_or_hardware_verified']) assert.equal(clearance[key], false);
  for (const [role, key] of Object.entries({geometry: 'geometry', bank: 'response_bank', review: 'reference_review',
    inventory: 'exceedance_inventory', joint: 'joint_applicability', readiness: 'readiness'}))
    assert.deepEqual(refs[role], delivery.artifacts[key], 'current index must join the exact frozen delivery artifact');
  assert.equal(validation.status, 'validated_conditional_delivery');
  assert.equal(validation.artifacts_checked, Object.keys(delivery.artifacts).length);
  assert.equal(validation.cases_checked, 6);
  for (const row of [delivery, bank, review, jointBank, method]) assert.deepEqual(row.load_contract, V10_CANDIDATE13_LOAD);
  for (const row of [delivery, bank, review]) assert.deepEqual([...row.case_ids].sort(), [...CURRENT_CASES].sort());
  assert.equal(bank.schema, 'eoere_v10_own_response_bank/v1');
  assert.equal(bank.admission_gate_N, 1e-5); assert.equal(bank.all_six_cases_admitted, true);
  assert.equal(bank.historical_force_pass_transferred, false);
  assert.deepEqual(bank.analysis_inventory, {bodies: 170, fittings: 24, ports: 112, roles: 626, shafts: 116, walls: 144, wood: 24});
  assert.deepEqual(bank.cases.map(row => row.case_id).sort(), [...CURRENT_CASES].sort());
  for (const [name, suffix] of Object.entries({analysis_geometry: 'geometry/geometry.json', material: 'material.json',
    inputs: 'four-hosts/preparation/inputs.json', prepared_readiness: 'adapter-readiness.json'}))
    v10FrozenReference(bank[name], 'analysis-attempt-08/'+suffix);
  const fields = {};
  for (const row of bank.cases) {
    assert.equal(row.both_independent_replays_admitted, true);
    referenceIndex(row.gradient_inf_N, 'Candidate13 equilibrium residual'); assert.ok(row.gradient_inf_N < 1e-5);
    for (const [key, file] of Object.entries({field: 'field.json', independent_replay: 'independent-replay.json',
      independent_plywood_replay: 'independent-replay-plywood.json', replay_binding: 'v10-replay-binding.json'}))
      v10FrozenReference(row[key], `analysis-attempt-08/four-hosts/${row.case_id}/${file}`);
    fields[row.case_id] = row.field;
  }
  assert.equal(bank.maximum_gradient_inf_N, Math.max(...bank.cases.map(row => row.gradient_inf_N)));
  for (const row of [review, inventory, method]) {
    assert.deepEqual(row.analysis_geometry, bank.analysis_geometry);
    assert.deepEqual(row.field_bindings, fields, 'reference fields must be the own admitted Candidate13 bank');
  }
  assert.equal(review.schema, 'eoere_v10_reference_review/v1');
  assert.deepEqual(review.response_bank, refs.bank);
  assert.equal(review.all_declared_numerical_references_below_one, false);
  referenceKeys(review.numerical_reference_maxima, V10_CANDIDATE13_FAMILIES, 'Candidate13 reference families');
  referenceKeys(inventory.source_families, V10_CANDIDATE13_FAMILIES, 'Candidate13 inventory sources');
  for (const [family, row] of Object.entries(review.numerical_reference_maxima)) {
    referenceIndex(row.index, 'Candidate13 reference maximum');
    assert.ok(CURRENT_CASES.includes(row.case_id) && typeof row.component === 'string');
    assert.equal(row.above_reference, row.index > 1);
    v10FrozenReference(row.worksheet, `analysis-attempt-08/reference-attempt-01/${family}.json`);
    assert.deepEqual(row.worksheet, inventory.source_families[family]);
    if ('complete_Cdelta' in row) assert.equal(row.complete_Cdelta, null);
    if (family === 'wood_bearing_whole_affine' || family === 'reduced_connection_axial_bending')
      referenceClose(row.index*row.Cg, row.individual_reference_before_Cg, 'unadopted trial decomposition');
  }
  assert.equal(inventory.schema, 'eoere_v10_complete_reference_flag_inventory/v1');
  const flags = inventory.above_reference_case_rows;
  assert.equal(inventory.count_above_reference_case_rows, 26); assert.equal(flags.length, 26);
  const keys = new Set();
  for (const row of flags) {
    assert.ok(CURRENT_CASES.includes(row.case_id) && axes.has(row.component));
    assert.equal(row.criterion, 'wood_bearing_whole_affine');
    assert.equal(row.complete_Cdelta, null);
    assert.ok(Number.isFinite(row.index) && row.index > 1 && Number.isFinite(row.Cg) && row.Cg > 0 && row.Cg <= 1);
    referenceClose(row.index*row.Cg, row.individual_reference_before_Cg, 'trial factor is arithmetic only');
    const key = `${row.case_id}/${row.component}/${row.criterion}`;
    assert.ok(!keys.has(key), 'duplicate trial flag'); keys.add(key);
  }
  for (const rows of [delivery.remaining_numerical_exceedances, validation.remaining_numerical_exceedances,
    readiness.above_reference_case_rows]) assert.deepEqual(rows, flags, 'all 26 original trial flags must remain intact');
  const maxima = [...new Set(flags.map(row => row.component))].sort().map(component =>
    flags.filter(row => row.component === component).reduce((a, b) => a.index >= b.index ? a : b));
  assert.equal(maxima.length, 13);
  const byComponent = rows => [...rows].sort((a, b) => a.component.localeCompare(b.component));
  assert.deepEqual(byComponent(inventory.component_maxima), byComponent(maxima));
  assert.deepEqual(byComponent(readiness.component_maxima), byComponent(maxima));
  assert.equal(readiness.count_above_reference_case_rows, 26);
  const worst = flags.reduce((a, b) => a.index >= b.index ? a : b);
  const trialValues = row => Object.fromEntries(['case_id', 'component', 'index', 'Cg',
    'complete_Cdelta', 'individual_reference_before_Cg'].map(key => [key, row[key]]));
  assert.deepEqual(trialValues(review.numerical_reference_maxima.wood_bearing_whole_affine), trialValues(worst));
  assert.equal(readiness.schema, 'eoere_v10_shop_planning_readiness/v1');
  assert.equal(readiness.status, 'COMPLETE_REFERENCE_FLAGS_AND_PHYSICAL_HOLD');
  assert.deepEqual(readiness.v10_geometry_receipt, refs.geometry); assert.deepEqual(readiness.v10_response_bank, refs.bank);
  assert.deepEqual(readiness.v10_component_review, refs.review);
  assert.equal(readiness.current_response_computed, true); assert.equal(readiness.complete_joint_qualified, false);
  assert.equal(readiness.credited_aggregate_wall_mm, 23.8); assert.equal(readiness.nominal_leaf_thickness_mm, 12.7);
  assert.equal(readiness.minimum_actual_leaf_thickness_hypothesis_mm, 11.9);
  assert.equal(readiness.side_depth_mm, 152.4); assert.deepEqual(readiness.top_rail_section_S_N_mm, [50.8, 139.7]);
  assert.equal(joint.schema, 'v10_joint_applicability_canonical_wsl_wrapper/v1');
  assert.equal(joint.review.axis_count, 116); assert.equal(joint.review.wood_occurrences, 158);
  falseClaims(joint.review, ['structural_acceptance', 'fabrication_released', 'climbing_released',
    'complete_geometry_factor_qualified', 'complete_group_action_qualified']);
  assert.equal(jointBank.schema, 'v10_candidate13_joint_applicability_bank_scope/v1');
  assert.deepEqual(jointBank.physical_geometry, refs.geometry); assert.deepEqual(jointBank.response_bank, refs.bank);
  assert.deepEqual(jointBank.applicability, refs.joint);
  for (const key of ['material', 'analysis_geometry', 'inputs', 'prepared_readiness']) assert.deepEqual(jointBank[key], bank[key]);
  assert.equal(jointBank.verified_proof_count, 24); assert.equal(jointBank.verified_case_proof_files.length, 24);
  const proofKeys = new Set();
  for (const row of jointBank.verified_case_proof_files) {
    const own = bank.cases.find(item => item.case_id === row.case_id);
    assert.ok(own && ['field', 'independent_replay', 'independent_plywood_replay', 'replay_binding'].includes(row.kind));
    assert.deepEqual(row.verified, own[row.kind]); proofKeys.add(`${row.case_id}/${row.kind}`);
  }
  assert.equal(proofKeys.size, 24);
  assert.equal(paper.schema, 'candidate13_bounded_paper_audit_bundle/v1');
  assert.equal(paper.status, 'bounded_paper_audit_complete_connection_acceptance_unresolved');
  assert.deepEqual(paper.candidate_geometry, refs.geometry); assert.deepEqual(paper.unchanged_response_bank, refs.bank);
  assert.deepEqual(paper.original_diagnostic_inventory, refs.inventory); assert.deepEqual(paper.prior_package_bundle, refs.delivery);
  assert.equal(paper.old_case_flags_preserved, true); assert.equal(paper.all13_component_maxima_and_dispositions_join_exactly, true);
  assert.equal(paper.actual_Cg_adopted, null); assert.equal(paper.actual_Cdelta_adopted, null);
  assert.equal(paper.old_trial_criterion_retained, 'wood_bearing_whole_affine');
  assert.equal(paper.candidate_geometry_changed, false); assert.equal(paper.global_reruns, 0);
  assert.equal(edgeCorrection.schema, 'candidate13_center_principal_correction/v1');
  assert.equal(edgeCorrection.net_actions_toward_near_edge_all_cases, false);
  assert.equal(edgeCorrection.fourD_both_edges_is_optional_conservative_envelope, true);
  assert.equal(edgeCorrection.established_NDS_near_edge_violation, false);
  assert.equal(edgeCorrection.idealized_resultant_edge_screen_clears, true);
  falseClaims(edgeCorrection, ['complete_oblique_eccentric_splitting_qualified', 'fabrication_released', 'climbing_released']);
  assert.equal(correctedCompletion.schema, 'v10_corrected_handoff_completion/v1');
  assert.equal(correctedCompletion.read_first_correction.sha256, refs.edgeCorrection.sha256);
  assert.equal(correctedCompletion.candidate_unchanged, true);
  falseClaims(correctedCompletion, ['full_connection_qualified', 'fabrication_released', 'climbing_released']);
  assert.equal(group.schema, 'candidate13_group_ownership_distribution_paper_audit/v2');
  assert.equal(group.per_component_dispositions.length, 13);
  assert.equal(group.signature_group_count, 52); assert.equal(group.wood_host_count, 24); assert.equal(group.steel_host_count, 24);
  assert.deepEqual(group.wood_actions_per_case, Array(6).fill(144));
  const dispositions = byComponent(group.per_component_dispositions);
  assert.deepEqual(dispositions.map(row => row.component), maxima.map(row => row.component));
  for (const row of dispositions) assert.deepEqual(row.worst_trial,
    trialValues(maxima.find(maximum => maximum.component === row.component)));
  for (const key of ['actual_model_equivalence_to_NDS_distribution_proven', 'actual_Cg_equal_1_adopted',
    'diagnostic_1_over_n_removed']) assert.equal(group.double_counting[key], false);
  assert.equal(groupSeal.schema, 'candidate13_group_paper_final_binding/v1');
  for (const row of [group, groupSeal]) {
    assert.deepEqual(row.physical_geometry, refs.geometry); assert.deepEqual(row.response_bank, refs.bank);
    falseClaims(row, ['complete_joint_qualified', 'complete_group_action_qualified', 'complete_geometry_factor_qualified']);
  }
  assert.equal(method.schema, 'candidate13-group-factor-method-audit-v1');
  assert.equal(method.current_above_one_case_rows, 26); assert.equal(method.current_above_one_component_rows.length, 13);
  assert.deepEqual(byComponent(method.current_above_one_component_rows).map(trialValues), byComponent(maxima).map(trialValues));
  assert.equal(continuation.schema, 'eoere_v10_candidate13_continuation_evaluation/v1');
  assert.equal(continuation.geometry_revision, index.geometry.revision);
  assert.deepEqual(continuation.candidate_geometry, index.geometry.receipt);
  assert.deepEqual(continuation.response_bank, index.response_bank);
  assert.equal(continuation.trial_flags_retained, 26);
  assert.equal(continuation.trial_flagged_component_count, 13);
  assert.deepEqual(byComponent(continuation.component_dispositions.map(row => row.legacy_diagnostic_maximum_unchanged)), maxima);
  assert.equal(continuation.actual_Cg_adopted, null); assert.equal(continuation.actual_Cdelta_adopted, null);
  assert.equal(continuation.owner_scope.panel_screw_exceedances_deferred, true);
  assert.equal(continuation.owner_scope.agent_review_loop_suspended, true);
  falseClaims(continuation, ['candidate_geometry_changed', 'signature_1_over_n_used_as_qualified_acceptance_criterion',
    'all_applicable_connection_criteria_resolved', 'complete_joint_qualified', 'structural_acceptance',
    'fabrication_released', 'climbing_released']);
  assert.equal(continuation.global_force_reruns, 0); assert.equal(continuation.native_solves, 0);
  const stock = data.standardTopStock, first = stock.first_option;
  assert.equal(stock.schema, 'eoere_v10_standard_top_stock_evaluation/v1');
  assert.deepEqual(stock.owner_constraint, index.owner_top_rail_constraint);
  assert.equal(stock.owner_constraint.sha256, 'e697c55556d2c437cfa265cc183eb52e18aadf4dfcc3edc7bdadc7a1a38cc247');
  assert.equal(stock.status, index.standard_top_stock_evaluation.status);
  assert.equal(stock.candidate13_section_result_transferred, false);
  assert.deepEqual(stock.load_contract, V10_CANDIDATE13_LOAD);
  assert.deepEqual(first.actual_section_mm, [38.1, 139.7]);
  assert.equal(first.counts.bolt_stacks, 116);
  assert.equal(first.counts.added_top_beam_bolts, 8);
  assert.equal(first.counts.panel_screw_axes, 66);
  assert.equal(first.status, 'rejected_by_fresh_top_rail_reference');
  assert.equal(first.all_six_cases_evaluated, false);
  assert.deepEqual(first.evaluated_cases.map(row => row.case_id), ['k12-right', 'a12-forward']);
  for (const row of first.evaluated_cases) {
    assert.deepEqual(row.input_bindings.physical_geometry, first.geometry);
    assert.deepEqual(row.input_bindings.receipt, first.receipt);
    assert.equal(row.status, 'early_rejection_by_top_rail_reference');
    assert.equal(row.complete_six_case_pass, null);
    assert.equal(row.early_rejection_sufficient, true);
    assert.ok(row.metric_values.shear_torsion_reference_upper > 1);
  }
  assert.equal(first.maximum_shear_torsion_reference,
    Math.max(...first.evaluated_cases.map(row => row.metric_values.shear_torsion_reference_upper)));
  assert.equal(first.maximum_shear_torsion_reference,
    index.standard_top_stock_evaluation.first_option_maximum_top_shear_torsion_reference);
  assert.equal(index.standard_top_stock_evaluation.preferred_purchase_stock_qualified, false);
  assert.deepEqual(stock.fallback.actual_section_mm, [88.9, 139.7]);
  falseClaims(stock, ['complete_joint_qualified', 'structural_acceptance', 'fabrication_released', 'climbing_released']);
  const matched = stock.fallback.matched_results;
  const selection = index.development_selection, decision = data.ownerDecision;
  assert.equal(decision.schema, 'moonboard_owner_candidate_decision/v1');
  assert.equal(selection.revision, 'v10-standard-top-4x6-stock-proposal-v2');
  assert.equal(selection.revision, decision.selected_revision);
  assert.equal(selection.revision, stock.fallback.geometry_revision);
  assert.deepEqual(selection.actual_top_section_mm, [88.9, 139.7]);
  assert.deepEqual(selection.actual_top_section_mm, decision.actual_top_section_mm);
  assert.deepEqual(selection.geometry_receipt, matched.geometry_receipt);
  assert.deepEqual(selection.physical_geometry, stock.fallback.geometry);
  for (const key of ['response_bank', 'reference_review', 'trial_inventory'])
    assert.deepEqual(selection[key], matched[key]);
  assert.equal(selection.response_bank.sha256, decision.source_response_bank.sha256);
  assert.equal(selection.reference_review.sha256, decision.source_reference_review.sha256);
  assert.equal(selection.top_conditional_shear_torsion_index,
    matched.member_section_references.base_rail_top.maximum_shear_torsion_reference.maximum_shear_torsion_reference_upper);
  assert.equal(selection.top_conditional_shear_torsion_index, decision.top_conditional_shear_torsion_index);
  assert.equal(selection.retained_bearing_diagnostic_case_rows, matched.trial_case_flags);
  assert.equal(selection.retained_bearing_diagnostic_case_rows, decision.retained_bearing_diagnostic_case_rows);
  assert.equal(selection.retained_bearing_diagnostic_components, matched.trial_flagged_components);
  assert.equal(selection.retained_bearing_diagnostic_components, decision.retained_bearing_diagnostic_components);
  assert.equal(selection.candidate_selection_only, true);
  assert.equal(selection.actual_NDS_Cg_adopted, null);
  assert.equal(decision.custom_receiver_signature_penalty_is_not_adopted_NDS_Cg, true);
  assert.equal(decision.no_other_member_stock_approval, true);
  assert.equal(decision.no_purchases_authorized, true);
  falseClaims(selection, ['other_nonstandard_member_stock_approved', 'purchase_authorized',
    'fabrication_released', 'climbing_released', 'structural_acceptance', 'complete_joint_qualified',
    'hardware_queue_duplicated_by_selection']);
  falseClaims(decision, ['fabrication_released', 'climbing_released', 'structural_acceptance']);
  assert.deepEqual(selection.still_open, decision.still_open);
  assert.equal(selection.still_open.length, 4);
  assert.deepEqual(selection.history_preserved, decision.preserve_history);
  assert.equal(selection.history_preserved.length, 2);
  assert.equal(stock.development_candidate_selection.revision, selection.revision);
  assert.deepEqual(stock.development_candidate_selection.owner_decision, selection.owner_decision);
  assert.equal(stock.development_candidate_selection.candidate_selection_only, true);
  falseClaims(stock.development_candidate_selection, ['other_nonstandard_member_stock_approved',
    'purchase_authorized', 'fabrication_released', 'climbing_released', 'structural_acceptance']);
  const {bank: stockBank, review: stockReview, inventory: stockInventory,
    receipt: stockReceipt} = data.stockRecords;
  assert.equal(stockBank.geometry_revision, stock.fallback.geometry_revision);
  assert.equal(stockReceipt.revision, stock.fallback.geometry_revision);
  assert.deepEqual(stockBank.physical_geometry, stock.fallback.receipt);
  assert.deepEqual(stockReceipt.checked_geometry, stock.fallback.geometry);
  assert.deepEqual(stockReceipt.checked_clearance, stock.fallback.clearance);
  assert.equal(stockReceipt.nominal_geometry_clear, true);
  assert.equal(stockReceipt.counts.occupied_parts_checked, 1151);
  assert.deepEqual(stockBank.case_ids, CURRENT_CASES);
  assert.equal(stockBank.cases.length, 6);
  assert.equal(stockBank.all_six_cases_admitted, true);
  assert.deepEqual(stockBank.load_contract, V10_CANDIDATE13_LOAD);
  for (const row of stockBank.cases) {
    assert.equal(row.both_independent_replays_admitted, true);
    assert.ok(row.gradient_inf_N <= 1e-5);
  }
  assert.equal(stockBank.maximum_gradient_inf_N,
    Math.max(...stockBank.cases.map(row => row.gradient_inf_N)));
  assert.equal(stockBank.maximum_gradient_inf_N, matched.maximum_gradient_inf_N);
  const stockFields = Object.fromEntries(stockBank.cases.map(row => [row.case_id, row.field]));
  for (const row of [stockReview, stockInventory]) {
    assert.deepEqual(row.analysis_geometry, stockBank.analysis_geometry);
    assert.deepEqual(row.field_bindings, stockFields);
  }
  assert.equal(stockReview.response_bank.sha256, matched.response_bank.sha256);
  assert.deepEqual(stockReview.physical_geometry, stockBank.physical_geometry);
  assert.deepEqual(stockReview.numerical_reference_maxima, matched.numerical_reference_maxima);
  assert.equal(stockInventory.count_above_reference_case_rows, stockInventory.above_reference_case_rows.length);
  assert.equal(stockInventory.count_above_reference_case_rows, matched.trial_case_flags);
  assert.deepEqual(stockInventory.component_maxima, matched.trial_component_maxima);
  assert.equal(stockInventory.component_maxima.length, matched.trial_flagged_components);
  assert.equal(matched.actual_Cg_adopted, null); assert.equal(matched.actual_Cdelta_adopted, null);
  falseClaims(matched, ['complete_joint_qualified']);
  for (const row of [stockBank, stockReview, stockInventory]) falseClaims(row);
  falseClaims(stockReceipt, ['fabrication_released', 'climbing_released']);
  const connection = stock.fallback.connection_method_summary;
  assert.equal(connection.current_case_axis_rows, 156);
  assert.equal(connection.force_only_scenario_rows, 132);
  for (const key of ['complete_connection_capacity', 'complete_group_capacity',
    'complete_wrench_interaction_pass', 'actual_Cg_adopted', 'actual_Cdelta_adopted',
    'NDS_edge_pass_or_violation_established']) assert.equal(connection[key], null);
  assert.equal(connection.current_068_069_net_actions.length, 12);
  for (const component of ['eoere_bolt_068', 'eoere_bolt_069']) {
    const rows = connection.current_068_069_net_actions.filter(row => row.axis_id === component);
    assert.deepEqual(rows.map(row => row.case_id), CURRENT_CASES);
    assert.ok(rows.every(row => row.net_force_toward_near_edge_N < 0 &&
      row.direction === 'away_from_near_edge'));
  }
  const catalogProbe = stock.fallback.catalog_audit.catalog_maximum_clearance_sensitivity;
  assert.deepEqual(catalogProbe.source_geometry, stock.fallback.geometry);
  assert.equal(catalogProbe.known_catalog_maximum_occupied_envelopes_clear, true);
  assert.equal(catalogProbe.changed_hardware_ids_checked, 110);
  assert.equal(catalogProbe.occupied_parts, 1151);
  assert.equal(catalogProbe.collisions, 0); assert.equal(catalogProbe.missing_candidates, 0);
  falseClaims(catalogProbe, ['source_geometry_or_force_bank_changed',
    'all_catalog_properties_or_delivered_fit_qualified', 'force_or_strength_result_transferred']);
  const slip = stock.fallback.group_slip_method_assessment;
  assert.equal(slip.actual_Cg_assigned, null);
  falseClaims(slip, ['FE_equivalent_to_NDS_gamma', 'subpath_values_are_qualified_connection_stiffness']);
  const rear = stock.fallback.rear_full_wrench_reference;
  assert.equal(rear.current_case_axis_rows, 24);
  for (const key of ['complete_connection_capacity', 'complete_wrench_interaction_pass',
    'actual_Cg_adopted', 'actual_Cdelta_adopted']) assert.equal(rear[key], null);
  falseClaims(rear, ['physical_failure_established', 'bolt_size_or_grade_remedy_adopted',
    'selected_Grade_5_Fyb_qualified', 'root_profile_is_delivered_or_acceptance_minimum',
    'legacy_trial_inventory_changed']);
  const groupCriteria = stock.fallback.physical_row_group_criteria;
  const active = data.activeConnectionCriteria, comparison = data.groupRowComparison;
  assert.equal(active.schema, 'eoere_physical_row_full_wrench_criteria/v1');
  assert.equal(active.revision, selection.revision);
  assert.equal(comparison.revision, selection.revision);
  assert.equal(comparison.selected_revision, selection.revision);
  assert.deepEqual(comparison.sources.map(row => row.sha256),
    [selection.physical_geometry, selection.response_bank, selection.reference_review].map(row => row.sha256));
  assert.deepEqual(active.source_bindings.provided_comparison, groupCriteria.comparison);
  assert.deepEqual(active.source_bindings.provided_producer, groupCriteria.producer);
  assert.deepEqual(active.source_bindings.legacy_trial_inventory, selection.trial_inventory);
  assert.deepEqual(active.load_contract, stockBank.load_contract);
  assert.deepEqual(active.analysis_geometry, stockBank.analysis_geometry);
  assert.deepEqual(active.field_bindings, stockFields);
  assert.equal(active.status, 'UNRESOLVED'); assert.equal(groupCriteria.status, active.status);
  for (const key of ['actual_Cg_adopted', 'actual_Cdelta_adopted', 'upper_cleat_three_media_Cg',
    'complete_connection_capacity', 'complete_connection_acceptance']) assert.equal(active[key], null);
  for (const key of ['actual_Cg_adopted', 'actual_Cdelta_adopted', 'upper_cleat_Cg',
    'complete_connection_acceptance']) assert.equal(groupCriteria[key], null);
  falseClaims(active, ['legacy_signature_1_over_n_used_for_acceptance', 'conditional_benchmark_factor_used_for_acceptance',
    'signed_forces_changed', 'signed_moments_changed', 'moments_omitted', 'loads_reduced', 'force_bank_rerun',
    'structural_acceptance', 'fabrication_released', 'climbing_released', 'purchase_authorized',
    'hardware_or_geometry_selected_by_this_comparison']);
  assert.equal(groupCriteria.legacy_1_over_n_is_acceptance_criterion, false);
  assert.equal(comparison.actual_Cg_adopted, null);
  falseClaims(comparison, ['acceptance_changed', 'release_changed']);
  assert.equal(comparison.tests.tests_passed, 6);
  assert.equal(comparison.conditional_scenarios.length, 5);
  assert.equal(active.provided_benchmarks.actual_connection_factors_or_passes, false);
  for (const row of comparison.conditional_scenarios) {
    assert.equal(row.actual_connection_Cg, null);
    assert.equal(row.complete_connection_status, 'UNRESOLVED');
    assert.equal(row.n_per_assumed_row, 2);
    assert.ok(row.Cg > 0.99 && row.Cg < 1, 'conditional row benchmark remains separate from 1/n');
  }
  assert.equal(active.legacy_diagnostics.case_rows, 15);
  assert.equal(active.legacy_diagnostics.components, 8);
  assert.equal(active.legacy_diagnostics.diagnostic_only, true);
  assert.equal(active.other_axes_not_cleared_by_absence_of_legacy_flag, true);
  assert.equal(active.flagged_component_dispositions.length, 8);
  assert.deepEqual(byComponent(active.flagged_component_dispositions.map(row => row.legacy_trial_maximum)),
    byComponent(stockInventory.component_maxima));
  for (const row of active.flagged_component_dispositions) {
    assert.equal(row.status, 'UNRESOLVED');
    assert.equal(row.legacy_trial_is_acceptance_criterion, false);
    for (const key of ['actual_physical_group_id', 'actual_row_assignment', 'actual_Cg',
      'complete_connection_capacity', 'complete_force_and_moment_interaction_pass']) assert.equal(row[key], null);
  }
  assert.equal(scene.schema, 'eoere_v10_geometry_patch/v1'); assert.equal(scene.revision, index.geometry.revision);
  assert.equal(scene.key, 'eoere-owner-frame-v10-development');
  assert.equal(scene.iteration, '13'); assert.equal(scene.part_count, 1167); assert.equal(scene.parent_part_count, 1021);
  assert.deepEqual(scene.counts, V10_CANDIDATE13_COUNTS);
  assert.equal(scene.layout_report.path, refs.geometry.path); assert.equal(scene.layout_report.sha256, refs.geometry.sha256);
  assert.deepEqual(scene.geometry_source, geometry.checked_geometry); assert.deepEqual(scene.clearance_source, geometry.checked_clearance);
  assert.equal(scene.parent_layout.path, index.preceding_revision.geometry.receipt.path);
  assert.equal(scene.parent_layout.sha256, index.preceding_revision.geometry.receipt.sha256);
  for (const key of ['current_response_computed', 'historical_capacity_transferred', 'complete_conditional_frame_evaluation',
    'actual_parts_verified', 'fabrication_released', 'climbing_released']) assert.equal(scene[key], false);
  assert.equal(scene.panel_Hillman_resolution_deferred, true);
  assert.equal(geometryJoin.scene.sha256, index.geometry.scene.sha256);
  assert.deepEqual(geometryJoin.geometry, refs.geometry); assert.deepEqual(geometryJoin.counts, V10_CANDIDATE13_COUNTS);
  return {passed: true, revision: index.geometry.revision, bolt_axes: 116, screw_axes: 66,
    angles: 24, occupied_parts: 1167, spacer_pieces: 60, current_response_revision: index.geometry.revision,
    trial_case_flags: 26, trial_flagged_components: 13, actual_Cg_adopted: null, complete_geometry_factor_resolved: false,
    center_principal_optional_both_edges_envelope_only: true, center_principal_established_NDS_near_edge_violation: false,
    complete_joint_qualified: false, structural_acceptance: false, fabrication_released: false, climbing_released: false,
    full_ignored_input_closure_checked: false, mechanics_executed: false};
}

export function validatePackerFreeMethodEvaluation(methods, index) {
  assert.equal(methods.schema, 'eoere_packer_free_connection_method_evaluation/v1');
  assert.equal(methods.revision, index.geometry.revision);
  assert.deepEqual(methods.response_bank, index.response_bank);
  assert.deepEqual(methods.evaluation, index.engineering_review);
  assert.deepEqual(methods.geometry_receipt, index.geometry.receipt);
  for (const [key, count] of Object.entries({axes: 112, axis_case_wrenches: 672, wood_intervals: 136,
    wood_action_rows: 816, signed_plane_wrenches: 792, receiver_actions: 1464, same_host_geometry_pairs: 536}))
    assert.equal(methods.coverage[key], count, `current packer-free method coverage: ${key}`);
  referenceKeys(methods.source_bindings, ['force_only', 'same_field', 'geometry', 'washer', 'hardware'],
    'current packer-free method sources');
  const sources = Object.values(methods.source_bindings);
  assert.equal(new Set(sources.map(ref => ref.path)).size, 5);
  for (const ref of sources) {
    referenceBinding(ref);
    assert.ok(ref.path.startsWith('fea/generated/v10-packer-free-v1/'), 'own packer-free method source required');
  }
  for (const key of ['force_only', 'same_field', 'geometry', 'washer', 'hardware'])
    assert.ok(methods[key] && typeof methods[key] === 'object' && !Array.isArray(methods[key]),
      `current conditional method summary required: ${key}`);
  assert.ok(Array.isArray(methods.remaining) && methods.remaining.length > 0);
  for (const key of ['actual_Cg', 'actual_Cdelta', 'complete_connection_acceptance']) assert.equal(methods[key], null);
  for (const key of ['structural_acceptance', 'fabrication_released', 'climbing_released', 'purchase_authorized'])
    assert.equal(methods[key], false);
  return methods;
}

export function validateUnselectedCenterFarRowTrial(entry, report, provenance) {
  validateCenterFarRowProvenance(provenance);
  assert.equal(entry.revision, CENTER_FAR_ROW_REVISION);
  referenceBinding(entry.evaluation, 'docs/bolted-frame-development/owner-frame-v10/packer-free-center-far-row/evaluation.json');
  assert.equal(entry.viewer.model, CENTER_FAR_ROW_MODEL);
  referenceBinding(entry.viewer.provenance, 'site/eoere-center-far-row-provenance.json');
  assert.equal(entry.viewer.provenance.sha256, CENTER_FAR_ROW_ASSETS.sha256);
  assert.deepEqual(entry.viewer.scene, {path: provenance.scene.path, sha256: provenance.scene.sha256});
  referenceBinding(entry.viewer.adapter, 'site/eoere-center-far-row-overlay.mjs');
  assert.equal(report.schema, 'v10_center_far_row_unselected_evaluation/v1');
  assert.equal(report.revision, entry.revision);
  for (const row of [entry, report.qualifications])
    for (const key of ['structural_acceptance', 'fabrication_released', 'climbing_released', 'purchase_authorized'])
      assert.equal(row[key], false);
  assert.equal(entry.selected, false); assert.equal(report.selected, false);
  referenceBinding(report.bindings.response_bank,
    'docs/bolted-frame-development/owner-frame-v10/packer-free-center-far-row/response-bank.json');
  referenceBinding(report.bindings.checked_receipt,
    'docs/bolted-frame-development/owner-frame-v10/packer-free-center-far-row/geometry-receipt.json');
  assert.equal(report.bindings.response_bank.sha256, provenance.sources.response_bank.sha256);
  assert.equal(report.bindings.checked_receipt.sha256, provenance.sources.geometry_receipt.sha256);
  referenceBinding(report.bindings.physical_geometry,
    'fea/generated/v10-packer-free-center-far-row-v1/geometry-v1/geometry.json');
  assert.equal(report.bindings.physical_geometry.sha256, provenance.geometry_sha256);
  assert.deepEqual(report.geometry.counts, {...provenance.counts, wood_packers: 0});
  assert.deepEqual(report.geometry.top_and_sides_actual_mm, [88.9, 139.7]);
  assert.deepEqual([...report.geometry.removed_axis_ids].sort(), [5, 6, 7, 8].map(n => `v10_top_bolt_00${n}`));
  assert.deepEqual(report.load_contract, provenance.load_contract);
  const vectors = {left_side: 'base_side_left', right_side: 'base_side_right', top: 'base_rail_top', header: 'base_header'};
  referenceKeys(report.vector_references, Object.keys(vectors), 'own unselected vector references');
  for (const [key, component] of Object.entries(vectors))
    referenceClose(report.vector_references[key], provenance.declared_vector_references[component].index, `unselected ${key}`);
  const diagnostics = report.bearing_diagnostics;
  assert.equal(diagnostics.case_rows, 15); assert.equal(diagnostics.component_count, 8);
  assert.equal(diagnostics.flags.length, 15);
  assert.equal(new Set(diagnostics.flags.map(row => `${row.case}/${row.axis}`)).size, 15);
  assert.equal(new Set(diagnostics.flags.map(row => row.axis)).size, 8);
  assert.equal(diagnostics.actual_Cg, null); assert.equal(diagnostics.actual_Cdelta, null);
  for (const row of diagnostics.flags) {
    assert.ok(CURRENT_CASES.includes(row.case) && typeof row.axis === 'string' && row.axis.length > 0);
    assert.ok(Number.isFinite(row.trial_index) && row.trial_index > 1);
    assert.ok(Number.isFinite(row.trial_Cg) && row.trial_Cg > 0 && row.trial_Cg <= 1);
    referenceIndex(row.individual_before_Cg, 'unselected individual bearing reference');
    referenceClose(row.trial_index * row.trial_Cg, row.individual_before_Cg, 'unselected diagnostic factor arithmetic');
  }
  const maximum = provenance.declared_family_maxima.wood_bearing_whole_affine;
  assert.ok(diagnostics.flags.some(row => row.case === maximum.case_id && row.axis === maximum.component && row.trial_index === maximum.index));
  assert.equal(Math.max(...diagnostics.flags.map(row => row.trial_index)), maximum.index);
  assert.equal(report.qualifications.complete_joint_qualified, false);
  assert.equal(report.qualifications.complete_connection_acceptance, null);
  assert.equal(report.qualifications.panel_screw_resolution_deferred, true);
  assert.equal(report.qualifications.physical_force_bounds_established, false);
  return {revision: report.revision, viewer_model: entry.viewer.model, selected: false, bolt_axes: 108, occupied_parts: 1105,
    bearing_diagnostic_case_rows: 15, bearing_diagnostic_components: 8, actual_Cg: null, actual_Cdelta: null,
    complete_connection_acceptance: null, complete_joint_qualified: false, structural_acceptance: false,
    fabrication_released: false, climbing_released: false, purchase_authorized: false};
}

export function validateLocalSubassemblyActionMap(report, index) {
  assert.equal(report.schema, 'v10_local_subassembly_action_map/v1');
  assert.equal(report.current_revision, index.geometry.revision);
  assert.deepEqual(report.current_response_bank, index.response_bank);
  const trial = index.unselected_trials?.center_far_row_only;
  assert.ok(trial, 'the action map requires its unselected trial authority');
  const assessment = JSON.parse(bound(trial.evaluation));
  assert.equal(report.unselected_revision, trial.revision);
  assert.deepEqual(report.unselected_response_bank, assessment.bindings.response_bank);
  assert.deepEqual(report.counts, {
    selected112: {vertices: 138, shafts: 112, angles: 24, bonded_cleats: 2, components: 30},
    current108: {vertices: 134, shafts: 108, angles: 24, bonded_cleats: 2, components: 30},
  });
  assert.equal(report.connected_hardware_components, 20); assert.equal(report.wood_only_review_scopes, 6);
  assert.deepEqual(report.model_constraints, {top_and_both_sides_actual_mm: [88.9, 139.7], wood_packers: 0});
  assert.equal(report.cleat_components.length, 2);
  for (const [side, upper, companion, headerStart] of [['left', 67, 71, 1], ['right', 70, 74, 3]]) {
    const component = report.cleat_components.find(row => row.bonded_cleat_body_id === `eoere_cleat_${side}`);
    assert.ok(component); assert.equal(component.component_id, `cleat-subassembly:eoere_cleat_${side}`);
    const cleatAxes = [`cleat_post_bolt_${side}_1`, `cleat_post_bolt_${side}_2`,
      `eoere_bolt_0${upper}`, `eoere_bolt_0${companion}`, ...[1, 2, 3].map(n => `v10_cleat_bolt_${side}_${n}`)];
    const headerAxes = [headerStart, headerStart + 1].flatMap(n => [`eoere_bolt_0${80 + n}`, `v10_header_bolt_00${n}`]);
    assert.deepEqual([...component.cleat_axis_ids].sort(), cleatAxes.sort());
    assert.deepEqual([...component.all_component_axis_ids].sort(), [...cleatAxes, ...headerAxes].sort());
    assert.deepEqual([...component.fitting_body_ids].sort(),
      [`eoere_clip_angle_base_${side}`, `eoere_clip_header_outer_under_${side}`].sort());
  }
  const scopes = report.critical_bearing_diagnostic_scopes;
  assert.equal(scopes.length, 4); assert.equal(new Set(scopes.map(row => row.scope_id)).size, 4);
  const scopeAxes = {
    'cleat-subassembly:eoere_cleat_left': ['eoere_bolt_067', 'v10_header_bolt_001'],
    'cleat-subassembly:eoere_cleat_right': ['eoere_bolt_070', 'v10_header_bolt_004'],
    'wood-only-joint:side_left+lumber_leg_left': ['lumber_leg_bolt_left_1', 'lumber_leg_bolt_left_2'],
    'wood-only-joint:side_right+lumber_leg_right': ['lumber_leg_bolt_right_1', 'lumber_leg_bolt_right_2'],
  };
  assert.deepEqual(scopes.map(row => row.scope_id).sort(), Object.keys(scopeAxes).sort());
  const axes = scopes.flatMap(row => row.axes);
  assert.equal(axes.length, 8); assert.equal(new Set(axes).size, 8);
  const currentAssessment = JSON.parse(bound(index.engineering_review));
  assert.deepEqual([...axes].sort(), Object.keys(currentAssessment.bearing_diagnostic_component_maxima).sort());
  assert.deepEqual([...axes].sort(), [...new Set(assessment.bearing_diagnostics.flags.map(row => row.axis))].sort());
  for (const row of scopes) {
    assert.ok(typeof row.scope_id === 'string' && row.scope_id.length > 0);
    assert.deepEqual([...row.axes].sort(), scopeAxes[row.scope_id]);
    assert.ok(Number.isInteger(row.current_case_rows) && row.current_case_rows >= 0);
    assert.ok(Number.isInteger(row.unselected_case_rows) && row.unselected_case_rows >= 0);
    assert.equal(row.complete_joint_utilization, null); assert.equal(row.NDS_group_assignment, null);
  }
  assert.equal(scopes.reduce((sum, row) => sum + row.current_case_rows, 0), 15);
  assert.equal(scopes.reduce((sum, row) => sum + row.unselected_case_rows, 0), 15);
  assert.deepEqual(report.gates, {force_N: 1e-4, moment_Nmm: 0.1});
  referenceKeys(report.closure, ['selected112', 'unselected108'], 'declared local action comparisons');
  for (const row of Object.values(report.closure)) {
    assert.equal(row.whole_field_comparisons, 6); assert.equal(row.component_comparisons, 120);
    assert.equal(row.wood_scope_comparisons, 36);
    for (const prefix of ['max_component_actual_equilibrium_residual', 'max_component_reconstruction_difference',
      'max_wood_scope_reconstruction_difference']) for (const [unit, gate] of [['N', report.gates.force_N], ['Nmm', report.gates.moment_Nmm]]) {
      referenceIndex(row[`${prefix}_${unit}`], 'declared local residual');
      assert.ok(row[`${prefix}_${unit}`] <= gate, 'declared local residual exceeds its recorded gate');
    }
  }
  assert.equal(report.residual_origin.selected112_comparisons_normalized_before_aggregation, true);
  assert.equal(report.residual_origin.unselected108_V2_overlay_required, true);
  assert.equal(report.residual_origin.source_forces_and_own_point_couples_changed, false);
  for (const key of ['actual_Cg', 'actual_Cdelta', 'complete_connection_acceptance']) assert.equal(report.qualification[key], null);
  for (const key of ['complete_joint_qualified', 'complete_load_path_established', 'nds_fastener_group_classification_established',
    'structural_acceptance', 'fabrication_released', 'climbing_released', 'purchase_authorized']) assert.equal(report.qualification[key], false);
  assert.equal(report.qualification.panel_screw_resolution_deferred, true);
  assert.equal(report.new_global_CAD_or_force_solve, false); assert.equal(report.selected_authority_or_viewer_changed, false);
  assert.equal(report.nominal_bore_check_unselected108.delivered_holes_or_bolt_body_inspected, false);
  assert.equal(report.primitive_bookkeeping.panel_resistance_recalculated, false);
  referenceKeys(report.raw_sources, ['body_graph', 'selected112_wrenches', 'unselected108_wrenches',
    'unselected108_residual_origin_overlay', 'unselected108_nominal_bore_audit'], 'retained raw action sources');
  for (const ref of Object.values(report.raw_sources)) referenceBinding(ref);
  return report;
}

export function validateCurrent112HardwarePlanning(plan, index, csvBytes) {
  assert.equal(plan.schema, 'v10_current112_nominal_hardware_planning/v1');
  assert.equal(plan.revision, index.geometry.revision);
  referenceKeys(plan.source_bindings, ['geometry_receipt', 'response_bank', 'resolved_spacers',
    'nominal_inventory', 'physical_geometry'], 'current nominal hardware sources');
  for (const ref of Object.values(plan.source_bindings)) referenceBinding(ref);
  assert.deepEqual(plan.source_bindings.geometry_receipt, index.geometry.receipt);
  assert.deepEqual(plan.source_bindings.response_bank, index.response_bank);
  assert.deepEqual(plan.source_bindings.resolved_spacers, index.hardware_spacer_mapping);
  const receipt = JSON.parse(bound(index.geometry.receipt));
  assert.deepEqual(plan.source_bindings.physical_geometry, {
    path: 'fea/generated/v10-packer-free-v1/geometry-v1/geometry.json', sha256: receipt.checked_geometry.sha256});
  const methods = JSON.parse(bound(index.connection_method_evaluation));
  assert.deepEqual(plan.source_bindings.nominal_inventory, methods.source_bindings.hardware);
  const spacers = JSON.parse(bound(index.hardware_spacer_mapping));
  assert.deepEqual(plan.retained_context_not_reselected, {angles: 24, Hillman_panel_kicker_axes: 66});
  assert.equal(plan.rows.length, 14);
  assert.equal(new Set(plan.rows.map(row => `${row.category}/${row.SKU}`)).size, 14);
  const fields = ['category', 'SKU', 'nominal_quantity', 'unit', 'planning_status', 'source_field', 'Actual', 'Disposition'];
  const sources = {bolt: 'nominal_inventory#/nominal_candidate_bom/bolt_SKU_quantities',
    nut: 'nominal_inventory#/nominal_candidate_bom/nut_SKU_quantities',
    washer: 'nominal_inventory#/nominal_candidate_bom/washer_SKU_quantities_two_per_stack',
    spacer: 'resolved_spacers#/nominal_catalog_SKU_quantities'};
  for (const row of plan.rows) {
    referenceKeys(row, fields, 'nominal hardware row');
    assert.ok(Object.hasOwn(sources, row.category));
    assert.ok(typeof row.SKU === 'string' && row.SKU.trim().length > 0);
    assert.ok(Number.isInteger(row.nominal_quantity) && row.nominal_quantity > 0);
    assert.equal(row.unit, 'pieces'); assert.equal(row.planning_status, 'NOMINAL_PLANNING_PHYSICAL_FIT_UNVERIFIED');
    assert.equal(row.source_field, sources[row.category]); assert.equal(row.Actual, ''); assert.equal(row.Disposition, '');
  }
  const totals = Object.fromEntries(Object.keys(sources).map(category => [category,
    plan.rows.filter(row => row.category === category).reduce((sum, row) => sum + row.nominal_quantity, 0)]));
  assert.deepEqual(plan.totals, {bolt: 112, nut: 112, washer: 224, spacer: 40});
  assert.deepEqual(totals, plan.totals);
  assert.deepEqual(Object.fromEntries(plan.rows.filter(row => row.category === 'spacer')
    .map(row => [row.SKU, row.nominal_quantity])), spacers.nominal_catalog_SKU_quantities);
  for (const key of ['structural_acceptance', 'fabrication_released', 'climbing_released', 'purchase_authorized',
    'delivered_parts_verified', 'physical_fit_qualified', 'prices_or_availability_claimed',
    'new_quantity_audit_or_geometry_force_calculation']) assert.equal(plan[key], false);
  assert.equal(plan.all_six_cases_and_both_replays_recorded, true);
  assert.equal(plan.publication_raw_inventory_and_geometry_pins_checked, true);
  assert.equal(plan.producer, 'scripts/publish_current112_hardware_plan.py');
  referenceBinding(plan.CSV, 'docs/bolted-frame-development/owner-frame-v10/packer-free/hardware-planning.csv');
  const csv = csvBytes ?? bound(plan.CSV);
  assert.equal(sha(csv), plan.CSV.sha256, 'issued nominal hardware CSV hash differs');
  const cell = value => /[",\r\n]/.test(String(value)) ? `"${String(value).replaceAll('"', '""')}"` : String(value);
  const expectedCSV = [fields.join(','), ...plan.rows.map(row => fields.map(key => cell(row[key])).join(','))].join('\n') + '\n';
  assert.equal(csv.toString('utf8'), expectedCSV, 'nominal hardware JSON/CSV rows differ');
  return plan;
}

export function validateCurrent112GroupEffects(report, index) {
  assert.equal(report.schema, 'eoere_v10_group_effects_public_summary/v1');
  assert.equal(report.revision, index.geometry.revision);
  assert.deepEqual(report.response_bank, index.response_bank);
  assert.deepEqual(report.geometry_receipt, index.geometry.receipt);
  assert.deepEqual(report.ownership_map, index.subassembly_action_map);
  const bank = JSON.parse(bound(report.response_bank));
  const receipt = JSON.parse(bound(report.geometry_receipt));
  const ownership = JSON.parse(bound(report.ownership_map));
  referenceBinding(report.work_packet,
    'docs/bolted-frame-development/owner-frame-v10/standard-top-stock/group-effects-replacement-work-packet-v1.txt');
  bound(report.work_packet);
  referenceKeys(report.source_bindings, ['analysis_geometry', 'boundary_wrenches', 'checked_receipt', 'component_graph',
    'legacy_evaluation', 'nds_chapter_11', 'nds_chapter_12', 'nds_evaluator', 'owner_work_packet', 'physical_geometry',
    'plywood_material', 'prepared_inputs', 'primary_method_closure', 'response_bank', 'serial_row_benchmark'], 'group-effects source declarations');
  for (const ref of Object.values(report.source_bindings)) referenceBinding(ref);
  const sources = report.source_bindings;
  assert.deepEqual(sources.response_bank, {path: 'fea/generated/v10-packer-free-v1/mechanics/analysis-v2/response-bank.json',
    sha256: index.response_bank.sha256});
  assert.deepEqual(sources.checked_receipt, bank.physical_geometry);
  assert.deepEqual(sources.analysis_geometry, bank.analysis_geometry);
  assert.deepEqual(sources.physical_geometry, {path: 'fea/generated/v10-packer-free-v1/geometry-v1/geometry.json',
    sha256: receipt.checked_geometry.sha256});
  assert.deepEqual(sources.boundary_wrenches, ownership.raw_sources.selected112_wrenches);
  assert.deepEqual(sources.component_graph, ownership.raw_sources.body_graph);
  assert.deepEqual(sources.legacy_evaluation, index.engineering_review);
  assert.deepEqual(sources.primary_method_closure, index.method_followups.primary_method_closure);
  assert.deepEqual(sources.owner_work_packet, report.work_packet);
  referenceBinding(report.raw_assessment); referenceBinding(report.current112_operator_reuse_proof,
    'fea/generated/v10-packer-free-v1/connections/method-closure/group-slip/rear-coupon-current112-reuse-proof-v1.json');
  // The frozen producer records its original absolute path; it is a declaration, never a portable read.
  referenceKeys(report.producer, ['path', 'sha256'], 'group-effects producer declaration');
  assert.ok(typeof report.producer.path === 'string' && report.producer.path.length > 0 &&
    !report.producer.path.split(/[\\/]/).includes('..'));
  assert.match(report.producer.sha256, /^[a-f0-9]{64}$/);
  assert.deepEqual(report.load_contract, bank.load_contract); assert.equal(report.admission_gate_N, bank.admission_gate_N);
  assert.deepEqual(report.coverage, {attachment_memberships: 108, attachment_row_roles: 54, axes: 112,
    axes_with_attachment_roles: 96, cases: 6, hardware_cleat_scopes: 20, topology_only_cleat_axes: 6,
    wood_geometric_candidate_rows: 6, wood_only_scopes: 6});
  assert.equal(report.review_scopes.length, 26);
  assert.equal(new Set(report.review_scopes.map(row => row.scope_id)).size, 26);
  for (const [kind, count] of [['hardware_cleat', 20], ['wood_only', 6]])
    assert.equal(report.review_scopes.filter(row => row.kind === kind).length, count);
  const axes = report.review_scopes.flatMap(row => row.axis_ids);
  const scene = JSON.parse(gunzipSync(bound(index.repository_viewer.scene)));
  assert.equal(axes.length, 112); assert.equal(new Set(axes).size, 112);
  assert.deepEqual([...axes].sort(), scene.stack_updates.map(row => row.axis_id).sort());
  for (const row of report.review_scopes) {
    referenceKeys(row, ['actual_Cg', 'applicability_status', 'axis_ids', 'capacity', 'kind', 'scope_id'], 'unresolved group review scope');
    assert.ok(typeof row.scope_id === 'string' && row.scope_id.length > 0 && row.axis_ids.length > 0);
    assert.equal(row.actual_Cg, null); assert.equal(row.capacity, null); assert.equal(row.applicability_status, 'UNRESOLVED');
  }
  for (const component of ownership.cleat_components)
    assert.deepEqual([...report.review_scopes.find(row => row.scope_id === component.component_id).axis_ids].sort(),
      [...component.all_component_axis_ids].sort());
  for (const scope of ownership.critical_bearing_diagnostic_scopes)
    assert.ok(scope.axes.every(axis => report.review_scopes.find(row => row.scope_id === scope.scope_id)?.axis_ids.includes(axis)));
  assert.deepEqual(report.active_group_assessment, {accepted_capacity_exceedance_count: null, candidate_Cdelta: null,
    candidate_Cg: null, candidate_payloads_routed_to_NDS: 0, complete_joint_capacity: null, criterion_disposition: 'UNRESOLVED',
    legacy_receiver_signature_1_over_n_is_acceptance: false, strategy: 'eligible_source_bound_NDS_row_or_UNRESOLVED'});
  assert.deepEqual(report.legacy_diagnostics, {acceptance_criterion: false, components: 8, preserved: true, rows: 15,
    source: index.engineering_review});
  const benchmark = report.serial_row_benchmark, result = benchmark.result, distribution = result.serial_row_distribution;
  assert.equal(benchmark.status, 'PASS_METHOD_BENCHMARK_ONLY'); assert.equal(benchmark.expected_published_rounded_Cg, 0.98);
  assert.deepEqual(benchmark.inputs, {diameter_in: 0.625, fastener_count: 3, main_A_in2: 144, main_E_psi: 1600000,
    nominal_gamma_lbf_per_in: 88939.05919223567, pitch_in: 2.5, side_A_in2: 10.88, side_E_psi: 1600000});
  assert.equal(result.gamma_lbf_per_in, benchmark.inputs.nominal_gamma_lbf_per_in);
  assert.equal(result.scope, 'synthetic two-member wood-to-wood elastic serial row only; no candidate Cg');
  assert.equal(result.capacity, null); assert.equal(result.criterion_disposition, 'pending'); assert.equal(result.matches_within_tolerance, true);
  referenceClose(result.NDS_Cg_method_only, 0.9806318451462117, 'published synthetic Cg benchmark');
  referenceClose(result.distribution_Cg, result.NDS_Cg_method_only, 'synthetic serial-row comparison');
  referenceClose(result.Cg_difference, Math.abs(result.distribution_Cg-result.NDS_Cg_method_only), 'synthetic Cg difference');
  assert.equal(distribution.fastener_count, 3); assert.equal(distribution.applied_load, 1);
  assert.equal(distribution.bolt_force_fractions.length, 3); assert.deepEqual(distribution.bolt_forces, distribution.bolt_force_fractions);
  for (const fraction of distribution.bolt_force_fractions) assert.ok(Number.isFinite(fraction) && fraction > 0 && fraction < 1);
  referenceClose(distribution.bolt_force_fractions.reduce((sum, value) => sum+value, 0), 1, 'synthetic force fractions');
  referenceClose(distribution.max_force_fraction, Math.max(...distribution.bolt_force_fractions), 'synthetic maximum fraction');
  referenceClose(distribution.cg_from_distribution, 1/(3*distribution.max_force_fraction), 'synthetic distribution Cg');
  referenceClose(distribution.cg_from_distribution, result.distribution_Cg, 'synthetic Cg result');
  referenceClose(distribution.total_transferred_force, 1, 'synthetic transferred force');
  referenceClose(distribution.force_balance_residual, 0, 'synthetic force balance');
  referenceClose(distribution.force_balance_relative_residual, 0, 'synthetic relative force balance');
  const comparison = report.current_operator_comparison, coupon = comparison.coupon;
  assert.equal(comparison.matched_axis_case_descriptors, 24);
  assert.deepEqual([...comparison.matched_rear_axes].sort(), ['left', 'right'].flatMap(side =>
    [1, 2].map(n => `lumber_leg_bolt_${side}_${n}`)));
  assert.equal(coupon.station_count, 13); assert.equal(coupon.free_DOFs, 26);
  assert.deepEqual(coupon.media, ['wood', 'wood']); assert.equal(coupon.diameter_mm, 12.7);
  referenceClose(coupon.condensed_stiffness_N_per_mm, 286.5816634407049, 'conditional local coupon stiffness');
  referenceClose(coupon.NDS_gamma_N_per_mm, 11145.003549347048, 'nominal NDS gamma comparison');
  referenceClose(coupon.coupon_to_NDS_gamma, coupon.condensed_stiffness_N_per_mm/coupon.NDS_gamma_N_per_mm, 'local coupon comparison');
  assert.ok(Number.isFinite(coupon.equilibrium_residual_N) && coupon.equilibrium_residual_N >= 0 &&
    coupon.equilibrium_residual_N <= report.admission_gate_N);
  assert.equal(comparison.limits.scope, 'local two-wood, 13-station, zero-gap full-active rigid-host scalar transverse tangent coupon only');
  for (const key of ['actual_Cg', 'actual_physical_slip', 'candidate_force_distribution',
    'complete_connection_acceptance', 'complete_group_or_connection_capacity']) assert.equal(comparison.limits[key], null);
  for (const key of ['loads_or_wrenches_reused', 'new_coupon_or_condensation_run', 'structural_acceptance'])
    assert.equal(comparison.limits[key], false);
  for (const key of ['candidate_factor_assigned', 'capacity_computed', 'climbing_released', 'component_graph_is_a_fastener_group',
    'criterion_acceptance', 'current_authority_changed', 'fabrication_released', 'loads_reduced', 'new_native_or_CAD_run',
    'physical_hardware_or_bond_verified', 'purchase_authorized', 'structural_acceptance']) assert.equal(report.qualifications[key], false);
  assert.equal(report.qualifications.separate_direct_wood_to_wood_contact_channel_retained, true);
  return report;
}

const PACKER_FREE_FOLLOWUP_SCHEMAS = {
  primary_method_closure: 'v10_packer_free_primary_method_closure_summary/v1',
  geometry_method_followup: 'v10_geometry_method_followup/v1',
  connection_criterion_dispositions: 'v10_connection_criterion_dispositions/v1',
  contact_law_evaluation: 'v10_packer_free_contact_law_evaluation/v1',
  rear_foot_shear_evaluation: 'v10_packer_free_rear_foot_shear_evaluation/v1',
  rear_foot_centering_screen: 'rear_foot_centering_screen_summary/v1',
  fitting_gross_strip_reference: 'v10-packer-free-fitting-gross-strip-reference/v1',
  sawn_connection_shear_evaluation: 'v10_packer_free_sawn_connection_shear_evaluation/v1',
};

export function validatePackerFreeFittingReference(report, index) {
  assert.equal(report.schema, 'v10-packer-free-fitting-gross-strip-reference/v1');
  assert.equal(report.candidate, index.geometry.revision);
  assert.equal(report.status, 'CONDITIONAL_GROSS_STRIP_ELASTIC_REFERENCE_ONLY');
  const sources = report.source_bindings;
  for (const [key, ref] of Object.entries(sources)) {
    if (key === 'current_fitting_operator') assert.match(ref.sha256, /^[a-f0-9]{64}$/);
    else referenceBinding({path: ref.path, sha256: ref.sha256});
  }
  referenceBinding(sources.section_and_torsion_bound.controls);
  assert.deepEqual(sources.analysis_v2_response_bank, {
    path: 'fea/generated/v10-packer-free-v1/mechanics/analysis-v2/response-bank.json', sha256: index.response_bank.sha256});
  const geometry = JSON.parse(bound(index.method_followups.geometry_method_followup));
  assert.deepEqual(sources.analysis_v2_prepared_inputs, geometry.current_model_bindings.prepared_inputs);
  assert.deepEqual(sources.prior_current_method_report, index.connection_method_evaluation);
  const methods = JSON.parse(bound(index.connection_method_evaluation));
  assert.deepEqual(sources.current_same_field_material_reference, methods.source_bindings.same_field);
  referenceBinding(sources.current_fitting_operator_snapshot,
    'fea/generated/v10-packer-free-v1/mechanics/analysis-v2/eoere_v10_fitting-method-snapshot.py');
  assert.equal(sources.current_fitting_operator_snapshot.sha256, sources.current_fitting_operator.sha256);
  assert.ok(sources.raw_recovery.path.startsWith('fea/generated/v10-packer-free-v1/connections/method-closure/fitting/'));
  assert.equal(report.known_answer_control.passed, true);
  assert.equal(report.known_answer_control.actual_fy_adopted, false);
  referenceClose(report.known_answer_control.required_fy_reference_mpa, 2.7322405932977976, 'gross-strip known coupon');
  const result = report.six_case_result;
  assert.equal(result.fittings, 24); assert.equal(result.signed_port_wrenches_per_case, 192);
  assert.equal(result.section_endpoint_wrenches_per_case, 384);
  assert.deepEqual(result.per_case_maximum_mpa.map(row => row.case_id).sort(), [...CURRENT_CASES].sort());
  for (const row of result.per_case_maximum_mpa) referenceIndex(row.value, 'conditional fitting reference');
  const maximum = result.largest_gross_rectangle_vm_upper_bound_required_fy_reference_mpa;
  referenceClose(maximum, 80.57272595573455, 'nominal required fitting Fy reference');
  assert.equal(maximum, Math.max(...result.per_case_maximum_mpa.map(row => row.value)));
  assert.equal(result.actual_steel_fy, null);
  assert.equal(report.applicability_and_gaps.capacity_and_release, null);
  assert.deepEqual(report.release, {physical_fitting_strength: false, complete_connection_acceptance: false,
    fabrication: false, climbing: false});
  return {fitting_gross_strip_case_states: 144, fitting_gross_strip_section_ends: 2304,
    fitting_gross_strip_required_nominal_Fy_MPa: maximum, fitting_gross_strip_actual_Fy_MPa: null,
    fitting_gross_strip_strength_qualified: false};
}

export function validatePackerFreeSawnReference(report, index) {
  assert.equal(report.schema, 'v10_packer_free_sawn_connection_shear_evaluation/v1');
  assert.equal(report.revision, index.geometry.revision);
  assert.equal(report.status, 'bounded conditional reduced-depth shear component evaluations; corrected unordered-profile hulls; other connection checks and acceptance remain open');
  const bindings = report.current_bindings;
  const geometry = JSON.parse(bound(index.method_followups.geometry_method_followup));
  for (const ref of [bindings.physical_geometry, bindings.prepared_inputs, bindings.geometry_action_atlas]) referenceBinding(ref);
  assert.deepEqual(bindings.physical_geometry, geometry.current_model_bindings.physical_geometry);
  assert.deepEqual(bindings.prepared_inputs, geometry.current_model_bindings.prepared_inputs);
  assert.deepEqual(bindings.geometry_action_atlas, geometry.current_model_bindings.current_geometry_action_inventory);
  assert.deepEqual({path: bindings.six_case_response_bank.path, sha256: bindings.six_case_response_bank.sha256},
    geometry.current_model_bindings.six_case_bank);
  assert.equal(bindings.six_case_response_bank.all_six_cases_admitted, true);
  assert.deepEqual([...bindings.cases].sort(), [...CURRENT_CASES].sort());
  const prior = report.prior_current_receiver_core_qualification, coverage = prior.coverage;
  for (const [key, count] of Object.entries({profile_groups: 50, group_case_rows: 300, finished_BRep_exact_rectangles: 44,
    outer_post_inscribed_cores: 4, side_profile_sliver_cores_within_operative_tolerance: 2,
    outer_post_component_references_recalculated: 24})) assert.equal(coverage[key], count);
  referenceClose(coverage.max_outer_post_core_optional_two_edge_envelope_ratio, 0.738382, 'outer-post-only reference');
  referenceClose(coverage.max_all_50_groups_optional_two_edge_envelope_ratio, 0.7728831052664072, 'prior 50-group reference');
  assert.deepEqual(prior.outer_post_core_proof.core_bounds_mm,
    {V: [0, 139.7], left_U: [0, 79.375], right_U: [9.525, 88.9]});
  const replay = report.fresh_six_case_replay;
  for (const [key, count] of Object.entries({rows: 300, saved_full_cut_wrenches_replayed: 4032,
    complete_left_right_event_pairs: 1716, current_point_action_events_in_bands: 1716,
    current_prepared_centroid_intervals_joined_to_atlas: 136, field_shaft_descriptors_compared_to_preparation: 816,
    current_profile_grain_bands_rejoined_to_axes_and_bore_radii: 54, missing_band_boundaries: 0,
    missing_event_sides: 0, max_saved_closure_record_delta: 0, additional_current_group_case_rows: 24,
    additional_current_group_cut_wrenches: 408, total_group_scopes: 54, total_group_case_scopes: 324}))
    assert.equal(replay[key], count);
  const additional = report.additional_nonrectangular_current_groups;
  const groupNames = ['base_principal_center_left', 'base_principal_center_right', 'base_side_left', 'base_side_right'];
  assert.equal(additional.group_case_rows, 24);
  assert.deepEqual(additional.groups.map(row => row.group).sort(), groupNames);
  assert.deepEqual(additional.group_maxima.map(row => row.group).sort(), groupNames);
  assert.equal(additional.principal_center_exclusions?.length ?? 0, 0, 'the old unordered-polygon exclusions are not current');
  referenceClose(report.method.geometry_tolerances.separate_NDS_geometry_guard_mm, 0.001, 'NDS geometry guard');
  for (const core of additional.groups) {
    const principal = core.group.startsWith('base_principal_');
    assert.equal(core.all_current_bore_circles_fit, true);
    assert.equal(core.BRep_core_boolean_missing_volume_mm3, 0); assert.equal(core.BRep_core_boolean_unmodeled_volume_mm3, 0);
    referenceClose(core.actual_profile_d_mm, principal ? 139.70000076447488 : 139.7, 'full profile depth for denominator');
    referenceClose(core.inscribed_core_d_mm, principal ? 128.81257403 : 125.164287373, 'inscribed core depth');
    if (principal) referenceClose(core.near_edge_check.center_to_near_q_edge_mm, 33.7042949305785, '068/069 BRep near edge');
  }
  for (const row of additional.group_maxima) {assert.equal(row.loaded_edge, null); referenceIndex(row.ratio, 'conditional receiver reference');}
  assert.match(additional.current_profile_boundary_proof.vertex_ordering, /vertices_luv_mm is unordered/);
  assert.match(additional.current_profile_boundary_proof.vertex_ordering, /ordered convex hull/);
  assert.match(additional.references.signed_edge_classification, /068\/069 signed-net correction remains/);
  assert.match(additional.references.signed_edge_classification, /net force is away from the near edge in all six cases/);
  assert.match(additional.references.signed_edge_classification, /not an established NDS violation/);
  const discrepancy = report.producer_identity_discrepancy;
  referenceBinding(discrepancy.preserved_raw_claimed_V2_source);
  referenceBinding(discrepancy.currently_available_V2_profile_helper);
  assert.equal(discrepancy.preserved_raw_claimed_V2_source.path, discrepancy.currently_available_V2_profile_helper.path);
  assert.notEqual(discrepancy.preserved_raw_claimed_V2_source.sha256, discrepancy.currently_available_V2_profile_helper.sha256);
  assert.match(discrepancy.handling, /missing historical producer bytes were not fabricated or edited/);
  for (const ref of [prior.producer, prior.result]) referenceBinding(ref);
  referenceBinding(additional.producer, 'fea/generated/v10-packer-free-v1/connections/method-closure/geometry/nonrectangular-common-core-v5.py');
  referenceBinding(additional.source_result, 'fea/generated/v10-packer-free-v1/connections/method-closure/geometry/nonrectangular-common-core-v5.json');
  const foot = JSON.parse(bound(index.method_followups.rear_foot_shear_evaluation));
  assert.deepEqual(report.separate_prior_screens.outer_top_result.raw_result, geometry.result_binding.result);
  assert.deepEqual(report.separate_prior_screens.rear_foot_optional_envelope_flags.flags,
    foot.optional_envelope_exceedances.map(row => ({case: row.case_id, member: row.member, ratio: row.ratio})));
  assert.deepEqual(report.release, {climbing_released: false, fabrication_released: false, structural_acceptance: false});
  assert.match(report.scope, /Not a complete joint\/member qualification or physical demand bound/);
  const maximum = Math.max(coverage.max_all_50_groups_optional_two_edge_envelope_ratio,
    ...additional.group_maxima.map(row => row.ratio));
  referenceClose(maximum, 0.9643026546447111, 'additional conditional sawn reference');
  return {additional_sawn_group_count: 54, additional_sawn_case_rows: 324,
    additional_sawn_maximum_optional_envelope_ratio: maximum, additional_sawn_component_acceptance: null,
    additional_sawn_complete_joint_qualified: false, additional_sawn_principal_common_core_exclusions: 0,
    additional_sawn_principal_common_core_groups: 2,
    additional_sawn_exclusions_are_NDS_violations: false, additional_sawn_historical_producer_mismatch_disclosed: true};
}

export function validatePackerFreeMethodFollowups(reports, index) {
  referenceKeys(reports, Object.keys(PACKER_FREE_FOLLOWUP_SCHEMAS), 'current method followups');
  for (const [key, schema] of Object.entries(PACKER_FREE_FOLLOWUP_SCHEMAS)) assert.equal(reports[key].schema, schema);
  const primary = reports.primary_method_closure, geometry = reports.geometry_method_followup;
  const criteria = reports.connection_criterion_dispositions, contact = reports.contact_law_evaluation;
  const foot = reports.rear_foot_shear_evaluation, center = reports.rear_foot_centering_screen;
  const bank = JSON.parse(bound(index.response_bank)), receipt = JSON.parse(bound(index.geometry.receipt));
  const evaluation = JSON.parse(bound(index.engineering_review));
  const physicalGeometry = {path: 'fea/generated/v10-packer-free-v1/geometry-v1/geometry.json',
    sha256: receipt.checked_geometry.sha256};
  const rawBank = {path: 'fea/generated/v10-packer-free-v1/mechanics/analysis-v2/response-bank.json',
    sha256: index.response_bank.sha256};
  for (const report of [primary, criteria]) assert.equal(report.candidate, index.geometry.revision);
  for (const report of [geometry, contact, foot]) assert.equal(report.revision, index.geometry.revision);
  const criterionSources = Object.fromEntries(Object.entries(criteria.source_bindings).map(([key, row]) => {
    assert.ok(Array.isArray(row) && row.length === 2);
    const ref = {path: row[0], sha256: row[1]}; referenceBinding(ref); return [key, ref];
  }));
  for (const refs of [primary.source_bindings, geometry.current_model_bindings, contact.evidence_bindings,
    foot.source_bindings, center.source_refs]) for (const ref of Object.values(refs))
    if (ref && typeof ref === 'object' && !Array.isArray(ref)) referenceBinding({path: ref.path, sha256: ref.sha256});
  for (const ref of [primary.source_bindings.current_response_bank, geometry.current_model_bindings.six_case_bank,
    criterionSources.current_response_bank, foot.source_bindings.response_bank, center.source_refs.six_case_bank])
    assert.deepEqual(ref, rawBank, 'current followup bank required');
  assert.deepEqual(contact.evidence_bindings.current_response_bank, index.response_bank);
  assert.deepEqual(primary.source_bindings.current_method_report, index.connection_method_evaluation);
  assert.deepEqual(primary.source_bindings.current_evaluation, index.engineering_review);
  for (const ref of [geometry.current_model_bindings.physical_geometry, criterionSources.current_physical_geometry,
    contact.evidence_bindings.physical_geometry, foot.source_bindings.current_geometry, center.source_refs.current_geometry])
    assert.deepEqual(ref, physicalGeometry, 'current followup physical geometry required');
  for (const ref of [geometry.current_model_bindings.checked_receipt, foot.source_bindings.checked_geometry_receipt,
    center.source_refs.checked_geometry_receipt]) assert.deepEqual(ref, bank.physical_geometry);
  assert.deepEqual(contact.evidence_bindings.checked_geometry_receipt, index.geometry.receipt);
  for (const ref of [geometry.current_model_bindings.analysis_geometry, contact.evidence_bindings.prepared_analysis_geometry,
    foot.source_bindings.analysis_geometry]) assert.deepEqual(ref, bank.analysis_geometry);
  assert.deepEqual(criterionSources.current_wrench_atlas, index.method_source_joins.current_wrench_atlas);
  assert.deepEqual(criterionSources.current_primary_method_closure, primary.source_bindings.raw_method_closure);
  const flaggedAxes = Object.keys(evaluation.bearing_diagnostic_component_maxima).sort();
  assert.equal(flaggedAxes.length, 8);
  assert.deepEqual([...criteria.coverage.flagged_axes].sort(), flaggedAxes);
  assert.deepEqual([...criteria.coverage.cases].sort(), [...CURRENT_CASES].sort());
  assert.equal(criteria.coverage.flagged_case_rows, 48); assert.equal(criteria.coverage.current_atlas_rows, 672);
  assert.deepEqual(criteria.current_flagged_action_envelopes.map(row => row.axis).sort(), flaggedAxes);
  assert.ok(criteria.current_flagged_action_envelopes.every(row => row.atlas_rows.length === 6));
  assert.equal(new Set(criteria.current_flagged_action_envelopes.flatMap(row => row.atlas_rows)).size, 48);
  assert.deepEqual(primary.flagged_component_thresholds_not_capacities.map(row => row.axis_id).sort(), flaggedAxes);
  for (const key of ['actual_Fe_Fyb_Fy_Fu', 'actual_Cg_Cdelta', 'complete_group_capacity',
    'complete_connection_capacity', 'complete_simultaneous_six_wrench_interaction_pass']) assert.equal(primary.qualification[key], null);
  for (const key of ['actual_Cg', 'actual_Cdelta', 'NDS_group_capacity', 'complete_connection_capacity',
    'complete_NDS_acceptance', 'splitting_capacity']) assert.equal(criteria.disposition[key], null);
  assert.equal(criteria.disposition.no_automatic_Cg_or_1_over_n_acceptance, true);
  assert.equal(geometry.status, 'bounded_conditional_component_complete_TableD_and_other_joint_checks_open');
  assert.equal(geometry.conditional_outcome.group_case_comparisons, 12);
  assert.equal(geometry.conditional_outcome.all_case_rows.length, 12);
  assert.equal(contact.conditional_sawn_wood_mean_pressure_screen.panel_contact_rows_skipped, 942);
  assert.match(contact.scope, /conditional analytical evaluation, not structural acceptance/);
  assert.equal(foot.cut_inventory.case_group_rows, 12); assert.equal(foot.cut_inventory.total_full_cut_wrenches, 48);
  assert.equal(foot.cut_inventory.cuts_per_case_group_row, 4);
  assert.equal(foot.cut_inventory.all_full_force_and_moment_vectors_retained, true);
  const rearCutReference = {path: foot.case_results_reference.path, sha256: foot.case_results_reference.sha256};
  referenceBinding(rearCutReference);
  assert.deepEqual(foot.cut_inventory.raw_detail_reference, rearCutReference);
  assert.deepEqual(foot.source_bindings.raw_complete_source_inventory, rearCutReference);
  assert.deepEqual(foot.source_bindings.outer_top_component_result_separate, geometry.result_binding.result);
  assert.equal(foot.current_bank.all_six_cases_admitted, true);
  assert.deepEqual([...foot.current_bank.case_ids].sort(), [...CURRENT_CASES].sort());
  assert.equal(foot.current_bank.physical_force_bounds_established, false);
  assert.equal(foot.geometry.physical_geometry_sha256, receipt.checked_geometry.sha256);
  assert.equal(foot.geometry.physical_stock_or_drilling_observed, false); assert.equal(foot.actual_observations, null);
  const members = foot.geometry.members;
  assert.deepEqual(members.map(row => row.axis_id).sort(), ['rail_rear_bolt_left_1', 'rail_rear_bolt_right_1']);
  for (const member of members) {
    assert.equal(member.actual_loaded_edge_classification, null); assert.equal(member.local_couple_and_splitting_qualification, null);
    assert.deepEqual(member.edge_branches.map(row => row.branch).sort(), ['q_max_unloaded', 'q_min_unloaded']);
    for (const row of member.edge_branches) assert.ok(Number.isFinite(row.optional_component_reference_N) && row.optional_component_reference_N > 0);
  }
  const flags = foot.optional_envelope_exceedances;
  assert.deepEqual(flags.map(row => `${row.member}/${row.case_id}`).sort(),
    ['lumber_leg_left/a12-forward', 'lumber_leg_left/a12-left', 'lumber_leg_right/k12-right']);
  for (const row of flags) {
    assert.equal(row.actual_loaded_edge_classification, null);
    assert.equal(row.classification, 'optional conservative two-edge envelope exceedance; not a loaded-edge violation finding');
    assert.ok(Number.isFinite(row.ratio) && row.ratio > 1);
    const member = members.find(member => member.member === row.member);
    const branch = member.edge_branches.find(branch => branch.branch === row.optional_reference_branch);
    assert.equal(row.optional_lower_of_two_edge_reference_N, branch.optional_component_reference_N);
    assert.equal(row.optional_lower_of_two_edge_reference_N, Math.min(...member.edge_branches.map(branch => branch.optional_component_reference_N)));
  }
  const maximum = Math.max(...flags.map(row => row.ratio));
  referenceClose(maximum, 1.0977299914214838, 'optional rear-foot envelope maximum');
  for (const key of ['NDS_loaded_edge_violation_found', 'local_couples_and_splitting_resolved', 'other_modes_or_complete_joint_qualified'])
    assert.equal(foot.interpretation[key], false);
  assert.equal(foot.interpretation.three_optional_reference_exceedances, true);
  assert.equal(center.status, 'conditional_geometry_screen_only');
  assert.deepEqual(center.source_refs.prior_force_and_cut_result, rearCutReference);
  assert.deepEqual(center.source_refs.current_BREP_section_proof, foot.source_bindings.current_rear_foot_brep_proof);
  assert.equal(center.qualification.actual_physical_observations, null);
  for (const row of [primary.qualification, criteria.disposition, contact, foot, center.qualification, center.screen])
    for (const key of ['structural_acceptance', 'physical_failure_claim', 'fabrication_released', 'climbing_released',
      'complete_joint_qualified', 'physical_demand_bounds_established', 'adopted', 'actual_new_pass', 'actual_pass'])
      if (Object.hasOwn(row, key)) assert.ok(row[key] === false || row[key] === null, `followup claim boundary: ${key}`);
  const fitting = validatePackerFreeFittingReference(reports.fitting_gross_strip_reference, index);
  const sawn = validatePackerFreeSawnReference(reports.sawn_connection_shear_evaluation, index);
  return {...fitting, ...sawn, optional_rear_foot_case_group_rows: 12, optional_rear_foot_full_cut_wrenches: 48,
    optional_rear_foot_envelope_case_rows: flags.length, optional_rear_foot_envelope_axes: members.length,
    optional_rear_foot_maximum_envelope_ratio: maximum, optional_rear_foot_actual_loaded_edge: null,
    optional_rear_foot_NDS_loaded_edge_violation_found: false, optional_rear_foot_centering_adopted: false};
}

export function checkDevelopment(index = readIndex(), {entryChecks = true} = {}) {
  if (index.schema === 'bolted_frame_development_revisions/v17') {
    assert.equal(index.preceding_revision.schema, 'bolted_frame_development_revisions/v16');
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const retained = index.preceding_revision.next_candidate_constraint;
    assert.equal(retained.new_geometry_and_matched_bank_complete, true);
    assert.equal(index.geometry.revision, PACKER_FREE_REVISION);
    for (const [current, earlier] of [
      [index.geometry.receipt, retained.trial_geometry_receipt],
      [index.response_bank, retained.trial_response_bank],
      [index.engineering_review, retained.trial_evaluation],
      [index.stock_planning, retained.conditional_stock_planning],
      [index.owner_no_packers, retained.owner_record],
      [index.current_stock_documents, index.preceding_revision.current_stock_documents],
      [index.selected_baseline, index.preceding_revision.selected_baseline],
    ]) assert.deepEqual(current, earlier, 'current packer-free authority must retain its validated source');
    const geometryViewer = retained.repository_geometry_viewer;
    assert.equal(index.geometry.viewer, geometryViewer.model);
    assert.equal(index.geometry.viewer_url, geometryViewer.url);
    assert.deepEqual(index.geometry.scene, geometryViewer.scene);
    for (const name of ['base_rail_top', 'base_side_left', 'base_side_right'])
      assert.deepEqual(index.geometry.actual_sections_mm[name], retained.top_and_both_sides_actual_mm);
    const viewer = index.repository_viewer;
    assert.equal(viewer.model, PACKER_FREE_MODEL);
    assert.equal(viewer.model, index.geometry.viewer);
    assert.equal(viewer.url, index.geometry.viewer_url);
    for (const [current, earlier] of [
      [viewer.scene, geometryViewer.scene], [viewer.provenance, geometryViewer.provenance],
      [viewer.frozen_export, geometryViewer.frozen_export],
      [viewer.geometry_overlay, geometryViewer.overlay], [viewer.geometry_publisher, geometryViewer.publisher],
    ]) assert.deepEqual(current, earlier, 'results must retain the validated geometry viewer');
    assert.equal(viewer.geometry_only, false);
    assert.equal(viewer.ignored_runtime_dependencies, false);
    assert.equal(viewer.published_or_deployed, false);
    assert.deepEqual(viewer.results_json, PACKER_FREE_RESULTS_ASSET);
    referenceBinding(viewer.results_overlay, 'site/eoere-packer-free-results.mjs');
    referenceBinding(viewer.results_publisher, 'scripts/publish_packer_free_results.py');
    bound(viewer.results_overlay); bound(viewer.results_publisher);
    const results = validatePackerFreeResults(JSON.parse(bound(viewer.results_json)));
    assert.deepEqual(results.geometry_receipt, index.geometry.receipt);
    assert.deepEqual(results.geometry_provenance, viewer.provenance);
    assert.deepEqual(results.sources.evaluation, index.engineering_review);
    assert.deepEqual(results.sources.response_bank, index.response_bank);
    assert.equal(results.producer, viewer.results_publisher.path);
    validatePackerFreeMethodEvaluation(JSON.parse(bound(index.connection_method_evaluation)), index);
    referenceKeys(index.method_source_joins, ['current_wrench_atlas', 'v3_post_audit'], 'current method evidence joins');
    const evaluation = JSON.parse(bound(index.engineering_review));
    assert.deepEqual(index.method_source_joins.current_wrench_atlas, evaluation.current_wrench_atlas);
    for (const ref of Object.values(index.method_source_joins)) {
      referenceBinding(ref);
      assert.ok(ref.path.startsWith('fea/generated/v10-packer-free-v1/'), 'own current method evidence required');
    }
    referenceKeys(index.method_followups, Object.keys(PACKER_FREE_FOLLOWUP_SCHEMAS), 'current public method followups');
    const followups = Object.fromEntries(Object.entries(index.method_followups).map(([key, ref]) => {
      referenceBinding(ref, `docs/bolted-frame-development/owner-frame-v10/packer-free/${key.replaceAll('_', '-')}.json`);
      return [key, JSON.parse(bound(ref))];
    }));
    const optionalRearFoot = validatePackerFreeMethodFollowups(followups, index);
    const stock = JSON.parse(bound(index.stock_planning));
    assert.ok(stock.scope.startsWith('Wood allocation only.'), 'non-wood purchases remain outside stock planning');
    const spacers = JSON.parse(bound(index.hardware_spacer_mapping));
    assert.equal(spacers.schema, 'eoere_packer_free_spacer_catalog_mapping/v1');
    assert.equal(spacers.revision, index.geometry.revision);
    assert.deepEqual(spacers.geometry_receipt, index.geometry.receipt);
    assert.equal(spacers.current_spacer_pieces, 40);
    assert.deepEqual(spacers.nominal_catalog_SKU_quantities, {'13731': 20, '13733': 20});
    assert.deepEqual(index.hardware_model.nominal_spacer_SKU_quantities, spacers.nominal_catalog_SKU_quantities);
    assert.deepEqual(spacers.recovered_selected_field_blanks, [
      'eoere_bolt_081_spacer', 'eoere_bolt_082_spacer', 'eoere_bolt_083_spacer', 'eoere_bolt_084_spacer',
      'v10_header_bolt_001_spacer', 'v10_header_bolt_002_spacer', 'v10_header_bolt_003_spacer', 'v10_header_bolt_004_spacer']);
    for (const key of ['actual_dimensions_or_material_verified', 'actual_strength_or_fit_qualified',
      'geometry_or_matched_forces_changed', 'purchase_authorized', 'structural_acceptance',
      'fabrication_released', 'climbing_released']) assert.equal(spacers[key], false);
    assert.ok(index.conditional_frame_evaluation == null, 'no inherited complete frame acceptance');
    for (const key of ['actual_Cg_adopted', 'actual_Cdelta_adopted', 'complete_connection_acceptance'])
      assert.equal(index[key], null);
    for (const key of ['complete_joint_qualified', 'structural_acceptance', 'fabrication_released',
      'climbing_released', 'purchase_authorized', 'physical_operations_authorized']) assert.equal(index[key], false);
    assert.equal(index.panel_Hillman_resolution_deferred, true);
    assert.equal(index.agent_review_loop_suspended, true);
    assert.deepEqual(index.hardware_model, {actual_parts_verified: false, bolt_stacks: 112,
      nominal_spacer_SKU_quantities: {'13731': 20, '13733': 20},
      selected_for_build: false, spacer_pieces: 40, washers: 224, wood_packers: 0});
    assert.deepEqual(index.shop, {...index.preceding_revision.shop, revision: index.geometry.revision});
    if (index.development_selection) assert.equal(index.development_selection.revision, index.geometry.revision);
    const html = read('site/index.html').toString();
    assert.equal(viewerModel(html, null), index.selected_baseline.candidate);
    assert.equal(viewerModel(html, viewer.model), viewer.model);
    assert.ok(html.includes("import {loadPackerFreeResultsScene} from './eoere-packer-free-results.mjs'"));
    const unselectedTrials = {};
    const trial = index.unselected_trials?.center_far_row_only;
    if (trial !== undefined) {
      assert.ok(trial && typeof trial === 'object' && !Array.isArray(trial), 'unselected trial record required');
      const provenance = validateCenterFarRowProvenance(JSON.parse(bound(trial.viewer.provenance)));
      const report = JSON.parse(bound(trial.evaluation));
      const metadata = validateUnselectedCenterFarRowTrial(trial, report, provenance);
      bound(trial.viewer.adapter);
      const decoded = gunzipSync(bound(trial.viewer.scene));
      assert.equal(sha(decoded), provenance.scene.decoded_sha256);
      const scene = validateCenterFarRowScene(JSON.parse(decoded));
      assert.deepEqual(report.bindings.physical_geometry, scene.geometry_source);
      assert.deepEqual(scene.geometry_receipt, provenance.sources.geometry_receipt);
      assert.deepEqual(provenance.parent_results, viewer.results_json);
      assert.deepEqual(scene.parent_results, viewer.results_json);
      bound(report.bindings.response_bank); bound(report.bindings.checked_receipt);
      assert.equal(viewerModel(html, trial.viewer.model), trial.viewer.model);
      unselectedTrials.center_far_row_only = metadata;
    }
    if (index.subassembly_action_map !== undefined) {
      referenceBinding(index.subassembly_action_map, 'docs/bolted-frame-development/owner-frame-v10/packer-free/subassembly-action-map.json');
      validateLocalSubassemblyActionMap(JSON.parse(bound(index.subassembly_action_map)), index);
    }
    if (index.hardware_planning !== undefined) {
      referenceBinding(index.hardware_planning, 'docs/bolted-frame-development/owner-frame-v10/packer-free/hardware-planning.json');
      validateCurrent112HardwarePlanning(JSON.parse(bound(index.hardware_planning)), index);
    }
    if (index.group_effects_assessment !== undefined) {
      referenceBinding(index.group_effects_assessment, 'docs/bolted-frame-development/owner-frame-v10/packer-free/group-effects-assessment.json');
      validateCurrent112GroupEffects(JSON.parse(bound(index.group_effects_assessment)), index);
    }
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    return {passed: true, ...optionalRearFoot, unselected_trials: unselectedTrials,
      revision: index.geometry.revision, bolt_axes: 112, screw_axes: 66, angles: 24,
      occupied_parts: 1125, spacer_pieces: 40, wood_packers: 0, current_response_revision: index.geometry.revision,
      repository_viewer_integrated: true, repository_viewer_model: viewer.model, geometry_only: false,
      reference_case_exceedances: 15, reference_component_exceedances: 8, bearing_diagnostic_case_rows: 15,
      actual_Cg_adopted: null, actual_Cdelta_adopted: null, complete_connection_acceptance: null,
      complete_joint_qualified: false, structural_acceptance: false, fabrication_released: false,
      climbing_released: false, purchase_authorized: false, stock_planning_scope: 'wood allocation only',
      preserved_previous_development_revision: prior.revision, selected_baseline_candidate: index.selected_baseline.candidate,
      full_ignored_input_closure_checked: false, mechanics_executed: false};
  }
  if (index.schema === 'bolted_frame_development_revisions/v16') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.standard_side_stock_evaluation));
    const owner = JSON.parse(bound(index.owner_side_constraint));
    const geometry = JSON.parse(bound(index.geometry.receipt));
    const bank = JSON.parse(bound(index.response_bank));
    const review = JSON.parse(bound(index.engineering_review));
    const inventory = JSON.parse(bound(index.exceedance_inventory));
    const revision = 'v10-standard-4x6-top-and-sides-development-v1';
    const stock = JSON.parse(bound(index.stock_planning));
    assert.equal(stock.schema, 'eoere_v10_standard_stock_planning_sources/v1');
    assert.equal(stock.revision, revision);
    for (const ref of Object.values(stock.outputs)) {
      const snapshot = index.stock_planning_frozen_output_snapshots?.[ref.path];
      if (snapshot) {
        assert.equal(index.next_candidate_constraint.wood_packers_permitted, false);
        assert.ok(['docs/bolted-frame-development/owner-frame-v10/standard-stock-planning.md',
          'docs/bolted-frame-development/owner-frame-v10/buying-list-current.csv'].includes(ref.path));
        assert.equal(snapshot.sha256, ref.sha256);
        bound(snapshot);
      } else bound(ref);
    }
    for (const [key, ref] of Object.entries(stock.source_bindings))
      if (key !== 'allocation_physical_geometry') bound(ref);
    assert.deepEqual(stock.source_bindings.allocation_physical_geometry, report.geometry);
    for (const imported of Object.values(stock.imports)) {
      assert.equal(imported.integrated.sha256, imported.original.sha256);
      bound(imported.integrated);
    }
    assert.deepEqual(stock.source_bindings.current_checked_geometry_receipt, index.geometry.receipt);
    assert.deepEqual(stock.source_bindings.current_response_bank, index.response_bank);
    assert.deepEqual(stock.dimensional_validation.board_counts,
      {stock_2x6x10: 3, stock_2x6x8: 5, stock_4x6x10: 3, stock_4x6x8: 2});
    assert.equal(stock.dimensional_validation.sawn_members, 22);
    assert.equal(stock.current_buying_CSV.obsolete_4x8_solid_timber_row_removed, true);
    for (const key of ['structural_acceptance', 'fabrication_released', 'climbing_released'])
      assert.equal(stock[key], false);
    assert.equal(owner.schema, 'owner-standard-side-4x6-v1');
    assert.deepEqual(owner.owner_constraint.actual_cross_section_mm, [88.9, 139.7]);
    assert.deepEqual(owner.owner_constraint.members, ['base_side_left', 'base_side_right']);
    assert.equal(report.schema, 'eoere_v10_standard_side_stock_evaluation/v1');
    for (const row of [index.geometry, report, geometry]) assert.equal(row.revision, revision);
    assert.equal(index.development_selection.revision, revision);
    assert.deepEqual(index.development_selection.actual_sections_mm, report.actual_sections_mm);
    assert.equal(index.development_selection.custom_packers_approved, false);
    assert.equal(index.development_selection.purchase_authorized, false);
    assert.equal(index.hardware_model.selected_for_build, false);
    assert.equal(index.hardware_model.actual_parts_verified, false);
    assert.equal(index.shop.instructions_current_for_fabrication, false);
    assert.equal(index.shop.historical_cut_drill_packet_current, false);
    assert.equal(index.complete_joint_qualified, false);
    assert.equal(index.physical_operations_authorized, false);
    assert.ok(index.conditional_frame_evaluation == null, 'no inherited complete frame acceptance');
    for (const key of ['actual_Cg_adopted', 'actual_Cdelta_adopted', 'complete_connection_acceptance'])
      assert.equal(index[key], null);
    assert.deepEqual(report.owner_constraint, index.owner_side_constraint);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    assert.equal(report.new_geometry_verified, true);
    assert.equal(report.new_sixcase_bank_complete, true);
    assert.equal(report.old_152p4_side_geometry_results_and_bound_group_scenarios_transferred, false);
    for (const name of ['base_side_left', 'base_side_right', 'base_rail_top'])
      assert.deepEqual(report.actual_sections_mm[name], [88.9, 139.7]);
    assert.deepEqual(geometry.checked_geometry, report.geometry);
    assert.deepEqual(geometry.checked_clearance, report.clearance);
    assert.equal(geometry.nominal_geometry_clear, true);
    assert.equal(geometry.counts.occupied_parts_checked, 1151);
    assert.equal(geometry.counts.structural_axes, 116);
    assert.equal(geometry.counts.panel_screw_axes, 66);
    assert.equal(geometry.counts.side_receiver_bore_cores_checked, 30);
    assert.deepEqual(bank.physical_geometry, index.geometry.receipt_source);
    assert.equal(bank.geometry_revision, revision);
    assert.equal(bank.all_six_cases_admitted, true);
    assert.deepEqual(bank.case_ids, CURRENT_CASES);
    assert.equal(bank.cases.length, 6);
    assert.equal(bank.admission_gate_N, 1e-5);
    assert.deepEqual(bank.load_contract, V10_CANDIDATE13_LOAD);
    assert.deepEqual(report.load_contract, bank.load_contract);
    assert.equal(report.gravity_m_s2, 9.80665);
    const oldBank = JSON.parse(bound(index.preceding_revision.development_selection.response_bank));
    const oldFields = new Set(oldBank.cases.map(row => row.field.sha256));
    for (const row of bank.cases) {
      assert.equal(row.both_independent_replays_admitted, true);
      assert.ok(row.gradient_inf_N < 1e-5);
      assert.ok(row.field.path.includes('/v10-standard-side-stock-v1/'));
      assert.ok(!oldFields.has(row.field.sha256), 'old deeper-side forces cannot be reused');
    }
    const fields = Object.fromEntries(bank.cases.map(row => [row.case_id, row.field]));
    for (const row of [review, inventory]) {
      assert.deepEqual(row.analysis_geometry, bank.analysis_geometry);
      assert.deepEqual(row.field_bindings, fields);
    }
    assert.equal(review.geometry_revision, revision);
    assert.deepEqual(review.load_contract, bank.load_contract);
    assert.deepEqual(report.artifacts.geometry_receipt, index.geometry.receipt);
    assert.deepEqual(report.artifacts.response_bank, index.response_bank);
    assert.deepEqual(report.artifacts.reference_review, index.engineering_review);
    assert.deepEqual(report.artifacts.diagnostic_inventory, index.exceedance_inventory);
    assert.deepEqual(report.artifacts.connection_review, index.connection_review);
    for (const ref of Object.values(report.artifacts)) bound(ref);
    const connection = JSON.parse(bound(index.connection_review));
    assert.equal(connection.revision, revision);
    assert.deepEqual(connection.geometry, report.geometry);
    assert.deepEqual(connection.response_bank, report.response_bank_source);
    assert.equal(connection.axis_case_rows, 228);
    assert.equal(connection.signed_plane_wrenches, 312);
    assert.equal(connection.receiver_actions_with_local_moments, 540);
    assert.equal(connection.status, 'UNRESOLVED');
    assert.equal(connection.legacy_signature_1_over_n_used_for_acceptance, false);
    for (const key of ['actual_Cg', 'actual_Cdelta', 'complete_group_capacity',
      'complete_wrench_interaction_pass', 'upper_cleat_three_media_Cg']) assert.equal(connection[key], null);
    assert.deepEqual(review.response_bank, report.response_bank_source);
    assert.equal(inventory.count_above_reference_case_rows, inventory.above_reference_case_rows.length);
    assert.equal(report.reference_case_exceedances, inventory.count_above_reference_case_rows);
    assert.equal(report.reference_component_exceedances, inventory.component_maxima.length);
    assert.equal(report.bearing_diagnostic_case_rows, inventory.above_reference_case_rows
      .filter(row => row.criterion === 'wood_bearing_whole_affine').length);
    assert.deepEqual(report.reference_maxima, review.numerical_reference_maxima);
    assert.equal(report.custom_packers.stock_and_geometry_approved, false);
    assert.deepEqual(report.custom_packers.members, ['top_packer_left', 'top_packer_right']);
    assert.equal(report.lengths_provisional, true);
    assert.equal(report.connection_assessment.status, 'UNRESOLVED');
    assert.equal(report.connection_assessment.legacy_signature_1_over_n_used_for_acceptance, false);
    for (const key of ['actual_Cg_adopted', 'actual_Cdelta_adopted',
      'upper_cleat_three_media_Cg', 'complete_connection_acceptance']) assert.equal(report[key], null);
    for (const row of [index, report, bank, review, inventory]) for (const key of [
      'structural_acceptance', 'fabrication_released', 'climbing_released']) assert.equal(row[key], false);
    assert.equal(index.purchase_authorized, false);
    assert.equal(report.purchase_authorized, false);
    assert.equal(index.other_nonstandard_member_stock_approved, false);
    assert.equal(index.geometry.viewer_scope, 'repository_local_site');
    const repositoryViewer = index.repository_viewer;
    assert.equal(repositoryViewer.model, index.geometry.viewer);
    assert.equal(repositoryViewer.url, index.geometry.viewer_url);
    assert.deepEqual(repositoryViewer.scene, index.geometry.scene);
    assert.equal(repositoryViewer.ignored_runtime_dependencies, false);
    assert.equal(repositoryViewer.historical_aliases_preserved, true);
    assert.equal(repositoryViewer.selected_baseline_changed, false);
    assert.equal(repositoryViewer.published_or_deployed, false);
    const nextConstraint = index.next_candidate_constraint;
    if (nextConstraint) {
      const ownerDirection = JSON.parse(bound(nextConstraint.owner_record));
      assert.equal(ownerDirection.schema, 'owner-no-wood-packers-v1');
      assert.equal(nextConstraint.wood_packers_permitted, false);
      assert.deepEqual(nextConstraint.top_and_both_sides_actual_mm, [88.9, 139.7]);
      assert.equal(nextConstraint.current_packer_bank_transferred_to_new_design, false);
      if (nextConstraint.trial_response_bank) {
        const trialBank = JSON.parse(bound(nextConstraint.trial_response_bank));
        const evaluation = JSON.parse(bound(nextConstraint.trial_evaluation));
        assert.equal(nextConstraint.new_geometry_and_matched_bank_complete, true);
        assert.equal(trialBank.geometry_revision, 'v10-packer-free-flush-return-far-row-only-v1');
        assert.equal(evaluation.schema, 'eoere_packer_free_matched_reference_evaluation/v1');
        assert.equal(evaluation.revision, trialBank.geometry_revision);
        assert.deepEqual(evaluation.response_bank, nextConstraint.trial_response_bank);
        assert.deepEqual(evaluation.geometry_receipt, nextConstraint.trial_geometry_receipt);
        assert.deepEqual(trialBank.analysis_geometry, evaluation.analysis_geometry);
        assert.equal(trialBank.physical_geometry.sha256, nextConstraint.trial_geometry_receipt.sha256);
        assert.equal(trialBank.all_six_cases_admitted, true);
        assert.equal(trialBank.admission_gate_N, 1e-5);
        assert.ok(trialBank.maximum_gradient_inf_N < trialBank.admission_gate_N);
        assert.deepEqual(trialBank.load_contract, {accessory_mass_kg: 25, downward_multiplier: 2,
          duration_factor_CD: 1, horizontal_force_N: 300, weight_lb: 250});
        assert.deepEqual(trialBank.case_ids, ['a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear']);
        assert.deepEqual(trialBank.cases.map(row => row.case_id), trialBank.case_ids);
        for (const row of trialBank.cases) {
          assert.equal(row.both_independent_replays_admitted, true);
          assert.ok(row.field.path.includes('/v10-packer-free-v1/mechanics/analysis-v2/'));
          assert.ok(row.gradient_inf_N < trialBank.admission_gate_N);
        }
        assert.equal(evaluation.physical_inventory.wood_packers, 0);
        assert.equal(evaluation.physical_inventory.bolt_stacks, 112);
        assert.equal(evaluation.bearing_diagnostic_case_rows, 15);
        assert.equal(evaluation.bearing_diagnostic_components, 8);
        assert.equal(evaluation.bearing_diagnostic_rows.length, 15);
        assert.equal(evaluation.actual_Cg_adopted, null);
        assert.equal(evaluation.actual_Cdelta_adopted, null);
        assert.equal(evaluation.complete_connection_acceptance, null);
        for (const item of [trialBank, evaluation]) for (const key of
          ['structural_acceptance', 'fabrication_released', 'climbing_released']) assert.equal(item[key], false);
      } else assert.equal(nextConstraint.new_geometry_and_matched_bank_complete, false);
      assert.equal(nextConstraint.old_packer_machining_and_allocation_on_hold, true);
      if (nextConstraint.trial_geometry_receipt) {
        const trial = JSON.parse(bound(nextConstraint.trial_geometry_receipt));
        assert.equal(trial.revision, 'v10-packer-free-flush-return-far-row-only-v1');
        assert.equal(trial.checked_geometry.sha256, '9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde');
        assert.equal(trial.counts.bolts, 112);
        assert.equal(trial.counts.spacer_pieces, 40);
        assert.equal(trial.counts.occupied_parts_checked, 1125);
        assert.equal(trial.nominal_geometry_clear, true);
        assert.equal(trial.fresh_matched_mechanics_required, true);
        assert.equal(trial.structural_acceptance, false);
        assert.equal(trial.fabrication_released, false);
        assert.equal(trial.climbing_released, false);
      }
      if (nextConstraint.repository_geometry_viewer) {
        const viewer = nextConstraint.repository_geometry_viewer;
        assert.equal(viewer.model, 'eoere-packer-free-standard-stock-preview');
        assert.equal(viewer.ignored_runtime_dependencies, false);
        assert.equal(viewer.geometry_only, true);
        assert.equal(viewer.published_or_deployed, false);
        bound(viewer.overlay); bound(viewer.publisher);
        const provenance = JSON.parse(bound(viewer.provenance));
        validatePackerFreeProvenance(provenance, JSON.parse(bound(viewer.frozen_export)));
        validatePackerFreeDelta(JSON.parse(gunzipSync(bound(viewer.scene))));
        assert.deepEqual(provenance.geometry_receipt, nextConstraint.trial_geometry_receipt);
        assert.deepEqual(provenance.parent_provenance, index.repository_viewer.provenance);
        assert.equal(viewerModel(read('site/index.html').toString(), viewer.model), viewer.model);
      }
      if (nextConstraint.conditional_stock_planning) {
        const plan = JSON.parse(bound(nextConstraint.conditional_stock_planning));
        assert.equal(plan.schema, 'eoere_v10_packer_free_first_trial_stock_planning/v1');
        assert.deepEqual(plan.source_bindings.checked_geometry_receipt, nextConstraint.trial_geometry_receipt);
        assert.equal(plan.sawn_coverage_count, 20);
        assert.equal(plan.wood_packer_count, 0);
        assert.deepEqual(plan.unassigned_sawn_members, []);
        assert.deepEqual(plan.duplicate_member_assignments, []);
        assert.deepEqual(plan.counts.map(row => row.boards), [5, 3, 3, 2]);
        assert.equal(plan.boards.length, 13);
        const members = plan.boards.flatMap(row => row.members);
        assert.equal(members.length, 20);
        assert.equal(new Set(members).size, 20);
        assert.ok(!members.some(name => name.includes('packer')));
        for (const row of plan.boards) {
          const used = row.member_lengths_mm.reduce((sum, value) => sum + value, 0)
            + 2 * plan.allowances.trim_each_board_end_mm
            + row.members.length * plan.allowances.kerf_each_member_mm;
          assert.ok(Math.abs(used - row.including_trim_and_kerf_mm) < 1e-6);
          assert.ok(Math.abs(row.length_ft * 304.8 - used - row.remaining_mm) < 1e-6);
          assert.ok(row.remaining_mm >= 0);
          assert.equal(row.Actual, ''); assert.equal(row.Disposition, '');
        }
        assert.deepEqual(plan.outputs.current_buying_CSV, index.current_stock_documents['buying-list-current.csv']);
        assert.deepEqual(plan.outputs.standard_stock_document, index.current_stock_documents['standard-stock-planning.md']);
        for (const key of ['actual_grade_moisture_dimensions_or_supply_verified',
          'purchases_or_physical_changes_authorized', 'prior_forces_or_structural_acceptance_transferred',
          'structural_acceptance', 'fabrication_released', 'climbing_released']) assert.equal(plan[key], false);
      }
      for (const [key, ref] of Object.entries(index.current_stock_documents)) {
        assert.equal(ref.path, `docs/bolted-frame-development/owner-frame-v10/${key}`);
        bound(ref);
      }
      assert.deepEqual(Object.keys(index.current_stock_documents).sort(),
        ['buying-list-current.csv', 'standard-stock-planning.md']);
      for (const key of ['purchase_authorized', 'fabrication_released', 'climbing_released'])
        assert.equal(nextConstraint[key], false);
    }
    const methods = JSON.parse(bound(index.connection_method_evaluation));
    assert.equal(methods.schema, 'eoere_standard_stock_connection_method_evaluation/v1');
    assert.equal(methods.revision, revision);
    assert.deepEqual(methods.response_bank, index.response_bank);
    assert.deepEqual(methods.reference_review, index.engineering_review);
    assert.deepEqual(methods.diagnostic_inventory, index.exceedance_inventory);
    bound(methods.cleat_input_interpretation);
    assert.deepEqual(methods.frozen_matched_evaluation, index.standard_side_stock_evaluation);
    assert.equal(methods.coverage.axis_case_wrenches, 696);
    assert.equal(methods.coverage.complete_qualified_connection_rows, 0);
    assert.equal(methods.actual_Cg, null);
    assert.equal(methods.actual_Cdelta, null);
    assert.equal(methods.complete_connection_acceptance, null);
    for (const key of ['purchase_authorized', 'fabrication_released', 'climbing_released', 'structural_acceptance'])
      assert.equal(methods[key], false);
    bound(repositoryViewer.overlay); bound(repositoryViewer.publisher);
    const viewerProvenance = JSON.parse(bound(repositoryViewer.provenance));
    const viewerStatus = JSON.parse(bound(repositoryViewer.status));
    validateStandardStockProvenance(viewerProvenance, viewerStatus);
    validateStandardStockScene(JSON.parse(gunzipSync(bound(repositoryViewer.scene))));
    assert.equal(viewerProvenance.geometry_sha256, report.geometry.sha256);
    for (const [key, ref] of Object.entries({geometry_receipt: index.geometry.receipt,
      response_bank: index.response_bank, reference_review: index.engineering_review,
      diagnostic_inventory: index.exceedance_inventory})) assert.deepEqual(viewerProvenance.result_sources[key], ref);

    const html = read('site/index.html').toString();
    assert.equal(viewerModel(html, null), index.selected_baseline.candidate);
    assert.equal(viewerModel(html, repositoryViewer.model), repositoryViewer.model);
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    return {passed: true, revision, bolt_axes: 116, screw_axes: 66, angles: 24,
      occupied_parts: 1151, spacer_pieces: 44, current_response_revision: revision,
      repository_viewer_integrated: true, repository_viewer_model: repositoryViewer.model,
      next_candidate_revision: nextConstraint?.trial_revision ?? null,
      next_candidate_own_matched_bank_complete: nextConstraint?.new_geometry_and_matched_bank_complete ?? false,
      next_candidate_bolt_stacks: nextConstraint?.trial_response_bank ? 112 : null,
      reference_case_exceedances: report.reference_case_exceedances,
      reference_component_exceedances: report.reference_component_exceedances,
      bearing_diagnostic_case_rows: report.bearing_diagnostic_case_rows,
      legacy_signature_1_over_n_used_for_acceptance: false, connection_assessment_status: 'UNRESOLVED',
      actual_Cg_adopted: null, complete_connection_acceptance: null, custom_packers_approved: false,
      purchase_authorized: false, other_nonstandard_member_stock_approved: false,
      structural_acceptance: false, fabrication_released: false, climbing_released: false,
      preserved_previous_development_revision: prior.revision,
      preserved_integrated_package_revision: index.preceding_revision.geometry.revision,
      selected_baseline_candidate: index.selected_baseline.candidate, mechanics_executed: false};
  }
  if (index.schema === 'bolted_frame_development_revisions/v15') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const data = readV10Candidate13Authority(index);
    const result = validateV10Candidate13Authority(index, data);
    const html = read('site/index.html').toString();
    for (const model of [index.geometry.viewer, index.preserved_owner_v9_viewer, 'eoere-owner-frame-v10-development'])
      assert.equal(viewerModel(html, model), model, 'current and preserved development viewers must remain selectable');
    assert.equal(viewerModel(html, null), index.selected_baseline.candidate);
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    return {...result, revision: index.development_selection.revision,
      occupied_parts: 1151, spacer_pieces: 44, trial_case_flags: 15, trial_flagged_components: 8,
      current_response_revision: index.development_selection.revision,
      candidate_selection_only: true, other_nonstandard_member_stock_approved: false, purchase_authorized: false,
      legacy_signature_1_over_n_used_for_acceptance: false,
      connection_assessment_status: 'UNRESOLVED', complete_connection_acceptance: null,
      preserved_integrated_package_revision: result.revision,
      preserved_previous_development_revision: prior.revision,
      selected_baseline_candidate: index.selected_baseline.candidate};
  }

  if (index.schema === 'bolted_frame_development_revisions/v14') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_single_spacer_revision/v1');
    assert.equal(report.revision, 'eoere-single-spacer-cleat-stacks-v9');
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    for (const row of [index.geometry, index.hardware_model, index.shop]) assert.equal(row.revision, report.revision);
    assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
    assert.deepEqual(index.shop.geometry, index.geometry.receipt);assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.equal(index.conditional_frame_evaluation, null);
    for (const key of ['engineering_review', 'testing_review', 'bolt_geometry_review', 'panel_bracing_review']) if (index[key]) {
      const review = JSON.parse(bound(index[key]));
      assert.equal(review.geometry_revision, report.revision, 'changed hardware needs its own applicable review');
      assert.deepEqual(review.physical_geometry, index.geometry.receipt);
      if (key === 'bolt_geometry_review') validateCurrentBoltGeometryReview(review, index);
      if (key === 'engineering_review') validateCurrentConventionalReferenceReview(review, index);
      if (key === 'panel_bracing_review') validateCurrentPanelBracingSummary(review, index);
    }
    if (index.response_bank) validateOwnResponseBank(JSON.parse(bound(index.response_bank)), index);
    for (const row of [index, report]) {
      assert.equal(row.fabrication_released, false);assert.equal(row.climbing_released, false);
      assert.equal(row.panel_Hillman_resolution_deferred, true);
    }
    for (const flag of ['current_response_computed', 'historical_capacity_transferred', 'complete_conditional_frame_evaluation',
      'actual_parts_verified']) assert.equal(report[flag], false);
    for (const flag of ['nominal_geometry_clear', 'nominal_catalog_windows_checked',
      'timber_holes_fittings_and_66_screws_unchanged', 'forty_inward_stacks_preserved']) assert.equal(report[flag], true);
    assert.equal(report.changed_stacks, 8);assert.equal(report.changed_parts, 24);assert.equal(report.removed_spacer_parts, 16);
    assert.equal(report.actual_observations, null);bound(report.producer);
    for (const binding of Object.values(report.files)) bound(binding);
    const previous = JSON.parse(bound(index.preceding_revision.geometry.receipt));
    assert.deepEqual(report.counts, {...previous.counts, spacer_pieces: 16, occupied_parts: 1021});
    const parameters = JSON.parse(bound(report.files['candidate-parameters.json']));
    assert.deepEqual(parameters.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(parameters.parent_checked_geometry, previous.checked_geometry);
    assert.equal(parameters.axis_updates.length, 8);assert.equal(parameters.part_transforms.length, 24);
    assert.equal(parameters.removed_parts.length, 16);assert.equal(parameters.actual_parts_verified, false);
    assert.equal(parameters.mechanical_force_or_strength_results_transferred, false);
    bound(parameters.producer);
    const oldAxes = new Map(JSON.parse(bound(previous.files['axis-updates.json'])).axes.map(a => [a.id, a]));
    for (const update of parameters.axis_updates) {
      assert.deepEqual(update.before_axis, oldAxes.get(update.axis_id));
      for (const key of ['id', 'point_xyz_mm', 'direction_xyz', 'diameter_mm', 'bore_diameter_mm', 'attachments',
        'receivers', 'grip_mm', 'before_plate_mm', 'after_plate_mm', 'head_faces', 'nut_faces'])
        assert.deepEqual(update.after_axis[key], update.before_axis[key]);
      assert.equal(update.after_axis.nominal_under_head_length_mm, 190.5);
      assert.equal(update.after_axis.nut_side_spacer_mm, 25.4);
      for (const key of ['selected_bolt_grade', 'selected_nut_SKU', 'selected_washer_SKU', 'selected_drive', 'selected_diameter_mm'])
        assert.deepEqual(update.after_selection[key], update.before_selection[key]);
      assert.equal(update.after_selection.minimum_body_mm, 144.272);
      assert.equal(update.after_selection.maximum_grip_gaging_mm, 158.75);
      assert.equal(update.after_selection.minimum_body_to_nominated_target_margin_mm > 8, true);
    }
    for (const row of parameters.stack_checks) {
      assert.equal(row.nominal.all_nominal_reference_margins_positive, true);
      assert.equal(row.USS_minimum_thickness.all_nominal_reference_margins_positive, true);
      assert.equal(row.delivered_dimensions_observed, false);assert.equal(row.complete_joint_qualified, false);
      assert.equal(row.rejected_shorter_options.find(r => r.product === '8094').wood_and_steel_body_margin_mm < 0, true);
    }
    const scene = validateSingleSpacers(JSON.parse(bound(index.geometry.scene)), index.geometry.receipt.sha256);
    assert.deepEqual(scene.parent_scene, index.preceding_revision.geometry.scene);
    assert.deepEqual(scene.parent_layout, index.preceding_revision.geometry.receipt);
    for (const row of scene.part_transforms) {
      const own = parameters.part_transforms.find(r => r.name === row.name);
      for (const key of Object.keys(row)) assert.deepEqual(row[key], own[key]);
    }
    assert.deepEqual(scene.removals, parameters.removed_parts.map(r => r.id));
    assert.deepEqual(scene.stack_updates, parameters.axis_updates.map(u => u.after_selection));
    const html = read('site/index.html').toString();
    for (const value of [path.basename(index.geometry.scene.path), index.geometry.scene.sha256,
      index.geometry.receipt.sha256, index.preserved_owner_v8_viewer]) assert.ok(html.includes(value), 'single-spacer viewer binding missing');
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    const currentReference = index.engineering_review ? JSON.parse(bound(index.engineering_review)) : null;
    const currentMethods = currentReference?.schema === 'eoere_current_conventional_reference_review/v1' &&
      Boolean(currentReference.source_bindings?.timber_cores && currentReference.source_bindings?.timber_vector);
    return {...prior, revision: report.revision, spacer_pieces: 16, occupied_parts: 1021, simplified_cleat_stacks: 8,
      testing_method_correction_applied: currentMethods,
      testing_method_correction_scope: 'current own-field core and vector references; no historical force pass',
      current_response_revision: (index.response_bank || index.engineering_review) ? report.revision : null};
  }
  if (index.schema === 'bolted_frame_development_revisions/v13') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_inward_angles_revision/v1');
    assert.equal(report.revision, 'eoere-inward-bolts-and-angles-v8');
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    for (const row of [index.geometry, index.hardware_model, index.shop]) assert.equal(row.revision, report.revision);
    assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
    assert.deepEqual(index.shop.geometry, index.geometry.receipt);
    assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.equal(index.conditional_frame_evaluation, null);
    for (const key of ['engineering_review', 'testing_review', 'bolt_geometry_review', 'panel_bracing_review']) if (index[key]) {
      const review = JSON.parse(bound(index[key]));
      assert.equal(review.geometry_revision, report.revision, 'matching cumulative geometry required');
      assert.deepEqual(review.physical_geometry, index.geometry.receipt);
      if (key === 'bolt_geometry_review') validateCurrentBoltGeometryReview(review, index);
    }
    if (index.response_bank) validateOwnResponseBank(JSON.parse(bound(index.response_bank)), index);
    for (const row of [index, report]) {
      assert.equal(row.fabrication_released, false);assert.equal(row.climbing_released, false);
      assert.equal(row.panel_Hillman_resolution_deferred, true);
    }
    for (const flag of ['current_response_computed', 'historical_capacity_transferred', 'complete_conditional_frame_evaluation'])
      assert.equal(report[flag], false);
    for (const flag of ['nominal_geometry_clear', 'inward_bolt_directions_preserved',
      'stock_outlines_and_66_screws_preserved', 'hardware_lengths_and_counts_preserved']) assert.equal(report[flag], true);
    assert.equal(report.retained_inward_exterior_stacks, 40);
    assert.equal(report.moved_angles, 8);assert.equal(report.moved_axes, 24);
    assert.equal(report.changed_receivers, 13);assert.equal(report.changed_parts, 173);
    assert.deepEqual(report.translation_xyz_mm, [0, 6, 0]);assert.equal(report.actual_observations, null);
    bound(report.producer);
    for (const binding of Object.values(report.files)) bound(binding);
    const previous = JSON.parse(bound(index.preceding_revision.geometry.receipt));
    assert.deepEqual(report.counts, previous.counts);
    const changes = JSON.parse(bound(report.files['changes.json']));
    assert.deepEqual(changes.parent_geometry, previous.checked_geometry);
    assert.equal(changes.prior_force_results_transferred, false);
    assert.equal(changes.fresh_stock_only_not_a_physical_repair_instruction, true);
    assert.equal(changes.panel_and_kicker_screws_changed, false);assert.equal(changes.member_outlines_changed, false);
    const updates = JSON.parse(bound(report.files['axis-updates.json']));
    assert.equal(updates.axes.length, 24);assert.equal(updates.fitting_poses.length, 8);
    assert.equal(updates.inward_bolt_directions_preserved, true);assert.equal(updates.screw_axes_changed, false);
    const v6 = JSON.parse(bound(index.preceding_revision.preceding_revision.geometry.receipt));
    const additions = JSON.parse(bound(v6.files['axes-additions.json']));
    const axes = new Map([...JSON.parse(bound(additions.parent_axes)).axes, ...additions.axes].map(a => [a.id, a]));
    const orientation = JSON.parse(bound(previous.files['orientation.json']));
    for (const {after} of orientation.axis_updates) axes.set(after.id, after);
    for (const after of updates.axes) {
      const before = axes.get(after.id);
      assert.deepEqual(after.point_xyz_mm, before.point_xyz_mm.map((p, i) => p+(i === 1 ? 6 : 0)));
      for (const key of Object.keys(before).filter(k => !['point_xyz_mm', 'attachments'].includes(k)))
        assert.deepEqual(after[key], before[key], 'inward orientation and hardware must remain: '+after.id+' '+key);
      assert.equal(after.attachments.length, before.attachments.length);
      for (let i = 0; i < after.attachments.length; i++) {
        assert.deepEqual(after.attachments[i].point, before.attachments[i].point.map((p, j) => p+(j === 1 ? 6 : 0)));
        const a = {...after.attachments[i]}, b = {...before.attachments[i]};delete a.point;delete b.point;
        assert.deepEqual(a, b);
      }
    }
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = validateInwardAngles(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.deepEqual(scene.parent_scene, index.preceding_revision.geometry.scene);
    assert.deepEqual(scene.parent_layout, index.preceding_revision.geometry.receipt);
    assert.deepEqual(scene.replacements.map(r => r.name).sort(), [...changes.affected_wood_receivers].sort());
    const html = read('site/index.html').toString();
    for (const value of [path.basename(index.geometry.scene.path), index.geometry.scene.sha256,
      index.geometry.scene.decoded_sha256, index.geometry.receipt.sha256, index.preserved_owner_v7_viewer])
      assert.ok(html.includes(value), 'cumulative geometry viewer binding missing');
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    return {...prior, revision: report.revision, retained_inward_exterior_stacks: 40,
      inset_angles: 8, translated_shared_axes: 24,
      current_response_revision: index.engineering_review ? report.revision : null};
  }
  if (index.schema === 'bolted_frame_development_revisions/v12') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_inward_bolts_revision/v1');
    assert.equal(report.revision, 'eoere-inward-exterior-bolts-v7');
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    for (const row of [index.geometry, index.hardware_model, index.shop]) assert.equal(row.revision, report.revision);
    assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
    assert.deepEqual(index.shop.geometry, index.geometry.receipt);
    assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.equal(index.conditional_frame_evaluation, null);
    for (const key of ['engineering_review', 'testing_review', 'bolt_geometry_review'])
      assert.equal(index[key], undefined, 'reversed hardware cannot inherit a preceding review');
    assert.equal(index.hardware_model.selected_for_build, false);
    assert.equal(index.shop.instructions_current_for_fabrication, false);
    for (const row of [index, report]) {
      assert.equal(row.fabrication_released, false); assert.equal(row.climbing_released, false);
      assert.equal(row.panel_Hillman_resolution_deferred, true);
    }
    for (const key of ['current_response_computed', 'historical_capacity_transferred',
      'complete_conditional_frame_evaluation', 'thread_windows_washer_seats_and_tool_access_requalified'])
      assert.equal(report[key], false, 'orientation change is nominal geometry only');
    for (const key of ['nominal_geometry_clear', 'holes_members_panels_and_screws_unchanged',
      'bolt_lengths_grades_and_spacer_counts_unchanged']) assert.equal(report[key], true);
    assert.equal(report.actual_observations, null);
    assert.equal(report.reversed_stacks, 40); assert.equal(report.side_stacks, 32);
    assert.equal(report.top_stacks, 8); assert.equal(report.changed_hardware_parts, 224);
    bound(report.producer);
    const previous = JSON.parse(bound(index.preceding_revision.geometry.receipt));
    assert.deepEqual(report.counts, previous.counts);
    const orientation = JSON.parse(bound(report.files['orientation.json']));
    assert.deepEqual(orientation.parent, previous.checked_geometry);
    const additions = JSON.parse(bound(previous.files['axes-additions.json']));
    const old = JSON.parse(bound(additions.parent_axes));
    const axes = new Map([...old.axes, ...additions.axes].map(a => [a.id, a]));
    assert.equal(axes.size, 96); assert.equal(orientation.axis_updates.length, 40);
    for (const {before, after} of orientation.axis_updates) {
      assert.deepEqual(before, axes.get(before.id));
      assert.equal(after.id, before.id);
      assert.deepEqual(after.direction_xyz, before.direction_xyz.map(n => -n));
      assert.deepEqual(after.point_xyz_mm, before.point_xyz_mm.map((p, i) => p+before.grip_mm*before.direction_xyz[i]));
      assert.equal(after.before_plate_mm, before.after_plate_mm);
      assert.equal(after.after_plate_mm, before.before_plate_mm);
      for (const key of ['attachments', 'receivers', 'grip_mm', 'diameter_mm', 'bore_diameter_mm',
        'nominal_under_head_length_mm', 'hardware_scenario']) assert.deepEqual(after[key], before[key]);
      assert.equal(after.nut_faces, 'interior'); assert.equal(after.head_faces, 'exterior');
    }
    const scene = validateInwardBolts(JSON.parse(bound(index.geometry.scene)), index.geometry.receipt.sha256);
    assert.deepEqual(scene.parent_scene, index.preceding_revision.geometry.scene);
    assert.deepEqual(scene.parent_layout, index.preceding_revision.geometry.receipt);
    assert.equal(orientation.transforms.length, 40);
    assert.equal(orientation.replacement_part_ids.length, 224);
    for (const row of orientation.transforms) {
      const transform = scene.transforms.find(r => r.axis_id === row.axis_id);
      assert.ok(transform);
      for (const key of Object.keys(transform)) assert.deepEqual(transform[key], row[key]);
      const head = row.after_centers_xyz_mm.head, nut = row.after_centers_xyz_mm.nut;
      if (row.exterior_face === 'top') assert.ok(nut[1] < head[1] && nut[2] < head[2]);
      else assert.ok(Math.abs(nut[0]) < Math.abs(head[0]));
    }
    const html = read('site/index.html').toString();
    for (const value of [path.basename(index.geometry.scene.path), index.geometry.scene.sha256,
      index.geometry.receipt.sha256, index.preserved_owner_v6_viewer]) assert.ok(html.includes(value), 'inward-bolt viewer binding missing');
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    return {...prior, revision: report.revision, exterior_stacks_reversed: 40,
      current_response_revision: null, testing_method_correction_applied: false,
      previous_testing_method_correction_preserved: true, geometry_clear: true};
  }
  if (index.schema === 'bolted_frame_development_revisions/v11') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_principal_pair_revision/v1');
    assert.equal(report.revision, 'eoere-flat-cleats-principal-upper-pairs-v6');
    for (const value of [index.geometry.revision, index.hardware_model.revision, index.shop.revision])
      assert.equal(value, report.revision);
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
    assert.deepEqual(index.shop.geometry, index.geometry.receipt);
    assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.equal(index.conditional_frame_evaluation, null);
    if (index.engineering_review)
      validateCurrent96Review(JSON.parse(bound(index.engineering_review)), index);
    assert.ok(index.bolt_geometry_review, 'current96 bolt rule correction must remain incorporated');
    validateBoltGeometryReview(JSON.parse(bound(index.bolt_geometry_review)), index);
    assert.ok(index.testing_review, 'current96 method findings must remain incorporated');
    validateCurrent96TestingReview(JSON.parse(bound(index.testing_review)), index);
    assert.equal(index.hardware_model.selected_for_build, false);
    assert.equal(index.shop.instructions_current_for_fabrication, false);
    for (const record of [index, report]) {
      assert.equal(record.fabrication_released, false);
      assert.equal(record.climbing_released, false);
      assert.equal(record.panel_Hillman_resolution_deferred, true);
    }
    for (const key of ['current_response_computed', 'old_force_pass_transferred',
      'upper_pair_eligible', 'complete_conditional_frame_evaluation']) assert.equal(report[key], false);
    assert.equal(report.nominal_geometry_clear, true); assert.equal(report.actual_observations, null);
    assert.deepEqual(report.counts, {sawn_members: 20, plywood_cleats: 4, panels: 6,
      angles: 24, bolt_stacks: 96, nuts: 96, washers: 192, spacer_pieces: 32,
      Hillman_axes: 66, receiver_occurrences: 120, occupied_parts: 1037});
    bound(report.producer);
    for (const binding of Object.values(report.files)) bound(binding);
    const previous = JSON.parse(bound(index.preceding_revision.geometry.receipt));
    const additions = JSON.parse(bound(report.files['axes-additions.json']));
    assert.deepEqual(additions.parent_axes, previous.files['axes.json']);
    assert.equal(additions.screw_axes_changed, false); assert.equal(additions.fitting_poses_changed, false);
    const old = JSON.parse(bound(additions.parent_axes));
    assert.equal(old.axes.length+additions.axes.length, 96);
    assert.deepEqual(additions.axes.map(a => a.id), ['eoere_bolt_068', 'eoere_bolt_069']);
    for (const [i, retained] of ['eoere_bolt_072', 'eoere_bolt_073'].entries()) {
      const a = additions.axes[i], b = old.axes.find(a => a.id === retained);
      assert.deepEqual(a.point_xyz_mm, b.point_xyz_mm.map((n, j) => n-(j === 1 ? 50.8 : 0)));
      assert.deepEqual(a.receivers, b.receivers);
    }
    const updated = JSON.parse(bound(report.files['member-updates.json']));
    const profiles = JSON.parse(bound(previous.files['current_profiles.json']));
    assert.deepEqual(Object.keys(updated).sort(), ['base_principal_center_left', 'base_principal_center_right']);
    for (const [name, p] of Object.entries(updated))
      assert.deepEqual({...p, finished: profiles[name].finished}, profiles[name]);
    const revision = report.principal_pair_revision;
    assert.equal(revision.cleat_height_changed, false);
    assert.equal(revision.extend_toward_bolt_039_only_after_failed_calculation, true);
    assert.equal(revision.complete_upper_pair_eligibility_established, false);
    assert.equal(revision.flat_cleat_proofs.length, 4);
    for (const proof of revision.flat_cleat_proofs) {
      assert.equal(proof.outline_edges_per_face, 4); assert.equal(proof.straight_edges_only, true);
      assert.equal(proof.bolt_holes_per_leaf, 4);
      assert.deepEqual(proof.finished, profiles[proof.member].finished);
    }
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = validatePrincipalPairs(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.deepEqual(scene.parent_scene, index.preceding_revision.geometry.scene);
    assert.deepEqual(scene.flat_cleat_outline_yz_mm, previous.reference_cleat_revision.outline_yz_mm);
    assert.deepEqual(scene.replacements.map(r => r.name).sort(), revision.replacement_part_ids);
    const html = read('site/index.html').toString();
    for (const value of [path.basename(index.geometry.scene.path), index.geometry.scene.sha256,
      index.geometry.scene.decoded_sha256, index.geometry.receipt.sha256, index.preserved_owner_v5_viewer])
      assert.ok(html.includes(value), 'principal-pair viewer binding missing');
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    return {passed: prior.passed, revision: report.revision, bolt_axes: 96, angles: 24,
      screw_axes: 66, flat_cleat_sides: true, geometry_clear: true,
      current_response_revision: index.engineering_review ? report.revision : null,
      testing_method_correction_applied: true,
      bolt_rule_applicability_corrected: true, complete_bolt_geometry_resolved: false,
      complete_conditional_frame_evaluation: false};
  }
  if (index.schema === 'bolted_frame_development_revisions/v10') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_reference_cleat_revision/v1');
    assert.equal(report.revision, 'eoere-reference-cleat-upper-pair-v5');
    for (const value of [index.geometry.revision, index.hardware_model.revision, index.shop.revision])
      assert.equal(value, report.revision);
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    assert.deepEqual(index.shop.geometry, index.geometry.receipt);
    assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
    assert.equal(index.conditional_frame_evaluation, null);
    assert.equal(index.engineering_review, undefined, 'changed geometry cannot inherit the preceding strength review');
    assert.equal(index.hardware_model.selected_for_build, false);
    assert.equal(index.shop.instructions_current_for_fabrication, false);
    for (const record of [index, report]) {
      assert.equal(record.panel_Hillman_resolution_deferred, true);
      assert.equal(record.fabrication_released, false);
      assert.equal(record.climbing_released, false);
    }
    for (const key of ['old_force_pass_transferred', 'current_response_computed',
      'complete_conditional_frame_evaluation', 'upper_pair_eligible']) assert.equal(report[key], false);
    assert.equal(report.nominal_geometry_clear, true);
    assert.equal(report.actual_observations, null);
    assert.deepEqual(report.counts, {sawn_members: 20, plywood_cleats: 4, panels: 6,
      angles: 24, bolt_stacks: 94, nuts: 94, washers: 188, spacer_pieces: 32,
      Hillman_axes: 66, receiver_occurrences: 118, occupied_parts: 1027});
    bound(report.producer);
    for (const binding of Object.values(report.files)) bound(binding);
    const reference = JSON.parse(bound(report.reference_cleat_revision.outline_source));
    assert.deepEqual(report.reference_cleat_revision.outline_yz_mm, reference.new_cleat_YZ_polygon_mm);
    assert.equal(report.reference_cleat_revision.leaf_thickness_mm, 19.05);
    const previous = JSON.parse(bound(index.preceding_revision.geometry.receipt));
    const axes = JSON.parse(bound(report.files['axes.json']));
    const old = JSON.parse(bound(previous.files['axes.json']));
    assert.deepEqual(axes.screw_axes, old.screw_axes);
    assert.deepEqual(axes.fitting_poses, old.fitting_poses);
    assert.equal(axes.axes.length, 94);
    for (const axis of old.axes) assert.deepEqual(axes.axes.find(a => a.id === axis.id), axis);
    for (const [side, added, retained] of [['left', 'eoere_bolt_067', 'eoere_bolt_071'],
      ['right', 'eoere_bolt_070', 'eoere_bolt_074']]) {
      const a = axes.axes.find(a => a.id === added), b = axes.axes.find(a => a.id === retained);
      assert.ok(a && b, 'two upper pins per corner required');
      assert.deepEqual(a.point_xyz_mm, b.point_xyz_mm.map((v, i) => v-(i === 1 ? 50.8 : 0)));
      assert.deepEqual(a.receivers, b.receivers);
      for (const suffix of ['', '_outer'])
        assert.equal(axes.axes.filter(a => a.receivers.includes('eoere_cleat_'+side+suffix)).length, 4);
    }
    const profiles = JSON.parse(bound(report.files['current_profiles.json']));
    const oldProfiles = JSON.parse(bound(previous.files['current_profiles.json']));
    for (const [name, profile] of Object.entries(profiles)) {
      if (!/^(eoere_cleat_|base_side_)/.test(name)) assert.deepEqual(profile, oldProfiles[name]);
      if (name.startsWith('eoere_cleat_')) {
        assert.equal(profile.blank_mm[2], 19.05);
        const outline = [...new Set(profile.vertices_luv_mm.map(([l, , v]) =>
          JSON.stringify([Number((v+profile.datum_xyz_mm[1]).toFixed(6)), Number((l+profile.datum_xyz_mm[2]).toFixed(6))])))].sort();
        assert.deepEqual(outline, report.reference_cleat_revision.outline_yz_mm
          .map(p => JSON.stringify(p.map(v => Number(v.toFixed(6))))).sort());
      }
    }
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = validateReferenceCleats(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.deepEqual(scene.parent_scene, index.preceding_revision.geometry.scene);
    assert.deepEqual(scene.replacements.map(r => r.name).sort(), report.reference_cleat_revision.replacement_part_ids);
    const html = read('site/index.html').toString();
    for (const value of [path.basename(index.geometry.scene.path), index.geometry.scene.sha256,
      index.geometry.scene.decoded_sha256, index.geometry.receipt.sha256, index.preserved_owner_v4_viewer])
      assert.ok(html.includes(value), 'reference cleat viewer binding missing');
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    return {passed: prior.passed, revision: report.revision, bolt_axes: 94, angles: 24,
      screw_axes: 66, geometry_clear: true, current_response_revision: null,
      upper_pair_eligible: false, complete_conditional_frame_evaluation: false};
  }
  if (index.schema === 'bolted_frame_development_revisions/v9') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_owner_local_bolt_revision/v1');
    assert.equal(report.revision, 'eoere-local-front-bolt-moves-v4');
    for (const value of [index.geometry.revision, index.hardware_model.revision, index.shop.revision])
      assert.equal(value, report.revision);
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
    assert.equal(index.conditional_frame_evaluation, null);
    assert.equal(index.hardware_model.selected_for_build, false);
    assert.equal(index.shop.instructions_current_for_fabrication, false);
    for (const record of [index, report]) {
      assert.equal(record.panel_Hillman_resolution_deferred, true);
      assert.equal(record.fabrication_released, false);
      assert.equal(record.climbing_released, false);
    }
    assert.equal(report.old_force_pass_transferred, false);
    assert.equal(report.complete_conditional_frame_evaluation, false);
    assert.equal(report.nominal_geometry_clear, true);
    assert.equal(report.cleat_move_adopted, false);
    assert.equal(report.upper_support_diameter_increased, false);
    assert.equal(report.actual_observations, null);
    bound(report.producer);
    for (const binding of Object.values(report.files)) bound(binding);
    const parent = JSON.parse(bound(index.preceding_revision.geometry.receipt));
    assert.deepEqual(report.counts, parent.counts);
    const axes = JSON.parse(bound(report.files['axes.json']));
    const old = JSON.parse(bound(parent.files['axes.json']));
    assert.deepEqual(axes.screw_axes, old.screw_axes);
    assert.deepEqual(axes.fitting_poses, old.fitting_poses);
    assert.equal(axes.axes.length, 92);
    const moved = new Set(['rail_front_bolt_left_1', 'rail_front_bolt_right_1']);
    assert.deepEqual(report.local_bolt_moves.axes.map(a => a.axis_id).sort(), [...moved].sort());
    for (const axis of axes.axes) {
      const previous = old.axes.find(a => a.id === axis.id);
      if (moved.has(axis.id)) {
        assert.equal(previous.point_xyz_mm[2], 50);
        assert.deepEqual(axis, {...previous, point_xyz_mm: previous.point_xyz_mm.map((n, i) => n+(i === 2 ? 10 : 0))});
      } else assert.deepEqual(axis, previous);
    }
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = validateOwnerFrame(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.deepEqual(scene.parent_scene, index.preceding_revision.geometry.scene);
    assert.deepEqual(scene.replacements.map(r => r.name).sort(), report.local_bolt_moves.replacement_part_ids);
    const review = JSON.parse(bound(index.engineering_review));
    assert.equal(review.schema, 'eoere_owner_local_bolt_move_review/v1');
    assert.equal(review.revision, report.revision);
    assert.deepEqual(review.geometry, index.geometry.receipt);
    for (const key of ['conditional_frame_evaluation_complete', 'structural_acceptance',
      'fabrication_released', 'climbing_released', 'native_executable_solve_performed']) assert.equal(review[key], false);
    assert.equal(review.panel_Hillman_resolution_deferred, true);
    assert.equal(review.panel_Hillman_strength_pass, false);
    assert.equal(review.actual_observations, null);
    assert.deepEqual(Object.keys(review.scenarios), ['four_hosts']);
    const scenario = review.scenarios.four_hosts;
    assert.equal(scenario.case_count, 6);
    assert.deepEqual(scenario.cases.map(c => c.case_id).sort(), ['a1-rear', 'a12-forward', 'a12-left', 'a12-rear', 'k12-rear', 'k12-right']);
    assert.ok(scenario.cases.every(c => c.residual_N < 1e-5 && c.all_credited_hosts_in_compression));
    for (const [name, wall] of [['nominal38p1_rows', 38.1], ['minimum36p5_rows', 36.5]]) {
      const rows = scenario[name];
      assert.equal(rows.credited_combined_wall_mm, wall);
      assert.equal(rows.case_count, 6);
      assert.equal(rows.maximum_row_reference_index, Math.max(...rows.cases.map(c => c.row_reference_index)));
      assert.ok(rows.cases.every(c => c.scalar_pressure_lower_bound <= c.row_reference_index+1e-10));
    }
    const html = read('site/index.html').toString();
    assert.equal(viewerModel(html, scene.key), scene.key);
    assert.equal(viewerModel(html, index.preserved_owner_v3_viewer), index.preserved_owner_v3_viewer);
    for (const value of [index.geometry.scene.sha256, index.geometry.scene.decoded_sha256, index.geometry.receipt.sha256])
      assert.ok(html.includes(value), 'local-move viewer binding missing');
    if (entryChecks) for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'])
      validateEntry(read(name).toString(), index);
    return {...prior, revision: report.revision, geometry_integrated: true};
  }
  if (index.schema === 'bolted_frame_development_revisions/v8') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_owner_requested_frame_revision/v1');
    for (const value of [index.geometry.revision, index.hardware_model.revision, index.shop.revision])
      assert.equal(value, report.revision);
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    assert.equal(index.conditional_frame_evaluation, null);
    assert.equal(report.complete_conditional_frame_evaluation, false);
    assert.equal(report.old_force_pass_transferred, false);
    assert.equal(index.hardware_model.selected_for_build, false);
    assert.equal(index.shop.instructions_current_for_fabrication, false);
    for (const record of [index, report]) {
      assert.equal(record.panel_Hillman_resolution_deferred, true);
      assert.equal(record.fabrication_released, false);
      assert.equal(record.climbing_released, false);
    }
    assert.deepEqual(report.counts, {sawn_members: 20, plywood_cleats: 4, panels: 6,
      angles: 24, bolt_stacks: 92, nuts: 92, washers: 184, spacer_pieces: 26,
      Hillman_axes: 66, receiver_occurrences: 112, occupied_parts: 1011});
    for (const binding of Object.values(report.files)) bound(binding);
    bound(report.producer); bound(report.geometry_producer);
    const sizing = JSON.parse(bound(index.engineering_sizing));
    assert.equal(sizing.schema, 'eoere_requested_three_quarter_cleat_sizing/v1');
    assert.deepEqual(sizing.geometry, report.checked_geometry);
    assert.equal(sizing.complete_conditional_frame_evaluation, false);
    assert.equal(sizing.fabrication_released, false); assert.equal(sizing.climbing_released, false);
    bound(sizing.producer);
    assert.equal(sizing.cases.length, 3);
    for (const row of sizing.cases) {
      assert.ok(row.gradient_inf_N < 1e-5);
      assert.equal(row.groups.length, 28);
      for (const group of row.groups) {
        const a = 2*Math.abs(group.signed_weighted_first_moment_mm)/group.whole_wall_mm;
        const minimum = a+Math.hypot(a, group.integrated_force_only_reference_index);
        assert.ok(Math.abs(minimum-group.minimum_scalar_pressure_reference_index) < 1e-12);
        assert.ok(group.balanced_pressure_reference_index+1e-12 >= minimum);
      }
    }
    const lamination = JSON.parse(bound(index.lamination_study));
    assert.equal(lamination.schema, 'eoere_owner_laminated_cleat_fixed_action_summary/v1');
    assert.deepEqual(lamination.geometry, report.checked_geometry);
    assert.equal(lamination.case_count, 5); assert.equal(lamination.cases.length, 5);
    assert.equal(lamination.global_perfect_bond_stiffness_recomputed, false);
    assert.equal(lamination.K12_right_original_floor_case_admitted, false);
    assert.equal(lamination.adhesive_or_complete_cleat_qualified, false);
    assert.equal(lamination.release, false);
    assert.ok(lamination.maximum_nominal_reference_index > 0.92 && lamination.maximum_nominal_reference_index < 0.94);
    assert.ok(lamination.maximum_minimum36p5_wall_fixed_action_sensitivity_index > 0.97 &&
      lamination.maximum_minimum36p5_wall_fixed_action_sensitivity_index < 0.99);
    assert.ok(lamination.cases.every(c => c.governing_group.axis_ids.length > 0 &&
      c.governing_bores.every(b => Math.abs(b.combined_wall_mm-38.1) < 1e-6 &&
        b.maximum_force_reconstruction_error_N < 1e-6 && b.maximum_moment_reconstruction_error_Nmm < 1e-4)));
    const review = JSON.parse(bound(index.engineering_review));
    assert.equal(review.schema, 'eoere_owner_current_engineering_review/v1');
    assert.equal(review.revision, report.revision);
    assert.deepEqual(review.geometry, index.geometry.receipt);
    assert.equal(review.lamination_question_evaluation_complete, true);
    assert.equal(review.conditional_frame_evaluation_complete, false);
    assert.equal(review.structural_acceptance, false);
    assert.equal(review.fabrication_released, false);
    assert.equal(review.climbing_released, false);
    assert.equal(review.panel_Hillman_resolution_deferred, true);
    assert.equal(review.panel_Hillman_strength_pass, false);
    assert.equal(review.actual_observations, null);
    assert.equal(review.native_executable_solve_performed, false);
    assert.deepEqual(review.counts, {physical_sawn_members: 20, physical_plywood_leaves: 4,
      analytical_laminates: 2, angles: 24, bolt_stacks: 92, Hillman_axes: 66, normal_floor_laws: 32});
    assert.deepEqual(Object.keys(review.scenarios).sort(), ['four_hosts', 'two_long_supports']);
    const caseIds = ['a1-rear', 'a12-forward', 'a12-left', 'a12-rear', 'k12-rear', 'k12-right'];
    for (const scenario of Object.values(review.scenarios)) {
      assert.equal(scenario.case_count, 6);
      assert.deepEqual(scenario.cases.map(c => c.case_id).sort(), caseIds);
      assert.ok(scenario.cases.every(c => c.residual_N < 1e-5 && c.all_credited_hosts_in_compression));
      assert.equal(scenario.all82_mandatory_geometry_eligible, true);
      for (const [name, wall] of [['nominal38p1_rows', 38.1], ['minimum36p5_rows', 36.5]]) {
        const rows = scenario[name];
        assert.equal(rows.credited_combined_wall_mm, wall);
        assert.equal(rows.case_count, 6);
        assert.deepEqual(rows.cases.map(c => c.case_id).sort(), caseIds);
        assert.equal(rows.maximum_row_reference_index, Math.max(...rows.cases.map(c => c.row_reference_index)));
        assert.ok(rows.maximum_row_reference_index > 1);
        assert.ok(rows.maximum_scalar_pressure_lower_bound > 1);
        assert.ok(rows.cases.every(c => c.scalar_pressure_lower_bound <= c.row_reference_index+1e-10));
        for (const row of rows.cases) {
          assert.deepEqual(row.field, scenario.cases.find(c => c.case_id === row.case_id).field);
          assert.ok(row.axes.length > 0 && row.force_and_first_moment_at_governing_bores.length === row.axes.length);
        }
      }
      for (const maximum of [...Object.values(scenario.shaft82_maxima), ...Object.values(scenario.timber20_maxima)]) {
        assert.ok(Number.isFinite(maximum.value) && maximum.value >= 0);
        assert.deepEqual(maximum.field, scenario.cases.find(c => c.case_id === maximum.case_id).field);
      }
    }
    const shop = JSON.parse(bound(index.shop.current_review));
    assert.equal(shop.schema, 'eoere_owner_frame_shop_review/v1');
    assert.deepEqual(shop.geometry, report.checked_geometry);
    assert.deepEqual(shop.counts, {members: 30, sawn: 20, leaves: 4, angles: 24, bolts: 92,
      nuts: 92, washers: 184, spacers: 26, receivers: 112, drawings: 24, sticks: 13, nominal_board_feet: 150});
    assert.equal(shop.coordinate_and_drilling_reconciliation_pass, true);
    assert.equal(shop.observation_cells_blank, true);
    assert.equal(shop.retained_exceedance_is_a_strength_pass, false);
    assert.equal(shop.fabrication_release, false); assert.equal(shop.climbing_release, false);
    for (const binding of Object.values(shop.files)) bound(binding);
    const axes = JSON.parse(bound(report.files['axes.json']));
    assert.equal(axes.axes.length, 92); assert.equal(axes.fitting_poses.length, 24);
    assert.ok(!axes.axes.some(a => a.id.startsWith('outboard_')));
    const parent = JSON.parse(bound(index.preceding_revision.geometry.receipt));
    assert.deepEqual(axes.screw_axes, JSON.parse(bound(parent.files['axes.json'])).screw_axes);
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = validateOwnerFrame(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.equal(scene.key, index.geometry.viewer);
    assert.deepEqual(scene.removals, report.owner_requested_revision.removed_part_ids);
    assert.deepEqual(scene.replacements.map(r => r.name).sort(), report.owner_requested_revision.replacement_part_ids);
    const html = read('site/index.html').toString();
    assert.equal(viewerModel(html, scene.key), scene.key);
    for (const value of [index.geometry.scene.sha256, index.geometry.scene.decoded_sha256, index.geometry.receipt.sha256])
      assert.ok(html.includes(value), 'owner-frame viewer binding missing');
    if (entryChecks) {
      for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md']) validateEntry(read(name).toString(), index);
      assert.ok(html.includes(`href="?model=${scene.key}&view=rear">Current eoere geometry`));
    }
    return {passed: prior.passed, revision: report.revision, bolt_axes: 92, angles: 24,
      screw_axes: 66, conditional_frame_evaluation_complete: false, geometry_integrated: true};
  }
  if (['bolted_frame_development_revisions/v6', 'bolted_frame_development_revisions/v7'].includes(index.schema)) {
    const retained = index.schema === 'bolted_frame_development_revisions/v7';
    const boltCount = retained ? 102 : 106;
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, retained ? 'eoere_retained_2x6_frame_revision/v1' : 'eoere_paired_frame_revision/v1');
    assert.equal(report.revision, retained ? 'eoere-paired-frame-retained-2x6-A574-v2' : 'eoere-paired-cleats-upper-leg-up15-v1');
    for (const value of [index.geometry.revision, index.hardware_model.revision, index.shop.revision])
      assert.equal(value, report.revision);
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.deepEqual(index.shop.geometry, index.geometry.receipt);
    assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    assert.equal(index.shop.shop_planning_only, true);
    assert.equal(index.hardware_model.actual_parts_verified, false);
    assert.equal(index.hardware_model.analysis_pass_transferred, false);
    assert.equal(report.development_model_integrated, true);
    assert.equal(report.old_force_pass_transferred, false);
    assert.equal(report.actual_observations, null);
    for (const record of [index, report]) {
      assert.equal(record.panel_Hillman_resolution_deferred, true);
      assert.equal(record.fabrication_released, false);
      assert.equal(record.climbing_released, false);
    }
    assert.deepEqual(report.counts, {sawn_members: 24, plywood_cleats: 4, panels: 6,
      angles: 26, bolt_stacks: boltCount, nuts: boltCount, washers: 2*boltCount, spacer_pieces: retained ? 34 : 36,
      Hillman_axes: 66, receiver_occurrences: retained ? 130 : 134, occupied_parts: retained ? 1075 : 1097});
    for (const binding of Object.values(report.files)) bound(binding);
    for (const name of ['scripts/publish_eoere_paired_frame.py', 'scripts/eoere_paired_frame_basis.py',
      ...(retained ? ['scripts/publish_eoere_retained_frame.py'] : [])])
      bound({path: name, sha256: report.source_sha256[name]});
    const axes = JSON.parse(bound(report.files['axes.json']));
    assert.equal(axes.axes.length, boltCount); assert.equal(new Set(axes.axes.map(a => a.id)).size, boltCount);
    assert.equal(axes.fitting_poses.length, 26); assert.equal(axes.screw_axes.length, 66);
    const parent = JSON.parse(bound(index.preceding_revision.geometry.receipt));
    const parentAxes = retained ? JSON.parse(bound(parent.files['axes.json'])) : parent;
    assert.deepEqual(axes.screw_axes, parentAxes.screw_axes);
    const ports = [];
    for (const axis of axes.axes) for (const attachment of axis.attachments) {
      const delta = attachment.point.map((v, i) => v-axis.point_xyz_mm[i]);
      const along = delta.reduce((s, v, i) => s+v*axis.direction_xyz[i], 0);
      assert.ok(Math.hypot(...delta.map((v, i) => v-along*axis.direction_xyz[i])) < 1e-6);
      assert.ok(Math.min(Math.abs(along), Math.abs(along-axis.grip_mm)) < 1e-6);
      assert.equal(attachment.installed_bolt_axis_id, axis.id);
      ports.push(`${attachment.angle_id}/${attachment.flange}/${attachment.transverse}`);
    }
    assert.equal(ports.length, retained ? 98 : 102); assert.equal(new Set(ports).size, retained ? 98 : 102);
    assert.equal(report.upper_leg_edge_correction.corrections.length, 2);
    for (const row of report.upper_leg_edge_correction.corrections)
      assert.deepEqual(row.after_xyz_mm.map((v, i) => v-row.before_xyz_mm[i]), [0, 0, 15]);
    const precedingCleat = JSON.parse(bound(report.source_cleat_evaluation));
    assert.equal(precedingCleat.complete_conditional_engineering_evaluation, true);
    assert.equal(precedingCleat.fabrication_or_drilling_or_climbing_release, false);
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = (retained ? validateRetainedFrame : validatePairedFrame)(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.equal(scene.key, index.geometry.viewer);
    assert.deepEqual(scene.replacements.map(r => r.name).sort(), retained ? report.viewer_delta_part_ids : report.changed_finished_solids.map(r => r.id).sort());
    if (retained) {
      assert.deepEqual(scene.removals, report.viewer_removed_part_ids);
      assert.deepEqual(scene.parent_scene, index.preceding_revision.geometry.scene);
      assert.deepEqual(scene.parent_layout, index.preceding_revision.geometry.receipt);
      for (const omitted of ['eoere_bolt_068', 'eoere_bolt_069', 'outboard_angle_left_eoere_bolt_006', 'outboard_angle_right_eoere_bolt_009'])
        assert.ok(!axes.axes.some(a => a.id === omitted));
    }
    const html = read('site/index.html').toString();
    assert.equal(viewerModel(html, scene.key), scene.key);
    for (const value of [index.geometry.scene.sha256, index.geometry.scene.decoded_sha256, index.geometry.receipt.sha256])
      assert.ok(html.includes(value), 'paired-frame viewer binding missing');
    if (entryChecks) {
      for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md']) validateEntry(read(name).toString(), index);
      assert.ok(html.includes(`href="?model=${scene.key}&view=rear">Current eoere geometry`));
    }
    let engineeringComplete = false;
    if (index.conditional_frame_evaluation) {
      const evaluation = JSON.parse(bound(index.conditional_frame_evaluation));
      assert.equal(evaluation.schema, 'eoere_paired_frame_engineering_evaluation/v1');
      assert.deepEqual(evaluation.geometry, index.geometry.receipt);
      assert.equal(evaluation.complete_conditional_frame_evaluation, true);
      assert.deepEqual(evaluation.remaining_required_frame_duties, []);
      assert.equal(evaluation.panel_Hillman_resolution_deferred, true);
      assert.equal(evaluation.fabrication_or_climbing_release, false);
      assert.ok(Object.values(evaluation.maximum_reference_indices).every(v => Number.isFinite(v) && v <= 1));
      engineeringComplete = true;
    }
    return {passed: prior.passed, revision: report.revision, bolt_axes: boltCount, bolts: boltCount,
      screw_axes: 66, angles: 26, enclosed_passages: 32, mechanics_executed: false,
      full_ignored_input_closure_checked: false, preserved_predecessor_revision: prior.revision,
      geometry_integrated: true, conditional_frame_evaluation_complete: engineeringComplete,
      panel_Hillman_resolution_deferred: true};
  }
  if (index.schema === 'bolted_frame_development_revisions/v5') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_leg_header_revision/v3');
    assert.equal(report.revision, index.geometry.revision);
    assert.equal(report.status, 'NOMINAL_GEOMETRY_CLEAR_STRENGTH_UNQUALIFIED');
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.deepEqual(report.counts, {sawn_members: 20, plywood_cleats: 2, panels: 6, angles: 24,
      bolt_stacks: 96, Hillman_axes: 66, receiver_occurrences: 112, occupied_parts: 1027, spacer_pieces: 24});
    assert.equal(report.axes.length, 96); assert.equal(new Set(report.axes.map(r => r.id)).size, 96);
    assert.equal(report.screw_axes.length, 66); assert.equal(report.fitting_poses.length, 24);
    assert.equal(report.post_row_Z_mm, 173.8125);
    assert.equal(report.removed_axes.length, 4);
    assert.ok(report.removed_axes.every(id => !report.axes.some(a => a.id === id)));
    const ports = [];
    for (const axis of report.axes) for (const a of axis.attachments) {
      const d = axis.direction_xyz, delta = a.point.map((v, i) => v-axis.point_xyz_mm[i]);
      const along = delta.reduce((s, v, i) => s+v*d[i], 0);
      const radial = Math.hypot(...delta.map((v, i) => v-along*d[i]));
      assert.ok(radial < 1e-6 && Math.min(Math.abs(along), Math.abs(along-axis.grip_mm)) < 1e-6,
        'fitting attachment must lie on its physical shaft at a stack face');
      assert.equal(a.installed_bolt_axis_id, axis.id);
      ports.push(`${a.angle_id}/${a.flange}/${a.transverse}`);
    }
    assert.equal(ports.length, 96); assert.equal(new Set(ports).size, 96);
    for (const ref of Object.values(report.files)) bound(ref);
    bound(report.inputs);
    bound({path: 'scripts/publish_eoere_leg_header.py', sha256: report.source_sha256['scripts/publish_eoere_leg_header.py']});
    for (const key of ['physical_installation_qualified', 'complete_joint_qualified', 'native_FEA_performed'])
      assert.equal(report[key], false);
    assert.equal(report.actual_observations, null); assert.ok(Object.values(report.release).every(v => v === false));
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = validateLegHeader(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.equal(scene.key, index.geometry.viewer);
    assert.deepEqual(scene.replacements.map(r => r.name).sort(), report.changed_finished_solids.map(r => r.id).sort());
    assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.deepEqual(index.hardware_model.receipt, index.geometry.receipt);
    assert.equal(index.hardware_model.revision, report.revision);
    for (const key of ['current_response', 'structural_assessment', 'engineering_assessment']) assert.equal(index[key], null);
    assert.equal(index.fabrication_released, false); assert.equal(index.climbing_released, false);
    assert.equal(index.optional_grid.applies_to_current_geometry, false);
    const responseStudy = JSON.parse(bound(index.conditional_response_study.result));
    assert.equal(responseStudy.revision, report.revision);
    assert.deepEqual(responseStudy.geometry, report.checked_geometry);
    assert.equal(responseStudy.all_six_raw_operator_and_force_replays_pass, true);
    assert.equal(responseStudy.all96_attachment_axes_checked, true);
    assert.equal(responseStudy.production_admission_issued, false);
    assert.equal(responseStudy.physical_demand_bound_established, false);
    assert.equal(responseStudy.structural_acceptance, false);
    assert.equal(responseStudy.cases.length, 6);
    assert.equal(new Set(responseStudy.cases.map(r => r.case_id)).size, 6);
    assert.equal(responseStudy.component_comparisons, 48);
    assert.equal(responseStudy.cases.flatMap(r => r.connection_shear_references).length, 48);
    assert.equal(responseStudy.component_reference_exceedances.length, 1);
    assert.equal(responseStudy.maximum_full_gradient_residual_N,
      Math.max(...responseStudy.cases.map(r => r.gradient_inf_N)));
    assert.ok(responseStudy.maximum_full_gradient_residual_N <= 1e-5);
    for (const row of responseStudy.cases) {
      assert.equal(row.counts.physical_bodies, 148); assert.equal(row.counts.shaft, 96);
      assert.equal(row.counts.fitting, 24); assert.equal(row.counts.end_captures, 192);
      assert.equal(row.equilibrium.all_body_and_global_checks_pass, true);
      assert.equal(row.connection_shear_references.length, 8);
    }
    const singlePins = JSON.parse(bound(index.conditional_response_study.single_pin_bolt_references));
    assert.equal(singlePins.revision, report.revision);
    assert.deepEqual(singlePins.geometry, report.checked_geometry);
    assert.equal(singlePins.comparison_count, 24); assert.equal(singlePins.rows.length, 24);
    assert.equal(singlePins.reference_exceedances.length, 0);
    assert.equal(singlePins.generic_45000_reference_exceedances.length, 4);
    assert.ok(singlePins.maximum_catalog_thread_fraction <= .25);
    for (const row of singlePins.rows) {
      const axis = report.axes.find(a => a.id === row.axis_id);
      assert.equal(row.nominal_diameter_mm, axis.diameter_mm);
      assert.equal(row.catalog_minimum_body_in, axis.diameter_mm === 9.525 ? .369 : .493);
      assert.equal(row.material_scenario_Fyb_psi, 92000);
      assert.equal(row.complete_joint_qualified, false);
    }
    const superseded = index.conditional_response_study.superseded_single_pin_bolt_references;
    bound(superseded);
    assert.equal(singlePins.superseded_report.path, superseded.path);
    assert.equal(singlePins.superseded_report.sha256, superseded.sha256);
    assert.equal(singlePins.structural_acceptance, false);
    const plywood = JSON.parse(bound(index.conditional_response_study.plywood_component_references));
    assert.equal(plywood.geometry_revision, report.revision);
    assert.equal(plywood.geometry.sha256, report.checked_geometry.sha256);
    assert.equal(plywood.disposition, 'REVISE_SINGLE_LEAF_REFERENCE_CONSTRUCTION');
    assert.ok(plywood.governing_checked_section.reference_upper > 1);
    assert.equal(plywood.complete_joint_qualified, false); assert.equal(plywood.release, false);
    assert.equal(plywood.paired_leaf_sizing_proposal.sharing_qualified, false);
    const pilots = JSON.parse(bound(index.unadopted_studies.paired_leaf_two_width_pilots));
    assert.equal(pilots.current_published_geometry_unchanged, true);
    assert.equal(pilots.current_published_revision, report.revision);
    assert.equal(pilots.variants.length, 2);
    assert.equal(pilots.geometry_adopted, false); assert.equal(pilots.structural_acceptance, false);
    for (const variant of pilots.variants) {
      assert.equal(variant.case, 'a12-left'); assert.equal(variant.leaves.length, 4);
      assert.equal(variant.counts.physical_bodies, 150);
      assert.ok(variant.gradient_inf_N <= 1e-5 && variant.maximum_section_reference_upper > 1);
      assert.equal(variant.geometry_adopted, false); assert.equal(variant.complete_joint_qualified, false);
    }
    const combined = JSON.parse(bound(index.unadopted_studies.coherent_bilateral_return_paired_cleats_signed_foot));
    assert.equal(combined.current_published_revision, report.revision);
    assert.equal(combined.current_published_geometry_unchanged, true);
    assert.equal(combined.geometry_adopted, false); assert.equal(combined.structural_acceptance, false);
    assert.equal(combined.complete_joint_qualified, false); assert.equal(combined.fabrication_or_climbing_release, false);
    assert.equal(combined.cases.length, 6); assert.equal(new Set(combined.cases.map(r => r.case)).size, 6);
    assert.equal(combined.named_leg_post_component_count, 48);
    assert.equal(combined.named_leg_post_exceedances.length, 0);
    assert.equal(combined.census.bolts, 108); assert.equal(combined.census.factory_angles, 26);
    assert.equal(combined.census.factory_12p7mm_spacer_pieces, 40); assert.equal(combined.census.Hillman_screws, 66);
    assert.equal(combined.maximum_plywood_leaf_section_reference,
      Math.max(...combined.cases.map(r => r.leaf_section_reference_upper)));
    assert.ok(combined.maximum_gradient_inf_N <= 1e-5 && combined.maximum_plywood_leaf_section_reference < 1);
    for (const row of combined.cases) {
      assert.equal(row.counts.physical_bodies, 168); assert.equal(row.counts.shaft, 108);
      assert.equal(row.counts.fitting, 26); assert.equal(row.leaf_maxima.length, 4);
      assert.equal(row.leg_post_references.length, 8);
      assert.ok(row.leg_post_references.every(r => r.reference_index_CD1 < 1));
      assert.equal(row.structural_acceptance, false);
    }
    const followup = JSON.parse(bound(index.unadopted_studies.coherent_return_component_followup));
    assert.deepEqual(followup.geometry, combined.geometry);
    assert.equal(followup.geometry_revision, combined.revision);
    assert.equal(followup.counts.hole_case_references, 192);
    assert.equal(followup.counts.cleat_physical_shaft_case_rows, 48);
    assert.equal(followup.cases.length, 6);
    for (const row of followup.cases) {
      assert.deepEqual(row.field, combined.cases.find(r => r.case === row.case).field);
    }
    assert.ok(followup.summary.hole_traction_max < 1);
    assert.ok(Object.values(followup.summary.cleat_component_maxima).every(value => value < 1));
    assert.equal(followup.complete_hole_strength_qualified, false);
    assert.equal(followup.complete_joint_qualified, false);
    assert.equal(followup.geometry_adopted, false); assert.equal(followup.release, false);
    const singleCleat = JSON.parse(bound(index.unadopted_studies.coherent_single_cleat_pin_pilot));
    assert.equal(singleCleat.current_published_revision, report.revision);
    assert.equal(singleCleat.current_published_geometry_unchanged, true);
    assert.equal(singleCleat.case, 'a12-forward');
    assert.equal(singleCleat.counts.physical_bodies, 164);
    assert.equal(singleCleat.counts.shaft, 104); assert.equal(singleCleat.counts.fitting, 26);
    assert.equal(singleCleat.counts.timber, 28); assert.equal(singleCleat.Hillman_screws, 66);
    assert.equal(singleCleat.actual_bolt_ports, 100); assert.equal(singleCleat.physical_flange_contact_strips, 104);
    assert.equal(singleCleat.unused_factory_holes_have_no_shaft_bearing_or_capture, true);
    assert.equal(singleCleat.raw_operator_and_force_replay_pass, true);
    assert.ok(singleCleat.gradient_inf_N < 1e-5);
    assert.equal(singleCleat.leaf_maxima.length, 4);
    assert.ok(singleCleat.maximum_leaf_section_reference < 1);
    assert.equal(singleCleat.leg_post_references.length, 8);
    assert.equal(singleCleat.exceeded_component_comparisons.length, 1);
    assert.equal(singleCleat.exceeded_component_comparisons[0].duty, 'post_cleat');
    assert.equal(singleCleat.exceeded_component_comparisons[0].member, 'base_post_outer_left');
    assert.ok(singleCleat.exceeded_component_comparisons[0].reference_index_CD1 > 1);
    assert.equal(singleCleat.leaf_seat_and_moment_returns.length, 4);
    assert.ok(singleCleat.leaf_seat_and_moment_returns.every(r => r.runner_compression_N > 0 && r.bolt_axial_torque_about_world_X_Nmm === 0));
    assert.equal(singleCleat.more_cases_admitted, false);
    assert.equal(singleCleat.geometry_adopted, false); assert.equal(singleCleat.structural_acceptance, false);
    assert.equal(singleCleat.complete_joint_qualified, false); assert.equal(singleCleat.fabrication_or_climbing_release, false);
    const threePin = JSON.parse(bound(index.unadopted_studies.coherent_three_pin_two_pilots));
    assert.equal(threePin.current_published_revision, report.revision);
    assert.equal(threePin.current_published_geometry_unchanged, true);
    assert.deepEqual(threePin.cases.map(r => r.case), ['a12-forward', 'a12-left']);
    assert.equal(threePin.census.bolts, 106); assert.equal(threePin.census.factory_angles, 26);
    assert.equal(threePin.census.Hillman_screws, 66); assert.equal(threePin.census.actual_bolt_ports, 102);
    assert.equal(threePin.named_leg_post_comparison_count, 16);
    assert.equal(threePin.named_leg_post_reference_exceedances.length, 0);
    assert.ok(threePin.maximum_leaf_section_reference < 1 && threePin.maximum_signed_foot_reference < 1);
    assert.equal(threePin.provisional_Grade8_lower_joint_construction.axis, 'cleat_post_bolt_left_2');
    assert.ok(threePin.provisional_Grade8_lower_joint_construction.reference_index > 1);
    for (const row of threePin.cases) {
      assert.equal(row.counts.physical_bodies, 166);
      assert.ok(row.gradient_inf_N < 1e-5 && row.contact_classification_changes > 0);
      assert.ok(row.maximum_timber_translation_mm > 80);
      assert.equal(row.finite_response_or_physical_error_bound, false);
    }
    assert.equal(threePin.all_six_cases_admitted, false); assert.equal(threePin.other_four_cases_held, true);
    assert.equal(threePin.geometry_adopted, false); assert.equal(threePin.complete_joint_qualified, false);
    assert.equal(threePin.structural_acceptance, false); assert.equal(threePin.fabrication_or_climbing_release, false);
    const cornerFloor = JSON.parse(bound(index.unadopted_studies.coherent_three_pin_corner_floor_pilot));
    assert.equal(cornerFloor.current_published_revision, report.revision);
    assert.equal(cornerFloor.current_published_geometry_unchanged, true);
    assert.deepEqual(cornerFloor.geometry, threePin.geometry);
    assert.equal(cornerFloor.case, 'a12-forward');
    assert.deepEqual(cornerFloor.census, {bolts: 106, factory_angles: 26, Hillman_screws: 66, physical_owners: 166});
    assert.equal(cornerFloor.counts.floor_normals, 32); assert.equal(cornerFloor.counts.floor_xy_components, 64);
    assert.equal(cornerFloor.unchanged_K_RHS_internal_contacts_and_normal_laws, true);
    assert.equal(cornerFloor.bearing_corners + cornerFloor.released_corner_XY_pairs, 32);
    assert.equal(cornerFloor.force_tamper_controls_rejected, true);
    assert.ok(cornerFloor.gradient_inf_N < 1e-5);
    assert.ok(cornerFloor.maximum_bearing_point_tangential_motion_mm < .02);
    assert.ok(cornerFloor.maximum_timber_node_translation_mm > 75);
    assert.ok(cornerFloor.finite_arm_contact_classification_changes > 0);
    for (const key of ['other_five_cases_held', 'other_four_centroid_only_cases_held']) assert.equal(cornerFloor[key], true);
    for (const key of ['finite_motion_response_or_physical_error_bound', 'new_motion_limit_adopted',
      'floor_friction_capacity_or_anchor_established', 'physical_floor_test_required', 'complete_joint_qualified',
      'geometry_adopted', 'structural_acceptance', 'native_FEA_performed', 'fabrication_or_climbing_release'])
      assert.equal(cornerFloor[key], false);
    const html = read('site/index.html').toString();
    assert.equal(viewerModel(html, scene.key), scene.key);
    for (const value of [index.geometry.scene.sha256, index.geometry.scene.decoded_sha256, index.geometry.receipt.sha256])
      assert.ok(html.includes(value), 'combined leg/header viewer binding missing');
    if (entryChecks) {
      for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md']) validateEntry(read(name).toString(), index);
      assert.ok(html.includes(`href="?model=${scene.key}&view=rear">Current eoere geometry`));
    }
    return {...prior, revision: report.revision, bolt_axes: 96, bolts: 96, angles: 24,
      new_response_computed: true, production_admission_issued: false,
      current_leg_foot_shear_reference: responseStudy.worst_leg_foot.conservative_reference_index_CD1,
      current_post_shear_reference: responseStudy.worst_front_post.conservative_reference_index_CD1};
  }
  if (index.schema === 'bolted_frame_development_revisions/v4') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_enclosed_passages_revision/v1');
    assert.equal(report.status, 'NOMINAL_GEOMETRY_CLEAR');
    assert.equal(report.revision, index.geometry.revision);
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry);
    assert.equal(report.bolt_axis_lines_preserved, 100); assert.equal(report.Hillman_axes_preserved, 66);
    assert.equal(report.passages.length, 32); assert.equal(report.new_front_open_notches, 0);
    assert.equal(new Set(report.passages.map(r => r.service)).size, 32);
    for (const row of report.passages) {
      assert.equal(row.diameter_mm, 38.1); assert.ok(Math.abs(row.board_normal_centre_mm-69.85) < 1e-6);
      assert.ok(Math.abs(row.front_rear_ligament_mm-50.8) < 1e-6);
      assert.ok(row.nominal_budget_remaining_mm > 0); assert.equal(row.Actual, ''); assert.equal(row.Disposition, '');
      assert.equal(row.grain_offset_mm, row.service === 'wire_072_F1_G1' ? 40 : 0);
    }
    for (const key of ['physical_feed_verified', 'hole_strength_qualified', 'new_response_computed', 'historical_capacity_transferred'])
      assert.equal(report[key], false);
    assert.ok(Object.values(report.release).every(v => v === false));
    for (const name of ['scripts/publish_eoere_enclosed_passages.py', report.shop_override.path,
      index.preceding_revision.geometry.receipt.path]) bound({path: name, sha256: report.source_sha256[name]});
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = validateEnclosedPassages(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.equal(scene.key, index.geometry.viewer);
    assert.deepEqual(scene.replacements.map(r => r.name).sort(), report.changed_finished_solids.map(r => r.id).sort());
    assert.deepEqual(index.shop.result, index.geometry.receipt);
    assert.deepEqual(index.shop.overrides, [report.shop_override]); bound(index.shop.passage_profile);
    for (const key of ['current_response', 'structural_assessment', 'engineering_assessment']) assert.equal(index[key], null);
    assert.equal(index.fabrication_released, false); assert.equal(index.climbing_released, false);
    assert.equal(index.optional_grid.applies_to_current_geometry, false);
    const registry = JSON.parse(bound(index.geometry_registry_check));
    assert.equal(registry.schema, 'eoere_enclosed_registry_check/v1');
    assert.equal(registry.passed, true); assert.deepEqual(registry.geometry_receipt, index.geometry.receipt);
    assert.equal(registry.geometry_changed, false); assert.equal(registry.registry_parts_checked, 1033);
    assert.equal(registry.corrected_panel_screw_bodies, 4);
    assert.equal(registry.positive_affected_screw_backing_count, 28);
    assert.ok(registry.minimum_old_backed_volume_mm3 > 0);
    assert.equal(registry.recorded_nut_translations_included, 8);
    assert.equal(registry.corrected_frame_part_pairs, 240);
    assert.deepEqual(registry.registry_bounds_mismatches, []);
    const html = read('site/index.html').toString();
    assert.equal(viewerModel(html, scene.key), scene.key);
    for (const value of [index.geometry.scene.sha256, index.geometry.scene.decoded_sha256, index.geometry.receipt.sha256])
      assert.ok(html.includes(value), 'enclosed-passage viewer binding missing');
    if (entryChecks) {
      for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md']) validateEntry(read(name).toString(), index);
      assert.ok(html.includes(`href="?model=${scene.key}&view=rear">Current eoere geometry`));
    }
    return {...prior, revision: report.revision, enclosed_passages: 32, new_response_computed: false};
  }
  if (index.schema === 'bolted_frame_development_revisions/v3') {
    const prior = checkDevelopment(index.preceding_revision, {entryChecks: false});
    const report = JSON.parse(bound(index.geometry.receipt));
    assert.equal(report.schema, 'eoere_narrow_channels_geometry/v1');
    assert.equal(report.revision, index.geometry.revision);
    assert.deepEqual(report.parent_geometry, index.preceding_revision.geometry.receipt);
    assert.deepEqual(index.hardware_model, index.preceding_revision.hardware_model);
    assert.deepEqual(index.selected_baseline, index.preceding_revision.selected_baseline);
    assert.equal(report.channel_count, 32); assert.equal(report.profile.front_width_mm, 14);
    assert.equal(report.profile.rear_depth_mm, 14.35); assert.equal(report.central_notch_location_holds, 6);
    assert.equal(report.unchanged_bolt_axis_lines, 100); assert.equal(report.unchanged_screw_axes, 66);
    assert.equal(report.service_routes_changed, false); assert.equal(report.new_response_computed, false);
    assert.equal(report.analysis_pass_transferred, false);
    assert.equal(report.reconstruction_proofs.length, 8);
    assert.equal(report.reconstruction_proofs.reduce((n, r) => n+r.channels, 0), 32);
    assert.ok(report.reconstruction_proofs.every(r => r.old_reconstruction_difference_mm3 < .01 && r.restored_volume_mm3 > 0));
    assert.equal(Object.keys(report.profile_overrides).length, 8); assert.equal(report.changed_finished_solids.length, 16);
    for (const [variant, total] of [['base', 1033], ['extra', 1428]]) {
      const c = report.clearance[variant]; assert.equal(c.parts, total); assert.equal(c.all_clear, true);
      assert.equal(c.added_material_pair_comparisons, 8*(total-1));
      assert.ok(c.exact_queries.length > 0 && c.exact_queries.every(r => r.intersection_mm3 < 1e-6));
    }
    bound({path: 'scripts/eoere_narrow_channels.py', sha256: report.source_sha256['scripts/eoere_narrow_channels.py']});
    const decoded = gunzipSync(bound(index.geometry.scene));
    assert.equal(sha(decoded), index.geometry.scene.decoded_sha256);
    const scene = validateNarrowChannels(JSON.parse(decoded), index.geometry.receipt.sha256);
    assert.equal(index.geometry.viewer, scene.keys.base); assert.equal(index.optional_grid.viewer, scene.keys.extra);
    assert.equal(index.optional_grid.default_enabled, false); assert.equal(index.optional_grid.official, false);
    assert.deepEqual(index.shop.result, index.geometry.receipt); assert.equal(index.shop.revision, report.revision);
    assert.equal(index.shop.overrides.length, 1); bound(index.shop.overrides[0]); bound(index.shop.channel_profile);
    assert.equal(index.shop.overrides[0].sha256, report.shop_override.sha256);
    for (const k of ['current_response', 'structural_assessment', 'engineering_assessment']) assert.equal(index[k], null);
    for (const k of ['fabrication_released', 'climbing_released']) assert.equal(index[k], false);
    assert.ok(Object.values(report.release).every(v => v === false));
    const html = read('site/index.html').toString();
    for (const model of Object.values(scene.keys)) assert.equal(viewerModel(html, model), model);
    for (const [key, expected] of Object.entries({url: path.basename(index.geometry.scene.path),
      expectedSha256: index.geometry.scene.sha256, decodedSha256: index.geometry.scene.decoded_sha256,
      layoutSha256: index.geometry.receipt.sha256})) {
      const expression = html.match(new RegExp(key + ': (frontPosts \\? [^\\n]+),?'))?.[1]?.replace(/,$/, '');
      assert.ok(expression, `current viewer ${key} binding missing`);
      assert.equal(runInNewContext(`(${expression})`, {frontPosts: false, narrowChannels: true}, {timeout: 1000}), expected);
    }
    if (entryChecks) {
      for (const name of ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md']) validateEntry(read(name).toString(), index);
      assert.ok(html.includes(`href="?model=${index.geometry.viewer}&view=rear">Current eoere geometry`));
    }
    return {...prior, revision: report.revision, narrowed_channels: 32, new_response_computed: false};
  }
  if (index.schema === 'bolted_frame_development_revisions/v2') return checkFrontPostRevision(index, entryChecks);
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
  assert.ok(index.current_response, 'current response missing');
  validateCurrentResponse(JSON.parse(bound(index.current_response.cases)), index);
  validateCurrentComponents(JSON.parse(bound(index.current_response.components)), index);
  assert.ok(index.engineering_assessment, 'current engineering assessment missing');
  validateEngineeringAssessment(JSON.parse(bound(index.engineering_assessment)), index);
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
  if (entryChecks) assert.ok(html.includes(`href="?model=${index.geometry.viewer}&view=rear">Current eoere geometry`));
  for (const [key, expected] of Object.entries({url: path.basename(hardwareModel.scene.path),
    expectedSha256: hardwareModel.scene.sha256, decodedSha256: hardwareModel.scene.decoded_sha256,
    layoutSha256: hardwareModel.receipt.sha256})) {
    const expression = html.match(new RegExp(`\\b${key}: ((?:frontPosts|selectedHardware) \\? .+),\\r?\\n`))?.[1];
    assert.ok(expression, `viewer ${key} binding missing`);
    assert.equal(runInNewContext(`(${expression})`, {frontPosts: false, narrowChannels: false, selectedHardware: true}, {timeout: 1000}), expected);
  }
  const entries = ['README.md', 'docs/README.md', 'docs/bolted-frame-development/README.md'];
  if (entryChecks) for (const name of entries) validateEntry(read(name).toString(), index);
  assert.ok(read(entries[2]).toString().trimEnd().split('\n').length <= 150,
    'keep the development entry within 150 lines; link details from the ledger');
  return {passed: true, revision: geometry.revision, shop_revision: shop.revision, response_revision: index.response.revision,
    current_response_revision: index.current_response.revision, current_response_hardware: index.current_response.hardware_revision,
    bolt_axes: geometry.axes.length, screw_axes: geometry.screw_axes.length,
    full_ignored_input_closure_checked: false, mechanics_executed: false};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url))
  console.log(JSON.stringify(checkDevelopment()));
