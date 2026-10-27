import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {gzipSync, gunzipSync} from 'node:zlib';
import {ROOT, readIndex, checkDevelopment, validateShorterRearMaterialReferences, validateShorterRearProjectedBearingWitness,
  validateShorterJointCriterionFollowthrough, validateV11BuildPackage, validateV11BracketThicknessConfirmation,
  validateShorterFormedAngleReference, validateShorterNearWasherSeat, validateShorterWasherMinimumThickness,
  validateMatchingRearAffectedComponents, validateShorterContactSensitivity,
  validateNominalDiameterBearingCorrection, validateGlobalWasherMinimum, validateCleatInterleafDemand,
  validateTopGeometryReview, validateFarRowFittingExtension, validateCurrentShorterJointDisposition} from '../scripts/check_bolted_development.mjs';

function packet() {
  const index = readIndex(), entry = index.owner_authorized_shorter_bolt_trial;
  return {index, entry, bank: JSON.parse(readFileSync(path.join(ROOT, entry.response_bank.path))),
    rear: JSON.parse(readFileSync(path.join(ROOT, entry.rear_wrench_material_references.path)))};
}

test('rear wrench references preserve the24 states and separate chosen Fe/5 flags from conditional metal scenarios', () => {
  const {entry, bank, rear} = packet();
  assert.equal(validateShorterRearMaterialReferences(rear, entry, bank), rear);
  assert.equal(rear.original_reference_summary.Fe_over_5_states_above_one, 8);
  assert.equal(rear.original_reference_summary.Grade5_92ksi_Fyb_scenario_exceedances, 0);
  assert.equal(rear.separate_hinge_reference_summary.Grade5_92ksi_scenario_exceedance_count, 0);
  assert.equal(rear.accepted_connection_exceedance_count, null);
});

for (const [name, mutate] of [
  ['foreign bank', (r, i) => {r.response_bank = i.response_bank;}],
  ['stale joint disposition', r => {r.joint_disposition.sha256 = '0'.repeat(64);}],
  ['missing rear state', r => {r.case_rows.pop();}],
  ['duplicate state preserves count', r => {r.case_rows[0].case_id = r.case_rows[1].case_id; r.case_rows[0].axis_id = r.case_rows[1].axis_id;}],
  ['chosen-field flags erased', r => {r.original_reference_summary.Fe_over_5_states_above_one = 0;}],
  ['physical failure count inferred', r => {r.accepted_connection_exceedance_count = 8;}],
  ['physical failure claim inferred', r => {r.original_reference_summary.physical_failure_claim = true;}],
  ['separate hinge sensitivity replaces original', r => {r.case_rows[0].preserved_Fyb_over_5.required_Fyb_MPa *= 2;}],
  ['source correction removed', r => {r.source_boolean_label_note = '';}],
  ['actual capacity invented', r => {r.complete_joint_capacity = 1000;}],
  ['drilling release inherited', r => {r.drilling_released = true;}],
]) test(`rear wrench delivery rejects ${name}`, () => {
  const {index, entry, bank, rear} = packet(); mutate(rear, index);
  assert.throws(() => validateShorterRearMaterialReferences(rear, entry, bank));
});

test('V20 hash-checks the optional rear record and permits the preserved trial without that supplement', () => {
  const {index, entry} = packet(); entry.rear_wrench_material_references.sha256 = '0'.repeat(64);
  assert.throws(() => checkDevelopment(index, {entryChecks: false}));
  delete entry.rear_wrench_material_references; delete entry.build_package; delete entry.rear_projected_bearing_witness; delete entry.joint_criterion_followthrough;
  const result = checkDevelopment(index, {entryChecks: false});
  assert.equal(result.owner_authorized_shorter_bolt_trial.reported_reference_rows, 110);
  assert.equal(result.complete_connection_acceptance, null); assert.equal(result.structural_acceptance, false);
});

const buildFolder = 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/build-package/';
const rearFolder = 'runner-leg-jigs/prototype-v3-verified/';
const digest = bytes => createHash('sha256').update(bytes).digest('hex');

function buildPacket() {
  const {entry, bank} = packet(), files = new Map();
  const manifest = {schema: 'v11_provisional_build_package/v1', revision: entry.revision, metadata: {
    geometry_receipt: structuredClone(entry.geometry_receipt), response_bank: structuredClone(entry.response_bank),
    joint_disposition: structuredClone(entry.joint_disposition), rear_wrench_material_references: structuredClone(entry.rear_wrench_material_references),
    counts: {bolts: 112, nuts: 112, washers: 224, metal_spacers: 4, sawn_members: 20, cleat_leaves: 4, panels: 6},
    angle_bodies_required: 24, actual_angle_count: null,
    source_records: {original_packet: {path: 'fea/generated/unavailable-test-original/build-manifest.json', sha256: '1'.repeat(64)}},
    frame_geometry_changed: false, new_global_or_native_solve: false, physical_fit_observed: false, structural_acceptance: false,
    purchase_authorized: false, drilling_released: false, fabrication_released: false, climbing_released: false,
  }, artifacts: [], active_print_files: []};
  const add = (name, content) => {
    const bytes = Buffer.from(content); files.set(buildFolder+name, bytes);
    const artifact = {path: name, sha256: digest(bytes), bytes: bytes.length,
      source: manifest.metadata.source_records.original_packet, use: 'Provisional marking reference only', documentation_links_adapted: false};
    manifest.artifacts.push(artifact); return artifact;
  };
  const left = add(rearFolder+'left-rear-foot-leg-marking-jig.stl', 'left handed fixture bytes');
  const right = add(rearFolder+'right-rear-foot-leg-marking-jig.stl', 'right handed fixture bytes');
  const bracket = add('bracket-jig/prototype-v3-horizontal-bottom-left-1-final/common-beam-fixture.stl', 'bracket fixture bytes');
  manifest.active_print_files = [left.path, right.path, bracket.path];
  const proof = {schema: 'v11_rear_foot_leg_marking_jig_prototype/v3', current_source_bindings: {
    checked_receipt: entry.geometry_receipt, response_bank: entry.response_bank, joint_record: entry.joint_disposition, geometry: bank.physical_geometry,
  }, outputs: {}, side_placement_proofs: {}, qualification: {
    drilling_released: false, fabrication_released: false, climbing_released: false, physical_fit_observed: false, structural_acceptance: false,
  }};
  for (const [side, artifact] of [['left', left], ['right', right]]) {
    const sign = side === 'left' ? -1 : 1;
    proof.outputs[path.basename(artifact.path)] = {sha256: artifact.sha256, bytes: artifact.bytes};
    proof.side_placement_proofs[side] = {axis_id: `rail_rear_bolt_${side}_1`, proper_rigid_transform: true, determinant: 1,
      basis_columns_xyz: [[0, 1, 0], [0, 0, sign], [sign, 0, 0]], cad_mark_local_u_w_z_mm: [2, 3*sign, 0],
      origin_xyz_mm_at_rear_foot_outer_face: [10*sign, 0, 0], mapped_mark_xyz_mm: [10*sign, 2, 3], source_axis_point_xyz_mm: [10*sign, 2, 3]};
  }
  const proofArtifact = add(rearFolder+'prototype-result-v3.json', JSON.stringify(proof));
  const updateProof = () => {
    const bytes = Buffer.from(JSON.stringify(proof)); files.set(buildFolder+proofArtifact.path, bytes);
    proofArtifact.sha256 = digest(bytes); proofArtifact.bytes = bytes.length;
  };
  const validate = () => validateV11BuildPackage(manifest, entry, bank, ref => {
    assert.ok(files.has(ref.path), `missing test artifact: ${ref.path}`); return files.get(ref.path);
  });
  return {entry, bank, manifest, files, proof, updateProof, validate};
}

test('provisional build package verifies all issued bytes and separate proper-handed rear proofs without ignored inputs', () => {
  const fixture = buildPacket(); assert.equal(fixture.validate(), fixture.manifest);
  assert.equal(fixture.manifest.active_print_files.length, 3);
});

for (const [name, mutate] of [
  ['foreign response bank', f => {f.manifest.metadata.response_bank = readIndex().response_bank;}],
  ['stale joint disposition', f => {f.manifest.metadata.joint_disposition.sha256 = '0'.repeat(64);}],
  ['old spacer count', f => {f.manifest.metadata.counts.metal_spacers = 24;}],
  ['physical fit claim', f => {f.manifest.metadata.physical_fit_observed = true;}],
  ['drilling release', f => {f.manifest.metadata.drilling_released = true;}],
  ['invented whole-joint capacity', f => {f.manifest.complete_joint_capacity = 1000;}],
  ['ignored-source closure claim', f => {f.manifest.full_ignored_input_closure_checked = true;}],
  ['artifact traversal', f => {f.manifest.artifacts[0].path = '../left.stl';}],
  ['absolute artifact path', f => {f.manifest.artifacts[0].path = '/tmp/left.stl';}],
  ['missing issued artifact', f => {f.files.delete(buildFolder+f.manifest.artifacts[0].path);}],
  ['stale artifact bytes', f => {f.files.set(buildFolder+f.manifest.artifacts[0].path, Buffer.from('replaced STL'));}],
  ['incorrect declared size', f => {f.manifest.artifacts[0].bytes++;}],
  ['unissued active print', f => {f.manifest.active_print_files[2] = 'old-unlisted.stl';}],
  ['superseded universal rear jig', f => {f.proof.schema = 'v11_rear_foot_leg_marking_jig_prototype/v2'; f.updateProof();}],
  ['improper left transform despite declared positive determinant', f => {f.proof.side_placement_proofs.left.basis_columns_xyz[1][2] *= -1; f.updateProof();}],
  ['wrong current rear target', f => {f.proof.side_placement_proofs.left.source_axis_point_xyz_mm[1]++; f.updateProof();}],
  ['STL inconsistent with current placement proof', f => {f.proof.outputs['left-rear-foot-leg-marking-jig.stl'].sha256 = '0'.repeat(64); f.updateProof();}],
]) test(`provisional build package rejects ${name}`, () => {
  const fixture = buildPacket(); mutate(fixture); assert.throws(fixture.validate);
});

function witnessPacket() {
  const {entry, bank} = packet();
  const axes = ['lumber_leg_bolt_left_1', 'lumber_leg_bolt_right_1', 'rail_rear_bolt_left_1', 'rail_rear_bolt_right_1'];
  const report = entry.rear_projected_bearing_witness ? JSON.parse(readFileSync(path.join(ROOT, entry.rear_projected_bearing_witness.path))) : {
    schema: 'v11_current_rear_projected_bearing_reference/v1', geometry_receipt: structuredClone(entry.geometry_receipt),
    response_bank: structuredClone(entry.response_bank), joint_disposition: structuredClone(entry.joint_disposition),
    rear_wrench_material_references: structuredClone(entry.rear_wrench_material_references),
    case_rows: axes.flatMap(axis_id => bank.case_ids.map(case_id => ({axis_id, case_id}))).map((row, i) =>
      ({...row, certified_reference_index: i === 0 ? 1.2790619680711501 : i < 5 ? 1.1 : 0.8})),
    summary: {state_count: 24, reference_index_above_one_count: 5, maximum_reference_index: 1.2790619680711501},
    accepted_connection_exceedance_count: null, complete_joint_capacity: null, actual_Cg: null, actual_Cdelta: null,
    physical_failure_claim: false, structural_acceptance: false, drilling_released: false, fabrication_released: false, climbing_released: false,
  };
  return {entry, report};
}

test('rear projected bearing witness retains24 named model references without physical acceptance', () => {
  const {entry, report} = witnessPacket(); assert.equal(validateShorterRearProjectedBearingWitness(report, entry), report);
});

for (const [name, mutate] of [
  ['foreign response bank', r => {r.response_bank = readIndex().response_bank;}],
  ['duplicate state preserving count', r => {r.case_rows[0].axis_id = r.case_rows[1].axis_id; r.case_rows[0].case_id = r.case_rows[1].case_id;}],
  ['erased above-one references', r => {r.summary.reference_index_above_one_count = 0;}],
  ['adopted actual group factor', r => {r.actual_Cg = 1;}],
  ['physical failure interpretation', r => {r.physical_failure_claim = true;}],
  ['fabrication release', r => {r.fabrication_released = true;}],
]) test(`rear projected bearing witness rejects ${name}`, () => {
  const {entry, report} = witnessPacket(); mutate(report); assert.throws(() => validateShorterRearProjectedBearingWitness(report, entry));
});

function criterionPacket() {
  const {index, entry, bank} = packet();
  const report = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, entry.joint_criterion_followthrough.path))));
  return {index, entry, bank, report};
}

test('current joint criterion supplement matches the26 base clusters while preserving model-reference and contact limits', () => {
  const {entry, bank, report} = criterionPacket();
  assert.equal(validateShorterJointCriterionFollowthrough(report, entry, bank), report);
  delete entry.joint_disposition;
  assert.equal(validateShorterJointCriterionFollowthrough(report, entry, bank), report);
});

for (const [name, mutate] of [
  ['foreign bank', (r, i) => {r.response_bank = i.response_bank;}],
  ['swapped axes across clusters despite preserved112 unique axes', r => {
    const a = r.joint_clusters[0].axis_ids, b = r.joint_clusters[1].axis_ids; [a[0], b[0]] = [b[0], a[0]];
  }],
  ['missing Appendix E case rows', r => {r.appendix_e.E3.pop();}],
  ['erased continuous-reference flags', r => {r.continuous_rear_bearing.summary.continuous_reference_exceedances = 0;}],
  ['robust-switch construction presented as contact acceptance', r => {r.objective_contact.interpretation_correction.zero_robust_switches_is_not_acceptance_evidence = false;}],
  ['invented complete-joint capacity', r => {r.complete_joint_capacity = 1000;}],
]) test(`joint criterion supplement rejects ${name}`, () => {
  const {index, entry, bank, report} = criterionPacket(); mutate(report, index);
  assert.throws(() => validateShorterJointCriterionFollowthrough(report, entry, bank));
});

test('V20 checks the decoded criterion hash and optional owner-preference bytes', () => {
  const {index, entry} = packet(); entry.joint_criterion_followthrough.decoded_sha256 = '0'.repeat(64);
  assert.throws(() => checkDevelopment(index, {entryChecks: false}));
  const clean = readIndex(); clean.owner_authorized_shorter_bolt_trial.owner_matching_rear_bolts.sha256 = '0'.repeat(64);
  assert.throws(() => checkDevelopment(clean, {entryChecks: false}));
});

function additionsPacket() {
  const {index, entry, bank} = packet(), matching = index.owner_authorized_matching_rear_bolt_trial;
  const load = ref => {const bytes = readFileSync(path.join(ROOT, ref.path)); return JSON.parse(ref.encoding === 'gzip' ? gunzipSync(bytes) : bytes);};
  const reports = {owner: load(index.owner_bracket_thickness_confirmation), formed: load(entry.formed_angle_component_followthrough),
    seat: load(entry.near_washer_seat_followthrough), minimum: load(entry.washer_catalog_minimum_thickness_sensitivity),
    affected: load(matching.affected_connection_component_followthrough)};
  const validators = {owner: report => validateV11BracketThicknessConfirmation(report, index),
    formed: report => validateShorterFormedAngleReference(report, entry, bank), seat: report => validateShorterNearWasherSeat(report, entry, bank),
    minimum: report => validateShorterWasherMinimumThickness(report, entry, bank),
    affected: report => validateMatchingRearAffectedComponents(report, matching, load(matching.response_bank), load(matching.geometry_receipt))};
  return {index, entry, reports, validate: key => validators[key](reports[key])};
}

test('five additive engineering records retain their source identities and explicit unqualified scope', () => {
  const fixture = additionsPacket();
  for (const key of Object.keys(fixture.reports)) assert.equal(fixture.validate(key), fixture.reports[key]);
  delete fixture.entry.near_washer_seat_followthrough; // The independently bound minimum-thickness record remains optional.
  assert.equal(fixture.validate('minimum'), fixture.reports.minimum);
});

for (const [name, key, mutate] of [
  ['owner report relabeled as assistant inspection', 'owner', r => {r.assistant_physical_inspection_performed = true;}],
  ['formed angle bound to the preserved force bank', 'formed', (r, i) => {r.source_bank.sha256 = i.response_bank.sha256;}],
  ['withdrawn native interpretation restored', 'formed', r => {r.correction.old_4mm_withdrawals.pop();}],
  ['elastic angle result promoted to assembly prying acceptance', 'formed', r => {r.remaining_scope.assembly_compatible_prying_or_capture_redistribution_qualified = true;}],
  ['near-seat construction assigned actual steel strength', 'seat', r => {r.strength_threshold_and_limits.actual_angle_Fy_MPa = 235;}],
  ['catalog maximum substituted as minimum', 'minimum', r => {r.catalog_basis.minimum_scenario_mm = 2.6416;}],
  ['duplicate washer state preserving96 rows', 'minimum', r => {r.rows[0].axis_id = r.rows[1].axis_id; r.rows[0].case_id = r.rows[1].case_id;}],
  ['fresh114 component result bound to112 forces', 'affected', (r, i) => {r.response_bank.sha256 = i.owner_authorized_shorter_bolt_trial.response_bank.sha256;}],
  ['three optional foot envelopes erased', 'affected', r => {r.reduced_depth.foot_optional_two_edge_flags = [];}],
  ['interrupted Appendix E paths credited by omission', 'affected', r => {r.AppendixE.material_path_exclusions = [];}],
  ['component references promoted to complete capacity', 'affected', r => {r.complete_joint_capacity = 1000;}],
]) test(`additive engineering delivery rejects ${name}`, () => {
  const fixture = additionsPacket(); mutate(fixture.reports[key], fixture.index); assert.throws(() => fixture.validate(key));
});

const additiveBindings = index => [index.owner_bracket_thickness_confirmation,
  index.owner_authorized_shorter_bolt_trial.formed_angle_component_followthrough,
  index.owner_authorized_shorter_bolt_trial.near_washer_seat_followthrough,
  index.owner_authorized_shorter_bolt_trial.washer_catalog_minimum_thickness_sensitivity,
  index.owner_authorized_matching_rear_bolt_trial.affected_connection_component_followthrough];

test('V20 checks all five encoded pins and both decoded pins', () => {
  for (let n = 0; n < 5; n++) {
    const index = readIndex(); additiveBindings(index)[n].sha256 = '0'.repeat(64);
    assert.throws(() => checkDevelopment(index, {entryChecks: false}));
  }
  for (const n of [3, 4]) {
    const index = readIndex(); additiveBindings(index)[n].decoded_sha256 = '0'.repeat(64);
    assert.throws(() => checkDevelopment(index, {entryChecks: false}));
  }
});

test('V20 preserves current authority when all five additive records are omitted', () => {
  const index = readIndex(), shorter = index.owner_authorized_shorter_bolt_trial;
  delete index.owner_bracket_thickness_confirmation; delete shorter.formed_angle_component_followthrough;
  delete shorter.near_washer_seat_followthrough; delete shorter.washer_catalog_minimum_thickness_sensitivity;
  delete index.owner_authorized_matching_rear_bolt_trial.affected_connection_component_followthrough;
  const result = checkDevelopment(index, {entryChecks: false});
  assert.equal(result.revision, 'v11-v9-eight-bolt-v4'); assert.equal(result.occupied_parts, 1109);
  assert.equal(result.owner_authorized_shorter_bolt_trial.occupied_parts, 1089);
  assert.equal(result.selected_baseline_candidate, 'compact-floor-flush-development'); assert.equal(result.complete_connection_acceptance, null);
});

test('one-case contact sensitivity binds its original bank and retains its outstanding reference', () => {
  const {index, entry, bank} = packet();
  const report = JSON.parse(readFileSync(path.join(ROOT, entry.objective_contact_response_sensitivity.path)));
  assert.equal(validateShorterContactSensitivity(report, entry, bank), report);
  for (const mutate of [r => {r.new_six_case_bank = true;}, r => {r.numerical_admission.residual_gate_n = 1e-3;},
    r => {r.original_response_bank.sha256 = '0'.repeat(64);}, r => {r.complete_joint_capacity = 1;},
    r => {r.rear_summary.continuous_receiver_reference_above_one_count = 0;}]) {
    const changed = structuredClone(report); mutate(changed);
    assert.throws(() => validateShorterContactSensitivity(changed, entry, bank));
  }
  delete index.owner_authorized_shorter_bolt_trial.objective_contact_response_sensitivity;
  assert.equal(checkDevelopment(index, {entryChecks: false}).complete_connection_acceptance, null);
});

test('nominal-D correction preserves the source actions and eight unresolved hinge references', () => {
  const {index, entry} = packet();
  const load = ref => JSON.parse(readFileSync(path.join(ROOT, ref.path)));
  const report = load(entry.nominal_diameter_bearing_followthrough), original = load(entry.joint_disposition);
  assert.equal(validateNominalDiameterBearingCorrection(report, original), report);
  for (const mutate of [r => {r.mixed.corrected_lateral_model_exceedance_states = 0;},
    r => {r.all_sawn_utilizations_nondecreasing = false;}, r => {r.complete_joint_capacity = 1;},
    r => {r.source_bindings.frozen_sources = [];}]) {
    const changed = structuredClone(report); mutate(changed);
    assert.throws(() => validateNominalDiameterBearingCorrection(changed, original));
  }
  delete index.owner_authorized_shorter_bolt_trial.nominal_diameter_bearing_followthrough;
  assert.equal(checkDevelopment(index, {entryChecks: false}).complete_connection_acceptance, null);
});

for (const [key, validate, mutations] of [
  ['global_washer_minimum_thickness', validateGlobalWasherMinimum, [r => {r.scope.near_seat_rows_kept_separate = 0;}, r => {r.summary.strength_or_fit_pass = true;}]],
  ['cleat_interleaf_transfer_demand', validateCleatInterleafDemand, [r => {r.scope.composite_bond_qualified = true;}, r => {r.operator_and_derivation.flow_coefficient_per_mm *= 10;}]],
  ['outer_top_method_and_review_spec', validateTopGeometryReview, [r => {r.review_option_adopted = true;}, r => {r.hole_scope_clarification.new_blanket_actual_metal_hole_violation_asserted = true;}]],
  ['far_row_fitting_component_extension', validateFarRowFittingExtension, [r => {r.per_state_results[0] = r.per_state_results[1];}, r => {r.limits.all144_states_or_all24_fittings_strength_qualified = true;}]],
]) test(`${key} preserves conditional scope and source identity`, () => {
  const {index, entry, bank} = packet(), ref = entry[key], raw = readFileSync(path.join(ROOT, ref.path));
  const report = JSON.parse(ref.encoding === 'gzip' ? gunzipSync(raw) : raw);
  assert.equal(validate(report, entry, bank), report);
  for (const mutate of mutations) {
    const changed = structuredClone(report); mutate(changed); assert.throws(() => validate(changed, entry, bank));
  }
  delete index.owner_authorized_shorter_bolt_trial[key];
  assert.equal(checkDevelopment(index, {entryChecks: false}).complete_connection_acceptance, null);
});

const preservedV2Disposition = {path: 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/current-joint-disposition.json.gz',
  sha256: '138645039a5b96e7a9c73b07be1cb93b1187366830426fe65e2b8bb5b74ab379', encoding: 'gzip', decoded_bytes: 485226,
  decoded_sha256: 'd395a41f3a3531d7ef444e17b2e56e561d51a5511741889e6e588759909ab565'};

function currentDispositionPacket() {
  const {index, entry} = packet(), ref = structuredClone(preservedV2Disposition);
  entry.current_joint_disposition = ref;
  const raw = readFileSync(path.join(ROOT, ref.path)), decoded = gunzipSync(raw);
  assert.equal(digest(raw), ref.sha256); assert.equal(digest(decoded), ref.decoded_sha256); assert.equal(decoded.length, ref.decoded_bytes);
  return {index, entry, report: JSON.parse(decoded)};
}

test('composed V2 resolves all26 current rows while retaining independent physical and engineering holds', () => {
  const {index, entry, report} = currentDispositionPacket();
  assert.equal(validateCurrentShorterJointDisposition(report, entry, index), report);
  assert.equal(report.counts.native_fitting_reference_states, 95); assert.equal(report.counts.native_fitting_geometry_exclusions, 42);
  assert.equal(report.reproduction.recursive_raw_source_closure_claimed, false);
});

for (const [name, mutate] of [
  ['foreign bank', (r, i) => {r.source_bindings.response_bank = i.response_bank;}],
  ['wrong per-joint ownership preserving112 unique axes', r => {
    const a = r.joint_clusters[0].axis_ids, b = r.joint_clusters[1].axis_ids; [a[0], b[0]] = [b[0], a[0]];
  }],
  ['eight mixed hinge states erased', r => {for (const row of r.joint_clusters) delete row.current_retained_flag_evidence.generic45_mixed_hinge_model_states;}],
  ['duplicated hinge pointer preserving the eight-state count', r => {
    const pointers = r.joint_clusters.find(row => row.current_retained_flag_evidence.generic45_mixed_hinge_model_states).current_retained_flag_evidence.generic45_mixed_hinge_model_states[0].pointers;
    pointers[1] = pointers[0];
  }],
  ['completed net components relabeled absent', r => {r.joint_clusters[0].current_duties.member_components.status = 'not_computed';}],
  ['native cases reassigned despite preserved95 total', r => {
    const coverage = r.joint_clusters[0].current_duties.fitting.native_case_coverage;
    const cases = Object.values(coverage)[0].per_state_results; cases[0] = cases[1];
  }],
  ['one fine observation promoted to other states', r => {
    r.joint_clusters.find(row => row.current_duties.fitting?.existing_fine_observation).current_duties.fitting.existing_fine_observation.other_states_fine_envelope_or_convergence_claimed = true;
  }],
  ['nonexistent public evidence pointer', r => {r.joint_clusters[0].current_duties.member_components.evidence[0].pointers.push('/unissued_result');}],
  ['adopted actual group factor', r => {r.actual_Cg = 1;}],
  ['fabrication release', r => {r.fabrication_released = true;}],
  ['recursive raw closure claim', r => {r.reproduction.recursive_raw_source_closure_claimed = true;}],
  ['fifth automatic header opening duty', r => {r.joint_clusters[2].current_duties.header_opening_bridge = r.joint_clusters[0].current_duties.header_opening_bridge;}],
]) test(`current composed disposition rejects ${name}`, () => {
  const {index, entry, report} = currentDispositionPacket(); mutate(report, index);
  assert.throws(() => validateCurrentShorterJointDisposition(report, entry, index));
});

test('current composed book retains encoded, decoded and public dependency hash checks', () => {
  const {index, entry} = packet(); entry.current_joint_disposition.sha256 = '0'.repeat(64);
  assert.throws(() => checkDevelopment(index, {entryChecks: false}));
  const decoded = readIndex(); decoded.owner_authorized_shorter_bolt_trial.current_joint_disposition.decoded_sha256 = '0'.repeat(64);
  assert.throws(() => checkDevelopment(decoded, {entryChecks: false}));
  const fixture = currentDispositionPacket(); fixture.report.source_bindings.native_fitting_scope_extension.sha256 = '0'.repeat(64);
  assert.throws(() => validateCurrentShorterJointDisposition(fixture.report, fixture.entry, fixture.index));
});

test('current entry point composes from embedded public pins when optional addons are omitted', () => {
  const {index, entry} = packet();
  for (const key of ['joint_disposition', 'joint_criterion_followthrough', 'rear_wrench_material_references', 'rear_projected_bearing_witness',
    'formed_angle_component_followthrough', 'near_washer_seat_followthrough', 'washer_catalog_minimum_thickness_sensitivity', 'objective_contact_response_sensitivity',
    'nominal_diameter_bearing_followthrough', 'global_washer_minimum_thickness', 'cleat_interleaf_transfer_demand', 'outer_top_method_and_review_spec',
    'far_row_fitting_component_extension', 'build_package']) delete entry[key];
  delete index.owner_bracket_thickness_confirmation;
  const result = checkDevelopment(index, {entryChecks: false}); assert.equal(result.complete_connection_acceptance, null);
  delete entry.current_joint_disposition;
  assert.equal(checkDevelopment(index, {entryChecks: false}).owner_authorized_shorter_bolt_trial.reported_reference_rows, 110);
});

const currentV3Disposition = {path: 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/current-joint-disposition-v3.json.gz',
  sha256: '3b404463c4ccb484df36f95d57469ed74face7e8c8a94c7c8d47055d5ce2170f', encoding: 'gzip', decoded_bytes: 687391,
  decoded_sha256: '5d8ecddfa45e08e69ac934a835c65613e699fcb5070b1aceb24814e51e35bd9e'};

function currentV3Packet() {
  const {index, entry} = packet(), ref = structuredClone(currentV3Disposition), files = new Map(), reads = [];
  entry.current_joint_disposition = ref;
  const raw = readFileSync(path.join(ROOT, ref.path)), decoded = gunzipSync(raw);
  assert.equal(digest(raw), ref.sha256); assert.equal(digest(decoded), ref.decoded_sha256); assert.equal(decoded.length, ref.decoded_bytes);
  const report = JSON.parse(decoded);
  const readArtifact = binding => {
    assert.ok(binding.path.startsWith('docs/'), 'V3 opens public artifacts only; raw sources are declarations'); reads.push(binding.path);
    return files.get(binding.path) ?? readFileSync(path.join(ROOT, binding.path));
  };
  const rebind = (name, mutate) => {
    const binding = report.source_bindings[name], encoded = readArtifact(binding);
    const record = JSON.parse(binding.encoding === 'gzip' ? gunzipSync(encoded) : encoded); mutate(record);
    const bytes = Buffer.from(JSON.stringify(record)+'\n'), updated = binding.encoding === 'gzip' ? gzipSync(bytes) : bytes;
    binding.sha256 = digest(updated);
    if (binding.encoding === 'gzip') {binding.decoded_sha256 = digest(bytes); binding.decoded_bytes = bytes.length;}
    if (entry[name] !== undefined) entry[name] = structuredClone(binding);
    files.set(binding.path, updated);
  };
  return {index, entry, report, rebind, reads, validate: () => validateCurrentShorterJointDisposition(report, entry, index, readArtifact)};
}

test('V3 composes public132/48 fitting, actual sections, washer and method evidence without raw input reads', () => {
  const f = currentV3Packet(); assert.equal(f.validate(), f.report);
  assert.deepEqual([f.report.counts.joint_clusters, f.report.counts.unique_axes, f.report.counts.fittings], [26, 112, 24]);
  assert.deepEqual([f.report.counts.native_fitting_reference_states, f.report.counts.native_fitting_torque_holds], [132, 12]);
  assert.equal(f.report.counts.header_fitting_variant_states, 48); assert.equal(f.report.counts.plywood_face_mean_bearing_rows, 96);
  assert.equal(f.report.counts.plywood_circular_plate_rows+f.report.counts.plywood_hex_inscribed_circle_plate_rows, 96);
  assert.equal(f.report.counts.retained_separate_reference_inventories.finite_projected_rear_witness_states, 5);
  assert.equal(f.report.counts.retained_separate_reference_inventories.generic45_mixed_hinge_model_states, 8);
  assert.equal(f.report.additional_separate_method_reference_inventories.updated_current112_mixed_Mp4_states, 5);
  assert.ok(f.reads.length && f.reads.every(name => name.startsWith('docs/')));
});

const fittingRow = report => report.joint_clusters.find(row => row.current_duties.fitting);
const cleatRow = report => report.joint_clusters.find(row => row.current_duties.actual_station_reduced_depth);
const mixedRow = report => report.joint_clusters.find(row => row.current_duties.lateral_common_law?.Mp4_common_work_reference);

for (const [name, mutate] of [
  ['foreign revision', r => {r.revision = 'v11-matching-rear-bolts-v1';}],
  ['foreign force bank', (r, i) => {r.source_bindings.response_bank = i.response_bank;}],
  ['reassigned joint ownership despite112 axes', r => {
    const a = r.joint_clusters[0].axis_ids, b = r.joint_clusters[1].axis_ids; [a[0], b[0]] = [b[0], a[0]];
  }],
  ['132 observations plus12 mapped holds relabeled144 accepted', r => {
    r.counts.native_fitting_reference_states = 144; r.counts.native_fitting_torque_holds = 0;
    for (const row of r.joint_clusters.filter(x => x.current_duties.fitting)) {
      const f = row.current_duties.fitting; f.native_reference_states += f.radial_torque_hold_states; f.radial_torque_hold_states = 0;
      for (const coverage of Object.values(f.native_case_coverage)) {coverage.per_state_results.push(...coverage.named_radial_torque_holds); coverage.named_radial_torque_holds = [];}
    }
  }],
  ['95 historical observations erased from the current record', r => {r.source_work_recognized.local_native_fitting.preserved_far_observations = 0;}],
  ['a selected mesh observation promoted to the remaining states', r => {fittingRow(r).current_duties.fitting.selected_mesh_is_all_state_fine_envelope = true;}],
  ['header variant observations mixed into baseline counts', r => {r.counts.native_fitting_reference_states += r.counts.header_fitting_variant_states;}],
  ['header diagnostic event limits treated as additional applied loads', r => {r.source_work_recognized.prescribed_header_static_atlas.diagnostic_totals_are_additional_applied_loads = true;}],
  ['an old inadequate common core reinstated as current missing shear work', r => {
    const d = cleatRow(r).current_duties.member_components; d.unresolved_core_evidence = structuredClone(d.superseded_reduced_depth_core_exclusion_evidence);
  }],
  ['actual-section evidence replaced with the old joint root', r => {cleatRow(r).current_duties.actual_station_reduced_depth.evidence = [{source: 'base', pointers: ['']}];}],
  ['24 physical Appendix E interruptions silently accepted', r => {r.source_work_recognized.confirmed_AppendixE_path_interruptions.new_E3_E4_resistance_or_load_allocation_assigned = true;}],
  ['plywood mean bearing promoted to whole-washer qualification', r => {cleatRow(r).current_duties.plywood_washer_mean.actual_panel_or_full_washer_qualified = true;}],
  ['a plywood plate pointer substituted for mean-bearing evidence', r => {
    cleatRow(r).current_duties.plywood_washer_mean.evidence[0].pointers = ['/sections/plywood_circular_plate/data/rows/0'];
  }],
  ['prescribed plywood plate arithmetic promoted to material acceptance', r => {cleatRow(r).current_duties.plywood_washer_plate.strength_or_fit_pass = true;}],
  ['independent virtual-slip angle equated with the NDS load angle', r => {r.source_work_recognized.generalized_lateral_common_law.NDS_load_angle_equals_independent_virtual_slip_angle_assumed = true;}],
  ['a common-law reference promoted to actual NDS capacity', r => {r.source_work_recognized.generalized_lateral_common_law.actual_NDS_or_joint_capacity_adopted = true;}],
  ['114 forces silently transferred into112', r => {r.source_work_recognized.generalized_lateral_common_law.unselected114_forces_transferred_or_geometry_adopted = true;}],
  ['the five current rear flags erased', r => {for (const row of r.joint_clusters) delete row.current_retained_flag_evidence.finite_projected_rear_witness_states;}],
  ['the eight historical generic45 flags erased', r => {for (const row of r.joint_clusters) delete row.current_retained_flag_evidence.generic45_mixed_hinge_model_states;}],
  ['new Mp/4 flags recast as physical failures', r => {r.additional_separate_method_reference_inventories.physical_failure_count = 5;}],
  ['actual Fyb invented from the Mp/4 requirement', r => {mixedRow(r).current_duties.lateral_common_law.Mp4_common_work_reference.actual_Fyb = 92000;}],
  ['the owner falsely said to have selected or purchased T88', r => {cleatRow(r).current_duties.bond_composite.owner_selected_or_purchased = true;}],
  ['physical release inferred from computed components', r => {r.fabrication_released = true;}],
  ['nonexistent evidence pointer', r => {cleatRow(r).current_duties.actual_station_reduced_depth.evidence[0].pointers.push('/sections/actual_station_reduced_depth/data/no_result');}],
  ['recursive raw-source validation claimed', r => {r.reproduction.recursive_raw_source_closure_claimed = true;}],
]) test(`V3 disposition rejects ${name}`, () => {
  const f = currentV3Packet(); mutate(f.report, f.index); assert.throws(f.validate);
});

test('V3 counterfactual public-bundle fixture rebinds both hashes before semantic tests', () => {
  const f = currentV3Packet(); f.rebind('local_member_followthrough', data => {data.fixture_note = 'No numerical or claim change';});
  assert.equal(f.validate(), f.report);
});

for (const [name, source, mutate] of [
  ['a baseline artifact with a historical95 source replaced', 'all_fitting_component_reference', d => {d.preserved_95_state_summary.sha256 = '0'.repeat(64);}],
  ['header native rows joined to another baseline case', 'header_fitting_variant', d => {d.per_state_results[0].baseline_summary_json_pointer = '/per_state_results/0';}],
  ['header event aliases counted as192 independent replacements', 'header_fitting_variant', d => {d.counts.combined_bore_replacements = 192;}],
  ['both event aliases applied as separate physical loads', 'header_fitting_variant', d => {d.counts.event_limit_aliases_are_duplicate_inputs = false;}],
  ['one bore replacement applied twice under two event names', 'header_fitting_variant', d => {d.per_state_results[0].modified_bores[1] = d.per_state_results[0].modified_bores[0];}],
  ['selected fine observations promoted to arbitrary pressure bounds', 'governing_fitting_mesh_comparison', d => {d.method_limits.arbitrary_contact_traction_stress_upper_bound_proven = true;}],
  ['actual-station source width substituted with an old thin core', 'local_member_followthrough', d => {d.sections.actual_station_reduced_depth.data.groups[0].actual_member_breadth_mm = 38.1;}],
  ['the actual24 paths relabeled as mere core artifacts', 'local_member_followthrough', d => {d.sections.appendix_path_recheck.data.interpretation.not_a_common_core_exclusion = false;}],
  ['a sawn-wood bearing factor applied to plywood means', 'plywood_washer_followthrough', d => {d.sections.plywood_washer_mean.data.adjustments_used.Cb = 1.25;}],
  ['prescribed plate stress made into actual washer strength', 'plywood_washer_followthrough', d => {d.sections.plywood_hex_plate.data.summary.washer_strength_or_fit_pass = true;}],
  ['a contracted proof promoted to arbitrary independent angles', 'lateral_method_followthrough', d => {d.sections.contracted_common_law_proof.data.common_work_bridge.arbitrary_independent_load_angle_and_virtual_velocity_angle_bound = true;}],
  ['an actual NDS capacity inserted into the formal theorem', 'lateral_method_followthrough', d => {d.sections.generalized_lateral_theorem.data.complete_NDS_connection_capacity = 1000;}],
  ['the separate114 bank substituted for current112 rear fields', 'lateral_method_followthrough', d => {const f = d.sections.contracted_saved_fields.data; f.current112_rear.bank = f.unselected114_rear.bank;}],
  ['current mixed force reconstruction replaced by another saved field', 'lateral_method_followthrough', d => {d.sections.mixed_Mp4_projection.data.rows[0].full_N_V_T_M_and_capture_demands_sha256_unchanged = '0'.repeat(64);}],
  ['conditional T88 selection rewritten as an owner purchase', 'adhesive_bond_basis', d => {d.selection.purchased_or_delivered = true;}],
  ['adhesive process data treated as a fabrication release', 'adhesive_bond_basis', d => {d.decision_and_release.purchase_or_fabrication_released = true;}],
  ['24hour functional strength substituted for full cure', 'adhesive_bond_basis', d => {d.manufacturer_process_reference.cure.TDS_full_cure_at_70F = '24 hours';}],
]) test(`V3 rejects ${name} after valid public artifact rebinding`, () => {
  const f = currentV3Packet(); f.rebind(source, mutate); assert.throws(f.validate);
});

test('V3 entry point checks encoded/decoded pins and works without optional addon fields', () => {
  const f = currentV3Packet(); assert.equal(checkDevelopment(f.index, {entryChecks: false}).complete_connection_acceptance, null);
  f.entry.current_joint_disposition.decoded_sha256 = '0'.repeat(64); assert.throws(() => checkDevelopment(f.index, {entryChecks: false}));
  f.entry.current_joint_disposition = structuredClone(currentV3Disposition); f.entry.current_joint_disposition.sha256 = '0'.repeat(64);
  assert.throws(() => checkDevelopment(f.index, {entryChecks: false}));
  f.entry.current_joint_disposition = structuredClone(currentV3Disposition);
  for (const key of ['all_fitting_component_reference', 'header_fitting_variant', 'governing_fitting_mesh_comparison', 'local_member_followthrough',
    'plywood_washer_followthrough', 'lateral_method_followthrough', 'adhesive_bond_basis', 'joint_disposition', 'joint_criterion_followthrough',
    'formed_angle_component_followthrough', 'far_row_fitting_component_extension', 'global_washer_minimum_thickness', 'build_package']) delete f.entry[key];
  assert.equal(checkDevelopment(f.index, {entryChecks: false}).complete_connection_acceptance, null);
});
