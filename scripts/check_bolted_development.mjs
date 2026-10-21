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
import {validateFrontPosts} from '../site/eoere-front-posts-4x6-overlay.mjs';
import {validateNarrowChannels} from '../site/eoere-narrow-channels-overlay.mjs';
import {validateEnclosedPassages} from '../site/eoere-enclosed-passages-overlay.mjs';
import {validateLegHeader} from '../site/eoere-leg-header-overlay.mjs';

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

export function checkDevelopment(index = readIndex(), {entryChecks = true} = {}) {
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
