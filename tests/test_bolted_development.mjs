import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {test} from 'node:test';
import {gunzipSync} from 'node:zlib';
import {ROOT, readIndex as readCurrentIndex, checkDevelopment as checkCurrentDevelopment, validateEntry, validateStructuralAssessment, validateCurrentResponse, validateCurrentComponents, validateEngineeringAssessment, viewerModel} from '../scripts/check_bolted_development.mjs';
import {validateKickerClearance} from '../site/eoere-kicker-clearance-overlay.mjs';
import {validateUniformChannels} from '../site/eoere-uniform-channels-overlay.mjs';
import {validateFrontPosts} from '../site/eoere-front-posts-4x6-overlay.mjs';
import {validateNarrowChannels} from '../site/eoere-narrow-channels-overlay.mjs';
import {validateRetainedFrame} from '../site/eoere-retained-frame-overlay.mjs';
import {validateOwnerFrame} from '../site/eoere-owner-frame-overlay.mjs';

// Keep exercising the preserved force/shop contracts against their own geometry.
function ownRevision(revision) {
  let index = readCurrentIndex();
  while (index && index.geometry.revision !== revision) index = index.preceding_revision;
  assert.ok(index, `preserved revision missing: ${revision}`);
  return index;
}
const readNotchIndex = () => ownRevision('eoere-narrow-channel-openings-v1');
const readPostIndex = () => ownRevision('eoere-4x6-front-posts-v1');
const readIndex = () => ownRevision('eoere-raised-kicker-screws-v1');
const checkDevelopment = (index = readIndex()) => checkCurrentDevelopment(index, {entryChecks: false});

test('current geometry/shop, preceding response and baseline keep their own identities', () => {
  assert.equal(checkCurrentDevelopment().passed, true);
});

test('owner revision cannot inherit the removed-return frame acceptance', () => {
  const index = readCurrentIndex();
  index.conditional_frame_evaluation = ownRevision('eoere-paired-frame-retained-2x6-A574-v2').conditional_frame_evaluation;
  assert.throws(() => checkCurrentDevelopment(index));
});

for (const [label, mutate] of [
  ['unrelated cleat part moved', scene => {scene.replacements[0].name = 'eoere_cleat_left';}],
  ['foreign parent', scene => {scene.parent_layout.sha256 = '0'.repeat(64);}],
  ['front move claims acceptance', scene => {scene.complete_conditional_frame_evaluation = true;}],
]) test(`reject local front revision ${label}`, () => {
  const index = readCurrentIndex();
  const scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validateOwnerFrame(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['missing omitted stack component', scene => {scene.removals.pop();}],
  ['foreign parent receipt', scene => {scene.parent_layout.sha256 = '0'.repeat(64);}],
  ['historical strength transferred', scene => {scene.historical_capacity_transferred = true;}],
]) test(`reject retained-frame ${label}`, () => {
  const index = ownRevision('eoere-paired-frame-retained-2x6-A574-v2');
  const scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validateRetainedFrame(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['stale post geometry', i => {i.geometry.revision = i.preceding_revision.geometry.revision;}],
  ['post scene drift', i => {i.geometry.scene.sha256 = '0'.repeat(64);}],
  ['old response transfer to 4x6 posts', i => {i.current_response = i.preceding_revision.current_response;}],
  ['post hardware receipt drift', i => {i.hardware_model.receipt = i.preceding_revision.hardware_model.receipt;}],
  ['post hardware override omission', i => {i.shop.overrides.pop();}],
  ['post physical release', i => {i.fabrication_released = true;}],
]) test(`reject ${label}`, () => {
  const index = readPostIndex(); mutate(index);
  assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});

for (const [label, mutate] of [
  ['second spacer hidden by a duplicate role', p => {p.replacements.find(r => r.name.endsWith('_spacer_2')).fabrication.hardware_role = 'spacer';}],
  ['incomplete advertised stack roles', p => {p.replacements.find(r => r.fabrication.connection_name === 'cleat_post_bolt_left_1').fabrication.stack_roles.pop();}],
]) test(`reject post viewer ${label}`, () => {
  const index = readPostIndex(), scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene);
  assert.throws(() => validateFrontPosts(scene, index.geometry.receipt.sha256));
});

for (const [label, mutate] of [
  ['stale current revision', i => {i.geometry.revision = i.response.revision;}],
  ['unknown viewer', i => {i.geometry.viewer = 'not-a-model';}],
  ['scene hash drift', i => {i.geometry.scene.sha256 = '0'.repeat(64);}],
  ['response relabel', i => {i.response.revision = i.geometry.revision;}],
  ['response transfer', i => {i.response.applies_to_current_geometry = true;}],
  ['missing shop override', i => {i.shop.overrides = [];}],
  ['stale shop revision', i => {i.shop.revision = i.response.revision;}],
  ['stale shop geometry', i => {i.shop.geometry = i.response.geometry;}],
  ['shop result hash drift', i => {i.shop.result.sha256 = '0'.repeat(64);}],
  ['missing current channel drawings', i => {i.shop.current_channel_drawings_complete = false;}],
  ['shop hardware application missing', i => {i.shop.hardware_model_updated = false;}],
  ['applied hardware binding missing', i => {delete i.hardware_model;}],
  ['applied hardware parent drift', i => {i.hardware_model.wood_screw_geometry = i.response.geometry;}],
  ['hardware response transfer', i => {i.hardware_model.analysis_pass_transferred = true;}],
  ['shop plan relabeled as release', i => {i.shop.shop_planning_only = false;}],
  ['official optional grid', i => {i.optional_grid.official = true;}],
  ['optional viewer aliasing the base', i => {i.optional_grid.viewer = i.geometry.viewer;}],
  ['proposal relabel', i => {i.unadopted_proposal.revision = 'invented-revision';}],
  ['adopted Z180 proposal', i => {i.unadopted_proposal.adopted = true;}],
  ['physical release', i => {i.fabrication_released = true;}],
  ['structural assessment missing', i => {delete i.structural_assessment;}],
  ['structural assessment hash drift', i => {i.structural_assessment.sha256 = '0'.repeat(64);}],
  ['current response missing', i => {delete i.current_response;}],
  ['engineering assessment missing', i => {delete i.engineering_assessment;}],
  ['engineering assessment hash drift', i => {i.engineering_assessment.sha256 = '0'.repeat(64);}],
  ['current response hardware transfer', i => {i.current_response.hardware_model = i.response.geometry;}],
]) test(`reject ${label}`, () => {
  const index = readIndex(); mutate(index);
  assert.throws(() => checkDevelopment(index));
});

for (const [label, mutate] of [
  ['structural acceptance', r => {r.structural_acceptance = true;}],
  ['invented joint capacity', r => {r.complete_joint_resistance = 1;}],
  ['invented bracing', r => {r.member_effective_length_domain[0].actual_effective_length_factor = .5;}],
  ['changed effective length', r => {r.member_effective_length_domain[0].maximum_effective_length_for_l_over_d_50_mm *= 2;}],
  ['missing member domain', r => {r.member_effective_length_domain.pop();}],
  ['wrong model', r => {r.geometry_revision = 'old';}],
  ['wrong producer', r => {r.producer.sha256 = '0'.repeat(64);}],
  ['missing case', r => {r.cases.pop();}],
  ['wrong probe state', r => {r.finite_arm_contact_probe.cases[1].state_id = r.cases[0].state_id;}],
  ['wrong load direction', r => {r.load_checks[0].climber_force_xyz_n[1] *= -1;}],
  ['changed gravity', r => {r.load_checks[0].permanent_and_accessory_weight_n += 1;}],
  ['invented complete load envelope', r => {r.recorded_load_basis.dynamic_spectrum_or_all_hold_direction_envelope_verified = true;}],
  ['invented physical error bound', r => {r.finite_arm_contact_probe.finite_equilibrium_contact_law_or_error_bound = true;}],
  ['invented pressure response', r => {r.finite_arm_contact_probe.cases[0].physical_error_bound_or_response = true;}],
  ['missing contact switches', r => {r.finite_arm_contact_probe.cases[0].strict_open_compressed_class_changes = 0;}],
  ['coordinated contact-switch omission', r => {
    for (const c of r.finite_arm_contact_probe.cases) {
      c.open_to_compressed = c.compressed_to_open = c.strict_open_compressed_class_changes = 0;
      c.largest_gap_change_class_switch = null;
    }
  }],
  ['compressed-to-open census omission', r => {
    for (const c of r.finite_arm_contact_probe.cases) {
      c.compressed_to_open = 0; c.strict_open_compressed_class_changes = c.open_to_compressed;
      if (!c.open_to_compressed) c.largest_gap_change_class_switch = null;
    }
  }],
  ['missing contact scalar', r => {r.finite_arm_contact_probe.cases[0].all_contact_scalars.pop();}],
  ['nonfinite contact scalar', r => {r.finite_arm_contact_probe.cases[0].all_contact_scalars[0][1] = Infinity;}],
  ['wrong witness contact identity', r => {r.finite_arm_contact_probe.cases[0].maximum_absolute_gap_change.contact_id = 'foreign';}],
  ['changed gap witness', r => {r.finite_arm_contact_probe.cases[0].maximum_absolute_gap_change.gap_change_mm = 0;}],
  ['coherent fabricated gap maximum', r => {
    const w = r.finite_arm_contact_probe.cases[0].maximum_absolute_gap_change;
    w.fixed_director_finite_arm_gap_mm = 1; w.gap_change_mm = 1-w.linear_gap_mm; w.surrogate_class = 1;
  }],
  ['missing whole-load moment', r => {delete r.load_checks[0].whole_moment_about_origin_xyz_nmm;}],
  ['finite wrong whole-load moment', r => {r.load_checks[0].whole_moment_about_origin_xyz_nmm[0] += 1e6;}],
  ['zeroed whole-load moments', r => {for (const load of r.load_checks) load.whole_moment_about_origin_xyz_nmm = [0,0,0];}],
  ['zeroed eccentric couples', r => {for (const load of r.load_checks) load.midplane_couple_xyz_nmm = [0,0,0];}],
  ['wrong load point', r => {r.load_checks[0].load_point_xyz_mm = [0,0,0];}],
  ['foreign hold', r => {r.load_checks[0].hold = 'foreign';}],
  ['foreign loaded panel', r => {r.load_checks[0].panel = 'foreign';}],
  ['wrong wrench reference', r => {r.equilibrium_wrench_reference_xyz_mm[0] += 1;}],
  ['missing hold geometry', r => {delete r.recorded_hold_geometry.A12;}],
  ['wrong maximum rotation', r => {r.finite_arm_contact_probe.cases[0].maximum_relative_linear_rotation.relative_linear_rotation_rad = 0;}],
  ['missing active-action count', r => {delete r.active_action_load_path_screen[0].active_action_rows;}],
  ['zero active-action count', r => {r.active_action_load_path_screen[0].active_action_rows = 0;}],
  ['coordinated omitted routing edges', r => {for (const s of r.active_action_load_path_screen) {s.active_action_rows = 0; s.active_edge_census = [];}}],
  ['wrong routing owner census', r => {r.active_action_load_path_screen[0].physical_owner_ids.pop();}],
  ['false disconnected owner', r => {
    const s = r.active_action_load_path_screen[0];
    s.owners_without_active_action_path_to_floor = [s.physical_owner_ids[0]]; s.all_owners_have_active_action_path_to_floor = false;
  }],
  ['connectivity claimed as resistance', r => {r.active_action_load_path_screen[0].directional_restraint_capacity_or_complete_joint_behavior_qualified = true;}],
  ['screw-panel waiver', r => {r.screw_panel_load_path_removed_or_capacity_accepted = true;}],
  ['screw-panel deferral missing', r => {r.screw_panel_exceedance_resolution_deferred_by_owner = false;}],
  ['new unadopted motion threshold', r => {r.small_motion_threshold_adopted = .01;}],
  ['wrong frozen inputs', r => {r.verified_input_unions.pop();}],
]) test(`reject engineering assessment ${label}`, () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.engineering_assessment.path)));
  mutate(report);
  assert.throws(() => validateEngineeringAssessment(report, index));
});

for (const [label, mutate] of [
  ['stale geometry', r => {r.geometry_revision = 'old';}],
  ['stale hardware', r => {r.hardware_revision = 'old';}],
  ['response transfer', r => {r.preceding_reference_comparisons.applies_to_current_model = true;}],
  ['invented capacity', r => {r.thread_stacks[0].current_capacity = 1;}],
  ['false actual observation', r => {r.actual_observations = {};}],
  ['wrong source', r => {r.source_sha256[readIndex().hardware_model.receipt.path] = '0'.repeat(64);}],
  ['wrong producer', r => {r.source_sha256['scripts/eoere_structural_assessment.py'] = '0'.repeat(64);}],
  ['missing exceedances', r => {r.preceding_reference_comparisons.saved_reference_exceedances = [];}],
  ['missing witnesses', r => {r.preceding_reference_comparisons.governing_own_case_witnesses = [];}],
  ['missing case disclosures', r => {r.preceding_reference_comparisons.other_saved_exceedance_and_sensitivity_disclosures.pop();}],
  ['false count summary', r => {r.thread_catalog_envelope_counts = {NOMINAL_SMOOTH_BODY_COVERS_WOOD: 100};}],
  ['wrong quarter threshold', r => {r.thread_method.threshold = .27;}],
  ['missing unresolved mode', r => {r.current_unresolved_modes.pop();}],
  ['duplicated unresolved mode', r => {r.current_unresolved_modes[1] = r.current_unresolved_modes[0];}],
  ['invented spacer resistance', r => {r.spacer_contact.current_resistance = 1000;}],
  ['invented spacer action', r => {r.spacer_contact.current_axial_actions = {uncomputed: 1000};}],
  ['zero spacer contact area', r => {r.spacer_contact.nominal_projection_areas_mm2.spacer_annulus = 0;}],
  ['false spacer unit pressure', r => {r.spacer_contact.mean_pressure_mpa_per_1000n_centered_axial_force.spacer_annulus = 0;}],
  ['missing spacer unit pressure', r => {delete r.spacer_contact.mean_pressure_mpa_per_1000n_centered_axial_force.spacer_annulus;}],
  ...['structural_acceptance', 'native_solve_performed', 'remedies_attempted', 'extra_grid']
    .map(key => [key, r => {r[key] = true;}]),
]) test(`reject structural assessment ${label}`, () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.structural_assessment.path)));
  mutate(report);
  assert.throws(() => validateStructuralAssessment(report, index));
});

for (const [label, mutate] of [
  ['stale geometry', r => {r.geometry = readIndex().response.geometry;}],
  ['stale hardware', r => {r.hardware_revision = 'old';}],
  ['missing case', r => {r.cases.pop();}],
  ['duplicated state', r => {r.cases[1].state_id = r.cases[0].state_id;}],
  ['failed admission', r => {r.cases[0].current_equilibrium_and_recovery_pass = false;}],
  ['residual above gate', r => {r.cases[0].gradient_inf_n = .01;}],
  ['false residual maximum', r => {r.maximum_full_gradient_residual_n = 0;}],
  ['old case path', r => {r.cases[0].field.path = 'old/field.json';}],
  ['missing spacer action', r => {r.cases[0].spacer_nut_capture_actions.pop();}],
  ['unmeasured floor capacity', r => {r.cases[0].floor_support_summary.friction_or_anchor_capacity_established = true;}],
  ['invented panel RHS check', r => {r.cases[0].applied_load_checks.distributed_panel_rhs_independently_regenerated = true;}],
  ['invented joint capacity', r => {r.complete_joint_resistance = 1;}],
  ['invented finished capacity', r => {r.finished_member_capacity = 1;}],
  ['missing release flags', r => {r.release = {};}],
  ['changed force producer', r => {r.force_producer.sha256 = '0'.repeat(64);}],
  ['changed input checker', r => {r.input_checker.sha256 = '0'.repeat(64);}],
  ...['extra_grid', 'native_solve_performed', 'historical_q_forces_or_passes_transferred',
    'remedies_attempted', 'actual_build_fit_work_performed', 'structural_acceptance',
    'physical_demand_bounds_established'].map(key => [key, r => {r[key] = true;}]),
]) test(`reject current force response ${label}`, () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.current_response.cases.path)));
  mutate(report);
  assert.throws(() => validateCurrentResponse(report, index));
});

test('incoming descriptions reject a stale revision even when its link resolves', () => {
  const index = readCurrentIndex(), root = readFileSync(path.join(ROOT, 'README.md'), 'utf8');
  assert.throws(() => validateEntry(root.replaceAll(index.geometry.revision, index.preceding_revision.geometry.revision), index));
  const html = readFileSync(path.join(ROOT, 'site/index.html'), 'utf8');
  assert.equal(viewerModel(html, index.preceding_revision.geometry.revision), index.selected_baseline.candidate);
});

for (const [label, mutate] of [
  ['foreign force packet', r => {r.current_response = r.geometry;}],
  ['foreign geometry', r => {r.geometry = r.hardware_model;}],
  ['foreign state', r => {r.cases[0].state_id = r.cases[1].state_id;}],
  ['foreign field', r => {r.cases[0].field = r.cases[1].field;}],
  ['foreign raw component', r => {r.cases[0].raw_components.path = r.cases[1].raw_components.path;}],
  ['stale component producer', r => {r.component_producer.sha256 = '0'.repeat(64);}],
  ['stale section producer', r => {r.section_producer.sha256 = '0'.repeat(64);}],
  ['stale summary producer', r => {r.summary_producer.sha256 = '0'.repeat(64);}],
  ['missing release', r => {r.release = {};}],
  ['screw product capacity', r => {r.Hillman_product_capacity = 100;}],
  ['complete joint capacity', r => {r.complete_joint_resistance = 100;}],
  ['finished member capacity', r => {r.finished_member_capacity = 100;}],
  ['missing head exceedances', r => {r.cases[0].coarse.generic_screw_references.generic_CD1_head_exceedance_axis_ids = [];}],
  ['missing nonworst head exceedance', r => {r.cases[0].coarse.generic_screw_references.generic_CD1_head_exceedance_axis_ids.pop();}],
  ['missing nonworst head exceedances with coordinated counts', r => {
    const screws = r.cases[0].coarse.generic_screw_references;
    screws.generic_CD1_head_exceedance_axis_ids = [screws.generic_head_ratio_CD1.axis_id];
    screws.reference_counts.generic_CD1_head_exceedances = 1;
  }],
  ['foreign screw scalar axis', r => {r.cases[0].coarse.generic_screw_references.all_screw_reference_scalars[0].axis_id = 'foreign';}],
  ['nonfinite head reference', r => {r.cases[0].coarse.generic_screw_references.all_screw_reference_scalars[0].generic_head_ratio_CD1 = NaN;}],
  ['missing thread exceedances', r => {r.cases[0].coarse.generic_screw_references.all_effective_thread_length_reference_exceedances = [];}],
  ['missing nonworst thread exceedance with coordinated counts', r => {
    const screws = r.cases[3].coarse.generic_screw_references;
    screws.all_effective_thread_length_reference_exceedances = screws.all_effective_thread_length_reference_exceedances.filter(w =>
      w.axis_id === screws.generic_withdrawal_required_effective_thread_mm_CD1.axis_id);
    screws.reference_counts.effective_thread_length_exceedances = screws.all_effective_thread_length_reference_exceedances.length;
  }],
  ['missing panel exceedances', r => {r.cases[0].coarse.panels.sampled_section_exceedances_CD1 = [];}],
  ['missing nonworst panel exceedance', r => {r.cases[0].coarse.panels.sampled_section_exceedances_CD1.pop();}],
  ['missing stability census', r => {delete r.cases[0].gross_member_stability.all_member_witness_records;}],
  ['missing stability member', r => {r.cases[0].gross_member_stability.all_member_witness_records.pop();}],
  ['duplicate stability member', r => {
    const rows = r.cases[0].gross_member_stability.all_member_witness_records;
    rows[1] = structuredClone(rows[0]);
  }],
  ['foreign stability member', r => {r.cases[0].gross_member_stability.all_member_witness_records[0].member = 'foreign';}],
  ['changed stability span', r => {r.cases[0].gross_member_stability.all_member_witness_records[0].span_mm += 1;}],
  ['missing stability domain exceedances', r => {delete r.cases[0].gross_member_stability.full_length_domain_exceedances;}],
  ['empty stability domain exceedances', r => {r.cases[0].gross_member_stability.full_length_domain_exceedances = [];}],
  ['missing nonworst stability domain exceedance', r => {r.cases[0].gross_member_stability.full_length_domain_exceedances.pop();}],
  ['missing largest stability witness', r => {delete r.cases[0].gross_member_stability.largest_saved_K1_normal_sensitivity;}],
  ['changed whole largest stability witness', r => {r.cases[0].gross_member_stability.largest_saved_K1_normal_sensitivity.stress_compression_tension_strong_weak_mpa[0] += 1;}],
  ['missing stability reference exceedance list', r => {delete r.cases[0].gross_member_stability.saved_witness_reference_exceedances;}],
  ['nonexceeding stability reference witness', r => {
    const s = r.cases[0].gross_member_stability;
    s.saved_witness_reference_exceedances.push({member: s.all_member_witness_records[0].member,
      ...s.all_member_witness_records[0].two_saved_witness_sensitivities[0]});
  }],
  ['invented stability resistance', r => {r.cases[0].gross_member_stability.all_member_witness_records[0].actual_restraint_or_complete_resistance = 1;}],
  ['qualified outside stability domain', r => {
    const w = r.cases[0].gross_member_stability.all_member_witness_records
      .flatMap(m => m.two_saved_witness_sensitivities).find(v => !v.within_slenderness_limits);
    w.ratio_qualified_inside_declared_stability_domain = true;
  }],
  ['wrong screw reference census', r => {r.cases[0].coarse.generic_screw_references.reference_counts.axes = 65;}],
  ['duplicate head exceedance', r => {r.cases[0].coarse.generic_screw_references.generic_CD1_head_exceedance_axis_ids[1] = r.cases[0].coarse.generic_screw_references.generic_CD1_head_exceedance_axis_ids[0];}],
  ['foreign thread exceedance state', r => {r.cases[0].coarse.generic_screw_references.all_effective_thread_length_reference_exceedances[0].state_id = 'foreign';}],
  ['nonexceeding thread witness', r => {r.cases[0].coarse.generic_screw_references.all_effective_thread_length_reference_exceedances[0].generic_withdrawal_required_effective_thread_mm_CD1 = 0;}],
  ['changed same-axis thread witness', r => {r.cases[0].coarse.generic_screw_references.all_effective_thread_length_reference_exceedances[0].lateral_n += 1.;}],
  ['changed nonworst same-axis thread witness', r => {
    const screws = r.cases[3].coarse.generic_screw_references;
    const nonworst = screws.all_effective_thread_length_reference_exceedances.find(w =>
      w.axis_id !== screws.generic_withdrawal_required_effective_thread_mm_CD1.axis_id);
    assert.ok(nonworst);
    nonworst.lateral_n += 999;
  }],
  ['changed panel exceedance witness', r => {r.cases[0].coarse.panels.sampled_section_exceedances_CD1[0].xy_mm[0] += 1.;}],
  ['missing steel scenarios', r => {for (const c of r.cases) delete c.rich.steel_scenarios;}],
  ['missing steel scenario', r => {r.cases[0].rich.steel_scenarios.pop();}],
  ['foreign steel scenario', r => {r.cases[0].rich.steel_scenarios[0].comparison.id = 'foreign';}],
  ['invented Eoere strength', r => {r.cases[0].rich.steel_scenarios[0].product_strength = 100;}],
  ['steel changed actions', r => {r.cases[0].rich.steel_scenarios[0].fixed_actions_only = false;}],
  ['missing steel category', r => {delete r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined;}],
  ['wrong steel comparison count', r => {r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined.comparison_count = 87;}],
  ['missing steel scalar census', r => {delete r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined.all_reference_values;}],
  ['short steel scalar census', r => {r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined.all_reference_values.pop();}],
  ['missing heel exceedances', r => {r.cases[0].rich.steel_scenarios[0].summary.radius_conditioned_heel_component_with_gravity.exceedances = [];}],
  ['missing nonworst heel exceedance with coordinated counts and bindings', r => {
    const c = r.cases[2].rich.steel_scenarios[0].summary.radius_conditioned_heel_component_with_gravity;
    assert.ok(c.exceedances.length > 1);
    c.exceedances = [structuredClone(c.worst)];
    c.whole_exceedance_witness_bindings = structuredClone(c.exceedances);
    c.exceedance_count = 1;
  }],
  ['changed nonworst heel witness', r => {
    const c = r.cases[2].rich.steel_scenarios[0].summary.radius_conditioned_heel_component_with_gravity;
    const w = c.exceedances.find(w => w.conditional_combined_yield_reference_ratio < c.worst.conditional_combined_yield_reference_ratio);
    assert.ok(w); w.pure_bending_peak_mpa += 1;
  }],
  ['false worst steel value', r => {r.cases[0].rich.steel_scenarios[0].summary.near_hole_nominal_combined.worst.conditional_combined_yield_reference_ratio = 999;}],
  ['wood washer land transfer', r => {r.cases[0].rich.washers.nominal_seat_geometry.all_current_finished_wood_lands_qualified = true;}],
  ['spacer loading proxy', r => {r.cases[0].spacer_nuts[0].nominal_washer_ring_reference.uniform_load_ring_outer_radius_mm = 6.;}],
  ['spacer own force', r => {r.cases[0].spacer_nuts[0].N_n += 1.;}],
  ['mixed stack capacity', r => {r.cases[0].mixed_stack_statics.compatible_threaded_contact_or_yield_capacity = 100;}],
  ['floor capacity', r => {r.cases[0].support_screen.floor_friction_or_contact_pressure_capacity = 100;}],
  ['foreign finished state', r => {r.targeted_finished_sections.per_case_worst_witnesses[0].normal_worst.state_id = 'foreign';}],
  ['foreign global normal state', r => {r.targeted_finished_sections.maximum_normal_reference.state_id = 'foreign';}],
  ['foreign global shear state', r => {r.targeted_finished_sections.maximum_necessary_mean_shear.state_id = 'foreign';}],
  ['inconsistent global normal value', r => {r.targeted_finished_sections.maximum_normal_reference.normal_reference.fully_braced_linear_normal_CD1_reference_index = 999;}],
  ['inconsistent global shear value', r => {r.targeted_finished_sections.maximum_necessary_mean_shear.necessary_mean_shear_over_CD1_Fv = 999;}],
  ['missing global normal witness', r => {delete r.targeted_finished_sections.maximum_normal_reference;}],
  ['missing global shear witness', r => {delete r.targeted_finished_sections.maximum_necessary_mean_shear;}],
  ['missing finished normal exceedance list', r => {delete r.targeted_finished_sections.all_selected_plane_normal_reference_exceedances;}],
  ['missing finished shear exceedance list', r => {delete r.targeted_finished_sections.all_selected_plane_necessary_shear_reference_exceedances;}],
  ['fabricated foreign finished exceedance', r => {
    const f = r.targeted_finished_sections, w = structuredClone(f.maximum_normal_reference);
    w.state_id = 'foreign'; w.normal_reference.fully_braced_linear_normal_CD1_reference_index = 1.1;
    f.all_selected_plane_normal_reference_exceedances = [w];
  }],
  ['fabricated current finished exceedance', r => {
    const f = r.targeted_finished_sections, w = structuredClone(f.maximum_normal_reference);
    w.normal_reference.fully_braced_linear_normal_CD1_reference_index = 1.1;
    f.all_selected_plane_normal_reference_exceedances = [w];
  }],
  ['nonexceeding finished normal witness', r => {r.targeted_finished_sections.all_selected_plane_normal_reference_exceedances = [structuredClone(r.targeted_finished_sections.maximum_normal_reference)];}],
  ['nonexceeding finished shear witness', r => {r.targeted_finished_sections.all_selected_plane_necessary_shear_reference_exceedances = [structuredClone(r.targeted_finished_sections.maximum_necessary_mean_shear)];}],
  ['foreign finished plane', r => {r.targeted_finished_sections.per_case_worst_witnesses[0].normal_worst.member = 'foreign';}],
  ['nonfinite finished maximum', r => {r.targeted_finished_sections.maximum_normal_reference.normal_reference.fully_braced_linear_normal_CD1_reference_index = NaN;}],
  ['mixed global normal witness', r => {r.targeted_finished_sections.maximum_normal_reference.necessary_mean_shear_mpa += 1;}],
  ['duplicate plane', r => {r.targeted_finished_sections.planes[1] = r.targeted_finished_sections.planes[0];}],
  ['missing finished scalar census', r => {delete r.targeted_finished_sections.all_selected_plane_reference_scalars;}],
  ['missing finished scalar row', r => {r.targeted_finished_sections.all_selected_plane_reference_scalars.pop();}],
  ['duplicate finished scalar row', r => {
    const scalars = r.targeted_finished_sections.all_selected_plane_reference_scalars;
    scalars[1] = structuredClone(scalars[0]);
  }],
  ['foreign nonworst finished scalar state', r => {r.targeted_finished_sections.all_selected_plane_reference_scalars[0].state_id = 'foreign';}],
  ['nonfinite nonworst finished scalar', r => {r.targeted_finished_sections.all_selected_plane_reference_scalars[0].necessary_mean_shear_over_CD1_Fv = NaN;}],
  ['changed selected-plane normal worst value', r => {
    const f = r.targeted_finished_sections;
    f.per_case_worst_witnesses[0].normal_worst.normal_reference.fully_braced_linear_normal_CD1_reference_index += .01;
  }],
  ['continuous member capacity', r => {r.targeted_finished_sections.continuous_finished_member_resistance = 100;}],
  ...['extra_grid', 'structural_acceptance', 'native_solve_performed', 'CAD_rebuilt', 'actual_build_fit_work_performed',
    'remedies_attempted', 'physical_demand_bounds_established'].map(key => [key, r => {r[key] = true;}]),
]) test(`reject current component references ${label}`, () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.current_response.components.path)));
  mutate(report);
  assert.throws(() => validateCurrentComponents(report, index));
});

test('stability disclosures retain complete strict-threshold and tied whole witnesses', () => {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.current_response.components.path)));
  const stability = report.cases[0].gross_member_stability, members = stability.all_member_witness_records;
  for (const [i, j, ratio] of [[0, 0, 1.25], [1, 0, 1.25], [0, 1, 1.1], [1, 1, 1]]) {
    const witness = members[i].two_saved_witness_sensitivities[j];
    witness.interaction_ratio = ratio;
    witness.ratio_exceeds_one = ratio > 1;
  }
  const all = members.flatMap(m => m.two_saved_witness_sensitivities.map(w => ({member: m.member, ...w})));
  stability.saved_witness_reference_exceedances = structuredClone(all.filter(w => w.interaction_ratio > 1));
  stability.largest_saved_K1_normal_sensitivity = structuredClone(all.find(w => w.interaction_ratio === 1.25));
  assert.equal(stability.saved_witness_reference_exceedances.length, 3);
  validateCurrentComponents(report, index);
  stability.saved_witness_reference_exceedances.pop();
  assert.throws(() => validateCurrentComponents(report, index));
});

function reportWithFinishedExceedances() {
  const index = readIndex(), report = JSON.parse(readFileSync(path.join(ROOT, index.current_response.components.path)));
  const f = report.targeted_finished_sections;
  const planeID = w => JSON.stringify([w.member, w.station_global_grain_projection_mm]);
  function raise(caseIndex, worstKey, metric, value, otherPlane = false) {
    const original = f.per_case_worst_witnesses[caseIndex][worstKey];
    const plane = otherPlane ? f.planes.find(p => planeID(p) !== planeID(original)) : original;
    const scalar = f.all_selected_plane_reference_scalars.find(s => s.case_id === original.case_id && planeID(s) === planeID(plane));
    const witness = structuredClone(original);
    Object.assign(witness, {member: scalar.member, station_global_grain_projection_mm: scalar.station_global_grain_projection_mm,
      finished_area_mm2: f.planes.find(p => planeID(p) === planeID(scalar)).finished_area_mm2});
    scalar[metric] = value;
    witness.normal_reference.fully_braced_linear_normal_CD1_reference_index = scalar.fully_braced_linear_normal_CD1_reference_index;
    witness.necessary_mean_shear_over_CD1_Fv = scalar.necessary_mean_shear_over_CD1_Fv;
    scalar.exceedance_witness = witness;
  }
  const normalKey = 'fully_braced_linear_normal_CD1_reference_index', shearKey = 'necessary_mean_shear_over_CD1_Fv';
  for (const i of [0, 1]) raise(i, 'normal_worst', normalKey, 1.25);
  raise(0, 'normal_worst', normalKey, 1.1, true);
  for (const i of [2, 3]) raise(i, 'necessary_shear_worst', shearKey, i === 2 ? 1.2 : 1.3);
  raise(2, 'necessary_shear_worst', shearKey, 1.05, true);
  for (const row of f.per_case_worst_witnesses) for (const [key, metric] of [['normal_worst', normalKey], ['necessary_shear_worst', shearKey]]) {
    const worst = f.all_selected_plane_reference_scalars.filter(s => s.case_id === row.case_id).reduce((a,b) => a[metric] >= b[metric] ? a : b);
    row[key] = structuredClone(worst.exceedance_witness ?? row[key]);
  }
  f.maximum_normal_reference = structuredClone(f.per_case_worst_witnesses[1].normal_worst);
  f.maximum_necessary_mean_shear = structuredClone(f.per_case_worst_witnesses[3].necessary_shear_worst);
  f.all_selected_plane_normal_reference_exceedances = f.all_selected_plane_reference_scalars.filter(s => s[normalKey] > 1).map(s => structuredClone(s.exceedance_witness));
  f.all_selected_plane_necessary_shear_reference_exceedances = f.all_selected_plane_reference_scalars.filter(s => s[shearKey] > 1).map(s => structuredClone(s.exceedance_witness));
  return {index, report};
}

test('finished disclosures accept complete exceedances and tied whole maxima', () => {
  const {index, report} = reportWithFinishedExceedances();
  validateCurrentComponents(report, index);
});

for (const kind of ['normal_reference', 'necessary_shear_reference']) test(`reject omitted finished ${kind} witness`, () => {
  const {index, report} = reportWithFinishedExceedances();
  report.targeted_finished_sections[`all_selected_plane_${kind}_exceedances`].shift();
  assert.throws(() => validateCurrentComponents(report, index));
});

for (const [kind, metric, value] of [['normal_reference', w => w.normal_reference.fully_braced_linear_normal_CD1_reference_index, 1.1],
  ['necessary_shear_reference', w => w.necessary_mean_shear_over_CD1_Fv, 1.05]]) test(`reject omitted nonworst same-case finished ${kind} witness`, () => {
  const {index, report} = reportWithFinishedExceedances();
  const key = `all_selected_plane_${kind}_exceedances`;
  assert.ok(report.targeted_finished_sections[key].some(w => metric(w) === value));
  report.targeted_finished_sections[key] = report.targeted_finished_sections[key].filter(w => metric(w) !== value);
  assert.throws(() => validateCurrentComponents(report, index));
});

test('existing scene validators reject altered counts, moves and acceptance claims', () => {
  const index = readIndex();
  const current = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  const parent = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, 'site', current.parent_scene.url))));
  for (const [patch, validate, digest, mutate] of [
    [current, validateKickerClearance, index.geometry.receipt.sha256, p => {p.counts.base.screw = 65;}],
    [current, validateKickerClearance, index.geometry.receipt.sha256, p => {p.moved_screw_axes[0].new_origin_xyz_mm[2] = 211;}],
    [current, validateKickerClearance, index.geometry.receipt.sha256, p => {p.analysis_pass_transferred = true;}],
    [parent, validateUniformChannels, current.parent_scene.layout_sha256, p => {p.release.fabrication_released = true;}],
  ]) {
    const changed = structuredClone(patch); mutate(changed);
    assert.throws(() => validate(changed, digest));
  }
});

for (const [label, mutate] of [
  ['unsupported smaller harness envelope', p => {p.profile.front_width_mm = 8;}],
  ['missing narrowed member', p => {p.replacements.base.pop();}],
  ['notch physical release', p => {p.release.fabrication = true;}],
]) test(`reject ${label}`, () => {
  const index = readNotchIndex();
  const scene = JSON.parse(gunzipSync(readFileSync(path.join(ROOT, index.geometry.scene.path))));
  mutate(scene); assert.throws(() => validateNarrowChannels(scene, index.geometry.receipt.sha256));
});
for (const [label, mutate] of [
  ['notch receipt drift', i => {i.geometry.receipt.sha256 = '0'.repeat(64);}],
  ['missing narrowed shop coordinates', i => {i.shop.overrides = [];}],
  ['notch response transfer', i => {i.current_response = i.preceding_revision.preceding_revision.current_response;}],
]) test(`reject ${label}`, () => {
  const index = readNotchIndex(); mutate(index); assert.throws(() => checkCurrentDevelopment(index, {entryChecks: false}));
});
