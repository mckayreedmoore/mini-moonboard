import assert from 'node:assert/strict';
import {validateOwnerBarrelScene} from '../site/owner-barrel-overlay.mjs';

const stations = Array.from({length: 24}, (_, index) => `station_${index}`);
const hidden = Array.from({length: 170}, (_, index) => `part_${index}`);
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
    direct_joint_duties: 24,
  },
  station_dispositions: Object.fromEntries(stations.map(name => [name, 'LAYOUT_TRIAL'])),
  cross_family_physical_clash_stations: [],
  solids: [{role: 'moved_center_post'}, {role: 'moved_center_post'},
    {role: 'kicker_screw_backer'}, {role: 'kicker_screw_backer'}],
  diagnostic_bolt_axes: [],
  barrel_nut_envelopes: stations.map(source_station => ({source_station})),
  hidden_baseline_visual_names: hidden,
};

assert.equal(validateOwnerBarrelScene(scene, hidden), scene);
assert.throws(() => validateOwnerBarrelScene({...scene, structural_released: true}, hidden), /release boundary/);
assert.throws(() => validateOwnerBarrelScene({...scene, solids: [...scene.solids, {role: 'joint_wood'}]}, hidden), /Barrel-only/);
assert.throws(() => validateOwnerBarrelScene({...scene, station_dispositions: {}}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, barrel_nut_envelopes: []}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene({...scene, cross_family_physical_clash_stations: ['unknown']}, hidden), /24 duties/);
assert.throws(() => validateOwnerBarrelScene(scene, hidden.slice(1)), /baseline inventory/);
