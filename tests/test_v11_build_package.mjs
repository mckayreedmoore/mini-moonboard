import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {ROOT, readIndex, checkDevelopment, validateShorterRearMaterialReferences, validateShorterRearProjectedBearingWitness,
  validateShorterJointCriterionFollowthrough, validateV11BuildPackage, validateV11BracketThicknessConfirmation,
  validateShorterFormedAngleReference, validateShorterNearWasherSeat, validateShorterWasherMinimumThickness,
  validateMatchingRearAffectedComponents} from '../scripts/check_bolted_development.mjs';

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
