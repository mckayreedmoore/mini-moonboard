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
  validateTopGeometryReview, validateFarRowFittingExtension, validateCurrentShorterJointDisposition,
  validateShorterV4ComponentOverlay, validateShorterContactCaseSet, preservedDevelopmentIndex} from '../scripts/check_bolted_development.mjs';

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
  const index = preservedDevelopmentIndex(readIndex()), shorter = index.owner_authorized_shorter_bolt_trial;
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

function v4ComponentFixture() {
  // Synthetic component data uses public V3 demands only. It is not an issued
  // engineering projection or the pending contact-case publication.
  const {index, entry, report: base} = currentV3Packet();
  const methodRef = base.source_bindings.lateral_method_followthrough;
  const methods = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, methodRef.path)))).sections;
  const criteria = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, base.source_bindings.criteria.path))));
  const originals = criteria.continuous_rear_bearing.exact_exceedance_certificates;
  const mixed = methods.mixed_Mp4_projection.data.rows, rear = methods.contracted_saved_fields.data.current112_rear.states;
  const raw = name => ({path: `fea/generated/unavailable-v4-software-fixture/${name}.json`, sha256: '1'.repeat(64)});
  const scenarioRows = mixed.map((prior, n) => {
    const a574 = prior.Fyb_basis_unchanged.includes('A574'), Fyb = a574 ? 166500 : 92000, hinge = 1000*prior.Mp4_required_Fyb_ksi/Fyb;
    return {axis_id: prior.axis_id, case_id: prior.case_id, source_pointer: `/rows/${n}`, source_row_sha256: '2'.repeat(64),
      declared_material_scenario: a574 ? 'A574_design_note153_TR12_mean166.5' : 'retained_Grade5_F60692', conditional_Fy_psi: a574 ? 153000 : 92000,
      conditional_estimated_Fyb_psi: Fyb, Mp4_required_Fyb_ksi_unchanged: prior.Mp4_required_Fyb_ksi, Mp4_hinge_index: hinge,
      contracted_bearing_index_unchanged: prior.contracted_bearing_index_unchanged,
      combined_common_work_bearing_Mp4_index: Math.max(hinge, prior.contracted_bearing_index_unchanged), independent_full_N_V_T_M_Fy_over2_index: .1};
  });
  const certificates = methods.contracted_common_law_summary.data.current112_rear.bearing_above_one_states.map(flag => {
    const saved = rear.find(row => row.axis_id === flag.axis_id && row.case_id === flag.case_id);
    const n = originals.findIndex(row => row.axis_id === flag.axis_id && row.case_id === flag.case_id), original = originals[n], lambda = saved.governing.lambda;
    const receiverIndex = criteria.continuous_rear_bearing.case_rows.findIndex(row => row.axis_id === flag.axis_id && row.case_id === flag.case_id && row.host === original.host);
    const a = BigInt(lambda*2**53), b = 2n**53n, upper = {numerator: (BigInt(original.support_integral_upper_exact.numerator)*a).toString(),
      denominator: (BigInt(original.support_integral_upper_exact.denominator)*b).toString()};
    const lower = Number(original.equilibrium_functional_exact.numerator)/Number(original.equilibrium_functional_exact.denominator)/(Number(upper.numerator)/Number(upper.denominator));
    return {axis_id: flag.axis_id, case_id: flag.case_id, host: original.host, original_certificate_pointer: `/rows/${receiverIndex}`, certified_continuous_lower_bound: lower,
      equilibrium_functional_exact: original.equilibrium_functional_exact, contracted_support_integral_upper_exact: upper,
      regions: original.regions.map(region => ({region_id: region.id, lambda, lambda_exact: {numerator: a.toString(), denominator: b.toString()}})),
      selected_contracted_witness_index: saved.contracted_bearing_maximum,
      full_signed_actions_and_metal_sha256_unchanged: saved.unchanged_full_signed_actions_and_metal_sha256,
      all_source_receiver_forces_and_first_moments_unchanged: true, reference_threshold_one_exactly_exceeded: true};
  });
  const axial = {schema: 'v11_axial_interface_resultant_composition/v1', revision: entry.revision,
    counts: {axes: 112, cases: 6, all_end_case_states: 1344, end_resultant_rows: 1344, axial_interface_reference_rows: 1248,
      separate_plywood_head_rows: 96, fitting_root_flange_cut_wrenches_not_added_as_extra_loads: 288},
    interpretation: {load_only_interface_resultant_reconciliation: true, joint_level_static_equilibrium_certificate: false,
      physical_prying_or_finite_contact_prediction: false, static_lower_bound_capacity_certificate: false, structural_acceptance: false,
      fabrication_released: false, climbing_released: false}};
  const note = {schema: 'v11_A574_declared_note_TR12_estimate_summary/v1', hypotheses: {A574_design_only_Fy_psi_at2percent_offset: 153000,
    A574_full_size_Fu_psi: 180000, TR12_approximate_Fyb_psi: 166500},
    actual_Cg: null, actual_Cdelta: null, actual_Fy: null, actual_Fyb: null, actual_product_conformity: null, complete_joint_capacity: null,
    grade_required_F606_minimum_resolved: false, property_adopted: false, physical_or_structural_acceptance: false, new_optimization_FE_CAD_native_or_global_solve: false,
    summary: {preserved_generic45_Mp4_flags: methods.mixed_Mp4_summary.data.summary.new_reference_above_one_rows, preserved_uniform_Mp5_flag_count: 8}};
  const bound = {schema: 'v11_contracted_continuous_bearing_necessary_bound/v1', revision: entry.revision, rows: certificates,
    summary: {maximum_continuous_necessary_index: Math.max(...certificates.map(row => row.certified_continuous_lower_bound))}, actual_Cg: null, actual_Cdelta: null, complete_joint_capacity: null,
    geometry_or_forces_changed: false, new_global_native_or_pressure_solve: false, physical_failure_claim: false, structural_acceptance: false,
    unselected114_geometry_or_forces_transferred: false};
  const updates = base.joint_clusters.map((prior, n) => {
    const indices = scenarioRows.flatMap((row, k) => prior.axis_ids.includes(row.axis_id) ? [k] : []), picked = certificates.filter(row => prior.axis_ids.includes(row.axis_id));
    const duties = {axial_interface_resultant_reconciliation: {axis_count: prior.axis_ids.length, case_count: 6, end_resultant_rows: 12*prior.axis_ids.length,
      raw_row_selection: {source: 'axial_static_composition', array_pointer: '/end_resultants', axis_ids: prior.axis_ids, case_ids: bankCaseIds(),
        ends: ['head', 'nut'], full_rows_omitted_from_overlay: true}, joint_level_static_equilibrium_certificate: false,
      physical_prying_or_finite_contact_prediction: false, static_lower_bound_capacity_certificate: false}};
    if (indices.length) duties.A574_declared_note_TR12_reference = {compact_case_reference_indices: indices, case_rows: indices.length,
      maximum_combined_common_work_bearing_Mp4_index: Math.max(...indices.map(k => scenarioRows[k].combined_common_work_bearing_Mp4_index)), above_one_reference_rows: 0,
      grade_required_F606_minimum_resolved: false, property_adopted: false, actual_Fy: null, actual_Fyb: null};
    if (picked.length) duties.contracted_continuous_rear_necessary_reference = {case_rows: picked.length, maximum_necessary_reference_index: Math.max(...picked.map(row => row.certified_continuous_lower_bound)),
      pressure_search_can_clear_same_reference: false, same_duals_and_source_receiver_wrenches: true};
    return {joint_id: prior.joint_id, axis_ids: prior.axis_ids, base_pointer: `/joint_clusters/${n}`, retained_v3_flags_pointer: `/joint_clusters/${n}/current_retained_flag_evidence`,
      retained_v3_method_flags_pointer: prior.current_duties.lateral_common_law ? `/joint_clusters/${n}/current_duties/lateral_common_law/additional_separate_fixed_field_reference_flags` : null,
      additional_duties: duties, remaining_limit_ids: ['axial_static_composition', ...(indices.length ? ['A574_note_TR12'] : []), ...(picked.length ? ['contracted_necessary_bound'] : [])],
      actual_Cg: null, actual_Cdelta: null, complete_joint_capacity: null, whole_joint_qualified: false};
  });
  const report = {schema: 'v11_current_joint_disposition_additive_overlay/v4', revision: entry.revision, preserved_base_v3: currentV3Disposition,
    response_bank: entry.response_bank, geometry_receipt: entry.geometry_receipt, source_bindings: {base_v3: currentV3Disposition,
      contracted_continuous_bound: raw('bound'), A574_note_TR12_summary: raw('note-summary'), A574_note_TR12_projection: raw('note-rows'), axial_static_composition: raw('axial')},
    inherited_reference_inventories: {retained_separate_reference_inventories: base.counts.retained_separate_reference_inventories,
      additional_separate_method_reference_inventories: base.additional_separate_method_reference_inventories},
    composition: {base_rows: '/joint_clusters', overlay_rows: '/joint_updates', join_key: 'joint_id', whole_joint_qualification_or_capacity_inherited: false},
    compact_new_evidence: {contracted_continuous_bound: {source: 'contracted_continuous_bound', data: bound},
      A574_note_TR12_case_references: {source: 'A574_note_TR12_projection', rows: scenarioRows}, A574_note_TR12_summary: {source: 'A574_note_TR12_summary', data: note},
      axial_static_composition: {source: 'axial_static_composition', data: axial, omitted_source_arrays: {'/end_resultants': 1344}}}, joint_updates: updates,
    counts: {joint_updates: 26, unique_axes: 112, inherited_fittings: 24, new_continuous_necessary_reference_rows: 5,
      A574_note_TR12_scenario_rows: 144, A574_note_scenario_rows: 72, unchanged_Grade5_scenario_rows: 72, axial_end_resultant_rows_reconciled: 1344},
    actual_Cg: null, actual_Cdelta: null, actual_Fyb: null, complete_joint_capacity: null, accepted_connection_exceedance_count: null, physical_failure_count: null,
    whole_joint_qualified: false, candidate_selected: false, structural_acceptance: false, property_adopted: false, purchase_authorized: false,
    drilling_released: false, fabrication_released: false, climbing_released: false, new_force_geometry_or_native_work: false, recursive_raw_source_closure_claimed: false,
    publication_ready: false, pending_extensions: {final_contact_case_set_summary: {incorporated: false}}};
  const reads = [], readArtifact = ref => {assert.ok(ref.path.startsWith('docs/'), 'component guard must never open raw fixture declarations'); reads.push(ref.path); return readFileSync(path.join(ROOT, ref.path));};
  return {report, index, entry, reads, validate: () => validateShorterV4ComponentOverlay(report, entry, index, readArtifact)};
}

function bankCaseIds() {return ['a12-forward', 'a12-left', 'a12-rear', 'k12-right', 'k12-rear', 'a1-rear'];}

test('V4 component preparation covers sparse joins without raw inputs or activating a pending publication', () => {
  const f = v4ComponentFixture(); assert.equal(f.validate(), f.report); assert.ok(f.reads.length);
  assert.equal(f.report.publication_ready, false); assert.equal(f.report.pending_extensions.final_contact_case_set_summary.incorporated, false);
  assert.throws(() => validateCurrentShorterJointDisposition(f.report, f.entry, f.index), 'the live dispatcher must not accept this unfinished overlay');
});

for (const [name, mutate] of [
  ['a different inherited book', r => {r.preserved_base_v3 = {...r.preserved_base_v3, sha256: '0'.repeat(64)};}],
  ['another force-bank revision', r => {r.revision = 'v11-matching-rear-bolts-v1';}],
  ['a duplicate sparse joint', r => {r.joint_updates[1].joint_id = r.joint_updates[0].joint_id;}],
  ['a reassigned base pointer', r => {r.joint_updates[0].base_pointer = '/joint_clusters/1';}],
  ['old generic45 flags erased by the new property scenario', r => {r.inherited_reference_inventories.additional_separate_method_reference_inventories.updated_current112_mixed_Mp4_states = 0;}],
  ['an exact support bound that no longer proves exceedance', r => {r.compact_new_evidence.contracted_continuous_bound.data.rows[0].contracted_support_integral_upper_exact.numerator = '100';}],
  ['a rounded certificate ratio substituted for its own rational proof', r => {r.compact_new_evidence.contracted_continuous_bound.data.rows[0].certified_continuous_lower_bound = 1.3;}],
  ['a receiver force-and-moment source replaced', r => {r.compact_new_evidence.contracted_continuous_bound.data.rows[0].full_signed_actions_and_metal_sha256_unchanged = '0'.repeat(64);}],
  ['an unrelated equilibrium functional dressed as the same saved force', r => {r.compact_new_evidence.contracted_continuous_bound.data.rows[0].equilibrium_functional_exact.numerator = '999999999999999999999999999999999999999999999';}],
  ['a filtered-certificate index used in the full receiver-row source', r => {r.compact_new_evidence.contracted_continuous_bound.data.rows[1].original_certificate_pointer = '/rows/1';}],
  ['a stronger contraction substituted for the declared law', r => {r.compact_new_evidence.contracted_continuous_bound.data.rows[0].regions[0].lambda_exact.numerator = '1';}],
  ['a pressure search said to clear the same necessary reference', r => {r.joint_updates.find(x => x.additional_duties.contracted_continuous_rear_necessary_reference).additional_duties.contracted_continuous_rear_necessary_reference.pressure_search_can_clear_same_reference = true;}],
  ['a theoretical note relabeled as an applicable F606 property minimum', r => {r.compact_new_evidence.A574_note_TR12_summary.data.grade_required_F606_minimum_resolved = true;}],
  ['153ksi design yield used as adopted actual Fy', r => {r.compact_new_evidence.A574_note_TR12_summary.data.actual_Fy = 153000;}],
  ['TR12 Fyb substituted for independent Fy', r => {r.compact_new_evidence.A574_note_TR12_case_references.rows[0].conditional_Fy_psi = 166500;}],
  ['the existing five generic45 flags removed from the new summary', r => {r.compact_new_evidence.A574_note_TR12_summary.data.summary.preserved_generic45_Mp4_flags = [];}],
  ['one property case silently omitted', r => {r.compact_new_evidence.A574_note_TR12_case_references.rows.pop();}],
  ['a different current demand attached to a property case', r => {r.compact_new_evidence.A574_note_TR12_case_references.rows[0].Mp4_required_Fyb_ksi_unchanged *= 2;}],
  ['only1248 axial rows claimed while plywood heads vanish', r => {r.compact_new_evidence.axial_static_composition.data.counts.end_resultant_rows = 1248;}],
  ['288 fitting-root cuts added again as external reactions', r => {r.compact_new_evidence.axial_static_composition.data.counts.end_resultant_rows += 288;}],
  ['the nut end replaced by a duplicate head selector', r => {r.joint_updates[0].additional_duties.axial_interface_resultant_reconciliation.raw_row_selection.ends = ['head', 'head'];}],
  ['axial resultant closure promoted to a joint equilibrium certificate', r => {r.compact_new_evidence.axial_static_composition.data.interpretation.joint_level_static_equilibrium_certificate = true;}],
  ['load-only axial bookkeeping promoted to a lower-bound capacity', r => {r.joint_updates[0].additional_duties.axial_interface_resultant_reconciliation.static_lower_bound_capacity_certificate = true;}],
  ['zero saved end couples interpreted as zero physical prying', r => {r.compact_new_evidence.axial_static_composition.data.interpretation.physical_prying_or_finite_contact_prediction = true;}],
  ['actual Cg inferred', r => {r.actual_Cg = 1;}],
  ['an owner purchase released', r => {r.purchase_authorized = true;}],
  ['raw-source closure claimed', r => {r.recursive_raw_source_closure_claimed = true;}],
]) test(`V4 component preparation rejects ${name}`, () => {
  const f = v4ComponentFixture(); mutate(f.report); assert.throws(f.validate);
});

function contactCaseFixture() {
  // Software fixture only: its raw refs deliberately cannot be opened. Actual
  // sensitivity results enter through the final public, hash-bound overlay.
  const {entry, bank} = packet(), raw = name => ({path: `fea/generated/unavailable-contact-fixture/${name}.json`, sha256: digest(name)});
  const hosts = ['base_post_center_left', 'base_post_center_right', 'lumber_leg_left', 'lumber_leg_right'];
  const rows = bankCaseIds().map((caseId, n) => {
    const qHash = digest(caseId+'/new-q'), result = raw(caseId+'/result');
    const guess = raw(caseId+'/actual_result_final_q_numerical_guess'), locator = caseId === 'a12-rear' ? guess : result;
    return {case_id: caseId, original_field: bank.cases[n].field, original_q_canonical_sha256: digest(caseId+'/old-q'),
      original_case_applied_vector_sha256: digest(caseId+'/rhs'), new_q_canonical_sha256: qHash,
      ...Object.fromEntries(['original_operators', 'original_operator_arrays', 'export_report', 'new_q_export', 'optimizer_result',
        'actual_result_final_q_numerical_guess', 'direct_contact_action_export'].map(key => [key, raw(caseId+'/'+key)])),
      original_operators: {...raw(caseId+'/operators'), path: path.posix.dirname(bank.cases[n].field.path)+'/operators.json'},
      original_operator_arrays: {...raw(caseId+'/operator-arrays'), path: path.posix.dirname(bank.cases[n].field.path)+'/operators.npz'}, optimizer_result: result,
      export_status: 'PASS_RESIDUAL_FIXED_SUPPORT_OBJECTIVE_CONTACT_VARIANT_ONLY', actual_result_q_reference_pointer: '/final_q_numerical_guess',
      same_case_result_RHS_digest_present_and_verified: caseId !== 'a12-rear', direct_contact_rows: 1580, direct_contact_active_rows: 300+n,
      gradient_inf_N: (n+1)*1e-7, residual_gate_N: 1e-5,
      independent_reassembly_record_authenticated: true, independent_reassembly: {status: 'PASS', gradient_inf_n: (n+1)*1e-7,
        gradient_inf_difference_n: 1e-12, direct_contact_gradient_reassembly_max_difference_n: 1e-12, abs_energy_difference_nmm: 1e-12},
      fixed_support: {active_host_ids: hosts, active_tangent_ids: hosts.flatMap(host => [host+'/no-slip-0', host+'/no-slip-1']),
        active_tangent_count: 8, tangent_ids_by_host: Object.fromEntries(hosts.map(host => [host, [host+'/no-slip-0', host+'/no-slip-1']])),
        normal_threshold_N: 1e-7, normal_reactions_N_by_host: Object.fromEntries([...hosts, 'base_floor_left', 'base_floor_right', 'base_post_outer_left', 'base_post_outer_right'].map(host => [host, 100])),
        all_four_enabled_hosts_above_threshold: true, support_mask_feedback: false},
      recorded_warm_start_metadata: {recorded: {path: locator.path+'#/q', polish_result: raw(caseId+'/polish'), sha256_canonical: qHash}, locator_file: locator,
        recorded_path_pointer_verified: caseId === 'a12-rear', recorded_path_pointer_q_canonical_sha256: caseId === 'a12-rear' ? qHash : null,
        recorded_path_pointer_is_admission_source: false}, sensitivity_forces_newly_evaluated: true,
      original_case_or_field_promoted_or_rewritten: false, physical_contact_or_no_slip_qualified: false, structural_acceptance: false};
  });
  const report = {schema: 'v11_objective_contact_case_set_summary/v1', revision: entry.revision,
    status: 'SIX_SAVED_OPERATOR_OBJECTIVE_CONTACT_SENSITIVITY_CASES_NUMERICALLY_ADMITTED_UNSELECTED',
    original_response_bank: entry.response_bank, physical_geometry: bank.physical_geometry, physical_receipt: entry.geometry_receipt, load_contract: bank.load_contract,
    counts: {cases: 6, saved_generalized_DOFs_per_case: 11102, fixed_XY_hosts_per_case: 4, active_tangents_per_case: 8}, case_rows: rows,
    residual_gate_N: 1e-5, maximum_gradient_inf_N: Math.max(...rows.map(row => row.gradient_inf_N)),
    source_bindings: {original_bank: entry.response_bank, producer: raw('producer'), case_export_reports: Object.fromEntries(rows.map(row => [row.case_id, row.export_report]))},
    method_scope: {sensitivity_forces_newly_evaluated_under_modified_contact_kinematics: true, source_casework_is_new_saved_operator_case_evaluation: true,
      source_casework_is_native_FEA_or_CAD: false, summary_operation_performed_objective_evaluations_or_solve: false,
      physical_closest_point_contact_finite_frame_or_no_slip_qualification: false},
    actual_Cg: null, actual_Cdelta: null, complete_joint_capacity: null, accepted_connection_exceedance_count: null,
    original_bank_promoted: false, original_bank_or_geometry_rewritten: false, candidate_selected: false, physical_failure_claim: false, structural_acceptance: false,
    purchase_authorized: false, drilling_released: false, fabrication_released: false, climbing_released: false};
  return {report, validate: () => validateShorterContactCaseSet(report, entry, bank)};
}

test('contact case preparation permits disclosed invalid warm locators and normal-only hosts without opening raw inputs', () => {
  const f = contactCaseFixture(); assert.equal(f.validate(), f.report);
  assert.equal(f.report.case_rows.filter(row => !row.recorded_warm_start_metadata.recorded_path_pointer_verified).length, 5);
  assert.equal(Object.keys(f.report.case_rows[0].fixed_support.normal_reactions_N_by_host).length, 8);
});

for (const [name, mutate] of [
  ['foreign original bank', r => {r.original_response_bank = {...r.original_response_bank, sha256: '0'.repeat(64)};}],
  ['another original field', r => {r.case_rows[0].original_field = r.case_rows[1].original_field;}],
  ['another case operator arrays', r => {r.case_rows[0].original_operator_arrays = r.case_rows[1].original_operator_arrays;}],
  ['repeated case under a six-row count', r => {r.case_rows[1].case_id = r.case_rows[0].case_id;}],
  ['original q presented as a new contact result', r => {r.case_rows[0].new_q_canonical_sha256 = r.case_rows[0].original_q_canonical_sha256;}],
  ['one q reused across different load cases', r => {r.case_rows[1].new_q_canonical_sha256 = r.case_rows[0].new_q_canonical_sha256;
    r.case_rows[1].recorded_warm_start_metadata.recorded.sha256_canonical = r.case_rows[0].new_q_canonical_sha256;}],
  ['one RHS substituted across load cases', r => {r.case_rows[1].original_case_applied_vector_sha256 = r.case_rows[0].original_case_applied_vector_sha256;}],
  ['legacy result RHS verification invented', r => {r.case_rows[2].same_case_result_RHS_digest_present_and_verified = true;}],
  ['unavailable result q path used for final admission', r => {r.case_rows[0].actual_result_q_reference_pointer = '/q';}],
  ['invalid warm locator promoted to admission source', r => {r.case_rows[0].recorded_warm_start_metadata.recorded_path_pointer_is_admission_source = true;}],
  ['invalid warm locator silently marked verified', r => {r.case_rows[0].recorded_warm_start_metadata.recorded_path_pointer_verified = true;}],
  ['unauthenticated independent reassembly', r => {r.case_rows[0].independent_reassembly_record_authenticated = false;}],
  ['mismatched saved-q reassembly', r => {r.case_rows[0].independent_reassembly.direct_contact_gradient_reassembly_max_difference_n = 1;}],
  ['gate relaxed for a residual that exceeds the original gate', r => {r.case_rows[0].gradient_inf_N = 2e-5; r.case_rows[0].residual_gate_N = 1e-4;}],
  ['stale maximum residual', r => {r.maximum_gradient_inf_N /= 2;}],
  ['a fifth XY support added', r => {r.case_rows[0].fixed_support.active_host_ids.push('base_floor_left');}],
  ['only one active tangent on a fixed host', r => {r.case_rows[0].fixed_support.tangent_ids_by_host.lumber_leg_left.pop();}],
  ['XY mask retained on an unloaded host', r => {r.case_rows[0].fixed_support.normal_reactions_N_by_host.lumber_leg_left = 0;}],
  ['support feedback substituted for fixed mask', r => {r.case_rows[0].fixed_support.support_mask_feedback = true;}],
  ['new sensitivity casework described as unchanged forces', r => {r.method_scope.sensitivity_forces_newly_evaluated_under_modified_contact_kinematics = false;}],
  ['summary projection described as a new solve', r => {r.method_scope.summary_operation_performed_objective_evaluations_or_solve = true;}],
  ['objective map promoted to physical closest-point qualification', r => {r.method_scope.physical_closest_point_contact_finite_frame_or_no_slip_qualification = true;}],
  ['sensitivity bank promotion', r => {r.original_bank_promoted = true;}],
  ['complete joint capacity inferred', r => {r.complete_joint_capacity = 1;}],
]) test(`contact case preparation rejects ${name}`, () => {
  const f = contactCaseFixture(); mutate(f.report); assert.throws(f.validate);
});

const currentV4Disposition = {path: 'docs/bolted-frame-development/owner-frame-v11/shorter-bolts/current-joint-disposition-v4.json.gz',
  sha256: 'f9f950b63d71ab0918087cfebeb75892e75988107da16048292da9e5f402792f', encoding: 'gzip', decoded_bytes: 818136,
  decoded_sha256: '0eca25c7bcff01783f030ef5711a7e5aa25e8149bdd18b748bdb5f973c43613c'};

function currentV4Packet() {
  const {index, entry} = packet(); entry.current_joint_disposition = structuredClone(currentV4Disposition);
  const encoded = readFileSync(path.join(ROOT, currentV4Disposition.path)), decoded = gunzipSync(encoded);
  assert.equal(digest(encoded), currentV4Disposition.sha256); assert.equal(digest(decoded), currentV4Disposition.decoded_sha256);
  assert.equal(decoded.length, currentV4Disposition.decoded_bytes);
  const report = JSON.parse(decoded), reads = [], readArtifact = ref => {
    assert.ok(ref.path.startsWith('docs/'), 'V4 source maps are declarations; portable validation never opens raw inputs');
    reads.push(ref.path); return readFileSync(path.join(ROOT, ref.path));
  };
  return {index, entry, report, reads, validate: () => validateCurrentShorterJointDisposition(report, entry, index, readArtifact)};
}

const v4Section = (report, key) => report.compact_new_evidence[key].data;
const v4Duty = (report, key) => report.joint_updates.find(row => row.additional_duties[key]).additional_duties[key];

test('V4 validates its pinned public V3 base and six distinct contact scenarios without raw input reads', () => {
  const f = currentV4Packet(); assert.equal(f.validate(), f.report); assert.ok(f.reads.length && f.reads.every(name => name.startsWith('docs/')));
  assert.equal(f.report.counts.member_case_reference_rows, 120); assert.equal(f.report.counts.axial_end_resultant_rows_reconciled, 1344);
  assert.equal(f.report.inherited_reference_inventories.retained_separate_reference_inventories.finite_projected_rear_witness_states, 5);
  assert.equal(f.report.inherited_reference_inventories.retained_separate_reference_inventories.generic45_mixed_hinge_model_states, 8);
  assert.equal(f.report.inherited_reference_inventories.additional_separate_method_reference_inventories.updated_current112_mixed_Mp4_states, 5);
});

for (const [name, mutate] of [
  ['unfinished component draft activated', r => {r.publication_ready = false;}],
  ['unincorporated contact set activated', r => {r.pending_extensions.final_contact_case_set_summary.incorporated = false;}],
  ['source contact casework described as unchanged forces', r => {r.source_contact_casework_newly_evaluated_forces = false;}],
  ['whole source history described as projection-only work', r => {r.new_force_geometry_or_native_work_scope = 'all_source_casework';}],
  ['foreign bank in the final contact summary', r => {v4Section(r, 'contact_case_set').original_response_bank.sha256 = '0'.repeat(64);}],
  ['member response q borrowed from another case', r => {const rows = v4Section(r, 'member_contact_references').cases; rows[0].sensitivity_q = rows[1].sensitivity_q;}],
  ['member q canonical digest copied from an original field', r => {const row = v4Section(r, 'member_contact_references').cases[0]; row.terminal_q_canonical_sha256 = v4Section(r, 'contact_case_set').case_rows[0].original_q_canonical_sha256;}],
  ['member internal replay failure hidden by passed=true', r => {v4Section(r, 'member_contact_references').cases[0].strict_seed_operator_action_replay.maximum_absolute_errors['member_element_actions.end_actions_local_n_nmm'] = .1;}],
  ['saved beam replay silently omitted under passed=true', r => {delete v4Section(r, 'member_contact_references').cases[0].strict_seed_operator_action_replay.maximum_absolute_errors['member_element_actions.end_actions_local_n_nmm'];}],
  ['one sawn member silently omitted', r => {delete v4Section(r, 'member_contact_references').cases[0].per_member_references.base_header;}],
  ['stale terminal member delta', r => {v4Section(r, 'member_contact_references').cases[0].per_member_references.base_side_left.terminal_minus_original_saved_field.maximum_shear_torsion_reference_upper = 0;}],
  ['stale terminal member maximum', r => {v4Section(r, 'member_contact_references').six_case_terminal_reference_maxima.maximum_shear_torsion_reference_upper.value = .9;}],
  ['original signed geometry eligibility transferred to new q', r => {v4Duty(r, 'member_contact_reference_sensitivity').current_geometry_or_row_direction_eligibility_transferred = true;}],
  ['global member maximum assigned to unrelated joint receivers', r => {v4Duty(r, 'member_contact_reference_sensitivity').member_ids.push('unowned-member');}],
  ['new contact sensitivity assigned132 native stress passes', r => {r.counts.original_native_reference_states_not_new_contact_states = 0; v4Duty(r, 'objective_contact_sensitivity_case_set').original_bank_or_native_component_results_transferred_to_new_sensitivity = true;}],
  ['rear source RHS borrowed from another case', r => {const rows = v4Section(r, 'rear_contact_references').cases; rows[0].same_case_RHS_little_endian_f64_sha256 = rows[1].same_case_RHS_little_endian_f64_sha256;}],
  ['duplicated rear receiver replaces a missing certificate', r => {const rows = v4Section(r, 'rear_contact_references').receiver_rows; rows[1] = structuredClone(rows[0]);}],
  ['the five sensitivity necessary flags erased', r => {v4Section(r, 'rear_contact_references').summary.sensitivity_receiver_above_one_rows = [];}],
  ['uncontracted necessary bounds labeled contracted witnesses', r => {r.compact_new_evidence.rear_contact_references.reference_type = {response_scenario: 'original_response_bank', constitutive_envelope: 'contracted_ellipse', certificate_kind: 'constructed_pressure_witness'};}],
  ['subset exclusion silently denied', r => {v4Duty(r, 'rear_contact_necessary_references').flagged_larger_envelope_exclusions_imply_contracted_subset_exclusion = false;}],
  ['new pressure witnesses invented for the five new cases', r => {v4Section(r, 'rear_contact_references').cases[0].sensitivity_pressure_witness_maximum = 1;}],
  ['support response joined to a different case', r => {const rows = v4Section(r, 'support_reaction_basis').saved_q_sensitivities; rows[0].response = rows[1].response;}],
  ['six support sensitivities reduced to two in the summary', r => {v4Section(r, 'support_reaction_basis').summary.sensitivity_count = 2;}],
  ['eight tangent axes presented as eight XY hosts', r => {v4Section(r, 'support_reaction_basis').support_census.xy_tangent_enabled_host_count = 8;}],
  ['signed tangent scalar reaction reversed', r => {v4Section(r, 'support_reaction_basis').saved_q_sensitivities[0].tangent_axis_actions[0].force_on_host_xyz_n[0] *= -1;}],
  ['host tangent magnitude substituted for signed components', r => {const host = v4Section(r, 'support_reaction_basis').saved_q_sensitivities[0].normal_hosts[2]; host.tangential_force_xy_n = [host.tangential_resultant_n, 0];}],
  ['two-axis resultant replaced by the largest scalar', r => {const host = v4Section(r, 'support_reaction_basis').saved_q_sensitivities[0].normal_hosts[2]; host.tangential_resultant_n = Math.max(...host.tangential_force_xy_n.map(Math.abs));}],
  ['support T/N ratio promoted to actual floor capacity', r => {v4Section(r, 'support_reaction_basis').summary.actual_floor_friction_capacity_assigned = true;}],
  ['resultant force ratio promoted to sufficient patch moment transfer', r => {v4Section(r, 'support_reaction_basis').summary.full_patch_moment_transfer_sufficiency_established = true;}],
  ['one new evidence pointer not present in the compact public projection', r => {v4Duty(r, 'objective_contact_sensitivity_case_set').evidence[0].pointers.push('/case_rows/missing');}],
  ['rear evidence reassigned to an unrelated joint', r => {v4Duty(r, 'rear_contact_necessary_references').evidence[0].pointers.push('/receiver_rows/1');}],
  ['sensitivity references promoted to physical acceptance', r => {v4Section(r, 'member_contact_references').structural_acceptance = true;}],
]) test(`V4 public overlay rejects ${name}`, () => {
  const f = currentV4Packet(); mutate(f.report); assert.throws(f.validate);
});

test('V4 entry point verifies encoded/decoded pins and retains optional-addon omission behavior', () => {
  const f = currentV4Packet(); assert.equal(checkDevelopment(f.index, {entryChecks: false}).complete_connection_acceptance, null);
  f.entry.current_joint_disposition.decoded_sha256 = '0'.repeat(64); assert.throws(() => checkDevelopment(f.index, {entryChecks: false}));
  f.entry.current_joint_disposition = {...currentV4Disposition, sha256: '0'.repeat(64)}; assert.throws(() => checkDevelopment(f.index, {entryChecks: false}));
  f.entry.current_joint_disposition = structuredClone(currentV4Disposition);
  for (const key of ['all_fitting_component_reference', 'header_fitting_variant', 'governing_fitting_mesh_comparison', 'local_member_followthrough',
    'plywood_washer_followthrough', 'lateral_method_followthrough', 'adhesive_bond_basis', 'joint_disposition', 'joint_criterion_followthrough',
    'formed_angle_component_followthrough', 'far_row_fitting_component_extension', 'global_washer_minimum_thickness', 'build_package', 'objective_contact_response_sensitivity']) delete f.entry[key];
  assert.equal(checkDevelopment(f.index, {entryChecks: false}).complete_connection_acceptance, null);
});
