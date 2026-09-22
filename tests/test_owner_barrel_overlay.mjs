import assert from 'node:assert/strict';
import {validateOwnerBarrelScene} from '../site/owner-barrel-overlay.mjs';

const headerStations = ['clip_timber_header_outer_left', 'clip_timber_header_outer_right'];
const stations = [...headerStations, ...Array.from({length: 22}, (_, index) => `station_${index}`)];
const hidden = ['base_header', ...Array.from({length: 183}, (_, index) => `part_${index}`)];
const recessEnvelopes = headerStations.flatMap(source_station =>
  [1, 2].flatMap(index => ['recess_head', 'recess_washer', 'recess_counterbore']
    .map(role => ({name: `${source_station}_${index}_${role}`, role, source_station}))));
const nominalAxial = {
  tip_past_assumed_axis_mm: 2.2,
  maximum_body_overlap_if_fully_threaded_mm: 7.2038,
  tip_to_modeled_bore_cap_mm: 4,
  flags: ['AXIS_REACHED_WITHIN_MODELED_BORE'],
  thread_engagement: 'UNKNOWN',
};
const scene = {
  schema: 'owner_barrel_layout_scene/v1',
  status: 'complete_layout_concept_not_qualified',
  baseline: 'compact-floor-flush-kerf-right',
  layout_clearance_approved: false,
  drilling_released: false,
  fabrication_released: false,
  structural_released: false,
  inventory: {
    replaced_angle_duties: 24,
    removed_structural_sds: 144,
    integrated_center_posts: 2,
    barrel_replacement_timbers: 16,
    kicker_screw_backers: 0,
    derived_cut_headers: 1,
    fixed_panel_kicker_screw_axes: 66,
    retained_frame_bolt_axes: 12,
    barrel_nut_envelopes: 46,
    new_diagnostic_bolt_axes: 46,
    rail_head_washer_envelopes: 40,
    other_head_washer_envelopes: 44,
    backer_attachment_duties: 0,
    backer_barrel_nut_envelopes: 0,
    backer_diagnostic_bolt_axes: 0,
    backer_head_washer_envelopes: 0,
    conditional_outer_header_recess_envelopes: 12,
    direct_joint_duties: 24,
  },
  station_dispositions: Object.fromEntries(stations.map(name => [name, 'LAYOUT_TRIAL'])),
  cross_family_physical_clash_stations: [],
  solids: [{role: 'integrated_center_post'}, {role: 'integrated_center_post'},
    {role: 'derived_cut_header', name: 'base_header/derived_outer_header_cut', mesh: {triangles: [[0, 1, 2]]}},
    ...Array.from({length: 13}, () => ({role: 'barrel_replacement_timber'}))],
  diagnostic_bolt_axes: Array.from({length: 46}, (_, index) => ({
    source_station: stations[index % stations.length], nominal_axial: nominalAxial,
  })),
  rail_head_washer_envelopes: Array(40).fill({role: 'rail_washer'}),
  other_head_washer_envelopes: Array(44).fill({role: 'joint_washer'}),
  backer_barrel_nut_envelopes: [],
  backer_diagnostic_bolt_axes: [],
  backer_head_washer_envelopes: [],
  backer_attachment: {status: 'not_applicable_integrated_center_posts'},
  integrated_kicker_backing: {
    status: 'geometric_receiver_and_post_header_path_only',
    fixed_center_kicker_screw_count: 4,
    post_header_barrel_pair_count: 4,
    complete_backing_load_path_verified: false,
  },
  integrated_center_joint_trial: {
    stations: Object.fromEntries(stations.slice(0, 4).map(name => [name, {}])),
    nominal_geometry_disposition: 'CANDIDATE_ONLY_UNVERIFIED',
    candidate_service_diameter_mm: 25.4,
    service_feed_qualified: false,
    assembly_moment_transfer_verified: false,
    unverified: {single_connector_moment_transfer_and_stiffness: true,
      service_feed_and_strength: true},
    structural_capacity_verified: false,
    release_flags: {drilling_released: false, fabrication_released: false},
  },
  barrel_nut_envelopes: Array.from({length: 46}, (_, index) => ({
    source_station: stations[index % stations.length],
  })),
  conditional_outer_header_recess_envelopes: recessEnvelopes,
  outer_header_cut_diagnostics: {
    source_member: 'base_header', counterbore_count: 4, machine_bore_count: 4,
    connected_solid_count: 1, cut_is_valid: true, uncut_volume_mm3: 100,
    cut_volume_mm3: 90, minimum_modeled_radial_edge_residual_mm: 6.35,
    displayed_visual_header_volume_mm3: 85, displayed_visual_header_includes_retained_cuts: true,
    counterbore_floor_residual_mm: 31.449, net_section_capacity_verified: false,
    disposition: 'REVISE', clearance_approved: false,
  },
  rim_first_sequence: {
    temporary_fixed_fastener_removal_required: true,
    per_rim_release: {panel_screws: 8, frame_bolts: 2, trial_rim_joint_bolts: 10},
    operational_result: 'conditional_unverified',
  },
  outer_header_recess_trial: {
    forward_row_y_mm: -85,
    counterbore_depth_mm: 6.651,
    side_rim_removal_required_for_driver: true,
    actual_rim_removal_verified: false,
    delivered_hardware_verified: false,
    structural_capacity_verified: false,
  },
  visual_wood_replacement: {
    replacement_timber_members: 16, excluded_legacy_sds_axes: 144,
    fixed_panel_receiver_cuts_in_replacements: 66,
    fixed_panel_axes_landing_on_separate_backers: 0,
    candidate_service_diameter_mm: 25.4,
    center_trial_cuts: 20,
    outer_header_barrel_body_cuts: 4,
    center_barrel_body_cuts: 6,
    remaining_trial_cuts: 108,
    candidate_barrel_pairs_with_cut_wood: 46,
    barrel_drilling_paths_without_cut_wood: [],
    barrel_path_host_anomalies: [],
    unrelated_remaining_pair_cut_intersections: [],
    remaining_pair_cut_intersections: Array(36).fill({}),
    remaining_to_protected_cut_intersections: [{member: 'base_rail_service_lower_left'}, {member: 'base_rail_service_upper_left'}],
    release: false,
  },
  hidden_baseline_visual_names: hidden,
};

assert.equal(validateOwnerBarrelScene(scene, hidden), scene);
assert.throws(() => validateOwnerBarrelScene({...scene, integrated_kicker_backing: {...scene.integrated_kicker_backing, complete_backing_load_path_verified: true}}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, structural_released: true}, hidden), /release boundary/);
assert.throws(() => validateOwnerBarrelScene({...scene, solids: [...scene.solids, {role: 'joint_wood'}]}, hidden), /Barrel-only/);
assert.throws(() => validateOwnerBarrelScene({...scene, station_dispositions: {}}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, barrel_nut_envelopes: []}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, conditional_outer_header_recess_envelopes: []}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, solids: scene.solids.slice(0, 4)}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, outer_header_cut_diagnostics: {...scene.outer_header_cut_diagnostics, connected_solid_count: 2}}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, rim_first_sequence: {...scene.rim_first_sequence, operational_result: 'verified'}}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, outer_header_recess_trial: {...scene.outer_header_recess_trial, structural_capacity_verified: true}}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, cross_family_physical_clash_stations: ['unknown']}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, backer_diagnostic_bolt_axes: Array(4).fill({})}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene(scene, hidden.slice(1)), /baseline inventory/);
