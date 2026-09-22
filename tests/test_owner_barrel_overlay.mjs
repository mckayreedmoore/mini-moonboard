import assert from 'node:assert/strict';
import {validateOwnerBarrelScene} from '../site/owner-barrel-overlay.mjs';

const headerStations = ['clip_timber_header_outer_left', 'clip_timber_header_outer_right'];
const stations = [...headerStations, ...Array.from({length: 22}, (_, index) => `station_${index}`)];
const hidden = Array.from({length: 170}, (_, index) => `part_${index}`);
const recessEnvelopes = headerStations.flatMap(source_station =>
  [1, 2].flatMap(index => ['recess_head', 'recess_washer', 'recess_counterbore']
    .map(role => ({name: `${source_station}_${index}_${role}`, role, source_station}))));
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
    moved_center_posts: 2,
    kicker_screw_backers: 2,
    fixed_panel_kicker_screw_axes: 66,
    retained_frame_bolt_axes: 12,
    barrel_nut_envelopes: 24,
    new_diagnostic_bolt_axes: 0,
    rail_head_washer_envelopes: 40,
    other_head_washer_envelopes: 48,
    backer_attachment_duties: 2,
    backer_barrel_nut_envelopes: 4,
    backer_diagnostic_bolt_axes: 4,
    backer_head_washer_envelopes: 8,
    conditional_outer_header_recess_envelopes: 12,
    direct_joint_duties: 24,
  },
  station_dispositions: Object.fromEntries(stations.map(name => [name, 'LAYOUT_TRIAL'])),
  cross_family_physical_clash_stations: [],
  solids: [{role: 'moved_center_post'}, {role: 'moved_center_post'},
    {role: 'kicker_screw_backer'}, {role: 'kicker_screw_backer'}],
  diagnostic_bolt_axes: [],
  rail_head_washer_envelopes: Array(40).fill({role: 'rail_washer'}),
  other_head_washer_envelopes: Array(48).fill({role: 'joint_washer'}),
  backer_barrel_nut_envelopes: Array(4).fill({role: 'backer_barrel'}),
  backer_diagnostic_bolt_axes: Array(4).fill({}),
  backer_head_washer_envelopes: Array(8).fill({role: 'backer_washer'}),
  backer_attachment: {
    station_dispositions: {backer_attachment_left: 'REVISE', backer_attachment_right: 'REVISE'},
    thread_engagement_verified: false,
    capacity_verified: false,
    release_flags: {drilling_released: false, fabrication_released: false},
  },
  barrel_nut_envelopes: stations.map(source_station => ({source_station})),
  conditional_outer_header_recess_envelopes: recessEnvelopes,
  outer_header_recess_trial: {
    forward_row_y_mm: -85,
    counterbore_depth_mm: 6.651,
    side_rim_removal_required_for_driver: true,
    actual_rim_removal_verified: false,
    delivered_hardware_verified: false,
    structural_capacity_verified: false,
  },
  hidden_baseline_visual_names: hidden,
};

assert.equal(validateOwnerBarrelScene(scene, hidden), scene);
assert.throws(() => validateOwnerBarrelScene({...scene, structural_released: true}, hidden), /release boundary/);
assert.throws(() => validateOwnerBarrelScene({...scene, solids: [...scene.solids, {role: 'joint_wood'}]}, hidden), /Barrel-only/);
assert.throws(() => validateOwnerBarrelScene({...scene, station_dispositions: {}}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, barrel_nut_envelopes: []}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, conditional_outer_header_recess_envelopes: []}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, outer_header_recess_trial: {...scene.outer_header_recess_trial, structural_capacity_verified: true}}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, cross_family_physical_clash_stations: ['unknown']}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene(scene, hidden.slice(1)), /baseline inventory/);
